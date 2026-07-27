#!/usr/bin/env python3
"""
migrate_sections.py — M23's one-time, MECHANICAL section-heading migration.

    python3 scripts/migrate_sections.py components/<area>            # dry run
    python3 scripts/migrate_sections.py components/<area> --write    # apply

Strips the display LETTER off every procedure sub-section heading in one area:

    ### A. Process Overview   ->   ### Process Overview

That is the whole job. Titles are NOT touched, bodies are NOT touched, callouts,
steps, `consult-meta` end matter and line COUNT are all untouched — this is pure
identity work (the letter is now assigned at render from the profile's
`sections:` order), so there is zero judgment in it and no drafter pass is
needed. It is the reason M16 move 1's re-letter is a registry edit rather than a
~15-pass full re-draft.

Guarantees:

  - IDEMPOTENT. A second run reports "0 heading(s)" and writes nothing; a file
    with nothing to change is not rewritten at all (mtime preserved).
  - ZERO CONTENT CHANGE. The only edit is deleting the `X. ` between `### ` and
    the title. Verified per file: the migrated text must equal the original with
    exactly those prefixes removed, and every heading must still resolve to the
    same section slug it resolved to before. Any file that fails the check is
    left alone and reported.
  - SAFE TO SKIP. Migration is NOT a prerequisite. `doc_model.section_of_heading`
    resolves both forms, so an unmigrated area renders, aggregates, reconciles
    and drift-checks exactly as it does today (see docs/M23-section-identity.md,
    "Transition contract"). This script is a tidy-up, not a gate.

Only `role: procedure` components are considered: static and derived files have
their own `###` sub-headings ("### Pain Points" in Appendix A) that are not
sections and must never be rewritten.

Exit codes:
    0 = nothing to do, or the migration applied cleanly
    1 = a fragment could not be migrated safely (nothing written for it)
    2 = bad usage / unreadable input
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import doc_model  # noqa: E402  (the section registry + the one heading parser)


def strip_letters(text: str) -> tuple[str, int]:
    """Return (migrated_text, headings_changed) for one fragment's text.

    A heading is rewritten only when the LETTERLESS form still identifies the
    same section — i.e. the title itself is in the registry. A heading whose
    title is unknown keeps its letter, because the letter is the only thing
    naming its section and dropping it would lose the identity.
    """
    lines = text.split("\n")
    changed = 0
    for i, line in enumerate(lines):
        m = doc_model.SECTION_HEADING_RE.match(line)
        if not m or not m.group("letter"):
            continue
        before = doc_model.section_of_heading(line)
        stripped = f"### {m.group('title')}"
        if before is None or doc_model.section_of_heading(stripped) != before:
            continue           # unknown title: the letter is load-bearing here
        lines[i] = stripped
        changed += 1
    return "\n".join(lines), changed


def _verify(original: str, migrated: str) -> bool:
    """The zero-content-change check: migrated == original with only `X. `
    letter prefixes dropped from section headings, same line count."""
    a, b = original.split("\n"), migrated.split("\n")
    if len(a) != len(b):
        return False
    for old, new in zip(a, b):
        if old == new:
            continue
        m = doc_model.SECTION_HEADING_RE.match(old)
        if not m or not m.group("letter"):
            return False
        if new != f"### {m.group('title')}":
            return False
        if doc_model.section_of_heading(new) != doc_model.section_of_heading(old):
            return False
    return True


def migrate_area(area, write: bool = False) -> dict:
    """Migrate one area folder. Returns a stats dict; writes only if `write`."""
    area = Path(area)
    manifest = doc_model.load_manifest(area)
    stats = {"files": 0, "headings": 0, "written": [], "skipped": [],
             "failed": []}
    for comp in manifest.get("components", []):
        if comp.get("role") != "procedure":
            continue
        path = area / comp.get("file", "")
        if not path.is_file():
            continue
        stats["files"] += 1
        original = path.read_text(encoding="utf-8")
        migrated, changed = strip_letters(original)
        if not changed:
            stats["skipped"].append(comp["file"])
            continue
        if not _verify(original, migrated):
            stats["failed"].append(comp["file"])
            continue
        stats["headings"] += changed
        stats["written"].append((comp["file"], changed))
        if write:
            path.write_text(migrated, encoding="utf-8")
    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Strip display letters from an area's section headings (M23)")
    ap.add_argument("area", help="area folder containing manifest.json")
    ap.add_argument("--write", action="store_true",
                    help="apply the migration (default: dry run, report only)")
    a = ap.parse_args(argv)

    area = Path(a.area)
    if not (area / "manifest.json").is_file():
        print(f"error: no manifest.json in folder: {area}", file=sys.stderr)
        return 2
    try:
        stats = migrate_area(area, write=a.write)
    except doc_model.ManifestError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    verb = "migrated" if a.write else "would migrate"
    print(f"{verb} {stats['headings']} heading(s) in "
          f"{len(stats['written'])} of {stats['files']} fragment(s)")
    for file, n in stats["written"]:
        print(f"  {file}: {n} heading(s)")
    if stats["skipped"]:
        print(f"  already letterless: {len(stats['skipped'])} fragment(s)")
    for file in stats["failed"]:
        print(f"ERROR {file}: heading edit would change content — left alone",
              file=sys.stderr)
    if not a.write and stats["headings"]:
        print("dry run — re-run with --write to apply")
    return 1 if stats["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
