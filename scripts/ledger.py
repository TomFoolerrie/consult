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
