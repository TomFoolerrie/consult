"""WP-W0 — characterization tripwires for the four untested v1 source paths.

These tests pin CURRENT behavior of `sources.assess_new_sources`,
`sources.registered_ids`, `scaffold.write_promoted_notes`,
`engagement.intake_status` and `reconcile.check_src_citations` so the M34
consumer-wiring packages (W1-W3) cannot silently re-point them. They are
descriptive, not aspirational: where a behavior looks like a defect it is
characterized as-is and called out in a docstring comment.

Conventions per tests/conftest.py: every fixture lives under tmp_path, tests
assert observable results only, no repo-tracked writes.
"""
import hashlib

import yaml

import engagement
import reconcile
import scaffold
import sources


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_area(tmp_path, entries=None, staged=None, name="area"):
    """A minimal area: `_reference/sources.yaml` + staged `_sources/new/` files.

    `entries` is written verbatim as the `sources:` list (None -> no file at
    all). `staged` maps area-relative path -> file text.
    """
    area = tmp_path / "components" / name
    (area / "_sources" / "new").mkdir(parents=True)
    if entries is not None:
        (area / "_reference").mkdir(parents=True, exist_ok=True)
        (area / "_reference" / "sources.yaml").write_text(
            yaml.safe_dump({"sources": entries}), encoding="utf-8")
    for rel, text in (staged or {}).items():
        p = area / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    return area


# --------------------------------------------------------------------------- #
# sources.assess_new_sources — the guard-5 discriminator
# --------------------------------------------------------------------------- #

