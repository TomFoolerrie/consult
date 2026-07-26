"""Tests for M18 — advisor honesty (the resolvable-action invariant).

One test per acceptance bullet in docs/M18-advisor-honesty.md:

  * an orphan notes file gates at `review_triage` naming the slug, never
    `apply_review`; on an unscoped area with sources waiting, `taxonomy` still
    wins (F1)
  * retirement with dangling refs only in `82` → `synthesize`, then reconcile
    passes; refs in a procedure fragment → `unresolvable` naming file and
    reference (F8), driven through the REAL reconcile.py so the failing-files
    plumbing is pinned end to end
  * a nonexistent area returns `error`, and `next` exits nonzero (F3)
  * a manifest slug with no file names the slug and the file (F4)
  * one kind raising in guard 9 does not suppress another kind's staleness (F6)
  * a duplicate slug keeps both files in the change signal, and an
    old-shape `.aggregate.json` degrades to exactly one aggregate pass (F5)
  * `next` is read-only: `git status` clean after any call
  * `unresolvable` is a resting gate, not an error: human_gate + exit 0
"""
import json
import os
import subprocess

import pytest

import orchestrate
import reconcile
import scope_delta


SYSTEMS_YAML = "systems:\n  - slug: netsuite\n    name: NetSuite\n"
ROLES_YAML = "roles:\n  - slug: controller\n    name: Controller\n"
SOURCES_YAML = ("sources:\n- id: SRC-001\n  file: _sources/processed/i.md\n"
                "  touches:\n  - bank-rec\n  state: processed\n")
DEP_MARKER = "<!-- derived: dependencies; writer: agent -->"

FILLED = "## Proc\n\nReal drafted content.\n"
UNFILLED = "## Proc\n\n<!-- unfilled -->\n\nTBD.\n"


def proc(slug, fname=None, order=10):
    return {"file": fname or f"10_{slug}.md", "role": "procedure", "slug": slug,
            "heading": slug.title(), "l2": "ops", "order": order}


