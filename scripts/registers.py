#!/usr/bin/env python3
"""registers.py — engagement register machinery (M30).

Usage (dispatched from engagement.py — the verb the orchestrator runs):
    python3 scripts/engagement.py register add <register> --id <entry-id> \
        --class citable|context --text "..." --provenance "SRC-004 (p2p)"
    python3 scripts/engagement.py register update <register> --id <entry-id> \
        --text "..." [--provenance "..."]
    python3 scripts/engagement.py register list \
        [--register X] [--class citable|context]

THE ONE WRITER of components/_client/registers/*.md — humans included (A2):
the human's authorship is the approval conversation, never the text editor.
Register CONTENT is always the human's call; this verb executes an approval,
it never judges. It is deliberately DUMB: refusals are if-statements
(id collision, missing provenance, unknown class/id), writes are idempotent
at content, and it holds no state beyond the files themselves.

File format (machine-parsed here, human-readable everywhere):

    # <Register Title>

    ## <entry-id>  [citable|context]

    body text (one or more lines)

    provenance: SRC-004 (p2p), SRC-002 (fixed-assets)

Two entry classes (M30 Part B): CITABLE = publishable source-backed shared
facts — prose references them, render compiles them into the appendix.
CONTEXT = engagement intelligence drafters ALIGN with but never cite by
name — prose cites the provenance SOURCE or raises a GAP; context entries
never reach rendered output. BOTH classes require --provenance (an
unprovenanced entry is the evidence-free channel by another name).

NOT enforced here (recorded for the approval conversation, per A1): the
two-areas promotion rule — a CITABLE entry needs evidence that 2+ areas
need the fact; one-area facts bounce back to prose at approval.

Seed files without `## <id> [class]` entries are pre-M30 freeform: `list`
reports them as unstructured; add/update refuse to touch them.

Exit codes: 0 = done (incl. idempotent no-op); 2 = refusal / bad usage.
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

import argparse
import re
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)
from dataclasses import dataclass
from pathlib import Path

CLASSES = ("citable", "context")
#: `## <entry-id>  [class]` — the entry heading grammar. Ids are the
#: `<register>#<entry-id>` convention's right half, so they get slug rules.
ENTRY_RE = re.compile(r"^##\s+(?P<id>[A-Za-z0-9][A-Za-z0-9_.-]*)\s+"
                      r"\[(?P<cls>[a-z]+)\]\s*$")
ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*")
PROV_PREFIX = "provenance:"


@dataclass
class Entry:
    id: str
    cls: str
    text: str          # body prose, newline-joined, no provenance line
    provenance: str


def registers_dir(root: Path) -> Path:
    return root / "_client" / "registers"


def register_files(root: Path) -> list[Path]:
    reg = registers_dir(root)
    return sorted(p for p in reg.glob("*") if p.is_file()) \
        if reg.is_dir() else []


def _titleize(name: str) -> str:
    return name.replace("-", " ").replace("_", " ").title()


def parse_register(path: Path) -> tuple[str, list[Entry] | None]:
    """(title, entries) — entries is None for a pre-M30 freeform file
    (non-blank content, zero entry headings). A file that is only an H1
    (or empty) parses as structured-with-no-entries."""
    text = path.read_text(encoding="utf-8")
    title = _titleize(path.stem)
    entries: list[Entry] = []
    cur: Entry | None = None
    body: list[str] = []
    saw_heading = False
    other_content = False

    def close():
        nonlocal cur, body
        if cur is not None:
            cur.text = "\n".join(body).strip("\n")
            entries.append(cur)
        cur, body = None, []

    for ln in text.split("\n"):
        m = ENTRY_RE.match(ln)
        if m and m.group("cls") in CLASSES:
            close()
            saw_heading = True
            cur = Entry(m.group("id"), m.group("cls"), "", "")
            continue
        if cur is not None:
            s = ln.strip()
            if s.lower().startswith(PROV_PREFIX):
                cur.provenance = s[len(PROV_PREFIX):].strip()
            else:
                body.append(ln)
            continue
        s = ln.strip()
        if s.startswith("# "):
            title = s[2:].strip()
        elif s:
            other_content = True
    close()
    if not saw_heading and other_content:
        return title, None
    return title, entries


def _serialize(title: str, entries: list[Entry]) -> str:
    out = [f"# {title}", ""]
    for e in entries:
        out += [f"## {e.id}  [{e.cls}]", "", e.text.strip("\n"), "",
                f"{PROV_PREFIX} {e.provenance}", ""]
    return "\n".join(out)


def load_all(root: Path) -> list[tuple[Path, str, list[Entry] | None]]:
    """Every register file, parsed: [(path, title, entries-or-None)].
    None marks a pre-M30 freeform file. The one read seam every consumer
    (briefs, render appendix) shares, so the format cannot drift."""
    out = []
    for p in register_files(root):
        try:
            title, entries = parse_register(p)
        except OSError:
            continue
        out.append((p, title, entries))
    return out


def first_line(text: str) -> str:
    for ln in text.split("\n"):
        if ln.strip():
            return ln.strip()
    return ""


def _err(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return 2


def _load_for_write(root: Path, name: str, must_exist: bool
                    ) -> tuple[Path, str, list[Entry] | None] | int:
    if not ID_RE.fullmatch(name or ""):
        return _err(f"bad register name {name!r} — letters, digits, "
                    f"dot, dash, underscore")
    path = registers_dir(root) / f"{name}.md"
    if not path.is_file():
        if must_exist:
            known = ", ".join(p.stem for p in register_files(root)) or "none"
            return _err(f"no register {name!r} under {registers_dir(root)} "
                        f"(known: {known})")
        return path, _titleize(name), []
    title, entries = parse_register(path)
    if entries is None:
        # v1.17.2: the old message implied a migration path that does not
        # exist (run-5 finding #3) — name the two real ones honestly. Both
        # are HUMAN moves: freeform content is human-authored, so what
        # survives migration is a content judgment, never mechanical.
        return _err(f"{path} is unstructured (pre-M30 freeform) — the verb "
                    f"never writes into freeform files, and there is no "
                    f"automated migration (what survives is a content "
                    f"judgment). Two paths, both the human's call: "
                    f"(a) move the freeform file aside, then re-create the "
                    f"facts worth keeping as entries via `register add` on "
                    f"the now-empty name; or (b) leave it freeform and put "
                    f"new entries in a NEW register name")
    return path, title, entries


def cmd_add(root: Path, name: str, eid: str, cls: str, text: str,
            provenance: str) -> int:
    if cls not in CLASSES:
        return _err(f"unknown --class {cls!r} (known: {', '.join(CLASSES)})")
    if not ID_RE.fullmatch(eid or ""):
        return _err(f"bad --id {eid!r} — letters, digits, dot, dash, "
                    f"underscore (the `{name}#{eid}` reference needs a "
                    f"stable id)")
    if not (text or "").strip():
        return _err("add requires --text")
    if not (provenance or "").strip():
        # BOTH classes: an unprovenanced entry is the evidence-free channel
        # by another name (A1 step 2 — same discipline as --peers on notes).
        return _err(f"a {cls} entry requires --provenance (SRC id(s) + "
                    f"origin area, stamped at approval) — nothing written")
    loaded = _load_for_write(root, name, must_exist=False)
    if isinstance(loaded, int):
        return loaded
    path, title, entries = loaded
    text, provenance = text.strip(), provenance.strip()
    hit = next((e for e in entries if e.id == eid), None)
    if hit is not None:
        if (hit.text, hit.cls, hit.provenance) == (text, cls, provenance):
            print(f"already present ({name}#{eid}, identical content) "
                  f"— no-op")
            return 0
        return _err(f"id collision: {name}#{eid} exists with different "
                    f"content — `register update` is the change verb")
    entries.append(Entry(eid, cls, text, provenance))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_serialize(title, entries), encoding="utf-8")
    print(f"added {name}#{eid}  [{cls}]  → {path}")
    return 0


def cmd_update(root: Path, name: str, eid: str, text: str,
               provenance: str | None) -> int:
    if not (text or "").strip():
        return _err("update requires --text (the replacement body)")
    loaded = _load_for_write(root, name, must_exist=True)
    if isinstance(loaded, int):
        return loaded
    path, title, entries = loaded
    hit = next((e for e in entries if e.id == eid), None)
    if hit is None:
        known = ", ".join(e.id for e in entries) or "none"
        return _err(f"no entry {name}#{eid} (known: {known})")
    new_prov = provenance.strip() if provenance is not None \
        else hit.provenance
    if not new_prov:
        return _err("an entry cannot lose its provenance — pass a non-empty "
                    "--provenance")
    if (hit.text, hit.provenance) == (text.strip(), new_prov):
        print(f"already current ({name}#{eid}, identical content) — no-op")
        return 0
    hit.text, hit.provenance = text.strip(), new_prov
    path.write_text(_serialize(title, entries), encoding="utf-8")
    print(f"updated {name}#{eid}  [{hit.cls}]  → {path}")
    return 0


def cmd_list(root: Path, register: str | None, cls: str | None) -> int:
    if cls is not None and cls not in CLASSES:
        return _err(f"unknown --class {cls!r} (known: {', '.join(CLASSES)})")
    files = load_all(root)
    if register is not None:
        files = [(p, t, e) for p, t, e in files if p.stem == register]
        if not files:
            known = ", ".join(p.stem for p in register_files(root)) or "none"
            return _err(f"no register {register!r} under "
                        f"{registers_dir(root)} (known: {known})")
    filters = [f"register={register}" if register else "",
               f"class={cls}" if cls else ""]
    filters = [f for f in filters if f]
    if filters:
        # A filtered view says so — nobody mistakes it for the whole picture.
        print(f"filtered view ({', '.join(filters)})")
    if not files:
        print(f"no registers under {registers_dir(root)}")
        return 0
    for path, title, entries in files:
        if entries is None:
            print(f"unstructured (pre-M30): {path}")
            continue
        print(f"REGISTER {path.stem} — {title}  ({path})")
        shown = [e for e in entries if cls is None or e.cls == cls]
        for e in shown:
            print(f"  {path.stem}#{e.id}  [{e.cls}]  {first_line(e.text)}")
            print(f"    provenance: {e.provenance}")
        if not shown:
            print("  (no entries" + (f" of class {cls}" if cls else "")
                  + ")")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="engagement.py register",
        description=(
            "The ONLY writer of components/_client/registers/ — humans "
            "included; approval happens in conversation, this verb executes "
            "it. TWO-AREAS PROMOTION RULE (applied at the approval "
            "conversation, not enforced here): a citable entry needs 2+ "
            "areas needing the fact — one-area facts stay in prose. "
            "Reference entries as <register>#<entry-id>."))
    ap.add_argument("action", choices=["add", "update", "list"])
    ap.add_argument("register", nargs="?",
                    help="register name (file stem under "
                         "_client/registers/); required for add/update")
    ap.add_argument("--root", default="components",
                    help="the engagement components/ dir "
                         "(default: ./components)")
    ap.add_argument("--id", dest="eid", help="entry id (stable — it is the "
                    "reference target <register>#<entry-id>)")
    ap.add_argument("--class", dest="cls",
                    help="citable (publishable, rendered) | context "
                         "(align-only, never rendered, never cited by name)")
    ap.add_argument("--text", help="the entry body")
    ap.add_argument("--provenance", default=None,
                    help="SRC id(s) + origin area — REQUIRED for add "
                         "(both classes)")
    ap.add_argument("--register", dest="filter_register", default=None,
                    help="list: only this register")
    a = ap.parse_args(argv)
    root = Path(a.root)
    if a.action == "list":
        return cmd_list(root, a.filter_register or a.register, a.cls)
    if not a.register or not a.eid:
        return _err(f"{a.action} requires <register> and --id")
    if a.action == "add":
        if not a.cls:
            return _err("add requires --class citable|context")
        return cmd_add(root, a.register, a.eid, a.cls, a.text or "",
                       a.provenance or "")
    return cmd_update(root, a.register, a.eid, a.text or "", a.provenance)


if __name__ == "__main__":
    raise SystemExit(main())
