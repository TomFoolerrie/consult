"""M46 acceptance tests — written BEFORE the build.

Pins: the interview-agenda deliverable definition (loads through the
four-stage loader; binds the needs view — the first consumer of M44's
`engagement-needs`), the per-role render over the IPO fixture, the
refusals, and the human-trigger rule (no agent, no automatic loop).

Everything skips until kernel/deliverables/interview-agenda.yaml exists.
"""

import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
DEFINITION = REPO / "kernel" / "deliverables" / "interview-agenda.yaml"
SKILL = REPO / "skills" / "consult-orchestrate" / "SKILL.md"

needs_agenda = pytest.mark.skipif(
    not DEFINITION.is_file(),
    reason="M46 interview-agenda definition not built yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def write_objective(area):
    cdir = area / "_client"
    cdir.mkdir(exist_ok=True)
    (cdir / "objective.yaml").write_text(
        "objective:\n"
        "  goal: Deliver a controls matrix.\n"
        "  deliverables: [process-controls-matrix]\n"
        "  cycles: [procure-to-pay]\n", encoding="utf-8")


@needs_agenda
class TestDefinition:
    def test_loads_through_the_four_stage_loader(self, tmp_path):
        import definitions
        root, area = ipo_copy(tmp_path)
        defn = definitions.load_definition("interview-agenda", area=area)
        assert defn is not None

    def test_binds_the_needs_view(self, tmp_path):
        # the first consumer of M44's engagement-needs — the join is declared
        # in the definition, never inferred by a writer
        import definitions
        root, area = ipo_copy(tmp_path)
        defn = definitions.load_definition("interview-agenda", area=area)
        assert "engagement-needs" in str(defn.bindings) \
            or "needs" in str(defn.bindings)


@needs_agenda
class TestRender:
    def test_renders_for_a_fixture_role(self, tmp_path):
        import agenda
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        out = agenda.render(area, role="ap-manager")
        assert isinstance(out, str) and out.strip()
        assert "ap manager" in out.lower() or "ap-manager" in out.lower() \
            or "accounts payable manager" in out.lower()

    def test_carries_recorded_needs_for_the_roles_territory(self, tmp_path):
        import agenda
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        out = agenda.render(area, role="ap-manager")
        assert "GAP-" in out          # the fixture's open gaps surface

    def test_unknown_role_refuses_by_name(self, tmp_path):
        import agenda
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        with pytest.raises(Exception) as exc:
            agenda.render(area, role="chief-basket-weaver")
        assert "chief-basket-weaver" in str(exc.value)

    def test_nothing_to_ask_is_a_report_not_a_crash(self, tmp_path):
        # a role with no needs in its territory gets an honest empty agenda
        import agenda
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        out = agenda.render(area, role="corporate-controller")
        assert isinstance(out, str) and out.strip()

    def test_read_only(self, tmp_path):
        import agenda
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        before = {p: (p.stat().st_mtime_ns, p.stat().st_size)
                  for p in root.rglob("*") if p.is_file()}
        agenda.render(area, role="ap-manager")
        after = {p: (p.stat().st_mtime_ns, p.stat().st_size)
                 for p in root.rglob("*") if p.is_file()}
        assert before == after


@needs_agenda
class TestHumanTrigger:
    def test_skill_documents_the_human_trigger(self):
        low = SKILL.read_text(encoding="utf-8").lower()
        assert "interview-agenda" in low or "interview agenda" in low
        assert "human" in low and ("ad hoc" in low or "ad-hoc" in low
                                   or "on request" in low)

    def test_no_agent_contract_generates_agendas(self):
        # an agent MAY cite agenda-worthy clusters; none may generate. The
        # mechanical pin: no agent contract instructs running the agenda
        # render.
        for path in sorted((REPO / "agents").rglob("*.md")):
            low = path.read_text(encoding="utf-8").lower()
            assert "agenda.py" not in low, path
