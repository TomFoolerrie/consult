"""M66 WP2 — capture is the brain, and the documents are renders over it.

Amendment A1 (items 1, 2b, 3, 4) and A2 (items 4, 5, 6) of
`docs/v2/M66-objective-shaped-capture.md`, built on WP1's capture-type
resolvers. What these pin:

* a central-mode (v2) confirm scaffolds PROCESS-STEP skeletons from the type
  declaration — six parts, no `Quick Reference` / `Before You Start` — and
  writes NO document furniture (no `0x_` statics, no `8x_`/`9x_` derived
  stubs, no static/derived manifest components);
* the v1 per-area confirm is byte-identical to what it always wrote;
* the drafter brief's unit line and seam titles come from the capture type,
  and the area's live `_taxonomy/` nodes are listed READ-ONLY;
* the deliverable an area builds comes from the OBJECTIVE, and a v2 area with
  no objective-named deliverable says so instead of claiming
  desktop-procedure;
* `_taxonomy/` is written only at the confirm gate — reconcile fails an area
  whose live nodes changed since the record, and stays silent where there is
  no record (a pre-M66 area);
* the confirm gate states, in one sentence, that capture is not render.

Fixture conventions per the house characterization files: everything under
`tmp_path`, observable results only, no repo-tracked writes.
"""
import json
import hashlib
from pathlib import Path

import pytest
import yaml

import brief
import client_config
import definitions
import doc_model
import kernel
import orchestrate
import reconcile
import scaffold

REPO = Path(__file__).resolve().parent.parent

PROCESS_STEP_TITLES = ["Scope", "Inputs", "Transformation", "Outputs",
                       "Controls", "Issues"]

NODE_A = """\
# Invoice Handling

## Scope
Supplier invoices from receipt to posting.
"""


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #

def _proposals(area: Path) -> Path:
    proposed = area / "_reference" / ".proposed"
    proposed.mkdir(parents=True, exist_ok=True)
    (proposed / "procedures.yaml").write_text(yaml.safe_dump({
        "procedures": [
            {"slug": "receive-invoice", "title": "Receive Invoice",
             "l2": "invoices"},
            {"slug": "pay-invoice", "title": "Pay Invoice", "l2": "payments"},
        ]
    }), encoding="utf-8")
    (proposed / "systems.yaml").write_text(yaml.safe_dump({
        "systems": [{"slug": "sap", "name": "SAP"}]
    }), encoding="utf-8")
    (proposed / "notes.yaml").write_text(yaml.safe_dump({"notes": []}),
                                         encoding="utf-8")
    return proposed


def _taxonomy_file(tmp_path: Path) -> Path:
    taxonomy = tmp_path / "taxonomy.yaml"
    taxonomy.write_text(yaml.safe_dump({
        "taxonomy": {"categories": [
            {"slug": "p2p", "subcategories": [{"slug": "invoices"},
                                              {"slug": "payments"}]},
        ]}
    }), encoding="utf-8")
    return taxonomy


def make_central(tmp_path, nodes=None, objective=None):
    """A confirm-ready CENTRAL (v2) area — the engagement ledger is the mode
    marker. Returns `(root, area, taxonomy_path)`."""
    root = tmp_path / "engagement"
    (root / "_sources" / "new").mkdir(parents=True)
    (root / "_sources" / "sources.yaml").write_text(
        yaml.safe_dump({"sources": []}), encoding="utf-8")
    area = root / "components" / "p2p"
    area.mkdir(parents=True)
    _proposals(area)
    for name, body in (nodes or {}).items():
        staged = scaffold.proposed_taxonomy_dir(area)
        staged.mkdir(parents=True, exist_ok=True)
        (staged / f"{name}.md").write_text(body, encoding="utf-8")
    if objective is not None:
        cdir = root / "components" / "_client"
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "objective.yaml").write_text(
            yaml.safe_dump({"objective": objective}), encoding="utf-8")
    return root, area, _taxonomy_file(tmp_path)


