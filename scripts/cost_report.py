#!/usr/bin/env python3
"""cost_report.py — per-phase cost map reporter (CONSULT, T56). READ-ONLY.

Aggregates the two halves of the per-phase cost picture into one screen:

  - **Measured output tokens** — read from the persisted `engagements/E/cost_map.json`
    the `consult-fanout` workflow's `budget.spent()` deltas feed (a content-free
    per-stage list: `{stage, targets, outputTokensDelta}`). This file is the ONLY
    source of measured tokens (they are ephemeral to the live workflow turn); we
    READ it, never generate it. Absence is handled gracefully (the measured
    column reads `-`).
  - **Estimated input sizes + output bytes** — from the read-only disk walk in
    `orchestrate.py measure` (which reuses the gatherers' own content-free
    sizing). chars/4 is an ESTIMATE, labelled as such.

Plus a `--measured-usd` field to PASTE the run's measured dollar total alongside
the map, so size->cost can be correlated across runs. No persistence layer of its
own, no plotting, dependency-free.

HARD CONTRACT — content-free. Every value emitted (and every value read from
`cost_map.json`, which is itself content-free) is a number / count / fixed phase
label. No document text, evidence refs, dedup_keys, or `source#loc` strings.

Usage:
  cost_report.py --engagement E [--measured-usd 9.87] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Same-dir helpers (scripts/): the read-only per-phase disk walk + engagement dir.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import orchestrate  # noqa: E402  (reuse _measure_phases — the disk-walk side)
from state_machine import engagement_dir  # noqa: E402

# Phase ordering for the one-screen table (the gatherer/fan-out phases plus the
# pre-fan-out classify stage, which can appear in cost_map.json but has no input
# gatherer of its own).
PHASE_ORDER = ["classify", "consolidate", "draft", "synthesize"]


def load_cost_map(eid: str) -> Optional[List[Dict[str, Any]]]:
    """Read the persisted content-free `cost_map.json` (measured output tokens).

    Returns the per-stage list, or None if the file is absent (no measured run
    yet) — the caller renders the measured column as `-` in that case. Tolerates
    either a bare list or a `{"stages": [...]}` wrapper.
    """
    path = engagement_dir(eid) / "cost_map.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if isinstance(data, dict):
        data = data.get("stages") or data.get("cost") or []
    return data if isinstance(data, list) else []


def _measured_by_phase(cost_map: Optional[List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
    """Sum measured output-token deltas per phase from the cost map (if present)."""
    out: Dict[str, Dict[str, Any]] = {}
    for entry in cost_map or []:
        stage = entry.get("stage")
        if not stage:
            continue
        slot = out.setdefault(stage, {"output_tokens": 0, "targets": 0})
        slot["output_tokens"] += int(entry.get("outputTokensDelta", 0) or 0)
        slot["targets"] += int(entry.get("targets", 0) or 0)
    return out


def build_report(eid: str, measured_usd: Optional[float]) -> Dict[str, Any]:
    """Join measured tokens (cost_map.json) + disk-walk sizes into one map. READ-ONLY."""
    walk = orchestrate._measure_phases(eid)  # est. input + output bytes per phase
    walk_by_phase = {ph["phase"]: ph for ph in walk["phases"]}
    cost_map = load_cost_map(eid)
    measured = _measured_by_phase(cost_map)

    phases: List[Dict[str, Any]] = []
    seen = set()
    for phase in PHASE_ORDER + [p for p in walk_by_phase if p not in PHASE_ORDER]:
        if phase in seen:
            continue
        seen.add(phase)
        w = walk_by_phase.get(phase, {})
        m = measured.get(phase)
        # #targets: prefer the disk-walk count; fall back to the measured count.
        targets = w.get("targets")
        if targets is None:
            targets = (m or {}).get("targets")
        phases.append({
            "phase": phase,
            "targets": targets,
            "output_tokens_measured": (m or {}).get("output_tokens"),
            "est_input_tokens": w.get("est_input_tokens_total"),
            "output_bytes": w.get("output_bytes"),
        })

    return {
        "engagement": eid,
        "cost_map_present": cost_map is not None,
        "est_tokens_basis": walk["est_tokens_basis"],
        "measured_usd": measured_usd,
        "phases": phases,
    }


def _fmt(v: Any) -> str:
    return "-" if v is None else str(v)


def print_human(report: Dict[str, Any]) -> None:
    print(f"Engagement: {report['engagement']}  (per-phase cost map; READ-ONLY)")
    if not report["cost_map_present"]:
        print("  NOTE: no cost_map.json yet — measured output-token column is '-'. "
              "Run a fan-out under the consult-fanout workflow to populate it.")
    print(f"  est. input tokens = {report['est_tokens_basis']}")
    print(f"  {'phase':<12} {'#targets':>9} {'out.tok(meas)':>14} "
          f"{'est.in.tok':>11} {'out.bytes':>11}")
    for ph in report["phases"]:
        print(f"  {ph['phase']:<12} {_fmt(ph['targets']):>9} "
              f"{_fmt(ph['output_tokens_measured']):>14} "
              f"{_fmt(ph['est_input_tokens']):>11} {_fmt(ph['output_bytes']):>11}")
    usd = report["measured_usd"]
    print(f"  measured $ total (pasted): "
          + (f"${usd:.2f}" if usd is not None else "(not provided; pass --measured-usd)"))


def main() -> None:
    p = argparse.ArgumentParser(
        description="Per-phase cost map reporter (READ-ONLY, content-free).")
    p.add_argument("--engagement", required=True)
    p.add_argument("--measured-usd", type=float, default=None,
                   help="Paste the run's measured $ total for size->cost correlation.")
    p.add_argument("--json", action="store_true",
                   help="Emit the machine cost map as JSON.")
    args = p.parse_args()
    report = build_report(args.engagement, args.measured_usd)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_human(report)


if __name__ == "__main__":
    main()