class TestAssessNewSources:

    def test_empty_staging_returns_two_empty_lists(self, tmp_path):
        area = make_area(tmp_path, entries=[])
        assert sources.assess_new_sources(str(area)) == ([], [])

    def test_staged_file_with_no_registry_entry_is_unassessed(self, tmp_path):
        area = make_area(tmp_path, entries=[],
                         staged={"_sources/new/a.md": "alpha"})
        unassessed, assessed = sources.assess_new_sources(str(area))
        assert unassessed == ["_sources/new/a.md"]
        assert assessed == []

    def test_missing_sources_yaml_makes_everything_unassessed(self, tmp_path):
        area = make_area(tmp_path, entries=None,
                         staged={"_sources/new/a.md": "alpha"})
        assert sources.assess_new_sources(str(area)) == (
            ["_sources/new/a.md"], [])

    def test_entry_with_no_recorded_hash_is_unassessed(self, tmp_path):
        """No `hash:` -> unassessed WITHOUT hashing the file (deliberate: the
        file may be a large binary the advisor sees on every `next`)."""
        area = make_area(
            tmp_path,
            entries=[{"id": "SRC-001", "file": "_sources/new/a.md",
                      "touches": ["p1"], "state": "new"}],
            staged={"_sources/new/a.md": "alpha"})
        unassessed, assessed = sources.assess_new_sources(str(area))
        assert unassessed == ["_sources/new/a.md"]
        assert assessed == []

    def test_empty_string_hash_is_unassessed(self, tmp_path):
        """`hash: ""` (stamp_sources writes this for a missing file) reads the
        same as no hash at all."""
        area = make_area(
            tmp_path,
            entries=[{"id": "SRC-001", "file": "_sources/new/a.md",
                      "hash": "   ", "touches": ["p1"], "state": "new"}],
            staged={"_sources/new/a.md": "alpha"})
        assert sources.assess_new_sources(str(area)) == (
            ["_sources/new/a.md"], [])

    def test_hash_mismatch_is_unassessed(self, tmp_path):
        area = make_area(
            tmp_path,
            entries=[{"id": "SRC-001", "file": "_sources/new/a.md",
                      "hash": _sha("OLD BYTES"), "touches": ["p1"],
                      "state": "new"}],
            staged={"_sources/new/a.md": "NEW BYTES"})
        unassessed, assessed = sources.assess_new_sources(str(area))
        assert unassessed == ["_sources/new/a.md"]
        assert assessed == []

    def test_hash_match_is_assessed_with_message_material(self, tmp_path):
        """An assessed entry carries exactly {id, file, touches, consumed,
        state} — the gate's message material."""
        area = make_area(
            tmp_path,
            entries=[{"id": "SRC-001", "file": "_sources/new/a.md",
                      "hash": _sha("alpha"), "touches": ["p1", "p2"],
                      "consumed": ["p1"], "state": "new"}],
            staged={"_sources/new/a.md": "alpha"})
        unassessed, assessed = sources.assess_new_sources(str(area))
        assert unassessed == []
        assert assessed == [{
            "id": "SRC-001",
            "file": "_sources/new/a.md",
            "touches": ["p1", "p2"],
            "consumed": ["p1"],
            "state": "new",
        }]

    def test_assessed_entry_defaults_id_and_state(self, tmp_path):
        """A matched entry with no `id:`/`state:` still assesses: id becomes
        '?' and state None (assessment is by hash, not by identity)."""
        area = make_area(
            tmp_path,
            entries=[{"file": "_sources/new/a.md", "hash": _sha("alpha")}],
            staged={"_sources/new/a.md": "alpha"})
        _unassessed, assessed = sources.assess_new_sources(str(area))
        assert assessed == [{"id": "?", "file": "_sources/new/a.md",
                             "touches": [], "consumed": [], "state": None}]

    def test_mixed_partition_is_sorted_by_staged_path(self, tmp_path):
        area = make_area(
            tmp_path,
            entries=[{"id": "SRC-001", "file": "_sources/new/a.md",
                      "hash": _sha("alpha"), "state": "new"}],
            staged={"_sources/new/a.md": "alpha",
                    "_sources/new/b.md": "bravo",
                    "_sources/new/c.md": "charlie"})
        unassessed, assessed = sources.assess_new_sources(str(area))
        assert unassessed == ["_sources/new/b.md", "_sources/new/c.md"]
        assert [a["id"] for a in assessed] == ["SRC-001"]

    def test_stale_recorded_path_matches_by_unambiguous_basename(self, tmp_path):
        """The fallback: the entry still records `_sources/processed/a.md` but
        the file sits in new/ — matched by basename because that basename is
        unique among registry entries."""
        area = make_area(
            tmp_path,
            entries=[{"id": "SRC-001", "file": "_sources/processed/a.md",
                      "hash": _sha("alpha"), "touches": ["p1"],
                      "state": "processed"}],
            staged={"_sources/new/a.md": "alpha"})
        unassessed, assessed = sources.assess_new_sources(str(area))
        assert unassessed == []
        # NB: `file` in the result is the STAGED path, while `state` comes from
        # the (stale) entry — so an assessed entry can read state: processed.
        assert assessed[0]["file"] == "_sources/new/a.md"
        assert assessed[0]["state"] == "processed"

    def test_ambiguous_basename_disables_the_fallback(self, tmp_path):
        """AMBIGUITY IS COUNTED ON THE REGISTRY SIDE, not the staging side: two
        ENTRIES recording the same basename in different subdirs make that
        basename ambiguous, so a staged file whose recorded path does not match
        exactly falls through to unassessed."""
        area = make_area(
            tmp_path,
            entries=[{"id": "SRC-001", "file": "_sources/processed/a.md",
                      "hash": _sha("alpha"), "state": "processed"},
                     {"id": "SRC-002", "file": "_sources/old/a.md",
                      "hash": _sha("alpha"), "state": "processed"}],
            staged={"_sources/new/a.md": "alpha"})
        unassessed, assessed = sources.assess_new_sources(str(area))
        assert unassessed == ["_sources/new/a.md"]
        assert assessed == []

    def test_two_staged_files_same_basename_both_match_one_entry(self, tmp_path):
        """Characterized, and surprising: two staged files sharing a basename in
        different subdirs are BOTH matched by the single registry entry's
        basename (staging-side duplication does not make the basename
        ambiguous). The exact-path match wins for one; the fallback claims the
        other, so a nested copy with identical bytes reads as assessed under the
        same SRC- id."""
        area = make_area(
            tmp_path,
            entries=[{"id": "SRC-001", "file": "_sources/new/a.md",
                      "hash": _sha("alpha"), "state": "new"}],
            staged={"_sources/new/a.md": "alpha",
                    "_sources/new/nested/a.md": "alpha"})
        unassessed, assessed = sources.assess_new_sources(str(area))
        assert unassessed == []
        assert sorted(a["file"] for a in assessed) == [
            "_sources/new/a.md", "_sources/new/nested/a.md"]
        assert {a["id"] for a in assessed} == {"SRC-001"}

    def test_dotfiles_and_route_sidecars_excluded(self, tmp_path):
        area = make_area(
            tmp_path, entries=[],
            staged={"_sources/new/a.md": "alpha",
                    "_sources/new/.DS_Store": "junk",
                    "_sources/new/a.md.route.md": "pointer prose",
                    "_sources/new/nested/.hidden": "junk"})
        assert sources.new_source_files(str(area)) == ["_sources/new/a.md"]
        unassessed, assessed = sources.assess_new_sources(str(area))
        assert unassessed == ["_sources/new/a.md"]
        assert assessed == []

    def test_nested_staged_files_are_listed_recursively(self, tmp_path):
        area = make_area(tmp_path, entries=[],
                         staged={"_sources/new/sub/deep/a.md": "alpha"})
        assert sources.new_source_files(str(area)) == [
            "_sources/new/sub/deep/a.md"]

    def test_malformed_registry_reads_as_nothing_assessed(self, tmp_path):
        """The tolerant read: a broken registry must not explode the advisor —
        every staged file reads unassessed and routes to taxonomy."""
        area = make_area(tmp_path, entries=[],
                         staged={"_sources/new/a.md": "alpha"})
        (area / "_reference" / "sources.yaml").write_text(
            "sources: [unclosed\n", encoding="utf-8")
        assert sources.assess_new_sources(str(area)) == (
            ["_sources/new/a.md"], [])


