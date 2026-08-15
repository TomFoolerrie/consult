"""M36 WP-G1 gate — the docx is ASSEMBLED FROM the plan.

The central claim, and the reason this package exists: v1's document, assembled
from the DEFINITION (`resolve_definition` -> `compile_plan` -> the docx
adapter), is indistinguishable from v1's document assembled from the manifest.
`TestCentralProof` pays that against the committed WP-G0 golden — a red golden
here is a defect in the assembly path, never a stale golden
(tests/fixtures/golden/p2p-v1/README.md); regeneration is forbidden.

The rest proves the shape fidelity render_glue's fidelity statement now claims,
on a toy definition where the difference is visible:

  * static block text is INJECTED when the area carries no fragment for it;
  * blocks render in PLAN order (a definition with two view blocks swapped
    produces a differently-ordered document — proven through docx_compare's
    difference report, not by eyeballing text);
  * an entity-part block's binding `parts:` selection and `Block.body_omit`
    decide which parts reach the body (shaded via a real M14 profile);
  * a view block whose derived fragment the area does not carry renders NOTHING
    under `require_views=False`, and is still refused BY NAME by default.

Suite conventions honored: the frozen fixture is never written (every render
runs over a tmp copy; one test fingerprints it), no network, no wall clock, no
order dependence.
"""

from __future__ import annotations

import re
import shutil
import zipfile

from pathlib import Path

import pytest

import docx_compare

FIXTURE_AREA = (Path(__file__).resolve().parent / "fixtures" / "p2p-complete"
                / "components" / "procure-to-pay")
GOLDEN = Path(__file__).resolve().parent / "fixtures" / "golden" / "p2p-v1"

definitions = pytest.importorskip("definitions")
render_glue = pytest.importorskip("render_glue")

DOC = docx_compare.DOCUMENT_PART


# --------------------------------------------------------------------------- #
# Helpers (the D3 smoke's tmp-copy pattern)
# --------------------------------------------------------------------------- #
def area_copy(root: Path, name: str = "p2p") -> Path:
    area = root / "eng" / "components" / name
    area.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FIXTURE_AREA, area)
    return area


def fingerprint(root: Path) -> dict:
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in root.rglob("*") if p.is_file()}


def render_from_definition(area: Path, out: Path, defn, **kw):
    plan = definitions.compile_plan(defn, area)
    definitions.render_plan(plan, area, out, bindings=defn.bindings, **kw)
    assert out.is_file() and out.stat().st_size > 0
    return out


