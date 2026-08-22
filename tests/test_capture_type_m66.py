"""M66 Amendment A2 items 1-3 — the read side splits by CAPTURE TYPE.

The ruling makes `process-step` the v2 capture unit. Three v1 residues stood
between that ruling and a correct read of a process-step fragment:

  1. the section parser (`doc_model.section_of_heading`) is v1's seven-section
     table — `### Inputs` mis-files to `before-you-start`, `### Transformation`
     and `### Issues` return None;
  2. the profile vocabulary (`client_config.ALL_SECTIONS` and friends) loads
     `activity` unconditionally, so a v2 `profile.yaml` is REFUSED;
  3. render letters and hides through the same v1 map, stamping
     `### C. Before You Start` over an authored `### Inputs`.

Every test below pins one half of the split: the v2 half reads through the
type declaration, the v1 half is byte-identical to what it always was.
"""

import json
from pathlib import Path

import pytest
import yaml

import client_config
import doc_model
import kernel
import orchestrate
import render


PROCESS_STEP_FRAGMENT = """## Receive Invoice

### Scope
Invoices arriving by e-mail.

### Inputs
- Supplier invoice PDF

### Transformation
The clerk keys the header into the ledger.

### Outputs
- Posted invoice

### Controls
> **CONTROL — CTRL-1:** Three-way match before posting.

### Issues
> **PAIN POINT — PP-1:** The re-key is manual.
"""

ACTIVITY_FRAGMENT = """## Receive Invoice

### Scope
Invoices arriving by e-mail.

### At a Glance
- Owner: AP clerk

### Before You Start
- Supplier invoice PDF

### Procedure
1. Key the header.

### Outputs & Evidence
- Posted invoice

### Key Controls
> **CONTROL — CTRL-1:** Three-way match before posting.

### Known Issues & Improvement Opportunities
> **PAIN POINT — PP-1:** The re-key is manual.
"""

PROCESS_STEP_PARTS = ["scope", "inputs", "transformation", "outputs",
                      "controls", "issues"]


def _manifest(area_name: str, slugs) -> dict:
    return {
        "schema": "consult-mvp-manifest/v1",
        "area": area_name, "l1": area_name.upper(), "title": area_name.upper(),
        "l2_order": ["main"],
        "components": [
            {"file": f"10_{s}.md", "heading": s, "order": i + 10,
             "role": "procedure", "slug": s, "l2": "main"}
            for i, s in enumerate(slugs)
        ],
    }


def make_central_area(tmp_path: Path, text: str = PROCESS_STEP_FRAGMENT) -> Path:
    """A central-mode (v2) area: the engagement ledger IS the mode marker."""
    root = tmp_path / "engagement"
    (root / "_sources" / "new").mkdir(parents=True)
    (root / "_sources" / "sources.yaml").write_text(
        yaml.safe_dump({"sources": []}), encoding="utf-8")
    area = root / "components" / "p2p"
    area.mkdir(parents=True)
    (area / "manifest.json").write_text(
        json.dumps(_manifest("p2p", ["receive-invoice"]), indent=2),
        encoding="utf-8")
    (area / "10_receive-invoice.md").write_text(text, encoding="utf-8")
    return area


def make_v1_area(tmp_path: Path, text: str = ACTIVITY_FRAGMENT) -> Path:
    """A v1 per-area engagement: no central ledger anywhere above it."""
    area = tmp_path / "solo" / "p2p"
    area.mkdir(parents=True)
    (area / "manifest.json").write_text(
        json.dumps(_manifest("p2p", ["receive-invoice"]), indent=2),
        encoding="utf-8")
    (area / "10_receive-invoice.md").write_text(text, encoding="utf-8")
    return area


def write_profile(area: Path, **fields) -> None:
    (area / "_client").mkdir(exist_ok=True)
    (area / "_client" / "profile.yaml").write_text(
        yaml.safe_dump({"profile": fields}), encoding="utf-8")


# --------------------------------------------------------------------------- #
# The resolver itself
# --------------------------------------------------------------------------- #
class TestCaptureType:
    def test_central_area_captures_process_step(self, tmp_path):
        area = make_central_area(tmp_path)
        assert client_config.capture_type(area) == "process-step"

    def test_v1_area_captures_activity(self, tmp_path):
        area = make_v1_area(tmp_path)
        assert client_config.capture_type(area) == "activity"

    def test_every_area_of_a_central_engagement_agrees(self, tmp_path):
        area = make_central_area(tmp_path)
        root = area.parent.parent
        assert client_config.capture_type(root) == "process-step"
        assert client_config.capture_type(area.parent) == "process-step"


