#!/usr/bin/env python3
"""orchestrate.py — state-driven "what's next" advisor (CONSULT pipeline).

READ-ONLY. This is the deterministic glue under the `consult-run` skill: it reads
the engagement `status` (state_machine.py `build_status` / the `status --json`
command) and returns the **single next action**, picked as a first-match walk
down the readiness order

    ingest -> classify -> merge -> consolidate -> gap -> draft -> synthesize
            -> render -> final | gate_blocked

For each action it reports the **targets** (which docs / nodes / L1s the agent
should act on) and whether the step is **deterministic** (the agent runs the
named Python script itself) or an **llm_fanout** (the agent spawns the named
sub-agent skill once per target).

This is the **state-driven** form of `orchestration_contract.md` §3/§5/§6 (T37):
it does NOT dead-end at the render gate. After render it handles the **review
re-entry** — a node marked diagnosis-dirty again (e.g. by review ingestion) loops
back to `consolidate -> draft -> render`; deliverable streams whose content `rev`
is ahead of their `rendered_rev` re-`render`. Once everything is rendered/reviewed
AND `gates.py final-check` passes, it recommends the terminal `final` action
(`kind=deterministic`, the agent applies it: it sets deliverable statuses
`final`). If `final-check` FAILS it returns `gate_blocked`, naming the failing
gates, and does NOT advance to `final`.

Idempotency / read-only: this command writes nothing — not state.json, not the
register, not any deliverable. It only derives the next step from state, so it is
safe to call on every loop iteration; the state byte-image is identical before
and after. All advancement is performed by the agent via the named scripts/skills
— including the `final` action it *recommends* (applied by the agent, not here).

Commands:
  next --engagement E [--json] [--all]

`--json` emits the machine action object; default prints a human-readable line.
`--all` lists **every** ready action on the frontier (not just the first).
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
    is_diagnosis_dirty,
    load_state,
)

# The read-only final-check gate (gates.py). Imported in-process so `next` and
# `final-check` never derive a different PASS/FAIL from the same state.
from gates import run_final_check

# The state-driven readiness order. `next` returns the first action whose
# readiness predicate fires. The walk no longer dead-ends at `render`: after
# render it loops back through consolidate/draft/render on review re-entry, then
# terminates at the gated `final` (or `gate_blocked` if a DoD gate fails).
#
# `done` remains in the order as the post-`final` terminal: once the agent has
# applied `final` (deliverable statuses set `final`), the frontier is empty and
# `next` reports `done`.
ORDER = [
    "ingest", "classify", "merge", "consolidate", "gap",
    "draft", "synthesize", "render", "final", "gate_blocked", "done",
]
# Back-compat alias: older readers / the `order` field name still say SLICE1.
SLICE1_ORDER = ORDER

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
    # `final` is deterministic and applied BY THE AGENT (not by `next`): it blesses
    # the rendered/reviewed deliverables `final` via state_machine.py set-sop /
    # set-improvement --status final. orchestrate.py only *recommends* it.
    "final":       {"kind": DETERMINISTIC, "script": "scripts/state_machine.py"},
    # `gate_blocked` is not an automatable action — it is a hard stop telling the
    # agent which DoD gate(s) must be cleared before `final` can be recommended.
    "gate_blocked": {"kind": None},
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
        # Fall back to the key-derived L1 when the node is absent OR present but
        # lacks/`None`s `l1` (a malformed node must not silently drop from the
        # draft target). Read-only command -> fall back, never raise.
        l1 = (node or {}).get("l1") or (key.split(".", 1)[0] if "." in key else key)
        if l1 and l1 not in seen:
            seen.append(l1)
    return seen


def _deliverable_exists(eid: str, rel: str) -> bool:
    return (engagement_dir(eid) / "deliverables" / rel).exists()


def _l1_ids(state: Dict[str, Any]) -> List[str]:
    seen: List[str] = []
    for key, node in state["nodes"].items():
        # Same fallback as `_l1s_of_nodes`: a node present but lacking/`None`-ing
        # `l1` falls back to its key-derived L1 rather than being dropped (it
        # drives render targets, so a drop would silently skip a stream).
        l1 = (node or {}).get("l1") or (key.split(".", 1)[0] if "." in key else key)
        if l1 and l1 not in seen:
            seen.append(l1)
    return seen


def decide_next(eid: str) -> Dict[str, Any]:
    """Derive the single next Slice-1 action + its targets. READ-ONLY.

    The single next action is `frontier(eid)[0]` — the first ready action in
    ORDER. `decide_next` and `frontier` therefore share ONE ordered builder
    (`frontier`), so they can never drift on a predicate (e.g. the `synthesize`
    gate, which requires `drafted_any` AND no `synthesis.md`): `next` reports
    exactly the head of the same frontier `next --all` lists. The frontier is
    never empty (the terminal `done`/`final`/`gate_blocked` always closes it), so
    indexing [0] is total.
    """
    return frontier(eid)[0]


def _all_deliverables_final(state: Dict[str, Any]) -> bool:
    """True once every started sop/improvement node block is status `final`.

    A node block that was never started (`not_started`) does not block `final`
    (there is nothing to bless). Returns False if there is no started block at
    all (nothing to finalize -> not yet a finished engagement)."""
    any_started = False
    for node in state["nodes"].values():
        for block in ("sop", "improvement"):
            art = node.get(block, {}) or {}
            status = str(art.get("status", "not_started"))
            if status == "not_started":
                continue
            any_started = True
            if status != "final":
                return False
    return any_started


def _finalizable_streams(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Started node blocks not yet `final` — the targets of the `final` action."""
    out: List[Dict[str, Any]] = []
    for key, node in sorted(state["nodes"].items()):
        for block in ("sop", "improvement"):
            art = node.get(block, {}) or {}
            status = str(art.get("status", "not_started"))
            if status not in ("not_started", "final"):
                out.append({"node": key, "block": block, "status": status})
    return out


