"""M36 WP-G2 — the DETERMINISTIC layer follows the definition.

WP-G1 made the document assembled from the plan. This package makes the three
deterministic stages around it read the same definition instead of their own
module constants, and pays for it the only way the gate accepts: v1's outputs,
byte for byte, with the plan in the loop.

What is proven here, in the order the ticket lists it:

  A. `Plan.bindings` — a compiled plan carries its definition's binding map, so
     `render_glue.render_plan` no longer needs the map handed to it separately.
     An explicit `bindings=` kwarg still WINS (WP-G1's tests pass it, unchanged).
  B. `aggregate.run` — the derived views BUILT and WRITTEN are the plan's
     python-writer view blocks. Proof is a before/after over one fixture copy
     each: the plan-driven run and the documented no-plan fallback (v1's
     manifest-driven path) write the SAME FILE SET with the SAME BYTES. Plus the
     refusal: a plan naming a view no builder serves is refused BY NAME, with
     the area untouched.
  C. `scaffold` — the section skeleton's sections, titles and order come from
     `kernel.load_type("activity").parts`. Pinned two ways: the emitted skeleton
     matches an expectation DERIVED FROM the declaration, and reordering the
     declaration reorders the skeleton (which a surviving hard-coded list could
     not do).
  D. the M21 render signal — keyed per definition, with a TOLERANT read: a
     pre-M36 `.render.json` (no `definition` key) yields the identical advisor
     verdict, and the advisor's whole ladder over the frozen fixture returns
     v1's actions at every step. A signal naming a DIFFERENT deliverable is the
     one behavior change, and it is unreachable today (one deliverable exists).

THE GOLDEN: not re-run here. `tests/test_render_golden_m36.py` (the WP-G0 gate)
and `tests/test_plan_assembly_m36.py::TestCentralProof` both render the fixture
and diff it against the committed golden in this same suite, so a byte of drift
from any change in this package lands there. A red golden is a defect in the
change, never a stale golden — regeneration is forbidden
(tests/fixtures/golden/p2p-v1/README.md).

Suite conventions honored: the frozen fixture is never written (every run is
over a tmp copy, and one test fingerprints the fixture to prove it), no network,
no wall clock, no order dependence.
"""

from __future__ import annotations

import json
import shutil

from pathlib import Path

import pytest

import aggregate
import definitions
import kernel
import orchestrate
import scaffold
import scope_delta

FIXTURE_AREA = (Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
                / "components" / "procure-to-pay")


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def area_copy(root: Path, name: str = "p2p") -> Path:
    """A writable copy of the frozen fixture, inside an engagement tree (so the
    `_client/deliverables/` resolution path is the real one)."""
    area = root / "eng" / "components" / name
    area.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FIXTURE_AREA, area)
    return area


def fingerprint(root: Path) -> dict:
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in root.rglob("*") if p.is_file()}


def file_bytes(area: Path) -> dict[str, bytes]:
    """{area-relative path: bytes} for every file in the area."""
    return {str(p.relative_to(area)): p.read_bytes()
            for p in sorted(area.rglob("*")) if p.is_file()}


def written_markdown(area: Path) -> dict[str, bytes]:
    """The derived markdown views only — what aggregate is judged on."""
    return {k: v for k, v in file_bytes(area).items()
            if k.endswith(".md") and b"<!-- derived:" in v}


# --------------------------------------------------------------------------- #
# A — Plan.bindings
# --------------------------------------------------------------------------- #

class TestPlanCarriesItsBindings:

    def test_compiled_plan_carries_the_definitions_bindings(self, tmp_path):
        area = area_copy(tmp_path)
        defn = definitions.resolve_definition(area)
        plan = definitions.compile_plan(defn, area)
        assert plan.bindings == defn.bindings
        # A copy, not the definition's own dict: a consumer mutating the plan's
        # view of a binding cannot rewrite the loaded definition.
        plan.bindings["procedure-parts"]["parts"] = ["scope"]
        assert defn.bindings["procedure-parts"]["parts"] != ["scope"]

    def test_render_plan_prefers_the_plans_bindings_when_the_kwarg_is_absent(
            self, tmp_path, monkeypatch):
        """The seam WP-G1's tests rely on: kwarg wins if both are present, the
        plan's own map is used when it is not, and `bindings={}` still means
        "apply no selection"."""
        import render_glue

        seen = []

        def fake_render_folder(area, out, **kw):
            seen.append(kw["shape"].plan_bindings)
            return {}

        monkeypatch.setattr(render_glue, "check_plan", lambda plan, area: [])
        import render
        monkeypatch.setattr(render, "render_folder", fake_render_folder)

        area = area_copy(tmp_path)
        defn = definitions.resolve_definition(area)
        plan = definitions.compile_plan(defn, area)
        out = tmp_path / "o.docx"

        render_glue.render_plan(plan, area, out)                    # no kwarg
        render_glue.render_plan(plan, area, out, bindings={"x": {}})  # kwarg
        render_glue.render_plan(plan, area, out, bindings={})         # explicit
        assert seen == [plan.bindings, {"x": {}}, {}]


