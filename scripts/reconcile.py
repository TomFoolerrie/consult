#!/usr/bin/env python3
"""
reconcile.py — QC gate for a CONSULT area folder (folder-native, per-fragment).

This is the r3 rewrite of the old global-ID reconciler. IDs are now
PROCEDURE-LOCAL: `CTRL-001` in `bank-reconciliation` and `CTRL-001` in
`asset-disposal` are distinct, keyed on the tuple `(slug, local-id)`. Each
procedure fragment is parsed independently; a reference only reconciles within
its own fragment. There is no global ID namespace.

Checks (see docs/README.md + docs/M2-splitter-manifest.md; the authoritative
ORDER and numbering live in the CHECKS registry at the bottom of this file —
M28 replaced the old per-check comment numbering with that one list):

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
    - a known individual's FULL NAME in procedure/derived prose (names come
      from roles.yaml `people:` lists + `_client/org-chart.yaml`; procedures
      refer to people by ROLE, never by name)
    - M19 — a procedure fragment with no substance: zero-byte, or nothing
      beyond its heading(s). NOT a length check (M15's retirement stands).
    - M22.1 — an `SRC-<n>` citation with no entry in `_reference/sources.yaml`,
      and a procedure fragment citing no `SRC-` id at all
    - M22.2 — a `sources.yaml` `touches` slug that is not a manifest procedure
      slug (same check, same message, as `sources.py` load time)
    - M22.3 — a derived file whose `<!-- derived: KIND; writer: W -->` marker
      disagrees with the manifest's `derived_kind`/`writer` (or is unparseable)
    - M22.4 — an H1 in a procedure fragment (the heading contract): an ATX
      `# ` line, or (M28) a setext `===` underline making the line above an H1
    - M22.5 — a baked display number (`see|per|step|section 1.2`) in fragment or
      agent-derived prose; the sanctioned cross-reference form is `[[slug]]`
    - M22.6 — a callout ID quoted in agent-owned derived prose (82/84) outside a
      derived-table row (render display-transforms IDs only inside procedures)
    - M16.3 — a callout carrying `detail:` with no `note:`. The two are two views
      of one body; `detail` renders only in the appendix, so the inline view at
      the step would be empty (see `check_note_detail`)
    - M29 — a DRAFTED procedure fragment (no `unfilled` sentinel) with no
      `consult-meta` fenced block at all: noun binding is silently skipped, so
      the Systems view / Role Dictionary / RACI just omit the procedure
    - M29 2.1a — a register reference (the `<register>#<entry-id>` id form, or
      the `the <Title> register` phrase form) naming a register or entry that
      does not exist under the engagement's components/_client/registers
      (known registers/entries are named in the message; an unresolved
      all-lowercase phrase is business-register prose and never flags)
    - M29 2.1c — a reference resolving to a class-CONTEXT register entry (or a
      file-level phrase reference to an all-context register): context entries
      are never cited by name — cite the provenance source or raise a GAP
      (M30 A2's align-never-evidence backstop)

  WARNING (exit stays 0):
    - a `consult-meta` systems:/roles: slug absent from `_reference/*.yaml`
    - a standalone first/last name of a known individual in procedure/derived
      prose (possible leak — could be a coincidence, so the human judges)
    - fragments cite `SRC-` ids but `_reference/sources.yaml` holds none (the
      citation checks are skipped — see the documented boundaries below)
    - M16.3 — a `detail:` on a CONTROL / SCREENSHOT PLACEHOLDER: those kinds are
      short by nature and take `note` only. The register still carries it
    - M16.1 — two `###` headings resolving to ONE section (`Pre-Requisites` +
      `Inputs` after the merge): the fragment is awaiting the content wave. Every
      fact is kept (aggregate concatenates) so this can never be an error
    - M29 — a PROSE line past 100 columns in a procedure fragment (the drafter
      contract hard-wraps at ~80; consolidator anchors (M12) and the citation
      scrub's one-newline window (M4) depend on it). Table rows, fenced blocks,
      URLs, headings, callout `>` lines and HTML comments are exempt; ONE
      warning per fragment (first offending line + "and N more")
    - M29 — a number-only `[[#slug]]` token outside a table row: the form is
      for Ref cells where the title is its own column; in prose it renders a
      cryptic bare number (use `[[slug]]`). Cross-area `[[#area/slug]]` is
      already an M26 ERROR and is not double-reported here
    - M29 2.1b — a CITABLE register entry's distinctive value (dollar amount,
      quoted string) restated in a fragment that nowhere references the owning
      register: reference, don't restate (essential-to-execute values may
      stay — the human judges; one warning per fragment+entry)

Documented boundaries (deliberate, see docs/M19 + docs/M22):
    - A fragment still carrying the `<!-- unfilled -->` sentinel is exempt from
      the M19 substance check, the M22 zero-citation check, and the advisory
      language/shape checks (hedge, British, table shape, cross-area): it
      declares itself unfinished and the advisor routes it to `fill`. M19
      targets SILENT emptiness. The GRAMMAR checks (callout/ID parse, heading
      contract, baked numbers, named individuals) still run on a skeleton —
      an H1 or a name leak is already wrong before the content wave, and the
      scaffolder never writes one. The exemption is decided ONCE per fragment
      (Ctx.fragments) so no check can drift its own reading of the sentinel.
    - `touches` membership and the SRC- citation checks need a manifest /
      a populated sources.yaml respectively; during initial scoping either may
      not exist yet, so each check no-ops until its authority is on disk.
    - M29: the consult-meta PRESENCE check no-ops until a noun registry exists
      on disk (`_reference/systems.yaml` or `roles.yaml`) — same M22 pattern:
      a block that binds prose to registry slugs cannot be demanded before any
      registry exists to bind to (initial scoping, or a standalone fixture
      area). Once either file is present, a drafted fragment with no block is
      an ERROR: the omission is invisible downstream (the views just omit it).
    - M29 2.1: the register checks no-op outside a components/ engagement root
      — registers are engagement-level (M30 rejected per-area shadowing), so a
      standalone area has no layer to resolve against. Inside a root the
      answering layer is always the parent's _client/registers. An
      UNSTRUCTURED pre-M30 register file resolves by name but its entries are
      unknowable: references into it pass 2.1a and never trigger 2.1c.

Usage:
    python3 scripts/reconcile.py <area-folder>

Exit code: 0 = clean or warnings only; 1 = errors; 2 = bad usage / unreadable.

Python 3, stdlib + pyyaml.
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

import re
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)
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

# `sources.py` owns _reference/sources.yaml: the `touches` ⊆ manifest-slugs
# validator (M22 check 2) lives there so the load-time gate and this gate can
# never drift, and the SRC- id registry read has one implementation.
try:
    import sources as sources_mod
except ImportError:  # pyyaml absent → sources.py unimportable; check no-ops
    sources_mod = None

# `registers.py` owns the register entry grammar (M30): its load_all() is the
# single read seam for components/_client/registers/, so the M29 Part 2.1
# checks never re-parse register files with their own regex.
try:
    import registers as registers_mod
except ImportError:  # pragma: no cover - registers.py is always present
    registers_mod = None

# The `unfilled` sentinel grammar is the advisor's fill predicate (guard 4);
# borrowed rather than restated so the M19/M22 exemption cannot drift from it.
try:
    from orchestrate import UNFILLED_RE
except ImportError:  # pragma: no cover - orchestrate is always present
    UNFILLED_RE = re.compile(r"(<!--\s*unfilled\s*-->)|(status\s*:\s*unfilled)",
                             re.I)


# --------------------------------------------------------------------------- #
# Callout grammar
# --------------------------------------------------------------------------- #

# Callout grammar primitives are shared with aggregate.py via callouts.py so the
# LABEL→prefix map + ID/gap grammar never drift. reconcile keeps its own loose
# CALLOUT_RE (it must still detect a callout with a MALFORMED id to flag it).
import client_config  # noqa: E402

from callouts import (  # noqa: E402
    LABEL_PREFIX, DELIM as _DELIM, ID_INLINE_RE,
    id_strict_re, id_inline_re,
    BODY_GAP_RE, BARE_GAP_RE, XREF_RE, blank_fences as strip_fences,
    NOTE_FIELD, DETAIL_FIELD, DETAIL_KINDS, callout_field,
)

# A callout label line inside a blockquote (loose id capture so a malformed id
# is still seen here and reported, then validated against the declared id
# grammar parse_procedure assembles):
#   > **<LABEL> — <ID>:** <text>
CALLOUT_RE = re.compile(
    r"^\s*>\s*\*\*\s*(?P<label>[A-Z][A-Z ]+?)\s*" + _DELIM + r"\s*"
    r"(?P<id>[^:*]+?)\s*:\*\*",
)

DERIVED_MARKER_RE = re.compile(r"<!--\s*derived:", re.IGNORECASE)

# The ownership marker in full: `<!-- derived: KIND; writer: W -->` (M22 check 3
# compares both fields against the manifest entry).
DERIVED_MARKER_FULL_RE = re.compile(
    r"<!--\s*derived:\s*(?P<kind>[^;>]+?)\s*;\s*writer:\s*(?P<writer>[^\s>]+?)\s*-->",
    re.IGNORECASE,
)

# An `SRC-` citation as the drafter writes it (docs/README.md sources lifecycle).
# Compared LITERALLY against the ids in _reference/sources.yaml, so `SRC-1` does
# not satisfy a registry holding `SRC-001`.
SRC_RE = re.compile(r"\bSRC-\d+\b")

# An H1 line — "the one rule" (docs/README.md heading contract). Up to three
# leading spaces still opens an ATX heading.
H1_RE = re.compile(r"^ {0,3}#[ \t]")

# A setext H1 underline (`Title` + `===`) — the same defect in the other
# markdown spelling, which evaded the contract until M28. Only promotes the
# line ABOVE it, so check_heading_contract pairs it with a paragraph line.
SETEXT_H1_RE = re.compile(r"^ {0,3}=+\s*$")

# A baked display number: the ticket's deliberately NARROW contextual pattern.
# Case-insensitive ("Section 3.2" is the same defect). A false positive costs one
# rewritten sentence; a false negative goes stale on the first reorder.
BAKED_NUMBER_RE = re.compile(r"\b(?:see|per|step|section)\s+\d+\.\d+", re.IGNORECASE)

# Fenced code blocks (``` or ~~~) are blanked via callouts.blank_fences
# (imported above as strip_fences), preserving line count/numbers.
FENCE_LINE_RE = re.compile(r"^\s*(```|~~~)")


def extract_consult_meta(text: str) -> tuple[dict, int]:
    """The parsed body of the ```consult-meta``` fence plus the fence opener's
    1-based line number, or ({}, 0) when there is none (M28: the line rides
    along so the registry-slug warnings can point at the fence)."""
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
                return {}, 0
            try:
                return (yaml.safe_load(raw) or {}), i + 1
            except yaml.YAMLError:
                return {}, i + 1
    return {}, 0


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


def load_people_names(folder: Path) -> list[str]:
    """Known individuals: roles.yaml `people:` lists + _client/org-chart.yaml.

    Both sources are optional; with neither present the name check is a no-op
    (the drafters' role-only rule still applies, it just isn't enforced)."""
    names: list[str] = []
    if yaml is None:
        return names

    rfile = folder / "_reference" / "roles.yaml"
    if rfile.is_file():
        try:
            data = yaml.safe_load(rfile.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            data = {}
        for entry in data.get("roles") or []:
            if isinstance(entry, dict):
                for p in entry.get("people") or []:
                    if isinstance(p, str):
                        names.append(p.strip())

    # M13: the org chart resolves through the client-config layers — the area's
    # own `_client/` shadows the engagement-wide `components/_client/`.
    for entry in client_config.load(folder).get("people") or []:
        if isinstance(entry, dict) and isinstance(entry.get("name"), str):
            names.append(entry["name"].strip())
        elif isinstance(entry, str):
            names.append(entry.strip())

    seen: set[str] = set()
    out: list[str] = []
    for n in names:
        if n and n.lower() not in seen:
            seen.add(n.lower())
            out.append(n)
    return out


# --------------------------------------------------------------------------- #
# Run context: read-once cache + fragment iteration (M28)
# --------------------------------------------------------------------------- #

def _components(manifest: dict, role: str | None = None,
                writer: str | None = None) -> list[dict]:
    """Manifest components, optionally filtered by `role` and (for derived
    files) by `writer`."""
    out = []
    for comp in manifest.get("components", []):
        if role is not None and comp.get("role") != role:
            continue
        if writer is not None and comp.get("writer") != writer:
            continue
        out.append(comp)
    return out


class FragText:
    """One component's text as a check sees it: raw, fence-blanked, and the
    `unfilled` sentinel verdict — each produced exactly once per run."""

    __slots__ = ("comp", "file", "slug", "raw", "blanked", "unfilled")

    def __init__(self, comp: dict, raw: str, blanked: str, unfilled: bool):
        self.comp = comp
        self.file = comp.get("file", "")
        self.slug = comp.get("slug")
        self.raw = raw
        self.blanked = blanked
        self.unfilled = unfilled


class Ctx:
    """One reconcile run: the manifest, the error/warning accumulators, and
    the read-once file cache — `{relpath: (raw, blanked, unfilled)}`. Every
    check takes this instead of the pre-M28 copy-pasted
    (folder, manifest, errors, warnings) preamble, so each fragment costs one
    disk read, one blank_fences pass and one UNFILLED_RE search per run
    (folder state is the run's snapshot; a mid-run write is already undefined,
    so there is no mtime invalidation)."""

    def __init__(self, folder: Path, manifest: dict):
        self.folder = folder
        self.manifest = manifest
        self.errors: list[str] = []
        self.warnings: list[str] = []
        # slug -> Frag, built by check_procedure_parse for check_derived_tables.
        self.frags: dict[str, Frag] = {}
        # relpath -> (raw | None, blanked | None, unfilled).
        self._cache: dict[str, tuple[str | None, str | None, bool]] = {}
        # Sibling areas, scanned once — the xref check and the cross-area
        # ownership check both consume them (doc_model owns the one scanner).
        self.siblings = doc_model.sibling_procedures(folder)

    def _entry(self, comp: dict) -> tuple[str | None, str | None, bool]:
        file = comp.get("file", "")
        got = self._cache.get(file)
        if got is None:
            fpath = self.folder / file
            if file and fpath.is_file():
                raw = fpath.read_text(encoding="utf-8")
                got = (raw, strip_fences(raw), bool(UNFILLED_RE.search(raw)))
            else:
                got = (None, None, False)
            self._cache[file] = got
        return got

    def read(self, comp: dict) -> str | None:
        """A component's raw text, or None when the file is not on disk
        (missing files are reported once by the manifest/derived checks)."""
        return self._entry(comp)[0]

    def blanked(self, comp: dict) -> str | None:
        """A component's fence-blanked text (same None contract as read)."""
        return self._entry(comp)[1]

    def fragments(self, comps: list[dict], skip_unfilled: bool = False):
        """Yield a FragText per on-disk component of `comps`, in manifest
        order. `skip_unfilled=True` applies the documented sentinel exemption
        (see the module docstring's boundaries)."""
        for comp in comps:
            raw, blanked, unfilled = self._entry(comp)
            if raw is None or (skip_unfilled and unfilled):
                continue
            yield FragText(comp, raw, blanked, unfilled)