def frontier(eid: str) -> List[Dict[str, Any]]:
    """Every ready action on the frontier (for `next --all`), in ORDER. READ-ONLY.

    Where `decide_next` returns the single first-match action, this returns the
    full set whose readiness predicate independently fires. Most stages are
    sequential (one fires at a time, matching `decide_next`), but several can
    coexist — e.g. `render` (a stale stream) alongside `draft` (a still-draftable
    node), or `synthesize` pending alongside a stale per-L1 render. The terminal
    `final`/`gate_blocked`/`done` are only offered once the pre-render frontier is
    empty (nothing left to ingest/classify/merge/consolidate/gap/draft/synthesize
    and nothing to render), so the gate is never reported prematurely.
    """
    # Clean guard for a bad --engagement (otherwise build_status/load_state raise
    # mid-walk). Read-only: matches render_deliverables.py's existence check.
    if not engagement_dir(eid).exists():
        raise SystemExit(f"No engagement '{eid}' at {engagement_dir(eid)}.")
    status = build_status(eid)
    _, state = load_state(eid)

    ingested = status["ingested_docs"]
    unclassified = status["unclassified_docs"]
    dirty = status["diagnosis_dirty_nodes"]
    draftable = status["draftable_nodes"]
    artifacts = _classify_artifacts(eid)
    open_gaps = status["open_gaps"]["total"]

    out: List[Dict[str, Any]] = []

    if ingested == 0:
        out.append(_action("ingest", status, targets={"docs": []},
                           summary="No ingested documents. Run ingest first."))
    if unclassified["count"] > 0:
        out.append(_action("classify", status,
                           targets={"docs": unclassified["docs"]},
                           summary=(f"{unclassified['count']} ingested doc(s) lack a "
                                    "classify artifact; fan out one classifier per doc.")))
    if artifacts and not _any_evidence(state):
        out.append(_action("merge", status, targets={"artifacts": artifacts},
                           summary=(f"{len(artifacts)} classify artifact(s) present and "
                                    "unmerged; run classify_merge.")))
    if dirty["count"] > 0:
        out.append(_action("consolidate", status, targets={"nodes": dirty["nodes"]},
                           summary=(f"{dirty['count']} diagnosis-dirty node(s); fan out "
                                    "one consolidator per node.")))
    if _any_evidence(state) and open_gaps == 0 and draftable["count"] > 0:
        out.append(_action("gap", status, targets={"scope": "engagement"},
                           summary="Run gap_report scan (structural + unmapped triage)."))
    if draftable["count"] > 0:
        l1s = _l1s_of_nodes(state, draftable["nodes"])
        out.append(_action("draft", status,
                           targets={"nodes": draftable["nodes"], "l1s": l1s},
                           summary=(f"{draftable['count']} draftable node(s) across "
                                    f"{len(l1s)} L1(s); fan out drafter + improvement-drafter.")))
    drafted_any = any(
        str((node.get(b, {}) or {}).get("status", "not_started")) != "not_started"
        for node in state["nodes"].values() for b in ("sop", "improvement"))
    if drafted_any and not _deliverable_exists(eid, "synthesis.md"):
        out.append(_action("synthesize", status, targets={"scope": "engagement"},
                           summary="Author the lead synthesis.md (cross-cutting POV)."))

    rendered = _rendered_targets(eid, state)
    pending_render = [
        t for t in rendered
        if (t["md_exists"] and not t["docx_exists"]) or t.get("stale")
    ]
    if pending_render:
        stale_any = any(t.get("stale") for t in pending_render)
        out.append(_action("render", status,
                           targets={"deliverables": pending_render},
                           summary=("Re-render redrafted deliverable(s) "
                                    "(rev > rendered_rev)." if stale_any
                                    else "Render deliverable MD(s) to .docx."),
                           gate="render"))

    # The terminal gate is only on the frontier once nothing pre-render is ready.
    # (decide_next applies the same precedence via its first-match walk.)
    pre_render_pending = bool(out)
    if not pre_render_pending:
        report = run_final_check(eid)
        if not report["passed"]:
            failing = [g for g in report["gates"] if not g["passed"]]
            out.append(_action("gate_blocked", status,
                               targets={"failing_gates": failing},
                               summary=("DoD final-check FAILED ("
                                        + ", ".join(g["gate"] for g in failing)
                                        + "); do NOT advance to `final`."),
                               gate="final"))
        elif _all_deliverables_final(state):
            out.append(_action("done", status, targets={},
                               summary="All deliverables final and DoD gates pass; "
                                       "engagement complete.",
                               gate="final"))
        else:
            out.append(_action("final", status,
                               targets={"deliverables": _finalizable_streams(state)},
                               summary="DoD final-check PASSED; apply the terminal "
                                       "`final` action (set statuses `final`).",
                               gate="final"))

    out.sort(key=lambda a: ORDER.index(a["action"]))
    return out


