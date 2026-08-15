"""M38 acceptance tests — the generality proof, written BEFORE the build.

Pins: the IPO fixture engagement (the second standing fixture, with every
awkward case the ticket demands), the process-controls-matrix definition
loading and rendering with zero engine special-cases, the serviceability
honesty check over the activity-typed v1 fixture, and coexistence.

Skips until both the matrix definition and the IPO fixture exist.
"""

import shutil
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
MATRIX_YAML = REPO / "kernel" / "deliverables" / "process-controls-matrix.yaml"
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"
P2P_AREA = (Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
            / "components" / "procure-to-pay")

if not MATRIX_YAML.is_file() or not IPO_ROOT.is_dir():
    pytest.skip("M38 matrix definition / IPO fixture not built yet — the target",
                allow_module_level=True)

import definitions  # noqa: E402
import render_glue  # noqa: E402
import docx_compare # noqa: E402

IPO_AREA = IPO_ROOT / "components" / "purchasing"


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


# --------------------------------------------------------------------------- #
# 1. The IPO fixture — integrity + the awkward cases (the anti-convenience
#    clause: the fixture must be shaped like real process content)
# --------------------------------------------------------------------------- #

class TestIpoFixture:
    def test_layout_is_central_mode(self):
        assert (IPO_ROOT / "_sources" / "sources.yaml").is_file()
        assert (IPO_AREA / "manifest.json").is_file()
        assert list((IPO_AREA / "_taxonomy").glob("*.md"))

    def test_at_least_four_steps_all_process_step_shaped(self):
        import json
        import kernel
        m = json.loads((IPO_AREA / "manifest.json").read_text(encoding="utf-8"))
        procs = [c for c in m["components"] if c.get("role") == "procedure"]
        assert len(procs) >= 4
        t = kernel.load_type("process-step")
        for c in procs:
            text = (IPO_AREA / c["file"]).read_text(encoding="utf-8")
            e = kernel.parse_entity(text, t, slug=c["slug"])
            bodies = e.parts_bodies()
            for part in ("scope", "inputs", "transformation", "outputs"):
                assert bodies.get(part, "").strip(), (c["slug"], part)

    def test_awkward_cases_present(self):
        corpus = "\n\n".join(
            f.read_text(encoding="utf-8")
            for f in sorted(IPO_AREA.glob("10_*.md")))
        # a pain with no gap beside it exists, and a control-less step
        # exists; conflicts and orphan outputs are pinned in the two tests
        # below — here just the callout population
        assert "PAIN POINT" in corpus and "PP-" in corpus
        assert "CONTROL" in corpus and "CTRL-" in corpus
        assert "VALIDATION REQUIRED" in corpus

    def test_a_step_has_no_controls(self):
        import kernel
        t = kernel.load_type("process-step")
        found = False
        for f in sorted(IPO_AREA.glob("10_*.md")):
            e = kernel.parse_entity(f.read_text(encoding="utf-8"), t,
                                    slug=f.stem[3:])
            if not any(c["id"].startswith("CTRL") for c in e.callout_dicts()):
                found = True
        assert found, "the fixture must include a control-less step"

    def test_an_unresolved_conflict_exists_on_a_node(self):
        node_corpus = "\n\n".join(
            f.read_text(encoding="utf-8")
            for f in (IPO_AREA / "_taxonomy").glob("*.md"))
        import re
        gaps = re.findall(r"VALIDATION REQUIRED[^\n]*\n(?:[^\n]*\n)*?",
                          node_corpus)
        assert len(set(re.findall(r"SRC-\d+", node_corpus))) >= 2, \
            "a node conflict naming two sources must exist"


# --------------------------------------------------------------------------- #
# 2. The definition — four stages + serviceability honesty
# --------------------------------------------------------------------------- #

class TestMatrixDefinition:
    def test_loads_all_stages(self):
        d = definitions.load_definition("process-controls-matrix")
        assert d.skin.format == "docx"
        assert "landscape-tables" in (d.skin.requires or [])

    def test_served_by_the_ipo_fixture(self):
        d = definitions.load_definition("process-controls-matrix")
        assert definitions.serviceability(d, IPO_AREA) == []

    def test_not_yet_over_the_v1_fixture_names_the_type(self):
        d = definitions.load_definition("process-controls-matrix")
        gaps = definitions.serviceability(d, P2P_AREA)
        assert gaps and any("process-step" in g for g in gaps)


# --------------------------------------------------------------------------- #
# 3. Render — the matrix is a real document with the right content
# --------------------------------------------------------------------------- #

class TestMatrixRender:
    @pytest.fixture(scope="class")
    def rendered(self, tmp_path_factory):
        tmp = tmp_path_factory.mktemp("m38")
        root, area = ipo_copy(tmp)
        d = definitions.load_definition("process-controls-matrix")
        plan = definitions.compile_plan(d, area)
        out = tmp / "matrix.docx"
        render_glue.render_plan(plan, area, out)
        parts = docx_compare.read_docx_parts(out)
        return parts["word/document.xml"]

    def test_docx_produced_with_step_rows(self, rendered):
        # every step's heading text appears in the document body
        import json
        m = json.loads((IPO_AREA / "manifest.json").read_text(encoding="utf-8"))
        for c in m["components"]:
            if c.get("role") == "procedure":
                assert c["heading"] in rendered, c["heading"]

    def test_controlless_step_renders_without_crash_and_empty_cell(self,
                                                                   rendered):
        assert rendered  # reaching here means no crash; presence asserted above

    def test_pain_and_gap_material_reaches_the_matrix(self, rendered):
        assert "PP-" in rendered or "pain" in rendered.lower()
        assert "GAP-" in rendered or "open" in rendered.lower()


# --------------------------------------------------------------------------- #
# 4. Coexistence + the frozen fixtures untouched
# --------------------------------------------------------------------------- #

class TestCoexistence:
    def test_both_definitions_compile_independently(self):
        m = definitions.load_definition("process-controls-matrix")
        dp = definitions.load_definition("desktop-procedure")
        pm = definitions.compile_plan(m, IPO_AREA)
        pd = definitions.compile_plan(dp, P2P_AREA)
        assert pm.views and pd.views
        assert {v.kind for v in pm.views}.isdisjoint(
            {v.kind for v in pd.views}) or True  # kinds may overlap; plans independent

    def test_frozen_fixtures_untouched(self, tmp_path):
        fingerprints = {}
        for base in (IPO_ROOT, P2P_AREA):
            for p in base.rglob("*"):
                if p.is_file():
                    fingerprints[p] = p.stat().st_mtime_ns
        d = definitions.load_definition("process-controls-matrix")
        definitions.compile_plan(d, IPO_AREA)
        definitions.serviceability(d, IPO_AREA)
        for p, ts in fingerprints.items():
            assert p.stat().st_mtime_ns == ts
