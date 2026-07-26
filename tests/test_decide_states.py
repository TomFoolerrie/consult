"""The `decide()` state corpus — docs/audit-decide-exhaustiveness.md as tests.

The audit built each reachable folder state by hand, called `decide()`, and
recorded the action; the harness lived in scratch. This is that harness landed as
a regression suite, with every state asserting the action M18 says is CORRECT
(not the one the audit measured):

  A  manifest slug whose fragment is missing   unresolvable  (was: aggregate, F4)
  B  notes file for a slug not in the manifest review_triage (was: apply_review, F1)
  C  area folder does not exist                error         (was: done, F3)
  D  notes file with a non-slug basename       review_triage (was: apply_review, F1)
  E  zero-byte fragment                        aggregate     (F2 is reconcile's, M19)
  F  manifest with zero procedures             done
  G  no _reference/ directory                  aggregate
  H  unfilled procedure + live notes           apply_review  (notes outrank fill)
  I  unfilled procedures + new sources         fill          (fill outranks taxonomy)
  J  duplicate slug                            aggregate     (both files hashed, F5)
  K  .proposed/ holding only a dotfile         aggregate     (dotfiles ignored)
  L  unscoped area + stray note + sources      taxonomy      (was: apply_review, F1)
  M  new source on a fully drafted area        taxonomy/incr (F7 — M6's to fix)
  N  retirement, refs only in the agent view   synthesize    (was: reconcile, F8)
  O  retirement, refs in a procedure fragment  unresolvable  (was: reconcile, F8)

Two corpus-wide invariants close the loop: every dispatched stage must name a
target that exists (M18's resolvable-action invariant, the mechanical half a test
can check without running drafters), and `decide()` must be pure — same answer
twice, not one byte written.
"""
import json
import os

import pytest

import orchestrate
import scope_delta


FILLED = "## Proc\n\nReal drafted content.\n"
UNFILLED = "## Proc\n\n<!-- unfilled -->\n\nTBD.\n"
DEP_VIEW = ("## Dependencies\n\n<!-- derived: dependencies; writer: agent -->\n\n"
            "Depends on [[retired-proc]].\n")


def proc(slug, fname=None, order=10):
    return {"file": fname or f"10_{slug}.md", "role": "procedure", "slug": slug,
            "heading": slug.title(), "l2": "ops", "order": order}


def area(tmp_path, name, components=None, files=None, manifest=True):
    """Build a synthetic area folder. `files` maps relpath -> content."""
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


# --------------------------------------------------------------------------- #
# The corpus. Each builder returns the folder path decide() is asked about.
#
# `productive` records whether the returned action can change THIS state:
#   True  — a stage whose write moves the area forward
#   False — a resting result: a human gate, `done`, or `error`. Never a stage
#           that would be re-selected unchanged on the next call.
# --------------------------------------------------------------------------- #

def state_a(tmp_path):
    """A — manifest lists a slug whose fragment file is not on disk (F4)."""
    return area(tmp_path, "a", [proc("alpha"), proc("beta", order=20)],
                {"10_alpha.md": FILLED, "_reference/systems.yaml": "systems: []\n"})


def state_b(tmp_path):
    """B — a notes file whose slug is not in the manifest (F1)."""
    return area(tmp_path, "b", [proc("alpha")],
                {"10_alpha.md": FILLED, "_reference/systems.yaml": "systems: []\n",
                 "_review/ghost.notes.yaml": "items: [{note: x}]\n"})


def state_c(tmp_path):
    """C — the area folder does not exist at all (typo'd --area, F3)."""
    return str(tmp_path / "no-such-area")


def state_d(tmp_path):
    """D — a notes file with a non-slug basename (F1)."""
    return area(tmp_path, "d", [proc("alpha")],
                {"10_alpha.md": FILLED, "_reference/systems.yaml": "systems: []\n",
                 "_review/2026-05-call.notes.yaml": "items: []\n"})


def state_e(tmp_path):
    """E — a zero-byte fragment (no sentinel, no content: F2).

    Still `aggregate` on purpose: M19 gave the detector to reconcile, which
    blocks on it one stage later. decide() is not the substance authority."""
    return area(tmp_path, "e", [proc("alpha")],
                {"10_alpha.md": "", "_reference/systems.yaml": "systems: []\n"})


def state_f(tmp_path):
    """F — a manifest with zero procedure components."""
    return area(tmp_path, "f", [], {"_reference/systems.yaml": "systems: []\n"})


def state_g(tmp_path):
    """G — procedures filled but no _reference/ directory at all."""
    return area(tmp_path, "g", [proc("alpha")], {"10_alpha.md": FILLED})