# Per-L1 deliverable stream -> the state node block whose rev markers drive it.
STREAM_TO_BLOCK = {"sop": "sop", "improvements": "improvement"}


def _l1_block_revs(state: Dict[str, Any], l1: str, block: str) -> Dict[str, int]:
    """Aggregate rev markers across an L1's nodes for one stream block.

    A per-L1 deliverable is rendered from the union of that L1's L2 node draft
    blocks. The stream is "stale vs render" if ANY contributing node's content
    `rev` is ahead of its `rendered_rev` (drafted/redrafted but not re-rendered),
    and "awaiting review" if `rendered_rev` is ahead of `reviewed_rev`. We surface
    the maxima so the loop can compare the stream as a whole.
    """
    max_rev = max_rendered = max_reviewed = 0
    any_started = False
    for node in state["nodes"].values():
        if node.get("l1") != l1:
            continue
        art = node.get(block, {}) or {}
        if str(art.get("status", "not_started")) != "not_started":
            any_started = True
        max_rev = max(max_rev, int(art.get("rev", 0)))
        max_rendered = max(max_rendered, int(art.get("rendered_rev", 0)))
        max_reviewed = max(max_reviewed, int(art.get("reviewed_rev", 0)))
    return {
        "rev": max_rev,
        "rendered_rev": max_rendered,
        "reviewed_rev": max_reviewed,
        "any_started": any_started,
    }


