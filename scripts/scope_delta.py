#!/usr/bin/env python3
"""scope_delta.py — content-hash change signal for M5 judgment agents.

Single mechanism, no git-diff path (M5 review #15): a per-derived-file baseline
of the procedure content hashes each agent-owned file was last built from, stored
in ``.hashes.json`` (git-ignored). The changed-procedure set for a given derived
file is every procedure whose current content hash differs from — or is absent
from — that baseline. First run (no baseline for the kind) => every procedure is
"changed".

This module produces the M5 work order dict::

    {
      "derived_kind": "dependencies" | "raci",
      "changed_procedure_slugs": [<slug>, ...],
      "bundle_path": "<folder>/<area>.extract.json"
    }

It deliberately does **not** include the agent's prior file contents: the agent
has Read and pulls its own prior file from disk (review #11), so the orchestrator
never lifts a derived draft into its context (r3 review #13).

After a successful agent write, :func:`commit` rebaselines ``.hashes.json`` for
that derived kind to the current procedure hashes.

Manifest / procedure enumeration is delegated to ``doc_model.py`` (owned by M2);
this module imports it rather than re-parsing the manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)
from typing import Dict, List

# doc_model.py lives beside this file in scripts/ (M2-owned). Import it for
# manifest load + procedure enumeration; never re-implement that here.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import doc_model  # noqa: E402  (path set above)

HASHES_FILENAME = ".hashes.json"

# derived_kind values M5 owns. Mechanical (python-owned) kinds are not tracked
# here — only the agent-owned judgment files carry a hash baseline.
#
# M36 WP-G2: this pair is v1's, and it is now what the DEFINITION says rather
# than a fact about this module — `agent_derived_kinds(folder)` asks the area's
# compiled plan which view blocks carry `writer: agent`. The shipped
# desktop-procedure definition names exactly these two, in this order, so v1
# areas are unaffected; the constant remains as the fallback for an area whose
# definition cannot be resolved (stripped install, no/invalid definition).
AGENT_DERIVED_KINDS = ("dependencies", "raci")


def agent_derived_kinds(folder=None) -> tuple:
    """The agent-owned derived kinds of this area's deliverable, plan order.

    Best-effort and read-only: any failure to resolve or compile the definition
    falls back to `AGENT_DERIVED_KINDS` (documented above), so this never turns a
    baseline read into a crash."""
    if folder is None:
        return AGENT_DERIVED_KINDS
    try:
        import definitions
        defn = definitions.resolve_definition(folder)
        plan = definitions.compile_plan(defn, folder)
    except Exception:
        return AGENT_DERIVED_KINDS
    kinds = tuple(v.kind for v in plan.views if v.writer == "agent")
    return kinds or AGENT_DERIVED_KINDS


# --------------------------------------------------------------------------- #
# Manifest / procedure access (thin wrappers over doc_model)
# --------------------------------------------------------------------------- #

def _load_manifest(folder: str) -> dict:
    """Load the area manifest via doc_model, tolerating minor API naming."""
    for fn_name in ("load_manifest", "read_manifest"):
        fn = getattr(doc_model, fn_name, None)
        if callable(fn):
            return fn(folder)
    raise AttributeError(
        "doc_model exposes no load_manifest()/read_manifest(); cannot enumerate "
        "procedures"
    )


def _procedure_components(folder: str) -> List[dict]:
    """Return the manifest components with role == 'procedure', in manifest order.

    Prefers a doc_model helper if one exists; otherwise filters the manifest's
    ``components`` list directly (the v1 schema documented in docs/README.md).
    """
    getter = getattr(doc_model, "procedures", None)
    if callable(getter):
        return list(getter(_load_manifest(folder)))
    manifest = _load_manifest(folder)
    components = manifest.get("components", [])
    return [c for c in components if c.get("role") == "procedure"]


def _area(folder: str) -> str:
    manifest = _load_manifest(folder)
    return manifest.get("area") or os.path.basename(os.path.abspath(folder))


# --------------------------------------------------------------------------- #
# Content hashing
# --------------------------------------------------------------------------- #

def _content_hash(path: str) -> str:
    """SHA-256 of a procedure file's bytes.

    Hashing the file bytes (not the assembled/numbered text) means a manifest-only
    reorder — which changes ``order``/``l2_order`` but no procedure file — produces
    no hash change and therefore no synthesis work (M5 acceptance: reorder-staleness
    closed; numbers are resolved at render, M4).
    """
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def procedure_hashes(folder: str) -> Dict[str, str]:
    """{slug: content_hash} for every current procedure in the area.

    A procedure whose file is missing on disk is simply absent from the map (it
    was deleted); its judgment rows are the agent's / M3's concern, not ours.
    """
    result: Dict[str, str] = {}
    for comp in _procedure_components(folder):
        slug = comp.get("slug")
        rel = comp.get("file")
        if not slug or not rel:
            continue
        path = os.path.join(folder, rel)
        if not os.path.isfile(path):
            continue
        result[slug] = _content_hash(path)
    return result


# --------------------------------------------------------------------------- #
# .hashes.json baseline
# --------------------------------------------------------------------------- #

def _hashes_path(folder: str) -> str:
    return os.path.join(folder, HASHES_FILENAME)


def load_baseline(folder: str) -> Dict[str, Dict[str, str]]:
    """Load ``.hashes.json`` => {derived_kind: {slug: hash}}. Missing file => {}."""
    path = _hashes_path(folder)
    if not os.path.isfile(path):
        return {}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


def _save_baseline(folder: str, baseline: Dict[str, Dict[str, str]]) -> None:
    path = _hashes_path(folder)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(baseline, fh, indent=2, sort_keys=True)
        fh.write("\n")


# --------------------------------------------------------------------------- #
# Delta + work order
# --------------------------------------------------------------------------- #

def changed_procedure_slugs(folder: str, derived_kind: str) -> List[str]:
    """Procedures whose current hash differs from / is absent in the baseline.

    First run for the kind (no baseline entry) => all current procedures. Result
    is sorted for deterministic work orders.
    """
    current = procedure_hashes(folder)
    prior = load_baseline(folder).get(derived_kind)
    if prior is None:  # first run for this derived kind
        return sorted(current)
    changed = [
        slug
        for slug, h in current.items()
        if prior.get(slug) != h  # differs or absent
    ]
    return sorted(changed)


def bundle_path(folder: str) -> str:
    """Path to M3's extract bundle for this area (scratch JSON, git-ignored)."""
    return os.path.join(folder, f"{_area(folder)}.extract.json")


