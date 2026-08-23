#!/usr/bin/env python3
"""
flags.py — the per-area FLAG QUEUE (M76 Part A, docs/v2/M76-returns-feed-the-record.md).

A flag is a piece of AGENT JUDGMENT formed during a pass and aimed at something
the pass itself does not own: "this node spans five performers, it is a split
candidate", "this SoD barrier wants a register entry", "this policy item is
surfaced, not closed". Before M76 that judgment lived in the return transcript
and nowhere else — paid for, then discarded.

    add(area, target=..., origin=..., text=...)  -> "FLAG-001"
    entries(area, state=None)                    -> [entry dicts]
    open_entries(area) / open_count(area)        -> the readers' view
    actioned(area, fid, reference=...)           -> closed, WITH its reference
    declined(area, fid, reference=...)           -> closed, WITH its reference

DELIBERATELY NOT A NOTES KIND. `notes_util`'s bus is FRAGMENT altitude: every
item lives in `_review/<slug>.notes.yaml` and is a work order an `apply_review`
drafter dispatch consumes. A flag targets a NODE, a REGISTER or the area, so
putting it on that bus would either dispatch drafters at fragment altitude for
node-altitude work or demand a filtered exemption in every notes consumer.
`notes_util.KINDS` is unchanged and a `flag` kind is refused there, by
construction; this module may reuse notes_util-style validation posture but
owns its own file and its own schema. `notes_util` stays a LIBRARY with no CLI
— the verb lives here.

THE FIELDS. Each flag carries:

  * `target` — `<node-slug>` | `register:<name>` | the literal `area`;
  * `origin` — `<agent-kind>/<slug>`, the pass that formed the judgment;
  * `text`   — one line of judgment, in the forming agent's own words;
  * `state`  — `open` | `actioned` | `declined`;
  * `reference` — the ACTIONING REFERENCE, required on every close: the
    taxonomy change, the register entry, the finding id, the ASK id (the M75
    boundary: the curator may propose an ask FROM a flag, and the flag then
    records that ask id), or the human's declared decline.

APPEND-ONLY, like the ledger. A close records the state change in the entry's
`history` and never deletes anything: a flag drops out of the OPEN views and
stays in the file forever. A closed flag cannot be re-closed — the refusal
names its current state.

ONE WRITER, ONE FILE: `_dump` -> `flags_path(area)`
(`<area>/_reference/flags.yaml`). Python 3, stdlib + pyyaml. Fail-loud: every
refusal is a FlagsError naming the offending value, and nothing is written on
a refusal.
"""

from __future__ import annotations

# M67 interpreter floor: this block runs BEFORE any first-party import, because
# a < 3.10 interpreter dies inside the engine modules at import time and a check
# placed after those imports could never fire.
import os as _os  # noqa: E402
import sys as _sys  # noqa: E402
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _pyfloor  # noqa: E402  (3.9-importable by contract)

_pyfloor.require()

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import argparse
import re

from pathlib import Path

import yaml


class FlagsError(Exception):
    """Raised when a flag operation is refused. The message always names the
    offending value (the asks.AsksError / findings.FindingsError posture)."""


#: The queue's home, relative to the AREA folder — a flag is area state, like
#: the rest of `_reference/`.
REFERENCE_DIRNAME = "_reference"
FLAGS_FILENAME = "flags.yaml"

#: The states. A flag is open until it is closed one of two ways, and a close
#: always carries its actioning reference.
OPEN, ACTIONED, DECLINED = "open", "actioned", "declined"
STATES = (OPEN, ACTIONED, DECLINED)
CLOSED_STATES = (ACTIONED, DECLINED)

#: `FLAG-nnn` — the id grammar, mirroring FIND-nnn / ASK-nnn / SRC-nnn.
ID_PREFIX = "FLAG"
ID_RE = re.compile(rf"^{ID_PREFIX}-(\d+)$")

#: The literal target meaning "the area itself" (an observation about the
#: whole area, not about one node).
TARGET_AREA = "area"

