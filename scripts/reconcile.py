#!/usr/bin/env python3
"""
reconcile.py — QC gate for a CONSULT area folder (folder-native, per-fragment).

This is the r3 rewrite of the old global-ID reconciler. IDs are now
PROCEDURE-LOCAL: `CTRL-001` in `bank-reconciliation` and `CTRL-001` in
`asset-disposal` are distinct, keyed on the tuple `(slug, local-id)`. Each
procedure fragment is parsed independently; a reference only reconciles within
its own fragment. There is no global ID namespace.

Checks (see docs/README.md + docs/M2-splitter-manifest.md):

  ERROR (nonzero exit):
    - manifest.json invalid against v1 schema (incl. duplicate order/slug)
    - bare gap tag `[[GAP — ...]]` (no numeric id)
    - malformed callout ID grammar
    - callout ID prefix not matching its label (e.g. PAIN POINT with CTRL-)
    - duplicate/conflicting callout ID within one procedure
    - referenced ID not defined within the SAME procedure (dangling, per-fragment)
    - dangling `[[slug]]` cross-reference (no such procedure)
    - a manifest `derived` file missing its `<!-- derived: ... -->` marker
    - a derived-table row whose (Source-Procedure slug, id) pair is unknown

  WARNING (exit stays 0):
    - a `consult-meta` systems:/roles: slug absent from `_reference/*.yaml`

Usage:
    python3 scripts/reconcile.py <area-folder>

Exit code: 0 = clean or warnings only; 1 = errors; 2 = bad usage / unreadable.

Python 3, stdlib + pyyaml.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import doc_model
except ImportError:  # allow `python3 scripts/reconcile.py` from repo root
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import doc_model

try:
    import yaml
except ImportError:
    yaml = None


# --------------------------------------------------------------------------- #
# Callout grammar
# --------------------------------------------------------------------------- #

# Callout grammar primitives are shared with aggregate.py via callouts.py so the
# LABEL→prefix map + ID/gap grammar never drift. reconcile keeps its own loose
# CALLOUT_RE (it must still detect a callout with a MALFORMED id to flag it).
from callouts import (  # noqa: E402
    LABEL_PREFIX, PREFIXES, DELIM as _DELIM, ID_STRICT_RE, ID_INLINE_RE,
    BODY_GAP_RE, BARE_GAP_RE, XREF_RE, blank_fences as strip_fences,
)

# A callout label line inside a blockquote (loose id capture so a malformed id
# is still seen here and reported, then validated against ID_STRICT_RE):
#   > **<LABEL> — <ID>:** <text>
CALLOUT_RE = re.compile(
    r"^\s*>\s*\*\*\s*(?P<label>[A-Z][A-Z ]+?)\s*" + _DELIM + r"\s*"
    r"(?P<id>[^:*]+?)\s*:\*\*",
)

DERIVED_MARKER_RE = re.compile(r"<!--\s*derived:", re.IGNORECASE)

# Fenced code blocks (``` or ~~~) are blanked via callouts.blank_fences
# (imported above as strip_fences), preserving line count/numbers.
FENCE_LINE_RE = re.compile(r"^\s*(```|~~~)")


def extract_consult_meta(text: str) -> dict:
    """Return the parsed body of the ```consult-meta``` fence, or {}."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = FENCE_LINE_RE.match(line)
        if m and line.strip().lstrip("`~").strip().lower() == "consult-meta":
            tok = m.group(1)
            body = []
            for j in range(i + 1, len(lines)):
                if lines[j].strip().startswith(tok):
                    break
                body.append(lines[j])
            raw = "\n".join(body)
            if yaml is None:
                return {}
            try:
                return yaml.safe_load(raw) or {}
            except yaml.YAMLError:
                return {}
    return {}


# --------------------------------------------------------------------------- #
# Registry (nouns)
# --------------------------------------------------------------------------- #

def _harvest_slugs(obj, out: set[str]) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "slug" and isinstance(v, str):
                out.add(v)
            _harvest_slugs(v, out)
    elif isinstance(obj, list):
        for item in obj:
            _harvest_slugs(item, out)


def load_registry_slugs(folder: Path) -> tuple[set[str], set[str]]:
    """(systems_slugs, roles_slugs) harvested tolerantly from _reference/*.yaml."""
    systems: set[str] = set()
    roles: set[str] = set()
    ref = folder / "_reference"
    if yaml is None or not ref.is_dir():
        return systems, roles
    for name, bucket in (("systems.yaml", systems), ("roles.yaml", roles)):
        f = ref / name
        if not f.is_file():
            continue
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
        except yaml.YAMLError:
            continue
        # dict keyed by slug, or list of entries carrying `slug`.
        if isinstance(data, dict):
            for k in data:
                if isinstance(k, str):
                    bucket.add(k)
        _harvest_slugs(data, bucket)
    return systems, roles