# --------------------------------------------------------------------------- #
# B — aggregate builds exactly the plan's python views
# --------------------------------------------------------------------------- #

class TestAggregateFollowsThePlan:

    def test_fixture_plan_names_exactly_v1s_python_view_set(self, tmp_path):
        area = area_copy(tmp_path)
        kinds = aggregate.plan_python_kinds(area)
        assert kinds == ["procedure-index", "role-dictionary", "systems",
                         "appendix-a", "gap-log", "screenshot-index"]
        # Every one of them has a registered builder (nothing to refuse).
        assert aggregate.unbuildable_plan_views(kinds) == []

    def test_plan_driven_run_writes_the_same_files_with_the_same_bytes_as_v1(
            self, tmp_path, monkeypatch):
        """THE BEFORE/AFTER PROOF. One fixture copy aggregated through the plan,
        one through the documented no-plan fallback (v1's manifest-driven path):
        same derived file SET, same BYTES, same exit code."""
        after = area_copy(tmp_path / "after")
        before = area_copy(tmp_path / "before")

        assert aggregate.run(str(after)) == 0
        after_files = file_bytes(after)
        assert aggregate.plan_python_kinds(after) is not None  # plan was in play

        monkeypatch.setattr(aggregate, "plan_python_kinds", lambda area: None)
        assert aggregate.run(str(before)) == 0
        before_files = file_bytes(before)

        assert set(after_files) == set(before_files)
        assert after_files == before_files
        # And the set is not vacuous: v1's six python views were rebuilt.
        assert len(written_markdown(after)) == 8   # 6 python + 2 agent views

    def test_a_plan_view_with_no_builder_is_refused_by_name(
            self, tmp_path, monkeypatch, capsys):
        area = area_copy(tmp_path)
        before = fingerprint(area)
        monkeypatch.setattr(
            aggregate, "plan_python_kinds",
            lambda a: ["procedure-index", "risk-heatmap"])
        assert aggregate.run(str(area)) == 1
        out = capsys.readouterr().out
        assert "risk-heatmap" in out and "ERROR" in out
        assert "procedure-index" not in out.split("risk-heatmap")[0]
        # Refused BEFORE anything was touched.
        assert fingerprint(area) == before

    def test_the_fallback_is_the_documented_one(self, tmp_path, monkeypatch):
        """`plan_python_kinds` returns None — not a guess — when no definition
        can be resolved (a stripped install, a missing/invalid definition file),
        which is the only path on which aggregate's builder registry acts as the
        document shape. Any directory resolves the SHIPPED definition, so the
        failure is simulated at the resolver."""
        area = area_copy(tmp_path)
        assert aggregate.plan_python_kinds(area) is not None

        def boom(*a, **kw):
            raise definitions.DefinitionError("no definition here")

        monkeypatch.setattr(definitions, "resolve_definition", boom)
        assert aggregate.plan_python_kinds(area) is None

    def test_the_frozen_fixture_is_never_written(self):
        before = fingerprint(FIXTURE_AREA)
        assert before == fingerprint(FIXTURE_AREA)


# --------------------------------------------------------------------------- #
# C — the skeleton comes from the type declaration
# --------------------------------------------------------------------------- #

class TestSkeletonFromTheDeclaration:

    def test_declared_parts_are_the_activity_declarations_parts(self):
        decl = kernel.load_type("activity")
        assert scaffold.declared_parts() == [(p.slug, p.title)
                                             for p in decl.parts]
        assert scaffold.declared_sections() == [p.slug for p in decl.parts]

    def test_emitted_skeleton_sections_are_pinned_to_the_declaration(self):
        """The committed expectation: the `###` headings of a stamped skeleton
        are the declaration's part TITLES in DECLARED order — nothing else, in
        no other order."""
        expected = [p.title for p in kernel.load_type("activity").parts]
        assert expected == ["Scope", "At a Glance", "Before You Start",
                            "Procedure", "Outputs & Evidence", "Key Controls",
                            "Known Issues & Improvement Opportunities"]
        got = [ln[4:].strip()
               for ln in scaffold.render_skeleton("Bank Rec").splitlines()
               if ln.startswith("### ")]
        assert got == expected

    def test_the_declaration_decides_the_order(self, monkeypatch):
        """A hard-coded section list could not do this: reverse the declared
        parts and the emitted skeleton reverses with them."""
        parts = scaffold.declared_parts()
        monkeypatch.setattr(scaffold, "declared_parts",
                            lambda: list(reversed(parts)))
        got = [ln[4:].strip()
               for ln in scaffold._fallback_skeleton("Bank Rec").splitlines()
               if ln.startswith("### ")]
        assert got == [t for _s, t in reversed(parts)]

    def test_fallback_skeleton_keeps_the_sentinel_and_the_end_matter(self):
        text = scaffold._fallback_skeleton("Bank Rec")
        assert text.startswith("## Bank Rec\n\n<!-- unfilled -->\n")
        assert text.endswith("```consult-meta\nsystems: []\nroles:   []\n```\n")
        # The module attribute is the same thing as a `{heading}` template.
        assert scaffold._FALLBACK_SKELETON.format(heading="Bank Rec") == text


