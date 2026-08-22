#!/usr/bin/env python3
"""
screens_ingest.py — deterministic return-trip for screenshot templates (M9).

    python3 scripts/screens_ingest.py <area> [templates.docx ...]

With no explicit files, sweeps `{area}/_review/returned/` for docx whose core
category reads `cw-screens:<doc_id>` (kits stamp it, so renamed files still
identify themselves). For each anchored paste box (bookmark → the sidecar map
under `_review/.maps/`), every image pasted in that box is saved to

    {area}/_assets/screens/{slug}/{LOCAL-ID}.{ext}     (second image: -2, -3…)

which is exactly where `render.py --mode final` looks. Dropping a PNG at that
path BY HAND is an equally valid way to supply a screenshot — this script is
convenience, not the contract.

Empty boxes and images floating outside any box are REPORTED, never guessed.
Processed templates are archived to `_review/processed/`.
"""

from __future__ import annotations

# M67 interpreter floor: this block runs BEFORE any first-party import, because
# a < 3.10 interpreter dies inside `callouts.py` at import time and a check
# placed after those imports could never fire.
import os as _os  # noqa: E402
import sys as _sys  # noqa: E402
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _pyfloor  # noqa: E402  (3.9-importable by contract)

_pyfloor.require()

import argparse
import json
import shutil
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from docx import Document  # noqa: E402
from docx.oxml.ns import qn  # noqa: E402

_A_BLIP = ("{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
_R_EMBED = ("{http://schemas.openxmlformats.org/officeDocument/2006/"
            "relationships}embed")

_EXT_OF = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/gif": ".gif",
    "image/bmp": ".bmp", "image/tiff": ".tiff",
}


def _load_map(area: Path, doc) -> dict | None:
    cat = doc.core_properties.category or ""
    if not cat.startswith("cw-screens:"):
        return None
    doc_id = cat.split(":", 1)[1].strip()
    f = area / "_review" / ".maps" / f"{doc_id}.json"
    if not f.is_file():
        return None
    return json.loads(f.read_text(encoding="utf-8"))


def _blips_in(el) -> list[str]:
    return [b.get(_R_EMBED) for b in el.iter(_A_BLIP) if b.get(_R_EMBED)]


def ingest_template(area: Path, path: Path) -> dict:
    doc = Document(str(path))
    smap = _load_map(area, doc)
    if smap is None:
        return {"skipped": f"{path.name}: not a screenshot template (or its "
                           f"map under _review/.maps/ is missing)"}

    body = doc.element.body
    # bookmark name -> enclosing table cell element
    cell_of: dict[str, object] = {}
    for bm in body.iter(qn("w:bookmarkStart")):
        name = bm.get(qn("w:name")) or ""
        if not name.startswith("scr_"):
            continue
        el = bm
        while el is not None and el.tag != qn("w:tc"):
            el = el.getparent()
        if el is not None:
            cell_of[name] = el

    part = doc.part
    saved, empty = [], []
    used_rids: set[str] = set()
    for name, entry in sorted(smap.get("entries", {}).items()):
        cell = cell_of.get(name)
        rids = _blips_in(cell) if cell is not None else []
        if not rids:
            empty.append(entry["disp"])
            continue
        dest_dir = area / "_assets" / "screens" / entry["slug"]
        dest_dir.mkdir(parents=True, exist_ok=True)
        for k, rid in enumerate(rids):
            used_rids.add(rid)
            image_part = part.related_parts[rid]
            ext = _EXT_OF.get(image_part.content_type, ".png")
            suffix = "" if k == 0 else f"-{k + 1}"
            dest = dest_dir / f"{entry['local']}{suffix}{ext}"
            dest.write_bytes(image_part.blob)
            saved.append(f"{entry['slug']}/{dest.name}")

    stray = len({r for r in _blips_in(body)} - used_rids)
    return {"file": path.name, "saved": saved, "empty": empty, "stray": stray}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ingest filled screenshot templates (M9)")
    ap.add_argument("area", help="area folder")
    ap.add_argument("files", nargs="*",
                    help="template(s); default: _review/returned/*.docx that self-identify")
    ap.add_argument("--no-archive", action="store_true")
    a = ap.parse_args(argv)

    area = Path(a.area).resolve()
    explicit = bool(a.files)
    files = [Path(f) for f in a.files] or sorted(
        (area / "_review" / "returned").glob("*.docx"))
    if not files:
        print("no templates to ingest")
        return 0

    processed = area / "_review" / "processed"
    any_done = False
    for f in files:
        res = ingest_template(area, f)
        if "skipped" in res:
            if explicit:
                print(f"  SKIP {res['skipped']}")
            continue  # returned/ sweep: reviewed docs etc. are other scripts' input
        any_done = True
        print(f"template: {res['file']}")
        for s in res["saved"]:
            print(f"  saved _assets/screens/{s}")
        if res["empty"]:
            print(f"  empty box(es), not returned: {', '.join(res['empty'])}")
        if res["stray"]:
            print(f"  WARN: {res['stray']} image(s) pasted OUTSIDE any box — "
                  f"place them manually under _assets/screens/<slug>/")
        if not a.no_archive:
            processed.mkdir(parents=True, exist_ok=True)
            dest = processed / f.name
            if dest.exists():
                dest.unlink()
            shutil.move(str(f), str(dest))
    if not any_done and not explicit:
        print("no screenshot templates among returned files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
