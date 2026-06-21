#!/usr/bin/env python3
"""build_canned.py — materialize canned classify artifacts for the R2R fixture.

The ingest stage writes immutable, **content-hash-named** Markdown under
`engagements/{E}/ingested/`. Evidence refs (`path#Lstart-Lend`) must resolve into
those produced files, but the hashed filename isn't known until after ingest. So
the canned classify artifacts are kept as **templates** in this directory with
`__CLOSE_MD__` / `__RECON_MD__` placeholders; this helper resolves the real
ingested filenames (by the stable source slug) and writes concrete artifacts into
`engagements/{E}/classify/` so their refs resolve under `engagements/{E}/`.

This keeps the canned artifacts schema-valid AND ref-resolving regardless of the
date prefix or hash in the produced filename.

Usage:
    build_canned.py --engagement E [--classify-dir DIR]

Refs are written **relative to the engagement dir** (e.g.
`ingested/<file>.md#L27`), which is exactly how validate_artifact.py roots them.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent  # fixtures/r2r/canned -> repo root
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"

# (template filename, placeholder, source-slug marker in the ingested filename)
TEMPLATES = [
    ("close_walkthrough.artifact.template.json", "__CLOSE_MD__", "close-walkthrough"),
    ("recon_walkthrough.artifact.template.json", "__RECON_MD__", "recon-walkthrough"),
]


def find_ingested(eid: str, slug: str) -> str:
    """Return the engagement-relative path of the ingested MD whose filename
    carries `slug` (e.g. 'close-walkthrough'). Raises if not found/ambiguous."""
    ingested = ENGAGEMENTS_DIR / eid / "ingested"
    matches = sorted(p for p in ingested.glob("*.md") if slug in p.name)
    if not matches:
        raise SystemExit(f"No ingested MD for slug '{slug}' under {ingested}.")
    if len(matches) > 1:
        raise SystemExit(f"Ambiguous ingested MDs for slug '{slug}': "
                         f"{[m.name for m in matches]}.")
    return f"ingested/{matches[0].name}"


def build(eid: str, classify_dir: Path) -> int:
    classify_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for tmpl_name, placeholder, slug in TEMPLATES:
        tmpl = (HERE / tmpl_name).read_text(encoding="utf-8")
        rel = find_ingested(eid, slug)
        concrete = tmpl.replace(placeholder, rel)
        out_name = tmpl_name.replace(".artifact.template.json", ".artifact.json")
        out_path = classify_dir / out_name
        out_path.write_text(concrete, encoding="utf-8")
        written.append(out_path)
    for p in written:
        print(f"wrote {p}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Materialize canned R2R classify artifacts.")
    ap.add_argument("--engagement", required=True)
    ap.add_argument("--classify-dir",
                    help="Override output dir (default: engagements/{E}/classify).")
    args = ap.parse_args()
    classify_dir = (Path(args.classify_dir) if args.classify_dir
                    else ENGAGEMENTS_DIR / args.engagement / "classify")
    return build(args.engagement, classify_dir)


if __name__ == "__main__":
    sys.exit(main())
