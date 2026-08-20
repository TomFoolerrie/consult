"""M61 gate — the xlsx round trip: what the client typed is what the drafter
reads. Repros F-13, F-14, F-25. docs/v2/M61-xlsx-round-trip.md is the spec.
"""

import zipfile

import pytest

import xlsx_min
from xlsx_min import MEMBER_CAP, XlsxError, read_xlsx, write_xlsx

_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


class TestPartAWriterNeverCorrupts:
    def test_every_c0_control_round_trips_as_placeholder(self, tmp_path):
        rows = [[f"a{chr(code)}b"] for code in
                (0x00, 0x07, 0x0C, 0x1B, 0x1F)]
        out = tmp_path / "kit.xlsx"
        write_xlsx(out, ["Answer"], rows)
        got = read_xlsx(out)                     # the engine re-opens its own file
        assert len(got) == len(rows)
        for row in got:
            assert row["Answer"] == "a�b", (
                "illegal character must become the visible placeholder")

    def test_legal_whitespace_and_markup_chars_survive(self, tmp_path):
        out = tmp_path / "kit.xlsx"
        write_xlsx(out, ["Answer"], [["a<b & c>d\ttab\nnewline ünïcode"]])
        got = read_xlsx(out)[0]["Answer"]
        assert "a<b & c>d" in got and "ünïcode" in got
        assert "\t" in got and "\n" in got

    def test_output_is_well_formed_xml(self, tmp_path):
        from xml.etree import ElementTree as ET
        out = tmp_path / "kit.xlsx"
        write_xlsx(out, ["H"], [["x\x00y"]])
        with zipfile.ZipFile(out) as z:
            ET.fromstring(z.read("xl/worksheets/sheet1.xml"))  # must not raise


def excel_like_workbook(path, cells_xml, styles_extra="", shared=None):
    """A minimal Excel-saved-shaped workbook: sharedStrings + styles with a
    date format at cellXfs index 1 and a custom d/m/y format at index 2."""
    styles = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="{_NS}">
<numFmts count="1"><numFmt numFmtId="164" formatCode="yyyy\\-mm\\-dd"/></numFmts>
<cellXfs count="3">
<xf numFmtId="0"/><xf numFmtId="14"/><xf numFmtId="164"/>
</cellXfs>{styles_extra}
</styleSheet>"""
    sheet = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="{_NS}"><sheetData>{cells_xml}</sheetData></worksheet>"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml", xlsx_min._CONTENT_TYPES)
        z.writestr("_rels/.rels", xlsx_min._ROOT_RELS)
        z.writestr("xl/workbook.xml",
                   f'<workbook xmlns="{_NS}"><sheets/></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", xlsx_min._WB_RELS)
        z.writestr("xl/styles.xml", styles)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
        if shared:
            z.writestr("xl/sharedStrings.xml", shared)


class TestPartBReaderInterprets:
    def test_the_46022_repro(self, tmp_path):
        """A client answering "When is the cutoff?" with 12/31/2025 must not
        reach the drafter as "46022"."""
        cells = ('<row r="1"><c r="A1" t="inlineStr"><is><t>When</t></is></c>'
                 '</row>'
                 '<row r="2"><c r="A2" s="1"><v>46022</v></c></row>')
        wb = tmp_path / "returned.xlsx"
        excel_like_workbook(wb, cells)
        assert read_xlsx(wb)[0]["When"] == "2025-12-31"

    def test_custom_date_format_counts(self, tmp_path):
        cells = ('<row r="1"><c r="A1" t="inlineStr"><is><t>H</t></is></c>'
                 '</row>'
                 '<row r="2"><c r="A2" s="2"><v>45658</v></c></row>')
        wb = tmp_path / "returned.xlsx"
        excel_like_workbook(wb, cells)
        assert read_xlsx(wb)[0]["H"] == "2025-01-01"

    def test_bool_and_plain_number(self, tmp_path):
        cells = ('<row r="1">'
                 '<c r="A1" t="inlineStr"><is><t>B</t></is></c>'
                 '<c r="B1" t="inlineStr"><is><t>N</t></is></c></row>'
                 '<row r="2"><c r="A2" t="b"><v>1</v></c>'
                 '<c r="B2"><v>5</v></c></row>'
                 '<row r="3"><c r="A3" t="b"><v>0</v></c>'
                 '<c r="B3"><v>5</v></c></row>')
        wb = tmp_path / "returned.xlsx"
        excel_like_workbook(wb, cells)
        rows = read_xlsx(wb)
        assert rows[0]["B"] == "TRUE" and rows[1]["B"] == "FALSE"
        assert rows[0]["N"] == "5", "a plain number stays raw text"

    def test_gaps_ingest_note_carries_interpreted_answer(self, tmp_path):
        import gaps_ingest
        area = tmp_path / "area"
        (area / "_review").mkdir(parents=True)
        shared = (f'<sst xmlns="{_NS}" count="3" uniqueCount="3">'
                  '<si><t>Ref</t></si><si><t>Answer</t></si>'
                  '<si><t>close#GAP-01</t></si></sst>')
        cells = ('<row r="1"><c r="A1" t="s"><v>0</v></c>'
                 '<c r="B1" t="s"><v>1</v></c></row>'
                 '<row r="2"><c r="A2" t="s"><v>2</v></c>'
                 '<c r="B2" s="1"><v>46022</v></c></row>')
        wb = tmp_path / "returned.xlsx"
        excel_like_workbook(wb, cells, shared=shared)
        added, unmatched = gaps_ingest.ingest_workbook(area, wb)
        assert added == 1
        text = (area / "_review" / "close.notes.yaml").read_text(
            encoding="utf-8")
        assert "2025-12-31" in text and "46022" not in text


class TestPartCSizeCaps:
    def test_over_cap_member_refused_by_name(self, tmp_path, monkeypatch):
        monkeypatch.setattr(xlsx_min, "MEMBER_CAP", 64)
        wb = tmp_path / "bomb.xlsx"
        write_xlsx(wb, ["H"], [["x" * 4096]])
        with pytest.raises(XlsxError) as exc:
            read_xlsx(wb)
        assert "bomb.xlsx" in str(exc.value)
        assert "cap" in str(exc.value)

    def test_cap_is_generous_for_real_kits(self):
        assert MEMBER_CAP == 50 * 1024 * 1024