def work_order(folder: str, derived_kind: str) -> dict:
    """Build the M5 work order dict for one agent-owned derived file.

    NOTE: intentionally carries NO prior_file_contents — the agent reads its own
    prior file from disk (review #11/#13).
    """
    known = agent_derived_kinds(folder)
    if derived_kind not in known:
        raise ValueError(
            f"unknown derived_kind {derived_kind!r}; "
            f"expected one of {known}"
        )
    return {
        "derived_kind": derived_kind,
        "changed_procedure_slugs": changed_procedure_slugs(folder, derived_kind),
        "bundle_path": bundle_path(folder),
    }


def commit(folder: str, derived_kind: str) -> Dict[str, str]:
    """Rebaseline ``.hashes.json`` for ``derived_kind`` to current procedure hashes.

    Call after the agent has successfully written its file. Returns the new
    per-kind {slug: hash} map. Other kinds' baselines are left untouched.
    """
    known = agent_derived_kinds(folder)
    if derived_kind not in known:
        raise ValueError(
            f"unknown derived_kind {derived_kind!r}; "
            f"expected one of {known}"
        )
    baseline = load_baseline(folder)
    current = procedure_hashes(folder)
    baseline[derived_kind] = current
    _save_baseline(folder, baseline)
    return current


# --------------------------------------------------------------------------- #
# CLI (invoked by consult-orchestrate, M7)
# --------------------------------------------------------------------------- #

def _cmd_work_order(args: argparse.Namespace) -> int:
    print(json.dumps(work_order(args.folder, args.kind), indent=2))
    return 0


def _cmd_commit(args: argparse.Namespace) -> int:
    current = commit(args.folder, args.kind)
    print(
        json.dumps(
            {"derived_kind": args.kind, "procedures_baselined": len(current)},
            indent=2,
        )
    )
    return 0


def _cmd_changed(args: argparse.Namespace) -> int:
    print(json.dumps(changed_procedure_slugs(args.folder, args.kind), indent=2))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = p.add_subparsers(dest="command", required=True)

    def _add_common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--folder", required=True, help="the area folder")
        sp.add_argument(
            "--kind",
            required=True,
            choices=list(AGENT_DERIVED_KINDS),
            help="agent-owned derived kind",
        )

    wo = sub.add_parser("work-order", help="emit the M5 work order dict as JSON")
    _add_common(wo)
    wo.set_defaults(func=_cmd_work_order)

    cm = sub.add_parser(
        "commit", help="rebaseline .hashes.json after a successful agent write"
    )
    _add_common(cm)
    cm.set_defaults(func=_cmd_commit)

    ch = sub.add_parser("changed", help="print the changed-procedure slug list")
    _add_common(ch)
    ch.set_defaults(func=_cmd_changed)

    return p


def main(argv: List[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