# --------------------------------------------------------------------------- #
# Item 1 — heading resolution splits by type
# --------------------------------------------------------------------------- #
class TestHeadingResolution:
    def test_process_step_headings_file_under_their_own_slugs(self):
        resolve = kernel.heading_resolver("process-step")
        assert resolve("### Scope") == "scope"
        assert resolve("### Inputs") == "inputs"           # NOT before-you-start
        assert resolve("### Transformation") == "transformation"
        assert resolve("### Outputs") == "outputs"
        assert resolve("### Controls") == "controls"
        assert resolve("### Issues") == "issues"

    def test_v1_alias_misfiling_is_what_this_replaces(self):
        # The defect the ticket names, pinned so the split cannot be undone.
        assert doc_model.section_of_heading("### Inputs") == "before-you-start"
        assert doc_model.section_of_heading("### Transformation") is None
        assert doc_model.section_of_heading("### Issues") is None

    def test_activity_resolution_is_the_v1_parser(self):
        resolve = kernel.heading_resolver("activity")
        for line in ACTIVITY_FRAGMENT.split("\n"):
            assert resolve(line) == doc_model.section_of_heading(line)

    def test_letter_prefixes_are_tolerated_on_process_step(self):
        resolve = kernel.heading_resolver("process-step")
        assert resolve("### B. Inputs") == "inputs"
        assert resolve("### C. transformation") == "transformation"

    def test_unknown_heading_still_resolves_to_nothing(self):
        resolve = kernel.heading_resolver("process-step")
        assert resolve("### Quick Reference") is None
        assert resolve("#### Not a section") is None

    def test_every_declared_part_is_reachable_by_its_title(self):
        resolve = kernel.heading_resolver("process-step")
        tdecl = kernel.load_type("process-step")
        for part in tdecl.parts:
            assert resolve(f"### {part.title}") == part.slug


class TestPresentSections:
    def test_process_step_fragment_reports_all_six(self):
        present = orchestrate._present_sections(
            PROCESS_STEP_FRAGMENT,
            kernel.heading_resolver("process-step"))
        assert present == set(PROCESS_STEP_PARTS)

    def test_default_resolver_is_the_v1_parser(self):
        present = orchestrate._present_sections(ACTIVITY_FRAGMENT)
        assert "steps" in present and "quick-reference" in present

    def test_profile_drift_does_not_flag_transformation_or_issues(self, tmp_path):
        area = make_central_area(tmp_path)
        write_profile(area, sections=PROCESS_STEP_PARTS)
        state = orchestrate.AreaState(str(area))
        assert state.profile_drift() == {}

    def test_profile_drift_still_names_a_genuinely_missing_part(self, tmp_path):
        text = PROCESS_STEP_FRAGMENT.replace(
            "### Controls\n> **CONTROL — CTRL-1:** Three-way match before "
            "posting.\n\n", "")
        area = make_central_area(tmp_path, text)
        write_profile(area, sections=PROCESS_STEP_PARTS)
        state = orchestrate.AreaState(str(area))
        assert state.profile_drift() == {"receive-invoice": ["controls"]}


class TestScopeExtraction:
    def test_scope_digest_reads_a_process_step_fragment(self, tmp_path):
        import engagement
        area = make_central_area(tmp_path)
        components = area.parent
        comp = {"slug": "receive-invoice", "file": "10_receive-invoice.md"}
        lines = engagement._scope_digest(components, "p2p", comp)
        assert any("Invoices arriving by e-mail." in ln for ln in lines)
        # The Inputs body must NOT bleed into the scope digest.
        assert not any("Supplier invoice PDF" in ln for ln in lines)


