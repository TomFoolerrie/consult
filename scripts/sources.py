#!/usr/bin/env python3
"""sources.py — the input-move helper the orchestrator calls (M7).

Two mutating operations the driver skill invokes AFTER a stage succeeds; kept
out of the read-only advisor (orchestrate.py) and out of M0's scaffold:

  mark-processed <area> --filled <slugs...>
      Move each source whose ENTIRE `touches` set ⊆ the successfully-filled
      slugs from _sources/new/ → _sources/processed/, and flip its state in
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

This module also OWNS `_reference/sources.yaml` as a contract (M22 check 2): the
`touches` ⊆ manifest-procedure-slugs validator and the SRC- id registry read live
here, and `reconcile.py` imports them, so the load-time gate and the QC gate
report the identical defect. F14: one typo'd `touches` slug makes a source
permanently unretirable (`touches` never becomes a subset of the filled slugs),
so guard 5 re-fires `taxonomy` forever — it is named here the first time any
stage reads the file.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys

import yaml


class SourcesError(Exception):
    """A fail-loud defect in _reference/sources.yaml (never a warning)."""


def resolve_area(area: str) -> str:
    if os.path.isdir(area):
        return area.rstrip("/")
    candidate = os.path.join("components", area)
    return candidate if os.path.isdir(candidate) else area.rstrip("/")


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
    validate against" and say so, rather than failing every citation."""
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
# mark-processed
# --------------------------------------------------------------------------- #

def mark_processed(folder: str, filled: set) -> int:
    try:
        data = _load_sources(folder)
    except SourcesError as exc:
        # Fail loud at the source: nothing moves, nothing is flipped, exit 1.
        print("ERROR: %s" % exc, file=sys.stderr)
        return 1
    processed_dir = os.path.join(folder, "_sources", "processed")
    os.makedirs(processed_dir, exist_ok=True)

    moved, kept = [], []
    for entry in data["sources"]:
        if entry.get("state") == "processed":
            continue
        touches = set(entry.get("touches") or [])
        # Empty touches never auto-moves: a source informing no procedure has
        # nothing to "fully consume", so it stays outstanding for a human.
        if touches and touches <= filled:
            src = _source_relpath(entry, folder, "new")
            dest = os.path.join(processed_dir, os.path.basename(src))
            if os.path.isfile(src):
                shutil.move(src, dest)
            entry["state"] = "processed"
            entry["file"] = os.path.relpath(dest, folder)
            moved.append(entry.get("id", os.path.basename(dest)))
        else:
            kept.append(entry.get("id"))

    _dump_sources(folder, data)
    print("moved %d source(s) → processed: %s" % (len(moved), ", ".join(moved) or "-"))
    if kept:
        print("kept %d source(s) in new/ (touches not fully filled): %s"
              % (len(kept), ", ".join(str(k) for k in kept)))
    return 0


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
                      help="slugs whose fill succeeded this batch")

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
        return mark_processed(folder, set(args.filled))
    if args.cmd == "archive-review":
        return archive_review(folder, args.slugs, args.docx)
    return 2


if __name__ == "__main__":
    sys.exit(main())