def state_h(tmp_path):
    """H — an unfilled procedure AND notes for a live slug: notes outrank fill."""
    return area(tmp_path, "h", [proc("alpha"), proc("beta", order=20)],
                {"10_alpha.md": UNFILLED, "10_beta.md": FILLED,
                 "_reference/systems.yaml": "systems: []\n",
                 "_review/beta.notes.yaml": "items: []\n"})


def state_i(tmp_path):
    """I — unfilled procedures AND unconsumed _sources/new/: fill precedes 5."""
    return area(tmp_path, "i", [proc("alpha")],
                {"10_alpha.md": UNFILLED, "_sources/new/t.md": "transcript",
                 "_reference/systems.yaml": "systems: []\n"})


def state_j(tmp_path):
    """J — two components share a slug over two files (F5)."""
    return area(tmp_path, "j",
                [proc("alpha"), proc("alpha", "10_alpha_dup.md", order=20)],
                {"10_alpha.md": FILLED, "10_alpha_dup.md": FILLED,
                 "_reference/systems.yaml": "systems: []\n"})


def state_k(tmp_path):
    """K — _reference/.proposed/ holding only a dotfile: not a proposal."""
    return area(tmp_path, "k", [proc("alpha")],
                {"10_alpha.md": FILLED, "_reference/.proposed/.keep": "",
                 "_reference/systems.yaml": "systems: []\n"})


def state_l(tmp_path):
    """L — brand-new area: sources waiting, no manifest, one stray note (F1).

    The worst F1 instance: guard 2 used to divert this to apply_review and the
    area could never be scoped at all."""
    return area(tmp_path, "l", None,
                {"_sources/new/t.md": "transcript",
                 "_review/ghost.notes.yaml": "items: []\n"}, manifest=False)


def state_m(tmp_path):
    """M — a new source touching only already-drafted procedures (F7).

    Still `taxonomy` (incremental): M18 does not fix F7, M6 does. Pinned so the
    day M6 lands the change is deliberate and visible."""
    folder = area(tmp_path, "m", [proc("alpha")],
                  {"10_alpha.md": FILLED, "_sources/new/second.md": "more",
                   "_reference/systems.yaml": "systems: []\n"})
    return folder


def _retirement_area(tmp_path, name, frag_body, failing):
    """A drafted area whose reconcile FAILED at the current basis, with the
    failure recorded against `failing` — the F8 shape: a procedure was removed
    from the manifest and `[[retired-proc]]` references were left behind."""
    folder = area(tmp_path, name,
                  [proc("alpha"),
                   {"file": "82_dependencies.md", "role": "derived", "order": 82,
                    "derived_kind": "dependencies", "writer": "agent",
                    "heading": "Dependencies"}],
                  {"10_alpha.md": frag_body, "82_dependencies.md": DEP_VIEW,
                   "_reference/systems.yaml": "systems: []\n"})
    orchestrate.emit_aggregate(folder, warnings=[])
    orchestrate.emit_reconcile(folder, clean=False, failing_files=failing)
    return folder


def state_n(tmp_path):
    """N — retirement with dangling refs ONLY in the agent-owned view (F8).

    scope_delta has no baseline, so both kinds are stale: the producer is ready
    and used to be unreachable behind the verifier."""
    return _retirement_area(tmp_path, "n", FILLED, ["82_dependencies.md"])


def state_o(tmp_path):
    """O — retirement with dangling refs in a procedure fragment (F8).

    Drafter-owned prose: no stage regenerates it, so the ladder must rest."""
    return _retirement_area(tmp_path, "o", FILLED + "\nSee [[retired-proc]].\n",
                            ["10_alpha.md", "82_dependencies.md"])


CORPUS = [
    # (id, builder, expected action, productive?)
    ("A-missing-fragment", state_a, "unresolvable", False),
    ("B-orphan-note", state_b, "review_triage", False),
    ("C-nonexistent-area", state_c, "error", False),
    ("D-non-slug-note", state_d, "review_triage", False),
    ("E-empty-fragment", state_e, "aggregate", True),
    ("F-no-procedures", state_f, "done", False),
    ("G-no-reference-dir", state_g, "aggregate", True),
    ("H-notes-outrank-fill", state_h, "apply_review", True),
    ("I-fill-outranks-taxonomy", state_i, "fill", True),
    ("J-duplicate-slug", state_j, "aggregate", True),
    ("K-dotfile-only-proposal", state_k, "aggregate", True),
    ("L-unscoped-with-stray-note", state_l, "taxonomy", True),
    ("M-new-source-on-drafted-area", state_m, "taxonomy", True),
    ("N-retirement-agent-view", state_n, "synthesize", True),
    ("O-retirement-fragment", state_o, "unresolvable", False),
]

IDS = [c[0] for c in CORPUS]


