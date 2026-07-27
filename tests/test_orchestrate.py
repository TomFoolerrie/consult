"""Tests for scripts/orchestrate.py — the M7 read-only state advisor.

Pins the precedence table (first match wins), the M11 wave scheduling of the
`fill` guard, and the emit_* state-file round-trips. All areas are synthetic,
built under tmp_path.
"""
import json
import os

import orchestrate
import scope_delta


FILLED_BODY = "## {title}\n\nReal drafted content.\n"
UNFILLED_BODY = "## {title}\n\n<!-- unfilled -->\n\nTBD.\n"


def make_area(tmp_path, procs=None, name="treasury"):
    """Build a minimal area: manifest.json + one fragment per procedure.

    `procs` is a list of dicts: {slug, filled: bool, upstream: [slugs]}.
    Returns the area folder path (str).
    """
    area = tmp_path / name
    area.mkdir(parents=True, exist_ok=True)
    components = []
    for i, p in enumerate(procs or []):
        fname = f"10_{p['slug']}.md"
        comp = {"file": fname, "role": "procedure", "slug": p["slug"],
                "heading": p["slug"].title(), "l2": "ops",
                "order": 10 + 10 * i}
        if p.get("upstream"):
            comp["upstream"] = list(p["upstream"])
        components.append(comp)
        body = FILLED_BODY if p.get("filled") else UNFILLED_BODY
        (area / fname).write_text(body.format(title=p["slug"]),
                                  encoding="utf-8")
    manifest = {"schema": "consult-mvp-manifest/v1", "area": name,
                "l1": "finance", "l2_order": ["ops"], "title": "T",
                "subtitle": "S", "components": components}
    (area / "manifest.json").write_text(json.dumps(manifest),
                                        encoding="utf-8")
    return str(area)


def _declare_agent_views(area):
    """Add the two agent-owned derived components to an area's manifest.

    M14: guard 9's kinds come from the manifest — the document profile decides
    which derived views exist — so a walk that expects `synthesize` must say
    the judgment views are part of this document.
    """
    path = os.path.join(area, "manifest.json")
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["components"] += [
        {"file": "82_dependencies.md", "role": "derived", "order": 8200,
         "derived_kind": "dependencies", "writer": "agent",
         "heading": "Key Dependencies"},
        {"file": "84_raci.md", "role": "derived", "order": 8400,
         "derived_kind": "raci", "writer": "agent", "heading": "RACI Matrix"},
    ]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh)
    return area


