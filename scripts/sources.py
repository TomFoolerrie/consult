#!/usr/bin/env python3
"""sources.py — the input-move helper the orchestrator calls (M7).

Two mutating operations the driver skill invokes AFTER a stage succeeds; kept
out of the read-only advisor (orchestrate.py) and out of M0's scaffold:

  mark-processed <area> [--filled <slugs...>] [--updated <slugs...>]
      Move each source whose ENTIRE `touches` set has been CONSUMED from
      _sources/new/ → _sources/processed/, and flip its state in
      _reference/sources.yaml to `processed`. Per-source consumption (M7 r3
      review #10): a source touching an unfilled/failed procedure stays in
      new/ ("still outstanding"), so the next pass re-dispatches only the
      remaining procedures.

  archive-review <area> [--slugs <slugs...>] [--docx <path>]
      Move applied _review/<slug>.notes.yaml → _review/processed/ after an
      apply_review batch succeeds. With no --slugs, archives every
      _review/*.notes.yaml. Optionally also archives the consumed .docx.

Never called by hand and never by a subagent — the orchestrator owns moves so a
source is moved only once its fill has actually succeeded.

CONSUMPTION IS KIND-AWARE AND CROSS-BATCH (M6). Two ways a slug is credited
toward a source, and one durable record:

  * `--filled <slug>`  — a FIRST-DRAFT fill batch. The `fill` dispatch carries
    the slug's whole tagged source list, so a successful fill consumed every
    source that `touches` it: credit is unconditional.
  * `--updated <slug>` (or no flag at all) — an UPDATE batch. Credit requires
    EVIDENCE: the slug's consumed notes must carry a `kind: source` item naming
    this source's id. A reviewer comment, a rename note or a consolidation
    finding on the same procedure credits nothing, so it can never retire a
    source no drafter read (M6's bus contract, rule 3). The evidence is the
    ARCHIVED note (`_review/processed/{slug}.notes.yaml`) — a note reaches the
    archive only after its drafter batch succeeded. `--updated` additionally
    trusts the still-live note, for a driver that credits before it archives.
  * `consumed: [slug, ...]` on each source entry — the durable per-slug record,
    accumulated here and never reset. It is what makes the accounting
    CROSS-BATCH: a source touching {new procedure A, existing procedure B} is
    credited B by an `apply_review` batch and A by a `fill` batch, in either
    order and any number of passes apart, and retires when the union covers
    `touches`. It is also the DEDUPE TRACE: `scaffold.py` reads it at the
    confirm gate and never re-notifies a procedure already consumed for that
    SRC- id.

This module also OWNS `_reference/sources.yaml` as a contract (M22 check 2): the
`touches` ⊆ manifest-procedure-slugs validator and the SRC- id registry read live
here, and `reconcile.py` imports them, so the load-time gate and the QC gate
report the identical defect. F14: one typo'd `touches` slug makes a source
permanently unretirable (`touches` never becomes a subset of the filled slugs),
so guard 5 re-fires `taxonomy` forever — it is named here the first time any
stage reads the file.

CENTRAL MODE (M34). An engagement whose ROOT carries `_sources/sources.yaml` keeps
its sources once, at that root, and areas hold only consumption records. There is
exactly ONE detection seam — `central_root(folder)`, which walks up from an area
looking for that file — and the three source questions below (`registered_ids`,
`assess_new_sources`, `mark_processed`) branch on it once, at the top, delegating
to `ledger.py` (which owns the central layout) and otherwise running the v1 path
BYTE-IDENTICALLY. No consumer may test file positions to decide mode. `ledger` is
imported lazily and defensively: a missing module leaves v1 mode fully working.
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
import hashlib
import json
import os
import shutil
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import yaml

# notes_util owns the `_review/{slug}.notes.yaml` shape (the M6 bus). The join
# "which SRC- ids did this slug's consumed notes name" lives here, because the
# ACCOUNTING is this module's business; the file shape is not.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from notes_util import NOTES_SUFFIX, NotesError, load_items_from  # noqa: E402


class SourcesError(Exception):
    """A fail-loud defect in _reference/sources.yaml (never a warning)."""


def resolve_area(area: str) -> str:
    if os.path.isdir(area):
        return area.rstrip("/")
    candidate = os.path.join("components", area)
    return candidate if os.path.isdir(candidate) else area.rstrip("/")


# --------------------------------------------------------------------------- #
# The ONE central-mode detection seam (M34)
# --------------------------------------------------------------------------- #

CENTRAL_LEDGER_REL = os.path.join("_sources", "sources.yaml")


def central_root(folder: str) -> str | None:
    """The engagement root holding the M34 ledger, or None for a v1 area.

    Walks UP from `folder` (itself included) looking for `_sources/sources.yaml`.
    That file's existence IS the mode marker — the single question every consumer
    asks, so nothing else has to guess from file positions. None means v1: the
    area owns its own `_reference/sources.yaml` and `_sources/` tree, and every
    function below runs exactly the code it ran before M34.
    """
    try:
        current = os.path.abspath(os.path.realpath(folder))
    except OSError:
        return None
    while True:
        if os.path.isfile(os.path.join(current, CENTRAL_LEDGER_REL)):
            return current
        parent = os.path.dirname(current)
        if parent == current:            # filesystem root reached
            return None
        current = parent


def _ledger():
    """The ledger module, or None when it is not importable.

    Imported here rather than at module scope for two reasons: `ledger` imports
    THIS module (for `_hash_file`/`_slug_list`), and v1 mode must keep working in
    a tree that has no ledger.py at all."""
    try:
        import ledger                    # noqa: PLC0415  (deliberately lazy)
    except ImportError:
        return None
    return ledger


def _sources_yaml_path(folder: str) -> str:
    return os.path.join(folder, "_reference", "sources.yaml")


def _load_sources(folder: str) -> dict:
    path = _sources_yaml_path(folder)
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if "sources" not in data or data["sources"] is None:
        data["sources"] = []
    errs = touches_errors(folder, data)
    if errs:
        raise SourcesError("; ".join(errs))
    return data


# --------------------------------------------------------------------------- #
# sources.yaml as a contract (M22 check 2)
# --------------------------------------------------------------------------- #

def registered_ids(folder: str) -> set[str]:
    """The SRC- ids registered in _reference/sources.yaml.

    Empty set when the file is absent, unreadable, or registers nothing — the
    callers (reconcile's citation check) treat "no registry" as "nothing to
    validate against" and say so, rather than failing every citation.

    In central mode the registry is the engagement-root ledger, so the ids are
    engagement-global (plain `SRC-nnn`, one minter) — citations validate against
    exactly the same set of strings, one scope up."""
    ledger = _ledger()
    root = central_root(folder) if ledger is not None else None
    if root is not None:
        try:
            return {str(e.get("id") or "").strip()
                    for e in ledger.entries(root)
                    if str(e.get("id") or "").strip()}
        except ledger.LedgerError:
            return set()                 # v1's posture: no readable registry
    path = _sources_yaml_path(folder)
    if not os.path.isfile(path):
        return set()
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except yaml.YAMLError:
        return set()
    out = set()
    for entry in (data.get("sources") or []) if isinstance(data, dict) else []:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            out.add(entry["id"].strip())
    return out


def manifest_procedure_slugs(folder: str) -> set[str] | None:
    """Procedure slugs from manifest.json, or None when there is no readable
    manifest.

    None is the documented BOUNDARY for the `touches` check: during initial
    scoping `consult-taxonomy` writes sources.yaml (with its `touches` tags)
    BEFORE scaffold writes manifest.json, so for that window there is no
    authority to validate against and the check must no-op rather than reject
    every tag. An unreadable manifest is reported by reconcile/doc_model, not
    twice here."""
    path = os.path.join(folder, "manifest.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            manifest = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(manifest, dict):
        return None
    return {c.get("slug") for c in manifest.get("components") or []
            if isinstance(c, dict) and c.get("role") == "procedure"
            and isinstance(c.get("slug"), str)}


def touches_errors(folder: str, data: dict | None = None) -> list[str]:
    """`touches` ⊆ manifest procedure slugs — the single implementation.

    Returns [] when sources.yaml is absent/unreadable or when no manifest exists
    yet (see manifest_procedure_slugs). Called at load time (fail loud at the
    source) and by reconcile (fail loud at the gate)."""
    slugs = manifest_procedure_slugs(folder)
    if slugs is None:
        return []
    if data is None:
        path = _sources_yaml_path(folder)
        if not os.path.isfile(path):
            return []
        try:
            with open(path, encoding="utf-8") as fh:
                data = yaml.safe_load(fh) or {}
        except yaml.YAMLError:
            return []
    if not isinstance(data, dict):
        return []

    rel = "_reference/sources.yaml"      # message path: stable, not os-specific
    errs: list[str] = []
    for entry in data.get("sources") or []:
        if not isinstance(entry, dict):
            continue
        sid = entry.get("id", "?")
        touches = entry.get("touches") or []
        if isinstance(touches, str):
            errs.append(f"{rel}: {sid} `touches` must be a list of procedure "
                        f"slugs, got a string")
            continue
        for slug in touches:
            if slug not in slugs:
                errs.append(
                    f"{rel}: {sid} touches {slug!r} which is not a manifest "
                    f"procedure slug (unretirable source — F14)"
                )
    return errs


def _read_sources_tolerant(folder: str) -> list[dict]:
    """The registered source entries, or [] — never raises.

    The tolerant twin of `_load_sources`, for the READ-ONLY callers (the advisor
    is a total function: a malformed registry must not make `next` explode, it
    must read as "nothing is assessed" and route to taxonomy)."""
    path = _sources_yaml_path(folder)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
    except (yaml.YAMLError, OSError):
        return []
    if not isinstance(data, dict):
        return []
    return [e for e in (data.get("sources") or []) if isinstance(e, dict)]


def _slug_list(value) -> list[str]:
    """A `touches`/`consumed` value as a list of slugs (a bare string counts as
    one; reconcile/`touches_errors` reports the shape defect separately)."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    try:
        return [str(v) for v in value]
    except TypeError:
        return []


def _dump_sources(folder: str, data: dict) -> None:
    path = _sources_yaml_path(folder)
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True)


