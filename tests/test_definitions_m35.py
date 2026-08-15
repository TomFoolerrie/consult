"""M35 acceptance tests — written BEFORE the definition language exists.

These tests pin the deliverable-definition contract
(docs/v2/M35-deliverable-definitions.md): the three-layer language
(shape / bindings / skin), the four-stage fail-loud loader, and
compile-to-plan. Skips until `scripts/definitions.py` exists; then it is
the gate. Implementers: make these pass without editing them.

The frozen p2p corpus is the serviceability/plan target (read-only).
"""

from pathlib import Path

import pytest

FIXTURE_AREA = (Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
                / "components" / "procure-to-pay")

definitions = pytest.importorskip(
    "definitions", reason="M35 definition language not built yet — the target"
)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def load_bad(tmp_path, name, text):
    f = tmp_path / f"{name}.yaml"
    f.write_text(text, encoding="utf-8")
    with pytest.raises(definitions.DefinitionError) as exc:
        definitions.load_definition_file(f)
    msg = str(exc.value)
    assert name in msg or f.name in msg, "error must name the file"
    return msg


MINIMAL = """\
deliverable: {name}
shape:
  - id: body
    title: Body
    kind: entity-part
    binding: steps
bindings:
  steps: {{entities: activity, parts: [steps]}}
skin:
  format: docx
"""


# --------------------------------------------------------------------------- #
# 1. Loader stage 1 — syntax
# --------------------------------------------------------------------------- #

class TestSyntaxStage:
    def test_minimal_definition_loads(self, tmp_path):
        f = tmp_path / "mini.yaml"
        f.write_text(MINIMAL.format(name="mini"), encoding="utf-8")
        d = definitions.load_definition_file(f)
        assert d.name == "mini"
        assert [b.id for b in d.shape] == ["body"]

    def test_unknown_top_level_key_refused(self, tmp_path):
        msg = load_bad(tmp_path, "extra",
                       MINIMAL.format(name="extra") + "surprise: true\n")
        assert "surprise" in msg

    def test_block_missing_id_refused(self, tmp_path):
        msg = load_bad(tmp_path, "noid", """\
deliverable: noid
shape:
  - title: Anonymous
    kind: static
    text: hello
bindings: {}
skin: {format: docx}
""")
        assert "id" in msg

    def test_block_referencing_undefined_binding_refused(self, tmp_path):
        msg = load_bad(tmp_path, "dangler", """\
deliverable: dangler
shape:
  - {id: body, title: Body, kind: entity-part, binding: nope}
bindings: {}
skin: {format: docx}
""")
        assert "nope" in msg and "body" in msg

    def test_duplicate_block_id_refused(self, tmp_path):
        msg = load_bad(tmp_path, "dupe", """\
deliverable: dupe
shape:
  - {id: body, title: One, kind: static, text: a}
  - {id: body, title: Two, kind: static, text: b}
bindings: {}
skin: {format: docx}
""")
        assert "body" in msg


# --------------------------------------------------------------------------- #
# 2. Loader stage 2 — vocabulary (against type declarations, no engagement)
# --------------------------------------------------------------------------- #

class TestVocabularyStage:
    def test_binding_naming_unknown_type_refused(self, tmp_path):
        msg = load_bad(tmp_path, "badtype", """\
deliverable: badtype
shape:
  - {id: body, title: Body, kind: entity-part, binding: steps}
bindings:
  steps: {entities: no-such-type, parts: [steps]}
skin: {format: docx}
""")
        assert "no-such-type" in msg

    def test_binding_naming_unknown_part_refused(self, tmp_path):
        msg = load_bad(tmp_path, "badpart", """\
deliverable: badpart
shape:
  - {id: body, title: Body, kind: entity-part, binding: steps}
bindings:
  steps: {entities: activity, parts: [not-a-part]}
skin: {format: docx}
""")
        assert "not-a-part" in msg

    def test_vocabulary_checks_need_no_engagement(self, tmp_path):
        # a definition validates against DECLARATIONS alone
        f = tmp_path / "clean.yaml"
        f.write_text(MINIMAL.format(name="clean"), encoding="utf-8")
        d = definitions.load_definition_file(f)
        assert d.name == "clean"


# --------------------------------------------------------------------------- #
# 3. Loader stage 3 — serviceability ("not yet" gate, not an error)
# --------------------------------------------------------------------------- #