# --------------------------------------------------------------------------- #
# sources.registered_ids
# --------------------------------------------------------------------------- #

class TestRegisteredIds:

    def test_absent_file_is_empty_set(self, tmp_path):
        area = make_area(tmp_path, entries=None)
        assert sources.registered_ids(str(area)) == set()

    def test_malformed_yaml_is_empty_set(self, tmp_path):
        area = make_area(tmp_path, entries=[])
        (area / "_reference" / "sources.yaml").write_text(
            "sources: [unclosed\n", encoding="utf-8")
        assert sources.registered_ids(str(area)) == set()

    def test_empty_registry_is_empty_set(self, tmp_path):
        area = make_area(tmp_path, entries=[])
        assert sources.registered_ids(str(area)) == set()

    def test_null_sources_key_is_empty_set(self, tmp_path):
        area = make_area(tmp_path, entries=[])
        (area / "_reference" / "sources.yaml").write_text(
            "sources:\n", encoding="utf-8")
        assert sources.registered_ids(str(area)) == set()

    def test_normal_ids_are_read_and_stripped(self, tmp_path):
        area = make_area(tmp_path, entries=[
            {"id": "SRC-001"}, {"id": " SRC-002 "}])
        assert sources.registered_ids(str(area)) == {"SRC-001", "SRC-002"}

    def test_non_dict_and_non_string_id_entries_are_skipped(self, tmp_path):
        """Junk entries contribute nothing rather than raising — and note that
        an id of `3` (unquoted YAML int) is DROPPED, not coerced."""
        area = make_area(tmp_path, entries=[
            {"id": "SRC-001"}, "a bare string", {"no_id": "x"}, {"id": 3}])
        assert sources.registered_ids(str(area)) == {"SRC-001"}


# --------------------------------------------------------------------------- #
# scaffold.write_promoted_notes
# --------------------------------------------------------------------------- #

DRAFTED = "# P1\n\nReal drafted prose about the control.\n"
SKELETON = "# P1\n\n<!-- unfilled -->\n"


def make_notes_area(tmp_path, entries, fragments):
    """Minimal area for write_promoted_notes: sources.yaml + fragment files."""
    area = tmp_path / "components" / "area"
    (area / "_reference").mkdir(parents=True)
    (area / "_reference" / "sources.yaml").write_text(
        yaml.safe_dump({"sources": entries}), encoding="utf-8")
    slug_files = {}
    for slug, text in fragments.items():
        rel = "fragments/%s.md" % slug
        p = area / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        slug_files[slug] = rel
    return area, slug_files