def _source_relpath(entry: dict, folder: str, subdir: str) -> str:
    """Return the on-disk path for a source `entry`, honouring its recorded
    `file` (relative to the area) but falling back to <subdir>/<basename>."""
    recorded = entry.get("file")
    if recorded:
        p = os.path.join(folder, recorded)
        if os.path.isfile(p):
            return p
        # recorded path stale (e.g. still points at new/): fall back to basename
        return os.path.join(folder, "_sources", subdir, os.path.basename(recorded))
    return os.path.join(folder, "_sources", subdir, str(entry.get("id", "")))


# --------------------------------------------------------------------------- #
# mark-processed — the kind-aware retirement accounting (M6)
# --------------------------------------------------------------------------- #

CONSUMED_KEY = "consumed"


def note_src_ids(folder: str, slug: str, include_pending: bool = False) -> set[str]:
    """The SRC- ids named by `kind: source` items in a slug's CONSUMED notes.

    Consumption is the ARCHIVE: `_review/processed/{slug}.notes.yaml` exists only
    because an `apply_review` batch succeeded (the driver archives after success,
    exactly as it passes `--filled` only for fills that succeeded), so it is the
    durable evidence that a drafter read this source for this slug. A LIVE
    `_review/{slug}.notes.yaml` is PENDING, not consumed — read only when the
    caller explicitly asserts the slug's update succeeded (`--updated <slug>`,
    for a driver that credits before it archives).

    Items of any other kind contribute nothing: that is the whole point of the
    bus contract (a reviewer comment must never retire a source)."""
    paths = [os.path.join(folder, "_review", "processed", slug + NOTES_SUFFIX)]
    if include_pending:
        paths.append(os.path.join(folder, "_review", slug + NOTES_SUFFIX))
    out: set[str] = set()
    for p in paths:
        for item in load_items_from(p):
            if item.get("kind") == "source":
                sid = str(item.get("src") or "").strip()
                if sid:
                    out.add(sid)
    return out


