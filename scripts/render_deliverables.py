#!/usr/bin/env python3
"""render_deliverables.py — Stage 6 render: deliverable Markdown -> CFGI Word.

Slice 1 is **one-way**: this converts the built deliverable Markdown under
`engagements/{E}/deliverables/` into sibling `.docx` files using the existing
`cfgi_markdown_to_word.py` engine (the consult-docx-builder skill). It does NOT
reimplement MD->docx, and it does NOT ingest review comments (that is S2, T30+).

Targets (under `engagements/{E}/deliverables/`):
  - synthesis.md           -> synthesis.docx                   (--what synthesis)
  - sop/{l1}.md            -> sop/{l1}.docx                     (--what sop)
  - improvements/{l1}.md   -> improvements/{l1}.docx            (--what improvements)
  - gap_report.md          -> gap_report.docx                  (--what gap_report)

After a per-L1 stream doc renders successfully, the matching `rendered_rev` is
bumped on every L2 node of that L1 via state_machine.py
`set-sop`/`set-improvement --bump-rendered-rev`. The synthesis and gap_report
streams are engagement-level (not per-L1), so they have no rendered_rev marker.

Missing target MDs are skipped with a note (not an error): the command still
exits 0. What was rendered (and skipped) is printed.

Command:
  render --engagement E [--l1 L1] [--what synthesis|sop|improvements|gap_report|all]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Reuse state_machine's taxonomy helpers so we resolve an L1's L2 nodes the same
# way the rest of the pipeline does (single source of truth).
from state_machine import iter_l2, load_taxonomy

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"
CFGI_MD_TO_WORD = (REPO_ROOT / "skills" / "consult-docx-builder" / "scripts"
                   / "cfgi_markdown_to_word.py")
STATE_MACHINE = REPO_ROOT / "scripts" / "state_machine.py"

WHATS = ["synthesis", "sop", "improvements", "gap_report", "all"]
# Map a per-L1 stream to its state_machine set-* command + node block.
STREAM_TO_SETCMD = {"sop": "set-sop", "improvements": "set-improvement"}


def engagement_dir(eid: str) -> Path:
    return ENGAGEMENTS_DIR / eid


def l1_ids(l1_filter: Optional[str]) -> List[str]:
    """Distinct L1 ids from the taxonomy, optionally filtered to one."""
    seen: List[str] = []
    for l1, _l1_name, _l2, _l2_name, _l3 in iter_l2(load_taxonomy()):
        if l1 not in seen:
            seen.append(l1)
    if l1_filter is not None:
        return [l1_filter] if l1_filter in seen else [l1_filter]
    return seen


def l2_ids_for_l1(l1: str) -> List[str]:
    """L2 ids belonging to one L1 (taxonomy order)."""
    return [l2 for d1, _d1n, l2, _l2n, _l3 in iter_l2(load_taxonomy()) if d1 == l1]


def render_one(md_path: Path, docx_path: Path) -> bool:
    """Render a single MD -> docx via cfgi_markdown_to_word.py (subprocess).

    Returns True on a successful render, False if the source MD is missing
    (skipped). Any real conversion failure raises (non-zero subprocess).
    """
    if not md_path.exists():
        print(f"  skip (missing): {md_path.relative_to(REPO_ROOT)}")
        return False
    result = subprocess.run(
        [sys.executable, str(CFGI_MD_TO_WORD), str(md_path), "-o", str(docx_path)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(
            f"cfgi_markdown_to_word.py failed for {md_path} (exit {result.returncode}).")
    print(f"  rendered: {docx_path.relative_to(REPO_ROOT)}")
    return True


def bump_rendered_rev(eid: str, stream: str, l1: str) -> None:
    """Bump rendered_rev on every L2 node of `l1` for the given stream."""
    set_cmd = STREAM_TO_SETCMD[stream]
    for l2 in l2_ids_for_l1(l1):
        node = f"{l1}.{l2}"
        result = subprocess.run(
            [sys.executable, str(STATE_MACHINE), set_cmd,
             "--engagement", eid, "--node", node, "--bump-rendered-rev"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit(
                f"{set_cmd} --bump-rendered-rev failed for {node} (exit {result.returncode}).")


def render_per_l1_stream(eid: str, stream: str, l1_filter: Optional[str],
                         rendered: List[str], skipped: List[str]) -> None:
    """Render sop/ or improvements/ docs (one per L1) and bump rendered_rev."""
    edir = engagement_dir(eid)
    print(f"[{stream}]")
    for l1 in l1_ids(l1_filter):
        md_path = edir / "deliverables" / stream / f"{l1}.md"
        docx_path = edir / "deliverables" / stream / f"{l1}.docx"
        if render_one(md_path, docx_path):
            bump_rendered_rev(eid, stream, l1)
            rendered.append(str(docx_path.relative_to(REPO_ROOT)))
        else:
            skipped.append(str(md_path.relative_to(REPO_ROOT)))


def render_engagement_doc(eid: str, name: str, rendered: List[str],
                          skipped: List[str]) -> None:
    """Render an engagement-level doc (synthesis / gap_report); no rendered_rev."""
    edir = engagement_dir(eid)
    print(f"[{name}]")
    md_path = edir / "deliverables" / f"{name}.md"
    docx_path = edir / "deliverables" / f"{name}.docx"
    if render_one(md_path, docx_path):
        rendered.append(str(docx_path.relative_to(REPO_ROOT)))
    else:
        skipped.append(str(md_path.relative_to(REPO_ROOT)))


def cmd_render(eid: str, l1_filter: Optional[str], what: str) -> None:
    if not engagement_dir(eid).exists():
        raise SystemExit(f"No engagement '{eid}' at {engagement_dir(eid)}.")

    rendered: List[str] = []
    skipped: List[str] = []

    streams = [what] if what != "all" else ["synthesis", "sop", "improvements", "gap_report"]
    for stream in streams:
        if stream in ("sop", "improvements"):
            render_per_l1_stream(eid, stream, l1_filter, rendered, skipped)
        else:  # synthesis | gap_report (engagement-level)
            render_engagement_doc(eid, stream, rendered, skipped)

    print()
    print(f"Rendered {len(rendered)} doc(s); skipped {len(skipped)} missing target(s).")
    for r in rendered:
        print(f"  + {r}")
    for s in skipped:
        print(f"  - (skipped) {s}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Render engagement deliverable Markdown to CFGI Word (.docx), one-way.")
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("render", help="Render deliverable MDs to sibling .docx.")
    r.add_argument("--engagement", required=True)
    r.add_argument("--l1", help="Limit per-L1 streams (sop/improvements) to one L1.")
    r.add_argument("--what", default="all", choices=WHATS,
                   help="Which stream(s) to render (default: all).")

    args = p.parse_args()
    if args.command == "render":
        cmd_render(args.engagement, args.l1, args.what)


if __name__ == "__main__":
    main()