def _touch(area, *rel, content="x"):
    p = os.path.join(area, *rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(content)
    return p


# --------------------------------------------------------------------------- #
# precedence table, one guard at a time (first match wins)
# --------------------------------------------------------------------------- #

def test_confirm_outranks_everything(tmp_path):
    """Guard 1: a non-empty _reference/.proposed/ returns `confirm` (human gate) even when returns, notes and unfilled work all exist."""
    area = make_area(tmp_path, [{"slug": "a", "filled": False}])
    _touch(area, "_reference", ".proposed", "procedures.yaml")
    _touch(area, "_review", "returned", "doc.docx")
    _touch(area, "_review", "a.notes.yaml")
    _touch(area, "_sources", "new", "src.pdf")
    d = orchestrate.decide(area)
    assert d["action"] == "confirm"
    assert d["human_gate"] is True
    assert d["details"]["proposed_dir"] == os.path.join("_reference", ".proposed")


def test_proposed_dir_with_only_dotfiles_does_not_gate(tmp_path):
    """Guard 1 edge: .proposed/ containing only dotfiles (.gitkeep) counts as empty and does not trigger confirm."""
    area = make_area(tmp_path, [{"slug": "a", "filled": False}])
    _touch(area, "_reference", ".proposed", ".gitkeep")
    assert orchestrate.decide(area)["action"] == "fill"


def test_ingest_returns_beats_review_notes(tmp_path):
    """Guard 1.5: un-ingested files in _review/returned/ return `ingest_returns` before apply_review fires."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    _touch(area, "_review", "returned", "reviewed.docx")
    _touch(area, "_review", "a.notes.yaml")
    d = orchestrate.decide(area)
    assert d["action"] == "ingest_returns"
    assert d["details"]["files"] == [os.path.join("_review", "returned", "reviewed.docx")]


def test_apply_review_on_notes_excluding_unassigned(tmp_path):
    """Guard 2: *.notes.yaml (excluding _unassigned) returns `apply_review`, listing notes and surfacing the unassigned bucket."""
    area = make_area(tmp_path, [{"slug": "a", "filled": False}])
    _touch(area, "_review", "a.notes.yaml")
    _touch(area, "_review", "_unassigned.notes.yaml")
    d = orchestrate.decide(area)
    assert d["action"] == "apply_review"
    assert d["details"]["notes"] == [os.path.join("_review", "a.notes.yaml")]
    assert d["details"]["unassigned"] == os.path.join("_review", "_unassigned.notes.yaml")


def test_review_triage_when_only_unassigned_remains(tmp_path):
    """Guard 2b: only _unassigned.notes.yaml left returns `review_triage` as a human gate."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    _touch(area, "_review", "_unassigned.notes.yaml")
    d = orchestrate.decide(area)
    assert d["action"] == "review_triage"
    assert d["human_gate"] is True


def test_taxonomy_initial_no_manifest_with_sources(tmp_path):
    """Guard 3: no manifest + _sources/new/ non-empty returns taxonomy mode=initial."""
    area = tmp_path / "fresh"
    area.mkdir()
    _touch(str(area), "_sources", "new", "notes.txt")
    d = orchestrate.decide(str(area))
    assert d["action"] == "taxonomy"
    assert d["details"]["mode"] == "initial"


def test_done_when_no_manifest_and_no_sources(tmp_path):
    """No manifest and nothing to scope returns `done`."""
    area = tmp_path / "empty"
    area.mkdir()
    assert orchestrate.decide(str(area))["action"] == "done"


def test_fill_precedes_incremental_taxonomy(tmp_path):
    """Guard 4 before 5: a freshly-scaffolded area with unfilled skeletons AND sources still in _sources/new/ fills, not re-scopes."""
    area = make_area(tmp_path, [{"slug": "a", "filled": False}])
    _touch(area, "_sources", "new", "src.pdf")
    assert orchestrate.decide(area)["action"] == "fill"


def test_taxonomy_incremental_when_filled_and_new_sources(tmp_path):
    """Guard 5: manifest present, no unfilled, sources in _sources/new/ returns taxonomy mode=incremental."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    _touch(area, "_sources", "new", "src.pdf")
    d = orchestrate.decide(area)
    assert d["action"] == "taxonomy"
    assert d["details"]["mode"] == "incremental"


def test_done_when_manifest_has_no_procedures(tmp_path):
    """Steady state with an empty component list returns `done` (no procedures in manifest)."""
    area = make_area(tmp_path, [])
    d = orchestrate.decide(area)
    assert d["action"] == "done"
    assert d["reason"] == "no procedures in manifest"


# --------------------------------------------------------------------------- #
# M11 waves inside the fill guard
# --------------------------------------------------------------------------- #

def test_fill_no_upstream_returns_all_unfilled(tmp_path):
    """Fill without upstream hints returns every unfilled slug with no deferred/upstream_files keys."""
    area = make_area(tmp_path, [{"slug": "a", "filled": False},
                                {"slug": "b", "filled": False}])
    d = orchestrate.decide(area)
    assert d["action"] == "fill"
    assert d["details"]["unfilled"] == ["a", "b"]
    assert "deferred" not in d["details"]
    assert "upstream_files" not in d["details"]


def test_fill_wave_defers_downstream_of_unfilled_upstream(tmp_path):
    """Wave 1: only slugs whose upstreams are all filled are dispatched; downstream slugs land in details.deferred."""
    area = make_area(tmp_path, [
        {"slug": "a", "filled": False},
        {"slug": "b", "filled": False, "upstream": ["a"]},
        {"slug": "c", "filled": False, "upstream": ["b"]},
    ])
    d = orchestrate.decide(area)
    assert d["details"]["unfilled"] == ["a"]
    assert d["details"]["deferred"] == ["b", "c"]
    # a has no upstream, so no upstream_files at all this wave
    assert "upstream_files" not in d["details"]


def test_fill_wave_upstream_files_lists_only_filled_upstreams(tmp_path):
    """Wave 2: once the upstream is filled, its dependent joins the wave and upstream_files maps it to the FILLED fragment's relative path only."""
    area = make_area(tmp_path, [
        {"slug": "a", "filled": True},
        {"slug": "b", "filled": False, "upstream": ["a"]},
        {"slug": "c", "filled": False, "upstream": ["b"]},
    ])
    d = orchestrate.decide(area)
    assert d["details"]["unfilled"] == ["b"]
    assert d["details"]["deferred"] == ["c"]
    assert d["details"]["upstream_files"] == {"b": ["10_a.md"]}


def test_fill_cycle_falls_back_to_dispatch_all(tmp_path):
    """A cycle in upstream hints degrades to dispatching all unfilled slugs at once with a 'cycle' reason and no deferred."""
    area = make_area(tmp_path, [
        {"slug": "a", "filled": False, "upstream": ["b"]},
        {"slug": "b", "filled": False, "upstream": ["a"]},
    ])
    d = orchestrate.decide(area)
    assert d["action"] == "fill"
    assert sorted(d["details"]["unfilled"]) == ["a", "b"]
    assert "deferred" not in d["details"]
    assert "cycle" in d["reason"]


# --------------------------------------------------------------------------- #
# steady-state pipeline + emit round-trips
# --------------------------------------------------------------------------- #

def test_aggregate_fires_when_no_state_file(tmp_path):
    """Guard 6: a filled area with no .aggregate.json is stale and returns `aggregate`."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    assert orchestrate.decide(area)["action"] == "aggregate"


def test_emit_aggregate_roundtrip_and_procedure_edit_restales(tmp_path):
    """emit_aggregate writes what decide() reads: fresh aggregate moves past guard 6; editing a procedure makes it fire again."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    orchestrate.emit_aggregate(area, warnings=[])
    assert orchestrate.decide(area)["action"] == "reconcile"
    with open(os.path.join(area, "10_a.md"), "a", encoding="utf-8") as fh:
        fh.write("\nmore\n")
    assert orchestrate.decide(area)["action"] == "aggregate"


def test_registry_edit_restales_aggregate(tmp_path):
    """Guard 6, registry arm: editing a _reference/*.yaml after emit_aggregate
    (the registry top-up loop) makes decide() return `aggregate` again."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    _touch(area, "_reference", "systems.yaml", content="systems: []\n")
    orchestrate.emit_aggregate(area, warnings=[])
    assert orchestrate.decide(area)["action"] == "reconcile"
    _touch(area, "_reference", "systems.yaml",
           content="systems:\n  - slug: sap\n    name: SAP\n")
    assert orchestrate.decide(area)["action"] == "aggregate"


def test_checkpoint_seeds_gitignore_and_skips_signal_files(tmp_path):
    """checkpoint in a fresh git repo seeds the area .gitignore so signal
    files and _review/kits/ stay out of the commit, while fragments (and
    sources) are committed."""
    import subprocess
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    _touch(area, "_sources", "new", "transcript.txt", content="client words")
    _touch(area, ".aggregate.json", content="{}")
    _touch(area, "_review", "kits", "p", "README.md", content="kit")
    subprocess.run(["git", "init", "-q", area], check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "-C", area, "config", k, v], check=True)
    res = orchestrate.checkpoint(area, "aggregate")
    assert res["committed"] is True
    tracked = subprocess.run(["git", "-C", area, "ls-files"],
                             capture_output=True, text=True).stdout.split()
    assert "10_a.md" in tracked
    assert "_sources/new/transcript.txt" in tracked
    assert ".gitignore" in tracked
    assert ".aggregate.json" not in tracked
    assert not any(t.startswith("_review/kits/") for t in tracked)


def test_accept_review_clears_the_review_gate(tmp_path):
    """orchestrate accept flips awaiting_review so a fully-walked area moves
    from the `review` gate to `done`; with nothing rendered it no-ops."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    assert orchestrate.accept_review(area)["accepted"] is False
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=True)
    scope_delta.commit(area, "dependencies")
    scope_delta.commit(area, "raci")
    orchestrate.emit_render(area, "out.docx", awaiting_review=True)
    assert orchestrate.decide(area)["action"] == "review"
    res = orchestrate.accept_review(area)
    assert res["accepted"] is True and res["docx"] == "out.docx"
    assert orchestrate.decide(area)["action"] == "done"