#: A register target: `register:<name>`.
TARGET_REGISTER_PREFIX = "register:"

#: The slug grammar shared by node slugs and register names.
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")

#: `<agent-kind>/<slug>` — the pass that formed the judgment.
ORIGIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")


# --------------------------------------------------------------------------- #
# The file — the ONE thing this module writes
# --------------------------------------------------------------------------- #

def flags_path(area) -> Path:
    """`<area>/_reference/flags.yaml` — this module's only write target."""
    return Path(area) / REFERENCE_DIRNAME / FLAGS_FILENAME


def _empty() -> dict:
    return {"flags": []}


def _load(area) -> dict:
    """The queue as a mapping. A missing file is an EMPTY queue, not an error
    (an area whose passes formed no judgment is normal); a malformed one is
    fail-loud — this is unreproducible agent judgment."""
    path = flags_path(area)
    if not path.is_file():
        return _empty()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise FlagsError(f"{path}: flag queue is unreadable ({exc})") from exc
    if data is None:
        return _empty()
    if not isinstance(data, dict) or not isinstance(data.get("flags"), list):
        raise FlagsError(
            f'{path}: flag queue must be a mapping with a "flags" list '
            f"(got {type(data).__name__})")
    for entry in data["flags"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise FlagsError(f"{path}: every flag entry must be a mapping "
                             f"with an id (got {entry!r})")
    return data


def _dump(area, data: dict) -> None:
    """THE ONLY WRITE IN THIS MODULE (see the module docstring)."""
    path = flags_path(area)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True,
                       default_flow_style=False),
        encoding="utf-8")


# --------------------------------------------------------------------------- #
# Shape checks (nothing is written on a refusal)
# --------------------------------------------------------------------------- #

def clean_target(target) -> str:
    """Normalise a target, or refuse by name.

    Three shapes and no others: the literal `area`, `register:<name>`, or a
    node slug. A free-text target would make the queue unjoinable to the
    things it is about."""
    value = str(target or "").strip()
    if not value:
        raise FlagsError(
            "a flag requires a TARGET — `area`, `register:<name>` or a node "
            "slug; nothing written")
    if value == TARGET_AREA:
        return value
    if value.startswith(TARGET_REGISTER_PREFIX):
        name = value[len(TARGET_REGISTER_PREFIX):]
        if not SLUG_RE.match(name):
            raise FlagsError(
                f"bad register target {value!r} — the shape is "
                f"`register:<name>`; nothing written")
        return value
    if not SLUG_RE.match(value):
        raise FlagsError(
            f"bad target {value!r} — a flag targets `area`, "
            f"`register:<name>` or a node slug; nothing written")
    return value


def clean_origin(origin) -> str:
    """`<agent-kind>/<slug>` — who formed this judgment, on what."""
    value = str(origin or "").strip()
    if not ORIGIN_RE.match(value):
        raise FlagsError(
            f"bad origin {value!r} — the shape is `<agent-kind>/<slug>` (e.g. "
            f"`consult-drafter/receive-invoice`); nothing written")
    return value