def mark_processed(folder: str, filled: set, updated: set | None = None) -> int:
    """Credit this area's consumption and retire whatever is now fully read.

    Central mode delegates to `ledger.credit(root, area, ...)` with the same
    filled/updated sets — same evidence rules, same `_review/processed/` notes
    read for `--updated` — and the same CLI posture (0 on success; a LedgerError
    prints ERROR to stderr and returns 1, nothing moved). The move rule is one
    scope up: a file leaves the ROOT `_sources/new/` only when EVERY area's
    touches are covered, so one area's mark cannot retire a source another area
    still owes a read."""
    ledger = _ledger()
    root = central_root(folder) if ledger is not None else None
    if root is not None:
        area = os.path.basename(folder.rstrip("/").rstrip(os.sep))
        try:
            moved = ledger.credit(root, area, filled=sorted(filled or ()),
                                  updated=sorted(updated or ()))
        except ledger.LedgerError as exc:
            print("ERROR: %s" % exc, file=sys.stderr)
            return 1
        print("moved %d source(s) → processed (ledger: %s)" % (moved, area))
        return 0
    try:
        data = _load_sources(folder)
    except SourcesError as exc:
        # Fail loud at the source: nothing moves, nothing is flipped, exit 1.
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1
    filled = set(filled or ())
    updated_set = None if updated is None else set(updated)
    processed_dir = os.path.join(folder, "_sources", "processed")

    evidence: dict[str, set[str]] = {}

    def credits(slug: str) -> set[str]:
        """Memoized per-slug note evidence (read once per slug, not per source)."""
        if slug not in evidence:
            pending = updated_set is not None and slug in updated_set
            evidence[slug] = note_src_ids(folder, slug, include_pending=pending)
        return evidence[slug]

    # Pass 1 — READ ONLY: work out what each outstanding source has consumed.
    # All note reads happen here, before any file is moved, so a malformed note
    # on the bus leaves the area exactly as it was (nothing moved, nothing
    # written) instead of half-retiring an earlier entry.
    outstanding = []
    try:
        for entry in data["sources"]:
            if entry.get("state") == "processed":
                continue
            sid = str(entry.get("id") or "").strip()
            touches = _slug_list(entry.get("touches"))
            # The durable record: everything credited in any earlier batch.
            consumed = {s for s in _slug_list(entry.get(CONSUMED_KEY))
                        if s in touches}
            for slug in touches:
                if slug in consumed:
                    continue
                if slug in filled:
                    consumed.add(slug)          # first-draft fill: unconditional
                elif sid and sid in credits(slug):
                    consumed.add(slug)          # update: kind:source evidence
            outstanding.append((entry, touches, consumed))
    except NotesError as exc:
        # A malformed note on the bus is a defect, not a warning: nothing moves.
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1

    # Pass 2 — MUTATE: record the credit, and retire whatever is fully consumed.
    os.makedirs(processed_dir, exist_ok=True)
    moved, kept = [], []
    for entry, touches, consumed in outstanding:
        if consumed:
            entry[CONSUMED_KEY] = sorted(consumed)
        elif CONSUMED_KEY in entry:
            # `touches` was edited at a confirm gate and no longer names anything
            # credited: the record follows `touches`, so a slug the human re-adds
            # later is genuinely re-dispatched.
            entry[CONSUMED_KEY] = []
        # Empty touches never auto-moves: a source informing no procedure has
        # nothing to "fully consume", so it stays outstanding for a human.
        if touches and set(touches) <= consumed:
            src = _source_relpath(entry, folder, "new")
            dest = os.path.join(processed_dir, os.path.basename(src))
            if os.path.isfile(src):
                shutil.move(src, dest)
                # M25: the intake pointer sidecar retires with its source, so
                # a lone sidecar can never keep _sources/new/ "non-empty".
                side = src + ROUTE_SIDECAR_SUFFIX
                if os.path.isfile(side):
                    shutil.move(side, dest + ROUTE_SIDECAR_SUFFIX)
            entry["state"] = "processed"
            entry["file"] = os.path.relpath(dest, folder)
            moved.append(entry.get("id", os.path.basename(dest)))
        else:
            kept.append("%s [%d/%d consumed]"
                        % (entry.get("id"), len(consumed), len(touches)))

    _dump_sources(folder, data)
    print("moved %d source(s) → processed: %s" % (len(moved), ", ".join(moved) or "-"))
    if kept:
        print("kept %d source(s) in new/ (touches not fully consumed): %s"
              % (len(kept), ", ".join(str(k) for k in kept)))
    return 0


