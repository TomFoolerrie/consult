#!/usr/bin/env python3
"""orchestrate.py — the CONSULT read-only state advisor (M7).

Given an engagement *area* folder, derive the SINGLE next action from folder
state and print it (``next --area <area> --json``). This script **never
mutates**: it is a pure function of on-disk state, so re-running it is always
safe and idempotent (M7 "Design note"). All state changes happen in the stage
scripts (scaffold/aggregate/reconcile/render) and the subagents' writes; the
driver skill (skills/consult-orchestrate/SKILL.md) performs them.

Precedence (M7 table) — evaluated top to bottom, FIRST MATCH WINS:

  1  confirm          _reference/.proposed/ exists           (HUMAN GATE)
  2  apply_review     _review/*.notes.yaml present
  3  taxonomy         no manifest.json AND _sources/new/*     (mode=initial)
  4  fill             manifest AND any procedure `unfilled`
  5  taxonomy         manifest AND _sources/new/*             (mode=incremental)
  6  aggregate        procedure/registry hash changed vs aggregate state
  7  registry_topup   aggregate emitted unmatched-mention warnings (HUMAN GATE)
  8  reconcile        derived views not clean/current this pass
  9  synthesize       procedures changed vs synthesis basis / pending placeholders
 10  render           all views current+reconciled, no fresh .docx
 11  review           rendered, awaiting human review           (HUMAN GATE)
 12  done             nothing outstanding

The overlap between guards is real (e.g. after scaffold `_sources/new/` is still
full because sources move only after fill) — precedence is what makes the walk
deterministic and non-looping. See M7 "Why the order matters".

STATE FILES (all git-ignored, at the area root) — the advisor only READS these;
the named stage script WRITES each. This is the M7 orchestration contract:

  .aggregate.json  written by aggregate.py:
      {"proc_hashes": {slug: sha}, "registry_hash": sha, "warnings": [ ... ]}
      Records the procedure + registry state aggregate last consumed, plus the
      unmatched-mention WARNINGs it emitted (the registry top-up worklist).
  .hashes.json     written by synthesize (M5 agents' pass / the driver after it):
      {slug: sha}  — the procedure hashes as of the last synthesis. The
      "M5 change signal" (README folder model): synthesize compares against it to
      re-derive only changed procedures.
  .reconcile.json  written by reconcile.py:
      {"basis": sha, "clean": bool}  — the combined hash of procedures+derived+
      manifest at the last reconcile, and whether it passed.
  .render.json     written by the renderer (M4):
      {"basis": sha, "docx": path, "awaiting_review": bool}

If a state file is absent, its stage is treated as never-run (so the guard that
would run it fires). This keeps a fresh area walking forward from zero state.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys

# --- doc_model is OWNED BY M2 (do not create it here) -----------------------
# Prefer the shared spine's load_manifest. Until M2 lands, degrade to a minimal
# json read of manifest.json so the advisor is runnable in isolation; the
# contract is still "import load_manifest from doc_model".
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from doc_model import load_manifest  # type: ignore
except Exception:  # pragma: no cover - fallback only until M2 ships doc_model
    def load_manifest(folder: str) -> dict:
        with open(os.path.join(folder, "manifest.json"), encoding="utf-8") as fh:
            return json.load(fh)


# --------------------------------------------------------------------------- #
# Small filesystem / hashing helpers (deterministic, read-only)
# --------------------------------------------------------------------------- #

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha(path: str) -> str:
    with open(path, "rb") as fh:
        return _sha(fh.read())


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _load_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _dir_has_files(path: str) -> bool:
    """True iff `path` is a directory containing at least one regular file
    (recursively; ignores empty dirs and dotfiles like .gitkeep)."""
    if not os.path.isdir(path):
        return False
    for _root, _dirs, files in os.walk(path):
        for name in files:
            if not name.startswith("."):
                return True
    return False


def resolve_area(area: str) -> str:
    """Accept either a path to the area folder or a bare area name resolved
    under components/. Returns an absolute-ish folder path."""
    if os.path.isdir(area):
        return area.rstrip("/")
    candidate = os.path.join("components", area)
    if os.path.isdir(candidate):
        return candidate
    # Return the components/ candidate anyway so downstream "missing manifest"
    # logic can still fire on a not-yet-created area.
    return candidate


# --------------------------------------------------------------------------- #
# State extraction
# --------------------------------------------------------------------------- #

UNFILLED_RE = re.compile(r"(<!--\s*unfilled\s*-->)|(status\s*:\s*unfilled)", re.I)
PENDING_RE = re.compile(r"_Pending synthesis", re.I)


class AreaState:
    def __init__(self, folder: str):
        self.folder = folder
        self.manifest_path = os.path.join(folder, "manifest.json")
        self.has_manifest = os.path.isfile(self.manifest_path)
        self.manifest = load_manifest(folder) if self.has_manifest else None

        self.proposed_dir = os.path.join(folder, "_reference", ".proposed")
        self.sources_new = os.path.join(folder, "_sources", "new")

        # procedure + derived components from the manifest
        self.procedures = []   # list of (slug, abspath)
        self.agent_derived = []  # abspaths of writer==agent derived files
        self.derived_files = []  # all derived abspaths
        if self.manifest:
            for c in self.manifest.get("components", []):
                path = os.path.join(folder, c["file"])
                role = c.get("role")
                if role == "procedure":
                    self.procedures.append((c.get("slug", c["file"]), path))
                elif role == "derived":
                    self.derived_files.append(path)
                    if c.get("writer") == "agent":
                        self.agent_derived.append(path)

    # ---- guard signals ----------------------------------------------------

    def review_notes(self):
        """Un-archived procedure-anchored review notes (M8). Excludes
        _review/processed/."""
        pat = os.path.join(self.folder, "_review", "*.notes.yaml")
        return sorted(glob.glob(pat))

    def unfilled_slugs(self):
        out = []
        for slug, path in self.procedures:
            if os.path.isfile(path) and UNFILLED_RE.search(_read_text(path)):
                out.append(slug)
        return out

    def proc_hashes(self):
        return {slug: _file_sha(p) for slug, p in self.procedures if os.path.isfile(p)}

    def registry_hash(self):
        ref = os.path.join(self.folder, "_reference")
        parts = []
        for name in sorted(os.listdir(ref)) if os.path.isdir(ref) else []:
            if name.endswith(".yaml"):
                parts.append(name.encode())
                parts.append(_file_sha(os.path.join(ref, name)).encode())
        return _sha(b"|".join(parts))

    def basis_hash(self):
        """Combined hash of procedures + derived files + manifest — the unit
        reconcile and render gate on."""
        parts = []
        for _slug, p in sorted(self.procedures):
            if os.path.isfile(p):
                parts.append(_file_sha(p).encode())
        for p in sorted(self.derived_files):
            if os.path.isfile(p):
                parts.append(_file_sha(p).encode())
        if self.has_manifest:
            parts.append(_file_sha(self.manifest_path).encode())
        return _sha(b"|".join(parts))

    def pending_placeholders(self):
        """Agent-owned derived files still carrying the M3 pending placeholder."""
        out = []
        for p in self.agent_derived:
            if os.path.isfile(p) and PENDING_RE.search(_read_text(p)):
                out.append(os.path.relpath(p, self.folder))
        return out


# --------------------------------------------------------------------------- #
# Decision (the M7 precedence table)
# --------------------------------------------------------------------------- #

def decide(folder: str) -> dict:
    st = AreaState(folder)

    def result(action, reason, gate=False, **details):
        d = {"area": folder, "action": action, "reason": reason,
             "human_gate": gate}
        if details:
            d["details"] = details
        return d

    # 1 — pending proposal outranks everything (never re-scope an edited proposal)
    if _dir_has_files(st.proposed_dir):
        return result(
            "confirm",
            "_reference/.proposed/ exists — human must review/edit, then confirm",
            gate=True,
            proposed_dir=os.path.relpath(st.proposed_dir, folder),
        )

    # 2 — review notes route straight to the drafter (skip taxonomy)
    notes = st.review_notes()
    if notes:
        return result(
            "apply_review",
            "review notes present — dispatch consult-drafter (update) per slug",
            notes=[os.path.relpath(n, folder) for n in notes],
        )

    # 3 — initial scope: no manifest yet, raw sources waiting
    if not st.has_manifest and _dir_has_files(st.sources_new):
        return result("taxonomy",
                      "no manifest and _sources/new/ non-empty",
                      mode="initial")

    if not st.has_manifest:
        return result("done", "no manifest and no sources to scope")

    # 4 — fill: skeletons still stamped `unfilled` (precedes incremental taxonomy
    #     so a freshly-scaffolded area fills rather than re-scoping)
    unfilled = st.unfilled_slugs()
    if unfilled:
        return result("fill",
                      "%d procedure(s) still carry the unfilled sentinel" % len(unfilled),
                      unfilled=unfilled)

    # 5 — incremental scope: new sources arrived after scaffolding
    if _dir_has_files(st.sources_new):
        return result("taxonomy",
                      "manifest exists and _sources/new/ non-empty (no unfilled)",
                      mode="incremental")

    # ---- steady-state derived pipeline (needs real procedures) ----
    if not st.procedures:
        return result("done", "no procedures in manifest")

    cur_proc = st.proc_hashes()
    cur_reg = st.registry_hash()

    # 6 — aggregate: procedures or registry changed since the last aggregate.
    agg = _load_json(os.path.join(folder, ".aggregate.json")) or {}
    agg_stale = (agg.get("proc_hashes") != cur_proc
                 or agg.get("registry_hash") != cur_reg)
    if agg_stale:
        return result("aggregate",
                      "procedure/registry content changed since last aggregate")

    # 7 — registry top-up: aggregate flagged unmatched consult-meta slugs
    warnings = agg.get("warnings") or []
    if warnings:
        return result("registry_topup",
                      "aggregate emitted %d unmatched-mention warning(s)" % len(warnings),
                      gate=True,
                      warnings=warnings)

    # 8 — reconcile: derived views not verified against current basis this pass
    basis = st.basis_hash()
    rec = _load_json(os.path.join(folder, ".reconcile.json")) or {}
    if rec.get("basis") != basis or not rec.get("clean"):
        return result("reconcile",
                      "derived views changed or not yet reconciled clean this pass")

    # 9 — synthesize: judgment views stale vs the changed procedures
    synth_basis = _load_json(os.path.join(folder, ".hashes.json")) or {}
    pending = st.pending_placeholders()
    if pending or synth_basis != cur_proc:
        return result("synthesize",
                      "judgment views stale vs changed procedures",
                      pending=pending)

    # 10 — render: everything current + reconciled, no fresh docx
    ren = _load_json(os.path.join(folder, ".render.json")) or {}
    if ren.get("basis") != basis:
        return result("render", "views current and reconciled; no fresh .docx")

    # 11 — review: rendered, awaiting human sign-off (resting gate)
    if ren.get("awaiting_review"):
        return result("review",
                      "rendered; awaiting human review of the .docx",
                      gate=True,
                      docx=ren.get("docx"))

    # 12 — nothing outstanding
    return result("done", "all views current, reconciled, rendered and reviewed",
                  docx=ren.get("docx"))


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_next = sub.add_parser("next", help="print the single next action")
    p_next.add_argument("--area", required=True,
                        help="area folder path or bare area name under components/")
    p_next.add_argument("--json", action="store_true",
                        help="emit JSON (default; kept for explicitness)")
    args = parser.parse_args(argv)

    if args.cmd == "next":
        folder = resolve_area(args.area)
        decision = decide(folder)
        print(json.dumps(decision, indent=2, sort_keys=False))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