def make_area(tmp_path, name, components=None, files=None, manifest=True):
    """A synthetic area: manifest.json plus whatever `files` names."""
    folder = tmp_path / name
    folder.mkdir(parents=True, exist_ok=True)
    if manifest:
        man = {"schema": "consult-mvp-manifest/v1", "area": name, "l1": "fin",
               "l2_order": ["ops"], "title": "T", "subtitle": "S",
               "components": list(components or [])}
        (folder / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
    for rel, content in (files or {}).items():
        p = folder / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return str(folder)


def drafted(tmp_path, name="cash", frag_extra="", dep_ref="bank-rec"):
    """An area that passes every reconcile check: one real procedure fragment
    (citation, callout, consult-meta) plus the agent-owned dependencies view."""
    fragment = f"""## Bank Rec

### A. Process Overview

The Controller reconciles cash against the statement. (SRC-001)
{frag_extra}

### E. Step-by-Step Procedure

#### Step 1: Export

Export the statement from the portal.

> **CONTROL — CTRL-001:** Controller signs off on the reconciliation.

```consult-meta
systems:
  - netsuite
roles:
  - controller
```
"""
    comps = [proc("bank-rec"),
             {"file": "82_dependencies.md", "role": "derived", "order": 82,
              "derived_kind": "dependencies", "writer": "agent",
              "heading": "Dependencies"}]
    return make_area(tmp_path, name, comps, {
        "10_bank-rec.md": fragment,
        "82_dependencies.md": f"## Dependencies\n\n{DEP_MARKER}\n\n"
                              f"The rec depends on [[{dep_ref}]].\n",
        "_reference/systems.yaml": SYSTEMS_YAML,
        "_reference/roles.yaml": ROLES_YAML,
        "_reference/sources.yaml": SOURCES_YAML,
    })


# --------------------------------------------------------------------------- #
# F1 — guard 2 partitioned by manifest slug
# --------------------------------------------------------------------------- #

def test_orphan_note_gates_at_review_triage_naming_the_slug(tmp_path):
    """A note for a slug the manifest does not carry is `review_triage`, naming
    the orphaned slug and both resolutions — never `apply_review` (a drafter
    with no procedure to update; notes archive only on success)."""
    area = make_area(tmp_path, "a", [proc("alpha")],
                     {"10_alpha.md": FILLED,
                      "_review/ghost.notes.yaml": "items: []\n"})
    d = orchestrate.decide(area)
    assert d["action"] == "review_triage"
    assert d["human_gate"] is True
    assert d["details"]["orphan_slugs"] == ["ghost"]
    assert d["details"]["orphan_notes"] == [os.path.join("_review",
                                                         "ghost.notes.yaml")]
    joined = " ".join(d["details"]["resolutions"])
    assert "restore the procedure" in joined and "archive the note" in joined


def test_live_note_still_applies_and_surfaces_orphans_alongside(tmp_path):
    """A note naming a live slug still dispatches `apply_review` (unchanged
    behaviour); a coexisting orphan rides along in details rather than
    hijacking the action, and gates on the next call once the live note is
    archived."""
    area = make_area(tmp_path, "a", [proc("alpha")],
                     {"10_alpha.md": FILLED,
                      "_review/alpha.notes.yaml": "items: []\n",
                      "_review/ghost.notes.yaml": "items: []\n"})
    d = orchestrate.decide(area)
    assert d["action"] == "apply_review"
    assert d["details"]["notes"] == [os.path.join("_review", "alpha.notes.yaml")]
    assert d["details"]["orphan_notes"] == [os.path.join("_review",
                                                         "ghost.notes.yaml")]

    os.remove(os.path.join(area, "_review", "alpha.notes.yaml"))  # drafter ran
    assert orchestrate.decide(area)["action"] == "review_triage"


def test_stray_note_cannot_stop_a_new_area_being_scoped(tmp_path):
    """The worst F1 instance: one stray notes file on a brand-new area used to
    divert `taxonomy` → `apply_review` forever. Scoping wins — nothing can be
    applied to an area with no manifest."""
    area = make_area(tmp_path, "fresh", None,
                     {"_sources/new/transcript.md": "client words",
                      "_review/ghost.notes.yaml": "items: []\n"}, manifest=False)
    d = orchestrate.decide(area)
    assert d["action"] == "taxonomy"
    assert d["details"]["mode"] == "initial"


def test_unscoped_area_with_notes_and_nothing_to_scope_triages(tmp_path):
    """No manifest, no sources, but review notes on disk: `review_triage`, not
    the reassuring `done` (there is nothing to scope AND nothing to apply)."""
    area = make_area(tmp_path, "fresh", None,
                     {"_review/ghost.notes.yaml": "items: []\n"}, manifest=False)
    d = orchestrate.decide(area)
    assert d["action"] == "review_triage"
    assert d["human_gate"] is True
    assert d["details"]["orphan_slugs"] == ["ghost"]


def test_unscoped_area_with_only_unassigned_notes_triages(tmp_path):
    """The _unassigned bucket on an unscoped area gates too, with a message
    that says why (no procedure exists to attribute the items to)."""
    area = make_area(tmp_path, "fresh", None,
                     {"_review/_unassigned.notes.yaml": "items: []\n"},
                     manifest=False)
    d = orchestrate.decide(area)
    assert d["action"] == "review_triage"
    assert "unscoped" in d["reason"]


def test_notes_partition_is_reported_by_review_notes(tmp_path):
    """review_notes() returns (applicable, orphaned) — the manifest is the only
    authority on which notes a drafter can consume."""
    area = make_area(tmp_path, "a", [proc("alpha")],
                     {"10_alpha.md": FILLED,
                      "_review/alpha.notes.yaml": "items: []\n",
                      "_review/ghost.notes.yaml": "items: []\n",
                      "_review/_unassigned.notes.yaml": "items: []\n"})
    live, orphans = orchestrate.AreaState(area).review_notes()
    assert [os.path.basename(p) for p in live] == ["alpha.notes.yaml"]
    assert [os.path.basename(p) for p in orphans] == ["ghost.notes.yaml"]


# --------------------------------------------------------------------------- #
# F8 — the verifier must not precede its producer (through real reconcile.py)
# --------------------------------------------------------------------------- #

def test_retirement_in_agent_view_synthesizes_then_reconciles_clean(tmp_path):
    """Dangling `[[slug]]` only in the agent-owned view: reconcile records the
    failure against 82, the advisor runs the PRODUCER first, and reconcile then
    passes at the new basis."""
    area = drafted(tmp_path, dep_ref="retired-proc")
    orchestrate.emit_aggregate(area, warnings=[])
    assert reconcile.reconcile(area) == 1

    sig = json.loads(open(os.path.join(area, ".reconcile.json")).read())
    assert sig["clean"] is False
    assert sig["failing_files"] == ["82_dependencies.md"]

    d = orchestrate.decide(area)
    assert d["action"] == "synthesize"
    assert d["details"]["failing_files"] == ["82_dependencies.md"]
    assert sorted(d["details"]["stale_kinds"]) == ["dependencies", "raci"]

    # the synthesis agent regenerates the view; the driver rebaselines the kinds
    with open(os.path.join(area, "82_dependencies.md"), "w",
              encoding="utf-8") as fh:
        fh.write(f"## Dependencies\n\n{DEP_MARKER}\n\nDepends on [[bank-rec]].\n")
    scope_delta.commit(area, "dependencies")
    scope_delta.commit(area, "raci")

    assert orchestrate.decide(area)["action"] == "reconcile"
    assert reconcile.reconcile(area) == 0
    # M17 guard 8.5: the draft-ready gate holds back the first spend of the pass
    # (here `render`) until the draft is accepted — tests/test_stage_gates.py.
    orchestrate.accept_draft(area)
    assert orchestrate.decide(area)["action"] == "render"


def test_retirement_in_fragment_is_unresolvable_naming_file_and_reference(tmp_path):
    """Dangling `[[slug]]` in drafter-owned prose: no stage regenerates it, so
    the ladder rests at `unresolvable`, naming the fragment AND the reference."""
    area = drafted(tmp_path, frag_extra="\nSee also [[retired-proc]] for context.\n")
    orchestrate.emit_aggregate(area, warnings=[])
    assert reconcile.reconcile(area) == 1
    assert json.loads(open(os.path.join(area, ".reconcile.json")).read()
                      )["failing_files"] == ["10_bank-rec.md"]

    d = orchestrate.decide(area)
    assert d["action"] == "unresolvable"
    assert d["human_gate"] is True
    assert d["details"]["failing_files"] == ["10_bank-rec.md"]
    assert d["details"]["dangling_refs"] == {"10_bank-rec.md": ["retired-proc"]}
    assert "reconcile" in d["details"]["human_action"]

    # and it stays a resting gate: repeated calls never dispatch a stage
    assert orchestrate.decide(area)["action"] == "unresolvable"


def test_agent_view_failure_with_nothing_stale_is_unresolvable(tmp_path):
    """Failures confined to an agent-owned view, but the change signal marks
    nothing stale: `synthesize` would dispatch an EMPTY work order, so the
    honest answer is the gate."""
    area = drafted(tmp_path, dep_ref="retired-proc")
    orchestrate.emit_aggregate(area, warnings=[])
    scope_delta.commit(area, "dependencies")
    scope_delta.commit(area, "raci")
    assert reconcile.reconcile(area) == 1

    d = orchestrate.decide(area)
    assert d["action"] == "unresolvable"
    assert d["details"]["failing_files"] == ["82_dependencies.md"]
    assert "empty work order" in d["details"]["why_no_stage"]


def test_stale_basis_still_routes_to_reconcile(tmp_path):
    """Only failures recorded at the CURRENT basis are trusted: after any edit
    the area has moved, so re-running the verifier really can change the
    answer and `reconcile` is the honest action."""
    area = drafted(tmp_path, frag_extra="\nSee also [[retired-proc]].\n")
    orchestrate.emit_aggregate(area, warnings=[])
    assert reconcile.reconcile(area) == 1
    assert orchestrate.decide(area)["action"] == "unresolvable"

    # human fixes the fragment: basis moves, the recorded failure is history
    with open(os.path.join(area, "10_bank-rec.md"), encoding="utf-8") as fh:
        text = fh.read().replace("See also [[retired-proc]].", "")
    with open(os.path.join(area, "10_bank-rec.md"), "w", encoding="utf-8") as fh:
        fh.write(text)
    assert orchestrate.decide(area)["action"] == "aggregate"   # content changed
    orchestrate.emit_aggregate(area, warnings=[])
    assert orchestrate.decide(area)["action"] == "reconcile"


def test_failing_files_absent_keeps_pre_m18_behaviour(tmp_path):
    """emit_reconcile omits `failing_files` when not recorded, and guard 8 then
    behaves exactly as before M18 — an older signal file cannot mis-route."""
    area = drafted(tmp_path)
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=False)
    sig = json.loads(open(os.path.join(area, ".reconcile.json")).read())
    assert "failing_files" not in sig
    assert orchestrate.decide(area)["action"] == "reconcile"