# --------------------------------------------------------------------------- #
# assess-new — the advisor's guard-5 discriminator (M6, read-only)
# --------------------------------------------------------------------------- #

def _hash_file(path: str) -> str:
    try:
        with open(path, "rb") as fh:
            return hashlib.sha256(fh.read()).hexdigest()
    except OSError:
        return ""


#: M25 intake pointer sidecars (`<copy>.route.md`) beside a routed source:
#: routing metadata, never a source — excluded from assessment, folded into
#: the entry's `note:` by scaffold's stamp_sources, retired with the source.
ROUTE_SIDECAR_SUFFIX = ".route.md"


def new_source_files(folder: str) -> list[str]:
    """Area-relative paths of the real files in `_sources/new/`.

    Same walk as the advisor's `_dir_has_files`: recursive, dotfiles ignored, so
    "the folder is non-empty" and "these are the files" can never disagree.
    M25 route sidecars are metadata, not sources — skipped."""
    root = os.path.join(folder, "_sources", "new")
    out = []
    for base, _dirs, names in os.walk(root):
        for name in names:
            if name.startswith(".") or name.endswith(ROUTE_SIDECAR_SUFFIX):
                continue
            rel = os.path.relpath(os.path.join(base, name), folder)
            out.append(rel.replace(os.sep, "/"))
    return sorted(out)


