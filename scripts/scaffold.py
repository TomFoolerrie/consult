#!/usr/bin/env python3
"""
scaffold.py — M0 confirm-gate scaffolder for the CONSULT MVP.

This is the deterministic Python half of M0. The `consult-taxonomy` agent has
already written proposals to `{area}/_reference/.proposed/` (procedures.yaml,
systems.yaml, roles.yaml, sources.yaml, optional new_buckets.yaml / glossary.yaml)
and a human has reviewed/edited them in place. Running

    python3 scripts/scaffold.py --confirm --area components/<area> [--l1 <slug>] \
        [--taxonomy skills/consult-taxonomy/reference/reference_taxonomy.yaml] \
        [--title "..."] [--subtitle "..."]

promotes `.proposed/` into the live `_reference/` (a MERGE, never a wipe), then
scaffolds `manifest.json` (v1) + one A–H skeleton per confirmed procedure + the
static front-matter files + empty derived stubs.

The manifest is treated the same way: procedures already in the live manifest
are ALWAYS preserved and the proposal delta is merged into them (re-emitted
slugs update in place, new slugs append). An incremental pass whose new sources
only touch existing procedures may therefore run with an empty — or absent —
procedures.yaml: registry merge + source stamping still happen and `.proposed/`
is still consumed, so the advisor loop advances normally.

M6 — RE-DISPATCH RIDES THE NOTES QUEUE. This step is also where an incremental
pass's *already-drafted* procedures get told about the new sources: for each
outstanding source in the promoted `sources.yaml`, every slug in its `touches`
that is already drafted (no `unfilled` sentinel) gets a `_review/{slug}.notes.yaml`
item — `kind: source`, `src: SRC-<id>`, plus the "what's new" wording the taxonomy
agent staged in `.proposed/notes.yaml`. The advisor's guard 2 then dispatches
`consult-drafter` in `mode: update` for exactly those slugs. Freshly scaffolded
slugs get no note: they carry the sentinel and take the `fill` path, which already
hands the drafter its whole tagged source list. Retirement notes (F8's workflow
half) ride the same file, `kind: retirement`, one per procedure citing the retired
slug. `.proposed/notes.yaml` is CONSUMED here, never promoted.

M14 — THIS IS ENFORCEMENT POINT 1 FOR THE DOCUMENT PROFILE. The engagement's
`_client/profile.yaml` (resolved via `client_config.profile`) decides which A–H
sections the skeletons carry and which derived components the manifest lists.
Nothing else in the pipeline gets to decide shape: the drafter fills what it is
handed, and render (enforcement point 2) strips what a later profile change
removed. A `body_omit` section is scaffolded exactly as if it were not listed —
it is authored and aggregated, and only the RENDER hides it. A profile whose
`derived:` set changes AFTER the confirm gate ran is reconciled into the live
manifest with `--sync-profile` (no `.proposed/` round): the path that lets an
area acquire `appendix-controls` so `body_omit: [controls]` has a destination.

Nothing touches the live folder until `--confirm` is passed. The step is
idempotent: re-running with the same confirmed set is a no-op; adding one
procedure creates only its file and a manifest entry with a sparse `order`
*between* its neighbours, touching no existing file.

Ownership boundaries (see docs/README.md):
  - `doc_model.py` is owned by M2 — imported here, only to validate what we write.
  - `procedure_skeleton.md` is owned by M1 — read if present, else fall back.

Python 3, stdlib + pyyaml.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

import yaml

# doc_model.py lives beside this script (top-level scripts/). Import it to
# validate the manifest we write. It is M2-owned; we only consume its API.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import doc_model  # type: ignore
except Exception:  # pragma: no cover - doc_model is a hard dependency in practice
    doc_model = None

# notes_util owns the `_review/{slug}.notes.yaml` bus shape (M6): we are one of
# its five producers (source notes + retirement notes, written at confirm).
import notes_util  # noqa: E402

# client_config owns config resolution (M13) and the document profile built on
# it (M14). This is ENFORCEMENT POINT 1: the skeletons carry only the profile's
# sections and the manifest lists only the profile's derived components. The
# drafter is told what the callout/tag vocabulary is; it never decides shape.
import client_config  # noqa: E402

# The section registry (M23) is doc_model's; client_config imports it hard, so
# by here it has resolved even if the guarded import above did not.
if doc_model is None:  # pragma: no cover - see the guarded import above
    doc_model = client_config.doc_model

# The `unfilled` sentinel grammar is OWNED BY the advisor (orchestrate.py guard
# 4). Borrowed, never restated, so "is this procedure already drafted?" is
# answered identically here and at the guard that would otherwise fill it.
try:
    from orchestrate import UNFILLED_RE  # type: ignore
except Exception:  # pragma: no cover - orchestrate ships beside us
    UNFILLED_RE = re.compile(r"(<!--\s*unfilled\s*-->)|(status\s*:\s*unfilled)",
                             re.I)


REPO_ROOT = Path(__file__).resolve().parent.parent

PROCEDURE_SKELETON = (
    REPO_ROOT / "skills" / "consult-drafter" / "reference" / "procedure_skeleton.md"
)
DEFAULT_TAXONOMY = (
    REPO_ROOT / "skills" / "consult-taxonomy" / "reference" / "reference_taxonomy.yaml"
)

# Registry yaml files promoted from .proposed/ -> live _reference/. procedures.yaml
# and new_buckets.yaml are CONSUMED to build the manifest but are NOT live registry
# files, so they are never promoted.
REGISTRY_FILES = ("systems.yaml", "roles.yaml", "sources.yaml", "glossary.yaml")
REGISTRY_KEYS = {
    "systems.yaml": "systems",
    "roles.yaml": "roles",
    "sources.yaml": "sources",
    "glossary.yaml": "glossary",
}

# Static, human-owned front matter (band 00–09). Kept minimal: the two files the
# folder model names explicitly. order values sit below the procedure band.
STATIC_FILES = [
    {"file": "00_document-profile.md", "heading": "Document Profile", "order": 0},
    {"file": "04_process-overview.md", "heading": "Process Overview", "order": 5},
]

# Derived views. Reader-orientation views (procedure index, role dictionary,
# systems) sit in the FRONT-MATTER band (orders 6–8, after Process Overview at
# 5, before the first procedure at 10). Synthesis + appendices form the
# back-matter band at filename prefix × 100 (8200+) — the wide offset keeps it
# clear of the sparse procedure orders (10, 20, 30, …). M3 (python) and M5
# (agent) own the actual generation.
DERIVED_FILES = [
    {"file": "06_procedure-index.md", "kind": "procedure-index", "writer": "python",
     "heading": "In-Scope Procedures", "order": 6},
    {"file": "07_role-dictionary.md", "kind": "role-dictionary", "writer": "python",
     "heading": "Role Dictionary", "order": 7},
    {"file": "08_systems.md", "kind": "systems", "writer": "python",
     "heading": "Systems & Data Inputs", "order": 8},
    {"file": "82_dependencies.md", "kind": "dependencies", "writer": "agent",
     "heading": "Key Dependencies", "order": 8200},
    {"file": "84_raci.md", "kind": "raci", "writer": "agent",
     "heading": "RACI Matrix", "order": 8400},
    # Appendix headings carry NO letters — "Appendix — <what it shows>".
    # Letters forced renumbering whenever a profile added or dropped a
    # register (the controls register was given a letterless heading for
    # exactly that reason), and nothing in the document cites an appendix by
    # letter: prose references go to procedures ([[slug]]) and callout ids.
    {"file": "88_appendix-a.md", "kind": "appendix-a", "writer": "python",
     "heading": "Appendix — Risks, Pain Points & Improvement Opportunities",
     "order": 8800},
    # M14: the destination F never had. OPT-IN — absent from the default derived
    # set, so an area with no profile is byte-identical to pre-M14. Sits right
    # after Appendix A (the other mechanically-built register) and takes no
    # letter, so adding it never re-letters B and C.
    {"file": "89_appendix-controls.md", "kind": "appendix-controls",
     "writer": "python", "heading": "Appendix — Key Controls Register",
     "order": 8900},
    {"file": "90_appendix-b-gaps.md", "kind": "gap-log", "writer": "python",
     "heading": "Appendix — Gap / Validation Log", "order": 9000},
    {"file": "91_appendix-c-screens.md", "kind": "screenshot-index", "writer": "python",
     "heading": "Appendix — Screenshot / Evidence Index", "order": 9100},
]

PROC_BASE = 10   # first procedure order
PROC_GAP = 10    # sparse gap between procedure orders


def profile_derived_files(profile=None) -> list[dict]:
    """The DERIVED_FILES entries this engagement's profile asks for (M14).

    `None` means "no profile resolved" and yields the default set — today's
    eight views, WITHOUT `appendix-controls` — so a manifest scaffolded in an
    engagement with no `profile.yaml` is byte-identical to pre-M14.
    """
    prof = profile if profile is not None else client_config.Profile()
    return [d for d in DERIVED_FILES if prof.wants(d["kind"])]


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #

def _load_yaml(path: Path) -> dict:
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def _dump_yaml(path: Path, data: dict) -> None:
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False),
        encoding="utf-8",
    )


def _titleize(area_slug: str) -> str:
    return " ".join(w.capitalize() for w in area_slug.replace("_", "-").split("-") if w)


def _entry_key(entry: dict) -> str | None:
    """Merge key for a registry entry: slug, else id (sources), else term."""
    for k in ("slug", "id", "term"):
        if entry.get(k):
            return str(entry[k])
    return None


def _merge_by_key(existing: list, proposed: list) -> list:
    """Merge proposed entries into existing, keyed by slug/id/term.

    New entries are appended; an entry the delta re-emits overrides the
    existing one FIELD-WISE ({**existing, **proposed}): fields the re-emission
    omits are preserved, not wiped — so a title tweak at the confirm gate
    can't silently destroy `upstream`/`variants`/`people`. Emitting an
    explicit empty value still clears a field. Existing entries the delta did
    NOT re-emit are preserved untouched.
    Order: existing order first, then new entries in proposed order.
    """
    out = list(existing or [])
    index = {}
    for i, e in enumerate(out):
        k = _entry_key(e) if isinstance(e, dict) else None
        if k is not None:
            index[k] = i
    for e in (proposed or []):
        if not isinstance(e, dict):
            continue
        k = _entry_key(e)
        if k is not None and k in index:
            old = out[index[k]]
            out[index[k]] = {**old, **e} if isinstance(old, dict) else e
        else:
            if k is not None:
                index[k] = len(out)
            out.append(e)
    return out


# --------------------------------------------------------------------------- #
# taxonomy
# --------------------------------------------------------------------------- #

def load_l1_buckets(taxonomy_path: Path, l1_slug: str) -> list[str]:
    """Return the L2 bucket slugs for the given L1, in taxonomy order."""
    tax = _load_yaml(taxonomy_path)
    cats = (tax.get("taxonomy") or {}).get("categories") or []
    for cat in cats:
        if cat.get("slug") == l1_slug:
            return [sc.get("slug") for sc in (cat.get("subcategories") or []) if sc.get("slug")]
    raise SystemExit(
        f"error: L1 slug {l1_slug!r} not found in taxonomy {taxonomy_path}"
    )


def compute_l2_order(procedures: list[dict], tax_buckets: list[str],
                     existing_l2_order: list[str]) -> list[str]:
    """The area's ordered L2 buckets = the ordering authority display_numbers reads.

    - Preserve any existing l2_order verbatim (ordinals must not drift on merge).
    - Append taxonomy-order buckets actually used by a procedure.
    - Append approved NEW buckets (an l2 used by a procedure but absent from the
      taxonomy) in first-seen order — the taxonomy itself is never mutated.
    """
    used: list[str] = []
    for p in procedures:
        l2 = p.get("l2")
        if l2 and l2 not in used:
            used.append(l2)

    order = list(existing_l2_order or [])
    for b in tax_buckets:                     # known buckets, taxonomy order
        if b in used and b not in order:
            order.append(b)
    for l2 in used:                           # approved new buckets, first-seen
        if l2 not in order:
            order.append(l2)
    return order


# --------------------------------------------------------------------------- #
# order assignment (sparse, insert-in-gap, renormalize only if a gap is full)
# --------------------------------------------------------------------------- #

def assign_procedure_orders(procedures: list[dict], l2_order: list[str],
                            existing_orders: dict[str, int]) -> dict[str, int]:
    """Assign a sparse global `order` to every procedure.

    Existing procedures keep their order unchanged. New procedures are inserted
    at their position (grouped by l2 in l2_order, then within bucket after the
    existing members) and given an order *between* their neighbours. If a gap is
    too tight to hold the run, the whole procedure sequence is renormalized
    (touches only the manifest, never a file) — the README-sanctioned fallback.
    """
    # Build the desired full sequence.
    seq: list[dict] = []
    by_l2: dict[str, list[dict]] = {}
    for p in procedures:
        by_l2.setdefault(p.get("l2"), []).append(p)
    ordered_l2 = list(l2_order) + [k for k in by_l2 if k not in l2_order]
    for l2 in ordered_l2:
        bucket = by_l2.get(l2, [])
        known = sorted(
            [p for p in bucket if p["slug"] in existing_orders],
            key=lambda p: existing_orders[p["slug"]],
        )
        fresh = [p for p in bucket if p["slug"] not in existing_orders]
        seq.extend(known + fresh)

    result: dict[str, int] = {}
    n = len(seq)
    i = 0
    last = 0
    while i < n:
        p = seq[i]
        if p["slug"] in existing_orders:
            result[p["slug"]] = existing_orders[p["slug"]]
            last = existing_orders[p["slug"]]
            i += 1
            continue
        j = i
        while j < n and seq[j]["slug"] not in existing_orders:
            j += 1
        run = seq[i:j]
        k = len(run)
        high = existing_orders[seq[j]["slug"]] if j < n else None
        low = last
        if high is None:
            for m, p2 in enumerate(run, start=1):
                result[p2["slug"]] = low + PROC_GAP * m
            last = low + PROC_GAP * k
        else:
            span = high - low
            if span >= k + 1:
                step = span // (k + 1)
                for m, p2 in enumerate(run, start=1):
                    result[p2["slug"]] = low + step * m
            else:
                return _renormalize(seq)   # gap exhausted
        i = j
    return result


def _renormalize(seq: list[dict]) -> dict[str, int]:
    return {p["slug"]: PROC_BASE + PROC_GAP * idx for idx, p in enumerate(seq)}


# --------------------------------------------------------------------------- #
# skeleton + stub rendering
# --------------------------------------------------------------------------- #

_FALLBACK_SKELETON = """## {heading}