class TestWritePromotedNotes:

    def test_processed_entry_is_skipped_entirely(self, tmp_path):
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/processed/a.md",
              "touches": ["p1"], "state": "processed"}],
            {"p1": DRAFTED})
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report == {"written": [], "skeleton": [], "deduped": [],
                          "dropped": []}
        assert not (area / "_review").exists()

    def test_consumed_slug_is_deduped_and_writes_nothing(self, tmp_path):
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/new/a.md",
              "touches": ["p1"], "consumed": ["p1"], "state": "new"}],
            {"p1": DRAFTED})
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report["deduped"] == ["SRC-001→p1"]
        assert report["written"] == []
        assert not (area / "_review" / "p1.notes.yaml").exists()

    def test_skeleton_fragment_is_classified_not_notified(self, tmp_path):
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/new/a.md",
              "touches": ["p1"], "state": "new"}],
            {"p1": SKELETON})
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report["skeleton"] == ["SRC-001→p1"]
        assert report["written"] == []
        assert not (area / "_review" / "p1.notes.yaml").exists()

    def test_missing_fragment_file_reads_as_skeleton(self, tmp_path):
        """A slug in slug_files whose file is not on disk classifies skeleton
        (never drafted), not dropped."""
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/new/a.md",
              "touches": ["p1"], "state": "new"}],
            {"p1": DRAFTED})
        (area / slug_files["p1"]).unlink()
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report["skeleton"] == ["SRC-001→p1"]

    def test_slug_not_in_this_area_is_silently_ignored(self, tmp_path):
        """A `touches` slug absent from slug_files produces NO report line at
        all — reconcile/M22 is the reporter for that defect."""
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/new/a.md",
              "touches": ["elsewhere"], "state": "new"}],
            {"p1": DRAFTED})
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report == {"written": [], "skeleton": [], "deduped": [],
                          "dropped": []}

    def test_drafted_fragment_gets_a_kind_source_note(self, tmp_path):
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/new/a.md",
              "touches": ["p1"], "state": "new"}],
            {"p1": DRAFTED})
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report["written"] == ["SRC-001→p1"]
        notes = area / "_review" / "p1.notes.yaml"
        assert notes.is_file()
        items = yaml.safe_load(notes.read_text(encoding="utf-8"))["items"]
        assert len(items) == 1
        assert items[0]["kind"] == "source"
        assert items[0]["src"] == "SRC-001"
        assert "SRC-001" in items[0]["note"]

    def test_proposal_wording_is_used_when_it_matches_the_pair(self, tmp_path):
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/new/a.md",
              "touches": ["p1"], "state": "new"}],
            {"p1": DRAFTED})
        report = scaffold.write_promoted_notes(
            area, slug_files,
            [{"slug": "p1", "kind": "source", "src": "SRC-001",
              "note": "The new SOP changes the approval threshold."}])
        assert report["written"] == ["SRC-001→p1"]
        assert report["dropped"] == []
        items = yaml.safe_load(
            (area / "_review" / "p1.notes.yaml").read_text(encoding="utf-8"))["items"]
        assert items[0]["note"] == "The new SOP changes the approval threshold."

    def test_wording_for_an_untouched_pair_is_dropped(self, tmp_path):
        """`touches` is the veto: wording for a (slug, src) pair the registry
        does not claim is reported dropped and never written."""
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/new/a.md",
              "touches": [], "state": "new"}],
            {"p1": DRAFTED})
        report = scaffold.write_promoted_notes(
            area, slug_files,
            [{"slug": "p1", "kind": "source", "src": "SRC-001",
              "note": "orphaned wording"}])
        assert report["dropped"] == ["SRC-001→p1"]
        assert report["written"] == []
        assert not (area / "_review" / "p1.notes.yaml").exists()

    def test_deduped_pair_still_marks_the_wording_used(self, tmp_path):
        """Characterized: a deduped (slug, src) pair `continue`s BEFORE
        `used.add(...)`, so its proposal wording is additionally reported as
        dropped — one confirmed proposal yields both lines for one pair."""
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/new/a.md",
              "touches": ["p1"], "consumed": ["p1"], "state": "new"}],
            {"p1": DRAFTED})
        report = scaffold.write_promoted_notes(
            area, slug_files,
            [{"slug": "p1", "kind": "source", "src": "SRC-001",
              "note": "wording for an already-consumed pair"}])
        assert report["deduped"] == ["SRC-001→p1"]
        assert report["dropped"] == ["SRC-001→p1"]
        assert report["written"] == []

    def test_non_source_proposal_notes_pass_through(self, tmp_path):
        area, slug_files = make_notes_area(tmp_path, [], {"p1": DRAFTED})
        report = scaffold.write_promoted_notes(
            area, slug_files,
            [{"slug": "p1", "kind": "rename", "note": "Renamed to X."}])
        assert report["written"] == ["rename→p1"]
        items = yaml.safe_load(
            (area / "_review" / "p1.notes.yaml").read_text(encoding="utf-8"))["items"]
        assert items[0]["kind"] == "rename"
        assert "slug" not in items[0]

    def test_non_source_note_at_a_skeleton_is_classified_skeleton(self, tmp_path):
        area, slug_files = make_notes_area(tmp_path, [], {"p1": SKELETON})
        report = scaffold.write_promoted_notes(
            area, slug_files,
            [{"slug": "p1", "kind": "rename", "note": "Renamed to X."}])
        assert report["skeleton"] == ["rename→p1"]
        assert report["written"] == []

    def test_rerunning_the_same_promotion_writes_nothing_new(self, tmp_path):
        """Idempotence comes from notes_util's fingerprint dedupe: the second
        pass reports NO `written` line even though nothing is `consumed` yet."""
        area, slug_files = make_notes_area(
            tmp_path,
            [{"id": "SRC-001", "file": "_sources/new/a.md",
              "touches": ["p1"], "state": "new"}],
            {"p1": DRAFTED})
        assert scaffold.write_promoted_notes(
            area, slug_files, [])["written"] == ["SRC-001→p1"]
        assert scaffold.write_promoted_notes(
            area, slug_files, [])["written"] == []
        items = yaml.safe_load(
            (area / "_review" / "p1.notes.yaml").read_text(encoding="utf-8"))["items"]
        assert len(items) == 1

    def test_absent_sources_yaml_only_passes_proposal_notes(self, tmp_path):
        area = tmp_path / "components" / "area"
        (area / "fragments").mkdir(parents=True)
        (area / "fragments" / "p1.md").write_text(DRAFTED, encoding="utf-8")
        report = scaffold.write_promoted_notes(
            area, {"p1": "fragments/p1.md"},
            [{"slug": "p1", "kind": "retirement", "note": "Retire: superseded."}])
        assert report["written"] == ["retirement→p1"]


