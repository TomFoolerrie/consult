#!/usr/bin/env python3
"""
split_doc.py — LEGACY IMPORT splitter (DEFERRED, optional).

STATUS: Deferred out of the MVP critical path (tickets/M2). Folders are born
folder-native via M0's scaffold, so this tool is *not* the normal entry point.
It survives only to import a pre-existing single-file `.md` SOP into the folder
model ONCE. After import the folder is authoritative; steady-state work is
edit-in-place + `reconcile.py`. There is no "re-split the folder" operation.

The heading contract makes the rule trivial (M1 flat-H2): a new fragment starts
at EVERY `##` outside a fenced block (both ``` and ~~~). Everything before the
first `##` is the title (`#`) + subtitle (the first italic tagline) and is
recorded in the manifest — never duplicated into a fragment.

Role inference at bootstrap only:
  - `derived` if the section carries an M1 `<!-- derived: KIND; writer: W -->` marker.
  - `static` for the pre-procedure human sections (before the first procedure).
  - otherwise `procedure` (slug = slugified heading, set once).
Legacy import cannot know L2 buckets, so every procedure defaults to a single
catch-all bucket `imported`; real L2 assignment comes from M0's procedures.yaml.

Filename = `{band}_{slug}.md` (static 00-09, procedures 10-69, python-index
70-79, agent-derived 80-89, python-appendices 90-99). Slug collisions get a
deterministic `-2`, `-3`, ... suffix + a warning.

Usage:
    python3 scripts/split_doc.py SOURCE.md OUT_DIR --area <area> [--l1 <l1>]

Python 3, stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)
from pathlib import Path

H1_RE = re.compile(r"^#\s+(.*\S)\s*$")
H2_RE = re.compile(r"^##\s+(.*\S)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
DERIVED_RE = re.compile(r"<!--\s*derived:\s*([a-z0-9-]+)\s*;\s*writer:\s*(\w+)\s*-->",
                        re.IGNORECASE)
ITALIC_RE = re.compile(r"^\*(.+?)\*\s*$|^_(.+?)_\s*$")


def slugify(text: str, maxlen: int = 60) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:maxlen].rstrip("-")) or "section"


def split_sections(lines: list[str]):
    """Yield (heading_or_None, body_lines). First tuple (heading None) is the
    pre-first-## front matter (title + subtitle live there)."""
    in_fence = False
    fence_tok = None
    starts: list[int] = []
    headings: dict[int, str] = {}
    for i, line in enumerate(lines):
        m = FENCE_RE.match(line)
        if m:
            tok = m.group(1)
            if not in_fence:
                in_fence, fence_tok = True, tok
            elif tok == fence_tok:
                in_fence, fence_tok = False, None
            continue
        if in_fence:
            continue
        hm = H2_RE.match(line)
        if hm:
            starts.append(i)
            headings[i] = hm.group(1)

    boundaries = [0] + starts
    for idx, start in enumerate(boundaries):
        end = boundaries[idx + 1] if idx + 1 < len(boundaries) else len(lines)
        heading = headings.get(start) if start in headings else None
        yield heading, lines[start:end]


def parse_front_matter(front: list[str]) -> tuple[str, str, list[str]]:
    """`(title, subtitle, leftover lines)` from the pre-first-`##` block.

    M63 Part A: everything the title/subtitle read does NOT consume — scope
    paragraphs, preambles, disclaimers — is returned instead of vanishing, so
    the import can preserve it and report what it did."""
    title, subtitle = "", ""
    leftover: list[str] = []
    consumed_subtitle = False
    for line in front:
        if not title:
            m = H1_RE.match(line)
            if m:
                title = m.group(1).strip()
                continue
        elif not subtitle and not consumed_subtitle and line.strip():
            im = ITALIC_RE.match(line.strip())
            consumed_subtitle = True
            if im:
                subtitle = (im.group(1) or im.group(2)).strip()
                continue
        if line.strip():
            leftover.append(line)
    return title, subtitle, leftover


def band_for(role: str, i_among_procedures: int) -> int:
    if role == "static":
        return 0
    if role == "derived":
        return 80
    return 10  # procedures share band 10


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Legacy single-file .md -> folder import.")
    ap.add_argument("source")
    ap.add_argument("out_dir")
    ap.add_argument("--area", required=True)
    ap.add_argument("--l1", default="")
    args = ap.parse_args(argv)

    src = Path(args.source)
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    lines = src.read_text(encoding="utf-8").splitlines()

    title, subtitle = "", ""
    components = []
    used_slugs: dict[str, int] = {}
    order = 0
    seen_procedure = False

    front_leftover: list[str] = []
    for heading, body in split_sections(lines):
        if heading is None:
            title, subtitle, front_leftover = parse_front_matter(body)
            continue

        joined = "\n".join(body)
        dm = DERIVED_RE.search(joined)
        if dm:
            role = "derived"
        elif not seen_procedure and _looks_static(heading):
            role = "static"
        else:
            role = "procedure"
            seen_procedure = True

        base_slug = slugify(heading)
        slug = base_slug
        if base_slug in used_slugs:
            used_slugs[base_slug] += 1
            slug = f"{base_slug}-{used_slugs[base_slug]}"
            print(f"WARNING: slug collision on {base_slug!r} -> {slug}", file=sys.stderr)
        else:
            used_slugs[base_slug] = 1

        band = band_for(role, 0)
        order += 10
        fname = f"{band:02d}_{slug}.md"
        # avoid file collision by bumping band-local name
        while (out / fname).exists():
            band += 1
            fname = f"{band:02d}_{slug}.md"
        (out / fname).write_text(joined.strip("\n") + "\n", encoding="utf-8")

        comp = {"file": fname, "role": role, "heading": heading, "order": order}
        if role == "procedure":
            comp["slug"] = slug
            comp["l2"] = "imported"
        elif role == "derived":
            comp["derived_kind"] = dm.group(1)
            comp["writer"] = dm.group(2).lower()
        components.append(comp)

    # M63 Part A: unconsumed front matter is PRESERVED as its own component
    # (a static fragment at the top of the document) and reported — silence
    # stopped being an option.
    if front_leftover:
        fname = "00_front-matter.md"
        while (out / fname).exists():
            fname = "0" + fname
        (out / fname).write_text(
            "## Front Matter\n\n" + "\n".join(front_leftover).strip("\n")
            + "\n", encoding="utf-8")
        components.insert(0, {"file": fname, "role": "static",
                              "heading": "Front Matter", "order": 1})
        print(f"  front matter: {len(front_leftover)} unconsumed line(s) "
              f"preserved to {fname}")

    manifest = {
        "schema": "consult-mvp-manifest/v1",
        "area": args.area,
        "l1": args.l1,
        "l2_order": ["imported"],
        "title": title,
        "subtitle": subtitle,
        "components": components,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                       encoding="utf-8")
    print(f"Imported {src} -> {out}")
    print(f"  title={title!r} subtitle={subtitle!r}")
    print(f"  {len(components)} component(s); manifest.json written.")
    return 0


_STATIC_HINTS = ("profile", "how to use", "control", "source", "overview",
                 "purpose", "introduction")


def _looks_static(heading: str) -> bool:
    h = heading.lower()
    return any(hint in h for hint in _STATIC_HINTS)


if __name__ == "__main__":
    sys.exit(main())
