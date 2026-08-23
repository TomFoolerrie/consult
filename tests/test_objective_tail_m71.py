"""M71 acceptance tests — the tail reads the objective.

Written BEFORE the build. What they pin:

  * Part A — the `draft_ready` gate's `accept` note names the spend the gate
    is actually holding back (`details.would_spend`), in BOTH directions; a
    render-bound gate carries the render TARGET (`definition`); and a target
    whose serviceability would report "not yet" is said so in one sentence,
    which for a findings-bound deliverable names the human-called analyst.
    The answers list, the accept COMMAND and `would_spend` are untouched.
  * Part B — guard 10's `render` action carries the same "not yet" report, so
    the human decides before paying a render that would refuse. A v1 area's
    `render` action carries nothing new.
  * Part C — the skill's tail prose states the real rule rather than the v1
    tail, and the synthesize HANDLER mechanics survive.
  * No new dispatch: nothing in the advisor fires `consult-analyst`, and the
    human-trigger doctrine passage stands.
"""
import json
import os
from pathlib import Path

import yaml

import orchestrate
import definitions
import scope_delta

from test_stage_gates import simple, walk_to_gate

REPO = Path(__file__).resolve().parent.parent
SKILL = REPO / "skills" / "consult-orchestrate" / "SKILL.md"


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

def v2_area(tmp_path, deliverable="findings-report"):
    """A central-mode (v2) area whose OBJECTIVE names a deliverable, walked to
    the draft-ready gate. One filled procedure, no agent-derived components —
    so `synthesize` structurally cannot fire and `would_spend` is `render`."""
    root = tmp_path / "engagement"
    (root / "_sources" / "new").mkdir(parents=True)
    (root / "_sources" / "sources.yaml").write_text(
        yaml.safe_dump({"sources": []}), encoding="utf-8")
    cdir = root / "components" / "_client"
    cdir.mkdir(parents=True)
    (cdir / "objective.yaml").write_text(yaml.safe_dump(
        {"objective": {"goal": "Assess the P2P cycle",
                       "deliverables": [deliverable],
                       "cycles": ["procure-to-pay"]}}), encoding="utf-8")
    area = root / "components" / "p2p"
    area.mkdir(parents=True)
    (area / "manifest.json").write_text(json.dumps(
        {"schema": "consult-mvp-manifest/v1", "area": "p2p", "l1": "fin",
         "l2_order": ["ops"], "title": "T", "subtitle": "S",
         "components": [{"file": "10_receive.md", "role": "procedure",
                         "slug": "receive", "heading": "Receive",
                         "l2": "ops", "order": 10}]}), encoding="utf-8")
    (area / "10_receive.md").write_text("## Receive\n\nReal drafted content.\n",
                                        encoding="utf-8")
    (area / "_reference").mkdir()
    (area / "_reference" / "systems.yaml").write_text(
        "systems:\n  - slug: sap\n    name: SAP\n", encoding="utf-8")
    return str(area)


def accept_note(decision):
    answers = {a["name"]: a for a in decision["details"]["answers"]}
    return answers["accept"]["note"]


# --------------------------------------------------------------------------- #
# Part A — the gate reads the deliverable it is gating for
# --------------------------------------------------------------------------- #

class TestAcceptNoteTracksWouldSpend:
    def test_a_render_bound_gate_names_render(self, tmp_path):
        area = v2_area(tmp_path)
        d = walk_to_gate(area)
        assert d["action"] == "draft_ready"
        assert d["details"]["would_spend"] == "render"
        assert "lets the ladder through to render" in accept_note(d)
        assert "synthesize" not in accept_note(d)

    def test_a_v1_gate_still_names_synthesize(self, tmp_path):
        area = simple(tmp_path)
        d = walk_to_gate(area)
        assert d["details"]["would_spend"] == "synthesize"
        assert "lets the ladder through to synthesize" in accept_note(d)
        # the render target is not named where render is not the next spend
        assert "definition" not in d["details"]

    def test_a_v1_gate_holding_render_names_render_and_its_target(self,
                                                                 tmp_path):
        area = simple(tmp_path)
        scope_delta.commit(area, "dependencies")
        scope_delta.commit(area, "raci")
        d = walk_to_gate(area)
        assert d["details"]["would_spend"] == "render"
        assert "lets the ladder through to render" in accept_note(d)
        assert d["details"]["definition"] == "desktop-procedure"
        # a serviceable v1 deliverable says nothing about "not yet"
        assert "deliverable_not_yet" not in d["details"]

    def test_the_gate_shape_is_unchanged(self, tmp_path):
        """The pinned seams: three answers, the exact accept command."""
        area = v2_area(tmp_path)
        d = walk_to_gate(area)
        answers = {a["name"]: a for a in d["details"]["answers"]}
        assert sorted(answers) == ["accept", "consolidate", "read"]
        assert answers["accept"]["command"] == (
            "scripts/orchestrate.py accept-draft --area %s" % area)
        assert answers["accept"]["cost"] == "free"
        assert ".draft_ready.json" in answers["accept"]["note"]


