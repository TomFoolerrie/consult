#!/usr/bin/env python3
"""draft_inputs.py — Stage-5 SOP draft input gatherer (CONSULT pipeline).

READ-ONLY helper. Assembles the per-**L1** bundle the `consult-drafter` skill
needs to author one SOP per L1 cycle (its existing L1-Level mode), sourced from
engagement state/register instead of ad-hoc input. For every L2 node under the
L1 it gathers:
  - the node MD path + content (the per-L2 narrative the drafter prose builds on),
  - the node lenses (the 5 diagnostic lenses) + coverage,
  - the register rows on that node, bucketed to the SOP appendices:
      improvement (process lens / pain point) -> Appendix A (Risks & Pain Points)
      improvement (other lenses)               -> Appendix B (Process Improvements)
      gap                                       -> Appendix C (Gap / Validation Log)
      screenshot                                -> Appendix D (Screenshot Index)
    each row carried with its evidence ref (`path#L-L`) for inline rendering and
    its `evidence_tier`.

This script never writes state.json / register.json / any deliverable. It only
reads, so the LLM gets a clean, complete, deterministic input set instead of
foraging across files. The judgment (author the canonical SOP MD per the
drafter Quality Checklist) is the skill's; the write-back (set-sop) is the
command path's. See generation_review_contract.md §1 (5A) and the
consult-drafter SKILL "Source from engagement state" section.

Command:
  gather --engagement E --l1 L1 [--json]

`--json` emits the machine bundle; default prints a human-readable summary.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Same-dir helper (scripts/); content-free size side-channel for `--measure`.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_util  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"

# Mirror state_machine.py's lens order (kept local to avoid import coupling).
LENSES = ["current_state", "process", "automation", "capability", "operating_model"]

# Register row statuses that should not surface as live SOP items (aligned with
# state_machine.INACTIVE_STATUSES / improvement_log ARCHIVE∪DELETE statuses).
INACTIVE_STATUSES = {"archived", "inactive", "deleted_candidate", "deleted",
                     "delete", "removed", "remove"}

# Register row type -> SOP appendix. Improvements split by lens (see bucket_for):
# a process-lens improvement is a pain point -> Appendix A; other improvements
# are forward-looking opportunities -> Appendix B.
APPENDICES = {
    "A": "Risks & Pain Points Log",
    "B": "Process Improvement Opportunities",
    "C": "Gap / Validation Log",
    "D": "Screenshot / Evidence Index",
}


def engagement_dir(eid: str) -> Path:
    return ENGAGEMENTS_DIR / eid


# ---- loaders (read-only) ----------------------------------------------------

def load_state(eid: str) -> Dict[str, Any]:
    state_path = engagement_dir(eid) / "state.json"
    if not state_path.exists():
        raise SystemExit(f"No state.json for engagement '{eid}'. Run init first.")
    with state_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_register(eid: str) -> List[Dict[str, Any]]:
    register_path = engagement_dir(eid) / "register.json"
    if not register_path.exists():
        return []
    with register_path.open("r", encoding="utf-8") as f:
        return json.load(f).get("records", [])


def read_node_md(eid: str, rel_path: Optional[str]) -> Optional[str]:
    """Return the node MD content (read-only), or None if missing/unreadable.

    Guards against a node_md path escaping the engagement dir.
    """
    if not rel_path:
        return None
    edir = engagement_dir(eid)
    md_path = (edir / rel_path).resolve()
    try:
        md_path.relative_to(edir.resolve())
    except ValueError:
        return None
    if not md_path.exists():
        return None
    try:
        return md_path.read_text(encoding="utf-8")
    except OSError:
        return None


# ---- bucketing --------------------------------------------------------------

def _is_active(rec: Dict[str, Any]) -> bool:
    return str(rec.get("record_status", "active") or "active").lower() not in INACTIVE_STATUSES


def bucket_for(rec: Dict[str, Any]) -> Optional[str]:
    """Map a register row to its SOP appendix letter (A/B/C/D), or None.

    - improvement with `tag == process` (the process lens) is a pain point -> A
    - improvement (any other / no lens tag)                                 -> B
    - gap                                                                    -> C
    - screenshot                                                             -> D
    Rows of any other type (e.g. unmapped/theme) do not bucket to an appendix.
    """
    rtype = str(rec.get("type", "improvement") or "improvement").lower()
    if rtype == "improvement":
        if str(rec.get("tag") or "").lower() == "process":
            return "A"
        return "B"
    if rtype == "gap":
        return "C"
    if rtype == "screenshot":
        return "D"
    return None


def evidence_ref_of(rec: Dict[str, Any]) -> Optional[str]:
    """Best-effort `path#L-L` evidence ref for inline rendering.

    Prefers an explicit `evidence_ref` field; falls back to `dedup_key` or
    `source` when they already hold a `path#L...` ref (the classify/unmapped
    path stores the ref in those). Returns None if no ref-shaped value exists.
    """
    for field in ("evidence_ref", "dedup_key", "source"):
        val = rec.get(field)
        if val and isinstance(val, str) and "#L" in val:
            return val
    return None


def row_view(rec: Dict[str, Any]) -> Dict[str, Any]:
    """The slim, render-ready view of a register row for the SOP bundle."""
    return {
        "id": rec.get("id"),
        "type": rec.get("type"),
        "tag": rec.get("tag"),
        "l3_activity": rec.get("l3_activity"),
        "observation_pain_point": rec.get("observation_pain_point"),
        "root_cause": rec.get("root_cause"),
        "recommended_action": rec.get("recommended_action"),
        "impact_type": rec.get("impact_type"),
        "estimated_impact_benefit": rec.get("estimated_impact_benefit"),
        "effort": rec.get("effort"),
        "owner": rec.get("owner"),
        "evidence_ref": evidence_ref_of(rec),
        "evidence_tier": rec.get("evidence_tier"),
    }


# ---- bundle assembly --------------------------------------------------------

def build_bundle(eid: str, l1: str) -> Dict[str, Any]:
    state = load_state(eid)
    nodes = state["nodes"]

    # Every L2 node under this L1, sorted by node key for determinism.
    l2_keys = sorted(k for k, n in nodes.items() if n.get("l1") == l1)
    if not l2_keys:
        raise SystemExit(
            f"No L2 nodes under L1 '{l1}' in state.json for engagement '{eid}'.")

    l1_name = nodes[l2_keys[0]].get("l1_name")
    records = [r for r in load_register(eid) if _is_active(r)]

    l2_bundles: List[Dict[str, Any]] = []
    # L1-level appendix aggregation (rows bucketed across all L2s under the L1).
    appendices: Dict[str, List[Dict[str, Any]]] = {a: [] for a in APPENDICES}

    for key in l2_keys:
        node = nodes[key]
        l1_id, l2_id = node.get("l1"), node.get("l2")
        rows = [r for r in records
                if r.get("l1_cycle") == l1_id and r.get("l2_process") == l2_id]

        # Per-L2 appendix buckets.
        buckets: Dict[str, List[Dict[str, Any]]] = {a: [] for a in APPENDICES}
        for rec in rows:
            letter = bucket_for(rec)
            if letter is None:
                continue
            view = row_view(rec)
            buckets[letter].append(view)
            appendices[letter].append({**view, "node": key})

        l2_bundles.append({
            "key": key,
            "l1": l1_id, "l1_name": node.get("l1_name"),
            "l2": l2_id, "l2_name": node.get("l2_name"),
            "coverage": node.get("coverage"),
            "lenses": {lens: node["lenses"].get(lens) for lens in LENSES},
            "evidence": node.get("evidence", []),
            "node_md": node.get("node_md"),
            "node_md_content": read_node_md(eid, node.get("node_md")),
            "appendices": buckets,
        })

    return {
        "engagement": state["engagement"]["id"],
        "l1": l1,
        "l1_name": l1_name,
        "l2_count": len(l2_keys),
        "appendix_map": APPENDICES,
        "sop_path": f"engagements/{eid}/deliverables/sop/{l1}.md",
        "l2_nodes": l2_bundles,
        "appendices": appendices,
    }


# ---- rendering --------------------------------------------------------------

def print_human(bundle: Dict[str, Any]) -> None:
    print(f"Engagement: {bundle['engagement']}  |  L1: {bundle['l1']} "
          f"({bundle['l1_name']})")
    print(f"  L2 nodes under L1: {bundle['l2_count']}  |  "
          f"SOP write-back path: {bundle['sop_path']}")
    print("  Appendix map: "
          + ", ".join(f"{a}={name}" for a, name in bundle["appendix_map"].items()))

    for nb in bundle["l2_nodes"]:
        lenses = " ".join(f"{lens}={nb['lenses'].get(lens)}" for lens in LENSES)
        print(f"\n  [{nb['key']}] {nb['l2_name']}  (coverage={nb['coverage']})")
        print(f"    node_md: {nb['node_md']}"
              + ("" if nb["node_md_content"] is not None else "  (MISSING)"))
        print(f"    lenses: {lenses}")
        print(f"    evidence: {len(nb['evidence'])}")
        for letter in APPENDICES:
            rows = nb["appendices"][letter]
            if not rows:
                continue
            print(f"    Appendix {letter} — {APPENDICES[letter]} ({len(rows)}):")
            for r in rows:
                ref = r.get("evidence_ref") or "(no ref)"
                tier = r.get("evidence_tier") or "?"
                obs = (r.get("observation_pain_point")
                       or r.get("recommended_action") or "")
                print(f"      - {r.get('id')} [{r.get('type')}/{r.get('tag')}] "
                      f"tier={tier} ref={ref}")
                if obs:
                    print(f"        {obs}")

    print("\n  L1 appendix totals:")
    for letter in APPENDICES:
        print(f"    Appendix {letter} ({APPENDICES[letter]}): "
              f"{len(bundle['appendices'][letter])}")


def _measure_sections(bundle: Dict[str, Any]) -> List[Tuple[str, Any]]:
    """Fixed-label structural breakdown for the size side-channel (content-free).

    `taxonomy-slice` = the L1 scalars + per-L2 lenses/coverage/keys; `prior-MD` =
    the inlined node MD bodies (the bulk of the draft input); `evidence` = the
    per-L2 evidence lists; `appendices` = the register rows bucketed to A-D.
    Only serialized SIZES of these subtrees are emitted, never their content.
    """
    l2_nodes = bundle.get("l2_nodes", []) or []
    taxonomy_slice = {
        "l1": bundle.get("l1"),
        "l1_name": bundle.get("l1_name"),
        "l2_count": bundle.get("l2_count"),
        "appendix_map": bundle.get("appendix_map"),
        "sop_path": bundle.get("sop_path"),
        "l2_meta": [{k: nb.get(k) for k in ("key", "l1", "l2", "coverage", "lenses")}
                    for nb in l2_nodes],
    }
    prior_md = [nb.get("node_md_content") for nb in l2_nodes]
    evidence = [nb.get("evidence", []) for nb in l2_nodes]
    appendices = bundle.get("appendices", {})
    return [
        ("taxonomy-slice", taxonomy_slice),
        ("prior-MD", prior_md),
        ("evidence", evidence),
        ("appendices", appendices),
    ]


def cmd_gather(eid: str, l1: str, as_json: bool, measure: bool) -> None:
    bundle = build_bundle(eid, l1)
    if measure:
        # Side-channel (stderr): never pollutes the stdout worker bundle.
        measure_util.emit(bundle, _measure_sections(bundle),
                          header=f"draft | l1={l1}", as_json=as_json)
    if as_json:
        print(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")))
    else:
        print_human(bundle)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Read-only Stage-5 SOP draft input gatherer (per L1 cycle).")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("gather", help="Assemble the per-L1 SOP draft input bundle.")
    g.add_argument("--engagement", required=True)
    g.add_argument("--l1", required=True, help="L1 cycle id, e.g. record-to-report.")
    g.add_argument("--json", action="store_true", help="Emit the machine bundle as JSON.")
    g.add_argument("--measure", action="store_true",
                   help="Print a CONTENT-FREE size summary to stderr (sizes/tokens/labels "
                        "only); the stdout bundle is unchanged.")

    args = p.parse_args()
    if args.command == "gather":
        cmd_gather(args.engagement, args.l1, args.json, args.measure)


if __name__ == "__main__":
    main()
