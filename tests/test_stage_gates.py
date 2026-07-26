"""Tests for M17 — the draft-ready gate (build order item 1).

One test per acceptance bullet the gate owns; items 2 (consolidate visibility,
needs M12) and 3 (sticky holds, needs M13) are not built and are not tested here
beyond the gate's forward-compatible `consolidate` slot.

  * a freshly drafted+reconciled area returns `draft_ready`, not `synthesize`,
    with `.render.json` absent, and the gate names its three answers
  * `accept-draft` → the next call returns `synthesize`
  * `synthesize` rewriting `82`/`84` does NOT re-open the gate — ONE accept per
    pass, driven through the real emit_* signals rather than mocks (the keying
    bug docs/M17 calls out: draft_basis is procedures+registry, not basis_hash)
  * touching a fragment re-opens it; editing `_reference/*.yaml` re-opens it
  * `accept-draft` on an area that is not at the gate is a no-op with a reason,
    and writes nothing
  * the M18 guard-8 branches (reconcile NOT clean) bypass the gate untouched
  * `decide()` stays read-only at and around the gate: git status clean
  * `.draft_ready.json` is in the seeded area .gitignore, so a checkpoint never
    commits it

The gate fires only when a spend is actually outstanding (`synthesize` or
`render`) — see test_gate_does_not_preempt_the_review_gate for why.
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
RACI_MARKER = "<!-- derived: raci; writer: agent -->"
PENDING = "> _Pending synthesis._"

FILLED = "## Proc\n\nReal drafted content.\n"
UNFILLED = "## Proc\n\n<!-- unfilled -->\n\nTBD.\n"

FRAGMENT = """## Bank Rec

### A. Process Overview

The Controller reconciles cash against the statement. (SRC-001)

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


def proc(slug, fname=None, order=10):
    return {"file": fname or f"10_{slug}.md", "role": "procedure", "slug": slug,
            "heading": slug.title(), "l2": "ops", "order": order}


def derived(fname, kind, order):
    return {"file": fname, "role": "derived", "order": order,
            "derived_kind": kind, "writer": "agent",
            "heading": kind.title()}


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


def simple(tmp_path, name="cash", body=FILLED):
    """One filled procedure and a registry — the smallest area that can reach
    the gate. No derived components, so `synthesize`'s only work is the
    first-run delta and reconcile is driven by emit_reconcile."""
    return make_area(tmp_path, name, [proc("bank-rec")],
                     {"10_bank-rec.md": body,
                      "_reference/systems.yaml": SYSTEMS_YAML})


def two_view_area(tmp_path, name="cash"):
    """A reconcile-valid area with BOTH agent-owned views still carrying the M3
    pending placeholder — the shape the one-accept-per-pass test needs, because
    `synthesize` really does rewrite two files here."""
    return make_area(
        tmp_path, name,
        [proc("bank-rec"), derived("82_dependencies.md", "dependencies", 82),
         derived("84_raci.md", "raci", 84)],
        {"10_bank-rec.md": FRAGMENT,
         "82_dependencies.md": f"## Dependencies\n\n{DEP_MARKER}\n\n{PENDING}\n",
         "84_raci.md": f"## Raci\n\n{RACI_MARKER}\n\n{PENDING}\n",
         "_reference/systems.yaml": SYSTEMS_YAML,
         "_reference/roles.yaml": ROLES_YAML,
         "_reference/sources.yaml": SOURCES_YAML})


def flag(folder):
    path = os.path.join(folder, ".draft_ready.json")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def walk_to_gate(folder):
    """aggregate + a clean reconcile — the two free stages below the gate."""
    orchestrate.emit_aggregate(folder, warnings=[])
    orchestrate.emit_reconcile(folder, clean=True, failing_files=[])
    return orchestrate.decide(folder)


# --------------------------------------------------------------------------- #
# The gate opens the pass
# --------------------------------------------------------------------------- #

def test_freshly_drafted_area_gates_instead_of_synthesizing(tmp_path):
    """Acceptance bullet 1: a filled, aggregated, reconciled area returns the
    `draft_ready` human gate — not `synthesize` — with `.render.json` absent."""
    area = simple(tmp_path)
    d = walk_to_gate(area)
    assert d["action"] == "draft_ready"
    assert d["human_gate"] is True
    assert not os.path.exists(os.path.join(area, ".render.json"))
    assert d["details"]["draft_basis"] == orchestrate.AreaState(area).draft_basis()
    # the gate is the LAST free stop: the spend it is holding back is named
    assert d["details"]["would_spend"] == "synthesize"


