#!/usr/bin/env python3
"""
gaps_ingest.py — deterministic return-trip for the gap workbooks (M9).

    python3 scripts/gaps_ingest.py <area> [files.xlsx ...]

With no explicit files, sweeps `{area}/_review/returned/` for `*.xlsx`. Each
row with a non-empty **Answer** becomes a procedure-anchored review note (the
same `_review/{slug}.notes.yaml` shape the drafters already consume) — closing
a gap rewrites prose, which is drafter work by design; this script just moves
the answer to the right desk with zero token spend.

Row → procedure mapping uses the workbook's hidden `Ref (do not edit)` column
(`slug#LOCAL-ID`, written at kit time) — no display-ID guessing. A row whose
ref was damaged falls back to `_unassigned` so nothing is dropped.

Processed workbooks are archived to `_review/processed/`.
"""

from __future__ import annotations

import argparse
import shutil
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from notes_util import append_items  # noqa: E402
from xlsx_min import read_xlsx  # noqa: E402

UNASSIGNED = "_unassigned"


def _col(row: dict, *names: str) -> str:
    for k, v in row.items():
        for n in names:
            if k.strip().lower().startswith(n):
                return (v or "").strip()
    return ""


def ingest_workbook(area: Path, path: Path) -> tuple[int, int]:
    """Returns (answers_ingested, rows_unmatched)."""
    rows = read_xlsx(path)
    per_slug: dict[str, list[dict]] = {}
    unmatched = 0
    for row in rows:
        answer = _col(row, "answer")
        if not answer:
            continue
        status = _col(row, "status")
        ref = _col(row, "ref")
        gap_id = _col(row, "gap id")
        question = _col(row, "question")
        if "#" in ref:
            slug, local = ref.split("#", 1)
        else:
            slug, local = UNASSIGNED, gap_id
            unmatched += 1
        note = f"{local or gap_id} answered: {answer}"
        if status:
            note += f" [status: {status}]"
        per_slug.setdefault(slug.strip() or UNASSIGNED, []).append({
            "kind": "review",            # M6 notes-bus stamp (see notes_util)
            "type": "comment",
            "location": f"gap workbook row ({gap_id or local})",
            "anchor": question,
            "note": note,
            "source": path.name,
        })
    total = 0
    for slug, items in sorted(per_slug.items()):
        added = append_items(area, slug, items)
        total += added
        print(f"  {slug}: +{added} answer note(s)")
    return total, unmatched


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Ingest filled gap workbooks (M9)")
    ap.add_argument("area", help="area folder")
    ap.add_argument("files", nargs="*", help="workbook(s); default: _review/returned/*.xlsx")
    ap.add_argument("--no-archive", action="store_true")
    a = ap.parse_args(argv)

    area = Path(a.area).resolve()
    files = [Path(f) for f in a.files] or sorted(
        (area / "_review" / "returned").glob("*.xlsx"))
    if not files:
        print("no workbooks to ingest")
        return 0

    processed = area / "_review" / "processed"
    total = unmatched = 0
    for f in files:
        print(f"workbook: {f.name}")
        n, u = ingest_workbook(area, f)
        total += n
        unmatched += u
        if not a.no_archive:
            processed.mkdir(parents=True, exist_ok=True)
            dest = processed / f.name
            if dest.exists():
                dest.unlink()
            shutil.move(str(f), str(dest))
    print(f"ingested {total} answer(s)"
          + (f"; {unmatched} row(s) had a damaged ref -> _unassigned" if unmatched else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
