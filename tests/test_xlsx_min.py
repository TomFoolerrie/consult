"""Tests for scripts/xlsx_min.py — write_xlsx/read_xlsx round trip and reader tolerance."""
import zipfile

from xlsx_min import read_xlsx, write_xlsx, _col_letter, _cell_col

_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


def test_round_trip_basic(tmp_path):
    """write_xlsx then read_xlsx returns the same rows keyed by header."""
    p = tmp_path / "wb.xlsx"
    write_xlsx(p, ["ID", "Question"], [["GAP-01", "Who reviews?"],
                                       ["GAP-02", "When?"]])
    rows = read_xlsx(p)
    assert rows == [{"ID": "GAP-01", "Question": "Who reviews?"},
                    {"ID": "GAP-02", "Question": "When?"}]


def test_round_trip_special_chars(tmp_path):
    """XML-special characters and unicode survive the round trip."""
    p = tmp_path / "wb.xlsx"
    val = 'a < b & "c" > d — é ✓'
    write_xlsx(p, ["Col"], [[val]])
    assert read_xlsx(p)[0]["Col"] == val


def test_round_trip_empty_cells_and_none(tmp_path):
    """Empty strings and None write as empty cells and read back as ''."""
    p = tmp_path / "wb.xlsx"
    write_xlsx(p, ["A", "B", "C"], [["x", "", None], ["", "y", "z"]])
    rows = read_xlsx(p)
    assert rows == [{"A": "x", "B": "", "C": ""},
                    {"A": "", "B": "y", "C": "z"}]


def test_blank_rows_skipped(tmp_path):
    """Rows whose cells are all blank are dropped by the reader."""
    p = tmp_path / "wb.xlsx"
    write_xlsx(p, ["A"], [[""], ["kept"], ["  "]])
    assert read_xlsx(p) == [{"A": "kept"}]


def test_no_data_rows(tmp_path):
    """A header-only workbook reads as an empty list."""
    p = tmp_path / "wb.xlsx"
    write_xlsx(p, ["A", "B"], [])
    assert read_xlsx(p) == []


def test_is_valid_zip_with_expected_parts(tmp_path):
    """The output is a real zip containing the required xlsx parts."""
    p = tmp_path / "wb.xlsx"
    write_xlsx(p, ["A"], [["1"]])
    with zipfile.ZipFile(p) as z:
        names = set(z.namelist())
    assert {"[Content_Types].xml", "xl/workbook.xml",
            "xl/worksheets/sheet1.xml", "xl/styles.xml"} <= names


def test_sheet_name_sanitized(tmp_path):
    """Illegal sheet-name characters are replaced and length capped at 31."""
    p = tmp_path / "wb.xlsx"
    write_xlsx(p, ["A"], [["1"]], sheet_name="Bad:Name/" + "x" * 40)
    with zipfile.ZipFile(p) as z:
        wb = z.read("xl/workbook.xml").decode()
    assert ":" not in wb.split('name="')[1].split('"')[0]
    assert len(wb.split('name="')[1].split('"')[0]) <= 31


def _write_shared_strings_xlsx(path, header, rows):
    """Hand-build a workbook using sharedStrings, as Excel would re-save it."""
    strings = []
    def sref(s):
        if s not in strings:
            strings.append(s)
        return strings.index(s)

    def row_xml(r, vals):
        cells = "".join(
            f'<c r="{_col_letter(c)}{r}" t="s"><v>{sref(v)}</v></c>'
            for c, v in enumerate(vals)
        )
        return f'<row r="{r}">{cells}</row>'

    body = row_xml(1, header) + "".join(
        row_xml(i, r) for i, r in enumerate(rows, start=2))
    sheet = (f'<worksheet xmlns="{_NS}"><sheetData>{body}</sheetData></worksheet>')
    sst = (f'<sst xmlns="{_NS}">' +
           "".join(f"<si><t>{s}</t></si>" for s in strings) + "</sst>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/sharedStrings.xml", sst)
        z.writestr("xl/worksheets/sheet1.xml", sheet)


def test_read_shared_strings(tmp_path):
    """read_xlsx resolves t="s" cells through sharedStrings.xml."""
    p = tmp_path / "excel.xlsx"
    _write_shared_strings_xlsx(p, ["ID", "Answer"], [["GAP-01", "Bob reviews"]])
    assert read_xlsx(p) == [{"ID": "GAP-01", "Answer": "Bob reviews"}]


def test_read_numeric_and_str_cells(tmp_path):
    """Plain numeric cells and t="str" formula results read as their raw text."""
    sheet = (f'<worksheet xmlns="{_NS}"><sheetData>'
             '<row r="1"><c r="A1" t="str"><v>H</v></c></row>'
             '<row r="2"><c r="A2"><v>42</v></c></row>'
             '</sheetData></worksheet>')
    p = tmp_path / "n.xlsx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    assert read_xlsx(p) == [{"H": "42"}]


def test_read_bad_shared_index(tmp_path):
    """An out-of-range sharedStrings index reads as '' instead of raising."""
    sheet = (f'<worksheet xmlns="{_NS}"><sheetData>'
             '<row r="1"><c r="A1" t="s"><v>0</v></c></row>'
             '<row r="2"><c r="A2" t="s"><v>99</v></c>'
             '<c r="B2" t="inlineStr"><is><t>keep</t></is></c></row>'
             '</sheetData></worksheet>')
    sst = f'<sst xmlns="{_NS}"><si><t>H</t></si></sst>'
    p = tmp_path / "bad.xlsx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("xl/sharedStrings.xml", sst)
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    rows = read_xlsx(p)
    assert rows[0]["H"] == ""


def test_read_no_worksheet(tmp_path):
    """A zip with no worksheet part returns []."""
    p = tmp_path / "empty.xlsx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("dummy.xml", "<x/>")
    assert read_xlsx(p) == []


def test_col_letter_and_cell_col_inverse():
    """_col_letter and _cell_col are inverses across the AA boundary."""
    for idx in (0, 1, 25, 26, 27, 51, 52, 701, 702):
        assert _cell_col(_col_letter(idx) + "1") == idx
    assert _col_letter(0) == "A" and _col_letter(26) == "AA"
