"""M40 acceptance tests — written BEFORE the build.

Pins: the materialize verb (definition view blocks -> manifest derived
components, sync_profile's discipline plan-driven), the three missing
python view writers (information-requests, open-validations,
findings-by-theme), and the proof that the two never-rendered shipped
definitions (information-request, findings-report) render end-to-end
over the IPO fixture.

Skips until scripts/plan_views.py exists; materialize tests additionally
skip until definitions grows the verb (the two work packages land in
parallel).
"""

import json
import shutil
from pathlib import Path

import pytest

plan_views = pytest.importorskip(
    "plan_views", reason="M40 view-writer module not built yet — the target")

import definitions  # noqa: E402  (present since M35)

IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"

needs_materialize = pytest.mark.skipif(
    not hasattr(definitions, "materialize_views"),
    reason="M40 materialize verb not built yet — the target")


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def manifest(area):
    return json.loads((area / "manifest.json").read_text(encoding="utf-8"))


def derived(area):
    return [c for c in manifest(area)["components"]
            if c.get("role") == "derived"]


def fingerprint(base):
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in base.rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- #
# 1. The materialize verb
# --------------------------------------------------------------------------- #

@needs_materialize
class TestMaterialize:
    def test_adds_six_key_entries_for_each_view_block(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        definitions.materialize_views(area, name="information-request")
        by_kind = {c["derived_kind"]: c for c in derived(area)}
        for kind in ("information-requests", "open-validations"):
            comp = by_kind[kind]
            assert comp["role"] == "derived"
            assert comp["writer"] == "python"
            assert comp["heading"]          # the block's title
            assert comp["file"] and (area / comp["file"]).is_file()
            assert isinstance(comp["order"], int)

    def test_new_views_land_after_existing_components_in_block_order(
            self, tmp_path):
        root, area = ipo_copy(tmp_path)
        before_max = max(c["order"] for c in manifest(area)["components"])
        definitions.materialize_views(area, name="information-request")
        by_kind = {c["derived_kind"]: c for c in derived(area)}
        req = by_kind["information-requests"]["order"]
        val = by_kind["open-validations"]["order"]
        assert before_max < req < val   # block order: requests before gaps

    def test_idempotent_second_call_is_a_noop(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        definitions.materialize_views(area, name="information-request")
        before = fingerprint(area)
        definitions.materialize_views(area, name="information-request")
        assert fingerprint(area) == before

    def test_existing_hand_authored_entry_preserved_byte_for_byte(
            self, tmp_path):
        # The fixture's matrix component (hand-authored, order 20) is exactly
        # the case the preservation rule exists for.
        root, area = ipo_copy(tmp_path)
        before = [c for c in derived(area)
                  if c["derived_kind"] == "process-controls-matrix"]
        definitions.materialize_views(area, name="process-controls-matrix")
        after = [c for c in derived(area)
                 if c["derived_kind"] == "process-controls-matrix"]
        assert after == before and len(after) == 1

    def test_non_derived_components_never_touched(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        before = [c for c in manifest(area)["components"]
                  if c.get("role") != "derived"]
        definitions.materialize_views(area, name="findings-report")
        after = [c for c in manifest(area)["components"]
                 if c.get("role") != "derived"]
        assert after == before

    def test_manifest_validates_after_materialize(self, tmp_path):
        import doc_model
        root, area = ipo_copy(tmp_path)
        definitions.materialize_views(area, name="information-request")
        assert doc_model.validate_manifest(manifest(area)) == []

    def test_reports_its_delta(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        report = definitions.materialize_views(
            area, name="information-request")
        joined = str(report)
        assert "information-requests" in joined
        assert "open-validations" in joined


# --------------------------------------------------------------------------- #
# 2. The writers, over the fixture's facts
# --------------------------------------------------------------------------- #

class TestOpenValidations:
    def test_carries_every_gap_with_attribution(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        body = plan_views.build_open_validations({"area": area})
        for gap in ("GAP-01", "GAP-02", "GAP-03", "GAP-04"):
            assert gap in body
        assert "SRC-" in body    # evidence attribution reaches the reader


class TestInformationRequests:
    def test_reflects_computed_coverage(self, tmp_path):
        # The expected node set is computed IN-TEST through the same pure
        # function — the test pins agreement, not a hardcoded status table.
        import coverage_map
        from matrix_views import _nodes, _steps, group_steps
        import kernel
        root, area = ipo_copy(tmp_path)
        tdecl = kernel.load_type("process-step")
        titles = {n["slug"]: n["title"] for n in _nodes(area)}
        node_steps = {}
        for title, steps in group_steps(_steps(area, tdecl), _nodes(area)):
            slug = next((s for s, t in titles.items() if t == title), None)
            if slug:
                node_steps[slug] = [s["slug"] for s in steps]
        cov = coverage_map.coverage(root, node_steps)
        bound = {"claimed", "sourced", "conflicted"}   # thin = claimed|sourced
        expected = {slug for slug, status in cov.items() if status in bound}
        body = plan_views.build_information_requests({"area": area})
        for slug in expected:
            assert titles[slug] in body or slug in body
        for slug, status in cov.items():
            if status == "evidenced":
                assert titles[slug] not in body

    def test_read_only(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        before = fingerprint(root)
        plan_views.build_information_requests({"area": area})
        plan_views.build_open_validations({"area": area})
        assert fingerprint(root) == before


class TestFindingsByTheme:
    def test_accepted_only_grouped_by_theme(self, tmp_path):
        import findings
        root, area = ipo_copy(tmp_path)
        a = findings.propose(root, claim="Accepted claim text",
                             grounds=["PP-03", "SRC-001"],
                             theme="control-gaps")
        findings.accept(root, a)
        r = findings.propose(root, claim="Rejected claim text",
                             grounds=["PP-01"], theme="control-gaps")
        findings.reject(root, r, reason="no")
        findings.propose(root, claim="Proposed claim text",
                         grounds=["PP-02"], theme="handoffs")
        body = plan_views.build_findings_by_theme({"area": area})
        assert "Accepted claim text" in body
        assert "control-gaps" in body.lower() or "Control" in body
        assert "Rejected claim text" not in body
        assert "Proposed claim text" not in body
        # grounds reach the reader as citations
        assert "PP-03" in body and "SRC-001" in body

    def test_empty_register_says_so_instead_of_crashing(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        body = plan_views.build_findings_by_theme({"area": area})
        assert isinstance(body, str) and body.strip()


class TestRegistry:
    def test_all_three_registered_in_py_builders(self):
        import aggregate
        for kind in ("information-requests", "open-validations",
                     "findings-by-theme"):
            assert kind in aggregate.PY_BUILDERS


# --------------------------------------------------------------------------- #
# 3. End to end — the two never-rendered definitions render
# --------------------------------------------------------------------------- #

@needs_materialize
class TestEndToEnd:
    def _aggregate(self, area):
        import aggregate
        assert aggregate.run(str(area)) == 0

    def test_information_request_renders(self, tmp_path):
        import render_glue
        root, area = ipo_copy(tmp_path)
        definitions.materialize_views(area, name="information-request")
        self._aggregate(area)
        d = definitions.load_definition("information-request")
        plan = definitions.compile_plan(d, area)
        out = tmp_path / "info-request.docx"
        render_glue.render_plan(plan, area, out, skin=d.skin)
        assert out.is_file() and out.stat().st_size > 0

    def test_findings_report_renders_accepted_only(self, tmp_path):
        import findings
        import render_glue
        root, area = ipo_copy(tmp_path)
        a = findings.propose(root, claim="The one accepted claim",
                             grounds=["PP-03"], theme="control-gaps")
        findings.accept(root, a)
        definitions.materialize_views(area, name="findings-report")
        self._aggregate(area)
        d = definitions.load_definition("findings-report")
        plan = definitions.compile_plan(d, area)
        out = tmp_path / "findings.docx"
        render_glue.render_plan(plan, area, out, skin=d.skin)
        assert out.is_file() and out.stat().st_size > 0