def test_unknown_owner_failures_keep_routing_to_reconcile(tmp_path):
    """A failure recorded against something outside the drafter/agent split —
    manifest.json, a python-owned view, `_reference/sources.yaml` — is NOT
    gated: those causes can be fixed outside the basis (a registry edit
    re-stales aggregate), so the verifier stays the action."""
    area = drafted(tmp_path)
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=False,
                              failing_files=["_reference/sources.yaml"])
    assert orchestrate.decide(area)["action"] == "reconcile"


# --------------------------------------------------------------------------- #
# F3 — a missing area is not `done`
# --------------------------------------------------------------------------- #

def test_nonexistent_area_is_an_error_not_done(tmp_path):
    """The typo case: `error`, naming the folder it looked for. Not a gate — a
    gate rests, and there is nothing here to rest on."""
    d = orchestrate.decide(str(tmp_path / "no-such-area"))
    assert d["action"] == "error"
    assert d["human_gate"] is False
    assert "does not exist" in d["reason"]
    assert d["details"]["missing_folder"].endswith("no-such-area")


def test_next_exits_nonzero_for_a_missing_area(tmp_path, capsys, monkeypatch):
    """`next --area <typo>` exits 2 with the reason on stdout, so the driver
    stops instead of reading `done` as progress."""
    monkeypatch.chdir(tmp_path)      # sandbox resolve_area's components/ fallback
    rc = orchestrate.main(["next", "--area", "treasry"])
    out = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert out["action"] == "error"
    assert out["details"]["missing_folder"] == os.path.join("components", "treasry")


