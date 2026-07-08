#!/usr/bin/env python3
"""
split_doc.py — break an assembled process document into bite-sized, editable
component .md files, one per major section.

Split policy is structural, not keyed on exact heading text, so it survives
heading renames and the template's mixed H1/H2 hierarchy:

  - Front matter — the title and everything before the first content section —
    becomes a single fragment (orientation boilerplate, rarely edited).
  - Each top-level content section becomes its own fragment. "Top-level" is the
    shallowest heading level used after the title (H1 in the standard template:
    Current-State Process Documentation, Roles & Responsibilities, Systems &
    Data Inputs, Key Dependencies, each Appendix, ...).
  - Procedure modules (numbered headings like "1.1" or "2.3") and Appendix
    headings always get their own fragment, even when nested one level under a
    section heading. The section heading plus any intro before the first module
    becomes a small wrapper fragment, so procedures and appendices can be added,
    edited, or removed independently.

Headings inside fenced code blocks (``` ... ```) are ignored, so example markdown
in the document does not create false section breaks.

A manifest.json records component order so assemble_doc.py can stitch everything
back together with all content preserved, and reconcile.py can walk it without assembling first.

Usage:
    python3 split_doc.py ASSEMBLED.md OUT_DIR

Then edit files in OUT_DIR and either:
    python3 reconcile.py OUT_DIR             # QC the split project directly
    python3 assemble_doc.py OUT_DIR REBUILT.md
"""

import json
import os
import re
import sys

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
FENCE_RE = re.compile(r"^\s*```")
# A procedure module heading is numbered: 1.1, 1.2, 2.3.4, ...
MODULE_NUM_RE = re.compile(r"^\d+(?:\.\d+)+\b")
APPENDIX_RE = re.compile(r"^appendix\b", re.IGNORECASE)


def slug(text, maxlen=50):
    s = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return (s[:maxlen].rstrip("-")) or "section"


def parse_headings(lines):
    """Return [(line_index, level, text)] for headings outside fenced blocks."""
    out = []
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING_RE.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def is_module(text):
    """True for procedure modules (numbered) and appendix headings."""
    t = text.strip()
    return bool(MODULE_NUM_RE.match(t) or APPENDIX_RE.match(t))


def compute_roots(headings):
    """Line indices that start a new fragment.

    The first heading is treated as the document title and is never a root.
    Roots are headings at the section level (shallowest level used after the
    title) plus any procedure module or appendix heading at any depth.
    """
    if len(headings) < 2:
        return set()
    rest = headings[1:]
    section_level = min(level for _, level, _ in rest)
    roots = set()
    for idx, level, text in rest:
        if level == section_level or is_module(text):
            roots.add(idx)
    return roots


def write_component(out_dir, idx, heading, body_lines):
    name = f"{idx:02d}_{slug(heading or 'front-matter')}.md"
    path = os.path.join(out_dir, name)
    text = "\n".join(body_lines).strip("\n") + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return name


def main(src, out_dir):
    lines = open(src, encoding="utf-8").read().splitlines()
    os.makedirs(out_dir, exist_ok=True)

    headings = parse_headings(lines)
    roots = compute_roots(headings)
    head_by_idx = {idx: (level, text) for idx, level, text in headings}

    # Fragment start lines: 0 (front matter) then each root, in order.
    starts = sorted({0} | roots)

    manifest = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(lines)
        block = lines[start:end]
        if start in roots:
            level, heading = head_by_idx[start]
        else:
            level, heading = 0, None  # front matter
        rel = write_component(out_dir, i, heading, block)
        manifest.append(
            {"file": rel, "heading": heading or "(front matter)", "level": level}
        )

    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({"source": os.path.basename(src), "components": manifest}, f, indent=2)

    print(f"Split {src} -> {out_dir}")
    print(f"  {len(manifest)} component(s) written; manifest.json records order.")
    for c in manifest:
        print(f"    {c['file']}")
    return 0


if __name__ == "__main__":
    # Ignore any stray flags; per-procedure splitting is unconditional.
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], args[1]))
