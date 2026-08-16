"""M48 acceptance tests — written BEFORE the build.

Pins: the drafter contract split (shared law + one path document per unit,
no rule stated twice), the brief's YOUR UNIT line naming the path document
to read, the revise-pass model-tier hint in the orchestrate skill, and the
roster audit's mechanical residue (no reference to a retired agent
survives).

Everything skips until agents/drafting/ exists — the split lands whole.
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
ACTIVITY_PATH = REPO / "agents" / "drafting" / "activity.md"
STEP_PATH = REPO / "agents" / "drafting" / "process-step.md"
SKILL = REPO / "skills" / "consult-orchestrate" / "SKILL.md"

needs_split = pytest.mark.skipif(
    not (REPO / "agents" / "drafting").is_dir(),
    reason="M48 drafter split not built yet — the target")


def _low(path):
    return path.read_text(encoding="utf-8").lower()


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


@needs_split
class TestSplit:
    def test_three_documents_exist(self):
        assert DRAFTER.is_file()
        assert ACTIVITY_PATH.is_file()
        assert STEP_PATH.is_file()

    def test_unit_paths_live_in_their_own_documents_only(self):
        # the v2 drafting path heading (M43) moves whole to the step doc;
        # the v1 seven-section table moves whole to the activity doc
        assert "what you produce — a process step" in _low(STEP_PATH)
        assert "what you produce — a process step" not in _low(DRAFTER)
        assert "f. key controls" in _low(ACTIVITY_PATH)
        assert "f. key controls" not in _low(DRAFTER)

    def test_shared_law_stays_shared_and_single_homed(self):
        # the minting bars are unit-agnostic law: in the shared contract,
        # in NEITHER path document
        assert "minting bar" in _low(DRAFTER)
        assert "minting bar" not in _low(ACTIVITY_PATH)
        assert "minting bar" not in _low(STEP_PATH)

    def test_paths_never_cross_reference_the_other_unit(self):
        assert "seven section" not in _low(STEP_PATH)
        assert "process-step" not in _low(ACTIVITY_PATH)

    def test_shared_contract_routes_by_unit(self):
        low = _low(DRAFTER)
        assert "drafting/activity.md" in low
        assert "drafting/process-step.md" in low
        assert "your unit" in low


@needs_split
class TestBriefRouting:
    def _brief(self, area, slug):
        import brief
        manifest = json.loads((area / "manifest.json").read_text("utf-8"))
        return brief.drafter_brief(area, manifest, slug)

    def test_ipo_brief_names_the_step_path_document(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        out = self._brief(area, "receive-invoice")
        assert "drafting/process-step.md" in out
        assert "drafting/activity.md" not in out

    def test_v1_brief_names_the_activity_path_document(self):
        out = self._brief(P2P_AREA, "goods-receipt")
        assert "drafting/activity.md" in out
        assert "drafting/process-step.md" not in out


@needs_split
class TestReviseTier:
    def test_skill_carries_the_revise_tier_hint(self):
        low = SKILL.read_text(encoding="utf-8").lower()
        assert "revise" in low or "update" in low
        assert "tier" in low or "cheaper" in low or "model" in low
        # first drafts stay on the strong tier — stated, not implied
        assert "first draft" in low or "first-draft" in low


@needs_split
class TestRosterAudit:
    def test_ticket_records_a_ruling_per_row(self):
        # the audit table resolves at close-out: no "fold candidates" or
        # "posture going in" hedging survives in the ticket
        text = (REPO / "docs" / "v2" / "M48-efficiency-pass.md").read_text(
            encoding="utf-8").lower()
        assert "built" in text
        assert "posture going in" not in text

    def test_no_reference_to_a_retired_agent_survives(self):
        # the ticket's close-out amendment lists retirements; whatever it
        # lists must be gone from the dispatch surface. Mechanical floor
        # here: every agent file the skill dispatches must exist.
        import re
        skill = SKILL.read_text(encoding="utf-8")
        for name in set(re.findall(r"agents/(consult-[a-z-]+\.md)", skill)):
            assert (REPO / "agents" / name).is_file(), name
