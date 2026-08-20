"""notes_util.py — the `_review/{slug}.notes.yaml` NOTES BUS (M9/M10 + M6).

The one-doc review world could overwrite a slug's notes per extraction; the kit
world can't — a procedure's notes accumulate from several producers, possibly
across several invocations. This module owns the file shape: load-merge-emit,
de-duplicated on the full item tuple so re-running an ingest is idempotent.

THE BUS CONTRACT (M6 "Notes carry a kind"). One consumer (the advisor's guard 2
→ `consult-drafter` in `mode: update`) and five producers: M8 review extraction
(`review_extract.py`, plus `review_apply.py` fallbacks and `gaps_ingest.py`
answers), M6 source notes and retirement notes (written by `scaffold.py` at the
confirm gate), M12 consolidation findings, M20 rename notes. Undifferentiated
items break retirement accounting (a *reviewer comment* would retire a source no
drafter ever read — silent loss of client material) and the human veto (deleting
a *source* note strands its source forever). So:

  1. **Every item carries `kind:`** — one of `KINDS` — stamped by its producer.
     `kind: source` items also carry `src: SRC-<id>`, the id the drafter resolves
     through `_reference/sources.yaml`. There is NO default: a kind-less item is
     a loud error at load and at append, never a silent "review".
  2. **The field set is closed and preserved.** `_emit` writes every key in
     `_KEYS`, so a second producer appending to the same file cannot silently
     drop another's `kind`/`src` on merge; a field OUTSIDE the tuple is a loud
     error rather than a silent drop.
  3. Retirement accounting reads `kind`/`src` and credits a source only from
     `kind: source` consumption — `sources.py` owns that join.

Migration note: a notes file written before M6 carries no `kind:`, so the first
load raises `NotesError` naming the file and item. Those are un-archived reviewer
items — add `kind: review` to each by hand (or archive the file); nothing else
in the shape changed.

Python 3, stdlib + pyyaml.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

# The five producers' kinds (M6). `review` covers every reviewer-originated
# item (comments, tracked-change fallbacks, gap-workbook answers).
KINDS = ("review", "source", "retirement", "rename", "consolidation")

# The closed field set. `kind` leads (it is what the consumer routes on) and
# `src` follows it; the rest is M8's superset plus M12's two fields —
# `category` (the finding taxonomy) and `peers` (a comma-joined slug string,
# never a YAML list: `_scalar` would emit Python list syntax otherwise).
# Anything else is an error.
_KEYS = ("kind", "src", "origin", "type", "category", "location", "anchor",
         "change", "note", "peers", "author", "date", "source")

NOTES_SUFFIX = ".notes.yaml"


class NotesError(Exception):
    """A fail-loud defect in a notes item (never a silent drop)."""


def _stored_form(v) -> str:
    """The NORMALIZED value a scalar is stored as (M60 Part B): `\\n`, `\\r`,
    `\\t` flatten to single spaces — a deliberate encoding decision (items are
    one-line records) shared verbatim by `_fingerprint`, so dedup always
    compares what the file will actually hold."""
    return (str(v).replace("\r\n", " ").replace("\n", " ")
            .replace("\r", " ").replace("\t", " "))


def _scalar(v: str) -> str:
    """One double-quoted YAML scalar that ALWAYS parses (M60 Part A).

    Every character outside the printable-safe range — C0 controls, DEL, the
    C1 block (routine Windows-1252 mojibake in client docx) — is written as a
    YAML `\\xNN` escape. Property: for ANY Python string, write → load
    round-trips to `_stored_form(value)`. One raw control character used to
    make the whole file invalid YAML, silently erasing a slug's history."""
    s = _stored_form(v).replace("\\", "\\\\").replace('"', '\\"')
    out = []
    for ch in s:
        code = ord(ch)
        if code < 0x20 or code == 0x7F or 0x80 <= code <= 0x9F:
            out.append(f"\\x{code:02X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _emit(slug: str, items: list[dict]) -> str:
    lines = [
        f"# _review/{slug}.notes.yaml",
        "# Procedure-anchored notes (the M6 bus: every item carries `kind`).",
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
    # M60 Part B: fingerprint WHAT IS STORED — a reloaded multiline item must
    # match its raw incoming twin, or re-running an ingest appends forever.
    return tuple(_stored_form(it.get(k, "")) for k in _KEYS)


def validate_item(item: dict, where: str = "notes item") -> dict:
    """Enforce the bus contract on one item, or raise NotesError.

    Checked here rather than at each producer so all five stamp the same shape,
    and so a hand-edited file is caught the moment anything reads it."""
    unknown = sorted(k for k in item if k not in _KEYS)
    if unknown:
        raise NotesError(
            "%s: unknown field(s) %s — the notes bus carries only %s (M6 rule 2: "
            "an unknown field is an error, never a silent drop on merge)"
            % (where, ", ".join(unknown), ", ".join(_KEYS)))
    kind = str(item.get("kind") or "").strip()
    if not kind:
        raise NotesError(
            "%s: no `kind:` — every producer stamps one of %s and there is no "
            "default (M6 rule 1)" % (where, " | ".join(KINDS)))
    if kind not in KINDS:
        raise NotesError("%s: unknown kind %r — expected one of %s"
                         % (where, kind, " | ".join(KINDS)))
    if kind == "source" and not str(item.get("src") or "").strip():
        raise NotesError(
            "%s: `kind: source` with no `src:` — a source note that cannot name "
            "its SRC- id can never retire its source (M6 rule 3)" % where)
    if kind == "consolidation":
        # M12's evidence rule enforced at the bus, not just the producer: a
        # consolidation finding is a RELATIONSHIP, so it must name its peers
        # (the other procedure(s) that evidence it) and its category.
        if not str(item.get("category") or "").strip():
            raise NotesError(
                "%s: `kind: consolidation` with no `category:` — every M12 "
                "finding carries its taxonomy category" % where)
        if not str(item.get("peers") or "").strip():
            raise NotesError(
                "%s: `kind: consolidation` with no `peers:` — a finding "
                "visible in one procedure alone is out of bounds for the "
                "consolidator (M12 evidence rule: >=2 procedures)" % where)
    return item


def load_items_from(path) -> list[dict]:
    """Items from a notes file at an explicit path (live or archived).

    Absent file → `[]`. An EXISTING file that fails to parse, or parses to a
    non-mapping, raises `NotesError` (M60 Part C): this store holds real
    client input that cannot be regenerated, and returning `[]` for it made
    the NEXT append rewrite the file with only its own items — silent
    permanent erasure. The bus never pretends an unreadable history is an
    empty one. Non-dict entries are dropped; every dict is validated and a
    defect raises."""
    f = Path(path)
    if yaml is None or not f.is_file():
        return []
    try:
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise NotesError(
            f"{f}: existing notes file is not parseable YAML — refusing to "
            f"read it as empty (the accumulated items are client input that "
            f"cannot be regenerated; fix or archive the file): {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise NotesError(
            f"{f}: existing notes file is not a YAML mapping — refusing to "
            f"read it as empty")
    out = []
    for i, it in enumerate((data.get("items") or []), start=1):
        if not isinstance(it, dict):
            continue
        out.append(validate_item(it, "%s: item %d" % (f.name, i)))
    return out


def load_items(area: Path, slug: str) -> list[dict]:
    return load_items_from(Path(area) / "_review" / f"{slug}{NOTES_SUFFIX}")


def append_items(area, slug: str, new_items: list[dict]) -> int:
    """Merge new items into the slug's notes file. Returns how many were
    actually added (exact duplicates are dropped — idempotent re-runs).

    Every incoming item is validated BEFORE anything is read or written, so a
    producer that forgets its `kind` fails loud without leaving a half-written
    queue behind."""
    for i, it in enumerate(new_items or [], start=1):
        validate_item(it, "%s%s: new item %d" % (slug, NOTES_SUFFIX, i))
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
        out = area / "_review" / f"{slug}{NOTES_SUFFIX}"
        out.parent.mkdir(parents=True, exist_ok=True)
        # M60 Part C: never mid-state on disk — the accumulated notes are
        # unrecoverable client input, so the rewrite goes through a same-dir
        # temp file and an atomic os.replace.
        tmp = out.with_name(out.name + ".tmp")
        tmp.write_text(_emit(slug, existing), encoding="utf-8")
        os.replace(tmp, out)
    return added
