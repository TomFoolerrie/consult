#!/usr/bin/env python3
"""
doc_model.py — the shared spine of the CONSULT MVP pipeline.

This is the ONE module the rest of the system imports (M0 scaffold, M3 aggregate,
M4 docx builder, M5 synthesis, and reconcile.py). It owns:

  - load_manifest(folder)        -> dict         (read manifest.json)
  - validate_manifest(manifest)  -> [errors]     (v1 schema check)
  - display_numbers(manifest)    -> {slug: "L2.seq"}   (the ONLY numberer)
  - resolve_tokens(text, numbers, mode) -> text   ([[slug]] -> number/title)
  - assemble(folder)             -> AssembledDoc  (structured, not a string)

Contracts are defined in tickets/README.md. Keep this module free of any
number-baking or heading heuristics: numbering lives here and only here, and the
heading contract is "one `#` title (in the manifest), every section is `##`".

Python 3, stdlib only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

SCHEMA_V1 = "consult-mvp-manifest/v1"

VALID_ROLES = {"static", "procedure", "derived"}
VALID_WRITERS = {"python", "agent"}


class ManifestError(Exception):
    """Raised when a manifest is structurally invalid (validate_manifest reports
    a list; this is for load-time / hard failures)."""


# --------------------------------------------------------------------------- #
# Manifest load + validate (v1)
# --------------------------------------------------------------------------- #

def load_manifest(folder) -> dict:
    """Load manifest.json from an area folder (or accept the file path itself)."""
    p = Path(folder)
    if p.is_dir():
        p = p / "manifest.json"
    if not p.is_file():
        raise ManifestError(f"manifest.json not found at {p}")
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest.json is not valid JSON: {exc}") from exc


def validate_manifest(manifest: dict) -> list[str]:
    """Validate a manifest against the v1 schema.

    Returns a list of human-readable error strings (empty == valid). Does not
    raise, so callers (reconcile) can aggregate with their own diagnostics.
    """
    errors: list[str] = []

    if not isinstance(manifest, dict):
        return ["manifest is not a JSON object"]

    if manifest.get("schema") != SCHEMA_V1:
        errors.append(
            f'schema must be "{SCHEMA_V1}" (got {manifest.get("schema")!r})'
        )

    for key in ("area", "l1", "title"):
        if not manifest.get(key):
            errors.append(f'missing required top-level field "{key}"')

    l2_order = manifest.get("l2_order")
    if not isinstance(l2_order, list) or not all(isinstance(x, str) for x in l2_order):
        errors.append('"l2_order" must be a list of L2 bucket slug strings')
        l2_order = []
    if len(set(l2_order)) != len(l2_order):
        errors.append('"l2_order" contains duplicate buckets')

    components = manifest.get("components")
    if not isinstance(components, list):
        errors.append('"components" must be a list')
        return errors

    l2_set = set(l2_order)
    seen_orders: dict[int, list[str]] = {}
    seen_slugs: dict[str, list[str]] = {}
    seen_files: dict[str, int] = {}

    for i, comp in enumerate(components):
        where = f"components[{i}]"
        if not isinstance(comp, dict):
            errors.append(f"{where} is not an object")
            continue

        file = comp.get("file")
        if not file:
            errors.append(f'{where} missing "file"')
        else:
            seen_files[file] = seen_files.get(file, 0) + 1

        if not comp.get("heading"):
            errors.append(f'{where} ({file}) missing "heading"')

        order = comp.get("order")
        if not isinstance(order, int):
            errors.append(f'{where} ({file}) "order" must be an integer')
        else:
            seen_orders.setdefault(order, []).append(file or where)

        role = comp.get("role")
        if role not in VALID_ROLES:
            errors.append(
                f'{where} ({file}) "role" must be one of {sorted(VALID_ROLES)} '
                f"(got {role!r})"
            )

        if role == "procedure":
            slug = comp.get("slug")
            if not slug:
                errors.append(f'{where} ({file}) procedure missing "slug"')
            else:
                seen_slugs.setdefault(slug, []).append(file or where)
            l2 = comp.get("l2")
            if not l2:
                errors.append(f'{where} ({file}) procedure missing "l2"')
            elif l2_set and l2 not in l2_set:
                errors.append(
                    f'{where} ({file}) l2 "{l2}" is not in manifest l2_order'
                )

        elif role == "derived":
            if not comp.get("derived_kind"):
                errors.append(f'{where} ({file}) derived missing "derived_kind"')
            writer = comp.get("writer")
            if writer not in VALID_WRITERS:
                errors.append(
                    f'{where} ({file}) derived "writer" must be one of '
                    f"{sorted(VALID_WRITERS)} (got {writer!r})"
                )

    for order, files in seen_orders.items():
        if len(files) > 1:
            errors.append(f'duplicate "order" {order} on: {", ".join(files)}')
    for slug, files in seen_slugs.items():
        if len(files) > 1:
            errors.append(f'duplicate procedure "slug" {slug!r} on: {", ".join(files)}')
    for file, n in seen_files.items():
        if n > 1:
            errors.append(f'duplicate "file" {file!r} appears {n} times')

    return errors


# --------------------------------------------------------------------------- #
# display_numbers — the ONLY implementation of the display number
# --------------------------------------------------------------------------- #

def display_numbers(manifest: dict) -> dict[str, str]:
    """Return {procedure-slug: "L2.seq"} display numbers.

    display number = {L2-ordinal}.{activity-seq}:
      - L2-ordinal  = 1-based index of the procedure's `l2` bucket in the
                       manifest's `l2_order` list (the ordering authority).
      - activity-seq = 1-based rank of the procedure among procedures sharing
                       that L2, ordered by their manifest `order`.

    Procedures whose `l2` is not present in `l2_order` are skipped (a defect
    that validate_manifest / reconcile reports separately). This function never
    re-derives ordering from the taxonomy.
    """
    l2_order = manifest.get("l2_order") or []
    l2_ordinal = {l2: i + 1 for i, l2 in enumerate(l2_order)}

    # group procedures by l2 bucket
    buckets: dict[str, list[tuple[int, str]]] = {}
    for comp in manifest.get("components", []):
        if comp.get("role") != "procedure":
            continue
        slug = comp.get("slug")
        l2 = comp.get("l2")
        if not slug or l2 not in l2_ordinal:
            continue
        order = comp.get("order")
        order = order if isinstance(order, int) else 0
        buckets.setdefault(l2, []).append((order, slug))

    numbers: dict[str, str] = {}
    for l2, entries in buckets.items():
        entries.sort(key=lambda t: (t[0], t[1]))
        for seq, (_order, slug) in enumerate(entries, start=1):
            numbers[slug] = f"{l2_ordinal[l2]}.{seq}"
    return numbers


# --------------------------------------------------------------------------- #
# resolve_tokens — [[slug]] -> display number (or number + title)
# --------------------------------------------------------------------------- #

_TOKEN_START = "[["
_TOKEN_END = "]]"


def resolve_tokens(text: str, numbers, mode: str = "number") -> str:
    """Replace procedure cross-reference tokens `[[slug]]` in `text`.

    `numbers` maps slug -> either:
      - a display-number string ("1.1"), or
      - a mapping {"number": "1.1", "title": "Bank Reconciliation"}.

    mode:
      - "number"       -> "1.1"
      - "title"        -> "Bank Reconciliation"
      - "number+title" -> "1.1 Bank Reconciliation"

    A `[[GAP-...]]` body tag is NOT a procedure cross-ref and is left untouched.
    An unknown slug raises KeyError (dangling reference is an ERROR upstream).
    """
    if mode not in ("number", "title", "number+title"):
        raise ValueError(f"unknown mode {mode!r}")

    def _fmt(slug: str) -> str:
        if slug not in numbers:
            raise KeyError(f"unknown [[{slug}]] cross-reference")
        val = numbers[slug]
        if isinstance(val, str):
            num, title = val, ""
        else:
            num = val.get("number", "")
            title = val.get("title", "")
        if mode == "number":
            return num
        if mode == "title":
            return title
        return f"{num} {title}".strip()

    out = []
    i = 0
    n = len(text)
    while i < n:
        start = text.find(_TOKEN_START, i)
        if start == -1:
            out.append(text[i:])
            break
        out.append(text[i:start])
        end = text.find(_TOKEN_END, start + 2)
        if end == -1:
            out.append(text[start:])
            break
        inner = text[start + 2:end]
        # Leave gap/callout-style body tags alone: they contain a space+dash or
        # match an ID grammar, not a bare procedure slug.
        if _is_procedure_slug(inner):
            out.append(_fmt(inner.strip()))
        else:
            out.append(text[start:end + 2])
        i = end + 2
    return "".join(out)


def _is_procedure_slug(inner: str) -> bool:
    """A bare `[[slug]]` cross-ref: lowercase slug, no embedded ' — TEXT'."""
    s = inner.strip()
    if not s:
        return False
    # Body gap tags look like "GAP-01 — reason": they carry a delimiter/space.
    if any(d in s for d in ("—", "–")) or " " in s:
        return False
    # Callout ID grammar (UPPER-...) is not a slug.
    if s.upper() == s and any(c.isalpha() for c in s):
        return False
    return all(c.islower() or c.isdigit() or c == "-" for c in s)


# --------------------------------------------------------------------------- #
# assemble — structured AssembledDoc (NOT a string)
# --------------------------------------------------------------------------- #

@dataclass
class Section:
    heading: str
    role: str
    body: str
    slug: Optional[str] = None
    number: Optional[str] = None
    derived_kind: Optional[str] = None
    writer: Optional[str] = None
    file: Optional[str] = None


@dataclass
class AssembledDoc:
    title: str
    subtitle: str
    sections: list[Section] = field(default_factory=list)

    def procedures(self) -> list[Section]:
        return [s for s in self.sections if s.role == "procedure"]


def assemble(folder) -> AssembledDoc:
    """Assemble an area folder into a structured AssembledDoc.

    Sections are ordered by the manifest `order` field (the sole ordering
    authority). Procedure sections carry their derived `number` (via
    display_numbers) and `slug`; derived sections carry `derived_kind`/`writer`.
    Bodies are returned RAW — token resolution and consult-meta stripping happen
    at render time (M4), not here.
    """
    folder = Path(folder)
    manifest = load_manifest(folder)
    numbers = display_numbers(manifest)

    components = sorted(
        manifest.get("components", []),
        key=lambda c: (c.get("order", 0), c.get("file", "")),
    )

    sections: list[Section] = []
    for comp in components:
        file = comp.get("file")
        body = ""
        if file:
            fpath = folder / file
            if fpath.is_file():
                body = fpath.read_text(encoding="utf-8")
        slug = comp.get("slug")
        sections.append(
            Section(
                heading=comp.get("heading", ""),
                role=comp.get("role", ""),
                body=body,
                slug=slug,
                number=numbers.get(slug) if slug else None,
                derived_kind=comp.get("derived_kind"),
                writer=comp.get("writer"),
                file=file,
            )
        )

    return AssembledDoc(
        title=manifest.get("title", ""),
        subtitle=manifest.get("subtitle", "") or "",
        sections=sections,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("usage: python3 scripts/doc_model.py <area-folder>", file=sys.stderr)
        sys.exit(2)
    doc = assemble(sys.argv[1])
    print(f"# {doc.title}")
    if doc.subtitle:
        print(f"_{doc.subtitle}_")
    print()
    for s in doc.sections:
        num = f"{s.number} " if s.number else ""
        tag = f" [{s.role}"
        tag += f"/{s.derived_kind}" if s.derived_kind else ""
        tag += "]"
        print(f"## {num}{s.heading}{tag}")