def test_existing_but_empty_area_still_reports_done(tmp_path):
    """The other half of the distinction: an area that EXISTS with nothing to
    do is still `done` and exit 0."""
    area = make_area(tmp_path, "empty", None, manifest=False)
    assert orchestrate.decide(area)["action"] == "done"
    assert orchestrate.main(["next", "--area", area]) == 0


# --------------------------------------------------------------------------- #
# F4 — a manifest slug with no fragment file
# --------------------------------------------------------------------------- #

def test_missing_fragment_names_the_slug_and_the_file(tmp_path):
    """Was `aggregate` / "content changed" (the wrong cause, forever). Now a
    gate naming slug and file, with the resolutions that exist."""
    area = make_area(tmp_path, "a", [proc("alpha"), proc("beta", order=20)],
                     {"10_alpha.md": FILLED})
    d = orchestrate.decide(area)
    assert d["action"] == "unresolvable"
    assert d["human_gate"] is True
    assert d["details"]["missing_procedures"] == [{"slug": "beta",
                                                  "file": "10_beta.md"}]
    assert "'beta'" in d["details"]["state"] and "10_beta.md" in d["details"]["state"]
    assert "scaffold" in d["details"]["human_action"]


def test_missing_fragment_does_not_preempt_fill(tmp_path):
    """Ordering: real drafting work still goes first. `fill` dispatches the
    slugs that DO have skeletons; the gate is what remains afterwards."""
    area = make_area(tmp_path, "a",
                     [proc("alpha"), proc("beta", order=20)],
                     {"10_alpha.md": UNFILLED})
    assert orchestrate.decide(area)["action"] == "fill"


# --------------------------------------------------------------------------- #
# F6 — guard 9 accumulates staleness per kind
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize("boom,expected", [("raci", ["dependencies"]),
                                           ("dependencies", ["raci"])])
def test_one_kind_raising_does_not_erase_another(tmp_path, monkeypatch,
                                                 boom, expected):
    """`stale_kinds = []` inside the old `except` discarded kinds already found
    stale (and abandoned the loop). Each kind is now independent, in either
    order."""
    area = make_area(tmp_path, "a", [proc("alpha")], {"10_alpha.md": FILLED})
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=True)

    def fake(folder, kind):
        if kind == boom:
            raise RuntimeError("delta engine unavailable for %s" % kind)
        return ["alpha"]

    monkeypatch.setattr(scope_delta, "changed_procedure_slugs", fake)
    orchestrate.accept_draft(area)   # M17 guard 8.5 precedes guard 9
    d = orchestrate.decide(area)
    assert d["action"] == "synthesize"
    assert d["details"]["stale_kinds"] == expected


def test_both_kinds_raising_falls_back_to_pending_only(tmp_path, monkeypatch):
    """With the delta engine dead for every kind, guard 9 degrades to
    "synthesize only if a pending placeholder remains" — it does not invent
    staleness, and it does not block the walk."""
    area = make_area(tmp_path, "a", [proc("alpha")], {"10_alpha.md": FILLED})
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=True)

    def boom(folder, kind):
        raise RuntimeError("dead")

    monkeypatch.setattr(scope_delta, "changed_procedure_slugs", boom)
    orchestrate.accept_draft(area)   # M17 guard 8.5 precedes the first spend
    assert orchestrate.decide(area)["action"] == "render"