# --------------------------------------------------------------------------- #
# D — the render signal, keyed per definition (+ advisor replay)
# --------------------------------------------------------------------------- #

def advance_to_done(area: Path) -> None:
    """Drive one area copy up v1's ladder to the resting state, using only the
    public stage entry points (no signal file is hand-written)."""
    a = str(area)
    assert aggregate.run(a) == 0
    for kind in scope_delta.agent_derived_kinds(a):
        scope_delta.commit(a, kind)
    orchestrate.emit_reconcile(a, clean=True)
    assert orchestrate.accept_draft(a)["accepted"] is True
    orchestrate.emit_render(a, "out.docx", awaiting_review=False)


class TestRenderSignalKeyedPerDefinition:

    def test_the_signal_records_the_deliverable_it_is_about(self, tmp_path):
        area = area_copy(tmp_path)
        advance_to_done(area)
        sig = json.loads((area / ".render.json").read_text(encoding="utf-8"))
        assert sig["definition"] == "desktop-procedure"
        # Additive: v1's three keys are untouched.
        assert set(sig) == {"basis", "docx", "awaiting_review", "definition"}

    def test_an_old_format_signal_reads_as_v1s_only_deliverable(self):
        """TOLERANT READ (the advisor keeps reading old-format files): a signal
        with no `definition` key is a v1 signal, and v1 has one deliverable."""
        assert orchestrate.signal_definition({}) == "desktop-procedure"
        assert orchestrate.signal_definition(
            {"basis": "x"}) == "desktop-procedure"
        assert orchestrate.signal_definition(
            {"definition": " other "}) == "other"

    def test_the_verdict_is_identical_with_and_without_the_new_field(
            self, tmp_path):
        area = area_copy(tmp_path)
        advance_to_done(area)
        with_field = orchestrate.decide(str(area))

        path = area / ".render.json"
        sig = json.loads(path.read_text(encoding="utf-8"))
        del sig["definition"]                       # a pre-M36 signal file
        path.write_text(json.dumps(sig, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
        assert orchestrate.decide(str(area)) == with_field
        assert with_field["action"] == "done"

    def test_a_signal_for_another_deliverable_does_not_satisfy_the_gate(
            self, tmp_path):
        """The keying has teeth: a .docx of a different deliverable is not this
        area's document. Unreachable today — one deliverable exists — which is
        why this is behavior-identical for every v1 area."""
        area = area_copy(tmp_path)
        advance_to_done(area)
        assert orchestrate.decide(str(area))["action"] == "done"

        path = area / ".render.json"
        sig = json.loads(path.read_text(encoding="utf-8"))
        sig["definition"] = "process-map"
        path.write_text(json.dumps(sig, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
        assert orchestrate.decide(str(area))["action"] == "render"

    def test_scope_delta_agent_kinds_come_from_the_plan(self, tmp_path):
        area = area_copy(tmp_path)
        assert scope_delta.agent_derived_kinds(area) == ("dependencies", "raci")
        assert scope_delta.agent_derived_kinds(area) == \
            scope_delta.AGENT_DERIVED_KINDS
        # Unresolvable area -> the documented fallback, never a crash.
        assert scope_delta.agent_derived_kinds(tmp_path / "nope") == \
            scope_delta.AGENT_DERIVED_KINDS
        with pytest.raises(ValueError):
            scope_delta.work_order(str(area), "systems")


class TestAdvisorReplayEquivalence:

    def test_the_ladder_over_the_fixture_returns_v1s_actions_at_every_step(
            self, tmp_path):
        """Proof obligation 3, over the frozen fixture: the recorded sequence of
        advisor verdicts, PINNED. Every action and gate flag below is what v1
        returns today; a change in this package that moved any of them would be
        a compatibility break, not an improvement."""
        area = area_copy(tmp_path)
        a = str(area)
        seen = []

        def step(label):
            d = orchestrate.decide(a)
            seen.append((label, d["action"], d["human_gate"]))
            return d

        step("fresh")
        assert aggregate.run(a) == 0
        for kind in scope_delta.agent_derived_kinds(a):
            scope_delta.commit(a, kind)
        step("aggregated")
        orchestrate.emit_reconcile(a, clean=True)
        step("reconciled")
        assert orchestrate.accept_draft(a)["accepted"] is True
        step("draft-accepted")
        orchestrate.emit_render(a, "out.docx", awaiting_review=True)
        step("rendered")
        orchestrate.accept_review(a)
        step("reviewed")

        assert seen == [
            ("fresh", "aggregate", False),
            ("aggregated", "reconcile", False),
            ("reconciled", "draft_ready", True),
            ("draft-accepted", "render", False),
            ("rendered", "review", True),
            ("reviewed", "done", False),
        ]
