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

    a = ap.parse_args(argv)
    area = Path(a.area)
    try:
        if a.cmd == "add":
            print(add(area, target=a.target, origin=a.origin, text=a.text))
        elif a.cmd in CLOSED_STATES:
            print(close(area, a.flag, a.cmd, a.ref)["state"])
        else:
            lines = render(area, state=a.state)
            print("\n".join(lines) if lines else "(the flag queue is empty)")
    except FlagsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
