#!/usr/bin/env python3
"""synthesis_inputs.py — Stage-5C synthesis input gatherer (CONSULT pipeline).

READ-ONLY helper. Assembles the **cross-cutting** aggregation a
`consult-synthesizer` sub-agent needs to turn the bottom-up streams into a point
of view: the lead `deliverables/synthesis.md` (exec summary + prioritized
roadmap + current→future) and `type:theme` cross-cutting findings.

Where draft_inputs.py gathers one L1 (for an SOP) and consolidate_inputs.py
gathers one L2 (for a node MD), this gatherer reads the **whole engagement** and
rolls it up:
  - every active `type:improvement` row across all L1s, carried with its
    `effort` / `priority` / `phase` / `impact_type` / lens `tag` and node key,
  - node `coverage` + the 5 lens scores across L1s,
  - a simple **effort × impact bucketing** (e.g. quick-win = low-effort /
    high-impact), so the roadmap can be sequenced by the register fields,
  - a **per-L1 lens roll-up** — counts of each lens value under every L1, with
    `capability:new` surfaced as the future-state signal.

This script never writes state.json / register.json / any deliverable. It only
reads, so the LLM gets a clean, complete, deterministic input set instead of
foraging across files. The judgment (author synthesis.md, lift cross-cutting
findings into `type:theme` rows) is the sub-agent's; the register write-back is
the command path's (improvement_log upsert-json). See the consult-synthesizer
SKILL.

Command:
  gather --engagement E [--json]

`--json` emits the machine bundle; default prints a human-readable summary.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Same-dir helper (scripts/); content-free size side-channel for `--measure`.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measure_util  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"

# Mirror state_machine.py's lens order (kept local to avoid import coupling).
LENSES = ["current_state", "process", "automation", "capability", "operating_model"]

# Register row statuses that should not surface as live items (aligned with
# state_machine.INACTIVE_STATUSES / improvement_log ARCHIVE∪DELETE statuses).
INACTIVE_STATUSES = {"archived", "inactive", "deleted_candidate", "deleted",
                     "delete", "removed", "remove"}

# --- Effort × Impact model ---------------------------------------------------
# Effort comes straight from the register `effort` enum (low/med/high).
# Impact is read from the register `priority` enum (p1/p2/p3), the field the
# pipeline already uses to rank items: p1 = high impact, p2 = med, p3 = low.
# (priority is the deliberate prioritization signal; impact_type names the kind
# of value — cost/time/risk/quality/control — and is carried through for the
# narrative but is not itself an ordinal impact level.)
PRIORITY_TO_IMPACT = {"p1": "high", "p2": "med", "p3": "low"}
EFFORT_LEVELS = ["low", "med", "high"]
IMPACT_LEVELS = ["high", "med", "low"]

# The effort×impact bucket name for each (effort, impact) cell. quick-win is the
# headline: low effort, high impact. "unranked" catches rows missing effort or
# priority (the sub-agent should set requires_human_review, not invent them).
BUCKETS = {
    ("low", "high"): "quick_win",
    ("med", "high"): "major_project",
    ("high", "high"): "major_project",
    ("low", "med"): "incremental",
    ("med", "med"): "incremental",
    ("low", "low"): "fill_in",
    ("med", "low"): "fill_in",
    ("high", "med"): "thankless",
    ("high", "low"): "thankless",
}
BUCKET_ORDER = ["quick_win", "major_project", "incremental", "fill_in",
                "thankless", "unranked"]
BUCKET_LABELS = {
    "quick_win": "Quick win (low effort / high impact)",
    "major_project": "Major project (high impact, higher effort)",
    "incremental": "Incremental (medium impact)",
    "fill_in": "Fill-in (low impact, low/med effort)",
    "thankless": "Thankless (high effort, low/med impact)",
    "unranked": "Unranked (missing effort or priority — needs human review)",
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


# ---- helpers ----------------------------------------------------------------

def _is_active(rec: Dict[str, Any]) -> bool:
    return str(rec.get("record_status", "active") or "active").lower() not in INACTIVE_STATUSES


def _norm(value: Any) -> Optional[str]:
    if value is None:
        return None
    txt = str(value).strip().lower()
    return txt or None


def bucket_for(effort: Optional[str], priority: Optional[str]) -> str:
    """Map (effort, priority) onto an effort×impact bucket name.

    Impact is derived from priority via PRIORITY_TO_IMPACT. A row missing either
    effort or a recognized priority falls into `unranked` — the sub-agent must
    not invent the missing field (see SKILL non-negotiables).
    """
    e = _norm(effort)
    impact = PRIORITY_TO_IMPACT.get(_norm(priority) or "")
    if e in EFFORT_LEVELS and impact in IMPACT_LEVELS:
        return BUCKETS[(e, impact)]
    return "unranked"


def improvement_view(rec: Dict[str, Any], node_key: str) -> Dict[str, Any]:
    """Slim, synthesis-ready view of a type:improvement register row."""
    effort = _norm(rec.get("effort"))
    priority = _norm(rec.get("priority"))
    return {
        "id": rec.get("id"),
        "node": node_key,
        "l1": rec.get("l1_cycle"),
        "l2": rec.get("l2_process"),
        "tag": rec.get("tag"),                     # the diagnostic lens
        "observation_pain_point": rec.get("observation_pain_point"),
        "recommended_action": rec.get("recommended_action"),
        "impact_type": rec.get("impact_type"),
        "estimated_impact_benefit": rec.get("estimated_impact_benefit"),
        "effort": effort,
        "priority": priority,
        "impact": PRIORITY_TO_IMPACT.get(priority or ""),
        "phase": rec.get("phase"),
        "bucket": bucket_for(effort, priority),
        "dedup_key": rec.get("dedup_key"),
    }


# ---- bundle assembly --------------------------------------------------------

def build_bundle(eid: str) -> Dict[str, Any]:
    state = load_state(eid)
    nodes: Dict[str, Any] = state["nodes"]
    records = [r for r in load_register(eid) if _is_active(r)]

    # --- every active improvement, across all L1s ---
    improvements: List[Dict[str, Any]] = []
    for rec in records:
        if str(rec.get("type", "improvement") or "improvement").lower() != "improvement":
            continue
        l1, l2 = rec.get("l1_cycle"), rec.get("l2_process")
        node_key = f"{l1}.{l2}" if l1 and l2 else "(unmapped)"
        improvements.append(improvement_view(rec, node_key))
    improvements.sort(key=lambda v: (str(v.get("l1")), str(v.get("l2")), str(v.get("id"))))

    # --- effort × impact bucketing (ids grouped per bucket) ---
    buckets: Dict[str, List[str]] = {b: [] for b in BUCKET_ORDER}
    for imp in improvements:
        buckets[imp["bucket"]].append(imp["id"])
    effort_impact = {
        "labels": BUCKET_LABELS,
        "buckets": {b: buckets[b] for b in BUCKET_ORDER},
        "counts": {b: len(buckets[b]) for b in BUCKET_ORDER},
    }

    # --- node coverage + lens scores across L1s, and per-L1 lens roll-up ---
    # Group node keys by L1 for the roll-up; carry coverage + lenses per node.
    by_l1: Dict[str, List[str]] = {}
    node_coverage: Dict[str, Dict[str, Any]] = {}
    for key, node in nodes.items():
        l1 = node.get("l1")
        by_l1.setdefault(l1, []).append(key)
        node_coverage[key] = {
            "l1": l1,
            "l1_name": node.get("l1_name"),
            "l2": node.get("l2"),
            "l2_name": node.get("l2_name"),
            "coverage": node.get("coverage"),
            "lenses": {lens: node["lenses"].get(lens) for lens in LENSES},
            "improvement_count": node.get("counts", {}).get("improvements", 0),
        }

    per_l1: List[Dict[str, Any]] = []
    for l1 in sorted(by_l1):
        keys = sorted(by_l1[l1])
        l1_name = nodes[keys[0]].get("l1_name") if keys else None
        # Coverage tally for the L1.
        cov_counts: Counter = Counter(nodes[k].get("coverage", "none") for k in keys)
        # Lens roll-up: per lens, a value->count tally across the L1's nodes.
        lens_rollup: Dict[str, Dict[str, int]] = {}
        for lens in LENSES:
            tally: Counter = Counter()
            for k in keys:
                val = nodes[k]["lenses"].get(lens)
                if val is not None:
                    tally[val] += 1
            lens_rollup[lens] = dict(tally)
        # Future-state signal: nodes where capability lens == new.
        future_state_nodes = sorted(
            k for k in keys if nodes[k]["lenses"].get("capability") == "new")
        # Improvements landing under this L1, by bucket.
        l1_imps = [imp for imp in improvements if imp.get("l1") == l1]
        bucket_counts = Counter(imp["bucket"] for imp in l1_imps)
        per_l1.append({
            "l1": l1,
            "l1_name": l1_name,
            "l2_count": len(keys),
            "coverage_counts": dict(cov_counts),
            "lens_rollup": lens_rollup,
            "future_state_nodes": future_state_nodes,   # capability:new
            "improvement_count": len(l1_imps),
            "improvement_buckets": {b: bucket_counts.get(b, 0) for b in BUCKET_ORDER},
        })

    return {
        "engagement": state["engagement"]["id"],
        "synthesis_path": f"engagements/{state['engagement']['id']}/deliverables/synthesis.md",
        "totals": {
            "l1_count": len(by_l1),
            "node_count": len(nodes),
            "active_improvement_count": len(improvements),
        },
        "improvements": improvements,
        "effort_impact": effort_impact,
        "per_l1": per_l1,
        "node_coverage": node_coverage,
    }


# ---- rendering --------------------------------------------------------------

def print_human(bundle: Dict[str, Any]) -> None:
    t = bundle["totals"]
    print(f"Engagement: {bundle['engagement']}  |  synthesis write-back: "
          f"{bundle['synthesis_path']}")
    print(f"  L1 cycles: {t['l1_count']}  |  nodes: {t['node_count']}  |  "
          f"active improvements: {t['active_improvement_count']}")

    ei = bundle["effort_impact"]
    print("\n  Effort × Impact buckets:")
    for b in BUCKET_ORDER:
        ids = ei["buckets"][b]
        if not ids:
            continue
        print(f"    {ei['labels'][b]} ({len(ids)}): {', '.join(ids)}")

    print("\n  Improvements (id [bucket] effort/impact lens — node):")
    for imp in bundle["improvements"]:
        print(f"    - {imp['id']} [{imp['bucket']}] "
              f"effort={imp['effort']} impact={imp['impact']} "
              f"(priority={imp['priority']}) lens={imp.get('tag')} "
              f"phase={imp.get('phase')} @ {imp['node']}")
        if imp.get("observation_pain_point"):
            print(f"        {imp['observation_pain_point']}")

    print("\n  Per-L1 lens roll-up:")
    for row in bundle["per_l1"]:
        print(f"    [{row['l1']}] {row['l1_name']}  "
              f"(L2s={row['l2_count']}, improvements={row['improvement_count']})")
        print(f"      coverage: " + " ".join(
            f"{k}={v}" for k, v in sorted(row["coverage_counts"].items())))
        for lens in LENSES:
            roll = row["lens_rollup"].get(lens) or {}
            if roll:
                print(f"      {lens}: " + " ".join(
                    f"{k}={v}" for k, v in sorted(roll.items())))
        if row["future_state_nodes"]:
            print(f"      capability:new (future-state signal): "
                  f"{', '.join(row['future_state_nodes'])}")


def _measure_sections(bundle: Dict[str, Any]) -> List[Tuple[str, Any]]:
    """Fixed-label structural breakdown for the size side-channel (content-free).

    `taxonomy-slice` = the synthesis path + totals scalars; `improvements` = the
    active improvement rows; `effort-impact` = the bucketing; `per-l1-rollup` =
    the per-L1 lens roll-up; `coverage` = the node coverage map. Only serialized
    SIZES of these subtrees leave this function, never their content.
    """
    return [
        ("taxonomy-slice", {"synthesis_path": bundle.get("synthesis_path"),
                            "totals": bundle.get("totals", {})}),
        ("improvements", bundle.get("improvements", [])),
        ("effort-impact", bundle.get("effort_impact", {})),
        ("per-l1-rollup", bundle.get("per_l1", [])),
        ("coverage", bundle.get("node_coverage", {})),
    ]


def cmd_gather(eid: str, as_json: bool, measure: bool) -> None:
    bundle = build_bundle(eid)
    if measure:
        # Side-channel (stderr): never pollutes the stdout worker bundle.
        measure_util.emit(bundle, _measure_sections(bundle),
                          header="synthesis | engagement", as_json=as_json)
    if as_json:
        print(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")))
    else:
        print_human(bundle)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Read-only Stage-5C synthesis input gatherer (cross-cutting, "
                    "whole engagement).")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("gather", help="Assemble the cross-cutting synthesis input bundle.")
    g.add_argument("--engagement", required=True)
    g.add_argument("--json", action="store_true", help="Emit the machine bundle as JSON.")
    g.add_argument("--measure", action="store_true",
                   help="Print a CONTENT-FREE size summary to stderr (sizes/tokens/labels "
                        "only); the stdout bundle is unchanged.")

    args = p.parse_args()
    if args.command == "gather":
        cmd_gather(args.engagement, args.json, args.measure)


if __name__ == "__main__":
    main()