def _text_field(value, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FlagsError(f"a flag requires {what} (got {value!r}); "
                         f"nothing written")
    return " ".join(value.split())


# --------------------------------------------------------------------------- #
# The queue
# --------------------------------------------------------------------------- #

def _mint(existing: list[dict]) -> str:
    """`FLAG-nnn`, area-scoped, max existing + 1 — ids are never reused (a
    closed flag keeps its id forever, and something may cite it)."""
    highest = 0
    for entry in existing:
        m = ID_RE.match(str(entry.get("id") or ""))
        if m:
            highest = max(highest, int(m.group(1)))
    return f"{ID_PREFIX}-{highest + 1:03d}"


def add(area, target: str, origin: str, text: str) -> str:
    """File one flag and return its id.

    THE agents' verb (M76 Part B, the tenancy ruling): the agent that formed
    the judgment runs this before it returns, and its RETURN then carries the
    flag ids rather than the narration."""
    target = clean_target(target)
    origin = clean_origin(origin)
    text = _text_field(text, "TEXT — one line of judgment in your own words")

    data = _load(area)
    fid = _mint(data["flags"])
    data["flags"].append({
        "id": fid,
        "state": OPEN,
        "target": target,
        "origin": origin,
        "text": text,
        "history": [{"state": OPEN}],
    })
    _dump(area, data)
    return fid


def entries(area, state: str | None = None) -> list[dict]:
    """The flags, in filing order; `state` filters. Read-only; returns
    copies."""
    if state is not None and state not in STATES:
        raise FlagsError(f"unknown state {state!r} "
                         f"(known: {', '.join(STATES)})")
    out = []
    for entry in _load(area)["flags"]:
        if state is not None and entry.get("state") != state:
            continue
        out.append(dict(entry))
    return out


def open_entries(area) -> list[dict]:
    """The OPEN flags — what every reader in Part C lists."""
    return entries(area, state=OPEN)


def open_count(area) -> int:
    """How many flags this area carries unactioned — the draft-ready gate's
    advisor detail (never a gate of its own: accepting a draft with open
    flags stays a visible choice)."""
    return len(open_entries(area))


def _find(data: dict, fid: str) -> dict:
    hit = next((e for e in data["flags"] if e.get("id") == fid), None)
    if hit is None:
        known = ", ".join(str(e.get("id")) for e in data["flags"]) or "none"
        raise FlagsError(f"no flag {fid!r} in this area's queue "
                         f"(known: {known})")
    return hit


def close(area, fid: str, state: str, reference: str) -> dict:
    """Close a flag `actioned` or `declined`, WITH its actioning reference.

    The reference is what makes the queue append-only in spirit as well as on
    disk: a flag never just disappears, it is closed by naming the thing that
    closed it (the taxonomy change, the register entry, the finding id, the
    ASK id the M75 curator minted from it, or the human's declared decline)."""
    if state not in CLOSED_STATES:
        raise FlagsError(f"a flag closes {' or '.join(CLOSED_STATES)}, not "
                         f"{state!r}; nothing written")
    ref = _text_field(reference,
                      "an actioning REFERENCE (the taxonomy change, the "
                      "register entry, the finding id, the ASK id, or the "
                      "human's declared decline)")
    data = _load(area)
    hit = _find(data, fid)
    current = hit.get("state")
    if current != OPEN:
        raise FlagsError(f"{fid} is already {current} (reference: "
                         f"{hit.get('reference')!r}) — a closed flag is kept, "
                         f"never re-closed; nothing written")
    hit["state"] = state
    hit["reference"] = ref
    history = hit.get("history")
    if not isinstance(history, list):
        history = []
    history.append({"state": state, "reference": ref})
    hit["history"] = history
    _dump(area, data)
    return dict(hit)


def actioned(area, fid: str, reference: str) -> dict:
    """The flag was acted on — `reference` names what did it."""
    return close(area, fid, ACTIONED, reference)


def declined(area, fid: str, reference: str) -> dict:
    """The flag was declined — `reference` names the human's decision."""
    return close(area, fid, DECLINED, reference)


# --------------------------------------------------------------------------- #
# The TENURE RECORD (M77 Part A) — the taxonomist's own working record
#
# A flag is judgment aimed OUTWARD, at something the forming pass does not own.
# A tenure entry is judgment aimed INWARD: the taxonomist's own reasoning about
# its own house — a structural ruling and its rationale, a decision explicitly
# deferred with what would settle it, a call made reluctantly and worth
# revisiting. Before M77 that reasoning lived in the return transcript and the
# next incremental dispatch re-derived it from scratch, possibly DIFFERENTLY,
# because a fresh judge has no case law.
#
#     tenure_add(area, kind=..., text=...)     -> "TEN-001"
#     tenure_entries(area, state=None)         -> [entry dicts]
#     tenure_standing(area)                    -> the brief's view
#     tenure_supersede(area, tid, reference=...) / tenure_resolve(...)
#
# HOSTED HERE, NOT IN A NEW MODULE (the M77 set ruling): two near-identical
# one-writer library+CLI modules is exactly the harness sprawl this set's
# doctrine — grow the tenancy, not the harness — warns against. Same posture
# as the queue above: one file, one writer, append-only, fail-loud.
#
# THE BOUNDARY (M77 Part C): the tenure record is REASONING, not state. Its one
# reader is the taxonomist's own brief. The advisor never reads it, no guard
# keys off it, render never sees it. A tenure entry another agent needs is, by
# definition, a flag — file it as one, above.
#
# NO COLLISION WITH THE M66 NODE GUARD: `scaffold.taxonomy_hashes` globs
# `_taxonomy/*.md`, so this dot-named yaml inside the same folder is invisible
# to reconcile check 15.5.
# --------------------------------------------------------------------------- #

#: The record's home, relative to the AREA folder — inside `_taxonomy/`, the
#: house the taxonomist already owns, dot-named like the M66 guard file.
LIVE_TAXONOMY_DIRNAME = "_taxonomy"
TENURE_FILENAME = ".tenure.yaml"

#: The entry types. A tenure entry is one of exactly three things.
RULING, DEFERRED, DOUBT = "ruling", "deferred", "doubt"
TENURE_TYPES = (RULING, DEFERRED, DOUBT)

#: The states. An entry stands until it is closed one of two ways, and a close
#: always carries its superseding/resolving reference.
STANDING, SUPERSEDED, RESOLVED = "standing", "superseded", "resolved"
TENURE_STATES = (STANDING, SUPERSEDED, RESOLVED)
TENURE_CLOSED_STATES = (SUPERSEDED, RESOLVED)

#: `TEN-nnn` — the id grammar, mirroring FLAG-nnn / ASK-nnn / FIND-nnn.
TENURE_ID_PREFIX = "TEN"
TENURE_ID_RE = re.compile(rf"^{TENURE_ID_PREFIX}-(\d+)$")


def tenure_path(area) -> Path:
    """`<area>/_taxonomy/.tenure.yaml` — the record's one location."""
    return Path(area) / LIVE_TAXONOMY_DIRNAME / TENURE_FILENAME


def _tenure_empty() -> dict:
    return {"tenure": []}


def _tenure_load(area) -> dict:
    """The record as a mapping. A missing file is an EMPTY record, not an
    error (an area whose taxonomist has filed nothing is normal, and every v1
    area is exactly that); a malformed one is fail-loud."""
    path = tenure_path(area)
    if not path.is_file():
        return _tenure_empty()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise FlagsError(f"{path}: tenure record is unreadable ({exc})") from exc
    if data is None:
        return _tenure_empty()
    if not isinstance(data, dict) or not isinstance(data.get("tenure"), list):
        raise FlagsError(
            f'{path}: tenure record must be a mapping with a "tenure" list '
            f"(got {type(data).__name__})")
    for entry in data["tenure"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise FlagsError(f"{path}: every tenure entry must be a mapping "
                             f"with an id (got {entry!r})")
    return data


def _tenure_dump(area, data: dict) -> None:
    """THE ONLY WRITE to the tenure record in this codebase."""
    path = tenure_path(area)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True,
                       default_flow_style=False),
        encoding="utf-8")