# --------------------------------------------------------------------------- #
# engagement.intake_status
# --------------------------------------------------------------------------- #

class TestIntakeStatus:

    def test_no_intake_folder_is_two_empty_lists(self, tmp_path):
        comps = tmp_path / "components"
        comps.mkdir()
        assert engagement.intake_status(comps) == ([], [])

    def test_empty_intake_folder_is_two_empty_lists(self, tmp_path):
        comps = tmp_path / "components"
        comps.mkdir()
        (tmp_path / "intake").mkdir()
        assert engagement.intake_status(comps) == ([], [])

    def test_unprocessed_and_parked_are_both_reported(self, tmp_path):
        comps = tmp_path / "components"
        comps.mkdir()
        intake = tmp_path / "intake"
        (intake / "parked").mkdir(parents=True)
        (intake / "fresh.docx").write_text("x", encoding="utf-8")
        (intake / "parked" / "mystery.pdf").write_text("y", encoding="utf-8")
        (intake / "parked" / "reasons.log").write_text(
            "mystery.pdf — no area owns this yet\n", encoding="utf-8")
        unprocessed, parked = engagement.intake_status(comps)
        assert unprocessed == ["fresh.docx"]
        assert parked == [("mystery.pdf", "no area owns this yet")]

    def test_routed_and_parked_subfolders_are_not_unprocessed(self, tmp_path):
        comps = tmp_path / "components"
        comps.mkdir()
        intake = tmp_path / "intake"
        (intake / "routed").mkdir(parents=True)
        (intake / "parked").mkdir(parents=True)
        (intake / "routed" / "done.docx").write_text("x", encoding="utf-8")
        (intake / "routed" / "manifest.log").write_text("done.docx -> a\n",
                                                        encoding="utf-8")
        (intake / "parked" / "held.docx").write_text("y", encoding="utf-8")
        (intake / "top.docx").write_text("z", encoding="utf-8")
        unprocessed, parked = engagement.intake_status(comps)
        assert unprocessed == ["top.docx"]
        assert parked == [("held.docx", "(no reason recorded)")]

    def test_dotfiles_excluded_and_names_sorted(self, tmp_path):
        comps = tmp_path / "components"
        comps.mkdir()
        intake = tmp_path / "intake"
        intake.mkdir()
        for n in ("b.docx", "a.docx", ".DS_Store"):
            (intake / n).write_text("x", encoding="utf-8")
        assert engagement.intake_status(comps)[0] == ["a.docx", "b.docx"]

    def test_reasons_log_is_the_only_excluded_parked_name(self, tmp_path):
        """`reasons.log` itself never appears as a parked file, and a log line
        for a file that is no longer parked is simply unused."""
        comps = tmp_path / "components"
        comps.mkdir()
        parked_dir = tmp_path / "intake" / "parked"
        parked_dir.mkdir(parents=True)
        (parked_dir / "reasons.log").write_text(
            "gone.docx — parked then removed\n", encoding="utf-8")
        assert engagement.intake_status(comps) == ([], [])