# --------------------------------------------------------------------------- #
# Per-fragment parse
# --------------------------------------------------------------------------- #

class Frag:
    def __init__(self, slug: str, file: str):
        self.slug = slug
        self.file = file
        self.defined: dict[str, int] = {}       # id -> first def line
        self.dup: list[tuple[str, int]] = []     # (id, line) conflicting redefs
        self.referenced: dict[str, list[int]] = {}  # id -> ref lines
        self.errors: list[str] = []


def parse_procedure(slug: str, file: str, text: str) -> Frag:
    frag = Frag(slug, file)
    stripped = strip_fences(text)
    lines = stripped.splitlines()

    for n, line in enumerate(lines, start=1):
        # bare gap tags first
        if BARE_GAP_RE.search(line):
            frag.errors.append(
                f"{file}:{n}: BARE GAP TAG — use `[[GAP-NN — reason]]`"
            )

        # callout definitions
        m = CALLOUT_RE.match(line)
        if m:
            label = re.sub(r"\s+", " ", m.group("label")).strip()
            raw_id = m.group("id").strip()
            if label not in LABEL_PREFIX:
                # unknown label with the callout shape — not our concern here
                pass
            else:
                idm = ID_STRICT_RE.match(raw_id)
                if not idm:
                    frag.errors.append(
                        f"{file}:{n}: MALFORMED ID {raw_id!r} for label {label!r}"
                    )
                else:
                    prefix = idm.group(1)
                    expected = LABEL_PREFIX[label]
                    if prefix != expected:
                        frag.errors.append(
                            f"{file}:{n}: ID PREFIX MISMATCH — label {label!r} "
                            f"expects {expected}-, got {prefix}-"
                        )
                    if raw_id in frag.defined:
                        frag.errors.append(
                            f"{file}:{n}: DUPLICATE ID {raw_id} "
                            f"(first defined at line {frag.defined[raw_id]})"
                        )
                    else:
                        frag.defined[raw_id] = n
            continue  # a def line is not counted as a reference

    # references: inline ID mentions + body gap tags (skip def lines)
    def_lines = set(frag.defined.values())
    for n, line in enumerate(lines, start=1):
        if n in def_lines:
            continue
        for m in ID_INLINE_RE.finditer(line):
            _id = f"{m.group(1)}-{m.group(2)}"
            frag.referenced.setdefault(_id, []).append(n)
        for m in BODY_GAP_RE.finditer(line):
            _id = f"GAP-{m.group(1)}"
            frag.referenced.setdefault(_id, []).append(n)

    # per-fragment dangling: every referenced id defined in THIS procedure
    for _id, ref_lines in frag.referenced.items():
        if _id not in frag.defined:
            frag.errors.append(
                f"{file}:{ref_lines[0]}: DANGLING ID {_id} referenced but not "
                f"defined within procedure {slug!r}"
            )
    return frag


# --------------------------------------------------------------------------- #
# Derived-table (slug, id) check
# --------------------------------------------------------------------------- #