def test_the_gate_names_its_three_answers_with_commands(tmp_path):
    """The gate's details carry read / consolidate / accept: the subset render
    (all procedure slugs, no signal write), the M12 slot, and the exact
    accept-draft command."""
    area = make_area(tmp_path, "cash", [proc("bank-rec"), proc("ap", order=20)],
                     {"10_bank-rec.md": FILLED, "10_ap.md": FILLED,
                      "_reference/systems.yaml": SYSTEMS_YAML})
    d = walk_to_gate(area)
    answers = {a["name"]: a for a in d["details"]["answers"]}
    assert sorted(answers) == ["accept", "consolidate", "read"]

    read = answers["read"]
    assert "render.py" in read["command"]
    assert "--slugs ap,bank-rec" in read["command"]      # every live slug, sorted
    assert ".render.json" in read["note"]                # says it writes no signal
    assert read["cost"] == "free"

    # M12 is not built: the slot exists (stable gate shape) and records no pass
    assert answers["consolidate"]["consolidated_at_basis"] is None

    assert answers["accept"]["command"] == (
        "scripts/orchestrate.py accept-draft --area %s" % area)


def test_accept_draft_opens_the_gate_to_synthesize(tmp_path):
    """Acceptance bullet 2: accept-draft → the next call returns `synthesize`.
    The flag records the draft basis and nothing else."""
    area = simple(tmp_path)
    assert walk_to_gate(area)["action"] == "draft_ready"

    res = orchestrate.accept_draft(area)
    assert res["accepted"] is True
    assert res["next_action"] == "synthesize"
    assert flag(area) == {"accepted": True,
                         "draft_basis": orchestrate.AreaState(area).draft_basis()}

    d = orchestrate.decide(area)
    assert d["action"] == "synthesize"
    assert d["human_gate"] is False


def test_gate_holds_back_render_too_when_synthesis_is_current(tmp_path):
    """The gate guards `render` as well as `synthesize`: render costs no tokens
    but starts a human cycle, which M17 calls the scarcer resource. With the
    scope_delta baselines committed the only spend left is render, and the gate
    still fires — then accept lets it through."""
    area = simple(tmp_path)
    scope_delta.commit(area, "dependencies")
    scope_delta.commit(area, "raci")
    d = walk_to_gate(area)
    assert d["action"] == "draft_ready"
    assert d["details"]["would_spend"] == "render"
    orchestrate.accept_draft(area)
    assert orchestrate.decide(area)["action"] == "render"


# --------------------------------------------------------------------------- #
# One accept per pass — the keying decision, driven through real signals
# --------------------------------------------------------------------------- #

def test_synthesize_rewriting_the_views_does_not_reopen_the_gate(tmp_path,
                                                                capsys):
    """Acceptance bullet 3, the bug the first revision of M17 had: keying the
    flag on basis_hash() made `synthesize` rewriting 82/84 re-open a gate the
    human had just accepted, so every pass demanded two accepts for one
    decision. Walked end to end through the REAL reconcile + emit_* signals:
    gate → accept → synthesize → (both views rewritten, baselines committed) →
    reconcile → render → review, with the gate never re-appearing."""
    area = two_view_area(tmp_path)
    orchestrate.emit_aggregate(area, warnings=[])
    assert reconcile.reconcile(area) == 0
    capsys.readouterr()

    d = orchestrate.decide(area)
    assert d["action"] == "draft_ready"
    accepted_basis = d["details"]["draft_basis"]
    before = orchestrate.AreaState(area).basis_hash()
    orchestrate.accept_draft(area)

    d = orchestrate.decide(area)
    assert d["action"] == "synthesize"
    assert sorted(d["details"]["pending"]) == ["82_dependencies.md", "84_raci.md"]

    # the two judgment agents write their views; the driver rebaselines the kinds
    for fname, marker, ref in (("82_dependencies.md", DEP_MARKER, "bank-rec"),
                               ("84_raci.md", RACI_MARKER, "bank-rec")):
        with open(os.path.join(area, fname), "w", encoding="utf-8") as fh:
            fh.write(f"## View\n\n{marker}\n\nAbout [[{ref}]].\n")
    scope_delta.commit(area, "dependencies")
    scope_delta.commit(area, "raci")

    # the derived rewrite MOVED basis_hash (which is why keying on it was wrong)
    # but left the draft basis — procedures + registry — untouched
    st = orchestrate.AreaState(area)
    assert st.basis_hash() != before
    assert st.draft_basis() == accepted_basis

    assert orchestrate.decide(area)["action"] == "reconcile"
    assert reconcile.reconcile(area) == 0
    capsys.readouterr()

    # ONE accept per pass: the tail runs without asking again
    assert orchestrate.decide(area)["action"] == "render"
    orchestrate.emit_render(area, "out/cash.docx", awaiting_review=True)
    assert orchestrate.decide(area)["action"] == "review"
    assert flag(area)["draft_basis"] == accepted_basis     # never rewritten