def clean_tenure_type(kind) -> str:
    """One of `ruling | deferred | doubt`, or a refusal naming the value."""
    value = str(kind or "").strip().lower()
    if value not in TENURE_TYPES:
        raise FlagsError(
            f"unknown tenure type {kind!r} — an entry is a "
            f"{' | '.join(TENURE_TYPES)} (a structural decision and its "
            f"rationale, a decision NOT taken with what would settle it, or "
            f"a call made reluctantly); nothing written")
    return value


def _tenure_mint(existing: list[dict]) -> str:
    """`TEN-nnn`, area-scoped, max existing + 1 — ids are never reused: a
    superseded entry keeps its id forever and its successor cites it."""
    highest = 0
    for entry in existing:
        m = TENURE_ID_RE.match(str(entry.get("id") or ""))
        if m:
            highest = max(highest, int(m.group(1)))
    return f"{TENURE_ID_PREFIX}-{highest + 1:03d}"


def tenure_add(area, kind: str, text: str) -> str:
    """File one tenure entry and return its id.

    THE taxonomist's own verb (the M76 Part B tenancy ruling applies verbatim:
    the agent that formed the judgment files it, before it returns)."""
    kind = clean_tenure_type(kind)
    text = _text_field(text, "TEXT — one line of reasoning in your own words")

    data = _tenure_load(area)
    tid = _tenure_mint(data["tenure"])
    data["tenure"].append({
        "id": tid,
        "type": kind,
        "state": STANDING,
        "text": text,
        "history": [{"state": STANDING}],
    })
    _tenure_dump(area, data)
    return tid


