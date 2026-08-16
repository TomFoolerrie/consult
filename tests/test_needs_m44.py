"""M44 acceptance tests — written BEFORE the build.

Pins: the needs view (per-deliverable gap render over the brain —
objective-driven target selection, the three feeds, determinism,
read-only), the `engagement-needs` derived-view builder, and the two-mint
GAP doctrine's landing in the agent contracts (mechanical greps for the
load-bearing phrases).

Classes skip until their work package lands: WP-G1 gates on the module
import, WP-G2 on the drafter's "evidenced absence" anchor.
"""

import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
P2P_AREA = (Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
            / "components" / "procure-to-pay")

DRAFTER = REPO / "agents" / "consult-drafter.md"
SURVEYOR = REPO / "agents" / "consult-surveyor.md"
LIBRARIAN = REPO / "agents" / "consult-librarian.md"

ENTRY_KEYS = {"deliverable", "kind", "need", "where", "grounds"}
KINDS = {"binding-unserved", "coverage", "recorded-gap"}


def _module_missing():
    try:
        import needs  # noqa: F401
        return False
    except ImportError:
        return True


needs_module = pytest.mark.skipif(
    _module_missing(), reason="M44 needs module not built yet — the target")

needs_prose = pytest.mark.skipif(
    "evidenced absence" not in DRAFTER.read_text(encoding="utf-8").lower(),
    reason="M44 two-mint doctrine prose not landed yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def write_objective(area, deliverables, cycles=("procure-to-pay",)):
    cdir = area / "_client"
    cdir.mkdir(exist_ok=True)
    (cdir / "objective.yaml").write_text(
        "objective:\n"
        "  goal: Deliver what the engagement was hired for.\n"
        f"  deliverables: [{', '.join(deliverables)}]\n"
        f"  cycles: [{', '.join(cycles)}]\n", encoding="utf-8")


def fingerprint(base):
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in base.rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- #
# 1. Target selection (WP-G1)
# --------------------------------------------------------------------------- #

@needs_module
class TestTargets:
    def test_no_objective_no_param_is_empty_report(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        assert needs.needs(area) == []

    def test_objective_selects_the_targets(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area, ["process-controls-matrix"])
        entries = needs.needs(area)
        assert entries, "a configured target must render at least one entry " \
                        "or the empty list is a lie about this fixture"
        assert {e["deliverable"] for e in entries} == {"process-controls-matrix"}

    def test_explicit_deliverable_overrides(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        # no objective configured at all — the param alone selects
        entries = needs.needs(area, deliverable="process-controls-matrix")
        assert {e["deliverable"] for e in entries} == {"process-controls-matrix"}

    def test_unknown_deliverable_refuses_by_name(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        with pytest.raises(Exception) as exc:
            needs.needs(area, deliverable="no-such-deliverable")
        assert "no-such-deliverable" in str(exc.value)

    def test_entry_shape_is_total(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area, ["process-controls-matrix",
                               "information-request"])
        for e in needs.needs(area):
            assert set(e) >= ENTRY_KEYS, e
            assert e["kind"] in KINDS, e
            assert isinstance(e["grounds"], list) and e["grounds"], e


# --------------------------------------------------------------------------- #
# 2. The three feeds (WP-G1)
# --------------------------------------------------------------------------- #

@needs_module
class TestStructuralFeed:
    def test_v1_area_reports_the_missing_population(self):
        import needs
        entries = needs.needs(P2P_AREA, deliverable="process-controls-matrix")
        structural = [e for e in entries if e["kind"] == "binding-unserved"]
        assert structural
        assert "process-step" in str(structural)


@needs_module
class TestCoverageFeed:
    def test_claimed_node_surfaces_for_a_coverage_bound_target(self, tmp_path):
        import needs
        import scaffold
        root, area = ipo_copy(tmp_path)
        scaffold.seed_taxonomy(area, "procure-to-pay")
        scaffold.promote_taxonomy(area)          # payments lands "claimed"
        entries = needs.needs(area, deliverable="information-request")
        cov = [e for e in entries if e["kind"] == "coverage"]
        assert any("payments" in e["where"] for e in cov), cov

    def test_no_coverage_binding_no_coverage_entries(self, tmp_path):
        # the SHAPE of need follows the deliverable — a matrix has no
        # coverage binding, so it gets no coverage entries even when
        # unclaimed nodes exist
        import needs
        import scaffold
        root, area = ipo_copy(tmp_path)
        scaffold.seed_taxonomy(area, "procure-to-pay")
        scaffold.promote_taxonomy(area)
        entries = needs.needs(area, deliverable="process-controls-matrix")
        assert not [e for e in entries if e["kind"] == "coverage"]


@needs_module
class TestRecordedFeed:
    def test_open_gaps_surface_with_ids_and_steps(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        entries = needs.needs(area, deliverable="process-controls-matrix")
        recorded = [e for e in entries if e["kind"] == "recorded-gap"]
        assert recorded, entries
        joined = str(recorded)
        assert "GAP-" in joined                 # the display id in grounds
        wheres = {e["where"] for e in recorded}
        assert "match-po" in wheres             # the fixture's GAP-02 home


# --------------------------------------------------------------------------- #
# 3. Discipline (WP-G1)
# --------------------------------------------------------------------------- #

@needs_module
class TestDiscipline:
    def test_read_only(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area, ["process-controls-matrix"])
        before = fingerprint(root)
        needs.needs(area)
        assert fingerprint(root) == before

    def test_deterministic(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area, ["process-controls-matrix",
                               "information-request"])
        assert needs.needs(area) == needs.needs(area)

    def test_rerenders_when_the_objective_changes(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area, ["process-controls-matrix"])
        first = {e["deliverable"] for e in needs.needs(area)}
        write_objective(area, ["information-request"])
        second = {e["deliverable"] for e in needs.needs(area)}
        assert first == {"process-controls-matrix"}
        assert second == {"information-request"}


# --------------------------------------------------------------------------- #
# 4. The CLI and the builder (WP-G1)
# --------------------------------------------------------------------------- #

@needs_module
class TestRender:
    def test_cli_prints_the_render(self, tmp_path, capsys):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area, ["process-controls-matrix"])
        assert needs.main([str(area)]) == 0
        out = capsys.readouterr().out
        assert "process-controls-matrix" in out

    def test_cli_unconfigured_prints_the_absence_line(self, tmp_path, capsys):
        import needs
        root, area = ipo_copy(tmp_path)
        assert needs.main([str(area)]) == 0
        assert "no engagement objective" in capsys.readouterr().out.lower()

    def test_builder_registered_and_renders(self, tmp_path):
        import aggregate
        root, area = ipo_copy(tmp_path)
        write_objective(area, ["process-controls-matrix"])
        builder = aggregate.PY_BUILDERS["engagement-needs"]
        out = builder({"area": area})
        assert isinstance(out, str)
        assert "process-controls-matrix" in out


# --------------------------------------------------------------------------- #
# 5. The two-mint doctrine prose (WP-G2)
# --------------------------------------------------------------------------- #

@needs_prose
class TestDoctrineProse:
    def _text(self, path):
        return path.read_text(encoding="utf-8")

    def test_drafter_names_the_two_mints(self):
        low = self._text(DRAFTER).lower()
        assert "evidenced absence" in low
        assert "conflict" in low

    def test_drafter_ask_half_is_gone(self):
        low = self._text(DRAFTER).lower()
        assert "who can answer it" not in low

    def test_drafter_generic_thinness_rule_stands(self):
        low = self._text(DRAFTER).lower()
        assert "does not mint" in low
        assert "unconfirmed" in low

    def test_surveyor_agenda_is_rendered_from_needs(self):
        low = self._text(SURVEYOR).lower()
        assert "needs" in low
        assert "needs.py" in low or "needs view" in low

    def test_librarian_admits_the_ask_half_trim(self):
        low = self._text(LIBRARIAN).lower()
        assert "ask half" in low

    def test_objective_block_points_at_the_needs_view(self, tmp_path):
        import brief
        root, area = ipo_copy(tmp_path)
        write_objective(area, ["process-controls-matrix"])
        block = brief.objective_block(area)
        assert "needs" in block.lower()


# --------------------------------------------------------------------------- #
# 6. The grammar amendment (A3 — ruled 2026-08-16: retire Owner-to-confirm on
#    process steps, mint Grounds, align the Nature enum to the two mints)
# --------------------------------------------------------------------------- #

def _gap_fields_declared():
    try:
        import kernel
        tdecl = kernel.load_type("process-step")
        gap = [c for c in tdecl.callouts if c.prefix == "GAP"]
        return bool(gap and (getattr(gap[0], "fields", []) or []))
    except Exception:
        return False


needs_grammar = pytest.mark.skipif(
    not _gap_fields_declared(),
    reason="M44 A3 grammar amendment not landed yet — the target")


@needs_grammar
class TestGrammarAmendment:
    def test_gap_declares_grounds(self):
        import kernel
        tdecl = kernel.load_type("process-step")
        gap = [c for c in tdecl.callouts if c.prefix == "GAP"]
        assert list(gap[0].fields) == ["Grounds"]

    def test_v1_activity_type_untouched(self):
        import kernel
        tdecl = kernel.load_type("activity")
        gap = [c for c in tdecl.callouts if c.prefix == "GAP"]
        assert not (getattr(gap[0], "fields", []) or [])

    def test_drafter_scopes_the_retirement_by_unit(self):
        low = DRAFTER.read_text(encoding="utf-8").lower()
        assert "conflict | evidenced-absence" in low
        assert "retired" in low and "owner to confirm" in low
        # the v1 grammar block stands — kits.py routes by the field there
        assert "unknown | conflict | unsupported-assumption" in low

    def test_fielded_gap_parses(self):
        import kernel
        body = (
            "## Example Step\n\n"
            "### Scope\n\nOne sentence.\n\n"
            "### Inputs\n\n- an input\n\n"
            "### Transformation\n\n1. do the thing\n\n"
            "### Outputs\n\n- an output\n\n"
            "### Controls\n\nNone stated.\n\n"
            "### Issues\n\n"
            "> **VALIDATION REQUIRED — GAP-01:** The tolerance is not "
            "stated.\n"
            "> - **Nature:** evidenced-absence\n"
            "> - **Grounds:** SRC-001 and SRC-004 read in full; neither "
            "states a figure.\n\n"
            "```consult-meta\nsystems: []\nroles: []\n```\n")
        tdecl = kernel.load_type("process-step")
        entity = kernel.parse_entity(body, tdecl, slug="example-step")
        assert entity is not None