def check_derived_tables(folder: Path, manifest: dict, frags: dict[str, Frag],
                         errors: list[str]) -> None:
    """Each derived-table row that names a Source Procedure [[slug]] and an ID
    must reference a (slug, id) pair that exists in that procedure. Runs after
    aggregate; silently no-ops when derived files are absent."""
    # {slug: {display-id, ...}} — the render-time global numbering authority.
    display_ids_of: dict[str, set[str]] = {}
    for (slug, _local), disp in doc_model.callout_display_ids(folder).items():
        display_ids_of.setdefault(slug, set()).add(disp)
    for comp in manifest.get("components", []):
        if comp.get("role") != "derived":
            continue
        fpath = folder / comp.get("file", "")
        if not fpath.is_file():
            continue
        text = strip_fences(fpath.read_text(encoding="utf-8"))
        group_slug = None  # set by `#### [[slug]]` per-procedure group headings
        for n, line in enumerate(text.splitlines(), start=1):
            if line.lstrip().startswith("#"):
                hx = XREF_RE.findall(line)
                group_slug = hx[0] if hx else None
                continue
            if not line.lstrip().startswith("|"):
                continue
            # The row's own ID lives in the FIRST cell. Its procedure comes
            # from an enclosing `#### [[slug]]` group heading if one is set,
            # else from the row's LAST [[token]] (the Procedure column). Free-
            # text cells may quote sibling [[slugs]]/IDs, so nothing else on
            # the line is trusted for the pairing.
            first_cell = line.strip().strip("|").split("|", 1)[0]
            ids = {f"{a}-{b}" for a, b in ID_INLINE_RE.findall(first_cell)}
            if not ids:
                continue
            if group_slug is not None:
                row_slug = group_slug
            else:
                # Combined "ID ([[#slug]])" first cell is authoritative; the
                # last token on the line is only the legacy Source-Procedure-
                # column fallback (free-text cells may quote siblings).
                first_xrefs = XREF_RE.findall(first_cell)
                xrefs = XREF_RE.findall(line)
                row_slug = (first_xrefs[0] if first_xrefs
                            else (xrefs[-1] if xrefs else None))
            if row_slug is None:
                continue
            frag = frags.get(row_slug)
            for _id in ids:
                # Aggregate writes DISPLAY ids (doc_model.callout_display_ids);
                # a row is sound if its id is either the display id of one of
                # this procedure's callouts or (legacy) a local id it defines.
                ok = frag is not None and (
                    _id in frag.defined
                    or _id in display_ids_of.get(row_slug, ())
                )
                if not ok:
                    errors.append(
                        f"{comp.get('file')}:{n}: derived row references "
                        f"({row_slug}, {_id}) which is not defined in that procedure"
                    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

def reconcile(folder: str) -> int:
    folder = Path(folder)
    errors: list[str] = []
    warnings: list[str] = []

    try:
        manifest = doc_model.load_manifest(folder)
    except doc_model.ManifestError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    # 1. manifest v1 schema (incl. duplicate order/slug/file)
    for e in doc_model.validate_manifest(manifest):
        errors.append(f"manifest.json: {e}")

    numbers = doc_model.display_numbers(manifest)
    known_slugs = set(numbers)

    # 2. per-fragment procedure parse
    frags: dict[str, Frag] = {}
    for comp in manifest.get("components", []):
        if comp.get("role") != "procedure":
            continue
        slug = comp.get("slug")
        file = comp.get("file", "")
        fpath = folder / file
        if not fpath.is_file():
            errors.append(f"manifest.json: procedure file {file!r} not found on disk")
            continue
        text = fpath.read_text(encoding="utf-8")
        frag = parse_procedure(slug, file, text)
        errors.extend(frag.errors)
        frags[slug] = frag

    # 3. [[slug]] cross-references resolve (dangling = ERROR) — all files
    for comp in manifest.get("components", []):
        file = comp.get("file", "")
        fpath = folder / file
        if not fpath.is_file():
            continue
        text = strip_fences(fpath.read_text(encoding="utf-8"))
        for n, line in enumerate(text.splitlines(), start=1):
            for m in XREF_RE.finditer(line):
                slug = m.group(1)
                if slug not in known_slugs:
                    errors.append(
                        f"{file}:{n}: DANGLING [[{slug}]] — no such procedure"
                    )

    # 4. derived marker presence
    for comp in manifest.get("components", []):
        if comp.get("role") != "derived":
            continue
        file = comp.get("file", "")
        fpath = folder / file
        if not fpath.is_file():
            errors.append(
                f"manifest.json: derived file {file!r} declared but missing on disk"
            )
            continue
        if not DERIVED_MARKER_RE.search(fpath.read_text(encoding="utf-8")):
            errors.append(
                f"{file}: derived file missing its `<!-- derived: KIND; writer: W -->` marker"
            )

    # 5. consult-meta slug check vs registry (WARNING)
    systems, roles = load_registry_slugs(folder)
    for comp in manifest.get("components", []):
        if comp.get("role") != "procedure":
            continue
        file = comp.get("file", "")
        fpath = folder / file
        if not fpath.is_file():
            continue
        meta = extract_consult_meta(fpath.read_text(encoding="utf-8"))
        for key, registry in (("systems", systems), ("roles", roles)):
            for slug in (meta.get(key) or []):
                if slug not in registry:
                    warnings.append(
                        f"{file}: consult-meta {key} slug {slug!r} not in "
                        f"_reference/{key}.yaml (add entry/alias)"
                    )

    # 6. derived-table (slug,id) check (after aggregate)
    check_derived_tables(folder, manifest, frags, errors)

    # report
    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  - {e}")
    else:
        print("No blocking errors.")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print(f"  - {w}")

    # M7 signal file: record the current basis + clean flag so the advisor's
    # reconcile guard is satisfied only when the area verified clean this pass.
    import orchestrate
    orchestrate.emit_reconcile(str(folder), not errors)

    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(reconcile(sys.argv[1]))
