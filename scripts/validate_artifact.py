#!/usr/bin/env python3
"""validate_artifact.py — deterministic validator for classify artifacts (Stage 2).

A classifier sub-agent (skills/consult-classifier) reads one ingested MD and
emits a per-doc artifact (schemas/classify_artifact.schema.json). Before the
merge (T12) trusts an artifact, this validator runs four checks:

  1. JSON-Schema validation against classify_artifact.schema.json (shape).
  2. Every node_hit.node exists in reference/taxonomy.yaml (the schema only
     guarantees the {l1}.{l2} *pattern*, not existence).
  3. Every lens_signal.value is valid FOR ITS NAMED LENS (per LENS_VALUES).
     The schema's `value` is a flat union of all lens values, so e.g.
     `process: machine` passes the schema but is semantically invalid.
  4. Every evidence_ref / lens_signal.evidence_ref / unmapped.evidence_ref
     RESOLVES to real lines in the cited ingested MD: parse `path#Lstart-Lend`,
     open it under engagements/{E}/, and assert the line range exists.

Exit 0 + "ok" when clean; nonzero with a clear per-issue report on any failure.

Usage:
    validate_artifact.py validate --artifact PATH [--engagement E]

The --engagement is required for check (4) (to root the ingested-MD paths). If
omitted, the ref-resolution check is skipped with a reported note and the other
checks still run.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "classify_artifact.schema.json"
TAXONOMY_PATH = REPO_ROOT / "reference" / "taxonomy.yaml"
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"

# Reuse the lens-value sets from state_machine. Importing is fragile here because
# the orchestrator may have in-progress edits to state_machine.py; we import the
# module read-only and fall back to a local copy if the import fails. LENS_VALUES
# mirrors engagement_state.schema.json (the single source of truth for lens
# values) and changes rarely.
_FALLBACK_LENS_VALUES = {
    "current_state": ["present", "absent"],
    "process": ["pain_high", "pain_med", "pain_low", "strength"],
    "automation": ["machine", "mixed", "human"],
    "capability": ["new", "existing"],
    "operating_model": ["central", "mixed", "local"],
}


def _load_lens_values() -> Dict[str, List[str]]:
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import state_machine  # type: ignore

        lv = getattr(state_machine, "LENS_VALUES", None)
        if isinstance(lv, dict) and lv:
            return lv
    except Exception:
        pass
    return _FALLBACK_LENS_VALUES


def _load_taxonomy_nodes() -> set:
    """Set of valid '{l1}.{l2}' node keys. Reuses state_machine's loader when
    importable; otherwise parses the taxonomy directly."""
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import state_machine  # type: ignore

        tax = state_machine.load_taxonomy()
        return {f"{l1}.{l2}" for l1, _, l2, _, _ in state_machine.iter_l2(tax)}
    except Exception:
        pass
    # Fallback: parse the taxonomy ourselves.
    import yaml

    with TAXONOMY_PATH.open("r", encoding="utf-8") as f:
        tax = yaml.safe_load(f)
    nodes = set()
    for dom in tax.get("domains", []):
        for l2 in dom.get("l2", []):
            nodes.add(f"{dom['id']}.{l2['id']}")
    return nodes


# ---- check (1): JSON-Schema -------------------------------------------------

def schema_errors(instance: Dict[str, Any]) -> List[str]:
    if not SCHEMA_PATH.exists():
        return [f"(schema not found at {SCHEMA_PATH})"]
    try:
        import jsonschema
    except ImportError:
        return ["(jsonschema not installed — pip install jsonschema)"]
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft7Validator(schema)
    return [
        f"schema: {'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
    ]


# ---- check (2): node existence ----------------------------------------------

def node_errors(instance: Dict[str, Any], valid_nodes: set) -> List[str]:
    errs: List[str] = []
    for i, hit in enumerate(instance.get("node_hits", []) or []):
        node = hit.get("node")
        if node is not None and node not in valid_nodes:
            errs.append(f"node: node_hits[{i}].node '{node}' is not in the taxonomy.")
    return errs


# ---- check (3): lens value valid for its lens -------------------------------

def lens_errors(instance: Dict[str, Any], lens_values: Dict[str, List[str]]) -> List[str]:
    errs: List[str] = []
    for i, hit in enumerate(instance.get("node_hits", []) or []):
        for j, sig in enumerate(hit.get("lens_signals", []) or []):
            lens = sig.get("lens")
            value = sig.get("value")
            allowed = lens_values.get(lens)
            if allowed is None:
                # Unknown lens is a schema concern, but flag it anyway.
                errs.append(
                    f"lens: node_hits[{i}].lens_signals[{j}] unknown lens '{lens}'."
                )
                continue
            if value not in allowed:
                errs.append(
                    f"lens: node_hits[{i}].lens_signals[{j}] value '{value}' is not "
                    f"valid for lens '{lens}' (allowed: {', '.join(allowed)})."
                )
    return errs


# ---- evidence note guidance (informational, never a failure) ----------------

def evidence_note_notes(instance: Dict[str, Any]) -> List[str]:
    """Soft guidance: an evidence entry with neither `note` nor (legacy) `quote`
    carries no gloss for the merge. Absence of `quote` is NOT an error (T55 trim
    drops it); we only nudge toward adding a concise `note`. Emitted as a
    "(skipped ...)" informational note so it never fails validation."""
    out: List[str] = []
    for i, hit in enumerate(instance.get("node_hits", []) or []):
        for j, ev in enumerate(hit.get("evidence", []) or []):
            if not isinstance(ev, dict):
                continue
            if not (ev.get("note") or ev.get("quote")):
                out.append(
                    f"note: (skipped — guidance) node_hits[{i}].evidence[{j}] has "
                    f"no `note`; add a concise `note` so the evidence carries a gloss."
                )
    return out


# ---- check (4): evidence-ref resolution -------------------------------------

_REF_RE = re.compile(r"^(?P<path>.+?)#L(?P<start>[0-9]+)(?:-(?P<end>[0-9]+))?$")


def _collect_refs(instance: Dict[str, Any]) -> List[Tuple[str, str]]:
    """Return (location_label, ref_string) for every evidence ref in the artifact."""
    refs: List[Tuple[str, str]] = []
    for i, hit in enumerate(instance.get("node_hits", []) or []):
        for j, ev in enumerate(hit.get("evidence", []) or []):
            if ev.get("ref"):
                refs.append((f"node_hits[{i}].evidence[{j}].ref", ev["ref"]))
        for j, sig in enumerate(hit.get("lens_signals", []) or []):
            if sig.get("evidence_ref"):
                refs.append(
                    (f"node_hits[{i}].lens_signals[{j}].evidence_ref", sig["evidence_ref"])
                )
        for j, cf in enumerate(hit.get("candidate_findings", []) or []):
            if cf.get("evidence_ref"):
                refs.append(
                    (f"node_hits[{i}].candidate_findings[{j}].evidence_ref", cf["evidence_ref"])
                )
    for i, um in enumerate(instance.get("unmapped", []) or []):
        if um.get("evidence_ref"):
            refs.append((f"unmapped[{i}].evidence_ref", um["evidence_ref"]))
    return refs


def _count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for _ in f)


def ref_errors(instance: Dict[str, Any], engagement: str | None) -> List[str]:
    refs = _collect_refs(instance)
    if engagement is None:
        if refs:
            return ["ref: (skipped ref-resolution: no --engagement given)"]
        return []
    edir = ENGAGEMENTS_DIR / engagement
    errs: List[str] = []
    line_cache: Dict[Path, int] = {}
    for label, ref in refs:
        m = _REF_RE.match(ref)
        if not m:
            errs.append(f"ref: {label} '{ref}' is not a parseable path#Lstart-Lend ref.")
            continue
        rel_path = m.group("path")
        start = int(m.group("start"))
        end = int(m.group("end")) if m.group("end") else start
        if end < start:
            errs.append(f"ref: {label} '{ref}' has end line < start line.")
            continue
        if start < 1:
            errs.append(f"ref: {label} '{ref}' start line must be >= 1.")
            continue
        md_path = (edir / rel_path).resolve()
        # Guard against path escaping the engagement dir.
        try:
            md_path.relative_to(edir.resolve())
        except ValueError:
            errs.append(f"ref: {label} '{ref}' path escapes engagement dir.")
            continue
        if not md_path.exists():
            errs.append(
                f"ref: {label} cited MD does not exist: {rel_path} "
                f"(looked under engagements/{engagement}/)."
            )
            continue
        if md_path not in line_cache:
            line_cache[md_path] = _count_lines(md_path)
        n = line_cache[md_path]
        if end > n:
            errs.append(
                f"ref: {label} '{ref}' cites line {end} but {rel_path} has only {n} line(s)."
            )
    return errs


# ---- driver -----------------------------------------------------------------

def validate(artifact_path: Path, engagement: str | None) -> int:
    if not artifact_path.exists():
        print(f"FAIL: artifact not found: {artifact_path}")
        return 2
    try:
        with artifact_path.open("r", encoding="utf-8") as f:
            instance = json.load(f)
    except json.JSONDecodeError as e:
        print(f"FAIL: artifact is not valid JSON: {e}")
        return 2

    all_errs: List[str] = []
    all_errs += schema_errors(instance)
    # If the shape is broken, the cross-field checks may misfire; but they are
    # defensive (use .get with defaults), so run them anyway for a fuller report.
    valid_nodes = _load_taxonomy_nodes()
    lens_values = _load_lens_values()
    all_errs += node_errors(instance, valid_nodes)
    all_errs += lens_errors(instance, lens_values)
    all_errs += ref_errors(instance, engagement)
    all_errs += evidence_note_notes(instance)

    # A pure "(skipped ...)" note is informational, not a failure.
    hard = [e for e in all_errs if "(skipped" not in e]
    notes = [e for e in all_errs if "(skipped" in e]

    if hard:
        print(f"FAIL: {len(hard)} issue(s) in {artifact_path}:")
        for e in hard:
            print(f"  - {e}")
        for n in notes:
            print(f"  note: {n}")
        return 1

    print(f"ok: {artifact_path} validates (schema + node + lens + ref).")
    for n in notes:
        print(f"  note: {n}")
    return 0


def main() -> None:
    p = argparse.ArgumentParser(description="Validate a Stage 2 classify artifact.")
    sub = p.add_subparsers(dest="command", required=True)
    v = sub.add_parser("validate", help="Validate one artifact JSON file.")
    v.add_argument("--artifact", required=True, help="Path to the artifact JSON.")
    v.add_argument(
        "--engagement",
        help="Engagement id; roots evidence-ref resolution under engagements/{E}/.",
    )
    args = p.parse_args()
    if args.command == "validate":
        raise SystemExit(validate(Path(args.artifact), args.engagement))


if __name__ == "__main__":
    main()
