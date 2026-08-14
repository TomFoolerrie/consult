#!/usr/bin/env python3
"""ledger.py — THE engagement-root source ledger (M34).

This module OWNS `<root>/_sources/` and everything in it:

    <root>/_sources/
        sources.yaml    THE ledger — engagement-global SRC ids (one minter)
        new/            source files someone still owes a read
        processed/      fully-consumed source files
        parked/         staged files declined with a reason
        parked.yaml     the durable park reasons (one line per parked file)

v1 stores sources per area (`components/<area>/_sources/` plus its own
`_reference/sources.yaml`, `scripts/sources.py`); v2 stores them once, at the
engagement root, and areas hold only consumption records. The entry shape is
v1's, generalized one scope up: `id`, `file`, `hash`, plus the NAMESPACED maps
`touches: {area: [slug, ...]}` and `consumed: {area: [slug, ...]}`.

DOCTRINE — **file position is display; the ledger is truth.** Every
outstanding-ness answer (is this source unregistered? does this area still owe
it a read? may it move to processed/?) is a ledger query. No code path here may
answer such a question by listing a folder: `new/` vs `processed/` is a
self-describing convenience for humans, downstream of the ledger, never an
input to it. The one legitimate folder read is the loud-until-empty diff in
`status()` — and even there the folder supplies only candidate NAMES; whether a
name is unregistered is decided by the ledger.

Fail loud: every defect raises `LedgerError` with a message naming the file,
slug or area at fault (F14, one scope up — a typo'd `touches` slug makes a
source permanently unretirable, so it is refused at registration).

Python 3, stdlib + pyyaml.
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import os
import shutil
import sys
from datetime import date
from pathlib import Path

import yaml

# v1's per-area module is the discipline this module generalizes; its helpers are
# imported where they genuinely fit (content hashing, the slug-list coercion)
# rather than reimplemented. sources.py itself is untouched by M34.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from doc_model import ManifestError, load_manifest, procedures  # noqa: E402
from notes_util import NOTES_SUFFIX, NotesError, load_items_from  # noqa: E402
from sources import _hash_file, _slug_list  # noqa: E402

LEDGER_DIRNAME = "_sources"
LEDGER_FILENAME = "sources.yaml"
PARKED_FILENAME = "parked.yaml"
ID_PREFIX = "SRC-"
ROUTE_SIDECAR_SUFFIX = ".route.md"      # M25 metadata, never a source


class LedgerError(Exception):
    """A fail-loud defect in `<root>/_sources/` (never a warning)."""


# --------------------------------------------------------------------------- #
# Paths and I/O
# --------------------------------------------------------------------------- #

def _root(root) -> Path:
    return Path(root)


def sources_dir(root) -> Path:
    return _root(root) / LEDGER_DIRNAME


def ledger_path(root) -> Path:
    return sources_dir(root) / LEDGER_FILENAME


def new_dir(root) -> Path:
    return sources_dir(root) / "new"


def processed_dir(root) -> Path:
    return sources_dir(root) / "processed"


def parked_dir(root) -> Path:
    return sources_dir(root) / "parked"


def _parked_path(root) -> Path:
    return sources_dir(root) / PARKED_FILENAME


def _read_yaml_mapping(path: Path, label: str) -> dict:
    """Load a YAML mapping, or {} when absent. A malformed file is a DEFECT:
    this module is a writer, and guessing at a half-written ledger is how ids
    get minted twice."""
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError) as exc:
        raise LedgerError(f"{path}: {label} is unreadable: {exc}") from exc
    if not isinstance(data, dict):
        raise LedgerError(f"{path}: {label} must be a YAML mapping")
    return data


def _load_ledger(root) -> dict:
    data = _read_yaml_mapping(ledger_path(root), "ledger")
    entries = data.get("sources")
    if entries is None:
        entries = []
    if not isinstance(entries, list):
        raise LedgerError(f"{ledger_path(root)}: `sources` must be a list")
    data["sources"] = [e for e in entries if isinstance(e, dict)]
    return data


def _dump_ledger(root, data: dict) -> None:
    sources_dir(root).mkdir(parents=True, exist_ok=True)
    with open(ledger_path(root), "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def entries(root) -> list[dict]:
    """The ledger's entries, in registration order (a read-only view)."""
    return list(_load_ledger(root)["sources"])


