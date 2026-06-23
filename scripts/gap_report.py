#!/usr/bin/env python3
"""gap_report.py — Stage 4 structural gap detection (CONSULT pipeline).

Mechanically scans an engagement's state.json for *structural* gaps — empty
nodes, incomplete diagnoses, claims without evidence, undrafted SOPs — and
writes them into the Item Register as `type: gap` rows with stable IDs of the
form `GAP-STRUCT-{l1}-{l2}-{kind}`. Re-running `scan` upserts the same IDs
(idempotent) and self-heals: structural rows no longer detected are archived
so they drop out of node counts.

Structural gaps live in the register alongside the LLM-authored substantive
gaps (consult-gap-analyzer); both are `type: gap`. The two coexist by ID
prefix — this script only ever touches ids starting `GAP-STRUCT-`.

Detection rules (non-redundant, hierarchical) per node:
  coverage == none
      -> one gap: no-coverage (tag=not_documented). Implies the granular
         checks below, so they are NOT also emitted for an empty node.
  coverage == partial AND any lens null
      -> incomplete-diagnosis (tag=unconfirmed); lists the missing lenses.
  coverage == partial AND no evidence AND any active items
      -> no-evidence (tag=unconfirmed).
  coverage in {partial, covered} AND sop.status == not_started
      -> sop-not-started (tag=not_documented).

Write path: build ONE list of row dicts for all current structural rows (active)
plus stale rows (archived), upsert them through improvement_log.py
`upsert_records` (backup/validation/upsert-by-id), then state_machine.py `sync`
so node gap counts update.

Command:
  scan --engagement E [--dry-run]
"""
from __future__ import annotations

import argparse, json, subprocess, sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"
IMPROVEMENT_LOG_DIR = (REPO_ROOT / "skills" / "consult-improvement-log" / "scripts")
STATE_MACHINE = REPO_ROOT / "scripts" / "state_machine.py"

# The register engine is the single chokepoint for register.json writes; import
# its JSON-native upsert directly (no CSV transport, no subprocess fan-out).
sys.path.insert(0, str(IMPROVEMENT_LOG_DIR))
from improvement_log import upsert_records  # noqa: E402

# Mirror state_machine.py's data model (kept local to avoid import coupling).
LENSES = ["current_state", "process", "automation", "capability", "operating_model"]

STRUCT_PREFIX = "GAP-STRUCT-"
SOURCE = "structural-scan"


def engagement_dir(eid: str) -> Path:
    return ENGAGEMENTS_DIR / eid


def load_state(eid: str) -> Tuple[Path, Dict[str, Any]]:
    state_path = engagement_dir(eid) / "state.json"
    if not state_path.exists():
        raise SystemExit(f"No state.json for engagement '{eid}'. Run init first.")
    with state_path.open("r", encoding="utf-8") as f:
        return state_path, json.load(f)


def load_register_records(eid: str) -> List[Dict[str, Any]]:
    register_path = engagement_dir(eid) / "register.json"
    if not register_path.exists():
        return []
    with register_path.open("r", encoding="utf-8") as f:
        return json.load(f).get("records", [])


def struct_id(l1: str, l2: str, kind: str) -> str:
    return f"{STRUCT_PREFIX}{l1}-{l2}-{kind}"


def _has_substantive_items(node: Dict[str, Any]) -> bool:
    """Whether a node has substantive (non-gap) register items: improvements or
    screenshots. Gaps are absences and never count toward coverage, so they are
    excluded here too — this keeps the no-evidence rule from firing on a node
    whose only items are gaps."""
    counts = node.get("counts", {})
    return bool(counts.get("improvements", 0) or counts.get("screenshots", 0))