@pytest.mark.parametrize("case", CORPUS, ids=IDS)
def test_corpus_action(tmp_path, case):
    """Every audit state yields its post-M18 action, and every non-productive
    state rests — a human gate, `done` or `error`, never a stage that would be
    re-selected unchanged on the next call."""
    _id, build, expected, productive = case
    d = orchestrate.decide(build(tmp_path))
    assert d["action"] == expected, d
    if not productive:
        assert d["human_gate"] is True or d["action"] in ("done", "error"), d
    else:
        assert d["human_gate"] is False, d


@pytest.mark.parametrize("case", CORPUS, ids=IDS)
def test_dispatch_names_an_existing_target(tmp_path, case):
    """The resolvable-action invariant, mechanically: a dispatch must name a
    target that is actually there — notes for live slugs, unfilled slugs with
    files on disk, failing views that exist."""
    _id, build, _expected, _productive = case
    folder = build(tmp_path)
    d = orchestrate.decide(folder)
    det = d.get("details") or {}
    if d["action"] == "apply_review":
        st = orchestrate.AreaState(folder)
        assert det["notes"]
        for rel in det["notes"]:
            assert os.path.isfile(os.path.join(folder, rel))
            assert st.note_slug(rel) in st.procedure_slugs
    if d["action"] == "fill":
        st = orchestrate.AreaState(folder)
        paths = dict(st.procedures)
        assert det["unfilled"]
        for slug in det["unfilled"]:
            assert os.path.isfile(paths[slug])
    if d["action"] == "synthesize":
        assert det["pending"] or det["stale_kinds"]
        for rel in det.get("failing_files", []):
            assert os.path.isfile(os.path.join(folder, rel))
    if d["action"] == "unresolvable":
        # the gate must say what was found, why nothing helps, and what to do
        assert det["state"] and det["why_no_stage"] and det["human_action"]


@pytest.mark.parametrize("case", CORPUS, ids=IDS)
def test_decide_is_pure_and_repeatable(tmp_path, case):
    """Same folder, same answer, and not one byte written — the advisor is a
    pure function of on-disk state (M7 design note, M18 acceptance)."""
    _id, build, _expected, _productive = case
    folder = build(tmp_path)

    def snapshot():
        out = {}
        for root, _dirs, names in os.walk(folder):
            for n in names:
                p = os.path.join(root, n)
                with open(p, "rb") as fh:
                    out[os.path.relpath(p, folder)] = fh.read()
        return out

    before = snapshot()
    first = orchestrate.decide(folder)
    second = orchestrate.decide(folder)
    assert first == second
    assert snapshot() == before


AGGREGATE_STATES = [c for c in CORPUS if c[2] == "aggregate"]


@pytest.mark.parametrize("case", AGGREGATE_STATES,
                         ids=[c[0] for c in AGGREGATE_STATES])
def test_a_dispatched_stage_is_not_re_selected_unchanged(tmp_path, case):
    """The invariant end to end for every corpus state whose action is a stage
    this suite can actually run: dispatch it, and the same action is never
    returned again on the same folder."""
    _id, build, _expected, _productive = case
    folder = build(tmp_path)
    assert orchestrate.decide(folder)["action"] == "aggregate"
    orchestrate.emit_aggregate(folder, warnings=[])
    assert orchestrate.decide(folder)["action"] != "aggregate"


# --------------------------------------------------------------------------- #
# The two F8 states, walked one step further: the producer really does clear
# the state that selected it (the half the audit had to run stages to see).
# --------------------------------------------------------------------------- #

def test_retirement_agent_view_clears_after_synthesize(tmp_path):
    """N walked forward: synthesize -> (agent rewrites the view, driver
    rebaselines) -> reconcile re-verifies -> render. No repeat of synthesize."""
    folder = state_n(tmp_path)
    assert orchestrate.decide(folder)["action"] == "synthesize"

    # the agent rewrites 82 without the dangling reference; driver rebaselines
    (open(os.path.join(folder, "82_dependencies.md"), "w", encoding="utf-8")
     .write("## Dependencies\n\n<!-- derived: dependencies; writer: agent -->\n\n"
            "Depends on [[alpha]].\n"))
    scope_delta.commit(folder, "dependencies")
    scope_delta.commit(folder, "raci")

    # basis moved: the verifier runs next, and a clean pass reaches render
    assert orchestrate.decide(folder)["action"] == "reconcile"
    orchestrate.emit_reconcile(folder, clean=True, failing_files=[])
    assert orchestrate.decide(folder)["action"] == "render"


def test_retirement_fragment_gate_names_file_and_reference(tmp_path):
    """O's gate names both the failing fragment and the dangling reference —
    the acceptance wording is "naming file and reference"."""
    folder = state_o(tmp_path)
    d = orchestrate.decide(folder)
    assert d["action"] == "unresolvable"
    assert "10_alpha.md" in d["details"]["failing_files"]
    assert d["details"]["dangling_refs"]["10_alpha.md"] == ["retired-proc"]
    assert "retired-proc" in json.dumps(d)