# --------------------------------------------------------------------------- #
# Namespaced maps (the v1 `touches`/`consumed` lists, one scope up)
# --------------------------------------------------------------------------- #

def _area_map(value, label: str, sid: str) -> dict[str, list[str]]:
    """Coerce a `{area: [slugs]}` map, order-preserving."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise LedgerError(
            f"{sid}: `{label}` must be a map of area -> [procedure slugs], "
            f"got {type(value).__name__}"
        )
    return {str(area): _slug_list(slugs) for area, slugs in value.items()}


def _merge_area_map(base: dict[str, list[str]],
                    incoming: dict[str, list[str]]) -> dict[str, list[str]]:
    """Union each area's slug list, ORDER-PRESERVING (existing slugs keep their
    position; new ones append). Consumption/tagging accumulates and never
    resets, so a merge may only ever grow a map."""
    out = {area: list(slugs) for area, slugs in base.items()}
    for area, slugs in incoming.items():
        current = out.setdefault(area, [])
        for slug in slugs:
            if slug not in current:
                current.append(slug)
    return out


# --------------------------------------------------------------------------- #
# touches validation — the F14 typo trap, per area slice (M22 check 2)
# --------------------------------------------------------------------------- #

def area_procedure_slugs(root, area: str) -> set[str] | None:
    """Procedure slugs from `components/<area>/manifest.json`, or None when the
    area has no readable manifest.

    None is v1's documented BOUNDARY: taxonomy tags sources before scaffold
    writes the manifest, so for that window there is no authority to validate
    against and the check must no-op rather than reject every tag. An area
    FOLDER that does not exist at all is a different thing — a tag naming a
    non-area — and is refused by the caller."""
    area_path = _root(root) / "components" / area
    if not (area_path / "manifest.json").is_file():
        return None
    try:
        manifest = load_manifest(area_path)
    except ManifestError:
        return None
    if not isinstance(manifest, dict):
        return None
    return {c.get("slug") for c in procedures(manifest)
            if isinstance(c.get("slug"), str)}


def _validate_touches(root, filename: str,
                      touches: dict[str, list[str]]) -> None:
    """`touches[area] ⊆ that area's manifest procedure slugs`.

    F14, one scope up: one typo'd slug makes a source permanently unretirable
    (its touches map never becomes a subset of consumed), so it is refused HERE,
    the first time anything writes it, with the offending slug named."""
    for area, slugs in touches.items():
        area_path = _root(root) / "components" / area
        if not area_path.is_dir():
            raise LedgerError(
                f"{filename}: touches unknown area {area!r} "
                f"(no components/{area}/ in this engagement)"
            )
        known = area_procedure_slugs(root, area)
        if known is None:
            continue                    # no authority yet — v1's boundary
        for slug in slugs:
            if slug not in known:
                raise LedgerError(
                    f"{filename}: touches {slug!r} in area {area!r}, which is "
                    f"not a manifest procedure slug (unretirable source — F14)"
                )


# --------------------------------------------------------------------------- #
# Minting + registration
# --------------------------------------------------------------------------- #

def _mint(existing: list[dict]) -> str:
    """The next engagement-global SRC id. ONE minter, so collisions are
    impossible by construction."""
    highest = 0
    for entry in existing:
        sid = str(entry.get("id") or "")
        if sid.startswith(ID_PREFIX):
            tail = sid[len(ID_PREFIX):]
            if tail.isdigit():
                highest = max(highest, int(tail))
    return f"{ID_PREFIX}{highest + 1:03d}"


def register(root, filename: str, touches: dict) -> str:
    """Register `_sources/new/<filename>` and tag what it informs.

    `touches` is `{area: [procedure slugs]}`. Returns the SRC id — minted
    engagement-globally in registration order, or the EXISTING id when these
    exact bytes are already registered (idempotence by content hash, kept from
    M25): a re-drop MERGES the new touches map into the existing entry and
    never creates a second entry.

    The file is not moved: registration is tagging. Position changes only when
    the whole touches map has been consumed (WP-B's move rule).
    """
    path = new_dir(root) / filename
    if not path.is_file():
        raise LedgerError(f"{path}: no such file in _sources/new/ to register")

    touches_map = _area_map(touches, "touches", filename)
    _validate_touches(root, filename, touches_map)

    digest = _hash_file(str(path))
    if not digest:
        raise LedgerError(f"{path}: could not read the file to hash it")

    data = _load_ledger(root)
    ledger_entries = data["sources"]

    for entry in ledger_entries:
        if str(entry.get("hash") or "") == digest:
            # Same bytes: one source, one id, N tags.
            sid = str(entry.get("id") or "")
            merged = _merge_area_map(
                _area_map(entry.get("touches"), "touches", sid), touches_map)
            entry["touches"] = merged
            entry.setdefault("consumed", {})
            _dump_ledger(root, data)
            return sid

    sid = _mint(ledger_entries)
    ledger_entries.append({
        "id": sid,
        "file": f"{LEDGER_DIRNAME}/new/{filename}",
        "hash": digest,
        "registered": date.today().isoformat(),
        "touches": touches_map,
        "consumed": {},
    })
    _dump_ledger(root, data)
    return sid


# --------------------------------------------------------------------------- #
# Outstanding-ness — a ledger query, never a folder listing
# --------------------------------------------------------------------------- #

def outstanding(root, area: str) -> dict[str, list[str]]:
    """`{src_id: [slugs this area still owes a read]}` for one area.

    The per-area question "is this source outstanding FOR ME?" is exactly
    `touches[area] ⊄ consumed[area]` — derived here so no consumer is ever
    tempted to answer it from file position. Entries with nothing left for the
    area are absent (so `{}` means "this area is square with the ledger").

    (Read-only, and needed by registration's idempotence contract; the WRITER
    side of consumption — `credit` and the move rule — is WP-B, below.)
    """
    out: dict[str, list[str]] = {}
    for entry in _load_ledger(root)["sources"]:
        sid = str(entry.get("id") or "")
        tagged = _area_map(entry.get("touches"), "touches", sid).get(area, [])
        done = set(_area_map(entry.get("consumed"), "consumed", sid).get(area, []))
        remaining = [s for s in tagged if s not in done]
        if remaining:
            out[sid] = remaining
    return out


# --------------------------------------------------------------------------- #
# park + status — the loud-until-empty block, as a ledger/folder diff
# --------------------------------------------------------------------------- #

def _load_parked(root) -> dict:
    data = _read_yaml_mapping(_parked_path(root), "park record")
    parked = data.get("parked")
    if parked is None:
        parked = {}
    if not isinstance(parked, dict):
        raise LedgerError(f"{_parked_path(root)}: `parked` must be a mapping "
                          f"of filename -> reason")
    data["parked"] = {str(k): str(v) for k, v in parked.items()}
    return data


def park(root, filename: str, reason: str) -> None:
    """Decline a staged file: `_sources/new/` → `_sources/parked/`, with the
    reason recorded durably (`_sources/parked.yaml`) so `status` can say WHY a
    file was declined months later. A parked file is never registered — it is
    not evidence."""
    if not str(reason or "").strip():
        raise LedgerError(f"{filename}: park requires a reason "
                          f"(why this file is not evidence)")
    src = new_dir(root) / filename
    if not src.is_file():
        raise LedgerError(f"{src}: no such file in _sources/new/ to park")

    parked_dir(root).mkdir(parents=True, exist_ok=True)
    dest = parked_dir(root) / filename
    shutil.move(str(src), str(dest))

    data = _load_parked(root)
    data["parked"][filename] = str(reason)
    sources_dir(root).mkdir(parents=True, exist_ok=True)
    with open(_parked_path(root), "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def _new_file_names(root) -> list[str]:
    """Names of the real files staged in `_sources/new/` — CANDIDATES only.

    The folder supplies names; the ledger decides what they mean (see the module
    doctrine). Dotfiles and M25 route sidecars are metadata, not sources."""
    root_dir = new_dir(root)
    if not root_dir.is_dir():
        return []
    out = []
    for base, _dirs, names in os.walk(root_dir):
        for name in names:
            if name.startswith(".") or name.endswith(ROUTE_SIDECAR_SUFFIX):
                continue
            rel = os.path.relpath(os.path.join(base, name), root_dir)
            out.append(rel.replace(os.sep, "/"))
    return sorted(out)


def status(root) -> dict:
    """The loud-until-empty diff:

        {"unregistered": [names staged in new/ with NO ledger entry],
         "parked":       [(name, reason), ...]}

    v1 scanned the `intake/` folder; v2 diffs the staging folder against the
    ledger — a file in `new/` WITH an entry is registered work in progress, not
    a to-do, and never appears here. Both lists sorted; both empty means the
    block is quiet.
    """
    known_hashes = set()
    known_names = set()
    for entry in _load_ledger(root)["sources"]:
        digest = str(entry.get("hash") or "")
        if digest:
            known_hashes.add(digest)
        recorded = str(entry.get("file") or "").replace(os.sep, "/")
        if recorded:
            known_names.add(os.path.basename(recorded))

    unregistered = []
    for name in _new_file_names(root):
        if os.path.basename(name) in known_names:
            continue
        if _hash_file(str(new_dir(root) / name)) in known_hashes:
            continue                    # same bytes under a new name: known
        unregistered.append(name)

    parked = sorted(_load_parked(root)["parked"].items())
    return {"unregistered": sorted(unregistered), "parked": parked}


# --------------------------------------------------------------------------- #
# WP-B LANDS HERE — consumption + the move rule
#   credit(root, area, filled=(), updated=()) -> files_moved: int
#     v1 evidence rules verbatim, one scope up (sources.note_src_ids: `filled`
#     credits unconditionally, `updated` requires an archived `kind: source`
#     note at components/<area>/_review/processed/<slug>.notes.yaml naming the
#     id, non-source notes credit nothing), consumption accumulating into
#     entry["consumed"][area] and NEVER resetting, and the move rule at
#     engagement scope: a file goes new/ -> processed/ only when its ENTIRE
#     touches map — all areas — is covered by consumed.
#   `outstanding` above is the read side and needs no change.
# --------------------------------------------------------------------------- #

def _area_note_src_ids(root, area: str, slug: str) -> set[str]:
    """The SRC ids named by `kind: source` items in a slug's CONSUMED notes.

    `sources.note_src_ids` one scope up, and deliberately the ARCHIVE only:
    `components/<area>/_review/processed/<slug>.notes.yaml` exists because an
    apply_review batch succeeded, so it is the durable evidence that a drafter
    read this source for this slug. Items of any other kind contribute nothing —
    a reviewer comment that merely mentions an id must never retire a source.
    """
    path = (_root(root) / "components" / area / "_review" / "processed"
            / f"{slug}{NOTES_SUFFIX}")
    out: set[str] = set()
    try:
        items = load_items_from(path)
    except NotesError as exc:
        # A malformed note on the bus is a defect, not a warning: nothing moves.
        raise LedgerError(f"{path}: unreadable review notes: {exc}") from exc
    for item in items:
        if item.get("kind") == "source":
            sid = str(item.get("src") or "").strip()
            if sid:
                out.add(sid)
    return out


def _fully_consumed(touches: dict[str, list[str]],
                    consumed: dict[str, list[str]]) -> bool:
    """THE MOVE RULE, at engagement scope: the ENTIRE touches map — every area,
    not merely the one just credited — is covered by consumed.

    An empty touches map never satisfies it: a source informing no procedure has
    nothing to "fully consume", so it stays outstanding for a human (v1's rule).
    """
    if not any(touches.values()):
        return False
    for area, slugs in touches.items():
        done = set(consumed.get(area, []))
        if not set(slugs) <= done:
            return False
    return True


def credit(root, area: str, filled=(), updated=()) -> int:
    """Record what `area` consumed, and retire whatever is now fully read.

    v1's evidence rules verbatim, one scope up (see `sources.mark_processed`):

    * `filled` slugs credit UNCONDITIONALLY — a first-draft fill that succeeded
      is itself the evidence that the source was read for that procedure.
    * `updated` slugs credit ONLY with evidence: an archived `kind: source` note
      at `components/<area>/_review/processed/<slug>.notes.yaml` whose `src`
      names THAT entry's id. Non-source notes credit nothing.
    * Consumption ACCUMULATES into `entry["consumed"][area]` and NEVER resets —
      a later pass (even an empty one) may only ever grow the map, because
      un-consuming a source would silently re-dispatch reading already done.

    Returns the number of files this call moved `_sources/new/` →
    `_sources/processed/` — which happens, per the move rule, only when the
    whole touches map across ALL areas is covered (file position is display;
    the ledger is truth).
    """
    filled_set = {s for s in _slug_list(filled)}
    updated_set = {s for s in _slug_list(updated)}

    data = _load_ledger(root)                   # unreadable ledger raises here
    ledger_entries = data["sources"]

    if ledger_entries and not any(
            area in _area_map(e.get("touches"), "touches",
                              str(e.get("id") or ""))
            for e in ledger_entries):
        raise LedgerError(
            f"credit for area {area!r}, which no ledger entry touches — "
            f"a credit that can never land is a defect, not a no-op"
        )

    # Pass 1 — READ ONLY. Every note read happens before anything moves, so a
    # malformed note leaves the ledger exactly as it was.
    evidence: dict[str, set[str]] = {}

    def credits(slug: str) -> set[str]:
        if slug not in evidence:
            evidence[slug] = _area_note_src_ids(root, area, slug)
        return evidence[slug]

    plan: list[tuple[dict, dict, dict]] = []
    for entry in ledger_entries:
        sid = str(entry.get("id") or "").strip()
        touches = _area_map(entry.get("touches"), "touches", sid)
        consumed = _area_map(entry.get("consumed"), "consumed", sid)
        gained: list[str] = []
        already = set(consumed.get(area, []))
        for slug in touches.get(area, []):
            if slug in already:
                continue
            if slug in filled_set:
                gained.append(slug)                 # fill: unconditional
            elif slug in updated_set and sid and sid in credits(slug):
                gained.append(slug)                 # update: note evidence
        if gained:
            consumed = _merge_area_map(consumed, {area: gained})
        plan.append((entry, touches, consumed))

    # Pass 2 — MUTATE: persist the accumulated credit, then retire what the move
    # rule allows.
    moved = 0
    for entry, touches, consumed in plan:
        entry["consumed"] = consumed
        if entry.get("state") == "processed":
            continue
        if not _fully_consumed(touches, consumed):
            continue
        name = os.path.basename(str(entry.get("file") or "").replace(os.sep, "/"))
        src = new_dir(root) / name
        if src.is_file():
            processed_dir(root).mkdir(parents=True, exist_ok=True)
            dest = processed_dir(root) / name
            shutil.move(str(src), str(dest))
            # M25: the intake pointer sidecar retires with its source, so a lone
            # sidecar can never keep _sources/new/ "non-empty".
            side = Path(str(src) + ROUTE_SIDECAR_SUFFIX)
            if side.is_file():
                shutil.move(str(side), str(dest) + ROUTE_SIDECAR_SUFFIX)
            moved += 1
        entry["state"] = "processed"
        entry["file"] = f"{LEDGER_DIRNAME}/processed/{name}"

    _dump_ledger(root, data)
    return moved


# --------------------------------------------------------------------------- #
# WP-C LANDS HERE — the dual-layout adapter + centralize
#   entries_for_area(area_path) / outstanding_for_area(area_path): a v1
#     per-area `_reference/sources.yaml` read through this API, ids presented
#     as "<area-name>/SRC-nnn". READ-ONLY — the adapter never writes.
#   centralize(root) -> {"<area>/SRC-nnn": "SRC-mmm"}: fold v1 per-area
#     registries into this ledger (dedupe by hash, remint, merge the
#     touches/consumed maps per area, place each file in new/ or processed/ by
#     the DERIVED state, persist the remap table under _sources/).
# --------------------------------------------------------------------------- #
