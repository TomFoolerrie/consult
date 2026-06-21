#!/usr/bin/env python3
"""orchestrate.py — Slice-1 linear "what's next" advisor (CONSULT pipeline).

READ-ONLY. This is the deterministic glue under the `consult-run` skill: it reads
the engagement `status` (state_machine.py `build_status` / the `status --json`
command) and returns the **single next Slice-1 action**, in the fixed linear
order

    ingest -> classify -> merge -> consolidate -> gap -> draft -> synthesize
            -> render -> done

For each action it reports the **targets** (which docs / nodes / L1s the agent
should act on) and whether the step is **deterministic** (the agent runs the
named Python script itself) or an **llm_fanout** (the agent spawns the named
sub-agent skill once per target).

This is the **Slice-1 linear** form of `orchestration_contract.md` §3/§5: a
one-way walk that **stops at the render gate** (it never auto-finalizes, never
ingests review). The state-driven readiness loop (S2/T37) is out of scope here.

Idempotency / read-only: this command writes nothing — not state.json, not the
register, not any deliverable. It only derives the next step from state, so it is
safe to call on every loop iteration; the state byte-image is identical before
and after. All advancement is performed by the agent via the named scripts/skills.

Command:
  next --engagement E [--json]

`--json` emits the machine action object; default prints a human-readable line.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# Reuse the T04 status signal directly (same process, no re-derivation drift).
from state_machine import (
    DRAFTABLE_COVERAGE,
    build_status,
    engagement_dir,
    load_state,
)

# The fixed Slice-1 linear order. `next` returns exactly one of these (the first
# whose readiness predicate fires), or `done` at the render gate.
SLICE1_ORDER = [
    "ingest", "classify", "merge", "consolidate", "gap",
    "draft", "synthesize", "render", "done",
]

# Per-action dispatch kind (orchestration_contract.md §5 "Kind" column,
# Slice-1 subset). Deterministic = the agent runs the script; llm_fanout = the
# agent spawns the named sub-agent skill once per target.
DETERMINISTIC = "deterministic"
LLM_FANOUT = "llm_fanout"

# Action -> (kind, the script the agent runs | the skill(s) it fans out).
ACTION_DISPATCH: Dict[str, Dict[str, Any]] = {
    "ingest":      {"kind": DETERMINISTIC, "script": "scripts/ingest_normalize.py"},
    "classify":    {"kind": LLM_FANOUT,    "skill": "consult-classifier",
                    "then": "scripts/classify_merge.py"},
    "merge":       {"kind": DETERMINISTIC, "script": "scripts/classify_merge.py"},
    "consolidate": {"kind": LLM_FANOUT,    "skill": "consult-consolidator"},
    "gap":         {"kind": DETERMINISTIC, "script": "scripts/gap_report.py"},
    "draft":       {"kind": LLM_FANOUT,    "skill": ["consult-drafter",
                                                     "consult-improvement-drafter"]},
    "synthesize":  {"kind": LLM_FANOUT,    "skill": "consult-synthesizer"},
    "render":      {"kind": DETERMINISTIC, "script": "scripts/render_deliverables.py"},
    "done":        {"kind": None},
}


def _classify_artifacts(eid: str) -> List[str]:
    """Names of classify artifacts on disk (the merge's inputs). Read-only."""
    cdir = engagement_dir(eid) / "classify"
    if not cdir.is_dir():
        return []
    return sorted(p.name for p in cdir.glob("*.artifact.json"))


def _any_evidence(state: Dict[str, Any]) -> bool:
    """True if any node carries evidence (i.e. a merge has applied facts)."""
    return any(node.get("evidence") for node in state["nodes"].values())


def _l1s_of_nodes(state: Dict[str, Any], node_keys: List[str]) -> List[str]:
    """Distinct L1 ids (taxonomy order of appearance) for a set of node keys."""
    seen: List[str] = []
    for key in node_keys:
        node = state["nodes"].get(key)
        l1 = node.get("l1") if node else (key.split(".", 1)[0] if "." in key else key)
        if l1 and l1 not in seen:
            seen.append(l1)
    return seen


def _deliverable_exists(eid: str, rel: str) -> bool:
    return (engagement_dir(eid) / "deliverables" / rel).exists()


def _l1_ids(state: Dict[str, Any]) -> List[str]:
    seen: List[str] = []
    for node in state["nodes"].values():
        l1 = node.get("l1")
        if l1 and l1 not in seen:
            seen.append(l1)
    return seen


def decide_next(eid: str) -> Dict[str, Any]:
    """Derive the single next Slice-1 action + its targets. READ-ONLY.

    Readiness is a first-match walk down SLICE1_ORDER. Each predicate is a pure
    function of `status` (T04) + on-disk classify artifacts + deliverable MDs —
    so re-running re-derives the same answer until the agent advances the state.
    """
    status = build_status(eid)
    _, state = load_state(eid)
    nodes = state["nodes"]

    ingested = status["ingested_docs"]
    unclassified = status["unclassified_docs"]
    dirty = status["diagnosis_dirty_nodes"]
    draftable = status["draftable_nodes"]
    artifacts = _classify_artifacts(eid)

    # --- 1. ingest: nothing ingested yet ---
    if ingested == 0:
        action = "ingest"
        return _action(action, status,
                       targets={"docs": []},
                       summary="No ingested documents. Run ingest first.")

    # --- 2. classify: ingested docs without a classify artifact (fan-out) ---
    if unclassified["count"] > 0:
        return _action("classify", status,
                       targets={"docs": unclassified["docs"]},
                       summary=(f"{unclassified['count']} ingested doc(s) lack a "
                                "classify artifact; fan out one classifier per doc."))

    # --- 3. merge: artifacts present, not yet merged (no evidence applied) ---
    # After ingest+classify, every ingested doc has an artifact (count above is
    # 0). If the merge has not yet applied those facts, no node carries evidence.
    if artifacts and not _any_evidence(state):
        return _action("merge", status,
                       targets={"artifacts": artifacts},
                       summary=(f"{len(artifacts)} classify artifact(s) present and "
                                "unmerged; run classify_merge to apply evidence + lenses."))

    # --- 4. consolidate: diagnosis-dirty nodes (new evidence since synthesis) ---
    if dirty["count"] > 0:
        return _action("consolidate", status,
                       targets={"nodes": dirty["nodes"]},
                       summary=(f"{dirty['count']} diagnosis-dirty node(s); fan out one "
                                "consolidator per node."))

    # --- 5. gap: consolidated; run the structural gap scan (deterministic) ---
    # Slice-1 linear runs the scan once consolidation has settled (no dirty
    # nodes) and evidence exists. The scan is idempotent (self-healing upsert),
    # so it fires until structural rows exist; thereafter draftables take over.
    open_gaps = status["open_gaps"]["total"]
    if _any_evidence(state) and open_gaps == 0 and draftable["count"] > 0:
        return _action("gap", status,
                       targets={"scope": "engagement"},
                       summary="Diagnosis consolidated; run gap_report scan "
                               "(structural + unmapped triage).")

    # --- 6. draft: covered/partial nodes whose SOP/improvement not started ---
    if draftable["count"] > 0:
        l1s = _l1s_of_nodes(state, draftable["nodes"])
        return _action("draft", status,
                       targets={"nodes": draftable["nodes"], "l1s": l1s},
                       summary=(f"{draftable['count']} draftable node(s) across "
                                f"{len(l1s)} L1(s); fan out drafter + improvement-drafter "
                                "per L1 bundle."))

    # --- 7. synthesize: streams drafted; lead synthesis.md not yet authored ---
    if not _deliverable_exists(eid, "synthesis.md"):
        return _action("synthesize", status,
                       targets={"scope": "engagement"},
                       summary="Bottom-up streams drafted; author the lead "
                               "synthesis.md (cross-cutting point of view).")

    # --- 8. render: deliverables built, not yet rendered to .docx (GATE) ---
    rendered = _rendered_targets(eid, state)
    pending_render = [t for t in rendered if t["md_exists"] and not t["docx_exists"]]
    if pending_render:
        return _action("render", status,
                       targets={"deliverables": pending_render},
                       summary=("Deliverable MD(s) not yet rendered to .docx; run "
                                "render_deliverables, then STOP at the render gate "
                                "(human review — no auto-finalize)."),
                       gate="render")

    # --- 9. done: render gate reached ---
    return _action("done", status,
                   targets={},
                   summary="Render gate reached: all built deliverables are "
                           "rendered. Stop and report (no review ingestion in Slice 1).",
                   gate="render")


def _rendered_targets(eid: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The Slice-1 deliverable render targets and whether each MD/.docx exists."""
    targets: List[Dict[str, Any]] = []
    # Engagement-level docs.
    for name in ("synthesis", "gap_report"):
        targets.append({
            "what": name,
            "md": f"deliverables/{name}.md",
            "md_exists": _deliverable_exists(eid, f"{name}.md"),
            "docx_exists": _deliverable_exists(eid, f"{name}.docx"),
        })
    # Per-L1 streams.
    for l1 in _l1_ids(state):
        for stream in ("sop", "improvements"):
            targets.append({
                "what": stream,
                "l1": l1,
                "md": f"deliverables/{stream}/{l1}.md",
                "md_exists": _deliverable_exists(eid, f"{stream}/{l1}.md"),
                "docx_exists": _deliverable_exists(eid, f"{stream}/{l1}.docx"),
            })
    return targets


def _action(action: str, status: Dict[str, Any], targets: Dict[str, Any],
            summary: str, gate: Optional[str] = None) -> Dict[str, Any]:
    """Assemble the machine action object for one decided step."""
    dispatch = ACTION_DISPATCH[action]
    obj: Dict[str, Any] = {
        "engagement": status["engagement"],
        "action": action,
        "kind": dispatch.get("kind"),
        "targets": targets,
        "summary": summary,
        "order": SLICE1_ORDER,
    }
    if "script" in dispatch:
        obj["script"] = dispatch["script"]
    if "then" in dispatch:
        obj["then_script"] = dispatch["then"]
    if "skill" in dispatch:
        obj["skill"] = dispatch["skill"]
    if gate:
        obj["gate"] = gate
    return obj


def _fmt_targets(targets: Dict[str, Any]) -> str:
    if not targets:
        return "-"
    parts: List[str] = []
    if "docs" in targets:
        docs = targets["docs"]
        parts.append(", ".join(d.get("path", str(d)) for d in docs) if docs else "(none)")
    if "artifacts" in targets:
        parts.append(", ".join(targets["artifacts"]))
    if "nodes" in targets:
        parts.append(", ".join(targets["nodes"]))
    if "l1s" in targets:
        parts.append("L1s: " + ", ".join(targets["l1s"]))
    if "deliverables" in targets:
        parts.append(", ".join(t["md"] for t in targets["deliverables"]))
    if "scope" in targets:
        parts.append(targets["scope"])
    return " | ".join(p for p in parts if p)


def cmd_next(eid: str, as_json: bool) -> None:
    obj = decide_next(eid)
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        return
    kind = obj["kind"] or "-"
    print(f"Engagement: {obj['engagement']}")
    print(f"  Next action: {obj['action']}  (kind={kind})")
    if obj.get("script"):
        print(f"  Script:  {obj['script']}")
    if obj.get("then_script"):
        print(f"  Then:    {obj['then_script']}")
    if obj.get("skill"):
        skill = obj["skill"]
        skill_s = ", ".join(skill) if isinstance(skill, list) else skill
        print(f"  Skill:   {skill_s}  (fan out one per target)")
    print(f"  Targets: {_fmt_targets(obj['targets'])}")
    if obj.get("gate"):
        print(f"  Gate:    {obj['gate']} (stop + report; no auto-finalize)")
    print(f"  {obj['summary']}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="Slice-1 linear 'what's next' advisor (READ-ONLY).")
    sub = p.add_subparsers(dest="command", required=True)
    n = sub.add_parser("next", help="Print the single next Slice-1 action.")
    n.add_argument("--engagement", required=True)
    n.add_argument("--json", action="store_true",
                   help="Emit the machine action object as JSON.")
    args = p.parse_args()
    if args.command == "next":
        cmd_next(args.engagement, args.json)


if __name__ == "__main__":
    main()