def _fragment_and_agent_derived(manifest: dict) -> list[dict]:
    """Procedure fragments + agent-owned derived files: the prose a drafter or
    synthesis agent writes, and the only prose those checks police."""
    return (_components(manifest, role="procedure")
            + _components(manifest, role="derived", writer="agent"))


# --------------------------------------------------------------------------- #
# Named individuals
# --------------------------------------------------------------------------- #

def check_named_individuals(ctx: Ctx) -> None:
    """Individuals appear in prose by ROLE, never by name.

    A multi-token full name is unambiguous → ERROR. A standalone first/last
    name token (or a single-token person entry) could be a coincidence
    ("Mark", "Price") → WARNING, case-sensitive, for the human to judge.
    Static front matter (role: static) is exempt — e.g. the Document Profile
    legitimately credits interviewees by name."""
    names = load_people_names(ctx.folder)
    if not names:
        return

    full: list[tuple[str, re.Pattern]] = []
    token_owner: dict[str, str] = {}
    for name in names:
        parts = name.split()
        if len(parts) >= 2:
            full.append((name, re.compile(
                r"\b" + r"\s+".join(re.escape(p) for p in parts) + r"\b",
                re.IGNORECASE)))
            for tok in parts:
                if len(tok) >= 3:
                    token_owner.setdefault(tok, name)
        elif len(name) >= 3:
            token_owner.setdefault(name, name)
    token_res = [(tok, owner, re.compile(r"\b" + re.escape(tok) + r"\b"))
                 for tok, owner in token_owner.items()]

    comps = [c for c in ctx.manifest.get("components", [])
             if c.get("role") in ("procedure", "derived")]
    for f in ctx.fragments(comps):
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            spans: list[tuple[int, int]] = []
            for name, rx in full:
                for m in rx.finditer(line):
                    spans.append(m.span())
                    ctx.errors.append(
                        f"{f.file}:{n}: NAMED INDIVIDUAL {name!r} — refer to "
                        f"people by role (roles.yaml `people` mapping)"
                    )
            for tok, owner, rx in token_res:
                for m in rx.finditer(line):
                    if any(s <= m.start() and m.end() <= e for s, e in spans):
                        continue
                    ctx.warnings.append(
                        f"{f.file}:{n}: possible named individual {tok!r} "
                        f"({owner}) — use the role instead"
                    )
                    break  # one warning per token per line


