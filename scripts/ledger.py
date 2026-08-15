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


def _by_id(ledger_entries: list[dict], src_id: str) -> dict:
    sid = str(src_id or "").strip()
    for entry in ledger_entries:
        if str(entry.get("id") or "").strip() == sid:
            return entry
    raise LedgerError(f"{sid!r}: no such entry in the ledger")


def retag(root, src_id: str, area: str, slugs) -> list[str]:
    """REPLACE one entry's `touches[area]` slice with `slugs` (M34 confirm gate).

    The taxonomy pass may re-tag a source it already registered: in v1 that was a
    `.proposed/sources.yaml` merge into the area registry, and `touches` is the
    dispatch authority, so editing it at the CONFIRM GATE is the sanctioned M6
    veto. Hence REPLACE, not merge: a slug the human deleted at the gate must
    actually stop dispatching a drafter, which a union could never express.

    Only THIS area's slice moves — other areas' tags are untouched, and `slugs`
    is validated against `components/<area>/manifest.json` exactly as
    `register` validates (F14: a typo'd slug makes a source unretirable).

    `consumed` is deliberately NOT pruned when a slug leaves `touches`: dropping
    consumption records is the parked WP-B decision (touches-shrink pruning), and
    a stale consumed slug costs nothing (it can only ever suppress a re-read of
    something already read), while erasing one silently re-dispatches work.

    Returns the area's new slice.
    """
    wanted = _slug_list(slugs)
    data = _load_ledger(root)
    entry = _by_id(data["sources"], src_id)
    sid = str(entry.get("id") or "")
    _validate_touches(root, os.path.basename(str(entry.get("file") or "")) or sid,
                      {area: wanted})
    touches = _area_map(entry.get("touches"), "touches", sid)
    touches[area] = wanted
    entry["touches"] = touches
    entry.setdefault("consumed", {})
    _dump_ledger(root, data)
    return list(wanted)


def annotate(root, src_id: str, note: str) -> str:
    """Fold `note` into an entry's `note:` field, idempotently.

    The v1 entry shape carries free prose (`note:`) that reaches the drafter's
    brief; centrally there is nowhere else for M25's per-area relevance pointer
    or adopt's provenance sentence to live, so intake writes it here instead of
    the sidecar/registry route. Appending the SAME text twice is a no-op (a
    re-drop must not grow the note), matching `scaffold.stamp_sources`' fold.
    Returns the resulting note.
    """
    text = str(note or "").strip()
    data = _load_ledger(root)
    entry = _by_id(data["sources"], src_id)
    current = str(entry.get("note") or "").strip()
    if not text or text in current:
        return current
    entry["note"] = (current + " | " if current else "") + text
    _dump_ledger(root, data)
    return str(entry["note"])


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
# assess — the guard-5 question, at engagement scope (read-only)
# --------------------------------------------------------------------------- #

def _staged_entry_index(ledger_entries: list[dict]) -> tuple[dict, dict]:
    """`(by recorded path, by unambiguous basename)` — v1's match, one scope up.

    A recorded `file` can be stale (it still says `new/` after a move, or vice
    versa), so the basename is a fallback — but only when it names exactly one
    entry, because a guess between two entries could credit the wrong bytes."""
    by_rel: dict[str, dict] = {}
    base_count: dict[str, int] = {}
    for entry in ledger_entries:
        rel = str(entry.get("file") or "").replace(os.sep, "/").lstrip("./")
        if not rel:
            continue
        by_rel.setdefault(rel, entry)
        base = os.path.basename(rel)
        base_count[base] = base_count.get(base, 0) + 1
    by_base: dict[str, dict] = {}
    for entry in ledger_entries:
        rel = str(entry.get("file") or "").replace(os.sep, "/").lstrip("./")
        base = os.path.basename(rel) if rel else ""
        if base and base_count.get(base) == 1:
            by_base.setdefault(base, entry)
    return by_rel, by_base