def _unescape(text: str) -> str:
    """XML text as the reader sees it (`&amp;` is a literal ampersand in a
    heading like "Systems & Data Inputs")."""
    return (text.replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&amp;", "&"))


def doc_texts(docx: Path) -> list[str]:
    xml = zipfile.ZipFile(docx).read(DOC).decode("utf-8")
    return [_unescape(t)
            for t in re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", xml)]


def headings(docx: Path) -> list[str]:
    """The Heading2 paragraph texts, in document order — the block sequence a
    reader sees."""
    xml = zipfile.ZipFile(docx).read(DOC).decode("utf-8")
    out = []
    for para in re.findall(r"<w:p[ >].*?</w:p>", xml, flags=re.S):
        if 'w:val="Heading2"' in para:
            out.append(_unescape("".join(
                re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", para))))
    return out


TOY = """\
deliverable: toy-procedure
shape:
  - id: toy-overview
    title: Toy Overview
    kind: static
    text: This toy static block proves definition prose reaches the document.
  - id: procedure-body
    title: Procedures
    kind: entity-part
    binding: steps
    repeat: {over: activity, order: manifest}
  - id: procedure-index
    title: In-Scope Procedures
    kind: view
    writer: python
    binding: procedures
  - id: gap-log
    title: Appendix B — Gap / Validation Log
    kind: view
    writer: python
    binding: gaps
bindings:
  steps: {entities: activity, parts: [scope, steps], order: manifest}
  procedures: {entities: activity, order: manifest}
  gaps: {entities: activity, callouts: [VALIDATION REQUIRED], order: manifest}
skin:
  format: docx
  requires: [toc, cover-page]
"""


def toy_definition(tmp_path: Path, source: str = TOY, name: str = "toy"):
    f = tmp_path / f"{name}.yaml"
    f.write_text(source, encoding="utf-8")
    return definitions.load_definition_file(f)


# --------------------------------------------------------------------------- #
# 1. THE CENTRAL PROOF
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def assembled_from_plan(tmp_path_factory) -> Path:
    """ONE render of the fixture through resolve_definition -> compile_plan ->
    the plan assembly path, shared by the tests that only read it."""
    root = tmp_path_factory.mktemp("plan-assembly")
    area = area_copy(root)
    defn = definitions.resolve_definition(area)
    assert defn.name == "desktop-procedure"
    return render_from_definition(area, root / "from-plan.docx", defn)


class TestCentralProof:
    """resolve_definition -> compile_plan -> plan assembly == v1's document."""

    def test_definition_assembly_matches_the_committed_golden(
            self, assembled_from_plan):
        diffs = docx_compare.compare(GOLDEN, assembled_from_plan,
                                     label_a="golden-v1",
                                     label_b="from-definition")
        assert diffs == [], (
            "the document assembled FROM the definition is no longer "
            "semantically identical to v1's. This is a DEFECT in the assembly "
            "path, not a stale golden — see "
            "tests/fixtures/golden/p2p-v1/README.md.\n" + "\n".join(diffs))

    def test_the_plan_really_drove_the_assembly(self, assembled_from_plan):
        """Guard against compatibility theater: the proof above must not pass
        by having quietly fallen back to the manifest walk. Every Heading2 the
        document carries is a block of the plan's shape (or a procedure of its
        entity-part block), in the plan's order."""
        area_defn = definitions.load_definition("desktop-procedure")
        block_titles = [b.title for b in area_defn.shape
                        if b.kind in ("static", "view")]
        seen = [h for h in headings(assembled_from_plan) if h in block_titles]
        assert seen == block_titles, (
            f"plan block titles {block_titles} vs rendered {seen}")

    def test_frozen_fixture_is_never_written(self, tmp_path):
        before = fingerprint(FIXTURE_AREA)
        area = area_copy(tmp_path)
        defn = definitions.resolve_definition(area)
        render_from_definition(area, tmp_path / "frozen-check.docx", defn)
        assert fingerprint(FIXTURE_AREA) == before


# --------------------------------------------------------------------------- #
# 2. SHAPE FIDELITY on the toy definition
# --------------------------------------------------------------------------- #
class TestShapeFidelity:
    def test_static_block_text_is_injected(self, tmp_path):
        """The area carries no `toy-overview` fragment, so the DEFINITION's
        prose is what renders — the M35 fidelity statement's flagship gap."""
        area = area_copy(tmp_path)
        out = render_from_definition(area, tmp_path / "toy.docx",
                                    toy_definition(tmp_path))
        body = " ".join(doc_texts(out))
        assert "Toy Overview" in headings(out)
        assert "definition prose reaches the document" in body

    def test_area_fragment_wins_over_definition_text(self, tmp_path):
        """The other half of the injection rule: when the area HAS the
        fragment, authored engagement content is the truth about itself (this
        is what keeps the golden proof above honest)."""
        area = area_copy(tmp_path)
        src = TOY.replace("id: toy-overview", "id: process-overview") \
                 .replace("title: Toy Overview", "title: Process Overview")
        out = render_from_definition(area, tmp_path / "frag.docx",
                                    toy_definition(tmp_path, src, "frag"))
        body = " ".join(doc_texts(out))
        assert "definition prose reaches the document" not in body
        assert "Process Overview" in headings(out)

    def test_blocks_render_in_plan_order(self, tmp_path):
        """Reorder two view blocks in a copy of the definition -> the document
        order follows the PLAN. Proven both by the rendered heading sequence and
        by docx_compare reporting the two documents as different."""
        area = area_copy(tmp_path)
        straight = toy_definition(tmp_path)
        head, _, rest = TOY.partition("  - id: procedure-index\n")
        index_block, _, rest2 = rest.partition("  - id: gap-log\n")
        gap_block, _, tail = rest2.partition("bindings:\n")
        swapped_src = (head + "  - id: gap-log\n" + gap_block
                       + "  - id: procedure-index\n" + index_block
                       + "bindings:\n" + tail)
        swapped = toy_definition(tmp_path, swapped_src, "swapped")
        assert [b.id for b in swapped.shape] == [
            "toy-overview", "procedure-body", "gap-log", "procedure-index"]

        a = render_from_definition(area, tmp_path / "a.docx", straight)
        b = render_from_definition(area, tmp_path / "b.docx", swapped)

        index_title, gap_title = "In-Scope Procedures", \
            "Appendix B — Gap / Validation Log"
        ha, hb = headings(a), headings(b)
        assert ha.index(index_title) < ha.index(gap_title)
        assert hb.index(gap_title) < hb.index(index_title)
        diffs = docx_compare.compare(a, b, label_a="plan-order",
                                     label_b="swapped-order")
        assert diffs, "reordering the plan must change the document"
        assert any(d.startswith(DOC + ":") for d in diffs), diffs

    def test_part_selection_keeps_unselected_parts_out_of_the_body(
            self, tmp_path):
        """The toy binding selects only `scope` + `steps`; the five other parts
        the `activity` type declares are absent from the rendered body — while
        a definition that selects them all shows them."""
        area = area_copy(tmp_path)
        narrow = render_from_definition(area, tmp_path / "narrow.docx",
                                        toy_definition(tmp_path))
        wide_src = TOY.replace(
            "parts: [scope, steps]",
            "parts: [scope, quick-reference, before-you-start, steps, outputs, "
            "controls, issues]")
        wide = render_from_definition(area, tmp_path / "wide.docx",
                                      toy_definition(tmp_path, wide_src, "wide"))
        # Compared on the SECTION HEADINGS (the lettered `### F. Key Controls`
        # form), not on loose substrings: a procedure's prose legitimately
        # mentions "Key Controls" in a sentence, and part selection is about
        # which SECTIONS reach the body.
        narrow_body, wide_body = doc_texts(narrow), doc_texts(wide)
        for hidden in ("E. Outputs & Evidence", "F. Key Controls",
                       "G. Known Issues & Improvement Opportunities"):
            assert hidden in wide_body, \
                f"{hidden} must be in the all-parts render (the control)"
            assert hidden not in narrow_body, \
                f"{hidden} must not survive a binding that excludes it"
        for kept in ("A. Scope", "D. Procedure"):
            assert kept in narrow_body, f"{kept} is selected and must render"

    def test_body_omit_hides_the_section_but_keeps_it_bound(self, tmp_path):
        """A profile-shaded definition: `issues` stays in the binding (drafted,
        aggregated, register-collected) and leaves the BODY only — its callouts
        still reach the appendix-a register."""
        area = area_copy(tmp_path)
        (area / "_client").mkdir(exist_ok=True)
        (area / "_client" / "profile.yaml").write_text(
            "profile:\n"
            "  sections: [scope, quick-reference, before-you-start, steps,\n"
            "             outputs, controls, issues]\n"
            "  body_omit: [issues]\n"
            "  derived: [procedure-index, role-dictionary, systems,\n"
            "            dependencies, raci, appendix-a, gap-log]\n",
            encoding="utf-8")
        defn = definitions.resolve_definition(area)
        body_block = next(b for b in defn.shape if b.id == "procedure-body")
        assert body_block.body_omit == ["issues"]
        assert "issues" in defn.bindings["procedure-parts"]["parts"]

        out = render_from_definition(area, tmp_path / "omit.docx", defn)
        texts = doc_texts(out)
        assert "G. Known Issues & Improvement Opportunities" not in texts, \
            "body_omit must hide the section from the procedure body"
        # the pruned view is gone from the document, and the register that
        # catches the hidden section's callouts is still there
        assert "Appendix C — Screenshot / Evidence Index" not in headings(out)
        assert any("Risks, Pain Points" in h for h in headings(out))


# --------------------------------------------------------------------------- #
# 3. ABSENT-VIEW SEMANTICS (the appendix-controls question)
# --------------------------------------------------------------------------- #
class TestAbsentView:
    """A view block whose derived fragment the area does not carry.

    Two sanctioned answers, and the adapter serves both explicitly rather than
    guessing: refuse by name (the default — a plan asking for a document the
    area cannot supply is a defect worth a message), or render nothing
    (`require_views=False` — the opt-in-view semantics `appendix-controls`
    would need). What it must never do is silently render v1's document.
    """

    def _controls_definition(self, tmp_path):
        src = TOY.replace("id: gap-log", "id: appendix-controls").replace(
            "title: Appendix B — Gap / Validation Log",
            "title: Appendix D — Key Controls Register").replace(
            "callouts: [VALIDATION REQUIRED]", "callouts: [CONTROL]")
        return toy_definition(tmp_path, src, "controls")

    def test_absent_view_is_refused_by_name_by_default(self, tmp_path):
        area = area_copy(tmp_path)
        defn = self._controls_definition(tmp_path)
        plan = definitions.compile_plan(defn, area)
        with pytest.raises(render_glue.RenderGlueError) as exc:
            definitions.render_plan(plan, area, tmp_path / "nope.docx",
                                    bindings=defn.bindings)
        assert "appendix-controls" in str(exc.value)
        assert not (tmp_path / "nope.docx").exists()

    def test_absent_view_renders_nothing_when_not_required(self, tmp_path):
        area = area_copy(tmp_path)
        defn = self._controls_definition(tmp_path)
        out = render_from_definition(area, tmp_path / "absent.docx", defn,
                                     require_views=False)
        assert "Appendix D — Key Controls Register" not in headings(out)
        # ...and the rest of the plan rendered normally
        assert "In-Scope Procedures" in headings(out)

    def test_absent_view_is_not_a_silent_fallback_to_the_manifest(
            self, tmp_path):
        """The failure this whole knob guards: 'render nothing for the missing
        view' must not become 'render the area's full v1 document'."""
        area = area_copy(tmp_path)
        defn = self._controls_definition(tmp_path)
        out = render_from_definition(area, tmp_path / "absent2.docx", defn,
                                     require_views=False)
        assert "RACI Matrix" not in headings(out), \
            "a block the plan does not carry must not render"
        assert docx_compare.compare(GOLDEN, out) != []