def detect_gaps(state: Dict[str, Any]) -> List[Dict[str, str]]:
    """Detect structural gaps for every node. Returns active gap rows.

    Each row carries id/tag/l1/l2/kind/observation. Rules are hierarchical: an
    empty (coverage==none) node yields exactly one no-coverage row; granular
    checks apply only to partial/covered nodes. Coverage is read straight from
    state — gaps no longer affect coverage (state_machine.COVERAGE_BUCKETS), so
    re-scans are naturally stable.
    """
    gaps: List[Dict[str, str]] = []
    for key, node in state.get("nodes", {}).items():
        l1, l2 = node.get("l1"), node.get("l2")
        # Malformed-node guard: a node missing l1/l2 would produce a degenerate
        # id like GAP-STRUCT-None-None-...; skip it and report on stderr rather
        # than emit a junk gap row.
        if not l1 or not l2:
            sys.stderr.write(
                f"gap_report: skipping malformed node '{key}' "
                f"(missing l1/l2: l1={l1!r}, l2={l2!r}).\n")
            continue
        l2_name = node.get("l2_name", l2)
        l1_name = node.get("l1_name", l1)
        label = f"{l1_name} — {l2_name}"

        coverage = node.get("coverage", "none")
        has_items = _has_substantive_items(node)

        if coverage == "none":
            gaps.append({
                "l1": l1, "l2": l2, "kind": "no-coverage", "tag": "not_documented",
                "observation": f"Node '{l1}.{l2}' ({label}) is empty / undocumented "
                               "(coverage: none). An empty node is itself a finding.",
            })
            continue

        # Granular checks (partial / covered nodes only).
        missing_lenses = [lens for lens in LENSES if not node.get("lenses", {}).get(lens)]
        has_evidence = bool(node.get("evidence"))
        sop_status = node.get("sop", {}).get("status")

        if coverage == "partial" and missing_lenses:
            gaps.append({
                "l1": l1, "l2": l2, "kind": "incomplete-diagnosis", "tag": "unconfirmed",
                "observation": f"Node '{l1}.{l2}' ({label}) diagnosis incomplete; "
                               f"missing lenses: {', '.join(missing_lenses)}.",
            })

        if coverage == "partial" and not has_evidence and has_items:
            gaps.append({
                "l1": l1, "l2": l2, "kind": "no-evidence", "tag": "unconfirmed",
                "observation": f"Node '{l1}.{l2}' ({label}) has items / claims but no "
                               "evidence attached.",
            })

        if coverage in ("partial", "covered") and sop_status == "not_started":
            gaps.append({
                "l1": l1, "l2": l2, "kind": "sop-not-started", "tag": "not_documented",
                "observation": f"Node '{l1}.{l2}' ({label}) is covered enough to draft an "
                               "SOP, but the SOP has not been started.",
            })

    for g in gaps:
        g["id"] = struct_id(g["l1"], g["l2"], g["kind"])
    return gaps