# --------------------------------------------------------------------------- #
# M19 — fragment substance (docs/M19-fragment-integrity.md)
# --------------------------------------------------------------------------- #

def has_substance(text: str, blanked: bool = False) -> bool:
    """True when a fragment carries content beyond its heading(s).

    Fence bodies (including `consult-meta`) are blanked first (skipped with
    `blanked=True` when the caller already holds blank_fences output): a
    fragment whose only non-heading content is its end-matter slug block has
    not been written. Blank lines, HTML comments and horizontal rules are
    likewise not substance. There is deliberately NO length or verbosity
    threshold — this answers "did the writer finish", not "is this long
    enough" (M15's retirement stands)."""
    for line in (text if blanked else strip_fences(text)).splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("<!--") and s.endswith("-->"):
            continue
        if set(s) <= set("-*_=+ "):          # rules / empty bullets
            continue
        return True
    return False


def check_fragment_substance(ctx: Ctx) -> None:
    """A zero-byte or heading-only procedure fragment is a blocking error (F2).

    EXEMPTION: a fragment still carrying the `<!-- unfilled -->` sentinel is a
    scaffolded skeleton that declares itself unfinished and is routed to `fill`
    by the advisor (guard 4). M19 exists for SILENT emptiness — the interrupted
    drafter that removed the sentinel and wrote nothing."""
    for f in ctx.fragments(_components(ctx.manifest, role="procedure")):
        if not f.raw.strip():
            ctx.errors.append(
                f"{f.file}: EMPTY FRAGMENT — zero-byte procedure file; an "
                f"interrupted drafter leaves no `unfilled` sentinel, so re-run "
                f"fill for {f.slug!r}"
            )
        elif f.unfilled:
            continue                      # declared-unfinished skeleton: exempt
        elif not has_substance(f.blanked, blanked=True):
            ctx.errors.append(
                f"{f.file}: HEADING-ONLY FRAGMENT — no content beyond the "
                f"heading(s); re-run fill for {f.slug!r}"
            )


# --------------------------------------------------------------------------- #
# M22 — the constitution (docs/M22-enforce-invariants.md)
# --------------------------------------------------------------------------- #

def check_src_citations(ctx: Ctx) -> None:
    """M22 check 1 — every cited `SRC-<n>` is registered, and a procedure cites
    at least one.

    BOUNDARY: skipped when `_reference/sources.yaml` registers no ids (absent,
    unreadable, or empty — the initial-scoping window). The skip is loud: a
    fragment citing ids with no registry to check them against warns."""
    ids = sources_mod.registered_ids(str(ctx.folder)) if sources_mod else set()
    for f in ctx.fragments(_components(ctx.manifest, role="procedure")):
        cited: list[tuple[str, int]] = []
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            for m in SRC_RE.finditer(line):
                cited.append((m.group(0), n))
        if not ids:
            if cited:
                ctx.warnings.append(
                    f"{f.file}: cites {cited[0][0]} but _reference/sources.yaml "
                    f"registers no SRC- ids — citation check skipped"
                )
            continue
        for cid, n in cited:
            if cid not in ids:
                ctx.errors.append(
                    f"{f.file}:{n}: UNREGISTERED CITATION {cid} — no such id in "
                    f"_reference/sources.yaml"
                )
        if not cited and not f.unfilled:
            ctx.errors.append(
                f"{f.file}: NO SOURCE CITATION — procedure cites no SRC- id "
                f"(the drafter contract mandates Source Materials)"
            )


#: Hedge phrases that mark uncertainty. The drafter contract routes
#: uncertainty into GAP callouts (which final mode strips); a hedge in body
#: prose ships to the client, so it is flagged — WARNING, not ERROR, because
#: fragments drafted under the older contract are full of them and the fix
#: is editorial, not blocking.
HEDGE_RE = re.compile(
    r"\bTBD\b|\bunconfirmed\b|\bnot\s+confirmed\b|\bno\s+source\b",
    re.IGNORECASE)


#: Common British business spellings (drafter contract: American English,
#: always). A targeted word list, NOT a general -ise detector — "advise",
#: "premise", "raise", "analysis" and "analyst" are shared spellings and must
#: never flag.
BRITISH_RE = re.compile(
    r"\b\w*(?:synchronis|organis|standardis|authoris|finalis|prioritis"
    r"|recognis|categoris|centralis|formalis|normalis|utilis|minimis"
    r"|maximis|itemis|capitalis|operationalis|analys(?:e|ed|ing)"
    r"|colour|behaviour|favour|licenc|programme)\w*\b"
    r"|\bcentre\b|\bwhilst\b|\bamongst\b",
    re.IGNORECASE)


def check_british_spellings(ctx: Ctx) -> None:
    """American English, always (drafter contract). Sources may speak British;
    the fragment must not. WARNING — editorial, not blocking."""
    for f in ctx.fragments(_components(ctx.manifest, role="procedure"),
                           skip_unfilled=True):
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            m = BRITISH_RE.search(line)
            if m:
                ctx.warnings.append(
                    f"{f.file}:{n}: BRITISH SPELLING ('{m.group(0)}') — the "
                    f"drafter contract requires American English"
                )


def check_cross_area_ownership(ctx: Ctx) -> None:
    """One process is never documented in two L1s (the client-taxonomy
    boundary rule) — but [[slug]] tokens only resolve within an area, so a
    drafter describing a SIBLING AREA's activity has no reference to reach
    for and documents it inline instead. This check makes that visible: a
    fragment whose prose contains another area's procedure TITLE is flagged.
    Advisory (a legitimate one-sentence handoff mention also matches); the
    fix is the drafter's ownership rule — one handoff sentence, no steps.
    Single-word titles are skipped (too collision-prone to be signal)."""
    if ctx.folder.resolve().parent.name != "components":
        # Silent inertness is the failure mode this line exists to prevent:
        # an area run outside the engagement layout gets NO cross-L1
        # protection, and nothing else says so. A note, not a WARNING — a
        # deliberately standalone area is legitimate.
        print(f"note: cross-area ownership check inactive — {ctx.folder} is "
              f"not under a components/ engagement root, so sibling areas "
              f"are not visible")
        return
    # ctx.siblings is doc_model's one sibling scanner (the pre-M28 private
    # duplicate here had already drifted from it).
    sibs = [(area, slug, title)
            for area, info in ctx.siblings.items()
            for slug, title in info["slugs"].items()
            if len(title.split()) >= 2]
    if not sibs:
        return
    for f in ctx.fragments(_components(ctx.manifest, role="procedure"),
                           skip_unfilled=True):
        lines = f.blanked.lower().splitlines()
        for area_name, slug, title in sibs:
            needle = title.lower()
            for n, line in enumerate(lines, start=1):
                if needle in line:
                    ctx.warnings.append(
                        f"{f.file}:{n}: names '{title}' — an activity owned by "
                        f"{area_name}/{slug} (another area): describe the "
                        f"handoff in one sentence; never document another "
                        f"area's procedure"
                    )
                    break  # one warning per sibling title per file