def assess(root) -> tuple[list[str], list[dict]]:
    """`(unassessed names, assessed entries)` for `_sources/new/` — a pure read.

    Guard 5's question (`sources.assess_new_sources`, one scope up): has the
    taxonomy pass read THESE EXACT BYTES? The ledger answers it, so the rules
    are v1's verbatim —

    * no ledger entry for the staged file -> **unassessed**;
    * an entry with no recorded hash -> **unassessed**, decided WITHOUT hashing
      the file (the common case is a fresh transcript the advisor re-reads on
      every `next` call, and sources can be large binaries);
    * a recorded hash that differs from the file's current bytes ->
      **unassessed** (edited after registration: nobody has read this version);
    * a match -> **assessed**, carrying the entry itself as message material.

    Names are `_sources/new/`-relative and sorted; dotfiles and M25 route
    sidecars are excluded (`_new_file_names` — the folder supplies candidate
    names only). Entries are COPIES, never live ledger references.
    """
    names = _new_file_names(root)
    if not names:
        return [], []

    ledger_entries = _load_ledger(root)["sources"]
    by_rel, by_base = _staged_entry_index(ledger_entries)

    unassessed: list[str] = []
    assessed: list[dict] = []
    for name in names:
        entry = (by_rel.get(f"{LEDGER_DIRNAME}/new/{name}")
                 or by_base.get(os.path.basename(name)))
        recorded = str((entry or {}).get("hash") or "").strip()
        if not recorded:
            unassessed.append(name)
            continue
        if recorded != _hash_file(str(new_dir(root) / name)):
            unassessed.append(name)
            continue
        assessed.append(dict(entry))
    return unassessed, assessed


# --------------------------------------------------------------------------- #
# area_view — the v1-SHAPED slice re-pointed consumers read
# --------------------------------------------------------------------------- #

def area_view(root, area: str) -> list[dict]:
    """The entries touching `area`, in the v1 per-area entry shape.

    `{id, file, hash, note?, touches, consumed, state}` with `touches` and
    `consumed` FLATTENED to this area's slugs — exactly what v1's
    `_reference/sources.yaml` entries looked like, so a consumer that formats
    them (brief's source listing, scaffold's promoted notes) needs no shape
    change and its output stays byte-shaped.

    `state` is DERIVED, never copied: `"processed"` only when the ENTIRE
    touches map — every area — is covered (the move rule, `_fully_consumed`).
    An area that has finished its own slugs while another area still owes a read
    must not see the source as retired. Ledger order; copies, so a caller
    mutating what it got back cannot reach into the ledger.
    """
    out: list[dict] = []
    for entry in _load_ledger(root)["sources"]:
        sid = str(entry.get("id") or "")
        touches = _area_map(entry.get("touches"), "touches", sid)
        if area not in touches:
            continue
        consumed = _area_map(entry.get("consumed"), "consumed", sid)
        view = {
            "id": sid,
            "file": str(entry.get("file") or ""),
            "hash": str(entry.get("hash") or ""),
            "touches": list(touches.get(area, [])),
            "consumed": list(consumed.get(area, [])),
            "state": "processed" if _fully_consumed(touches, consumed) else "new",
        }
        note = entry.get("note")
        if note:
            view["note"] = note
        out.append(view)
    return out


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

REMAP_FILENAME = "remap.yaml"        # <root>/_sources/remap.yaml: the migration
                                     # record {"<area>/SRC-nnn": "SRC-mmm"},
                                     # what register-provenance strings written
                                     # under the v1 layout are rewritten through
V1_REGISTRY_REL = ("_reference", "sources.yaml")


def _remap_path(root) -> Path:
    return sources_dir(root) / REMAP_FILENAME


def _v1_registry_path(area_path) -> Path:
    return Path(area_path).joinpath(*V1_REGISTRY_REL)


def _v1_entries(area_path) -> list[dict]:
    """The raw entries of a v1 per-area registry, in registry order, or [].

    Deliberately the TOLERANT read (`sources._read_sources_tolerant` semantics):
    the adapter is a reader over someone else's layout, so a missing or malformed
    v1 registry reads as "this area registers nothing" rather than exploding a
    caller that only wanted to look."""
    path = _v1_registry_path(area_path)
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (yaml.YAMLError, OSError):
        return []
    if not isinstance(data, dict):
        return []
    return [e for e in (data.get("sources") or []) if isinstance(e, dict)]


def _prefixed(area_name: str, sid: str) -> str:
    """A v1 area-local id presented at engagement scope: `<area>/SRC-nnn`.

    This is the whole reason the adapter exists: `SRC-004` is ambiguous across
    areas (M34 problem 3), so the adapter qualifies it the way v1's register
    provenance did by hand."""
    return f"{area_name}/{sid}"