class TestServiceabilityStage:
    def test_served_by_the_fixture(self, tmp_path):
        f = tmp_path / "mini.yaml"
        f.write_text(MINIMAL.format(name="mini"), encoding="utf-8")
        d = definitions.load_definition_file(f)
        assert definitions.serviceability(d, FIXTURE_AREA) == []

    def test_not_yet_is_a_report_not_an_exception(self, tmp_path):
        f = tmp_path / "ps.yaml"
        f.write_text("""\
deliverable: ps
shape:
  - {id: rows, title: Rows, kind: entity-part, binding: steps}
bindings:
  steps: {entities: process-step, parts: [transformation]}
skin: {format: docx}
""", encoding="utf-8")
        d = definitions.load_definition_file(f)   # vocabulary-valid
        gaps = definitions.serviceability(d, FIXTURE_AREA)
        assert gaps, "activity-typed fixture cannot serve process-step yet"
        assert any("process-step" in g for g in gaps)


# --------------------------------------------------------------------------- #
# 4. Loader stage 4 — skin capability
# --------------------------------------------------------------------------- #

class TestSkinStage:
    def test_unknown_format_refused(self, tmp_path):
        msg = load_bad(tmp_path, "badskin",
                       MINIMAL.format(name="badskin").replace(
                           "format: docx", "format: hologram"))
        assert "hologram" in msg

    def test_undeclared_capability_refused(self, tmp_path):
        msg = load_bad(tmp_path, "needscap",
                       MINIMAL.format(name="needscap").replace(
                           "format: docx",
                           "format: docx\n  requires: [teleportation]"))
        assert "teleportation" in msg


# --------------------------------------------------------------------------- #
# 5. The shipped desktop-procedure definition compiles to v1's plan
# --------------------------------------------------------------------------- #

class TestDesktopProcedure:
    def test_ships_and_loads(self):
        d = definitions.load_definition("desktop-procedure")
        assert d.name == "desktop-procedure"
        assert d.skin.format == "docx"

    def test_plan_matches_v1_pipeline_structurally(self):
        d = definitions.load_definition("desktop-procedure")
        plan = definitions.compile_plan(d, FIXTURE_AREA)
        # the view set and writer map are pinned by the fixture manifest
        expected = {
            "procedure-index": "python",
            "role-dictionary": "python",
            "systems": "python",
            "dependencies": "agent",
            "raci": "agent",
            "appendix-a": "python",
            "gap-log": "python",
            "screenshot-index": "python",
        }
        assert {v.kind: v.writer for v in plan.views} == expected

    def test_plan_view_order_follows_manifest_order(self):
        d = definitions.load_definition("desktop-procedure")
        plan = definitions.compile_plan(d, FIXTURE_AREA)
        kinds = [v.kind for v in plan.views]
        assert kinds.index("procedure-index") < kinds.index("dependencies")
        assert kinds.index("dependencies") < kinds.index("raci")
        assert kinds.index("raci") < kinds.index("appendix-a")


# --------------------------------------------------------------------------- #
# 6. Two definitions coexist; compilation is read-only
# --------------------------------------------------------------------------- #

class TestIndependence:
    def test_compile_never_writes(self, tmp_path):
        d = definitions.load_definition("desktop-procedure")
        before = {p: p.stat().st_mtime_ns
                  for p in FIXTURE_AREA.rglob("*") if p.is_file()}
        definitions.compile_plan(d, FIXTURE_AREA)
        after = {p: p.stat().st_mtime_ns
                 for p in FIXTURE_AREA.rglob("*") if p.is_file()}
        assert before == after

    def test_user_definition_shadows_shipped(self, tmp_path):
        # a user file with the same name wins (M13 doctrine per file)
        import shutil
        root = tmp_path / "eng"
        area = root / "components" / "p2p"
        area.mkdir(parents=True)
        shutil.copy(FIXTURE_AREA / "manifest.json", area / "manifest.json")
        cdir = root / "components" / "_client" / "deliverables"
        cdir.mkdir(parents=True)
        (cdir / "desktop-procedure.yaml").write_text(
            MINIMAL.format(name="desktop-procedure"), encoding="utf-8")
        d = definitions.load_definition("desktop-procedure", area=area)
        assert [b.id for b in d.shape] == ["body"], "user file must shadow"
