#!/usr/bin/env python3
"""gates.py — engagement Definition-of-Done gate checker (READ-ONLY).

`final-check` answers the question "is this engagement done enough to bless a
deliverable `final`?" against the spec §5 DoD gates. It mutates nothing — it only
reads state.json + register.json + the node MDs / ingested docs and reports
PASS/FAIL. Exit code is 0 only when every gate passes (nonzero otherwise) so it
can be wired in front of any `set-sop/--status final` step.

Gates:
  1. unmapped_dispositioned   — every ACTIVE type:unmapped row has
                                disposition != pending (an owner is not enough;
                                the content must be reclassified / converted /
                                out_of_scope).
  2. no_open_human_review     — zero ACTIVE rows with requires_human_review true
                                (archived rows excluded).
  3. evidence_refs_resolve    — (best-effort) every node-evidence `source` ref
                                resolves to a readable file under the engagement
                                dir. Skipped refs (no source) do not fail.
  4. final_artifacts_have_path — no node whose sop.status / improvement.status
                                == final lacks a path.

This script is intentionally standalone: it imports a few read-only helpers from
state_machine.py but never calls any mutating command.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List

# Reuse the read-only loaders / predicates from the state machine. None of these
# mutate state; gates.py never writes.
import state_machine as sm

LENSES = sm.LENSES


def _check_unmapped_dispositioned(records: List[Dict[str, Any]]) -> List[str]:
    """Active type:unmapped rows whose disposition is still pending."""
    failures: List[str] = []
    for rec in records:
        if str(rec.get("type", "")).lower() != "unmapped":
            continue
        if not sm._is_active(rec):
            continue
        disposition = str(rec.get("disposition") or "pending").lower()
        if disposition == "pending":
            failures.append(
                f"{rec.get('id')}: unmapped row disposition=pending "
                f"(needs reclassified/converted/out_of_scope)")
    return failures


def _check_no_open_human_review(records: List[Dict[str, Any]]) -> List[str]:
    """Active rows flagged requires_human_review (archived excluded)."""
    failures: List[str] = []
    for rec in records:
        if not sm._is_active(rec):
            continue
        if sm._is_truthy_flag(rec.get("requires_human_review")):
            failures.append(
                f"{rec.get('id')}: requires_human_review is open "
                f"(type={rec.get('type')}, review_status={rec.get('review_status')})")
    return failures


def _check_evidence_refs_resolve(eid: str, state: Dict[str, Any]) -> List[str]:
    """Best-effort: every node-evidence `source` ref resolves to a real file.

    Evidence `source` paths are stored relative to the engagement dir (e.g.
    `ingested/foo.md`). A ref with no `source` is skipped (cannot be checked),
    not failed.
    """
    edir = sm.engagement_dir(eid)
    failures: List[str] = []
    for key, node in state["nodes"].items():
        for entry in node.get("evidence", []) or []:
            source = entry.get("source")
            if not source:
                continue
            loc = entry.get("loc")
            # Normalize + confine to the engagement dir: a `../..`-style source
            # must not resolve outside the engagement. Mirror the existing idiom
            # in consolidate_inputs.py / draft_inputs.py ((edir/rel).resolve() +
            # try relative_to(edir.resolve())), not is_relative_to.
            ref_path = (edir / source).resolve()
            try:
                ref_path.relative_to(edir.resolve())
            except ValueError:
                failures.append(
                    f"{key}: evidence ref escapes the engagement dir -> {source}"
                    + (f" (loc={loc})" if loc else ""))
                continue
            if not ref_path.exists():
                failures.append(
                    f"{key}: evidence ref does not resolve -> {source}"
                    + (f" (loc={loc})" if loc else ""))
    return failures


def _check_final_artifacts_have_path(eid: str, state: Dict[str, Any]) -> List[str]:
    """No node with sop/improvement.status == final lacking a path, and the
    path must point at a file that actually exists (symmetry with the evidence
    gate). Paths are stored relative to the engagement dir."""
    edir = sm.engagement_dir(eid)
    failures: List[str] = []
    for key, node in state["nodes"].items():
        for block in ("sop", "improvement"):
            art = node.get(block, {}) or {}
            if str(art.get("status", "")).lower() != "final":
                continue
            path = art.get("path")
            if not path:
                failures.append(f"{key}: {block}.status=final but path is null")
                continue
            if not (edir / path).exists():
                failures.append(
                    f"{key}: {block}.status=final but path does not exist -> {path}")
    return failures


def run_final_check(eid: str) -> Dict[str, Any]:
    """Assemble the read-only final-check report object for an engagement."""
    _, state = sm.load_state(eid)
    records = sm.load_register(eid)

    gates = [
        ("unmapped_dispositioned",
         _check_unmapped_dispositioned(records)),
        ("no_open_human_review",
         _check_no_open_human_review(records)),
        ("evidence_refs_resolve",
         _check_evidence_refs_resolve(eid, state)),
        ("final_artifacts_have_path",
         _check_final_artifacts_have_path(eid, state)),
    ]

    gate_results = []
    for name, failures in gates:
        gate_results.append({
            "gate": name,
            "passed": not failures,
            "failures": failures,
        })

    all_passed = all(g["passed"] for g in gate_results)
    return {
        "engagement": eid,
        "passed": all_passed,
        "gates": gate_results,
    }


def cmd_final_check(eid: str, as_json: bool) -> int:
    report = run_final_check(eid)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["passed"] else 1

    print(f"final-check: engagement {report['engagement']}")
    for g in report["gates"]:
        status = "PASS" if g["passed"] else "FAIL"
        print(f"  [{status}] {g['gate']}"
              + (f" ({len(g['failures'])} failing)" if g["failures"] else ""))
        for f in g["failures"]:
            print(f"      - {f}")
    overall = "PASS" if report["passed"] else "FAIL"
    print(f"Overall: {overall}")
    if not report["passed"]:
        print("Refusing to bless `final`: fix the failing gates above.")
    return 0 if report["passed"] else 1


def main() -> None:
    p = argparse.ArgumentParser(
        description="Engagement Definition-of-Done gate checker (read-only).")
    sub = p.add_subparsers(dest="command", required=True)
    fc = sub.add_parser(
        "final-check",
        help="Report PASS/FAIL on the DoD gates; exit 0 only when all pass.")
    fc.add_argument("--engagement", required=True)
    fc.add_argument("--json", action="store_true",
                    help="Emit the machine gate report as JSON.")
    args = p.parse_args()
    if args.command == "final-check":
        raise SystemExit(cmd_final_check(args.engagement, args.json))


if __name__ == "__main__":
    main()