def entries_for_area(area_path) -> list[dict]:
    """A v1 per-area registry read through this module's API — READ-ONLY.

    `components/<area>/_reference/sources.yaml` entries, in registry order, with
    ids presented as `<area-dir-name>/SRC-nnn` and every other key passed through
    verbatim (v1's `touches`/`consumed` stay area-local LISTS — this adapter
    presents the v1 shape, it does not pretend the entries are namespaced maps;
    `centralize` is what converts shape).

    THE ADAPTER NEVER WRITES. Not the registry, not the area's `_sources/` tree,
    not the root ledger — the p2p fixture is frozen and must read byte-identically
    forever (M36's compatibility gate). Entries are copies, so a caller mutating
    what it got back cannot reach back into the file either.
    """
    area = Path(area_path)
    name = area.name
    out: list[dict] = []
    for entry in _v1_entries(area):
        presented = dict(entry)
        presented["id"] = _prefixed(name, str(entry.get("id") or "").strip())
        out.append(presented)
    return out


def outstanding_for_area(area_path) -> dict[str, list[str]]:
    """`{"<area>/SRC-nnn": [slugs still owed a read]}` for a v1 area.

    v1 semantics exactly — `touches` minus `consumed` per entry, both area-local
    lists — answered from the REGISTRY, never from which `_sources/` subfolder a
    file happens to sit in (file position is display; the ledger is truth, in
    either layout). A fully-consumed area answers `{}`.
    """
    out: dict[str, list[str]] = {}
    for entry in entries_for_area(area_path):
        tagged = _slug_list(entry.get("touches"))
        done = set(_slug_list(entry.get("consumed")))
        remaining = [s for s in tagged if s not in done]
        if remaining:
            out[str(entry["id"])] = remaining
    return out


# --------------------------------------------------------------------------- #
# centralize — the one-time fold of a v1 engagement into this ledger
# --------------------------------------------------------------------------- #

def _v1_area_paths(root) -> list[Path]:
    """`components/<area>/` folders carrying a v1 registry, sorted by area name.

    Sorted because the fold must be DETERMINISTIC: re-running centralize on the
    same engagement has to mint the same ids, or every remap table and provenance
    string ever written from it becomes a lie."""
    components = _root(root) / "components"
    if not components.is_dir():
        return []
    return sorted((p for p in components.iterdir()
                   if p.is_dir() and _v1_registry_path(p).is_file()),
                  key=lambda p: p.name)


def _v1_physical_file(area_path: Path, entry: dict) -> Path | None:
    """The bytes behind a v1 entry: its recorded `file` (relative to the area),
    falling back to `_sources/{new,processed}/<basename>` when the recorded path
    is stale (`sources._source_relpath`'s tolerance, since a v1 registry's `file`
    can lag the last move)."""
    recorded = str(entry.get("file") or "").replace("\\", "/")
    if recorded:
        candidate = area_path / recorded
        if candidate.is_file():
            return candidate
    name = os.path.basename(recorded) if recorded else ""
    if not name:
        return None
    for sub in ("processed", "new", "parked"):
        candidate = area_path / "_sources" / sub / name
        if candidate.is_file():
            return candidate
    return None