# A markdown table separator row. It must carry at least one `|` or `:` —
# a bare `---` is a thematic break, not a table (M28: it used to match, so a
# prose line containing '|' above a horizontal rule read as a table header).
_TABLE_SEP_ROW_RE = re.compile(r"^(?=.*[|:])[\s|:\-]+$")


def _cell_count(line: str) -> int:
    """Cells in a markdown table row, honoring the `\\|` escape."""
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return len(re.split(r"(?<!\\)\|", line))


def check_table_shape(ctx: Ctx) -> None:
    """A table row with MORE cells than its header is almost always a bare
    `|` in cell text shearing the row (drafter contract: escape it `\\|`).
    The render ships the sheared shape silently — a phantom column and every
    later cell one over — so it is flagged here. Fewer cells than the header
    is not flagged: writers legitimately leave trailing cells off."""
    for f in ctx.fragments(_components(ctx.manifest, role="procedure"),
                           skip_unfilled=True):
        lines = f.blanked.splitlines()
        for i, line in enumerate(lines):
            if "|" not in line or i + 1 >= len(lines):
                continue
            nxt = lines[i + 1]
            if not ("-" in nxt and _TABLE_SEP_ROW_RE.match(nxt)):
                continue
            width = _cell_count(line)
            j = i + 2
            while j < len(lines) and lines[j].strip() and "|" in lines[j]:
                extra = _cell_count(lines[j]) - width
                if extra > 0:
                    ctx.warnings.append(
                        f"{f.file}:{j + 1}: SHEARED TABLE ROW — {extra} more "
                        f"cell(s) than the header; a bare '|' in cell text "
                        f"splits the row (escape it as '\\|')"
                    )
                j += 1


def check_hedge_prose(ctx: Ctx) -> None:
    """Uncertainty lives in callouts, never in body prose (drafter contract).
    A hedge phrase on a non-callout line of a filled procedure fragment would
    survive into the client export — callouts strip, prose does not."""
    for f in ctx.fragments(_components(ctx.manifest, role="procedure"),
                           skip_unfilled=True):
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            if line.lstrip().startswith(">"):
                continue
            m = HEDGE_RE.search(line)
            if m:
                ctx.warnings.append(
                    f"{f.file}:{n}: HEDGE IN PROSE ('{m.group(0)}') — "
                    f"uncertainty belongs in a GAP callout (strippable), not "
                    f"body prose; state what is established and raise a gap "
                    f"for the rest"
                )


def check_touches(ctx: Ctx) -> None:
    """M22 check 2 — `sources.yaml` `touches` ⊆ manifest procedure slugs.

    The validator itself lives in `sources.py` (it owns the file) so this gate
    and the load-time gate report the identical defect. BOUNDARY: no-ops until
    a readable manifest.json exists — during initial scoping `sources.yaml` is
    written by taxonomy BEFORE scaffold writes the manifest, and a check with no
    authority to check against must not fail an area."""
    if sources_mod is None:
        return
    for e in sources_mod.touches_errors(str(ctx.folder)):
        ctx.errors.append(e)


def check_derived_markers(ctx: Ctx) -> None:
    """Marker presence (r3) + M22 check 3: the marker's kind and writer must
    match the manifest entry. This is the DETECTION layer for one-writer-per-
    file — a drafter that overwrote a sibling's derived view is named here."""
    for comp in _components(ctx.manifest, role="derived"):
        file = comp.get("file", "")
        raw = ctx.read(comp)
        if raw is None:
            ctx.errors.append(
                f"manifest.json: derived file {file!r} declared but missing on disk"
            )
            continue
        if not DERIVED_MARKER_RE.search(raw):
            ctx.errors.append(
                f"{file}: derived file missing its `<!-- derived: KIND; writer: W -->` marker"
            )
            continue
        m = DERIVED_MARKER_FULL_RE.search(raw)
        if not m:
            ctx.errors.append(
                f"{file}: UNPARSEABLE OWNERSHIP MARKER — expected "
                f"`<!-- derived: KIND; writer: W -->`"
            )
            continue
        kind, writer = m.group("kind").strip(), m.group("writer").strip()
        want_kind = str(comp.get("derived_kind") or "").strip()
        want_writer = str(comp.get("writer") or "").strip()
        if kind.lower() != want_kind.lower():
            ctx.errors.append(
                f"{file}: OWNERSHIP MARKER MISMATCH — marker kind {kind!r} but "
                f"manifest derived_kind {want_kind!r}"
            )
        if writer.lower() != want_writer.lower():
            ctx.errors.append(
                f"{file}: OWNERSHIP MARKER MISMATCH — marker writer {writer!r} "
                f"but manifest writer {want_writer!r}"
            )


def check_heading_contract(ctx: Ctx) -> None:
    """M22 check 4 — an H1 in a procedure fragment. The assembled document's
    single `#` is the manifest title; component files carry none. Both
    spellings are caught: an ATX `# ` line, and (M28) a setext `===`
    underline promoting the paragraph line above it."""
    for f in ctx.fragments(_components(ctx.manifest, role="procedure")):
        lines = f.blanked.splitlines()
        for n, line in enumerate(lines, start=1):
            if H1_RE.match(line):
                ctx.errors.append(
                    f"{f.file}:{n}: H1 IN FRAGMENT — every section is "
                    f"`##`; the one `#` is the assembled title (manifest)"
                )
            elif SETEXT_H1_RE.match(line) and n >= 2:
                # A `===` underline is an H1 only under a paragraph line —
                # not under a heading, list, quote, table or another rule.
                prev = lines[n - 2].strip()
                if prev and not prev.startswith(("#", ">", "-", "*", "+", "|")) \
                        and not SETEXT_H1_RE.match(prev):
                    ctx.errors.append(
                        f"{f.file}:{n}: H1 IN FRAGMENT — a setext `===` "
                        f"underline makes {prev!r} an H1; every section is "
                        f"`##` (the one `#` is the assembled title)"
                    )


def check_baked_numbers(ctx: Ctx) -> None:
    """M22 check 5 — a baked display number in fragment or agent-derived prose.
    The sanctioned cross-reference is `[[slug]]`, resolved at render."""
    for f in ctx.fragments(_fragment_and_agent_derived(ctx.manifest)):
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            for m in BAKED_NUMBER_RE.finditer(line):
                ctx.errors.append(
                    f"{f.file}:{n}: BAKED DISPLAY NUMBER "
                    f"{m.group(0)!r} — cross-reference with [[slug]] (display "
                    f"numbers are derived at render time)"
                )


def check_quoted_callout_ids(ctx: Ctx) -> None:
    """M22 check 6 — a callout ID quoted in agent-owned derived prose (82/84)
    outside a derived-table row. render.py rewrites IDs to their display form
    only inside procedure sections, so a quoted local id silently disagrees with
    the document's numbering. Table rows are the sanctioned carrier (they are
    validated as (slug, id) pairs by check_derived_tables)."""
    for f in ctx.fragments(_components(ctx.manifest, role="derived",
                                       writer="agent")):
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            if line.lstrip().startswith("|"):
                continue
            # Floor-only by design: this walks AGENT-OWNED derived prose,
            # where no type declaration is in hand (M70).
            for m in ID_INLINE_RE.finditer(line):
                ctx.errors.append(
                    f"{f.file}:{n}: CALLOUT ID {m.group(0)} in "
                    f"agent-owned prose — reference [[slug]] and describe the "
                    f"item in words (ids are rewritten only in procedures)"
                )


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
        self.warnings: list[str] = []