def assess_new_sources(folder: str) -> tuple[list[str], list[dict]]:
    """`(unassessed, assessed)` for `_sources/new/` — a pure read.

    THE DISCRIMINATOR IS `sources.yaml` (M6). A file in `new/` is **unassessed**
    when the registry does not know it, or knows it at a different hash: the
    taxonomy agent has never read *these bytes*, so `taxonomy` (incremental) has
    real work. A file the registry knows at the current hash is **assessed** —
    the agent has already read it and proposed what it implies, so re-dispatching
    taxonomy over it proposes nothing new and re-spends a dispatch per lap
    (audit F7). Whether anything can still CONSUME an assessed source is the
    advisor's question, not this function's; by the time guard 5 is reached the
    higher guards have already ruled out pending notes and unfilled skeletons.

    `assessed` entries are message material for the gate: `{id, file, touches,
    consumed, state}`.

    In central mode the staging folder is the ROOT `_sources/new/` and the
    discriminator is the ledger: `ledger.assess` asks the identical question with
    the identical rules, at engagement scope."""
    ledger = _ledger()
    root = central_root(folder) if ledger is not None else None
    if root is not None:
        return ledger.assess(root)
    files = new_source_files(folder)
    if not files:
        return [], []

    entries = _read_sources_tolerant(folder)
    by_rel: dict[str, dict] = {}
    base_count: dict[str, int] = {}
    for entry in entries:
        rel = str(entry.get("file") or "").replace(os.sep, "/").lstrip("./")
        if not rel:
            continue
        by_rel.setdefault(rel, entry)
        base = os.path.basename(rel)
        base_count[base] = base_count.get(base, 0) + 1
    # A recorded path can be stale (it still says new/ after a move, or vice
    # versa), so fall back to the basename — but only when it is unambiguous.
    by_base = {}
    for entry in entries:
        rel = str(entry.get("file") or "").replace(os.sep, "/").lstrip("./")
        base = os.path.basename(rel) if rel else ""
        if base and base_count.get(base) == 1:
            by_base.setdefault(base, entry)

    unassessed, assessed = [], []
    for rel in files:
        entry = by_rel.get(rel) or by_base.get(os.path.basename(rel))
        recorded = str((entry or {}).get("hash") or "").strip()
        # Unregistered / never stamped is decided WITHOUT hashing: the common
        # case is a fresh transcript the advisor sees on every `next` call, and
        # sources can be large binaries.
        if not recorded:
            unassessed.append(rel)
            continue
        if recorded != _hash_file(os.path.join(folder, rel)):
            unassessed.append(rel)
            continue
        assessed.append({
            "id": str(entry.get("id") or "?"),
            "file": rel,
            "touches": _slug_list(entry.get("touches")),
            "consumed": _slug_list(entry.get(CONSUMED_KEY)),
            "state": entry.get("state"),
        })
    return unassessed, assessed


