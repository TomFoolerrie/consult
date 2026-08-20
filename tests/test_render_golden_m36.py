"""M36 WP-G0 — the golden render harness (compatibility-gate proof obligation 2).

Amendment A1 ruled the render proof to be NORMALIZED-XML semantic identity: the
p2p fixture, rendered through the definition path, must produce `document.xml`
(plus styles/numbering) that diffs empty against a v1-built reference committed
as a golden artifact — with volatile metadata stripped (timestamps, revision
ids, zip ordering) and text, element structure, ordering, numbering and style
references all retained.

This module is the instrument, in two halves:

  1. THE GATE. `test_v1_render_matches_committed_golden` renders the frozen
     fixture through the CURRENT v1 path and compares to the committed golden.
     It passes today — that is the point: it pins v1's self-consistency now and
     becomes the migration's tripwire, so WP-G1/G2's re-expression has an
     objective target. `test_render_is_deterministic` pins the other half of
     that claim: two independent renders normalize identically.

  2. THE INSTRUMENT'S OWN CALIBRATION. A harness that reports "no differences"
     is worthless until it is shown to report differences when they exist. The
     three mutation tests take a real render, corrupt `document.xml` one way
     each — a changed word, two section blocks swapped, a renumbered item — and
     assert the comparison catches it and names the part. Plus a guard that
     normalization has not been loosened into hiding content (real body text is
     still present in the golden).

Suite conventions honored: the frozen fixture is never written (every render
runs over a `tmp_path` copy, and one test fingerprints the fixture to prove
it), no network, no wall-clock dependence, no order dependence.

Speed: `pytest.ini` declares no custom markers and the suite defines no
slow/serial marker convention, so none is invented here (an undeclared mark
would only add warnings). Instead the shared render is a session-scoped
fixture: two renders total for the whole module, a few seconds.
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

import render

DOC = docx_compare.DOCUMENT_PART


# --------------------------------------------------------------------------- #
# Helpers — the D3 smoke's tmp-copy pattern (tests/test_definitions_d3_m35.py)
# --------------------------------------------------------------------------- #
def area_copy(root: Path, name: str = "p2p") -> Path:
    """A writable copy of the frozen fixture inside an engagement-shaped tree."""
    area = root / "eng" / "components" / name
    area.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(FIXTURE_AREA, area)
    return area


def fingerprint(root: Path) -> dict:
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in root.rglob("*") if p.is_file()}


def render_v1(root: Path, name: str) -> Path:
    """Render a fresh tmp copy of the fixture through the v1 path."""
    area = area_copy(root, name)
    out = root / f"{name}.docx"
    render.render_folder(area, out, mode="working", emit_signal=False)
    assert out.is_file() and out.stat().st_size > 0
    return out


@pytest.fixture(scope="session")
def rendered_v1(tmp_path_factory) -> Path:
    """One v1 render of the fixture, shared by every test that only reads it."""
    return render_v1(tmp_path_factory.mktemp("golden-render"), "p2p")


def mutate_document_xml(src: Path, dest: Path, mutate) -> None:
    """Copy a .docx, replacing word/document.xml with `mutate(text)`.

    Every other entry is copied through byte-for-byte, so the ONLY difference
    the comparison can see is the one the test injected.
    """
    with zipfile.ZipFile(src) as zin, \
            zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            if info.filename == DOC:
                new = mutate(data.decode("utf-8"))
                assert new != data.decode("utf-8"), "the mutation did not apply"
                data = new.encode("utf-8")
            zout.writestr(info, data)


def texts(xml: str) -> list[str]:
    return re.findall(r"<w:t(?: [^>]*)?>([^<]*)</w:t>", xml)


_TAG_RE = re.compile(r"<(/?)(w:[A-Za-z0-9]+)([^>]*?)(/?)>")


def body_children(xml: str) -> list[tuple[str, int, int]]:
    """(tag, start, end) string offsets of the DIRECT children of `w:body`.

    String-level so a swap stays byte-exact everywhere it is not swapping —
    round-tripping through a serializer would rewrite namespace prefixes and
    muddy what the mutation test actually proves.
    """
    open_body = xml.index("<w:body>") + len("<w:body>")
    close_body = xml.rindex("</w:body>")
    out: list[tuple[str, int, int]] = []
    depth, start, tag = 0, None, None
    for m in _TAG_RE.finditer(xml, open_body, close_body):
        closing, name, _, selfclose = m.group(1), m.group(2), m.group(3), m.group(4)
        if selfclose:
            if depth == 0:
                out.append((name, m.start(), m.end()))
            continue
        if not closing:
            if depth == 0:
                start, tag = m.start(), name
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                out.append((tag, start, m.end()))
    return out


def names_document_part(diffs: list[str]) -> bool:
    return any(d.startswith(DOC + ":") for d in diffs)


# --------------------------------------------------------------------------- #
# 1. The gate: v1 renders what the committed golden says v1 renders
# --------------------------------------------------------------------------- #
class TestGolden:
    def test_v1_render_matches_committed_golden(self, rendered_v1):
        """Proof obligation 2, pinned at v1: a fresh render of the frozen
        fixture is semantically identical to the committed reference."""
        diffs = docx_compare.compare(GOLDEN, rendered_v1,
                                     label_a="golden", label_b="fresh-v1")
        assert diffs == [], (
            "the v1 render no longer matches the committed golden. This is a "
            "DEFECT in the change, not a stale golden — see "
            "tests/fixtures/golden/p2p-v1/README.md.\n" + "\n".join(diffs))

    def test_golden_covers_all_three_a1_parts(self):
        assert sorted(docx_compare.canonical_parts(GOLDEN)) == [
            DOC, "word/numbering.xml", "word/styles.xml"]

    def test_render_is_deterministic(self, tmp_path):
        """Two independent renders of the fixture normalize identically —
        nothing volatile (ids, ordering, clock) reaches the compared parts."""
        first = render_v1(tmp_path / "one", "p2p")
        second = render_v1(tmp_path / "two", "p2p")
        diffs = docx_compare.compare(first, second,
                                     label_a="run1", label_b="run2")
        assert diffs == [], "v1 render is nondeterministic:\n" + "\n".join(diffs)

    def test_render_never_touches_the_frozen_fixture(self, tmp_path):
        before = fingerprint(FIXTURE_AREA)
        render_v1(tmp_path, "frozen-check")
        assert fingerprint(FIXTURE_AREA) == before


# --------------------------------------------------------------------------- #
# 2. Calibration: normalization strips volatility, never semantics
# --------------------------------------------------------------------------- #
class TestNormalizationKeepsSemantics:
    def test_body_text_survives_normalization(self):
        """A guard against over-normalizing: real body text, headings and the
        numbering/style references are all still in the golden."""
        doc = (GOLDEN / DOC.split("/")[-1]).read_text(encoding="utf-8")
        body = texts(doc)
        assert "Procure To Pay — Desktop Procedures" in body
        assert any(re.match(r"^\d+\.\d+ \S", t) for t in body), \
            "display-numbered procedure headings must survive"
        assert 'w:val="Heading2"' in doc, "style references must survive"
        assert "w:numId" in doc, "numbering references must survive"
        assert len(body) > 1000, f"only {len(body)} text nodes survived"

    def test_revision_save_ids_are_gone(self):
        """The one thing A1 names as strippable, actually stripped."""
        for f in GOLDEN.glob("*.xml"):
            assert "rsid" not in f.read_text(encoding="utf-8"), f.name

    def test_normalization_is_idempotent(self):
        for part, text in docx_compare.canonical_parts(GOLDEN).items():
            assert docx_compare.canonicalize(text) == text, part


class TestHarnessCatchesCorruption:
    """The instrument must catch what it exists to catch."""

    def test_harness_catches_changed_word(self, rendered_v1, tmp_path):
        target = next(t for t in texts(
            zipfile.ZipFile(rendered_v1).read(DOC).decode("utf-8"))
            if t.startswith("TBD — human-owned section"))

        def mutate(xml: str) -> str:
            return xml.replace(f">{target}<",
                               f">{target.replace('human-owned', 'robot-owned')}<",
                               1)

        bad = tmp_path / "changed-word.docx"
        mutate_document_xml(rendered_v1, bad, mutate)
        diffs = docx_compare.compare(GOLDEN, bad,
                                     label_a="golden", label_b="changed-word")
        assert names_document_part(diffs), diffs
        assert any("robot-owned" in d for d in diffs), \
            f"the diff must show the offending text: {diffs}"

    def test_harness_catches_reordered_sections(self, rendered_v1, tmp_path):
        """Swap two whole Heading-2 section blocks in the body."""
        xml = zipfile.ZipFile(rendered_v1).read(DOC).decode("utf-8")
        kids = body_children(xml)
        # A Heading2 paragraph opens a section; take three consecutive ones so
        # the two blocks between them are adjacent and complete.
        heads = [i for i, (tag, s, e) in enumerate(kids)
                 if tag == "w:p" and 'w:val="Heading2"' in xml[s:e]]
        assert len(heads) >= 3, "fixture must have several sections to swap"
        h0, h1, h2 = heads[0], heads[1], heads[2]
        first = xml[kids[h0][1]:kids[h1 - 1][2]]
        second = xml[kids[h1][1]:kids[h2 - 1][2]]
        between = xml[kids[h1 - 1][2]:kids[h1][1]]
        assert first and second

        def mutate(doc: str) -> str:
            old = first + between + second
            assert old in doc, "could not locate the two adjacent blocks"
            return doc.replace(old, second + between + first, 1)

        bad = tmp_path / "reordered.docx"
        mutate_document_xml(rendered_v1, bad, mutate)
        diffs = docx_compare.compare(GOLDEN, bad,
                                     label_a="golden", label_b="reordered")
        assert names_document_part(diffs), diffs
        assert any(re.search(r"w:body\[1\]/w:p\[\d+\]", d) for d in diffs), \
            f"the diff must name the divergent element path: {diffs}"

    def test_harness_catches_renumbered_item(self, rendered_v1, tmp_path):
        """Change a rendered display number ('1.2 …' -> '1.3 …')."""
        xml = zipfile.ZipFile(rendered_v1).read(DOC).decode("utf-8")
        target = next(t for t in texts(xml) if t.startswith("1.2 "))

        def mutate(doc: str) -> str:
            return doc.replace(f">{target}<",
                               ">" + target.replace("1.2 ", "1.3 ", 1) + "<", 1)

        bad = tmp_path / "renumbered.docx"
        mutate_document_xml(rendered_v1, bad, mutate)
        diffs = docx_compare.compare(GOLDEN, bad,
                                     label_a="golden", label_b="renumbered")
        assert names_document_part(diffs), diffs
        assert any("1.3 " in d for d in diffs), \
            f"the diff must show the wrong number: {diffs}"

    def test_harness_catches_a_dropped_element(self, rendered_v1, tmp_path):
        """Deletion, not just substitution: the element-count report fires."""
        xml = zipfile.ZipFile(rendered_v1).read(DOC).decode("utf-8")
        para = re.search(r"<w:p[ >].*?</w:p>", xml, flags=re.S).group(0)
        bad = tmp_path / "dropped.docx"
        mutate_document_xml(rendered_v1, bad, lambda d: d.replace(para, "", 1))
        diffs = docx_compare.compare(GOLDEN, bad,
                                     label_a="golden", label_b="dropped")
        assert names_document_part(diffs), diffs
        assert any("element count differs" in d for d in diffs), diffs

    def test_clean_copy_of_the_same_render_reports_nothing(self, rendered_v1,
                                                           tmp_path):
        """The control for the four mutations above: the same rezip pipeline
        with a no-op edit must still diff empty, so the mutations — not the
        repackaging — are what the harness reported."""
        same = tmp_path / "repacked.docx"
        mutate_document_xml(rendered_v1, same,
                            lambda d: d.replace("<w:body>", "<w:body >", 1))
        assert docx_compare.compare(GOLDEN, same) == []
