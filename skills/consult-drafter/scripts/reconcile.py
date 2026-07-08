#!/usr/bin/env python3
"""
reconcile.py — QC gate for lean process documents.

Checks ID integrity across a process document, EITHER as a single assembled
Markdown file OR as a split project directory (component .md files plus a
manifest.json produced by split_doc.py).

In split mode it walks the manifest in order, checks IDs across all fragments
together (so a body tag in one fragment reconciles to a table in another), and
reports every location as <component>:<line> so you can jump straight to the
fragment that needs editing. IDs must be reconciled across the whole document,
so always point this at the assembled file or the split directory — never at a
single fragment.

Errors:
- BARE GAP TAG: a body tag written as [[GAP — ...]] without an ID.
- DANGLING REFERENCE: an ID appears in the document but is not defined in a table row.
- MISSING COMPONENT: a file listed in manifest.json is not present on disk.

Warnings:
- ORPHAN: an ID is defined in a table but is never referenced elsewhere.
- DUPLICATE DEFINITION: an ID appears as the first cell of more than one table row.

Definition: an ID in the first cell of a Markdown table data row, or the first
<td> cell of an HTML table row. Reference: any other occurrence of the ID.

Registry types (SRC) are dangling-checked but exempt from ORPHAN warnings, since
a registered-but-uncited source is normal.

ID types checked by default:
SRC, GAP, SC, PP, IO, CTRL
Multi-segment IDs are supported, e.g. GAP-XL-01 and CTRL-TBD-01.

Usage:
    python3 reconcile.py path/to/process-doc.md          # single assembled file
    python3 reconcile.py path/to/split_dir               # split project (via manifest.json)
    python3 reconcile.py path/to/split_dir/manifest.json # same, pointed at the manifest

Exit code:
0 = no errors, warnings allowed
1 = errors found
2 = bad usage or unreadable input
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ID_TYPES = ["SRC", "GAP", "SC", "PP", "IO", "CTRL"]

# ID types that act as a registry (declared up front, not necessarily cited
# inline). These are still dangling-checked, but are exempt from ORPHAN
# warnings, since having a registered-but-uncited entry is normal.
ORPHAN_EXEMPT_TYPES = {"SRC"}

ID_RE = re.compile(r"\b(" + "|".join(ID_TYPES) + r")-([A-Z0-9]+(?:-[A-Z0-9]+)*)\b")
BARE_GAP_RE = re.compile(r"\[\[GAP(?!-)")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
HTML_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
HTML_CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")


def strip_code_fences(text: str) -> str:
    # Blank out fenced code blocks but preserve line count so that reported
    # line numbers stay accurate for content that follows a fence.
    def _blank(match: "re.Match[str]") -> str:
        return "\n" * match.group(0).count("\n")

    return FENCE_RE.sub(_blank, text)


def normalize_cell(text: str) -> str:
    text = TAG_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def first_cell_ids_markdown(line: str) -> set[str]:
    """Return IDs from the first cell of a Markdown table data row."""
    s = line.strip()
    if not s.startswith("|"):
        return set()
    cells = [c.strip() for c in s.strip("|").split("|")]
    if not cells:
        return set()
    first = cells[0]
    if not first or set(first) <= set("-: "):
        return set()
    return {f"{m.group(1)}-{m.group(2)}" for m in ID_RE.finditer(first)}


def first_cell_ids_html(text: str) -> dict[str, list[int]]:
    """Return definition line numbers for IDs in first cells of HTML table rows."""
    defs: dict[str, list[int]] = defaultdict(list)
    for row_match in HTML_ROW_RE.finditer(text):
        row = row_match.group(1)
        cells = HTML_CELL_RE.findall(row)
        if not cells:
            continue
        first = normalize_cell(cells[0])
        # Skip header-ish cells that do not contain an ID.
        for m in ID_RE.finditer(first):
            line_no = text.count("\n", 0, row_match.start()) + 1
            defs[f"{m.group(1)}-{m.group(2)}"].append(line_no)
    return defs


def collect_definitions(text: str) -> dict[str, list[int]]:
    definitions: dict[str, list[int]] = defaultdict(list)

    for line_no, line in enumerate(text.splitlines(), start=1):
        for id_ in first_cell_ids_markdown(line):
            definitions[id_].append(line_no)

    html_defs = first_cell_ids_html(text)
    for id_, lines in html_defs.items():
        definitions[id_].extend(lines)

    return definitions


def collect_occurrences(text: str) -> dict[str, list[int]]:
    occurrences: dict[str, list[int]] = defaultdict(list)
    for line_no, line in enumerate(text.splitlines(), start=1):
        for m in ID_RE.finditer(line):
            occurrences[f"{m.group(1)}-{m.group(2)}"].append(line_no)
    return occurrences


def _component_order(in_dir: Path) -> list[str]:
    """Component order from manifest.json, else every .md sorted by name."""
    manifest = in_dir / "manifest.json"
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        return [c["file"] for c in data.get("components", [])]
    return sorted(str(p.relative_to(in_dir)) for p in in_dir.rglob("*.md"))


def load_source(path: str):
    """Return (combined_text, sources, mode, label, load_errors).

    sources[i] maps global line i+1 to (component_relpath_or_None, local_line).
    Single-file mode uses component_relpath=None. A blank separator line is
    inserted between fragments to mirror assemble_doc.py; the line count is kept
    exact so reported line numbers stay aligned after fence stripping.
    """
    p = Path(path)
    if p.name == "manifest.json" and p.is_file():
        p = p.parent

    if p.is_dir():
        order = _component_order(p)
        combined: list[str] = []
        sources: list[tuple[str | None, int]] = []
        load_errors: list[str] = []
        present = 0
        for rel in order:
            fpath = p / rel
            if not fpath.exists():
                load_errors.append(
                    f"MISSING COMPONENT {rel}: listed in manifest.json but not found on disk"
                )
                continue
            present += 1
            frag = fpath.read_text(encoding="utf-8").splitlines()
            if combined:
                combined.append("")
                sources.append((rel, 0))
            for local_no, line in enumerate(frag, start=1):
                combined.append(line)
                sources.append((rel, local_no))
        label = f"{present}/{len(order)} component(s) from {p}"
        return "\n".join(combined), sources, "split", label, load_errors

    lines = p.read_text(encoding="utf-8").splitlines()
    sources = [(None, i + 1) for i in range(len(lines))]
    return "\n".join(lines), sources, "file", str(p), []


def locate(sources, mode, n: int) -> str:
    if mode == "split" and 1 <= n <= len(sources):
        rel, local = sources[n - 1]
        if rel is not None and local:
            return f"{rel}:{local}"
    return f"line {n}"


def main(path: str) -> int:
    try:
        raw_text, sources, mode, label, load_errors = load_source(path)
    except (OSError, ValueError) as exc:
        print(f"Could not read {path}: {exc}")
        return 2

    text = strip_code_fences(raw_text)

    errors: list[str] = list(load_errors)
    warnings: list[str] = []

    def loc(n: int) -> str:
        return locate(sources, mode, n)

    def locs(ns) -> str:
        return ", ".join(loc(n) for n in ns)

    for m in BARE_GAP_RE.finditer(text):
        line_no = text.count("\n", 0, m.start()) + 1
        errors.append(f"BARE GAP TAG at {loc(line_no)}: use [[GAP-## — reason]]")

    definitions = collect_definitions(text)
    occurrences = collect_occurrences(text)

    for id_, lines in sorted(occurrences.items()):
        if not definitions.get(id_):
            errors.append(
                f"DANGLING REFERENCE {id_}: referenced at {locs(sorted(set(lines)))} "
                f"but not defined in a table first cell"
            )

    for id_, def_lines in sorted(definitions.items()):
        unique = sorted(set(def_lines))
        if len(unique) > 1:
            warnings.append(f"DUPLICATE DEFINITION {id_}: defined at {locs(unique)}")
        if id_.split("-", 1)[0] in ORPHAN_EXEMPT_TYPES:
            continue
        ref_lines = [ln for ln in occurrences.get(id_, []) if ln not in unique]
        if not ref_lines:
            warnings.append(
                f"ORPHAN {id_}: defined at {locs(unique)} but not referenced elsewhere"
            )

    if mode == "split":
        print(f"Reconciled {label} via manifest order.\n")

    if errors:
        print("ERRORS:")
        for item in errors:
            print(f"- {item}")
    else:
        print("No blocking ID errors found.")

    if warnings:
        print("\nWARNINGS:")
        for item in warnings:
            print(f"- {item}")

    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