# --------------------------------------------------------------------------- #
# archive-review
# --------------------------------------------------------------------------- #

def archive_review(folder: str, slugs, docx: str | None) -> int:
    review_dir = os.path.join(folder, "_review")
    processed_dir = os.path.join(review_dir, "processed")
    os.makedirs(processed_dir, exist_ok=True)

    if slugs:
        notes = [os.path.join(review_dir, "%s.notes.yaml" % s) for s in slugs]
    else:
        notes = [os.path.join(review_dir, f) for f in sorted(os.listdir(review_dir))
                 if f.endswith(".notes.yaml") and os.path.isfile(os.path.join(review_dir, f))]

    archived = []
    for n in notes:
        if os.path.isfile(n):
            shutil.move(n, os.path.join(processed_dir, os.path.basename(n)))
            archived.append(os.path.basename(n))

    if docx and os.path.isfile(docx):
        shutil.move(docx, os.path.join(processed_dir, os.path.basename(docx)))
        archived.append(os.path.basename(docx))

    print("archived %d review artifact(s): %s"
          % (len(archived), ", ".join(archived) or "-"))
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_mp = sub.add_parser("mark-processed",
                          help="move fully-consumed sources new/ → processed/")
    p_mp.add_argument("area")
    p_mp.add_argument("--filled", nargs="*", default=[],
                      help="slugs whose FIRST-DRAFT fill succeeded this batch "
                           "(credits every source that touches them)")
    p_mp.add_argument("--updated", nargs="*", default=None,
                      help="slugs whose UPDATE batch succeeded this pass "
                           "(credits a source only where the slug's notes "
                           "carried a kind: source item naming it). Optional: "
                           "archived notes are always read as evidence.")

    p_ar = sub.add_parser("archive-review",
                          help="move applied review notes → _review/processed/")
    p_ar.add_argument("area")
    p_ar.add_argument("--slugs", nargs="*", default=None,
                      help="slugs whose notes were applied (default: all notes)")
    p_ar.add_argument("--docx", default=None,
                      help="optional consumed .docx to archive too")

    args = parser.parse_args(argv)
    folder = resolve_area(args.area)

    if args.cmd == "mark-processed":
        return mark_processed(folder, set(args.filled),
                              None if args.updated is None else set(args.updated))
    if args.cmd == "archive-review":
        return archive_review(folder, args.slugs, args.docx)
    return 2


if __name__ == "__main__":
    sys.exit(main())