def tenure_entries(area, state: str | None = None) -> list[dict]:
    """The entries, in filing order; `state` filters. Read-only; copies."""
    if state is not None and state not in TENURE_STATES:
        raise FlagsError(f"unknown tenure state {state!r} "
                         f"(known: {', '.join(TENURE_STATES)})")
    out = []
    for entry in _tenure_load(area)["tenure"]:
        if state is not None and entry.get("state") != state:
            continue
        out.append(dict(entry))
    return out


def tenure_standing(area) -> list[dict]:
    """The STANDING entries — the precedent the next dispatch starts from
    (standing rulings, open deferrals, live doubts). Superseded and resolved
    entries stay on disk and drop out of this view."""
    return tenure_entries(area, state=STANDING)


def _tenure_find(data: dict, tid: str) -> dict:
    hit = next((e for e in data["tenure"] if e.get("id") == tid), None)
    if hit is None:
        known = ", ".join(str(e.get("id")) for e in data["tenure"]) or "none"
        raise FlagsError(f"no tenure entry {tid!r} in this area's record "
                         f"(known: {known})")
    return hit


def tenure_close(area, tid: str, state: str, reference: str) -> dict:
    """Close an entry `superseded` or `resolved`, WITH its reference.

    Nothing is deleted: precedent accumulates append-only, and a later pass
    can always read what was decided, by whom it was overturned, and why."""
    if state not in TENURE_CLOSED_STATES:
        raise FlagsError(f"a tenure entry closes "
                         f"{' or '.join(TENURE_CLOSED_STATES)}, not "
                         f"{state!r}; nothing written")
    ref = _text_field(reference,
                      "a REFERENCE (the superseding TEN- id, the ASK id or "
                      "evidence that settled it, or the taxonomy change that "
                      "carried it out)")
    data = _tenure_load(area)
    hit = _tenure_find(data, tid)
    current = hit.get("state")
    if current != STANDING:
        raise FlagsError(f"{tid} is already {current} (reference: "
                         f"{hit.get('reference')!r}) — a closed tenure entry "
                         f"is kept, never re-closed; nothing written")
    hit["state"] = state
    hit["reference"] = ref
    history = hit.get("history")
    if not isinstance(history, list):
        history = []
    history.append({"state": state, "reference": ref})
    hit["history"] = history
    _tenure_dump(area, data)
    return dict(hit)


def tenure_supersede(area, tid: str, reference: str) -> dict:
    """The ruling was overturned — KNOWINGLY, by naming what replaces it."""
    return tenure_close(area, tid, SUPERSEDED, reference)


def tenure_resolve(area, tid: str, reference: str) -> dict:
    """The deferral or doubt was settled — `reference` names what settled
    it."""
    return tenure_close(area, tid, RESOLVED, reference)


def tenure_line(entry: dict) -> str:
    """One compact line for a tenure entry — the same words in the brief and
    in the CLI listing, so no two surfaces describe precedent differently."""
    ref = entry.get("reference")
    tail = f"  [{entry.get('state')}: {ref}]" if ref else ""
    return (f"{entry.get('id')}  {entry.get('type')}: "
            f"{entry.get('text')}{tail}")


def tenure_render(area, state: str | None = None) -> list[str]:
    """The tenure lines for one area. Read-only."""
    return [tenure_line(e) for e in tenure_entries(area, state=state)]