def build_csv_rows(detected: List[Dict[str, str]],
                   existing: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Build the CSV rows: detected gaps (active) + stale struct rows (archived).

    For a detected gap whose id already exists as an *active* GAP-STRUCT row in
    the loaded register, the human-review fields (review_status,
    requires_human_review, owner) are carried over from that existing row rather
    than reset to the insert-time defaults — so a re-scan never silently re-opens
    a gap a human has already reviewed/dispositioned. The observation text still
    refreshes. Newly-detected gaps (no active existing row) get the defaults.
    """
    detected_ids = {g["id"] for g in detected}
    # Index existing *active* GAP-STRUCT rows by id, so a re-scan preserves the
    # human-review state of rows already present (archived rows don't preserve;
    # a node re-becoming a gap is a fresh detection that gets the defaults).
    active_existing: Dict[str, Dict[str, Any]] = {}
    for rec in existing:
        rid = str(rec.get("id") or "")
        if not rid.startswith(STRUCT_PREFIX):
            continue
        if str(rec.get("record_status") or "active").lower() in ("archived", "inactive"):
            continue
        active_existing[rid] = rec
    rows: List[Dict[str, str]] = []

    for g in detected:
        prior = active_existing.get(g["id"])
        tag = g["tag"]
        if prior is not None:
            # Carry the human-review fields forward from the existing active row.
            review_status = prior.get("review_status") or "needs_review"
            rhr = prior.get("requires_human_review")
            requires_human_review = "true" if rhr is None else str(rhr).lower()
            owner = prior.get("owner")
            # Preserve a human-edited tag: if the existing active row's tag
            # differs from the detector's default, a human changed it — keep it
            # rather than overwrite on re-scan (mirrors review_status/owner).
            prior_tag = prior.get("tag")
            if prior_tag and prior_tag != g["tag"]:
                tag = prior_tag
        else:
            review_status = "needs_review"
            requires_human_review = "true"
            owner = None
        row = {
            "id": g["id"], "type": "gap", "tag": tag,
            "l1_cycle": g["l1"], "l2_process": g["l2"],
            "observation_pain_point": g["observation"], "source": SOURCE,
            "record_status": "active", "review_status": review_status,
            "requires_human_review": requires_human_review,
        }
        if owner is not None:
            row["owner"] = owner
        rows.append(row)

    # Self-heal: any existing GAP-STRUCT-* row not freshly detected is stale.
    for rec in existing:
        rid = str(rec.get("id") or "")
        if not rid.startswith(STRUCT_PREFIX) or rid in detected_ids:
            continue
        if str(rec.get("record_status") or "").lower() == "archived":
            continue  # already archived; no churn needed
        arch_row = {
            "id": rid, "type": "gap", "tag": rec.get("tag") or "not_documented",
            "l1_cycle": rec.get("l1_cycle") or "", "l2_process": rec.get("l2_process") or "",
            "observation_pain_point": rec.get("observation_pain_point") or "",
            "source": SOURCE, "record_status": "archived",
            "review_status": "needs_review", "requires_human_review": "true",
        }
        # Don't wipe a row's owner when archiving it: only carry owner forward
        # when the existing row has one (an absent key leaves the stored owner
        # untouched on upsert). Self-heal behavior is otherwise unchanged.
        arch_owner = rec.get("owner")
        if arch_owner is not None:
            arch_row["owner"] = arch_owner
        rows.append(arch_row)
    return rows


def write_register(eid: str, csv_rows: List[Dict[str, str]]) -> None:
    register_path = engagement_dir(eid) / "register.json"
    if not register_path.exists():
        raise SystemExit(f"No register.json for engagement '{eid}'. Run init first.")
    if not csv_rows:
        return

    # JSON-native upsert (by id; these rows carry no dedup_key). The rows are
    # already structured register-field dicts, so pass them straight to the
    # register engine — no temp CSV, no subprocess. upsert_records upserts by id
    # in-place (preserving the human-review fields build_csv_rows carried over).
    try:
        upsert_records(register_path, [dict(r) for r in csv_rows],
                       register_path, "gap-report")
    except Exception as exc:  # surface the engine error, don't leak a traceback
        sys.stderr.write(f"improvement_log upsert failed: {exc}\n")
        raise SystemExit("improvement_log upsert_records failed.")

    sync = subprocess.run(
        [sys.executable, str(STATE_MACHINE), "sync", "--engagement", eid],
        capture_output=True, text=True,
    )
    if sync.returncode != 0:
        sys.stderr.write(sync.stdout)
        sys.stderr.write(sync.stderr)
        raise SystemExit("state_machine.py sync failed.")


def write_md(eid: str, state: Dict[str, Any], detected: List[Dict[str, str]]) -> Path:
    """Emit deliverables/gap_report.md: a roll-up of active structural gaps."""
    edir = engagement_dir(eid)
    md_path = edir / "deliverables" / "gap_report.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)

    by_kind: Dict[str, int] = {}
    for g in detected:
        by_kind[g["kind"]] = by_kind.get(g["kind"], 0) + 1
    nodes_with_gaps = len({f"{g['l1']}.{g['l2']}" for g in detected})

    # Group gaps by node, then nodes by L1 (in state node order).
    gaps_by_node: Dict[str, List[Dict[str, str]]] = {}
    for g in detected:
        gaps_by_node.setdefault(f"{g['l1']}.{g['l2']}", []).append(g)

    eng = state.get("engagement", {})
    lines: List[str] = []
    lines.append("# Structural Gap Report")
    lines.append("")
    lines.append(f"Engagement: **{eng.get('id', eid)}**"
                 + (f" | client: {eng.get('client')}" if eng.get("client") else "")
                 + (f" | region: {eng.get('region')}" if eng.get("region") else ""))
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Total structural gaps: **{len(detected)}**")
    lines.append(f"- Nodes with structural gaps: **{nodes_with_gaps}**")
    lines.append("- By kind:")
    if by_kind:
        for kind in sorted(by_kind):
            lines.append(f"  - `{kind}`: {by_kind[kind]}")
    else:
        lines.append("  - (none)")
    lines.append("")

    # Per-L1 sections.
    seen_l1: List[str] = []
    l1_meta: Dict[str, str] = {}
    nodes_in_l1: Dict[str, List[str]] = {}
    for key, node in state.get("nodes", {}).items():
        l1 = node.get("l1")
        if l1 not in seen_l1:
            seen_l1.append(l1)
            l1_meta[l1] = node.get("l1_name", l1)
        nodes_in_l1.setdefault(l1, []).append(key)

    lines.append("## Gaps by L1 cycle")
    for l1 in seen_l1:
        node_keys = [k for k in nodes_in_l1[l1] if k in gaps_by_node]
        if not node_keys:
            continue
        lines.append("")
        lines.append(f"### {l1_meta[l1]} (`{l1}`)")
        for key in node_keys:
            node = state["nodes"][key]
            cov = node.get("coverage", "none")
            lines.append("")
            lines.append(f"- **{key}** — {node.get('l2_name', key)} "
                         f"(coverage: {cov})")
            for g in gaps_by_node[key]:
                lines.append(f"  - `{g['kind']}` ({g['tag']}): {g['observation']}")

    if not any(k in gaps_by_node for ks in nodes_in_l1.values() for k in ks):
        lines.append("")
        lines.append("_No structural gaps detected._")

    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def cmd_scan(eid: str, dry_run: bool) -> None:
    state_path, state = load_state(eid)
    existing = load_register_records(eid)
    detected = detect_gaps(state)

    # MD always reflects the freshly-detected set (even on dry-run).
    md_path = write_md(eid, state, detected)

    csv_rows = build_csv_rows(detected, existing)
    archived = sum(1 for r in csv_rows if r["record_status"] == "archived")

    if not dry_run:
        write_register(eid, csv_rows)

    by_kind: Dict[str, int] = {}
    for g in detected:
        by_kind[g["kind"]] = by_kind.get(g["kind"], 0) + 1

    mode = "DRY-RUN (register untouched)" if dry_run else "register updated"
    print(f"gap_report scan '{eid}' — {mode}")
    print(f"  active structural gaps: {len(detected)}")
    for kind in sorted(by_kind):
        print(f"    {kind}: {by_kind[kind]}")
    print(f"  stale archived this run: {archived}")
    print(f"  report: {md_path}")


def main() -> None:
    p = argparse.ArgumentParser(description="Stage 4 structural gap detection (gap_report).")
    sub = p.add_subparsers(dest="command", required=True)
    s = sub.add_parser("scan", help="Detect structural gaps, write register + gap_report.md.")
    s.add_argument("--engagement", required=True)
    s.add_argument("--dry-run", action="store_true",
                   help="Detect + write the md + print summary, but do not touch the register.")
    args = p.parse_args()
    if args.command == "scan":
        cmd_scan(args.engagement, args.dry_run)


if __name__ == "__main__":
    main()