# --------------------------------------------------------------------------- #
# F5 — no file's hash can vanish from the change signal
# --------------------------------------------------------------------------- #

def test_duplicate_slug_keeps_both_files_in_the_change_signal(tmp_path):
    """Two components over one slug: both files are hashed (per file inside the
    slug), so an edit to the SHADOWED file re-stales guard 6. The old dict
    comprehension dropped it and guard 6 went blind."""
    area = make_area(tmp_path, "a",
                     [proc("alpha"), proc("alpha", "10_alpha_dup.md", order=20)],
                     {"10_alpha.md": FILLED, "10_alpha_dup.md": FILLED})
    hashes = orchestrate.AreaState(area).proc_hashes()
    assert sorted(hashes["alpha"]) == ["10_alpha.md", "10_alpha_dup.md"]
    assert len(set(hashes["alpha"].values())) == 1     # same content, same sha

    orchestrate.emit_aggregate(area, warnings=[])
    assert orchestrate.decide(area)["action"] == "reconcile"
    with open(os.path.join(area, "10_alpha_dup.md"), "a", encoding="utf-8") as fh:
        fh.write("\nan edit only the shadowed file carries\n")
    assert orchestrate.decide(area)["action"] == "aggregate"


def test_old_shape_aggregate_signal_degrades_to_one_pass(tmp_path):
    """A `.aggregate.json` written before M18 ({slug: sha}) reads as stale
    exactly once: one harmless aggregate pass rewrites it in the new shape and
    the walk continues. No loop, no special-casing."""
    area = make_area(tmp_path, "a", [proc("alpha")], {"10_alpha.md": FILLED})
    st = orchestrate.AreaState(area)
    old = {"proc_hashes": {"alpha": list(st.proc_hashes()["alpha"].values())[0]},
           "registry_hash": st.registry_hash(), "warnings": []}
    with open(os.path.join(area, ".aggregate.json"), "w", encoding="utf-8") as fh:
        json.dump(old, fh)

    assert orchestrate.decide(area)["action"] == "aggregate"    # stale once
    orchestrate.emit_aggregate(area, warnings=[])               # the one pass
    assert orchestrate.decide(area)["action"] == "reconcile"    # and it sticks
    signal = json.loads(open(os.path.join(area, ".aggregate.json")).read())
    assert signal["proc_hashes"]["alpha"] == {"10_alpha.md":
                                              list(st.proc_hashes()["alpha"].values())[0]}


# --------------------------------------------------------------------------- #
# The advisor never writes
# --------------------------------------------------------------------------- #

def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, check=True)


@pytest.mark.parametrize("shape", ["fresh", "drafted", "gated"])
def test_next_is_read_only_git_diff_empty(tmp_path, capsys, shape):
    """M18 acceptance, asserted rather than asserted-in-prose: `git status`
    (tracked AND untracked) is empty after `next` on every shape of area,
    including the ones whose guards read scope_delta and the signal files."""
    if shape == "fresh":
        area = make_area(tmp_path, "fresh", None,
                         {"_sources/new/t.md": "words"}, manifest=False)
    elif shape == "drafted":
        area = drafted(tmp_path)
        orchestrate.emit_aggregate(area, warnings=[])
        reconcile.reconcile(area)
        capsys.readouterr()
    else:
        area = drafted(tmp_path, frag_extra="\nSee [[retired-proc]].\n")
        orchestrate.emit_aggregate(area, warnings=[])
        reconcile.reconcile(area)
        capsys.readouterr()

    _git(area, "init", "-q")
    _git(area, "config", "user.email", "t@example.com")
    _git(area, "config", "user.name", "T")
    _git(area, "add", "-A")
    _git(area, "commit", "-q", "-m", "state")

    for _ in range(3):
        assert orchestrate.main(["next", "--area", area]) in (0, 2)
    capsys.readouterr()
    assert _git(area, "status", "--porcelain").stdout == ""


def test_unresolvable_is_a_resting_gate_not_an_error(tmp_path, capsys):
    """The gate exits 0 (a resting state, like `review`), carries
    human_gate=True, and always answers all three questions: what state, why no
    stage, what the human does."""
    area = make_area(tmp_path, "a", [proc("alpha"), proc("beta", order=20)],
                     {"10_alpha.md": FILLED})
    rc = orchestrate.main(["next", "--area", area])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["action"] == "unresolvable"
    assert out["human_gate"] is True
    assert set(("state", "why_no_stage", "human_action")) <= set(out["details"])