# --------------------------------------------------------------------------- #
# The readers' render (one line per flag, shared by every surface)
# --------------------------------------------------------------------------- #

def line(entry: dict) -> str:
    """One compact line for a flag — the same words in the taxonomist brief,
    the analyst brief and the CLI listing, so no two surfaces can describe a
    flag differently."""
    ref = entry.get("reference")
    tail = f"  [{entry.get('state')}: {ref}]" if ref else ""
    return (f"{entry.get('id')}  target {entry.get('target')}  "
            f"(from {entry.get('origin')}): {entry.get('text')}{tail}")


def render(area, state: str | None = None) -> list[str]:
    """The flag lines for one area, or a single explanatory line when the
    queue is empty. Read-only."""
    rows = entries(area, state=state)
    return [line(e) for e in rows]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None) -> int:
    """`flags.py <verb> --area <area> [...]` — the deterministic surface the
    drafter and the taxonomist file through.

    Exit 0 on success, 2 on a refusal (named on stderr). Nothing here has
    judgment: the agent brings the judgment, the verb records it."""
    import sys

    ap = argparse.ArgumentParser(
        prog="flags.py",
        description="The per-area flag queue (M76) — agent judgment on disk.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def _area(p):
        p.add_argument("--area", required=True,
                       help="the AREA folder (components/<area>)")
        return p

    p = _area(sub.add_parser("add", help="file one flag"))
    p.add_argument("--target", required=True,
                   help="<node-slug> | register:<name> | area")
    p.add_argument("--origin", required=True,
                   help="<agent-kind>/<slug> — who formed the judgment")
    p.add_argument("--text", required=True, help="one line of judgment")

    for verb in CLOSED_STATES:
        q = _area(sub.add_parser(verb, help=f"close a flag as {verb}"))
        q.add_argument("flag", help="the FLAG id")
        q.add_argument("--ref", required=True,
                       help="the actioning reference (an ASK id, a register "
                            "entry, a finding id, the human's decline)")

    q = _area(sub.add_parser("list", help="print the queue"))
    q.add_argument("--state", choices=list(STATES), default=None)

    # M77 — the taxonomist's own working record, hosted here (not a new
    # module): the same one-writer, append-only, fail-loud posture.
    t = _area(sub.add_parser("tenure-add", help="file one tenure entry"))
    t.add_argument("--type", required=True, dest="kind",
                   help=" | ".join(TENURE_TYPES))
    t.add_argument("--text", required=True, help="one line of reasoning")

    for verb, state in (("tenure-supersede", SUPERSEDED),
                        ("tenure-resolve", RESOLVED)):
        t = _area(sub.add_parser(verb, help=f"close an entry {state}"))
        t.add_argument("entry", help="the TEN id")
        t.add_argument("--ref", required=True,
                       help="the superseding TEN id, the ASK id or evidence "
                            "that settled it, or the taxonomy change")

    t = _area(sub.add_parser("tenure-list", help="print the tenure record"))
    t.add_argument("--state", choices=list(TENURE_STATES), default=None)

    a = ap.parse_args(argv)
    area = Path(a.area)
    try:
        if a.cmd == "add":
            print(add(area, target=a.target, origin=a.origin, text=a.text))
        elif a.cmd in CLOSED_STATES:
            print(close(area, a.flag, a.cmd, a.ref)["state"])
        elif a.cmd == "tenure-add":
            print(tenure_add(area, kind=a.kind, text=a.text))
        elif a.cmd in ("tenure-supersede", "tenure-resolve"):
            state = (SUPERSEDED if a.cmd == "tenure-supersede" else RESOLVED)
            print(tenure_close(area, a.entry, state, a.ref)["state"])
        elif a.cmd == "tenure-list":
            lines = tenure_render(area, state=a.state)
            print("\n".join(lines) if lines
                  else "(the tenure record is empty)")
        else:
            lines = render(area, state=a.state)
            print("\n".join(lines) if lines else "(the flag queue is empty)")
    except FlagsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