def check_note_detail(file: str, lines: list[str], frag: Frag) -> None:
    """M16 move 3 — validate the two-view callout body.

    `note:` and `detail:` are ordinary sub-fields, so the only thing to check is
    that the split is coherent:

    - `detail:` with no `note:` is an **ERROR**. The two fields are two views of
      one source; `detail` renders only in the appendix, so the step would show
      a callout with an empty body — the reader at the step loses the finding
      entirely. Either add the note or drop the field name and let the whole
      body render inline (the pre-M16 behavior).
    - `detail:` on a CONTROL or SCREENSHOT PLACEHOLDER is a **WARNING**: those
      kinds are short by nature and take `note` only. Nothing is dropped — the
      register carries the detail either way — so this is a style signal, not a
      broken document.
    """
    label: str | None = None
    fields: dict[str, int] = {}

    def close() -> None:
        if label is None:
            return
        d = fields.get(DETAIL_FIELD.lower())
        if d and NOTE_FIELD.lower() not in fields:
            frag.errors.append(
                f"{file}:{d}: CALLOUT `{DETAIL_FIELD}:` WITHOUT `{NOTE_FIELD}:` "
                f"on {label!r} — `{DETAIL_FIELD}` renders only in the appendix, "
                f"so the inline view would be empty"
            )
        if d and label not in DETAIL_KINDS:
            frag.warnings.append(
                f"{file}:{d}: {label} takes `{NOTE_FIELD}` only — a "
                f"`{DETAIL_FIELD}:` here is carried to the register but the "
                f"kind is short by nature (M16 move 3)"
            )

    for n, line in enumerate(lines, start=1):
        m = CALLOUT_RE.match(line)
        if m:
            close()
            label = re.sub(r"\s+", " ", m.group("label")).strip()
            label = label if label in LABEL_PREFIX else None
            fields = {}
            continue
        if label is None:
            continue
        if not line.lstrip().startswith(">"):
            close()
            label = None
            continue
        f = callout_field(line)
        if f:
            fields.setdefault(f.lower(), n)
    close()


def check_merged_sections(file: str, text: str, frag: Frag) -> None:
    """M16 move 1 — TWO HEADINGS, ONE SECTION: the transition state, as a WARNING.

    The registry merged `Pre-Requisites` + `Inputs` into `Before You Start`, so a
    fragment drafted before the content wave heads the SAME slug twice. Nothing
    is broken by it — aggregate concatenates the bodies (no fact is lost), render
    letters both headings the same and only re-titles the first — so this is
    fail-LOUD but NOT blocking: the wave is imminent, and erroring would wedge
    every already-drafted area on what was supposed to be a registry edit.

    The warning points at the SECOND heading (the merge point) and names the
    fragment, the merged section and the two headings, so it doubles as the
    content wave's work list.
    """
    dups = doc_model.duplicate_sections(text)
    if not dups:
        return
    # Heading line numbers, via the one section-heading scanner.
    lines_of: dict[str, list[int]] = {}
    for n, line in enumerate(text.split("\n"), start=1):
        s = doc_model.section_of_heading(line)
        if s is not None:
            lines_of.setdefault(s, []).append(n)
    for slug, titles in dups.items():
        merged = doc_model.SECTION_MERGE_SOURCES.get(slug)
        why = (f" — {' + '.join(merged)} merged into it (M16 move 1)"
               if merged else "")
        at = lines_of.get(slug, [0, 0])[1]
        frag.warnings.append(
            f"{file}:{at}: {len(titles)} headings resolve to the one "
            f"`{doc_model.section_title(slug)}` section "
            f"({', '.join(repr(t) for t in titles)}){why}: every fact is kept "
            f"and the render is coherent, but this fragment is AWAITING THE "
            f"M16 CONTENT WAVE (see the drafter contract's "
            f"\"Content wave: 8 → 7 sections\" work order)"
        )


def parse_procedure(slug: str, file: str, text: str,
                    blanked: str | None = None,
                    label_to_prefix: dict | None = None) -> Frag:
    """Parse one procedure fragment's callout grammar into a Frag. `blanked`
    takes pre-computed blank_fences output (M28's cache); external callers
    (review_apply, tests) keep passing raw text alone.

    M70: the callout VOCABULARY may come from a loaded type declaration —
    `label_to_prefix` is its {LABEL: PREFIX} map, floor-unioned with the v1
    five — and both id patterns are assembled here from that set, exactly as
    kernel._parse_callouts assembles the strict one (M62 A1). With no
    declaration in hand the floor applies, byte-identically."""
    vocab = {**LABEL_PREFIX, **(label_to_prefix or {})}
    strict_re = id_strict_re(vocab.values())
    inline_re = id_inline_re(vocab.values())
    frag = Frag(slug, file)
    stripped = blanked if blanked is not None else strip_fences(text)
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
            if label not in vocab:
                # unknown label with the callout shape — not our concern here
                pass
            else:
                idm = strict_re.match(raw_id)
                if not idm:
                    frag.errors.append(
                        f"{file}:{n}: MALFORMED ID {raw_id!r} for label {label!r}"
                    )
                else:
                    prefix = idm.group(1)
                    expected = vocab[label]
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
        for m in inline_re.finditer(line):
            _id = f"{m.group(1)}-{m.group(2)}"
            frag.referenced.setdefault(_id, []).append(n)
        for m in BODY_GAP_RE.finditer(line):
            _id = f"GAP-{m.group(1)}"
            frag.referenced.setdefault(_id, []).append(n)

    check_note_detail(file, lines, frag)
    check_merged_sections(file, text, frag)

    # per-fragment dangling: every referenced id defined in THIS procedure
    for _id, ref_lines in frag.referenced.items():
        if _id not in frag.defined:
            frag.errors.append(
                f"{file}:{ref_lines[0]}: DANGLING ID {_id} referenced but not "
                f"defined within procedure {slug!r}"
            )
    return frag


def check_manifest_schema(ctx: Ctx) -> None:
    """Manifest v1 schema (incl. duplicate order/slug/file)."""
    for e in doc_model.validate_manifest(ctx.manifest):
        ctx.errors.append(f"manifest.json: {e}")


def check_procedure_parse(ctx: Ctx) -> None:
    """Per-fragment procedure parse: the callout/ID/gap grammar (parse_procedure)
    plus the missing-file error. Populates ctx.frags for check_derived_tables."""
    for comp in _components(ctx.manifest, role="procedure"):
        slug = comp.get("slug")
        file = comp.get("file", "")
        raw = ctx.read(comp)
        if raw is None:
            ctx.errors.append(
                f"manifest.json: procedure file {file!r} not found on disk")
            continue
        frag = parse_procedure(slug, file, raw, blanked=ctx.blanked(comp))
        ctx.errors.extend(frag.errors)
        ctx.warnings.extend(frag.warnings)
        ctx.frags[slug] = frag


def check_xref_tokens(ctx: Ctx) -> None:
    """[[slug]] cross-references resolve (dangling = ERROR) — all files.
    M26: [[area/slug]] cross-area tokens validate against the SIBLING
    manifest (identity exists from scoping — a scoped-but-unfilled target
    is valid). Outside a components/ engagement root, any cross token is
    an ERROR with a layout explanation."""
    known_slugs = set(doc_model.display_numbers(ctx.manifest))
    under_root = ctx.folder.resolve().parent.name == "components"
    for f in ctx.fragments(ctx.manifest.get("components", [])):
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            for m in XREF_RE.finditer(line):
                slug = m.group(1)
                area_ref, local = doc_model.split_xref(slug)
                if area_ref is None:
                    if slug not in known_slugs:
                        ctx.errors.append(
                            f"{f.file}:{n}: DANGLING [[{slug}]] — no such "
                            f"procedure"
                        )
                    continue
                if not under_root:
                    ctx.errors.append(
                        f"{f.file}:{n}: [[{slug}]] is a cross-area token, but "
                        f"this area is not under a components/ engagement "
                        f"root — move the L1s under one components/ dir, or "
                        f"reword as plain prose"
                    )
                    continue
                if m.group(0).startswith("[[#"):
                    ctx.errors.append(
                        f"{f.file}:{n}: [[#{slug}]] — cross-area tokens have "
                        f"no display number (another area's numbering is "
                        f"not stable from here); use [[{slug}]]"
                    )
                    continue
                sib = ctx.siblings.get(area_ref)
                if sib is None:
                    ctx.errors.append(
                        f"{f.file}:{n}: DANGLING [[{slug}]] — no sibling area "
                        f"{area_ref!r} (known: "
                        f"{', '.join(sorted(ctx.siblings)) or 'none'})"
                    )
                elif local not in sib["slugs"]:
                    ctx.errors.append(
                        f"{f.file}:{n}: DANGLING [[{slug}]] — area "
                        f"{area_ref!r} has no procedure {local!r} (its "
                        f"slugs: {', '.join(sorted(sib['slugs'])) or 'none'})"
                    )