def test_registry_topup_gate_on_aggregate_warnings(tmp_path):
    """Guard 7: unmatched-mention warnings recorded by emit_aggregate return `registry_topup` (human gate) with the warnings."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    orchestrate.emit_aggregate(area, warnings=["unmatched system: sap"])
    d = orchestrate.decide(area)
    assert d["action"] == "registry_topup"
    assert d["human_gate"] is True
    assert d["details"]["warnings"] == ["unmatched system: sap"]


def test_reconcile_not_clean_fires_reconcile(tmp_path):
    """Guard 8: a .reconcile.json with clean=false keeps returning `reconcile` even when its basis is current."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=False)
    assert orchestrate.decide(area)["action"] == "reconcile"


def test_full_walk_to_done(tmp_path):
    """Round-trip: aggregate -> reconcile -> draft_ready -> synthesize (first-run delta) -> render -> review -> done, each emit moving decide() forward."""
    area = _declare_agent_views(make_area(tmp_path, [{"slug": "a", "filled": True}]))
    orchestrate.emit_aggregate(area, warnings=[])
    assert orchestrate.decide(area)["action"] == "reconcile"
    orchestrate.emit_reconcile(area, clean=True)

    # guard 8.5 (M17): the draft-ready gate stands between reconcile and the
    # first spend — the human accepts the verbs and the nouns once per pass.
    assert orchestrate.decide(area)["action"] == "draft_ready"
    orchestrate.accept_draft(area)

    # guard 9: no scope_delta baselines yet => both kinds stale => synthesize
    d = orchestrate.decide(area)
    assert d["action"] == "synthesize"
    assert sorted(d["details"]["stale_kinds"]) == ["dependencies", "raci"]

    scope_delta.commit(area, "dependencies")
    scope_delta.commit(area, "raci")
    assert orchestrate.decide(area)["action"] == "render"

    orchestrate.emit_render(area, "out/area.docx", awaiting_review=True)
    d = orchestrate.decide(area)
    assert d["action"] == "review"
    assert d["human_gate"] is True
    assert d["details"]["docx"] == "out/area.docx"

    orchestrate.emit_render(area, "out/area.docx", awaiting_review=False)
    d = orchestrate.decide(area)
    assert d["action"] == "done"
    assert d["details"]["docx"] == "out/area.docx"