def test_draft_basis_ignores_derived_files_and_tracks_the_two_databases(tmp_path):
    """The keying rule as a unit: draft_basis() moves for a fragment edit and a
    registry edit, and does NOT move for a derived-view rewrite or a render —
    the inverse of basis_hash()."""
    area = two_view_area(tmp_path)
    st = orchestrate.AreaState(area)
    start, start_basis = st.draft_basis(), st.basis_hash()
    # the passed-in and re-read forms agree (the guard hands in what it already read)
    assert start == st.draft_basis(st.proc_hashes(), st.registry_hash())

    with open(os.path.join(area, "82_dependencies.md"), "a",
              encoding="utf-8") as fh:
        fh.write("\nregenerated by the agent\n")
    st = orchestrate.AreaState(area)
    assert st.basis_hash() != start_basis      # basis_hash sees the derived write
    assert st.draft_basis() == start           # the draft basis does not

    orchestrate.emit_render(area, "out.docx")               # a render moves nothing
    assert orchestrate.AreaState(area).draft_basis() == start

    with open(os.path.join(area, "10_bank-rec.md"), "a", encoding="utf-8") as fh:
        fh.write("\nA new step.\n")
    after_fragment = orchestrate.AreaState(area).draft_basis()
    assert after_fragment != start

    with open(os.path.join(area, "_reference", "systems.yaml"), "a",
              encoding="utf-8") as fh:
        fh.write("  - slug: sap\n    name: SAP\n")
    assert orchestrate.AreaState(area).draft_basis() != after_fragment


# --------------------------------------------------------------------------- #
# Re-opening: any change to the verbs or the nouns
# --------------------------------------------------------------------------- #

def test_touching_a_fragment_after_accepting_reopens_the_gate(tmp_path):
    """Acceptance bullet 4: an edit to one fragment changes the draft basis, so
    the accepted flag no longer matches and the gate re-opens (after the free
    aggregate pass the edit also triggers)."""
    area = simple(tmp_path)
    walk_to_gate(area)
    orchestrate.accept_draft(area)
    accepted = flag(area)["draft_basis"]
    assert orchestrate.decide(area)["action"] == "synthesize"

    with open(os.path.join(area, "10_bank-rec.md"), "a", encoding="utf-8") as fh:
        fh.write("\nOne more step the reviewer wanted.\n")
    # the free stages below the gate run first (the edit moved basis_hash too)
    assert orchestrate.decide(area)["action"] == "aggregate"
    orchestrate.emit_aggregate(area, warnings=[])
    assert orchestrate.decide(area)["action"] == "reconcile"
    orchestrate.emit_reconcile(area, clean=True, failing_files=[])

    d = orchestrate.decide(area)
    assert d["action"] == "draft_ready"
    assert d["details"]["draft_basis"] != accepted
    assert flag(area)["draft_basis"] == accepted    # the flag is stale, not gone


def test_editing_the_registry_after_accepting_reopens_the_gate(tmp_path):
    """Acceptance bullet 5: the registry is the other database the gate asks
    about, so a `_reference/*.yaml` edit re-opens it too."""
    area = simple(tmp_path)
    walk_to_gate(area)
    orchestrate.accept_draft(area)
    accepted = flag(area)["draft_basis"]

    with open(os.path.join(area, "_reference", "systems.yaml"), "a",
              encoding="utf-8") as fh:
        fh.write("  - slug: sap\n    name: SAP\n")
    assert orchestrate.decide(area)["action"] == "aggregate"
    orchestrate.emit_aggregate(area, warnings=[])
    # this area carries no python-derived views, so basis_hash did not move and
    # guard 8 is already satisfied; in a real area aggregate rewrites the systems
    # table first and reconcile re-verifies before the gate (as above).

    d = orchestrate.decide(area)
    assert d["action"] == "draft_ready"
    assert d["details"]["draft_basis"] != accepted


def test_an_accepted_gate_never_outranks_the_guards_above_it(tmp_path):
    """An accepted flag opens ONE gate; it does not fast-forward the ladder. A
    new source still routes to `taxonomy` (guard 5), and once it is consumed
    without changing any fragment the same accept still stands — the flag is
    keyed to the two databases, not to the pass."""
    area = simple(tmp_path)
    walk_to_gate(area)
    orchestrate.accept_draft(area)
    src = os.path.join(area, "_sources", "new", "call.md")
    os.makedirs(os.path.dirname(src), exist_ok=True)
    with open(src, "w", encoding="utf-8") as fh:
        fh.write("new client words\n")
    assert orchestrate.decide(area)["action"] == "taxonomy"

    os.remove(src)                       # scoping consumed it, no fragment moved
    assert orchestrate.decide(area)["action"] == "synthesize"