def check_consult_meta(ctx: Ctx) -> None:
    """consult-meta systems:/roles: slugs exist in _reference/*.yaml (WARNING)."""
    systems, roles = load_registry_slugs(ctx.folder)
    for f in ctx.fragments(_components(ctx.manifest, role="procedure")):
        meta, fence_line = extract_consult_meta(f.raw)
        for key, registry in (("systems", systems), ("roles", roles)):
            for slug in (meta.get(key) or []):
                if slug not in registry:
                    ctx.warnings.append(
                        f"{f.file}:{fence_line}: consult-meta {key} slug "
                        f"{slug!r} not in _reference/{key}.yaml (add entry/alias)"
                    )


def check_consult_meta_presence(ctx: Ctx) -> None:
    """M29 check 2 — a DRAFTED procedure fragment with NO consult-meta block.

    The block is the machine binding (drafter contract rule 2): without it the
    fragment silently skips noun binding, so the Systems view / Role Dictionary
    / RACI omit the procedure and nothing says so — only unknown SLUGS warned
    before M29; a missing BLOCK was invisible. ERROR.

    EXEMPTION: an `unfilled` skeleton is routed to `fill` (the scaffolder
    writes no block by design). BOUNDARY (documented above): no-ops until
    `_reference/systems.yaml` or `roles.yaml` exists — no noun registry on
    disk, no binding authority to demand a binding to."""
    if yaml is None:
        return  # extract_consult_meta cannot see a fence body without pyyaml
    ref = ctx.folder / "_reference"
    if not ((ref / "systems.yaml").is_file() or (ref / "roles.yaml").is_file()):
        return
    for f in ctx.fragments(_components(ctx.manifest, role="procedure"),
                           skip_unfilled=True):
        _meta, fence_line = extract_consult_meta(f.raw)
        if fence_line == 0:
            ctx.errors.append(
                f"{f.file}: NOUN BINDING SKIPPED — no consult-meta block; the "
                f"Systems/Role/RACI views will omit this procedure; add a "
                f"```consult-meta``` block with its systems:/roles: slugs"
            )


# A URL anywhere on a line exempts it from the hard-wrap check — a long link
# cannot be wrapped without breaking it.
_URL_RE = re.compile(r"https?://", re.IGNORECASE)

#: The hard-wrap tolerance. The drafter contract wraps at ~80 columns; the
#: check flags only clear breaches so reflowed-but-honest prose never warns.
WRAP_LIMIT = 100


def check_hard_wrap(ctx: Ctx) -> None:
    """M29 check 3 — a PROSE line past WRAP_LIMIT columns (WARNING).

    The ~80-column hard wrap is the contract rule two mechanisms depend on:
    consolidator anchors must sit inside one line to literal-match (M12), and
    the citation scrub's window spans at most one newline (M4). Exempt: table
    rows (`|`), fenced blocks (already blanked in the cache), lines carrying a
    URL, headings, callout/definition `>` lines, and HTML comments. ONE
    warning per fragment — the first offending line plus a count — never one
    per line (noise discipline)."""
    for f in ctx.fragments(_components(ctx.manifest, role="procedure"),
                           skip_unfilled=True):
        offenders: list[tuple[int, int]] = []  # (line no, length)
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            if len(line) <= WRAP_LIMIT:
                continue
            s = line.lstrip()
            if (s.startswith(("|", "#", ">"))
                    or s.startswith("<!--")
                    or _URL_RE.search(line)):
                continue
            offenders.append((n, len(line)))
        if offenders:
            n, length = offenders[0]
            more = (f" (and {len(offenders) - 1} more)"
                    if len(offenders) > 1 else "")
            ctx.warnings.append(
                f"{f.file}:{n}: LONG PROSE LINE — {length} chars{more}; "
                f"hard-wrap at ~80 columns (anchor matching and the citation "
                f"scrub depend on wrapped prose)"
            )


def check_number_only_xref_in_prose(ctx: Ctx) -> None:
    """M29 check 4 — a number-only `[[#slug]]` token outside a table row
    (WARNING). The form exists for Ref cells where the title is its own
    column; in prose it renders a cryptic bare number. Cross-area tokens
    (`[[#area/slug]]`) are skipped: M26 already hard-errors those in
    check_xref_tokens, and one defect gets one report."""
    for f in ctx.fragments(ctx.manifest.get("components", []),
                           skip_unfilled=True):
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            if line.lstrip().startswith("|"):
                continue
            for m in XREF_RE.finditer(line):
                slug = m.group(1)
                if m.group(0).startswith("[[#") and "/" not in slug:
                    ctx.warnings.append(
                        f"{f.file}:{n}: [[#{slug}]] outside a table row — "
                        f"the number-only form renders a cryptic bare number "
                        f"in prose; use [[{slug}]]"
                    )


# --------------------------------------------------------------------------- #
# M29 Part 2.1 — engagement register references (docs/M29 + docs/M30)
# --------------------------------------------------------------------------- #

# The id form `<register>#<entry-id>` (M30 A1: the convention agents already
# use in proposals; prose MAY use it too). Candidate capture is loose (dots
# allowed) so a known dotted stem still validates; an UNKNOWN stem only errors
# when it looks like a register name — word chars/hyphens with at least one
# letter — so `file.md#anchor` link targets never flag. The entry-id half
# never ends on punctuation, so a sentence's trailing period is not swallowed.
REG_ID_FORM_RE = re.compile(
    r"(?<![\w.-])(?P<stem>[A-Za-z0-9][A-Za-z0-9_.-]*)#"
    r"(?P<eid>[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?)")
_STEM_SHAPE_RE = re.compile(r"[\w-]*[A-Za-z][\w-]*")

# The phrase form `the <Title> register` (case-insensitive). Title is 1-5
# words; resolution tries the whole capture then progressively shorter
# suffixes ("the client Approval Matrix register" still resolves), so only a
# phrase whose EVERY suffix normalizes to no known stem errors — and then
# only when the title is proper-noun cased ("the Capex Limits register").
# An all-lowercase unresolved phrase is prose about a BUSINESS register
# ("post-hoc review of the payment register" — a subsidiary ledger) and is
# skipped: the run-4 fixture proved the generic form false-positives, and a
# false-positive-prone gate is worse than a contract rule (M29's own
# gate-gaming rule). Resolution to a KNOWN register stays case-insensitive.
REG_PHRASE_FORM_RE = re.compile(
    r"\bthe\s+((?:[\w-]+\s+){0,4}[\w-]+)\s+register\b", re.IGNORECASE)

#: Distinctive strings inside a citable entry body: dollar amounts (normalized
#: against comma/space variants) and explicitly quoted strings.
_DOLLAR_RE = re.compile(r"\$\s?\d[\d,]*(?:[ ,]\d{3})*(?:\.\d+)?")
_QUOTED_RE = re.compile(r'"([^"\n]{4,80})"')


