#!/usr/bin/env python3
"""
doc_model.py — the shared spine of the CONSULT MVP pipeline.

This is the ONE module the rest of the system imports (M0 scaffold, M3 aggregate,
M4 docx builder, M5 synthesis, and reconcile.py). It owns:

  - load_manifest(folder)        -> dict         (read manifest.json)
  - validate_manifest(manifest)  -> [errors]     (v1 schema check)
  - display_numbers(manifest)    -> {slug: "L2.seq"}   (the ONLY numberer)
  - SECTION_TITLES / section_slug / section_letters    (M23 section registry:
    slug is identity, the A–G letter is a render-time display transform;
    M16 move 1's seven-section model is an edit to that registry)
  - resolve_tokens(text, numbers, mode) -> text   ([[slug]] -> number/title)
  - assemble(folder)             -> AssembledDoc  (structured, not a string)

Contracts are defined in docs/README.md. Keep this module free of any
number-baking or heading heuristics: numbering lives here and only here, and the
heading contract is "one `#` title (in the manifest), every section is `##`".

Python 3, stdlib only.
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import json
import re
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
# M23 — the SECTION REGISTRY.  Slug is IDENTITY, letter is DISPLAY.
#
# This is the sections' half of the split `[[slug]]` : display number already
# has for procedures and `CTRL-01` : `CTRL-07` has for callouts. It lives here,
# in the shared spine, for the same reason `display_numbers` does: it is read by
# every engine (scaffold stamps titles from it, render assigns letters from it,
# client_config canonicalizes profile tokens through it, aggregate keys section
# bodies by it) and it must have exactly ONE definition. It is pure data plus
# three pure functions — no manifest, no filesystem, stdlib only.
#
# Fragments carry `### Scope`; the LETTER is stamped at render from
# the profile's `sections:` order. The A–H letters remain accepted as PROFILE
# aliases (frozen at their historical MEANING below) so a profile written before
# M16 move 1 keeps meaning the same sections after the rename + merge.
# --------------------------------------------------------------------------- #

#: slug -> canonical title, in canonical document order. THE M16 MOVE 1 EDIT
#: (the seven-section model with declared jobs) is this dict plus the alias maps
#: below — never a re-letter of every fragment heading in the corpus.
#:
#: The seven sections and their declared jobs (docs/M16-section-model.md,
#: Design 1) — the drafter contract carries them verbatim:
#:   A. Scope                 what this covers/excludes, which procedures adjoin
#:   B. At a Glance           a TABLE; the single home for the card facts
#:   C. Before You Start      one line per artifact (Pre-Requisites + Inputs)
#:   D. Procedure             the steps
#:   E. Outputs & Evidence    what exists afterwards, what is retained
#:   F. Key Controls          job unchanged
#:   G. Known Issues …        defects only
SECTION_TITLES: dict[str, str] = {
    "scope": "Scope",
    "quick-reference": "At a Glance",
    "before-you-start": "Before You Start",
    "steps": "Procedure",
    "outputs": "Outputs & Evidence",
    "controls": "Key Controls",
    "issues": "Known Issues & Improvement Opportunities",
}
#: Canonical document order (the order letters are assigned in by default).
SECTION_SLUGS: list[str] = list(SECTION_TITLES)

#: The historical A–H letter positions, FROZEN as profile aliases — pointed at
#: the M16 slugs the historical sections BECAME. These are not derived from the
#: order above: their whole job is to keep an existing `body_omit: [F]` pointing
#: at `controls` and `[H]` at `issues` across any reshape, which is why `G` still
#: means `outputs` even though `outputs` renders as E in the seven-section model
#: (M23 point 3 — "existing profiles keep meaning the same sections through any
#: future rename" — deliberately overrides M16's `body_omit: [F, G]` prose).
#: `C` and `D` both point at the merged `before-you-start`.
SECTION_LETTER_ALIASES: dict[str, str] = {
    "A": "scope", "B": "quick-reference", "C": "before-you-start",
    "D": "before-you-start", "E": "steps", "F": "controls", "G": "outputs",
    "H": "issues",
}

#: A `###` sub-section heading, with the letter prefix OPTIONAL — the parse
#: contract for the transition: `### Scope` (migrated) and
#: `### A. Process Overview` (pre-M16 title, unmigrated) both resolve to `scope`.
#: `####` steps never match (`###` must be followed by whitespace).
SECTION_HEADING_RE = re.compile(
    r"^(?P<hashes>#{3})\s+(?:(?P<letter>[A-Z])\.\s+)?(?P<title>\S.*?)\s*$"
)


def _norm_section_key(text: str) -> str:
    """Normalize a slug or title to its lookup key ("Pre-Requisites" ->
    "pre-requisites"), so registry titles, slugs and hand-typed variants of
    either resolve to the same entry."""
    return re.sub(r"[^a-z0-9]+", "-", str(text).strip().lower()).strip("-")


#: PAST titles -> slug. A section renamed in `SECTION_TITLES` adds its old title
#: here and every already-drafted fragment keeps resolving — which is what makes
#: M16 move 1's rename a registry edit instead of a corpus-wide heading rewrite.
#: This is the whole cost of M16 move 1's RENAME half: every 8-section fragment
#: in the corpus keeps parsing, rendering, aggregating and reconciling, and the
#: CONTENT wave (A-shrink, B-table, C+D merge) follows as a drafter pass.
SECTION_TITLE_ALIASES: dict[str, str] = {
    "Process Overview": "scope",
    "Quick Reference": "quick-reference",
    "Pre-Requisites": "before-you-start",
    "Inputs": "before-you-start",
    "Step-by-Step Procedure": "steps",
    "Outputs": "outputs",
    # M16's table names F simply "Controls"; the job is unchanged, so the
    # canonical title stays "Key Controls" and the short form is accepted.
    "Controls": "controls",
    # The docx builder's legacy label for H.
    "Known Issues / Improvement Notes": "issues",
}

#: PAST slugs -> slug. The profile-input half of the same promise: a hand-written
#: `body_omit: [overview]` or `sections: [prerequisites, inputs]` keeps meaning
#: the sections it always meant. Titles are matched separately (above), so these
#: never make a `###` heading resolve.
SECTION_SLUG_ALIASES: dict[str, str] = {
    "overview": "scope",
    "prerequisites": "before-you-start",
    "inputs": "before-you-start",
}

#: The M16 C+D merge, recorded so a diagnostic can NAME it. A fragment drafted
#: before the content wave carries BOTH of these headings, and both resolve to
#: `before-you-start` — see `duplicate_sections` for what the pipeline does with
#: that (tolerate, keep every fact, report).
SECTION_MERGE_SOURCES: dict[str, tuple[str, ...]] = {
    "before-you-start": ("Pre-Requisites", "Inputs"),
}

#: (title_keys, section_keys) rebuilt whenever the registry above changes, so a
#: runtime registry edit (a rename, a merge) takes effect everywhere at once.
_KEYS_CACHE: tuple = ()


def _section_keys() -> tuple[dict, dict]:
    """(title spellings -> slug, profile-input spellings -> slug).

    Title keys are TITLES ONLY — a heading is matched against them, so
    `### Steps` (which is nobody's title) stays unresolved rather than being
    mistaken for `Step-by-Step Procedure`. Profile-input keys add the slugs.
    """
    global _KEYS_CACHE
    stamp = (tuple(SECTION_TITLES.items()), tuple(SECTION_TITLE_ALIASES.items()),
             tuple(SECTION_SLUG_ALIASES.items()))
    if _KEYS_CACHE and _KEYS_CACHE[0] == stamp:
        return _KEYS_CACHE[1], _KEYS_CACHE[2]
    titles: dict[str, str] = {}
    inputs: dict[str, str] = {}
    for slug, title in SECTION_TITLES.items():
        for key in (_norm_section_key(title),
                    _norm_section_key(title).replace("-", "")):
            titles.setdefault(key, slug)
        for key in (slug, _norm_section_key(slug), _norm_section_key(title),
                    _norm_section_key(title).replace("-", "")):
            inputs.setdefault(key, slug)
    for title, slug in SECTION_TITLE_ALIASES.items():
        for key in (_norm_section_key(title),
                    _norm_section_key(title).replace("-", "")):
            titles.setdefault(key, slug)
            inputs.setdefault(key, slug)
    for old_slug, slug in SECTION_SLUG_ALIASES.items():
        inputs.setdefault(_norm_section_key(old_slug), slug)
    _KEYS_CACHE = (stamp, titles, inputs)
    return titles, inputs


def section_slug(token) -> Optional[str]:
    """Canonicalize one section reference to its slug, or None if unknown.

    Accepts the slug (`controls`), the canonical title (`Key Controls`) and the
    historical letter alias (`F`, `F.`) — profile point 3's "letter aliases
    remain accepted at parse time and are canonicalized to slugs".
    """
    if token is None:
        return None
    text = str(token).strip().rstrip(".")
    if not text:
        return None
    if len(text) == 1 and text.upper() in SECTION_LETTER_ALIASES:
        return SECTION_LETTER_ALIASES[text.upper()]
    return _section_keys()[1].get(_norm_section_key(text))


def section_of_title(title: str) -> Optional[str]:
    """The slug whose TITLE (canonical or a registered past title) this text is,
    or None. Titles only — `section_slug` is the one that also takes slugs and
    letters."""
    return _section_keys()[0].get(_norm_section_key(title or ""))


def section_of_heading(line: str) -> Optional[str]:
    """The section slug a `###` heading line identifies, or None.

    THE ONE PARSER of a section heading — render (hide/letter), aggregate (key
    the bodies), scaffold (filter the skeleton), kits and the advisor's profile
    drift guard all ask here, so "which section is this?" cannot be answered two
    ways.

    TRANSITION CONTRACT (both forms parse, migration is never a prerequisite):
      - `### Scope`                 -> `scope`     (migrated; title matched)
      - `### A. Process Overview`   -> `scope`     (a PAST title; still matched)
      - `### F. Some Local Wording` -> `controls`  (title unknown; LETTER used)
      - `### Steps`                 -> None        (nobody's title, no letter)
    Title first, letter second: the title is the identity the drafter writes,
    the letter is a legacy positional fallback.
    """
    m = SECTION_HEADING_RE.match(line or "")
    if not m:
        return None
    slug = section_of_title(m.group("title"))
    if slug is None and m.group("letter"):
        slug = SECTION_LETTER_ALIASES.get(m.group("letter"))
    return slug


def section_heading_title(line: str) -> Optional[str]:
    """The title text of a `###` heading, letter prefix stripped."""
    m = SECTION_HEADING_RE.match(line or "")
    return m.group("title") if m else None


def section_headings(text: str) -> list[tuple[str, str]]:
    """Every resolvable `###` section heading in `text`, as (slug, written title),
    in document order. THE ONE SCANNER — reconcile's merge diagnostic and any
    other "which sections does this fragment have, and how many times?" question
    ask here rather than re-walking lines with their own regex."""
    out: list[tuple[str, str]] = []
    for line in (text or "").split("\n"):
        slug = section_of_heading(line)
        if slug is not None:
            out.append((slug, section_heading_title(line) or ""))
    return out


def duplicate_sections(text: str) -> dict[str, list[str]]:
    """{slug: [written titles]} for every section slug `text` heads MORE THAN
    ONCE — i.e. the M16 C+D transition state, where a fragment drafted before
    the content wave carries `### Pre-Requisites` AND `### Inputs` and both
    resolve to `before-you-start`.

    THE TRANSITION BEHAVIOUR IS TOLERATE + REPORT, never fail:
      - `aggregate.split_subsections` CONCATENATES the bodies in document order,
        so no fact is lost and every register still sees its content;
      - `render` letters both headings the same and gives the registry title to
        the FIRST only, so the second stays visibly as authored (`C. Inputs`
        under `C. Before You Start`) — the reader can see the un-merged pair;
      - `reconcile` emits a WARNING naming the fragment and the merge, so the
        state is loud but exit 0: the content wave is imminent and blocking the
        gate on it would wedge every existing area on a rename.
    """
    seen: dict[str, list[str]] = {}
    for slug, written in section_headings(text):
        seen.setdefault(slug, []).append(written)
    return {slug: titles for slug, titles in seen.items() if len(titles) > 1}


def section_letters(order=None) -> dict[str, str]:
    """Return {slug: letter} — the render-time DISPLAY transform.

    The letter is the section's 1-based position in `order` (the profile's
    `sections:` list), exactly as a procedure's display number is its position
    in its L2 bucket. With the default order this is A–H, which is why a
    rendered document is letter-identical to a pre-M23 one.
    """
    slugs = list(SECTION_SLUGS if order is None else order)
    return {slug: chr(ord("A") + i) for i, slug in enumerate(slugs)}


def section_title(slug: str) -> str:
    """The canonical title for a slug (the slug itself if unregistered)."""
    return SECTION_TITLES.get(slug, slug)


# --------------------------------------------------------------------------- #
# display_numbers — the ONLY implementation of the display number
# --------------------------------------------------------------------------- #

def procedures(manifest: dict) -> list[dict]:
    """Module-level convenience: the manifest's `role: procedure` components,
    in manifest `order`. (Callers like scope_delta expect this alongside the
    AssembledDoc.procedures() method.)"""
    procs = [c for c in manifest.get("components", []) if c.get("role") == "procedure"]
    return sorted(procs, key=lambda c: (c.get("order", 0), c.get("file", "")))


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
# callout_display_ids — the ONLY implementation of global callout numbering
# --------------------------------------------------------------------------- #

def callout_display_ids(folder) -> dict[tuple[str, str], str]:
    """Return {(procedure-slug, local-id): display-id} for the whole area.

    Drafters always number callouts locally from 01 — they never know their
    place in the document. Global sequential numbering is a DISPLAY transform,
    derived here exactly like display_numbers: walk procedures in manifest
    order and hand out one 2-digit counter per prefix across the document
    (GAP-01…, PP-01…, zero-padded to 2 digits, growing naturally past 99).
    Procedure files are never rewritten; render and the derived-view builders
    both consume this one map so body and appendices always agree.
    """
    from callouts import iter_defined_ids  # sibling module, same directory

    folder = Path(folder)
    manifest = load_manifest(folder)
    counters: dict[str, int] = {}
    mapping: dict[tuple[str, str], str] = {}
    for comp in procedures(manifest):
        slug = comp.get("slug")
        fpath = folder / (comp.get("file") or "")
        if not slug or not fpath.is_file():
            continue
        text = fpath.read_text(encoding="utf-8")
        for prefix, local_id in iter_defined_ids(text):
            counters[prefix] = counters.get(prefix, 0) + 1
            mapping[(slug, local_id)] = f"{prefix}-{counters[prefix]:02d}"
    return mapping


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

    def _fmt_number(slug: str) -> str:
        if slug not in numbers:
            raise KeyError(f"unknown [[#{slug}]] cross-reference")
        val = numbers[slug]
        if isinstance(val, str):
            # Callers may pass "1.1" or a prebuilt "1.1 Title" label — the
            # number is always the leading token.
            return val.split(" ", 1)[0]
        return val.get("number", "")

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
        # `[[#slug]]` forces number-only resolution (table Ref cells where the
        # title is its own column); `[[slug]]` follows the caller's mode.
        number_only = inner.lstrip().startswith("#")
        bare = inner.lstrip().lstrip("#") if number_only else inner
        # Leave gap/callout-style body tags alone: they contain a space+dash or
        # match an ID grammar, not a bare procedure slug.
        if _is_procedure_slug(bare):
            out.append(_fmt_number(bare.strip()) if number_only
                       else _fmt(bare.strip()))
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