def centralize(root) -> dict[str, str]:
    """Fold a v1 engagement's per-area source trees into THIS ledger, once.

    Returns the remap table `{"<area>/SRC-nnn": "SRC-mmm"}` — every v1 area-local
    id (as the adapter presents it) mapped to the central id that now holds those
    bytes. Also persisted to `<root>/_sources/remap.yaml`, because register
    provenance strings written under the v1 layout (`SRC-004 (p2p)`) outlive the
    migration and need a lookup table to be rewritten through.

    What the fold does:

    * **Dedupe by content hash.** The whole point: M25's route verb COPIED a
      cross-area transcript, so the same bytes hold two area-local ids, two
      `touches` sets and two independent lifecycles. Same hash means one source:
      one central entry, one file on disk, N tags.
    * **Merge the maps per area.** Each v1 area-local `touches`/`consumed` LIST
      becomes that area's slice of the namespaced map. Consumption history from
      every area survives intact — nothing is re-dispatched for reading.
    * **Remint centrally**, in a deterministic order: areas in sorted name order,
      and within an area the registry's own order; an id is minted the FIRST time
      a hash is seen, and later copies join that entry. (So for areas p2p, r2r
      the fold mints p2p's registry top-to-bottom first, then r2r's new bytes.)
      Minting continues from any ids the central ledger already holds, so folding
      into a partly-centralized engagement cannot collide.
    * **Place each file by the DERIVED state** — `processed/` only when the
      MERGED touches map is fully covered by the merged consumed map (WP-B's
      `_fully_consumed`, all areas), else `new/`. This is where the fold earns
      its keep: a file v1 had filed under one area's `processed/` returns to
      `new/` when another area never read it. File position is display; the
      ledger is truth.

    The v1 area trees and registries are LEFT IN PLACE, untouched — they are the
    historical record of what each area was told it held, and deleting them is a
    separate, human decision (the fold copies bytes, it does not move them). The
    v1 `touches` slugs are taken as given rather than re-validated against the
    manifests: this is a migration of what an engagement already recorded, and
    refusing to fold a legacy typo would leave the engagement stranded between
    layouts. Registration-time validation (`_validate_touches`) still guards
    everything minted from here on.
    """
    data = _load_ledger(root)
    ledger_entries = data["sources"]

    by_hash: dict[str, dict] = {}
    for entry in ledger_entries:
        digest = str(entry.get("hash") or "")
        if digest:
            by_hash.setdefault(digest, entry)

    remap: dict[str, str] = {}
    bytes_for: dict[str, Path] = {}         # central id -> a copy of the bytes

    for area_path in _v1_area_paths(root):
        area = area_path.name
        for v1 in _v1_entries(area_path):
            old_id = str(v1.get("id") or "").strip()
            if not old_id:
                raise LedgerError(
                    f"{_v1_registry_path(area_path)}: an entry has no id "
                    f"(cannot be remapped — fix the v1 registry first)"
                )
            physical = _v1_physical_file(area_path, v1)
            digest = str(v1.get("hash") or "").strip()
            if not digest and physical is not None:
                digest = _hash_file(str(physical))
            if not digest:
                raise LedgerError(
                    f"{_v1_registry_path(area_path)}: {old_id} has no hash and "
                    f"no readable file — nothing to dedupe or fold"
                )

            touches = {area: _slug_list(v1.get("touches"))}
            consumed = {area: _slug_list(v1.get("consumed"))}

            entry = by_hash.get(digest)
            if entry is None:
                sid = _mint(ledger_entries)
                entry = {
                    "id": sid,
                    "file": f"{LEDGER_DIRNAME}/new/"
                            f"{os.path.basename(str(v1.get('file') or ''))}",
                    "hash": digest,
                    "registered": str(v1.get("registered")
                                      or date.today().isoformat()),
                    "touches": touches,
                    "consumed": consumed,
                }
                ledger_entries.append(entry)
                by_hash[digest] = entry
            else:
                sid = str(entry.get("id") or "")
                entry["touches"] = _merge_area_map(
                    _area_map(entry.get("touches"), "touches", sid), touches)
                entry["consumed"] = _merge_area_map(
                    _area_map(entry.get("consumed"), "consumed", sid), consumed)

            remap[_prefixed(area, old_id)] = str(entry["id"])
            if physical is not None:
                bytes_for.setdefault(str(entry["id"]), physical)

    # Place the bytes by the DERIVED state, then write the ledger and the remap.
    new_dir(root).mkdir(parents=True, exist_ok=True)
    for entry in ledger_entries:
        sid = str(entry.get("id") or "")
        source = bytes_for.get(sid)
        if source is None:
            continue                        # already-central entry: leave it be
        touches = _area_map(entry.get("touches"), "touches", sid)
        consumed = _area_map(entry.get("consumed"), "consumed", sid)
        done = _fully_consumed(touches, consumed)
        sub = "processed" if done else "new"
        dest_dir = processed_dir(root) if done else new_dir(root)
        dest_dir.mkdir(parents=True, exist_ok=True)
        name = os.path.basename(str(entry.get("file") or "")) or source.name
        dest = dest_dir / name
        if not dest.is_file():
            shutil.copy2(str(source), str(dest))
        entry["file"] = f"{LEDGER_DIRNAME}/{sub}/{name}"
        entry["state"] = sub

    _dump_ledger(root, data)
    sources_dir(root).mkdir(parents=True, exist_ok=True)
    with open(_remap_path(root), "w", encoding="utf-8") as fh:
        yaml.safe_dump({"remap": dict(sorted(remap.items()))}, fh,
                       sort_keys=False, allow_unicode=True)
    return remap