# --------------------------------------------------------------------------- #
# reconcile.check_src_citations
# --------------------------------------------------------------------------- #

def make_reconcile_area(tmp_path, entries, fragment_text):
    """Narrowest callable unit: a Ctx built directly (as reconcile's runner does
    at scripts/reconcile.py's `ctx = Ctx(folder, manifest)`) over a one-procedure
    manifest — the full runner would need a whole scaffolded area."""
    area = tmp_path / "components" / "area"
    (area / "fragments").mkdir(parents=True)
    (area / "fragments" / "p1.md").write_text(fragment_text, encoding="utf-8")
    if entries is not None:
        (area / "_reference").mkdir(parents=True, exist_ok=True)
        (area / "_reference" / "sources.yaml").write_text(
            yaml.safe_dump({"sources": entries}), encoding="utf-8")
    manifest = {"components": [
        {"slug": "p1", "role": "procedure", "file": "fragments/p1.md"}]}
    return reconcile.Ctx(area, manifest)


class TestCheckSrcCitations:

    def test_empty_registry_skips_with_a_warning_not_errors(self, tmp_path):
        """The BOUNDARY: a registry registering nothing must not fail every
        citation — the check warns loudly and skips."""
        ctx = make_reconcile_area(
            tmp_path, [], "# P1\n\nPer SRC-001 the threshold is $5k.\n")
        reconcile.check_src_citations(ctx)
        assert ctx.errors == []
        assert len(ctx.warnings) == 1
        assert "registers no SRC- ids" in ctx.warnings[0]
        assert "citation check skipped" in ctx.warnings[0]

    def test_absent_registry_skips_the_same_way(self, tmp_path):
        ctx = make_reconcile_area(
            tmp_path, None, "# P1\n\nPer SRC-001 the threshold is $5k.\n")
        reconcile.check_src_citations(ctx)
        assert ctx.errors == []
        assert len(ctx.warnings) == 1

    def test_empty_registry_and_no_citations_is_silent(self, tmp_path):
        """Characterized: with no registry the NO SOURCE CITATION error is not
        raised either — the whole check is skipped, both halves."""
        ctx = make_reconcile_area(tmp_path, [], "# P1\n\nPlain prose.\n")
        reconcile.check_src_citations(ctx)
        assert ctx.errors == []
        assert ctx.warnings == []

    def test_unregistered_cited_id_is_an_error(self, tmp_path):
        ctx = make_reconcile_area(
            tmp_path, [{"id": "SRC-001"}],
            "# P1\n\nPer SRC-001 and SRC-999 the threshold is $5k.\n")
        reconcile.check_src_citations(ctx)
        assert len(ctx.errors) == 1
        assert "UNREGISTERED CITATION SRC-999" in ctx.errors[0]
        assert "fragments/p1.md:3" in ctx.errors[0]
        assert ctx.warnings == []

    def test_registered_citation_passes(self, tmp_path):
        ctx = make_reconcile_area(
            tmp_path, [{"id": "SRC-001"}],
            "# P1\n\nPer SRC-001 the threshold is $5k.\n")
        reconcile.check_src_citations(ctx)
        assert ctx.errors == []
        assert ctx.warnings == []

    def test_procedure_citing_nothing_is_an_error_once_a_registry_exists(
            self, tmp_path):
        ctx = make_reconcile_area(
            tmp_path, [{"id": "SRC-001"}], "# P1\n\nPlain prose.\n")
        reconcile.check_src_citations(ctx)
        assert len(ctx.errors) == 1
        assert "NO SOURCE CITATION" in ctx.errors[0]

    def test_unfilled_skeleton_is_exempt_from_the_no_citation_error(self, tmp_path):
        ctx = make_reconcile_area(
            tmp_path, [{"id": "SRC-001"}], "# P1\n\n<!-- unfilled -->\n")
        reconcile.check_src_citations(ctx)
        assert ctx.errors == []
        assert ctx.warnings == []

    def test_citations_inside_fences_do_not_count(self, tmp_path):
        """Fence-blanked text is what the check reads, so an id that appears
        ONLY in a code fence leaves the procedure citing nothing."""
        ctx = make_reconcile_area(
            tmp_path, [{"id": "SRC-001"}],
            "# P1\n\n```\nSRC-001\n```\n")
        reconcile.check_src_citations(ctx)
        assert len(ctx.errors) == 1
        assert "NO SOURCE CITATION" in ctx.errors[0]
