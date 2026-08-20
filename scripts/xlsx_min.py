"""xlsx_min.py — dependency-free .xlsx writer + reader for the review kits (M9).

A single-sheet workbook is just zipped XML, so the gap workbook is always a
real Excel file even where openpyxl isn't installed. The reader handles files
we wrote (inline strings) AND files Excel re-saved after the client filled
them in (shared strings) — that round trip is the whole point.

Python 3, stdlib only.

M61 policies:

* **Writer sanitize policy — replace-and-note.** XML-1.0-illegal characters
  (C0 controls other than tab/newline/CR, and the lone surrogates /
  U+FFFE/U+FFFF) are replaced with U+FFFD before emission — the kit always
  ships and always re-opens (in Excel and in `read_xlsx`), and the drafter
  sees a visible marker where a form-feed pasted from a client PDF used to
  corrupt the workbook. The characters are never meaningful, so refusal was
  rejected in favor of the marker.
* **Reader typing.** Cells styled with a date/time number format come back as
  ISO text (`2025-12-31`, `13:30:00`, or both) — serial→date is pure epoch
  arithmetic; `t="b"` comes back `TRUE`/`FALSE`. Everything else stays raw
  text as before.
* **Size caps.** Every zip member read from a client-returned file is capped
  at `MEMBER_CAP` decompressed bytes; over the cap refuses loudly naming the
  file (decompression-bomb guard).
"""

from __future__ import annotations

import datetime as _dt
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"

#: Per-member decompressed-size cap for client-returned files (M61 Part C).
MEMBER_CAP = 50 * 1024 * 1024


class XlsxError(Exception):
    """A fail-loud defect reading or writing a workbook."""


# XML 1.0 cannot carry these AT ALL (not even as entities): C0 controls other
# than \t \n \r, DEL is legal but the surrogate range and U+FFFE/U+FFFF are not.
_XML_ILLEGAL = re.compile(
    "[\x00-\x08\x0B\x0C\x0E-\x1F\uD800-\uDFFF￾￿]")


def _sanitize(value: str) -> str:
    """Replace XML-1.0-illegal characters with U+FFFD (the documented
    replace-and-note policy — see the module docstring)."""
    return _XML_ILLEGAL.sub("�", value)


def _read_member(z: zipfile.ZipFile, name: str, label) -> bytes:
    """One zip member, refused loudly when its decompressed size exceeds the
    cap — client-returned files are opened through here (M61 Part C)."""
    info = z.getinfo(name)
    if info.file_size > MEMBER_CAP:
        raise XlsxError(
            f"{label}: zip member {name} decompresses to {info.file_size} "
            f"bytes, over the {MEMBER_CAP}-byte cap — refusing to parse a "
            f"decompression bomb")
    return z.read(name)


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
        v = escape(_sanitize(str(value if value is not None else "")))
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


# --------------------------------------------------------------------------- #
# M61 Part B — the minimum typing the kits need: date/time formats + booleans
# --------------------------------------------------------------------------- #

# Builtin numFmtIds that render date and/or time (ECMA-376 §18.8.30).
_BUILTIN_DATE = {14, 15, 16, 17, 22}
_BUILTIN_TIME = {18, 19, 20, 21, 45, 46, 47}


def _fmt_is_datish(code: str) -> tuple[bool, bool]:
    """(has date, has time) for a CUSTOM format code — `d`/`m`/`y` (date) or
    `h`/`s` (time) OUTSIDE quoted literals and color/condition brackets."""
    bare = re.sub(r'"[^"]*"|\[[^\]]*\]|\\.', "", code or "")
    has_date = bool(re.search(r"[dmy]", bare, re.I))
    has_time = bool(re.search(r"[hs]", bare, re.I))
    return has_date, has_time


def _style_kinds(z: zipfile.ZipFile, names, label) -> list[tuple[bool, bool]]:
    """Per cellXfs index: (renders date, renders time), from styles.xml."""
    if "xl/styles.xml" not in names:
        return []
    root = ET.fromstring(_read_member(z, "xl/styles.xml", label))
    custom: dict[int, tuple[bool, bool]] = {}
    for nf in root.iter(f"{{{_NS}}}numFmt"):
        try:
            custom[int(nf.get("numFmtId", ""))] = _fmt_is_datish(
                nf.get("formatCode", ""))
        except ValueError:
            continue
    kinds: list[tuple[bool, bool]] = []
    xfs = root.find(f"{{{_NS}}}cellXfs")
    for xf in (xfs.findall(f"{{{_NS}}}xf") if xfs is not None else []):
        try:
            fmt = int(xf.get("numFmtId", "0"))
        except ValueError:
            fmt = 0
        if fmt in custom:
            kinds.append(custom[fmt])
        else:
            kinds.append((fmt in _BUILTIN_DATE, fmt in _BUILTIN_TIME))
    return kinds


_EXCEL_EPOCH = _dt.datetime(1899, 12, 30)


def _serial_to_iso(raw: str, has_date: bool, has_time: bool) -> str:
    """A 1900-epoch serial as ISO text — pure arithmetic, no dependency.
    Unparseable values come back raw (never a crash on a client's cell)."""
    try:
        serial = float(raw)
    except ValueError:
        return raw
    if serial < 0:
        return raw
    # Excel's phantom 1900-02-29: serials >= 60 are one day ahead of the
    # 1899-12-31 epoch, which the 1899-12-30 epoch absorbs; 0 < serial < 60
    # needs one day back.
    base = serial if serial >= 60 or serial < 1 else serial + 1
    moment = _EXCEL_EPOCH + _dt.timedelta(days=base)
    date_part = moment.date().isoformat()
    seconds = round((base - int(base)) * 86400)
    time_part = (_dt.datetime.min
                 + _dt.timedelta(seconds=seconds)).time().isoformat()
    if has_date and has_time and seconds:
        return f"{date_part} {time_part}"
    if has_time and not has_date:
        return time_part
    return date_part


def read_xlsx(path) -> list[dict[str, str]]:
    """Read the FIRST worksheet as a list of {header: value} dicts.

    Handles t="inlineStr" (what we write), t="s" via sharedStrings.xml (what
    Excel writes when the client saves), t="str", t="b" as TRUE/FALSE, cells
    styled with a date/time number format as ISO text (M61 Part B — Excel
    auto-coerces a typed 12/31/2025 to serial 46022, which the drafter cannot
    recover), and plain numeric cells as their raw text."""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(_read_member(z, "xl/sharedStrings.xml", path))
            shared = [_text_of(si) for si in root.findall(f"{{{_NS}}}si")]
        style_kinds = _style_kinds(z, names, path)
        sheet_name = next(
            (n for n in ("xl/worksheets/sheet1.xml",) if n in names), None
        ) or next((n for n in sorted(names)
                   if n.startswith("xl/worksheets/") and n.endswith(".xml")), None)
        if not sheet_name:
            return []
        root = ET.fromstring(_read_member(z, sheet_name, path))

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
                elif t == "b":
                    val = "TRUE" if raw.strip() == "1" else "FALSE"
                else:
                    val = raw
                    if t in ("", "n"):
                        try:
                            kind = style_kinds[int(c.get("s", ""))]
                        except (ValueError, IndexError):
                            kind = (False, False)
                        if kind[0] or kind[1]:
                            val = _serial_to_iso(raw, *kind)
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
