"""notes_util.py — shared MERGE-append for `_review/{slug}.notes.yaml` (M9/M10).

The one-doc review world could overwrite a slug's notes per extraction; the kit
world can't — a procedure's notes now accumulate from several sources (comment
extraction per kit doc, review-apply fallbacks, gap-workbook answers), possibly
across several invocations. This module owns the file shape: load-merge-emit,
de-duplicated on the full item tuple so re-running an ingest is idempotent.

Item keys (superset of M8's): type, location, anchor, change|note, author,
date, source. Consumed by consult-drafter (mode: update).

Python 3, stdlib + pyyaml.
"""

from __future__ import annotations

from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

_KEYS = ("type", "location", "anchor", "change", "note", "author", "date", "source")


def _scalar(v: str) -> str:
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    s = s.replace("\n", " ").replace("\t", " ")
    return f'"{s}"'


def _emit(slug: str, items: list[dict]) -> str:
    lines = [
        f"# _review/{slug}.notes.yaml",
        "# Procedure-anchored review notes (extracted/ingested mechanically).",
        "# Consumed by consult-drafter (mode: update).",
        f"procedure: {_scalar(slug)}",
        "items:",
    ]
    for it in items:
        first = True
        for k in _KEYS:
            v = it.get(k)
            if v in (None, ""):
                continue
            prefix = "  - " if first else "    "
            lines.append(f"{prefix}{k}: {_scalar(v)}")
            first = False
    return "\n".join(lines) + "\n"


def _fingerprint(it: dict) -> tuple:
    return tuple(str(it.get(k, "")) for k in _KEYS)


def load_items(area: Path, slug: str) -> list[dict]:
    f = Path(area) / "_review" / f"{slug}.notes.yaml"
    if yaml is None or not f.is_file():
        return []
    try:
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError:
        return []
    return [it for it in (data.get("items") or []) if isinstance(it, dict)]


def append_items(area, slug: str, new_items: list[dict]) -> int:
    """Merge new items into the slug's notes file. Returns how many were
    actually added (exact duplicates are dropped — idempotent re-runs)."""
    area = Path(area)
    existing = load_items(area, slug)
    seen = {_fingerprint(it) for it in existing}
    added = 0
    for it in new_items:
        if _fingerprint(it) in seen:
            continue
        seen.add(_fingerprint(it))
        existing.append(it)
        added += 1
    if added:
        out = area / "_review" / f"{slug}.notes.yaml"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_emit(slug, existing), encoding="utf-8")
    return added