# --------------------------------------------------------------------------- #
# accept-draft is the sole writer, and no-ops with a reason
# --------------------------------------------------------------------------- #

NOT_AT_THE_GATE = [
    ("fill", lambda tmp: simple(tmp, body=UNFILLED)),
    ("aggregate", lambda tmp: simple(tmp)),
    ("confirm", lambda tmp: make_area(
        tmp, "cash", [proc("bank-rec")],
        {"10_bank-rec.md": FILLED, "_reference/systems.yaml": SYSTEMS_YAML,
         "_reference/.proposed/procedures.yaml": "procedures: []\n"})),
    ("error", lambda tmp: str(tmp / "no-such-area")),
]


@pytest.mark.parametrize("expected,build", NOT_AT_THE_GATE,
                         ids=[c[0] for c in NOT_AT_THE_GATE])
def test_accept_draft_off_the_gate_is_a_noop_with_a_reason(tmp_path, expected,
                                                           build):
    """Acceptance bullet 6 (and its neighbours): accept-draft on an area that is
    not at the gate writes nothing and says why, naming the action the advisor
    actually returns — an unfilled area is the headline case."""
    area = build(tmp_path)
    res = orchestrate.accept_draft(area)
    assert res["accepted"] is False
    assert res["next_action"] == expected
    assert "not at the draft-ready gate" in res["reason"]
    assert expected in res["reason"]
    assert flag(area) is None


def test_accept_draft_after_a_not_clean_reconcile_is_a_noop(tmp_path):
    """A reconcile that failed is below the gate: accept-draft cannot pre-accept
    a draft the verifier has not passed."""
    area = simple(tmp_path)
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=False)
    res = orchestrate.accept_draft(area)
    assert res["accepted"] is False and res["next_action"] == "reconcile"
    assert flag(area) is None


def test_accept_draft_twice_is_a_reported_noop_not_a_second_write(tmp_path):
    """Re-running accept-draft after the gate has opened reports the no-op (the
    advisor has moved on to `synthesize`) and leaves the flag byte-identical."""
    area = simple(tmp_path)
    walk_to_gate(area)
    orchestrate.accept_draft(area)
    path = os.path.join(area, ".draft_ready.json")
    with open(path, "rb") as fh:
        before = fh.read()
    res = orchestrate.accept_draft(area)
    assert res["accepted"] is False and res["next_action"] == "synthesize"
    with open(path, "rb") as fh:
        assert fh.read() == before


def test_cli_accept_draft_prints_json_and_exits_zero(tmp_path, capsys):
    """CLI wiring, mirroring `accept`: `accept-draft --area <area>` writes the
    flag, prints the result as JSON and exits 0 — on and off the gate."""
    area = simple(tmp_path)
    walk_to_gate(area)
    rc = orchestrate.main(["accept-draft", "--area", area])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert out["accepted"] is True
    assert out["draft_basis"] == orchestrate.AreaState(area).draft_basis()
    assert orchestrate.decide(area)["action"] == "synthesize"

    rc = orchestrate.main(["accept-draft", "--area", area])
    out = json.loads(capsys.readouterr().out)
    assert rc == 0 and out["accepted"] is False and "reason" in out


# --------------------------------------------------------------------------- #
# The gate does not disturb its neighbours (M18's guard-8 branches, `review`)
# --------------------------------------------------------------------------- #

def _failing_area(tmp_path, name, frag_body, failing):
    """A drafted area whose reconcile failed AT THE CURRENT BASIS, with the
    failure recorded against `failing` — the M18/F8 shapes."""
    area = make_area(tmp_path, name,
                     [proc("bank-rec"), derived("82_dependencies.md",
                                                "dependencies", 82)],
                     {"10_bank-rec.md": frag_body,
                      "82_dependencies.md": f"## Dependencies\n\n{DEP_MARKER}\n\n"
                                            "Depends on [[retired-proc]].\n",
                      "_reference/systems.yaml": SYSTEMS_YAML})
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=False, failing_files=failing)
    return area