def test_synthesize_on_pending_placeholder(tmp_path):
    """Guard 9: an agent-owned derived file carrying '_Pending synthesis' is reported in details.pending."""
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    # add an agent-owned derived component
    mpath = os.path.join(area, "manifest.json")
    with open(mpath, encoding="utf-8") as fh:
        m = json.load(fh)
    m["components"].append({"file": "82_dependencies.md", "role": "derived",
                            "derived_kind": "dependencies", "writer": "agent",
                            "heading": "Deps", "order": 8200})
    with open(mpath, "w", encoding="utf-8") as fh:
        json.dump(m, fh)
    _touch(area, "82_dependencies.md", content="## Deps\n\n> _Pending synthesis._\n")
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=True)
    scope_delta.commit(area, "dependencies")
    scope_delta.commit(area, "raci")
    orchestrate.accept_draft(area)      # M17 guard 8.5 precedes the first spend
    d = orchestrate.decide(area)
    assert d["action"] == "synthesize"
    assert d["details"]["pending"] == ["82_dependencies.md"]


# --------------------------------------------------------------------------- #
# checkpoint — the durable-state git commit the driver runs after each stage
# --------------------------------------------------------------------------- #

def _git(cwd, *args):
    import subprocess
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, check=True)


def _init_repo(tmp_path):
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "T")
    return tmp_path


def test_checkpoint_commits_area_changes(tmp_path):
    """A dirty area commits with the consult(<area>): <stage> message; a second
    call with no changes is a no-op."""
    _init_repo(tmp_path)
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])

    out = orchestrate.checkpoint(area, "fill")
    assert out["committed"] is True
    msg = _git(tmp_path, "log", "-1", "--pretty=%s").stdout.strip()
    assert msg == "consult(%s): fill" % os.path.basename(area)
    assert _git(tmp_path, "status", "--porcelain").stdout.strip() == ""

    again = orchestrate.checkpoint(area, "fill")
    assert again["committed"] is False
    assert again["reason"] == "nothing to commit"


def test_checkpoint_scopes_to_area_pathspec(tmp_path):
    """Staged work OUTSIDE the area is never swept into a checkpoint commit."""
    _init_repo(tmp_path)
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    outside = tmp_path / "unrelated.txt"
    outside.write_text("keep me out\n", encoding="utf-8")
    _git(tmp_path, "add", "unrelated.txt")

    out = orchestrate.checkpoint(area, "aggregate")
    assert out["committed"] is True
    committed = _git(tmp_path, "show", "--name-only", "--pretty=",
                     "HEAD").stdout
    assert "unrelated.txt" not in committed
    # the unrelated file is still staged, untouched
    assert "unrelated.txt" in _git(tmp_path, "diff", "--cached",
                                   "--name-only").stdout


def test_checkpoint_noop_outside_git(tmp_path):
    """An area outside any git work tree is a reported no-op, not an error."""
    import subprocess
    area = make_area(tmp_path, [{"slug": "a", "filled": True}])
    env_probe = subprocess.run(
        ["git", "-C", area, "rev-parse", "--is-inside-work-tree"],
        capture_output=True, text=True)
    if env_probe.returncode == 0:  # pragma: no cover - tmp under a repo
        import pytest
        pytest.skip("tmp_path unexpectedly inside a git work tree")
    out = orchestrate.checkpoint(area, "fill")
    assert out["committed"] is False
    assert "not inside a git work tree" in out["reason"]