# --------------------------------------------------------------------------- #
# Item 2 — profile vocabulary is a function of the capture type
# --------------------------------------------------------------------------- #
class TestProfileVocabulary:
    def test_process_step_vocabulary_is_the_declared_parts(self):
        vocab = client_config.section_vocabulary("process-step")
        assert list(vocab.sections) == PROCESS_STEP_PARTS

    def test_activity_vocabulary_is_the_module_constants(self):
        vocab = client_config.section_vocabulary("activity")
        assert list(vocab.sections) == list(client_config.ALL_SECTIONS)
        assert list(vocab.mandatory) == list(client_config.MANDATORY_SECTIONS)
        assert list(vocab.callouts) == list(client_config.ALL_CALLOUTS)

    def test_process_step_mandate_does_not_demand_v1_sections(self):
        vocab = client_config.section_vocabulary("process-step")
        assert "quick-reference" not in vocab.mandatory
        assert "steps" not in vocab.mandatory
        # The callout HOMES are what may never be dropped.
        assert {"controls", "issues", "transformation"} <= set(vocab.mandatory)

    def test_v2_profile_naming_process_step_parts_resolves(self, tmp_path):
        area = make_central_area(tmp_path)
        write_profile(area, sections=PROCESS_STEP_PARTS)
        prof = client_config.profile(area)
        assert prof.configured
        assert prof.capture_type == "process-step"
        assert prof.sections == PROCESS_STEP_PARTS

    def test_transformation_is_not_an_unknown_section(self, tmp_path):
        area = make_central_area(tmp_path)
        write_profile(area, sections=PROCESS_STEP_PARTS,
                      body_omit=["transformation"])
        prof = client_config.profile(area)
        assert prof.body_omit == ["transformation"]
        assert "transformation" in prof.hidden_sections()

    def test_inputs_is_not_aliased_away_on_a_v2_profile(self, tmp_path):
        area = make_central_area(tmp_path)
        write_profile(area, sections=PROCESS_STEP_PARTS, body_omit=["inputs"])
        prof = client_config.profile(area)
        assert prof.body_omit == ["inputs"]      # NOT "before-you-start"

    def test_a_genuinely_unknown_section_still_refuses(self, tmp_path):
        area = make_central_area(tmp_path)
        write_profile(area, sections=PROCESS_STEP_PARTS + ["quick-reference"])
        with pytest.raises(client_config.ProfileError) as exc:
            client_config.profile(area)
        assert "quick-reference" in str(exc.value)

    def test_dropping_a_callout_home_still_refuses(self, tmp_path):
        area = make_central_area(tmp_path)
        write_profile(area, sections=[s for s in PROCESS_STEP_PARTS
                                      if s != "issues"])
        with pytest.raises(client_config.ProfileError) as exc:
            client_config.profile(area)
        assert "issues" in str(exc.value)

    def test_v1_profile_with_quick_reference_still_resolves(self, tmp_path):
        area = make_v1_area(tmp_path)
        write_profile(area, sections=list(client_config.ALL_SECTIONS))
        prof = client_config.profile(area)
        assert prof.capture_type == "activity"
        assert prof.sections == list(client_config.ALL_SECTIONS)

    def test_v1_letter_aliases_still_resolve(self, tmp_path):
        area = make_v1_area(tmp_path)
        write_profile(area, sections=list("ABCDEFGH"))
        prof = client_config.profile(area)
        assert "before-you-start" in prof.sections

    def test_activity_area_demanding_process_step_parts_refuses(self, tmp_path):
        area = make_v1_area(tmp_path)
        write_profile(area, sections=PROCESS_STEP_PARTS)
        with pytest.raises(client_config.ProfileError) as exc:
            client_config.profile(area)
        # `transformation` is nobody's activity section.
        assert "transformation" in str(exc.value)

    def test_module_constants_stay_activity_valued(self):
        assert client_config.ALL_SECTIONS == [
            p.slug for p in kernel.load_type("activity").parts]
        assert client_config.MANDATORY_SECTIONS == [
            "scope", "quick-reference", "steps"]


# --------------------------------------------------------------------------- #
# Item 3 — render-time lettering and hiding come from the bound type
# --------------------------------------------------------------------------- #
class TestRenderLettering:
    def _profile(self, area):
        return client_config.profile(area)

    def test_process_step_letters_follow_the_declared_order(self, tmp_path):
        area = make_central_area(tmp_path)
        write_profile(area, sections=PROCESS_STEP_PARTS)
        out = render._apply_profile(PROCESS_STEP_FRAGMENT, self._profile(area))
        assert "### A. Scope" in out
        assert "### B. Inputs" in out
        assert "### C. Transformation" in out
        assert "### F. Issues" in out
        assert "Before You Start" not in out

    def test_process_step_letters_stop_at_f(self, tmp_path):
        area = make_central_area(tmp_path)
        write_profile(area, sections=PROCESS_STEP_PARTS)
        letters = set(self._profile(area).letters().values())
        assert letters == set("ABCDEF")
        # review_extract's location regex must still see every one of them.
        import review_extract
        for letter in sorted(letters):
            assert review_extract.SUBSECTION_LETTER_RE.match(f"{letter}. Inputs")

    def test_hiding_a_process_step_part_blanks_its_body(self, tmp_path):
        area = make_central_area(tmp_path)
        write_profile(area, sections=PROCESS_STEP_PARTS,
                      body_omit=["transformation"], derived=["appendix-a"])
        out = render._apply_profile(PROCESS_STEP_FRAGMENT, self._profile(area))
        assert "The clerk keys the header" not in out
        assert "Supplier invoice PDF" in out

    def test_v1_lettering_is_unchanged(self, tmp_path):
        area = make_v1_area(tmp_path)
        write_profile(area, sections=list(client_config.ALL_SECTIONS))
        out = render._apply_profile(ACTIVITY_FRAGMENT, self._profile(area))
        assert "### C. Before You Start" in out
        assert "### D. Procedure" in out

    def test_unprofiled_v1_fragment_letters_as_today(self):
        out = render._apply_profile(ACTIVITY_FRAGMENT, client_config.Profile())
        assert "### A. Scope" in out
        assert "### G. Known Issues & Improvement Opportunities" in out
