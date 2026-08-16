"""M45 acceptance tests — written BEFORE the build.

Pins: the merged `consult-taxonomist` contract (carries the load-bearing
anchors of BOTH absorbed contracts), the deletion of the two old agent
files, the repointed dispatch surface (orchestrate skill + engagement.py),
and the untouched human confirm gate.

Everything skips until agents/consult-taxonomist.md exists — the merge
lands as one campaign, not piecemeal (a roster with both the taxonomist
and the surveyor is a state no commit may show).
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
TAXONOMIST = REPO / "agents" / "consult-taxonomist.md"
SKILL = REPO / "skills" / "consult-orchestrate" / "SKILL.md"

needs_merge = pytest.mark.skipif(
    not TAXONOMIST.is_file(),
    reason="M45 taxonomist not built yet — the target")


def _text(path):
    return path.read_text(encoding="utf-8")


@needs_merge
class TestContract:
    def test_old_agent_files_are_gone(self):
        assert not (REPO / "agents" / "consult-surveyor.md").exists()
        assert not (REPO / "agents" / "consult-librarian.md").exists()

    def test_direct_write_rights_over_taxonomy(self):
        low = _text(TAXONOMIST).lower()
        assert "_taxonomy" in low
        # its files under the one-writer rule — stated, not implied
        assert "one writer" in low or "one-writer" in low \
            or "your files" in low or "you write" in low

    def test_notes_bus_boundary_for_other_writers_files(self):
        low = _text(TAXONOMIST).lower()
        assert "notes" in low
        assert "propose" in low
        assert "never edit" in low or "never write" in low \
            or "not yours to edit" in low

    def test_confirm_gate_untouched(self):
        low = _text(TAXONOMIST).lower()
        assert "confirm" in low
        assert "human" in low

    def test_objective_intake_survives_the_merge(self):
        low = _text(TAXONOMIST).lower()
        assert "objective" in low

    def test_grooming_vocabulary_survives_the_merge(self):
        low = _text(TAXONOMIST).lower()
        for kind in ("duplicate-gaps", "gap-likely-answered",
                     "ctrl-missing-field"):
            assert kind in low, kind

    def test_ask_agenda_stays_a_render(self):
        low = _text(TAXONOMIST).lower()
        assert "needs.py" in low or "needs view" in low


@needs_merge
class TestDispatchSurface:
    def test_skill_names_the_taxonomist_and_not_the_old_pair(self):
        low = _text(SKILL).lower()
        assert "consult-taxonomist" in low
        assert "consult-surveyor" not in low
        assert "consult-librarian" not in low

    def test_engagement_module_repointed(self):
        src = (REPO / "scripts" / "engagement.py").read_text(encoding="utf-8")
        assert "consult-surveyor" not in src
        assert "consult-librarian" not in src

    def test_no_stray_reference_across_agents_and_scripts(self):
        for base in (REPO / "agents", REPO / "scripts"):
            for path in sorted(base.rglob("*")):
                if not path.is_file() or path.suffix not in (".md", ".py"):
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                assert "consult-surveyor" not in text, path
                assert "consult-librarian" not in text, path
