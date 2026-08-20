"""WP-W3 — central-mode scaffold behavior (M34).

The v1 side of these paths is pinned by
`tests/test_v1_source_characterization.py`; this file covers what changes when
an area sits under an engagement carrying `<root>/_sources/sources.yaml`:

* `stamp_sources` is a no-op (hashes are stamped at registration);
* `.proposed/sources.yaml` is a TAG REFINEMENT — `ledger.retag` REPLACES the
  area's touches slice, and validates slugs like `register` does;
* `write_promoted_notes` reads `ledger.area_view` instead of a per-area
  registry (consumed pairs dedupe, drafted fragments get a `kind: source` note
  naming the ledger id);
* `engagement.adopt` mints through the ledger — ONE minter, so it cannot
  collide with an id the ledger already holds.

Fixture conventions per the characterization file: everything under tmp_path,
observable results only, no repo-tracked writes.
"""
import json

import pytest
import yaml

import engagement
import scaffold

import ledger

DRAFTED = "## Heading\n\nReal drafted prose, no sentinel here.\n"
SKELETON = "## Heading\n\n<!-- unfilled -->\n"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def make_central(tmp_path, fragments=None, procs=("p1", "p2")):
    """A central engagement with one area `p2p`, plus optional fragments.

    Returns `(root, area, slug_files)`. The empty ledger file IS the mode
    marker; `fragments` maps slug -> file text, mirroring `make_notes_area`.
    """
    root = tmp_path / "engagement"
    (root / "_sources" / "new").mkdir(parents=True)
    (root / "_sources" / "sources.yaml").write_text("sources: []\n",
                                                    encoding="utf-8")
    area = root / "components" / "p2p"
    (area / "_reference").mkdir(parents=True)
    manifest = {
        "schema": "consult-mvp-manifest/v1", "area": "p2p",
        "l1": "P2P", "title": "P2P", "l2_order": ["main"],
        "components": [
            {"file": f"10_{s}.md", "heading": s, "order": (i + 1) * 10,
             "role": "procedure", "slug": s, "l2": "main"}
            for i, s in enumerate(procs)
        ],
    }
    (area / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    slug_files = {}
    for slug, text in (fragments or {}).items():
        rel = "fragments/%s.md" % slug
        p = area / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        slug_files[slug] = rel
    return root, area, slug_files


def stage(root, name, text="transcript body\n"):
    f = root / "_sources" / "new" / name
    f.write_text(text, encoding="utf-8")
    return f


def propose(area, entries):
    d = area / "_reference" / ".proposed"
    d.mkdir(parents=True, exist_ok=True)
    (d / "sources.yaml").write_text(yaml.safe_dump({"sources": entries}),
                                    encoding="utf-8")


# --------------------------------------------------------------------------- #
# stamp_sources — a no-op with a stated reason
# --------------------------------------------------------------------------- #

class TestStampSourcesCentral:

    def test_no_op_prints_a_reason_and_writes_nothing(self, tmp_path, capsys):
        root, area, _ = make_central(tmp_path)
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1"]})
        before = (root / "_sources" / "sources.yaml").read_bytes()
        scaffold.stamp_sources(area)
        assert "central mode" in capsys.readouterr().out
        assert (root / "_sources" / "sources.yaml").read_bytes() == before
        assert not (area / "_reference" / "sources.yaml").exists()
        assert ledger.entries(root)[0]["id"] == sid

    def test_a_stray_area_registry_is_left_alone(self, tmp_path):
        """Central mode never touches a per-area sources.yaml, even a legacy
        one left behind by a migration — the ledger is the only writer."""
        root, area, _ = make_central(tmp_path)
        legacy = area / "_reference" / "sources.yaml"
        legacy.write_text(yaml.safe_dump(
            {"sources": [{"id": "SRC-001", "file": "_sources/new/x.md"}]}),
            encoding="utf-8")
        before = legacy.read_bytes()
        scaffold.stamp_sources(area)
        assert legacy.read_bytes() == before

    def test_v1_area_still_stamps(self, tmp_path):
        """The mode marker is what switches behavior — no marker, v1 stamping."""
        area = tmp_path / "components" / "cash"
        (area / "_reference").mkdir(parents=True)
        (area / "_sources" / "new").mkdir(parents=True)
        (area / "_sources" / "new" / "a.md").write_text("body\n",
                                                        encoding="utf-8")
        (area / "_reference" / "sources.yaml").write_text(yaml.safe_dump(
            {"sources": [{"id": "SRC-001", "file": "_sources/new/a.md",
                          "touches": ["p1"]}]}), encoding="utf-8")
        scaffold.stamp_sources(area)
        data = yaml.safe_load(
            (area / "_reference" / "sources.yaml").read_text(encoding="utf-8"))
        assert data["sources"][0]["hash"]
        assert data["sources"][0]["state"] == "new"


# --------------------------------------------------------------------------- #
# ledger.retag — the confirm-gate veto, as a REPLACE
# --------------------------------------------------------------------------- #

class TestRetag:

    def test_replaces_the_area_slice(self, tmp_path):
        root, area, _ = make_central(tmp_path)
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1", "p2"]})
        assert ledger.retag(root, sid, "p2p", ["p2"]) == ["p2"]
        assert ledger.entries(root)[0]["touches"] == {"p2p": ["p2"]}

    def test_empty_list_untags_the_area(self, tmp_path):
        """The human deleting every slug at the gate must actually stop the
        dispatch — which a union could not express."""
        root, area, _ = make_central(tmp_path)
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1"]})
        ledger.retag(root, sid, "p2p", [])
        assert ledger.outstanding(root, "p2p") == {}

    def test_other_areas_are_untouched(self, tmp_path):
        root, area, _ = make_central(tmp_path)
        other = root / "components" / "r2r"
        other.mkdir(parents=True)
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1"], "r2r": ["x"]})
        ledger.retag(root, sid, "p2p", ["p2"])
        touches = ledger.entries(root)[0]["touches"]
        assert touches == {"p2p": ["p2"], "r2r": ["x"]}

    def test_bad_slug_is_a_ledger_error(self, tmp_path):
        root, area, _ = make_central(tmp_path)
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1"]})
        with pytest.raises(ledger.LedgerError) as exc:
            ledger.retag(root, sid, "p2p", ["typo-slug"])
        assert "typo-slug" in str(exc.value)
        assert ledger.entries(root)[0]["touches"] == {"p2p": ["p1"]}

    def test_unknown_id_is_a_ledger_error(self, tmp_path):
        root, area, _ = make_central(tmp_path)
        with pytest.raises(ledger.LedgerError):
            ledger.retag(root, "SRC-404", "p2p", [])

    def test_consumed_is_not_pruned(self, tmp_path):
        """Parked WP-B decision: a slug leaving `touches` keeps its consumption
        record — erasing one would silently re-dispatch work already done."""
        root, area, _ = make_central(tmp_path)
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1", "p2"]})
        ledger.credit(root, "p2p", filled=["p1"])
        ledger.retag(root, sid, "p2p", ["p2"])
        assert ledger.entries(root)[0]["consumed"] == {"p2p": ["p1"]}


# --------------------------------------------------------------------------- #
# promote_reference / promote_tag_refinements — the sources half, centrally
# --------------------------------------------------------------------------- #

class TestPromoteTagRefinements:

    def test_proposal_matched_by_hash_refines_the_tags(self, tmp_path):
        root, area, _ = make_central(tmp_path)
        f = stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": []})
        digest = ledger._hash_file(str(f))
        propose(area, [{"id": "SRC-999", "hash": digest, "touches": ["p1"]}])
        scaffold.promote_reference(area)
        assert ledger.entries(root)[0]["touches"] == {"p2p": ["p1"]}
        assert ledger.entries(root)[0]["id"] == sid
        # no per-area registry is created in central mode
        assert not (area / "_reference" / "sources.yaml").exists()

    def test_proposal_matched_by_id_refines_the_tags(self, tmp_path):
        root, area, _ = make_central(tmp_path)
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1"]})
        propose(area, [{"id": sid, "touches": ["p2"]}])
        scaffold.promote_reference(area)
        assert ledger.entries(root)[0]["touches"] == {"p2p": ["p2"]}

    def test_unmatched_proposal_is_reported_and_dropped(self, tmp_path, capsys):
        root, area, _ = make_central(tmp_path)
        stage(root, "a.md")
        ledger.register(root, "a.md", {"p2p": ["p1"]})
        propose(area, [{"id": "SRC-404", "touches": ["p2"]}])
        scaffold.promote_reference(area)
        assert "SRC-404" in capsys.readouterr().err
        assert ledger.entries(root)[0]["touches"] == {"p2p": ["p1"]}
        assert len(ledger.entries(root)) == 1     # the gate mints nothing

    def test_bad_slug_at_the_gate_stops_the_run(self, tmp_path):
        root, area, _ = make_central(tmp_path)
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1"]})
        propose(area, [{"id": sid, "touches": ["nope"]}])
        with pytest.raises(SystemExit):
            scaffold.promote_reference(area)

    def test_other_registries_still_promote_centrally(self, tmp_path):
        root, area, _ = make_central(tmp_path)
        d = area / "_reference" / ".proposed"
        d.mkdir(parents=True)
        (d / "systems.yaml").write_text(
            yaml.safe_dump({"systems": [{"slug": "sap", "name": "SAP"}]}),
            encoding="utf-8")
        scaffold.promote_reference(area)
        live = yaml.safe_load(
            (area / "_reference" / "systems.yaml").read_text(encoding="utf-8"))
        assert live["systems"][0]["slug"] == "sap"


# --------------------------------------------------------------------------- #
# write_promoted_notes over a central engagement
# --------------------------------------------------------------------------- #

class TestWritePromotedNotesCentral:

    def test_drafted_fragment_gets_a_kind_source_note(self, tmp_path):
        root, area, slug_files = make_central(tmp_path, {"p1": DRAFTED})
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1"]})
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report["written"] == ["%s→p1" % sid]
        items = yaml.safe_load(
            (area / "_review" / "p1.notes.yaml").read_text(encoding="utf-8"))
        assert items["procedure"] == "p1"
        item = items["items"][0]
        assert item["kind"] == "source" and item["src"] == sid
        assert sid in item["note"]
        # the prose names the ENGAGEMENT ledger, not a per-area registry
        assert "_sources/sources.yaml" in item["note"]
        assert "_reference/sources.yaml" not in item["note"]

    def test_consumed_pair_dedupes(self, tmp_path):
        root, area, slug_files = make_central(tmp_path, {"p1": DRAFTED})
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1", "p2"]})
        ledger.credit(root, "p2p", filled=["p1"])
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report["deduped"] == ["%s→p1" % sid]
        assert report["written"] == []
        assert not (area / "_review" / "p1.notes.yaml").exists()

    def test_skeleton_is_classified_not_notified(self, tmp_path):
        root, area, slug_files = make_central(tmp_path, {"p1": SKELETON})
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1"]})
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report["skeleton"] == ["%s→p1" % sid]
        assert not (area / "_review" / "p1.notes.yaml").exists()

    def test_another_areas_source_is_invisible_here(self, tmp_path):
        root, area, slug_files = make_central(tmp_path, {"p1": DRAFTED})
        other = root / "components" / "r2r"
        other.mkdir(parents=True)
        stage(root, "b.md")
        ledger.register(root, "b.md", {"r2r": ["whatever"]})
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report == {"written": [], "skeleton": [], "deduped": [],
                          "dropped": []}

    def test_fully_consumed_source_is_skipped_as_processed(self, tmp_path):
        root, area, slug_files = make_central(tmp_path, {"p1": DRAFTED})
        stage(root, "a.md")
        ledger.register(root, "a.md", {"p2p": ["p1"]})
        ledger.credit(root, "p2p", filled=["p1"])
        report = scaffold.write_promoted_notes(area, slug_files, [])
        assert report["written"] == [] and report["deduped"] == []

    def test_rerun_writes_nothing_new(self, tmp_path):
        root, area, slug_files = make_central(tmp_path, {"p1": DRAFTED})
        stage(root, "a.md")
        ledger.register(root, "a.md", {"p2p": ["p1"]})
        scaffold.write_promoted_notes(area, slug_files, [])
        again = scaffold.write_promoted_notes(area, slug_files, [])
        assert again["written"] == []
        items = yaml.safe_load(
            (area / "_review" / "p1.notes.yaml").read_text(
                encoding="utf-8"))["items"]
        assert len(items) == 1

    def test_proposal_wording_wins_when_it_matches(self, tmp_path):
        root, area, slug_files = make_central(tmp_path, {"p1": DRAFTED})
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": ["p1"]})
        report = scaffold.write_promoted_notes(
            area, slug_files,
            [{"slug": "p1", "kind": "source", "src": sid,
              "note": "the AP cutoff rule is in here"}])
        assert report["written"] == ["%s→p1" % sid]
        items = yaml.safe_load(
            (area / "_review" / "p1.notes.yaml").read_text(
                encoding="utf-8"))["items"]
        assert items[0]["note"] == "the AP cutoff rule is in here"

    def test_wording_for_an_untagged_pair_is_dropped(self, tmp_path):
        """touches (in the ledger) is still the dispatch authority."""
        root, area, slug_files = make_central(tmp_path, {"p1": DRAFTED})
        stage(root, "a.md")
        sid = ledger.register(root, "a.md", {"p2p": []})
        report = scaffold.write_promoted_notes(
            area, slug_files,
            [{"slug": "p1", "kind": "source", "src": sid, "note": "nope"}])
        assert report["dropped"] == ["%s→p1" % sid]
        assert report["written"] == []


# --------------------------------------------------------------------------- #
# adopt: ONE minter
# --------------------------------------------------------------------------- #

class TestAdoptCentral:

    def _two_areas(self, tmp_path):
        root, area, _ = make_central(tmp_path, procs=("p1", "p2"))
        donor = root / "components" / "r2r"
        donor.mkdir(parents=True)
        (donor / "manifest.json").write_text(json.dumps({
            "schema": "consult-mvp-manifest/v1", "area": "r2r", "l1": "R2R",
            "title": "R2R", "l2_order": ["main"],
            "components": [{"file": "10_accrue.md", "heading": "Accruals",
                            "order": 10, "role": "procedure",
                            "slug": "accrue-ap", "l2": "main"}],
        }), encoding="utf-8")
        (donor / "10_accrue.md").write_text(
            "## Accruals\n\nDrafted accruals prose.\n", encoding="utf-8")
        return root, area, donor

    def test_adopt_mints_through_the_ledger(self, tmp_path):
        root, area, _ = self._two_areas(tmp_path)
        rc = engagement.adopt(area, "r2r/accrue-ap", ["p1"])
        assert rc == 0
        entries = ledger.entries(root)
        assert len(entries) == 1
        e = entries[0]
        assert e["touches"] == {"p2p": ["p1"]}
        assert e["hash"] and "adopted-r2r-accrue-ap.md" in e["file"]
        assert "adopted as a" in e["note"]         # provenance carried over
        # the bytes stage centrally, NOT in the area's own _sources/
        assert (root / "_sources" / "new"
                / "adopted-r2r-accrue-ap.md").is_file()
        assert not (area / "_sources").exists()
        assert not (area / "_reference" / "sources.yaml").exists()
        items = yaml.safe_load(
            (area / "_review" / "p1.notes.yaml").read_text(
                encoding="utf-8"))["items"]
        assert items[0]["src"] == e["id"]

    def test_no_max_plus_one_collision_with_an_existing_ledger_id(
            self, tmp_path):
        """ONE minter: the id adopt gets continues the ENGAGEMENT sequence, so
        it cannot land on top of a source another area already registered (v1's
        private max+1 counted only the area's own registry)."""
        root, area, _ = self._two_areas(tmp_path)
        stage(root, "prior.md", "someone else's transcript\n")
        first = ledger.register(root, "prior.md", {"p2p": ["p2"]})
        assert engagement.adopt(area, "r2r/accrue-ap", ["p1"]) == 0
        ids = [e["id"] for e in ledger.entries(root)]
        assert ids == [first, "SRC-002"]
        assert len(set(ids)) == 2

    def test_adopt_is_idempotent_at_the_hash(self, tmp_path, capsys):
        root, area, _ = self._two_areas(tmp_path)
        engagement.adopt(area, "r2r/accrue-ap", ["p1"])
        capsys.readouterr()
        assert engagement.adopt(area, "r2r/accrue-ap", ["p1"]) == 0
        assert "already adopted" in capsys.readouterr().out
        assert len(ledger.entries(root)) == 1
        assert ledger.entries(root)[0]["note"].count("adopted as a") == 1

    def test_bad_touches_slug_still_refused_before_anything_is_written(
            self, tmp_path):
        root, area, _ = self._two_areas(tmp_path)
        assert engagement.adopt(area, "r2r/accrue-ap", ["not-a-slug"]) == 2
        assert ledger.entries(root) == []
        assert not (root / "_sources" / "new"
                    / "adopted-r2r-accrue-ap.md").exists()