<!-- unfilled -->

### Scope

TBD — what this procedure covers, what it explicitly excludes, and which
procedures adjoin it. Nothing else.

### At a Glance

| Field | Value |
|---|---|
| Trigger | TBD |
| Frequency | TBD |
| Preparer | TBD |
| Reviewer | TBD |
| Systems | TBD |
| Key inputs | TBD |
| Key outputs | TBD |

### Before You Start

- **<Artifact>** — TBD; TBD — the state it must be in.

### Procedure

#### Step 1: TBD

TBD — Describe the step in neutral current-state procedural language.

### Outputs & Evidence

- **Output 1:** TBD
- **Evidence retained:** TBD
- **Not retained:** TBD

### Key Controls

> **CONTROL — CTRL-001:** TBD — what is checked / reconciled / approved.
> - **Type:** Preventive | Detective | Corrective
> - **Frequency:** TBD
> - **Owner:** TBD

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** TBD — observed current-state friction, source-grounded.
> - **Impact:** TBD
> - **Severity:** High | Medium | Low

> **IMPROVEMENT OPPORTUNITY — IO-001:** TBD — the proposed improvement.
> - **Addresses:** PP-001

```consult-meta
systems: []
roles:   []
```
"""


# The end-matter fence that terminates the last sub-section (the `consult-meta`
# block belongs to no section, so it must survive even when the section it
# trails is dropped). Sub-section headings are recognized by the shared
# registry (M23): `### Key Controls` and a legacy `### F. Key Controls` both
# resolve to the `controls` slug, as do the pre-M16 titles (`### Inputs` →
# `before-you-start`) through `SECTION_TITLE_ALIASES`.
_END_MATTER_RE = re.compile(r"^\s*(`{3,}|~{3,})\s*consult-meta\s*$", re.I)


def keep_sections(text: str, sections) -> str:
    """Drop the `###` blocks of every section NOT in `sections` (M14/M23).

    `sections` is a list of section SLUGS; headings are resolved to slugs
    through the shared registry, so a skeleton written either way (letterless,
    or with a legacy `### F.` prefix) is filtered correctly.

    Byte-identical short circuit: if the skeleton names no section the profile
    excludes, the text is returned UNCHANGED — an engagement with no
    `profile.yaml` gets exactly today's skeleton, byte for byte.

    Deletion (not blanking) is right here, unlike render: nothing maps
    provenance lines onto a freshly stamped skeleton, and a drafter handed a
    blank hole would fill it in.
    """
    wanted = set(sections)
    lines = text.splitlines(keepends=True)
    present = {s for ln in lines
               if (s := doc_model.section_of_heading(ln)) is not None}
    if not present - wanted:
        return text

    out: list[str] = []
    dropping = False
    for ln in lines:
        if _END_MATTER_RE.match(ln):
            dropping = False       # end matter belongs to no section
        else:
            slug = doc_model.section_of_heading(ln)
            if slug is not None:
                dropping = slug not in wanted
        if not dropping:
            out.append(ln)
    # Dropping whole blocks leaves runs of blank lines behind; collapse them so
    # the drafter reads a skeleton, not a gap map.
    text = "".join(out)
    return re.sub(r"\n{3,}", "\n\n", text)


def render_skeleton(heading: str, sections=None) -> str:
    """Stamp one skeleton for a procedure — LETTERLESS headings (M23).

    Prefers M1's `procedure_skeleton.md` (the single definition of procedure
    SHAPE): take from its first `##` line onward (dropping the doc-comment header)
    and substitute the title. Falls back to a minimal shell built from the
    section registry if M1's file is absent. Either way the `<!-- unfilled -->`
    sentinel is present.

    The stamped headings carry the TITLE only (`### Scope`): the
    letter is a render-time transform, so no drafter ever writes one and no
    reshape ever re-writes one.

    `sections` (M14) restricts the stamped skeleton to the profile's section
    slugs; `None` stamps the full shape. M1 still owns the SHAPE of each
    section — this only decides which of them exist.
    """
    wanted = (client_config.ALL_SECTIONS if sections is None else sections)
    if PROCEDURE_SKELETON.is_file():
        raw = PROCEDURE_SKELETON.read_text(encoding="utf-8")
        lines = raw.splitlines(keepends=True)
        start = next((i for i, ln in enumerate(lines) if ln.startswith("## ")), None)
        if start is not None:
            body = "".join(lines[start:])
            body = body.replace("<Procedure Title>", heading)
            if not body.endswith("\n"):
                body += "\n"
            if "<!-- unfilled -->" not in body:
                # Guarantee the sentinel even if a future skeleton drops it.
                body = body.replace(
                    f"## {heading}\n", f"## {heading}\n\n<!-- unfilled -->\n", 1
                )
            return keep_sections(body, wanted)
    return keep_sections(_FALLBACK_SKELETON.format(heading=heading), wanted)


def render_static(heading: str) -> str:
    return (
        f"## {heading}\n\n"
        "TBD — human-owned section. Populate before sign-off.\n"
    )


def render_derived(kind: str, writer: str, heading: str) -> str:
    return (
        f"## {heading}\n\n"
        f"<!-- derived: {kind}; writer: {writer} -->\n\n"
        "> _Pending generation._\n"
    )


# --------------------------------------------------------------------------- #
# promotion (merge) + sources stamping
# --------------------------------------------------------------------------- #

def promote_reference(area: Path) -> None:
    """MERGE `_reference/.proposed/` registry files into live `_reference/`.

    Initial run: live is empty, so this is effectively a copy. Incremental run:
    new entries are added, re-emitted entries updated, and entries the delta did
    NOT re-emit are left intact. procedures.yaml / new_buckets.yaml are NOT
    registry files and are never promoted (they only drive the manifest).
    """
    proposed = area / "_reference" / ".proposed"
    live = area / "_reference"
    live.mkdir(parents=True, exist_ok=True)

    for fname in REGISTRY_FILES:
        pfile = proposed / fname
        if not pfile.is_file():
            continue
        key = REGISTRY_KEYS[fname]
        proposed_data = _load_yaml(pfile)
        live_file = live / fname
        live_data = _load_yaml(live_file)
        merged = _merge_by_key(live_data.get(key, []), proposed_data.get(key, []))
        out = dict(live_data)
        out[key] = merged
        _dump_yaml(live_file, out)


def stamp_sources(area: Path) -> None:
    """Stamp `hash` + `state` on every source in the live sources.yaml.

    Hashing is deterministic byte-work, so it belongs here (not in the agent).
    A source with no hash yet gets sha256 of its file bytes and state `new`;
    an already-stamped source keeps its state (the orchestrator flips it to
    `processed` later, not us).
    """
    sfile = area / "_reference" / "sources.yaml"
    if not sfile.is_file():
        return
    data = _load_yaml(sfile)
    changed = False
    for src in data.get("sources", []) or []:
        if not isinstance(src, dict):
            continue
        rel = src.get("file")
        if rel:
            fpath = area / rel
            if fpath.is_file():
                digest = hashlib.sha256(fpath.read_bytes()).hexdigest()
                if src.get("hash") != digest:
                    # Content changed (or first stamp): refresh hash. Only reset
                    # to `new` when there is no state yet — never un-process.
                    src["hash"] = digest
                    changed = True
            elif "hash" not in src:
                src["hash"] = ""
                changed = True
        if not src.get("state"):
            src["state"] = "new"
            changed = True
    if changed:
        _dump_yaml(sfile, data)


# --------------------------------------------------------------------------- #
# the notes bus: re-dispatch rides the review queue (M6)
# --------------------------------------------------------------------------- #

# `.proposed/notes.yaml` — the taxonomy agent's note WORDING. Consumed here (like
# procedures.yaml / new_buckets.yaml), never promoted to the live registry.
PROPOSED_NOTES = "notes.yaml"
PROPOSED_NOTE_KEYS = ("slug", "kind", "src", "note", "type", "location", "anchor")


def load_proposed_notes(area: Path) -> list[dict]:
    """Raw `notes:` list from `_reference/.proposed/notes.yaml` (or [])."""
    data = _load_yaml(area / "_reference" / ".proposed" / PROPOSED_NOTES)
    items = data.get("notes") or []
    return [it for it in items if it is not None]


def validate_proposed_notes(items: list[dict], known_slugs: set[str],
                            known_src_ids: set[str]) -> list[dict]:
    """Shape-check the proposal's notes BEFORE anything is promoted.

    SHAPE is fail-loud (an item with no `kind`, an unknown kind, no note text, a
    `kind: source` item with no/unknown `src`): the human fixes `.proposed/` and
    re-confirms, with the live folder untouched. TARGETING is not: a note naming
    a slug this area does not carry is dropped with a WARNING rather than
    aborting the confirm — writing it would create an orphan note and gate the
    ladder at `review_triage`, and the human editing `touches` at the gate (the
    sanctioned M6 veto) must never hard-fail the promotion."""
    out: list[dict] = []
    for i, it in enumerate(items, start=1):
        where = "_reference/.proposed/%s item %d" % (PROPOSED_NOTES, i)
        if not isinstance(it, dict):
            raise SystemExit("error: %s: not a mapping" % where)
        unknown = sorted(k for k in it if k not in PROPOSED_NOTE_KEYS)
        if unknown:
            raise SystemExit(
                "error: %s: unknown field(s) %s (allowed: %s)"
                % (where, ", ".join(unknown), ", ".join(PROPOSED_NOTE_KEYS)))
        slug = str(it.get("slug") or "").strip()
        kind = str(it.get("kind") or "").strip()
        src = str(it.get("src") or "").strip()
        note = str(it.get("note") or "").strip()
        if not slug:
            raise SystemExit("error: %s: no `slug:` (which procedure's drafter "
                             "is this note for?)" % where)
        if not kind:
            raise SystemExit(
                "error: %s: no `kind:` — every notes-bus item carries one of %s "
                "and there is no default (M6)"
                % (where, " | ".join(notes_util.KINDS)))
        if kind not in notes_util.KINDS:
            raise SystemExit("error: %s: unknown kind %r (expected one of %s)"
                             % (where, kind, " | ".join(notes_util.KINDS)))
        if not note:
            raise SystemExit("error: %s: no `note:` text — the drafter is given "
                             "the note verbatim" % where)
        if kind == "source":
            if not src:
                raise SystemExit(
                    "error: %s: `kind: source` with no `src:` — the drafter "
                    "resolves the SRC- id through sources.yaml, and retirement "
                    "accounting credits nothing without it (M6)" % where)
            if src not in known_src_ids:
                raise SystemExit(
                    "error: %s: src %r is not registered in sources.yaml "
                    "(registered: %s)"
                    % (where, src, ", ".join(sorted(known_src_ids)) or "none"))
        if slug not in known_slugs:
            print("  WARNING: %s: dropping note for '%s' — not a procedure in "
                  "this area (an orphan note gates the ladder at review_triage)"
                  % (where, slug))
            continue
        item = {"slug": slug, "kind": kind, "note": note}
        for k in ("src", "type", "location", "anchor"):
            v = str(it.get(k) or "").strip()
            if v:
                item[k] = v
        out.append(item)
    return out


def _is_drafted(area: Path, rel: str) -> bool:
    """True when a fragment exists and no longer carries the `unfilled` sentinel.

    This is the M6 discriminator for "does this procedure need a note?": a
    freshly scaffolded skeleton keeps the SENTINEL path (guard 4 `fill`
    dispatches it with its whole tagged source list), so notifying it would
    dispatch an update drafter at a skeleton — and guard 2 outranks guard 4, so
    it would win."""
    fp = area / rel
    if not fp.is_file():
        return False
    return not UNFILLED_RE.search(fp.read_text(encoding="utf-8"))


def default_source_note(sid: str, rel_file: str) -> str:
    return ("New source %s informs this procedure. Read it (resolve %s through "
            "_reference/sources.yaml — it is %s) and work in what it adds: "
            "revise contradicted text and delete any GAP it closes."
            % (sid, sid, rel_file or "listed there"))


def write_promoted_notes(area: Path, slug_files: dict[str, str],
                         proposal_notes: list[dict]) -> dict:
    """Write the `_review/{slug}.notes.yaml` items this confirmed proposal implies.

    Two producers in one pass, both landing on the M6 bus:

    * **source notes** (`kind: source`, `src: SRC-<id>`) — DERIVED FROM `touches`
      in the freshly promoted `sources.yaml`, not from the proposal's note list.
      `touches` is the dispatch authority, so editing it at the confirm gate is
      the sanctioned veto (M6 "Veto semantics"); the proposal only supplies the
      "what's new" WORDING, keyed by (slug, src), and unmatched wording is
      reported and dropped rather than written. One note per ALREADY-DRAFTED
      procedure an outstanding source touches — guard 2 then dispatches
      `consult-drafter` in `mode: update` for exactly those slugs.
    * **retirement / rename / consolidation notes** — passed through from the
      proposal (they have no `touches` analogue). A retirement proposal
      enumerates the inbound `[[slug]]` references and carries one note per
      citing procedure, so the drafters clean the references up; no fragment is
      ever auto-deleted (audit F8's workflow half).

    Dedupe is on the SRC- id: a slug already recorded in the source's `consumed`
    list (sources.py's durable per-slug record) is never re-notified, so running
    the same source twice cannot re-dispatch a drafter that already absorbed it.
    """
    wording = {(n["slug"], n.get("src")): n["note"]
               for n in proposal_notes if n["kind"] == "source"}
    used: set[tuple] = set()
    report = {"written": [], "skeleton": [], "deduped": [], "dropped": []}

    sfile = area / "_reference" / "sources.yaml"
    data = _load_yaml(sfile) if sfile.is_file() else {}
    for entry in (data.get("sources") or []):
        if not isinstance(entry, dict) or entry.get("state") == "processed":
            continue
        sid = str(entry.get("id") or "").strip()
        if not sid:
            continue
        touches = entry.get("touches") or []
        if isinstance(touches, str):
            touches = [touches]
        consumed = set(str(s) for s in (entry.get("consumed") or []))
        for slug in [str(s) for s in touches]:
            rel = slug_files.get(slug)
            if rel is None:
                continue          # not a procedure here: reconcile/M22 reports it
            if slug in consumed:
                report["deduped"].append("%s→%s" % (sid, slug))
                continue
            if not _is_drafted(area, rel):
                report["skeleton"].append("%s→%s" % (sid, slug))
                continue
            note = wording.get((slug, sid))
            used.add((slug, sid))
            item = {"kind": "source", "src": sid,
                    "note": note or default_source_note(sid, str(entry.get("file") or ""))}
            if notes_util.append_items(area, slug, [item]):
                report["written"].append("%s→%s" % (sid, slug))

    for n in proposal_notes:
        if n["kind"] == "source":
            if (n["slug"], n.get("src")) not in used:
                # Wording for a (slug, src) pair `touches` does not claim: the
                # human edited touches at the gate, or the agent disagreed with
                # its own tags. touches wins — that is what makes it the veto.
                report["dropped"].append("%s→%s" % (n.get("src"), n["slug"]))
            continue
        rel = slug_files.get(n["slug"])
        if rel is None or not _is_drafted(area, rel):
            report["skeleton"].append("%s→%s" % (n["kind"], n["slug"]))
            continue
        item = {k: v for k, v in n.items() if k != "slug"}
        if notes_util.append_items(area, n["slug"], [item]):
            report["written"].append("%s→%s" % (n["kind"], n["slug"]))
    return report


# --------------------------------------------------------------------------- #
# manifest
# --------------------------------------------------------------------------- #

def build_manifest(area: Path, l1: str, title: str, subtitle: str,
                   procedures: list[dict], l2_order: list[str],
                   proc_orders: dict[str, int], profile=None) -> dict:
    """Build the v1 manifest. `profile` (M14) decides WHICH derived components
    are listed; `None` means today's default set."""
    components: list[dict] = []

    for sf in STATIC_FILES:
        components.append({
            "file": sf["file"], "role": "static",
            "heading": sf["heading"], "order": sf["order"],
        })

    known = {p["slug"] for p in procedures}
    for p in procedures:
        slug = p["slug"]
        comp = {
            "file": f"10_{slug}.md", "role": "procedure",
            "slug": slug, "heading": p["title"], "l2": p["l2"],
            "order": proc_orders[slug],
        }
        # M11 ordering hints: validated here (mechanics), decided by taxonomy
        # (judgment). Unknown or self references are dropped with a warning —
        # the manifest only ever carries hints the advisor can act on.
        upstream = list(dict.fromkeys(str(u) for u in (p.get("upstream") or []) if u))
        valid = [u for u in upstream if u in known and u != slug]
        for bad in [u for u in upstream if u not in valid]:
            print(f"  WARNING: {slug}: dropping upstream hint '{bad}' "
                  "(unknown slug or self-reference)")
        if valid:
            comp["upstream"] = valid
        components.append(comp)

    for d in profile_derived_files(profile):
        components.append({
            "file": d["file"], "role": "derived", "derived_kind": d["kind"],
            "writer": d["writer"], "heading": d["heading"], "order": d["order"],
        })

    components.sort(key=lambda c: (c["order"], c["file"]))

    return {
        "schema": "consult-mvp-manifest/v1",
        "area": area.name,
        "l1": l1,
        "l2_order": l2_order,
        "title": title,
        "subtitle": subtitle,
        "components": components,
    }


# --------------------------------------------------------------------------- #
# main confirm flow
# --------------------------------------------------------------------------- #

def resolve_l1(area: Path, arg_l1: str | None) -> str:
    if arg_l1:
        return arg_l1
    manifest_path = area / "manifest.json"
    if manifest_path.is_file():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8")).get("l1") or ""
        except Exception:
            pass
    meta = _load_yaml(area / "_reference" / ".proposed" / "area.yaml")
    if meta.get("l1"):
        return meta["l1"]
    raise SystemExit(
        "error: could not determine L1. Pass --l1 <slug> "
        "(or set l1 in _reference/.proposed/area.yaml)."
    )


def _manifest_procedures(existing_manifest: dict) -> list[dict]:
    """Recover the procedure list already committed to the live manifest.

    The manifest is the authoritative record of everything in scope; a proposal
    round only ever ADDS to it (or re-emits entries to update them). Procedures
    the delta did not re-emit must survive the rebuild.
    """
    procs: list[dict] = []
    for c in existing_manifest.get("components", []) or []:
        if c.get("role") != "procedure" or not c.get("slug"):
            continue
        p = {"slug": c["slug"], "title": c.get("heading") or c["slug"],
             "l2": c.get("l2")}
        if c.get("upstream"):
            p["upstream"] = list(c["upstream"])
        procs.append(p)
    return procs


def confirm(area: Path, l1_arg: str | None, taxonomy: Path,
            title_arg: str | None, subtitle_arg: str | None) -> int:
    proposed = area / "_reference" / ".proposed"
    if not proposed.is_dir():
        raise SystemExit(f"error: no proposals at {proposed} (run consult-taxonomy first)")

    proposed_procs = _load_yaml(proposed / "procedures.yaml").get("procedures", []) or []

    # The live manifest is authoritative for what is already in scope: merge the
    # proposal delta INTO it, never rebuild from the delta alone. This also lets
    # an incremental pass whose new sources only touch existing procedures run
    # with an empty (or absent) procedures.yaml — registry merge + source
    # stamping still happen and .proposed/ is still consumed.
    manifest_path = area / "manifest.json"
    existing_manifest = {}
    if manifest_path.is_file():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            existing_manifest = {}
    # Basic proposal sanity: unique kebab slugs, every proc has an l2. Checked
    # on the raw proposal list BEFORE merging (the merge would silently dedupe).
    seen = set()
    for p in proposed_procs:
        slug = p.get("slug")
        if not slug or not p.get("l2") or not p.get("title"):
            raise SystemExit(f"error: procedure entry missing slug/l2/title: {p!r}")
        if slug in seen:
            raise SystemExit(f"error: duplicate procedure slug {slug!r}")
        seen.add(slug)

    procedures = _merge_by_key(_manifest_procedures(existing_manifest), proposed_procs)
    if not procedures:
        raise SystemExit(
            f"error: no procedures in {proposed / 'procedures.yaml'} "
            "and no existing manifest to preserve"
        )

    # M6 notes bus: shape-check `.proposed/notes.yaml` BEFORE anything is
    # promoted, so a malformed proposal leaves the live folder untouched and the
    # human re-confirms after fixing it. Ids are validated against the union of
    # the live registry and the delta (the delta's own sources are not live yet).
    known_src_ids = set()
    for f in (area / "_reference" / "sources.yaml", proposed / "sources.yaml"):
        for e in (_load_yaml(f).get("sources") or []):
            if isinstance(e, dict) and e.get("id"):
                known_src_ids.add(str(e["id"]).strip())
    proposal_notes = validate_proposed_notes(
        load_proposed_notes(area), {p["slug"] for p in procedures}, known_src_ids)

    l1 = resolve_l1(area, l1_arg)

    # M14 enforcement point 1. Resolved BEFORE anything is promoted so a
    # malformed profile (a `body_omit` naming a section that does not exist,
    # `body_omit: [F]` with no controls register) stops the run with the live
    # folder untouched — same discipline as the notes shape-check above.
    profile = client_config.profile(area)

    # 1) Promote (MERGE) the registry, then stamp deterministic byte-work.
    promote_reference(area)
    stamp_sources(area)

    # 2) Compute ordering authorities.
    tax_buckets = load_l1_buckets(taxonomy, l1)
    existing_l2_order = existing_manifest.get("l2_order", []) or []
    existing_orders = {
        c["slug"]: c["order"]
        for c in existing_manifest.get("components", [])
        if c.get("role") == "procedure" and isinstance(c.get("order"), int)
    }

    l2_order = compute_l2_order(procedures, tax_buckets, existing_l2_order)
    proc_orders = assign_procedure_orders(procedures, l2_order, existing_orders)

    # 3) Title / subtitle (arg > existing manifest > derived default).
    title = (title_arg or existing_manifest.get("title")
             or f"{_titleize(area.name)} — Desktop Procedures")
    subtitle = (subtitle_arg if subtitle_arg is not None
                else existing_manifest.get("subtitle", "Current-state desktop procedures"))

    # 4) Build + validate the manifest.
    manifest = build_manifest(area, l1, title, subtitle, procedures, l2_order,
                              proc_orders, profile)
    if doc_model is not None:
        errors = doc_model.validate_manifest(manifest)
        if errors:
            raise SystemExit(
                "error: scaffolded manifest failed validation:\n  - "
                + "\n  - ".join(errors)
            )
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # 5) Write files (idempotent: never overwrite an existing component file).
    created, skipped = [], []

    def _write_if_absent(name: str, content: str):
        fp = area / name
        if fp.exists():
            skipped.append(name)
        else:
            fp.write_text(content, encoding="utf-8")
            created.append(name)

    for sf in STATIC_FILES:
        _write_if_absent(sf["file"], render_static(sf["heading"]))
    for p in procedures:
        content = render_skeleton(p["title"], profile.sections)
        # A merged near-duplicate pair carries `variants:` in procedures.yaml.
        # Stamp the coverage into the skeleton so the drafter documents the
        # shared flow once and branches where the variants diverge. HTML
        # comments are stripped at render, so this never reaches Word.
        variants = [str(v) for v in (p.get("variants") or []) if v]
        if variants:
            note = (
                "<!-- scope note: covers variants — " + "; ".join(variants)
                + ". Document the shared flow once; branch at the step(s) "
                  "where the variants diverge. -->"
            )
            content = content.replace(
                "<!-- unfilled -->", "<!-- unfilled -->\n\n" + note, 1
            )
        _write_if_absent(f"10_{p['slug']}.md", content)
    for d in profile_derived_files(profile):
        _write_if_absent(d["file"], render_derived(d["kind"], d["writer"], d["heading"]))

    # 5b) Re-dispatch rides the notes queue (M6/F7). Written AFTER the skeletons
    #     exist, so "already drafted" is asked of the final folder state: a slug
    #     created by this very pass carries the `unfilled` sentinel and takes the
    #     `fill` path (with its whole tagged source list) instead of a note.
    notes_report = write_promoted_notes(
        area,
        {c["slug"]: c["file"] for c in manifest["components"]
         if c.get("role") == "procedure" and c.get("slug")},
        proposal_notes)

    # 6) Consume the proposal set. Everything in .proposed/ has now been promoted
    #    (registry) or baked into the manifest (procedures/new_buckets), so the
    #    directory must go — otherwise the advisor's guard 1 keeps returning
    #    `confirm` and the build wedges at the first gate. This is the single
    #    stage that clears it; do it only after a fully successful scaffold.
    shutil.rmtree(proposed, ignore_errors=True)

    print(f"scaffolded {area}")
    print(f"  {profile.report_line()}")
    print(f"  l1={l1}  l2_order={l2_order}")
    print(f"  procedures={len(procedures)} (proposal delta={len(proposed_procs)})  "
          f"created={len(created)}  skipped(existing)={len(skipped)}")
    if created:
        print("  created: " + ", ".join(created))
    if notes_report["written"]:
        print("  notes (→ apply_review): " + ", ".join(notes_report["written"]))
    for key, label in (("skeleton", "no note needed (skeleton fills instead)"),
                       ("deduped", "already consumed for that source"),
                       ("dropped", "note wording dropped (not in `touches`)")):
        if notes_report[key]:
            print(f"  {label}: " + ", ".join(notes_report[key]))
    return 0


def sync_profile(area: Path) -> int:
    """Reconcile the live manifest's DERIVED components with the resolved
    profile — enforcement point 1 re-run, WITHOUT a `.proposed/` round.

    The confirm gate is the manifest's only writer and it refuses to run
    without proposals, so a profile whose `derived:` set changed AFTER
    scaffolding had no supported path back into the manifest. The case that
    matters is adding `appendix-controls` so `body_omit: [controls]` has a
    destination — without the component, render (which builds from the
    manifest, not the profile) would drop every control, which is why it
    fails loudly and names this command.

    Only the derived set is touched: static and procedure components are
    preserved byte-for-byte, and a derived entry whose kind the profile still
    wants keeps its existing (possibly hand-edited) fields. An added kind
    takes its DERIVED_FILES spec and gets its stub file iff absent; a removed
    kind loses only its manifest entry — the file stays on disk (scaffold
    never deletes) and the next render simply omits the view, exactly as a
    fresh confirm would. Idempotent: an in-sync manifest is left unwritten.
    """
    manifest_path = area / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(
            f"error: no manifest at {manifest_path} — sync-profile reconciles "
            "an ALREADY-SCAFFOLDED area with a changed profile; a fresh area "
            "goes through the confirm gate (--confirm)"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    profile = client_config.profile(area)

    wanted = profile_derived_files(profile)
    wanted_kinds = {d["kind"] for d in wanted}
    existing = {c.get("derived_kind"): c for c in manifest.get("components", [])
                if c.get("role") == "derived"}

    components = [c for c in manifest.get("components", [])
                  if c.get("role") != "derived"]
    added, created = [], []
    for d in wanted:
        if d["kind"] in existing:
            components.append(existing[d["kind"]])
            continue
        components.append({"file": d["file"], "role": "derived",
                           "derived_kind": d["kind"], "writer": d["writer"],
                           "heading": d["heading"], "order": d["order"]})
        added.append(d["kind"])
        fp = area / d["file"]
        if not fp.exists():
            fp.write_text(render_derived(d["kind"], d["writer"], d["heading"]),
                          encoding="utf-8")
            created.append(d["file"])
    removed = sorted(k for k in existing if k not in wanted_kinds)
    components.sort(key=lambda c: (c["order"], c["file"]))
    manifest["components"] = components

    if doc_model is not None:
        errors = doc_model.validate_manifest(manifest)
        if errors:
            raise SystemExit(
                "error: synced manifest failed validation:\n  - "
                + "\n  - ".join(errors)
            )

    print(f"sync-profile {area}")
    print(f"  {profile.report_line()}")
    if not added and not removed:
        print("  manifest already matches the profile — nothing to do")
        return 0
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if added:
        print("  derived added: " + ", ".join(added))
    if created:
        print("  created: " + ", ".join(created))
    if removed:
        print("  derived removed (files kept on disk): " + ", ".join(removed))
    print("  re-run aggregate before the next render so new registers fill")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M0 confirm-gate scaffolder")
    ap.add_argument("--confirm", action="store_true",
                    help="promote _reference/.proposed/ and scaffold the area")
    ap.add_argument("--sync-profile", action="store_true",
                    help="reconcile the live manifest's derived components with "
                         "the resolved profile (no .proposed/ round needed)")
    ap.add_argument("--area", required=True, help="path to the area folder")
    ap.add_argument("--l1", default=None, help="L1 taxonomy slug (else read from manifest/area.yaml)")
    ap.add_argument("--taxonomy", default=str(DEFAULT_TAXONOMY), help="path to the reference taxonomy")
    ap.add_argument("--title", default=None, help="document title override")
    ap.add_argument("--subtitle", default=None, help="document subtitle override")
    args = ap.parse_args(argv)

    if args.confirm and args.sync_profile:
        raise SystemExit("error: pass --confirm or --sync-profile, not both "
                         "(a confirm already rebuilds the derived set from "
                         "the profile)")
    if not args.confirm and not args.sync_profile:
        raise SystemExit(
            "refusing to run without --confirm: this is the human confirm gate. "
            "Review _reference/.proposed/ first, then re-run with --confirm."
        )

    area = Path(args.area).resolve()
    if not area.is_dir():
        raise SystemExit(f"error: area folder not found: {area}")
    if args.sync_profile:
        return sync_profile(area)
    return confirm(area, args.l1, Path(args.taxonomy), args.title, args.subtitle)


if __name__ == "__main__":
    sys.exit(main())