def make_v1(tmp_path):
    """A confirm-ready v1 per-area engagement: no central ledger above it."""
    area = tmp_path / "solo" / "p2p"
    area.mkdir(parents=True)
    _proposals(area)
    return area, _taxonomy_file(tmp_path)


def _manifest(area: Path) -> dict:
    return json.loads((area / "manifest.json").read_text(encoding="utf-8"))


def _roles(area: Path) -> set:
    return {c.get("role") for c in _manifest(area)["components"]}


# --------------------------------------------------------------------------- #
# A1 item 1 + A2 item 6 — the v2 scaffold captures process-step
# --------------------------------------------------------------------------- #

class TestCentralSkeletons:
    def test_skeleton_carries_exactly_the_six_declared_parts(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        assert scaffold.confirm(area, "p2p", tax, None, None) == 0
        text = (area / "10_receive-invoice.md").read_text(encoding="utf-8")
        headings = [ln[4:].strip() for ln in text.splitlines()
                    if ln.startswith("### ")]
        assert headings == PROCESS_STEP_TITLES

    def test_the_v1_only_sections_are_absent(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        text = (area / "10_pay-invoice.md").read_text(encoding="utf-8")
        assert "Quick Reference" not in text
        assert "At a Glance" not in text
        assert "Before You Start" not in text

    def test_inputs_transformation_and_issues_are_present(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        text = (area / "10_pay-invoice.md").read_text(encoding="utf-8")
        for title in ("### Inputs", "### Transformation", "### Issues"):
            assert title in text

    def test_the_unfilled_sentinel_survives(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        text = (area / "10_receive-invoice.md").read_text(encoding="utf-8")
        assert "<!-- unfilled -->" in text

    def test_the_skeleton_parses_as_a_process_step(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        tdecl = kernel.load_type("process-step")
        entity = kernel.parse_entity(
            (area / "10_receive-invoice.md").read_text(encoding="utf-8"),
            tdecl, slug="receive-invoice")
        assert set(entity.parts_bodies()) == {p.slug for p in tdecl.parts}

    def test_the_v1_skeleton_file_is_not_the_v2_source(self, tmp_path):
        """PROCEDURE_SKELETON stays, activity-only — it is the v1 shape."""
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert scaffold.PROCEDURE_SKELETON.is_file()
        text = (area / "10_receive-invoice.md").read_text(encoding="utf-8")
        assert "Step-by-Step" not in text


class TestCentralManifest:
    def test_title_no_longer_claims_desktop_procedures(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        m = _manifest(area)
        assert "Desktop Procedures" not in m["title"]
        assert m["title"] == "P2p — Process Capture"

    def test_subtitle_is_capture_neutral(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert "desktop procedures" not in _manifest(area)["subtitle"].lower()

    def test_the_manifest_validates(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert doc_model.validate_manifest(_manifest(area)) == []


# --------------------------------------------------------------------------- #
# A1 item 2b — no document furniture in v2 capture
# --------------------------------------------------------------------------- #

class TestNoFurniture:
    def test_no_static_or_derived_files_land_in_the_area(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        stray = [p.name for p in area.glob("*.md")
                 if p.name[:1].isdigit() and not p.name.startswith("10_")]
        assert stray == []

    def test_the_named_furniture_files_are_all_absent(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        for name in ("00_document-profile.md", "04_process-overview.md",
                     "06_procedure-index.md", "07_role-dictionary.md",
                     "08_systems.md", "82_dependencies.md", "84_raci.md",
                     "88_appendix-a.md", "90_appendix-b-gaps.md",
                     "91_appendix-c-screens.md"):
            assert not (area / name).exists(), name

    def test_the_manifest_lists_only_procedures(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert _roles(area) == {"procedure"}

    def test_confirm_reports_only_the_fragments_it_created(self, tmp_path,
                                                           capsys):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        out = capsys.readouterr().out
        assert "created: 10_receive-invoice.md, 10_pay-invoice.md" in out


class TestFurnitureFreeRenderPath:
    """The furniture leaves capture; the DEFINITION still supplies it."""

    def test_desktop_procedure_reports_not_yet_over_process_step_capture(
            self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        defn = definitions.load_definition("desktop-procedure")
        gaps = definitions.serviceability(defn, area)
        assert gaps, "a process-step area holds no activity entities"
        assert any("activity" in g for g in gaps)

    def test_the_definition_still_carries_every_furniture_block(self):
        defn = definitions.load_definition("desktop-procedure")
        ids = {b.id for b in defn.shape}
        for block in ("process-overview", "procedure-index", "role-dictionary",
                      "systems", "dependencies", "raci"):
            assert block in ids

    def test_findings_report_loads_and_compiles_over_the_bare_manifest(
            self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        defn = definitions.load_definition("findings-report")
        plan = definitions.compile_plan(defn, area)
        assert plan.views

    def test_findings_report_serviceability_is_an_honest_not_yet(self,
                                                                 tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        gaps = definitions.serviceability(
            definitions.load_definition("findings-report"), area)
        assert any("finding" in g.lower() for g in gaps)


# --------------------------------------------------------------------------- #
# The v1 path is untouched
# --------------------------------------------------------------------------- #

class TestV1Unchanged:
    def test_the_furniture_is_written_exactly_as_before(self, tmp_path):
        area, tax = make_v1(tmp_path)
        assert scaffold.confirm(area, "p2p", tax, None, None) == 0
        names = sorted(p.name for p in area.glob("*.md"))
        assert names == sorted(
            [sf["file"] for sf in scaffold.STATIC_FILES]
            + [d["file"] for d in scaffold.profile_derived_files(None)]
            + ["10_receive-invoice.md", "10_pay-invoice.md"])

    def test_one_static_is_byte_identical(self, tmp_path):
        area, tax = make_v1(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert (area / "04_process-overview.md").read_text(encoding="utf-8") \
            == scaffold.render_static("Process Overview")

    def test_the_title_default_is_unchanged(self, tmp_path):
        area, tax = make_v1(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        m = _manifest(area)
        assert m["title"] == "P2p — Desktop Procedures"
        assert m["subtitle"] == "Current-state desktop procedures"

    def test_the_skeleton_is_still_the_seven_section_shape(self, tmp_path):
        area, tax = make_v1(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        text = (area / "10_receive-invoice.md").read_text(encoding="utf-8")
        assert text == scaffold.render_skeleton("Receive Invoice",
                                                client_config.Profile().sections)
        assert "Before You Start" in text

    def test_the_manifest_still_carries_static_and_derived(self, tmp_path):
        area, tax = make_v1(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert _roles(area) == {"static", "procedure", "derived"}


# --------------------------------------------------------------------------- #
# A1 item 3 — the confirm gate says capture != render
# --------------------------------------------------------------------------- #

class TestCaptureIsNotRender:
    def test_the_sentence_is_printed_in_v2(self, tmp_path, capsys):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        out = capsys.readouterr().out
        assert scaffold.CAPTURE_NOT_RENDER in out
        assert "renders over it" in out

    def test_the_sentence_is_absent_in_v1(self, tmp_path, capsys):
        area, tax = make_v1(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert scaffold.CAPTURE_NOT_RENDER not in capsys.readouterr().out

    def test_the_skill_relays_it(self):
        skill = (REPO / "skills" / "consult-orchestrate"
                 / "SKILL.md").read_text(encoding="utf-8")
        assert "capture is not a render" in skill.lower()


# --------------------------------------------------------------------------- #
# A2 items 4 + 5 — the brief and the deliverable default
# --------------------------------------------------------------------------- #

def _drafter_brief(area: Path, slug: str) -> str:
    return brief.drafter_brief(area, _manifest(area), slug)


class TestBriefUnitLine:
    def test_v2_says_process_step_and_names_its_path_document(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        out = _drafter_brief(area, "receive-invoice")
        assert "YOUR UNIT: process-step" in out
        assert "agents/drafting/process-step.md" in out

    def test_v1_still_says_activity(self, tmp_path):
        area, tax = make_v1(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        out = _drafter_brief(area, "receive-invoice")
        assert "YOUR UNIT: activity" in out
        assert "agents/drafting/activity.md" in out

    def test_the_unit_line_no_longer_needs_derived_components(self, tmp_path):
        """The furniture is gone; the unit line must not have depended on it."""
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert _roles(area) == {"procedure"}
        assert "YOUR UNIT: process-step" in _drafter_brief(area,
                                                           "receive-invoice")


class TestSeamSections:
    def test_v1_seam_titles_stay_frozen(self):
        assert brief.SEAM_SECTIONS == "Scope, At a Glance, Outputs & Evidence"
        assert brief.seam_sections("activity") == brief.SEAM_SECTIONS

    def test_process_step_seam_titles_come_from_the_declaration(self):
        assert brief.seam_sections("process-step") == "Scope, Outputs"

    def test_the_v2_brief_prints_the_derived_titles(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        proposed = area / "_reference" / ".proposed"
        (proposed / "procedures.yaml").write_text(yaml.safe_dump({
            "procedures": [
                {"slug": "receive-invoice", "title": "Receive Invoice",
                 "l2": "invoices"},
                {"slug": "pay-invoice", "title": "Pay Invoice",
                 "l2": "payments", "upstream": ["receive-invoice"]},
            ]
        }), encoding="utf-8")
        scaffold.confirm(area, "p2p", tax, None, None)
        out = _drafter_brief(area, "pay-invoice")
        assert "seam sections only: Scope, Outputs" in out
        assert "At a Glance" not in out


class TestBriefListsTheSurvey:
    def test_live_nodes_are_listed_read_only(self, tmp_path):
        _root, area, tax = make_central(tmp_path,
                                        nodes={"invoice-handling": NODE_A})
        scaffold.confirm(area, "p2p", tax, None, None)
        out = _drafter_brief(area, "receive-invoice")
        assert "_taxonomy/invoice-handling.md" in out
        assert "survey scope notes — read-only, never edit" in out

    def test_an_area_without_nodes_lists_nothing(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert "survey scope notes" not in _drafter_brief(area,
                                                          "receive-invoice")

    def test_the_drafter_contract_states_the_rule(self):
        text = (REPO / "agents" / "consult-drafter.md").read_text(
            encoding="utf-8").lower()
        assert "_taxonomy/" in text
        assert "never edit" in text


class TestDeliverableDefault:
    def test_the_objective_names_the_deliverable(self, tmp_path):
        _root, area, tax = make_central(
            tmp_path, objective={"goal": "Assess the P2P cycle",
                                 "deliverables": ["findings-report"]})
        scaffold.confirm(area, "p2p", tax, None, None)
        assert definitions.area_deliverable(area) == "findings-report"
        assert orchestrate.area_definition(str(area)) == "findings-report"

    def test_a_v2_area_without_an_objective_is_honestly_unset(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert definitions.area_deliverable(area) is None
        assert orchestrate.area_definition(str(area)) \
            == orchestrate.UNSET_DEFINITION
        assert orchestrate.area_definition(str(area)) != "desktop-procedure"

    def test_the_unset_signal_carries_a_message(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        orchestrate.emit_render(str(area), "out.docx")
        sig = json.loads((area / ".render.json").read_text(encoding="utf-8"))
        assert sig["definition"] == orchestrate.UNSET_DEFINITION
        assert "objective" in sig["definition_note"]

    def test_v1_still_defaults_to_desktop_procedure(self, tmp_path):
        area, tax = make_v1(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        assert definitions.area_deliverable(area) == "desktop-procedure"
        assert orchestrate.area_definition(str(area)) == "desktop-procedure"


# --------------------------------------------------------------------------- #
# A1 item 4 — the node guard
# --------------------------------------------------------------------------- #

def _reconcile_errors(area: Path) -> list[str]:
    ctx = reconcile.Ctx(area, _manifest(area))
    reconcile.check_taxonomy_record(ctx)
    return ctx.errors


class TestNodeGuard:
    def test_confirm_records_the_live_node_hashes(self, tmp_path):
        _root, area, tax = make_central(tmp_path,
                                        nodes={"invoice-handling": NODE_A})
        scaffold.confirm(area, "p2p", tax, None, None)
        record = json.loads(
            (area / scaffold.TAXONOMY_RECORD).read_text(encoding="utf-8"))
        digest = hashlib.sha256(NODE_A.encode("utf-8")).hexdigest()
        assert record["nodes"] == {"invoice-handling.md": digest}

    def test_an_untouched_survey_reconciles_clean(self, tmp_path):
        _root, area, tax = make_central(tmp_path,
                                        nodes={"invoice-handling": NODE_A})
        scaffold.confirm(area, "p2p", tax, None, None)
        assert _reconcile_errors(area) == []

    def test_editing_a_live_node_is_an_error_naming_the_file(self, tmp_path):
        _root, area, tax = make_central(tmp_path,
                                        nodes={"invoice-handling": NODE_A})
        scaffold.confirm(area, "p2p", tax, None, None)
        (scaffold.live_taxonomy_dir(area) / "invoice-handling.md").write_text(
            NODE_A + "\nA drafter's edit.\n", encoding="utf-8")
        errors = _reconcile_errors(area)
        assert len(errors) == 1
        assert "_taxonomy/invoice-handling.md" in errors[0]
        assert "written only at the confirm gate" in errors[0]

    def test_a_node_added_outside_the_gate_is_an_error(self, tmp_path):
        _root, area, tax = make_central(tmp_path,
                                        nodes={"invoice-handling": NODE_A})
        scaffold.confirm(area, "p2p", tax, None, None)
        (scaffold.live_taxonomy_dir(area) / "smuggled.md").write_text(
            NODE_A, encoding="utf-8")
        assert any("smuggled.md" in e for e in _reconcile_errors(area))

    def test_a_deleted_node_is_an_error(self, tmp_path):
        _root, area, tax = make_central(tmp_path,
                                        nodes={"invoice-handling": NODE_A})
        scaffold.confirm(area, "p2p", tax, None, None)
        (scaffold.live_taxonomy_dir(area) / "invoice-handling.md").unlink()
        assert any("invoice-handling.md" in e for e in _reconcile_errors(area))

    def test_a_pre_m66_area_with_no_record_stays_silent(self, tmp_path):
        _root, area, tax = make_central(tmp_path,
                                        nodes={"invoice-handling": NODE_A})
        scaffold.confirm(area, "p2p", tax, None, None)
        (area / scaffold.TAXONOMY_RECORD).unlink()
        (scaffold.live_taxonomy_dir(area) / "invoice-handling.md").write_text(
            "anything at all\n", encoding="utf-8")
        assert _reconcile_errors(area) == []

    def test_promote_taxonomy_refreshes_the_record(self, tmp_path):
        _root, area, tax = make_central(tmp_path)
        scaffold.confirm(area, "p2p", tax, None, None)
        staged = scaffold.proposed_taxonomy_dir(area)
        staged.mkdir(parents=True, exist_ok=True)
        (staged / "later-node.md").write_text(NODE_A, encoding="utf-8")
        scaffold.promote_taxonomy(area)
        record = json.loads(
            (area / scaffold.TAXONOMY_RECORD).read_text(encoding="utf-8"))
        assert "later-node.md" in record["nodes"]
        assert _reconcile_errors(area) == []

    def test_the_guard_is_registered_in_the_check_list(self):
        assert reconcile.check_taxonomy_record in reconcile.CHECKS
