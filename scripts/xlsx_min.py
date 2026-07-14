"""xlsx_min.py — dependency-free .xlsx writer + reader for the review kits (M9).

A single-sheet workbook is just zipped XML, so the gap workbook is always a
real Excel file even where openpyxl isn't installed. The reader handles files
we wrote (inline strings) AND files Excel re-saved after the client filled
them in (shared strings) — that round trip is the whole point.

Python 3, stdlib only.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"


# --------------------------------------------------------------------------- #
# writer
# --------------------------------------------------------------------------- #

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
</Types>"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""

_WB_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

# style ids: s=0 body (wrap, top-aligned) · s=1 header (bold white on green)
_STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
<fonts count="2">
<font><sz val="11"/><name val="Calibri"/></font>
<font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font>
</fonts>
<fills count="3">
<fill><patternFill patternType="none"/></fill>
<fill><patternFill patternType="gray125"/></fill>
<fill><patternFill patternType="solid"><fgColor rgb="FF1A7A3D"/><bgColor indexed="64"/></patternFill></fill>
</fills>
<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
<cellXfs count="2">
<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf>
<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1" applyAlignment="1"><alignment vertical="center"/></xf>
</cellXfs>
</styleSheet>"""


def _col_letter(idx: int) -> str:
    out = ""
    idx += 1
    while idx:
        idx, rem = divmod(idx - 1, 26)
        out = chr(65 + rem) + out
    return out


def write_xlsx(path, header: list[str], rows: list[list[str]],
               sheet_name: str = "Sheet1", widths: list[float] | None = None) -> None:
    """Write a single-sheet workbook: bold header row + wrapped text cells."""
    path = Path(path)
    name = re.sub(r"[\\/*?\[\]:]", " ", sheet_name)[:31] or "Sheet1"

    cols = ""
    if widths:
        parts = [
            f'<col min="{i + 1}" max="{i + 1}" width="{w:.1f}" customWidth="1"/>'
            for i, w in enumerate(widths)
        ]
        cols = "<cols>" + "".join(parts) + "</cols>"

    def cell(r: int, c: int, value: str, style: int) -> str:
        v = escape(str(value if value is not None else ""))
        return (f'<c r="{_col_letter(c)}{r}" t="inlineStr" s="{style}">'
                f'<is><t xml:space="preserve">{v}</t></is></c>')

    body = [f'<row r="1">{"".join(cell(1, c, h, 1) for c, h in enumerate(header))}</row>']
    for ri, row in enumerate(rows, start=2):
        body.append(
            f'<row r="{ri}">{"".join(cell(ri, c, v, 0) for c, v in enumerate(row))}</row>'
        )

    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<worksheet xmlns="{_NS}">'
        f'{cols}<sheetData>{"".join(body)}</sheetData></worksheet>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<workbook xmlns="{_NS}" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f'<sheets><sheet name="{escape(name)}" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _ROOT_RELS)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", _WB_RELS)
        z.writestr("xl/styles.xml", _STYLES)
        z.writestr("xl/worksheets/sheet1.xml", sheet)


# --------------------------------------------------------------------------- #
# reader (tolerant: our inline strings OR Excel's shared strings)
# --------------------------------------------------------------------------- #

def _cell_col(ref: str) -> int:
    letters = re.match(r"([A-Z]+)", ref or "A").group(1)
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch) - 64)
    return idx - 1


def _text_of(el) -> str:
    return "".join(t.text or "" for t in el.iter(f"{{{_NS}}}t"))


def read_xlsx(path) -> list[dict[str, str]]:
    """Read the FIRST worksheet as a list of {header: value} dicts.

    Handles t="inlineStr" (what we write), t="s" via sharedStrings.xml (what
    Excel writes when the client saves), t="str", and plain numeric cells."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = [_text_of(si) for si in root.findall(f"{{{_NS}}}si")]
        sheet_name = next(
            (n for n in ("xl/worksheets/sheet1.xml",) if n in names), None
        ) or next((n for n in sorted(names)
                   if n.startswith("xl/worksheets/") and n.endswith(".xml")), None)
        if not sheet_name:
            return []
        root = ET.fromstring(z.read(sheet_name))

    grid: list[dict[int, str]] = []
    for row in root.iter(f"{{{_NS}}}row"):
        cells: dict[int, str] = {}
        for c in row.findall(f"{{{_NS}}}c"):
            col = _cell_col(c.get("r", ""))
            t = c.get("t", "")
            if t == "inlineStr":
                is_el = c.find(f"{{{_NS}}}is")
                val = _text_of(is_el) if is_el is not None else ""
            else:
                v = c.find(f"{{{_NS}}}v")
                raw = (v.text or "") if v is not None else ""
                if t == "s":
                    try:
                        val = shared[int(raw)]
                    except (ValueError, IndexError):
                        val = ""
                else:
                    val = raw
            cells[col] = val
        grid.append(cells)

    if not grid:
        return []
    header_cells = grid[0]
    ncols = (max(header_cells) + 1) if header_cells else 0
    header = [header_cells.get(i, f"col{i}").strip() for i in range(ncols)]
    out = []
    for cells in grid[1:]:
        if not any(v.strip() for v in cells.values()):
            continue
        out.append({header[i]: cells.get(i, "") for i in range(ncols)})
    return out
