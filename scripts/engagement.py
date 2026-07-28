#!/usr/bin/env python3
"""engagement.py — cross-area audit: one process, one home, one telling.

Usage:
    python3 scripts/engagement.py audit [components-dir]

The per-area guards (ownership map, taxonomy neighbors, reconcile check 17)
are PREVENTIVE and see only one area at a time. This audit is the
RETROSPECTIVE, engagement-wide sweep: it reads every area under the
components/ dir (default: ./components) and reports the three shapes of
cross-L1 duplication:

  1. TWIN L3s     — two areas each scoped a procedure whose titles are the
                    same activity (normalized-token containment). One of
                    them is the owner; the other should be retired or
                    reduced to a handoff.
  2. MENTIONS     — one area's prose names another area's procedure title
                    (reconcile check 17, aggregated engagement-wide with
                    both sides visible).
  3. SHARED PROSE — near-identical sentences appearing in fragments of two
                    different areas: the fingerprint of the same source
                    material drafted twice by siloed runs.

Read-only, advisory: exit 0 with findings (the human decides ownership),
exit 2 on a missing/empty components dir. The fix path for every finding is
the existing machinery — the human names the owner, the orchestrator appends
a `kind: review` note to the losing procedure's notes bus, and its drafter's
update pass reduces the duplication to a handoff sentence.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_WORD_RE = re.compile(r"[a-z0-9]+")
#: Title tokens carrying no activity identity on their own.
_STOP = {"the", "a", "an", "and", "of", "to", "for", "in", "process",
         "processing", "management", "and"}
#: Prose lines shorter than this carry too little identity to fingerprint.
_MIN_SENT = 60


def _tokens(title: str) -> frozenset[str]:
    return frozenset(w for w in _WORD_RE.findall(title.lower())
                     if w not in _STOP)


def _areas(root: Path) -> list[tuple[str, dict]]:
    out = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if d.name.startswith(("_", ".")):
            continue
        m = d / "manifest.json"
        if not m.is_file():
            continue
        try:
            out.append((d.name, json.loads(m.read_text(encoding="utf-8"))))
        except (OSError, ValueError):
            print(f"warning: {m} unreadable — area skipped", file=sys.stderr)
    return out


def _procedures(manifest: dict) -> list[dict]:
    return [c for c in manifest.get("components", [])
            if c.get("role") == "procedure"]


def _fragment_text(root: Path, area: str, comp: dict) -> str:
    p = root / area / comp.get("file", "")
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def _prose_sentences(text: str) -> set[str]:
    """Normalized prose lines long enough to fingerprint. Headings, tables,
    callout lines and the consult-meta fence are structure, not prose."""
    out = set()
    fenced = False
    for ln in text.split("\n"):
        s = ln.strip()
        if s.startswith("```"):
            fenced = not fenced
            continue
        if fenced or not s or s.startswith(("#", "|", ">", "<!--")):
            continue
        s = re.sub(r"^[-*+]\s+|^\d+\.\s+", "", s)
        s = re.sub(r"\s+", " ", s.lower())
        if len(s) >= _MIN_SENT:
            out.add(s)
    return out


def twin_l3s(areas, out: list[str]) -> int:
    """Same activity scoped as an L3 in two areas (title containment)."""
    procs = [(a, c.get("slug", "?"), (c.get("heading") or "").strip())
             for a, m in areas for c in _procedures(m)]
    n = 0
    for i, (a1, s1, t1) in enumerate(procs):
        k1 = _tokens(t1)
        if len(k1) < 2:
            continue
        for a2, s2, t2 in procs[i + 1:]:
            if a1 == a2:
                continue
            k2 = _tokens(t2)
            if len(k2) < 2:
                continue
            overlap = len(k1 & k2) / min(len(k1), len(k2))
            if overlap >= 0.75:
                n += 1
                out.append(f"  - {a1}/{s1} ('{t1}')  <->  {a2}/{s2} "
                           f"('{t2}')")
    return n


def cross_mentions(root: Path, areas, out: list[str]) -> int:
    """One area's prose naming another area's procedure title."""
    titles = [(a, c.get("slug", "?"), (c.get("heading") or "").strip())
              for a, m in areas for c in _procedures(m)
              if len((c.get("heading") or "").split()) >= 2]
    n = 0
    for a, m in areas:
        for comp in _procedures(m):
            text = _fragment_text(root, a, comp).lower()
            if not text:
                continue
            for oa, oslug, title in titles:
                if oa == a:
                    continue
                if title.lower() in text:
                    n += 1
                    out.append(f"  - {a}/{comp.get('slug', '?')} names "
                               f"'{title}' (owned by {oa}/{oslug})")
    return n


def shared_prose(root: Path, areas, out: list[str]) -> int:
    """Near-identical long sentences in fragments of two different areas."""
    sent_map: dict[tuple[str, str], set[str]] = {}
    for a, m in areas:
        for comp in _procedures(m):
            text = _fragment_text(root, a, comp)
            if text:
                sent_map[(a, comp.get("slug", "?"))] = _prose_sentences(text)
    keys = sorted(sent_map)
    n = 0
    for i, k1 in enumerate(keys):
        for k2 in keys[i + 1:]:
            if k1[0] == k2[0]:
                continue
            common = sent_map[k1] & sent_map[k2]
            if common:
                n += len(common)
                sample = sorted(common, key=len, reverse=True)[0]
                out.append(f"  - {k1[0]}/{k1[1]}  <->  {k2[0]}/{k2[1]}: "
                           f"{len(common)} shared sentence(s), e.g. "
                           f"\"{sample[:100]}…\"")
    return n


def audit(root: Path) -> int:
    areas = _areas(root)
    if len(areas) < 2:
        print(f"{root}: {len(areas)} area(s) found — the audit needs at "
              f"least two scoped areas under one components/ dir. If your "
              f"L1s live in separate folders, move each one under a single "
              f"engagement components/ directory first.")
        return 2 if not areas else 0
    print(f"ENGAGEMENT AUDIT — {len(areas)} areas under {root}: "
          + ", ".join(a for a, _ in areas))
    lines: list[str] = []
    n1 = twin_l3s(areas, lines)
    print(f"\n1. TWIN L3s — same activity scoped in two areas: {n1}")
    for ln in lines:
        print(ln)
    if n1:
        print("   fix: the human names the owner; the other area's "
              "procedure is retired (taxonomy retirement flow) or its "
              "drafter reduces it to the owner's handoff")

    lines = []
    n2 = cross_mentions(root, areas, lines)
    print(f"\n2. CROSS-AREA MENTIONS — prose naming another area's "
          f"procedure: {n2}")
    for ln in lines:
        print(ln)
    if n2:
        print("   fix: usually fine as ONE handoff sentence — flag only "
              "where the mention grew into documentation (see shape 3)")

    lines = []
    n3 = shared_prose(root, areas, lines)
    print(f"\n3. SHARED PROSE — near-identical sentences across areas: "
          f"{n3}")
    for ln in lines:
        print(ln)
    if n3:
        print("   fix: the human names the owning procedure; append a "
              "`kind: review` note to the OTHER procedure's notes bus "
              "naming the owner ('reduce to a handoff sentence'), then run "
              "its area's apply_review pass")

    total = n1 + n2 + n3
    print(f"\n{total} finding(s)." if total else "\nClean: no cross-area "
          "duplication detected.")
    return 0


def add_note(area: Path, slug: str, note: str) -> int:
    """Queue a `kind: review` item on a procedure's notes bus — the
    sanctioned fix path for audit findings ('reduce X to a handoff sentence;
    owner is <area>/<slug>'). Goes through notes_util.append_items, so it is
    validated and idempotent like every other producer."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import notes_util
    manifest = area / "manifest.json"
    if not manifest.is_file():
        print(f"error: {area} has no manifest.json — pass the AREA folder",
              file=sys.stderr)
        return 2
    slugs = {c.get("slug") for c in
             json.loads(manifest.read_text(encoding="utf-8"))
             .get("components", []) if c.get("role") == "procedure"}
    if slug not in slugs:
        print(f"error: unknown slug {slug!r} in {area} "
              f"(known: {', '.join(sorted(s for s in slugs if s))})",
              file=sys.stderr)
        return 2
    added = notes_util.append_items(area, slug,
                                    [{"kind": "review", "note": note}])
    print(f"{'queued 1 review note' if added else 'already queued (no-op)'} "
          f"for {slug} — the area's apply_review pass consumes it")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=["audit", "note"])
    ap.add_argument("root", nargs="?", default="components",
                    help="audit: the engagement components/ dir (default: "
                         "./components); note: the AREA folder")
    ap.add_argument("--slug", help="note: procedure slug to queue on")
    ap.add_argument("--note", help="note: the review instruction text")
    a = ap.parse_args(argv)
    root = Path(a.root)
    if a.command == "note":
        if not a.slug or not a.note:
            print("error: note requires --slug and --note", file=sys.stderr)
            return 2
        return add_note(root, a.slug, a.note)
    if not root.is_dir():
        print(f"error: {root} is not a directory — run from the engagement "
              f"root (the folder containing components/)", file=sys.stderr)
        return 2
    return audit(root)


if __name__ == "__main__":
    raise SystemExit(main())
