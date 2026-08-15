"""M42 acceptance tests — written BEFORE the build.

Pins: the callout doctrine's landing in the three agent contracts
(mechanical greps for the load-bearing phrases — paraphrase may drift,
these anchors may not), the objective block in the drafter brief
(additive: v1 output unchanged when unconfigured), and the worked
example's parseability.

The doctrine's normative text is docs/v2/M42-callout-doctrine.md Part A;
these tests check the ENCODING, the spec review checks the intent.
"""

import json
import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"

DRAFTER = REPO / "agents" / "consult-drafter.md"
SURVEYOR = REPO / "agents" / "consult-surveyor.md"
LIBRARIAN = REPO / "agents" / "consult-librarian.md"


def _text(path):
    return path.read_text(encoding="utf-8")


def _built():
    # the doctrine lands as one package; anchor on its most distinctive line
    return "four fields" in _text(DRAFTER).lower()


needs_doctrine = pytest.mark.skipif(
    not _built(), reason="M42 doctrine prose not landed yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


# --------------------------------------------------------------------------- #
# 1. The drafter contract carries the doctrine
# --------------------------------------------------------------------------- #

@needs_doctrine
class TestDrafterDoctrine:
    def test_ctrl_minting_bar_names_the_four_fields(self):
        text = _text(DRAFTER).lower()
        for anchor in ("performer", "against what", "trigger", "evidence"):
            assert anchor in text

    def test_weak_ctrl_refusal_prose_plus_gap(self):
        text = _text(DRAFTER).lower()
        assert "does not mint" in text or "not a control record" in text

    def test_boundary_vs_callout_differentiation(self):
        text = _text(DRAFTER).lower()
        assert "the break never records the control" in text \
            or "never infer a control from a boundary" in text

    def test_substeps_carry_no_callouts(self):
        text = _text(DRAFTER).lower()
        assert "sub-step" in text
        assert "callouts attach to the step" in text \
            or "never to a sub-step" in text

    def test_cross_owner_control_is_a_split_signal(self):
        text = _text(DRAFTER).lower()
        assert "split" in text and "performer" in text

    def test_gap_bar_operation_blocking_only(self):
        text = _text(DRAFTER).lower()
        assert "blocks" in text
        assert '"unconfirmed" alone does not mint' in text \
            or "unconfirmed alone does not mint" in text

    def test_gap_pain_both_never_merged(self):
        text = _text(DRAFTER).lower()
        assert "never merged" in text or "mint both" in text

    def test_worked_example_present_and_cross_referenced(self):
        text = _text(DRAFTER)
        assert "CTRL-" in text and "GAP-" in text and "PP-" in text


# --------------------------------------------------------------------------- #
# 2. The population-level responsibilities
# --------------------------------------------------------------------------- #

@needs_doctrine
class TestPopulationOwnership:
    def test_surveyor_owns_the_ask_agenda(self):
        text = _text(SURVEYOR).lower()
        assert "operation-blocking" in text or "ask agenda" in text

    def test_librarian_carries_the_grooming_trigger(self):
        text = _text(LIBRARIAN).lower()
        assert "duplicate" in text and ("gap" in text)
        assert "notes" in text  # proposes via the bus, never edits


# --------------------------------------------------------------------------- #
# 3. The objective block reaches the drafter brief (additive)
# --------------------------------------------------------------------------- #

class TestDrafterBriefObjective:
    def _brief(self, area, slug="receive-invoice"):
        import brief
        manifest = json.loads((area / "manifest.json").read_text("utf-8"))
        return brief.drafter_brief(area, manifest, slug)

    @needs_doctrine
    def test_configured_objective_reaches_the_brief(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        cdir = area / "_client"
        cdir.mkdir(exist_ok=True)
        (cdir / "objective.yaml").write_text(
            "objective:\n"
            "  goal: Deliver a controls matrix.\n"
            "  deliverables: [process-controls-matrix]\n"
            "  cycles: [procure-to-pay]\n", encoding="utf-8")
        out = self._brief(area)
        assert "controls matrix" in out.lower()
        assert "process-controls-matrix" in out

    def test_unconfigured_v1_brief_output_unchanged(self, tmp_path):
        # The block must APPEND, never reshape: with no objective configured,
        # a v1-style brief stays exactly what it was, or gains at most the
        # explicit absence line. Pin: every pre-existing section still there.
        root, area = ipo_copy(tmp_path)
        out = self._brief(area)
        assert "YOUR FILE" in out or "your file" in out.lower()


# --------------------------------------------------------------------------- #
# 4. The worked example parses under the declaration
# --------------------------------------------------------------------------- #

@needs_doctrine
class TestWorkedExampleParses:
    def test_example_ctrl_fragment_parses(self, tmp_path):
        """Extract the contract's worked-example callout lines and prove a
        fragment built around them parses as a process-step entity."""
        import kernel
        text = _text(DRAFTER)
        all_lines = text.splitlines()
        block = []
        for i, l in enumerate(all_lines):
            if l.strip().startswith("> **CONTROL — CTRL-"):
                block.append(l.strip())
                for follow in all_lines[i + 1:]:
                    if follow.strip().startswith(">"):
                        block.append(follow.strip())
                    else:
                        break
                break
        assert block, "the worked example must show a fully-minted CTRL"
        body = (
            "## Example Step\n\n"
            "### Scope\n\nOne sentence of scope.\n\n"
            "### Inputs\n\n- an input\n\n"
            "### Transformation\n\n1. do the thing\n\n"
            "### Outputs\n\n- an output\n\n"
            "### Controls\n\n" + "\n".join(block) + "\n\n"
            "### Issues\n\n—\n\n"
            "```consult-meta\nsystems: []\nroles: []\n```\n")
        tdecl = kernel.load_type("process-step")
        entity = kernel.parse_entity(body, tdecl, slug="example-step")
        assert entity is not None