F8_BRANCHES = [
    # (id, expected action, fragment body, recorded failing files)
    ("agent-view-stale", "synthesize", FILLED, ["82_dependencies.md"]),
    ("fragment-owned", "unresolvable", FILLED + "\nSee [[retired-proc]].\n",
     ["10_bank-rec.md", "82_dependencies.md"]),
    ("not-recorded", "reconcile", FILLED, None),
]


@pytest.mark.parametrize("case", F8_BRANCHES, ids=[c[0] for c in F8_BRANCHES])
def test_reconcile_failures_bypass_the_gate_untouched(tmp_path, case):
    """Guard 8.5 sits strictly BELOW guard 8: when reconcile is not clean at the
    current basis, every M18/F8 branch answers exactly as it did before M17 —
    the producer-first `synthesize`, the drafter-owned `unresolvable`, and the
    plain `reconcile` for an unrecorded failure. A gate above the verifier would
    have re-introduced the F8 deadlock in a new place."""
    _id, expected, body, failing = case
    area = _failing_area(tmp_path, _id, body, failing)
    d = orchestrate.decide(area)
    assert d["action"] == expected, d
    assert flag(area) is None       # and nothing was accepted along the way


def test_an_accepted_flag_cannot_open_a_dirty_reconcile(tmp_path):
    """The inverse: even with an accepted flag in place, a reconcile failure
    still routes through guard 8. The gate opens a spend; it never vouches for
    the verifier."""
    area = _failing_area(tmp_path, "dirty", FILLED, None)
    orchestrate._write_json(
        os.path.join(area, ".draft_ready.json"),
        {"accepted": True,
         "draft_basis": orchestrate.AreaState(area).draft_basis()})
    assert orchestrate.decide(area)["action"] == "reconcile"


def test_gate_does_not_preempt_the_review_gate(tmp_path):
    """A gate is a stop before a cost, so with nothing left to spend there is
    nothing to stop: an area whose render is current reports `review` (then
    `done`) even with no accepted flag at all. Firing here would ask the human
    to accept a draft whose document they have already read, and would make
    `done` unreachable for every area drafted before M17."""
    area = simple(tmp_path)
    orchestrate.emit_aggregate(area, warnings=[])
    orchestrate.emit_reconcile(area, clean=True, failing_files=[])
    scope_delta.commit(area, "dependencies")
    scope_delta.commit(area, "raci")
    orchestrate.emit_render(area, "out.docx", awaiting_review=True)

    assert flag(area) is None
    assert orchestrate.decide(area)["action"] == "review"
    orchestrate.accept_review(area)
    assert orchestrate.decide(area)["action"] == "done"


# --------------------------------------------------------------------------- #
# Purity + the ignore contract
# --------------------------------------------------------------------------- #

def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True, check=True)


@pytest.mark.parametrize("shape", ["at-the-gate", "accepted", "reopened"])
def test_next_at_the_gate_is_read_only(tmp_path, capsys, shape):
    """Acceptance: `next` on any state leaves git status empty. The gate reads
    one more signal file than before and writes none of them — only
    `accept-draft` writes `.draft_ready.json`."""
    area = simple(tmp_path, name=shape.replace("-", ""))
    walk_to_gate(area)
    if shape != "at-the-gate":
        orchestrate.accept_draft(area)
    if shape == "reopened":
        with open(os.path.join(area, "10_bank-rec.md"), "a",
                  encoding="utf-8") as fh:
            fh.write("\nlater edit\n")
        orchestrate.emit_aggregate(area, warnings=[])

    _git(area, "init", "-q")
    _git(area, "config", "user.email", "t@example.com")
    _git(area, "config", "user.name", "T")
    _git(area, "add", "-A")
    _git(area, "commit", "-q", "-m", "state")

    for _ in range(3):
        assert orchestrate.main(["next", "--area", area]) == 0
    capsys.readouterr()
    assert _git(area, "status", "--porcelain").stdout == ""


def test_draft_ready_flag_is_git_ignored_by_the_seeded_area_gitignore(tmp_path):
    """`.draft_ready.json` joins the signal-file family: it is advisor state, not
    engagement content, so the .gitignore checkpoint seeds must list it and a
    checkpoint must not commit it."""
    assert ".draft_ready.json" in orchestrate.AREA_GITIGNORE

    area = simple(tmp_path)
    walk_to_gate(area)
    orchestrate.accept_draft(area)
    assert flag(area) is not None

    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@example.com")
    _git(tmp_path, "config", "user.name", "T")
    res = orchestrate.checkpoint(area, "reconcile")
    assert res["committed"] is True
    tracked = _git(area, "ls-files").stdout.split()
    assert "10_bank-rec.md" in tracked
    assert ".draft_ready.json" not in tracked
    assert _git(area, "status", "--porcelain").stdout == ""