def _rendered_targets(eid: str, state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The deliverable render targets and whether each MD/.docx exists.

    Per-L1 streams additionally carry their aggregated rev markers + a `stale`
    flag (content `rev` ahead of `rendered_rev`) so the post-render loop can tell
    a re-render is owed after a redraft (the review re-entry path).
    """
    targets: List[Dict[str, Any]] = []
    # Engagement-level docs (no per-node rev markers).
    for name in ("synthesis", "gap_report"):
        targets.append({
            "what": name,
            "md": f"deliverables/{name}.md",
            "md_exists": _deliverable_exists(eid, f"{name}.md"),
            "docx_exists": _deliverable_exists(eid, f"{name}.docx"),
            "stale": False,
        })
    # Per-L1 streams.
    for l1 in _l1_ids(state):
        for stream in ("sop", "improvements"):
            revs = _l1_block_revs(state, l1, STREAM_TO_BLOCK[stream])
            md_exists = _deliverable_exists(eid, f"{stream}/{l1}.md")
            # Stale = content drafted past the last render (rev > rendered_rev).
            stale = revs["any_started"] and revs["rev"] > revs["rendered_rev"]
            targets.append({
                "what": stream,
                "l1": l1,
                "md": f"deliverables/{stream}/{l1}.md",
                "md_exists": md_exists,
                "docx_exists": _deliverable_exists(eid, f"{stream}/{l1}.docx"),
                "rev": revs["rev"],
                "rendered_rev": revs["rendered_rev"],
                "reviewed_rev": revs["reviewed_rev"],
                "stale": stale,
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
        delivs = targets["deliverables"]
        if delivs and "md" in delivs[0]:
            parts.append(", ".join(t["md"] for t in delivs))
        else:
            parts.append(", ".join(f"{t['node']}.{t['block']}" for t in delivs))
    if "failing_gates" in targets:
        parts.append(", ".join(g["gate"] for g in targets["failing_gates"]))
    if "scope" in targets:
        parts.append(targets["scope"])
    return " | ".join(p for p in parts if p)


def _print_action(obj: Dict[str, Any], header: str) -> None:
    kind = obj["kind"] or "-"
    print(f"  {header}: {obj['action']}  (kind={kind})")
    if obj.get("script"):
        print(f"    Script:  {obj['script']}")
    if obj.get("then_script"):
        print(f"    Then:    {obj['then_script']}")
    if obj.get("skill"):
        skill = obj["skill"]
        skill_s = ", ".join(skill) if isinstance(skill, list) else skill
        print(f"    Skill:   {skill_s}  (fan out one per target)")
    print(f"    Targets: {_fmt_targets(obj['targets'])}")
    if obj.get("gate"):
        print(f"    Gate:    {obj['gate']}")
    print(f"    {obj['summary']}")


def cmd_next(eid: str, as_json: bool, list_all: bool) -> None:
    if list_all:
        actions = frontier(eid)
        if as_json:
            print(json.dumps({"engagement": eid, "actions": actions, "order": ORDER},
                             ensure_ascii=False, indent=2))
            return
        print(f"Engagement: {eid}")
        print(f"  Ready actions ({len(actions)}):")
        for obj in actions:
            _print_action(obj, "action")
        return

    obj = decide_next(eid)
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
        return
    print(f"Engagement: {obj['engagement']}")
    _print_action(obj, "Next action")


# ---------------------------------------------------------------------------
# `measure` — read-only per-phase size walk (T56). Content-free.
# ---------------------------------------------------------------------------
# Mirrors `next`'s shape: a pure DERIVATION from disk state that writes nothing.
# It reports, per phase, the natural fan-out targets, an ESTIMATED input size per
# target (reusing the gatherers' own content-free sizing — `build_bundle` +
# `_measure_sections`), and the on-disk output artifact/MD sizes. Every figure is
# a number/count/fixed-label; no document text, refs, keys, or `source#loc`.


def _bytes_on_disk(path: Path) -> int:
    """File size in bytes (0 if absent). Read-only stat, never reads content."""
    try:
        return path.stat().st_size
    except OSError:
        return 0


def _input_size_for(build_bundle, sections_fn, *args) -> Optional[Dict[str, Any]]:
    """Content-free input-size summary for one target via a gatherer's own sizing.

    Reuses the gatherer's `build_bundle` + `_measure_sections` so `measure` and
    the `--measure` side-channel report identical numbers for the same fixture.
    Returns None (rather than raising) if a target's bundle can't be built — a
    measurement walk must not dead-end on one malformed node.
    """
    try:
        import measure_util
        bundle = build_bundle(*args)
        return measure_util.summarize(bundle, sections_fn(bundle))
    except Exception:
        return None


def _measure_phases(eid: str) -> Dict[str, Any]:
    """Per-phase content-free size map for the engagement. READ-ONLY.

    Phases mirror the gatherers: consolidate (per L2 node with evidence), draft
    (per L1), synthesize (whole engagement). Output sizes are the deliverable
    MD/.docx bytes on disk per phase.
    """
    if not engagement_dir(eid).exists():
        raise SystemExit(f"No engagement '{eid}' at {engagement_dir(eid)}.")

    import consolidate_inputs
    import draft_inputs
    import synthesis_inputs

    _, state = load_state(eid)
    edir = engagement_dir(eid)
    nodes = state["nodes"]
    l1s = _l1_ids(state)

    phases: List[Dict[str, Any]] = []

    # consolidate — one consolidator per L2 node carrying evidence.
    con_targets: List[Dict[str, Any]] = []
    for key in sorted(nodes):
        if not (nodes[key].get("evidence")):
            continue
        summ = _input_size_for(consolidate_inputs.build_bundle,
                               consolidate_inputs._measure_sections,
                               eid, key, False)
        con_targets.append({
            "target": key,
            "est_input_tokens": (summ or {}).get("est_tokens"),
            "input_chars": (summ or {}).get("total_chars"),
        })
    phases.append({
        "phase": "consolidate",
        "targets": len(con_targets),
        "per_target": con_targets,
        "est_input_tokens_total": sum(t["est_input_tokens"] or 0 for t in con_targets),
        "output_bytes": 0,  # consolidate writes node MDs (per-node, below in draft inputs)
    })

    # draft — one drafter per L1; output = the per-L1 SOP + improvements MD/.docx.
    draft_targets: List[Dict[str, Any]] = []
    draft_out_bytes = 0
    for l1 in l1s:
        summ = _input_size_for(draft_inputs.build_bundle,
                               draft_inputs._measure_sections, eid, l1)
        out_b = 0
        for stream in ("sop", "improvements"):
            out_b += _bytes_on_disk(edir / "deliverables" / stream / f"{l1}.md")
            out_b += _bytes_on_disk(edir / "deliverables" / stream / f"{l1}.docx")
        draft_out_bytes += out_b
        draft_targets.append({
            "target": l1,
            "est_input_tokens": (summ or {}).get("est_tokens"),
            "input_chars": (summ or {}).get("total_chars"),
            "output_bytes": out_b,
        })
    phases.append({
        "phase": "draft",
        "targets": len(draft_targets),
        "per_target": draft_targets,
        "est_input_tokens_total": sum(t["est_input_tokens"] or 0 for t in draft_targets),
        "output_bytes": draft_out_bytes,
    })

    # synthesize — whole engagement (one target); output = synthesis MD/.docx.
    syn = _input_size_for(synthesis_inputs.build_bundle,
                          synthesis_inputs._measure_sections, eid)
    syn_out = (_bytes_on_disk(edir / "deliverables" / "synthesis.md")
               + _bytes_on_disk(edir / "deliverables" / "synthesis.docx"))
    phases.append({
        "phase": "synthesize",
        "targets": 1,
        "per_target": [{
            "target": "engagement",
            "est_input_tokens": (syn or {}).get("est_tokens"),
            "input_chars": (syn or {}).get("total_chars"),
            "output_bytes": syn_out,
        }],
        "est_input_tokens_total": (syn or {}).get("est_tokens") or 0,
        "output_bytes": syn_out,
    })

    return {
        "engagement": eid,
        "est_tokens_basis": "chars/4 (estimate, not a tokenizer)",
        "phases": phases,
    }


def cmd_measure(eid: str, as_json: bool) -> None:
    report = _measure_phases(eid)
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    print(f"Engagement: {eid}  (read-only per-phase size map; "
          f"est. tokens = {report['est_tokens_basis']})")
    print(f"  {'phase':<12} {'#targets':>9} {'est.in.tok':>11} {'out.bytes':>11}")
    for ph in report["phases"]:
        print(f"  {ph['phase']:<12} {ph['targets']:>9} "
              f"{ph['est_input_tokens_total']:>11} {ph['output_bytes']:>11}")


def main() -> None:
    p = argparse.ArgumentParser(
        description="State-driven 'what's next' advisor (READ-ONLY).")
    sub = p.add_subparsers(dest="command", required=True)
    n = sub.add_parser("next", help="Print the next action (or --all ready actions).")
    n.add_argument("--engagement", required=True)
    n.add_argument("--json", action="store_true",
                   help="Emit the machine action object as JSON.")
    n.add_argument("--all", action="store_true", dest="list_all",
                   help="List every ready action on the frontier, not just the first.")
    m = sub.add_parser("measure",
                       help="READ-ONLY per-phase content-free size map (T56).")
    m.add_argument("--engagement", required=True)
    m.add_argument("--json", action="store_true",
                   help="Emit the machine size map as JSON.")
    args = p.parse_args()
    if args.command == "next":
        cmd_next(args.engagement, args.json, args.list_all)
    elif args.command == "measure":
        cmd_measure(args.engagement, args.json)


if __name__ == "__main__":
    main()