class TestTheGateNamesTheRenderTarget:
    def test_the_definition_is_the_objectives_deliverable(self, tmp_path):
        area = v2_area(tmp_path)
        d = walk_to_gate(area)
        assert d["details"]["definition"] == "findings-report"
        assert d["details"]["definition"] == orchestrate.area_definition(area)

    def test_an_empty_findings_register_names_the_analyst(self, tmp_path):
        area = v2_area(tmp_path)
        d = walk_to_gate(area)
        block = d["details"]["deliverable_not_yet"]
        assert "not yet" in block["note"]
        assert "analyst" in block["note"]
        # a statement of the path, never a dispatch
        assert "human" in block["note"]
        # the gaps are the serviceability read, not a re-derivation
        defn = definitions.resolve_definition(area, "findings-report")
        assert block["gaps"] == definitions.serviceability(defn, area)
        assert block["gaps"] == [
            r["gap"] for r in definitions.serviceability_records(defn, area)]

    def test_accepted_findings_close_the_not_yet(self, tmp_path):
        area = v2_area(tmp_path)
        reg = Path(area).parent.parent / "_registers"
        reg.mkdir(parents=True, exist_ok=True)
        (reg / "findings.yaml").write_text(yaml.safe_dump({"findings": [
            {"id": "F-001", "status": "accepted", "area": "p2p",
             "claim": "Invoices are approved after payment.",
             "theme": "controls"}]}), encoding="utf-8")
        d = walk_to_gate(area)
        assert d["details"]["definition"] == "findings-report"
        assert "deliverable_not_yet" not in d["details"]


# --------------------------------------------------------------------------- #
# Part B — the render action refuses forward, not backward
# --------------------------------------------------------------------------- #

class TestRenderActionCarriesServiceability:
    def test_render_reports_not_yet_for_an_unserved_deliverable(self,
                                                                tmp_path):
        area = v2_area(tmp_path)
        walk_to_gate(area)
        orchestrate.accept_draft(area)
        d = orchestrate.decide(area)
        assert d["action"] == "render"          # the action name is unchanged
        assert d["details"]["definition"] == "findings-report"
        assert d["details"]["serviceability"] == "not yet"
        defn = definitions.resolve_definition(area, "findings-report")
        assert d["details"]["gaps"] == definitions.serviceability(defn, area)
        assert "not yet" in d["details"]["note"]
        assert "analyst" in d["details"]["note"]

    def test_a_v1_render_action_is_byte_identical(self, tmp_path):
        area = simple(tmp_path)
        scope_delta.commit(area, "dependencies")
        scope_delta.commit(area, "raci")
        walk_to_gate(area)
        orchestrate.accept_draft(area)
        d = orchestrate.decide(area)
        assert d["action"] == "render"
        assert d["reason"] == "views current and reconciled; no fresh .docx"
        # nothing but the standing git advisory rides a serviceable render
        assert set(d.get("details", {})) <= {"git"}

    def test_a_served_v2_render_says_nothing_new(self, tmp_path):
        area = v2_area(tmp_path)
        reg = Path(area).parent.parent / "_registers"
        reg.mkdir(parents=True, exist_ok=True)
        (reg / "findings.yaml").write_text(yaml.safe_dump({"findings": [
            {"id": "F-001", "status": "accepted", "area": "p2p",
             "claim": "Invoices are approved after payment.",
             "theme": "controls"}]}), encoding="utf-8")
        walk_to_gate(area)
        orchestrate.accept_draft(area)
        d = orchestrate.decide(area)
        assert d["action"] == "render"
        assert set(d.get("details", {})) <= {"git"}


# --------------------------------------------------------------------------- #
# Part C — the skill stops narrating v1 as the default
# --------------------------------------------------------------------------- #

class TestSkillTailProse:
    def setup_method(self):
        self.text = SKILL.read_text(encoding="utf-8")

    def test_the_draft_ready_row_reads_would_spend_and_the_target(self):
        row = [ln for ln in self.text.splitlines()
               if ln.startswith("| `draft_ready` |")]
        assert len(row) == 1
        low = row[0].lower()
        assert "details.would_spend" in low
        assert "details.definition" in low
        assert "deliverable_not_yet" in low
        assert "analyst" in low

    def test_the_synthesize_row_keeps_its_mechanics(self):
        row = [ln for ln in self.text.splitlines()
               if ln.startswith("| `synthesize` |")]
        assert len(row) == 1
        low = row[0].lower()
        assert "scope_delta.py" in low and "commit" in low
        assert "consult-dependencies" in low and "consult-raci" in low
        # ... but no longer as the universal post-accept default
        assert "manifest" in low

    def test_the_framing_no_longer_promises_synthesize_after_every_accept(self):
        low = " ".join(self.text.lower().split())
        # the real rule is stated somewhere in the tail framing
        assert "render-the-deliverable" in low
        assert ("the post-accept spend is whatever the manifest and the "
                "objective's deliverable make it") in low
        # ... and the framing points at the advisor's own computed answer
        assert "details.would_spend" in low

    def test_the_render_row_relays_the_not_yet_report(self):
        row = [ln for ln in self.text.splitlines()
               if ln.startswith("| `render` |")]
        assert len(row) == 1
        assert "not yet" in row[0].lower()


class TestNoNewDispatch:
    def test_the_advisor_never_names_the_analyst_agent(self):
        src = (REPO / "scripts" / "orchestrate.py").read_text(encoding="utf-8")
        assert "consult-analyst" not in src

    def test_the_human_trigger_doctrine_stands(self):
        low = SKILL.read_text(encoding="utf-8").lower()
        assert "no action handler fires it" in low
        assert "never inside the drafting loop" in low