def _norm_stem(title: str) -> str:
    """Phrase-form normalization: lowercase, non-alnum runs → one hyphen."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _norm_dollar(s: str) -> str:
    return "$" + re.sub(r"[^\d.]", "", s).rstrip(".")


def load_engagement_registers(ctx: Ctx):
    """{stem: entries-or-None} via registers.load_all (the M30 read seam), or
    None when the area is not under a components/ engagement root — the
    documented no-op boundary for the Part 2.1 checks. Registers are
    ENGAGEMENT-LEVEL by construction (M30 rejected per-area shadowing), so the
    one layer that can answer is parent/_client/registers."""
    root = ctx.folder.resolve().parent
    if root.name != "components" or registers_mod is None:
        return None
    return {p.stem: entries
            for p, _title, entries in registers_mod.load_all(root)}


def _phrase_resolve(title: str, regs: dict) -> str | None:
    """The known stem a phrase capture resolves to, or None. Tries the whole
    normalized capture, then drops leading words (suffix match)."""
    words = title.split()
    for i in range(len(words)):
        stem = _norm_stem(" ".join(words[i:]))
        if stem in regs:
            return stem
    return None


def _register_refs(blanked: str, regs: dict):
    """Every register reference in a fragment, both detection forms:
    [(line, form, stem, eid-or-None, display)]. Unknown stems ride along with
    eid=None (phrase) or their eid (id form) for the existence check."""
    out = []
    for n, line in enumerate(blanked.splitlines(), start=1):
        url_spans = [m.span() for m in re.finditer(r"\S*://\S*", line)]
        for m in REG_ID_FORM_RE.finditer(line):
            if any(s <= m.start() < e for s, e in url_spans):
                continue
            stem = m.group("stem")
            if stem not in regs and not _STEM_SHAPE_RE.fullmatch(stem):
                continue  # dotted/dashed non-name (a link anchor, a path)
            out.append((n, "id", stem, m.group("eid"), m.group(0)))
        for m in REG_PHRASE_FORM_RE.finditer(line):
            stem = _phrase_resolve(m.group(1), regs)
            if stem is None and not re.search(r"\b[A-Z]", m.group(1)):
                continue  # unresolved all-lowercase phrase: business-register
                # prose ("the payment register"), not a reference — see above
            out.append((n, "phrase", stem if stem is not None
                        else _norm_stem(m.group(1)), None, m.group(0)))
    return out


def check_register_references(ctx: Ctx) -> None:
    """M29 Part 2.1(a) + (c) — register references resolve, and never name a
    context entry.

    (a) A reference to a register (or register#entry) that does not exist is
    an ERROR naming the known registers/entries. Two deliberately narrow
    detection forms only (no general prose NLP): the `<register>#<entry-id>`
    id form and the `the <Title> register` phrase form.

    (c) A reference resolving to a class-CONTEXT entry is an ERROR — context
    entries are never cited by name (M30 A2 item 2, the align-never-evidence
    backstop moved from prompt to gate). A file-level phrase reference to a
    register whose entries are ALL context errors the same way; a mixed-class
    register referenced at file level passes.

    BOUNDARIES: no-ops outside a components/ engagement root (registers are
    engagement-level; there is no layer to resolve against — same boundary as
    the cross-area checks). An UNSTRUCTURED pre-M30 register file resolves by
    name and its entries are unknowable: phrase and id references into it pass
    (a) and never trigger (c). The answering layer is always the engagement's
    components/_client/registers (M30 rejected per-area shadowing)."""
    regs = load_engagement_registers(ctx)
    if regs is None:
        return
    known = ", ".join(sorted(regs)) or "none"
    for f in ctx.fragments(_components(ctx.manifest, role="procedure"),
                           skip_unfilled=True):
        for n, form, stem, eid, disp in _register_refs(f.blanked, regs):
            if stem not in regs:
                ctx.errors.append(
                    f"{f.file}:{n}: UNKNOWN REGISTER {disp!r} — no register "
                    f"{stem!r} under components/_client/registers (the "
                    f"engagement layer; known: {known})"
                )
                continue
            entries = regs[stem]
            if entries is None:
                continue  # pre-M30 unstructured file: name resolves, entries
                # are unknowable — tolerated until migrated (registers.py)
            if form == "id":
                hit = next((e for e in entries if e.id == eid), None)
                if hit is None:
                    ids = ", ".join(e.id for e in entries) or "none"
                    ctx.errors.append(
                        f"{f.file}:{n}: UNKNOWN REGISTER ENTRY {disp} — "
                        f"register {stem!r} (engagement layer) has entries: "
                        f"{ids}"
                    )
                elif hit.cls == "context":
                    ctx.errors.append(
                        f"{f.file}:{n}: CONTEXT ENTRY CITED — {disp} is class "
                        f"context: context entries are never cited by name — "
                        f"cite the provenance source (see the register entry) "
                        f"or raise a GAP"
                    )
            elif entries and all(e.cls == "context" for e in entries):
                ctx.errors.append(
                    f"{f.file}:{n}: CONTEXT REGISTER CITED — {disp!r} names "
                    f"register {stem!r}, whose entries are all class context: "
                    f"context entries are never cited by name — cite the "
                    f"provenance source (see the register entry) or raise a "
                    f"GAP"
                )


def _distinctive_strings(body: str) -> list[str]:
    """A citable entry's distinctive strings: dollar amounts (normalized) and
    quoted strings. Values under 4 chars or purely numeric without a `$` are
    dropped (noise discipline)."""
    out = []
    for m in _DOLLAR_RE.finditer(body):
        v = _norm_dollar(m.group(0))
        if len(v) >= 4:  # `$` + 3 digits minimum
            out.append(v)
    for m in _QUOTED_RE.finditer(body):
        v = m.group(1).strip()
        if len(v) >= 4 and not re.fullmatch(r"[\d,. ]+", v):
            out.append(v)
    return out


def check_register_restatement(ctx: Ctx) -> None:
    """M29 Part 2.1(b) — a citable entry's DISTINCTIVE VALUE restated in
    fragment prose, in a fragment that nowhere references the owning register
    (either detection form): WARNING — reference, don't restate. Matching is
    deliberately conservative (exact dollar amounts normalized across
    comma/space variants, exact quoted strings — never fuzzy), and a fragment
    that references the register anywhere may carry the value (the
    essential-to-execute rule: the human judges). ONE warning per
    (fragment, entry). Same no-op boundary as check_register_references."""
    regs = load_engagement_registers(ctx)
    if not regs:
        return
    targets = []  # (stem, eid, [distinctive strings])
    for stem, entries in sorted(regs.items()):
        for e in entries or []:
            if e.cls == "citable":
                vals = _distinctive_strings(e.text)
                if vals:
                    targets.append((stem, e.id, vals))
    if not targets:
        return
    for f in ctx.fragments(_components(ctx.manifest, role="procedure"),
                           skip_unfilled=True):
        referenced = {stem for _n, _form, stem, _eid, _d
                      in _register_refs(f.blanked, regs) if stem in regs}
        lines = f.blanked.splitlines()
        for stem, eid, vals in targets:
            if stem in referenced:
                continue
            hit = None  # (line, value)
            for n, line in enumerate(lines, start=1):
                dollars = {_norm_dollar(m.group(0))
                           for m in _DOLLAR_RE.finditer(line)}
                for v in vals:
                    if (v in dollars if v.startswith("$") else v in line):
                        hit = (n, v)
                        break
                if hit:
                    break
            if hit:
                n, v = hit
                ctx.warnings.append(
                    f"{f.file}:{n}: RESTATED REGISTER VALUE {v!r} — restates "
                    f"{stem}#{eid} (engagement layer): reference the "
                    f"register, don't restate (essential-to-execute values "
                    f"may stay: human judges)"
                )


# --------------------------------------------------------------------------- #
# Derived-table (slug, id) check
# --------------------------------------------------------------------------- #

def check_derived_tables(ctx: Ctx) -> None:
    """Each derived-table row that names a Source Procedure [[slug]] and an ID
    must reference a (slug, id) pair that exists in that procedure. Runs after
    aggregate; silently no-ops when derived files are absent."""
    # {slug: {display-id, ...}} — the render-time global numbering authority,
    # fed from the read-once cache so the fragments are not re-read here.
    blanked_texts = {f.slug: f.blanked
                     for f in ctx.fragments(
                         _components(ctx.manifest, role="procedure"))
                     if f.slug}
    display_ids_of: dict[str, set[str]] = {}
    for (slug, _local), disp in doc_model.callout_display_ids(
            ctx.folder, blanked_texts=blanked_texts).items():
        display_ids_of.setdefault(slug, set()).add(disp)
    for f in ctx.fragments(_components(ctx.manifest, role="derived")):
        group_slug = None  # set by `#### [[slug]]` per-procedure group headings
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            if line.lstrip().startswith("#"):
                # Cross-area tokens (M26) are never Source-Procedure refs.
                hx = [x for x in XREF_RE.findall(line) if "/" not in x]
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
            # Floor-only by design: a derived TABLE row carries no type
            # declaration to build the alternation from (M70).
            ids = {f"{a}-{b}" for a, b in ID_INLINE_RE.findall(first_cell)}
            if not ids:
                continue
            if group_slug is not None:
                row_slug = group_slug
            else:
                # Combined "ID ([[#slug]])" first cell is authoritative; the
                # last token on the line is only the legacy Source-Procedure-
                # column fallback (free-text cells may quote siblings).
                first_xrefs = [x for x in XREF_RE.findall(first_cell)
                               if "/" not in x]
                xrefs = [x for x in XREF_RE.findall(line) if "/" not in x]
                row_slug = (first_xrefs[0] if first_xrefs
                            else (xrefs[-1] if xrefs else None))
            if row_slug is None:
                continue
            frag = ctx.frags.get(row_slug)
            for _id in ids:
                # Aggregate writes DISPLAY ids (doc_model.callout_display_ids);
                # a row is sound if its id is either the display id of one of
                # this procedure's callouts or (legacy) a local id it defines.
                ok = frag is not None and (
                    _id in frag.defined
                    or _id in display_ids_of.get(row_slug, ())
                )
                if not ok:
                    ctx.errors.append(
                        f"{f.file}:{n}: derived row references "
                        f"({row_slug}, {_id}) which is not defined in that procedure"
                    )


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #

# The gate, as ONE ordered list (M28). Order is observable — errors/warnings
# print in append order and tests grep the output — so new checks (M29+) are
# APPENDED to their severity band unless there is a reason not to. This list
# is also the numbering authority: the old per-call-site comment numbers
# (1-17, half-drifted from the docstring and from M22's internal numbers)
# live only here now.
def check_required_register_fields(ctx: Ctx) -> None:
    """v1.18 — fields a client deliverable must not ship blank, caught at the
    review round instead of discovered in the final export.

    Advisory (WARNING) on three sources the derived registers are built from:

    - a `roles.yaml` entry with no `reports_to` (an explicit
      "Not applicable" / "None" passes — unknown is the defect, not absence);
    - a `systems.yaml` entry with no `description`/`role` text;
    - a PAIN POINT callout with no `Impact:` (or `Severity:`) sub-field — the
      register row would carry an em dash where the reader expects why the
      pain point matters.
    """
    ref = ctx.folder / "_reference"
    if yaml is not None and ref.is_dir():
        for fname, field, what in (
                ("roles.yaml", ("reports_to", "reports-to"), "Reports To"),
                ("systems.yaml", ("description", "role"), "Role in Process")):
            f = ref / fname
            if not f.is_file():
                continue
            try:
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
            except yaml.YAMLError:
                continue
            # Unwrap the conventional top-level key (`roles:` / `systems:`).
            top = fname.split(".")[0]
            if isinstance(data, dict) and isinstance(
                    data.get(top), (list, dict)):
                data = data[top]
            entries = (data.items() if isinstance(data, dict)
                       else [(e.get("slug", "?"), e) for e in data
                             if isinstance(e, dict)]
                       if isinstance(data, list) else [])
            for slug, entry in entries:
                if not isinstance(entry, dict):
                    continue
                if not any(str(entry.get(k, "") or "").strip()
                           for k in field):
                    ctx.warnings.append(
                        f"_reference/{fname}: {slug!r} has no "
                        f"{'/'.join(field)} — the {what!r} register cell "
                        f"ships blank (state it, or say 'Not applicable')")
    for f in ctx.fragments(_components(ctx.manifest, role="procedure"),
                           skip_unfilled=True):
        label, label_line, fields = None, 0, set()

        def close():
            if label == "PAIN POINT":
                for need in ("impact", "severity"):
                    if need not in fields:
                        ctx.warnings.append(
                            f"{f.file}:{label_line}: PAIN POINT without "
                            f"`{need.title()}:` — its register row ships "
                            f"blank; say why it matters (or how much)")
        for n, line in enumerate(f.blanked.splitlines(), start=1):
            m = CALLOUT_RE.match(line)
            if m:
                close()
                label = re.sub(r"\s+", " ", m.group("label")).strip()
                label_line, fields = n, set()
                continue
            if label is None:
                continue
            if not line.lstrip().startswith(">"):
                close()
                label = None
                continue
            fld = callout_field(line)
            if fld:
                fields.add(fld.lower())
        close()


CHECKS: list = [
    # blocking-first: schema, grammar, references, ownership
    check_manifest_schema,        # 1  manifest v1 schema
    check_procedure_parse,        # 2  callout/ID/gap grammar + M16.3/M16.1
    check_xref_tokens,            # 3  [[slug]] + M26 [[area/slug]] tokens
    check_derived_markers,        # 4  derived marker presence + M22 check 3
    check_consult_meta,           # 5  consult-meta registry slugs (WARNING)
    check_derived_tables,         # 6  derived-table (slug, id) pairs
    check_named_individuals,      # 7  names → roles (ERROR full, WARNING token)
    check_fragment_substance,     # 8  M19 zero-byte / heading-only
    check_src_citations,          # 9  M22 check 1 — SRC- citations
    check_touches,                # 10 M22 check 2 — touches ⊆ manifest slugs
    check_heading_contract,       # 11 M22 check 4 — no H1 (ATX or setext)
    check_baked_numbers,          # 12 M22 check 5 — baked display numbers
    check_quoted_callout_ids,     # 13 M22 check 6 — quoted ids in agent prose
    check_consult_meta_presence,  # 14 M29 — no consult-meta block at all
    check_register_references,    # 15 M29 2.1a/c — register refs resolve;
    #                                  context entries never cited by name
    # advisory-only from here down (exit stays 0)
    check_hedge_prose,            # 16 hedges in body prose
    check_british_spellings,      # 17 British spellings
    check_table_shape,            # 18 sheared table rows
    check_cross_area_ownership,   # 19 sibling area's procedure title in prose
    check_hard_wrap,              # 20 M29 — prose line past ~100 cols
    check_number_only_xref_in_prose,  # 21 M29 — [[#slug]] outside a table row
    check_register_restatement,   # 22 M29 2.1b — restated distinctive value
    check_required_register_fields,  # 23 v1.18 — blank Reports To /
    #                                   system description / PP Impact
]


def reconcile(folder: str) -> int:
    folder = Path(folder)

    try:
        manifest = doc_model.load_manifest(folder)
    except doc_model.ManifestError as exc:
        # stdout like every other failure: callers tee stdout, and losing the
        # exit-2 explanation to an un-teed stderr was the M28 review's finding.
        print(f"ERROR: {exc}")
        return 2

    # M13: say which client-config layer answered, so a surprising name-check
    # result is one line of output away from being explained.
    print(client_config.report_line(folder))

    ctx = Ctx(folder, manifest)
    for check in CHECKS:
        check(ctx)
    errors, warnings = ctx.errors, ctx.warnings

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
    # M18/F8: also record WHICH files the errors name (every message above is
    # prefixed `<file>:` or `<file>:<line>:`), so guard 8 can route failures
    # confined to agent-owned derived views to their producer (`synthesize`)
    # and gate the ones no stage can fix. Files only — the messages stay here.
    import orchestrate
    orchestrate.emit_reconcile(
        str(folder), not errors,
        failing_files=sorted({e.split(":", 1)[0].strip() for e in errors}))

    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(reconcile(sys.argv[1]))
