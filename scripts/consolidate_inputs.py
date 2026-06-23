#!/usr/bin/env python3
"""consolidate_inputs.py — Stage-3 consolidate input gatherer (CONSULT pipeline).

READ-ONLY helper. Assembles the per-L2 bundle a `consult-consolidator` sub-agent
needs to do its judgment work for one node: the node's state (lenses, coverage,
evidence), the register rows already on the node, and the **staged
`candidate_findings`** from every classify artifact whose `node_hit.node == KEY`
(each carried with its `evidence_ref`, `evidence_tier`, and a proposed stable
`dedup_key`). Optionally resolves the cited evidence excerpts from the immutable
ingested MDs.

This script never writes state.json / register.json / any artifact. It only
reads, and exists so the LLM gets a clean, complete, deterministic input set
instead of foraging across files. The judgment (confirm/dedup findings, author
the node MD) is the sub-agent's; the orchestration (add-item, mark-consolidated)
is the command path's. See consolidate_contract.md §2 (inputs), §3 (sequence),
§4 (confirmation policy + dedup_key).

Command:
  gather --engagement E --node KEY [--json] [--excerpts]

`--json` emits the machine bundle; default prints a human-readable summary.
`--excerpts` resolves the cited MD lines into the bundle (off by default — it
reads the ingested MDs, still read-only).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"

# Mirror state_machine.py's lens order (kept local to avoid import coupling).
LENSES = ["current_state", "process", "automation", "capability", "operating_model"]

# Parse a `path#Lstart-Lend` (or `path#Lstart`) evidence ref into its parts.
_REF_RE = re.compile(r"^(?P<path>.+?)#L(?P<start>[0-9]+)(?:-(?P<end>[0-9]+))?$")

# Register row statuses that should not surface as live node items (aligned with
# state_machine.INACTIVE_STATUSES / improvement_log ARCHIVE∪DELETE statuses).
INACTIVE_STATUSES = {"archived", "inactive", "deleted_candidate", "deleted",
                     "delete", "removed", "remove"}


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


def load_artifacts(eid: str) -> List[Tuple[Path, Dict[str, Any]]]:
    """Load every classify/*.artifact.json that parses as JSON (read-only).

    A malformed artifact is skipped silently here — the merge (T12) and the
    validator own artifact health; this gatherer just reads what is staged.
    """
    classify_dir = engagement_dir(eid) / "classify"
    out: List[Tuple[Path, Dict[str, Any]]] = []
    if not classify_dir.is_dir():
        return out
    for art in sorted(classify_dir.glob("*.artifact.json")):
        try:
            with art.open("r", encoding="utf-8") as f:
                out.append((art, json.load(f)))
        except (OSError, json.JSONDecodeError):
            continue
    return out


# ---- finding extraction -----------------------------------------------------

def _is_active(rec: Dict[str, Any]) -> bool:
    return str(rec.get("record_status", "active") or "active").lower() not in INACTIVE_STATUSES


def _normalize_observation(text: str) -> str:
    """Lowercase + collapse whitespace + strip punctuation tails for the dedup seed."""
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    return text


def proposed_dedup_key(node: str, ftype: str, observation: str, evidence_ref: str) -> str:
    """Deterministic stable dedup_key seed: {node}|{type}|{normalized-obs-or-ref}.

    Mirrors consolidate_contract.md §4: stable from node + type + (normalized
    observation, else the primary evidence ref). The sub-agent may refine the
    normalized tail, but the shape is fixed so re-consolidation upserts the same
    row rather than minting a fresh IMP-/GAP- id.
    """
    norm = _normalize_observation(observation)
    tail = norm or (evidence_ref or "").strip()
    return f"{node}|{ftype}|{tail}"


def gather_candidate_findings(eid: str, key: str) -> List[Dict[str, Any]]:
    """Staged candidate_findings from every artifact whose node_hit.node == KEY.

    Each is enriched with its source artifact, evidence_ref, evidence_tier (the
    tier of the node-evidence that backs the ref, if known), and a proposed
    stable dedup_key. Tiers/refs are passed through, not invented.
    """
    findings: List[Dict[str, Any]] = []
    for art_path, artifact in load_artifacts(eid):
        doc = artifact.get("doc", {}) or {}
        for hit in artifact.get("node_hits", []) or []:
            if hit.get("node") != key:
                continue
            for cf in hit.get("candidate_findings", []) or []:
                ftype = cf.get("type")
                observation = cf.get("observation", "")
                evidence_ref = cf.get("evidence_ref", "")
                findings.append({
                    "type": ftype,
                    "tag": cf.get("tag"),
                    "confidence": cf.get("confidence"),
                    "observation": observation,
                    "recommended_action": cf.get("recommended_action"),
                    "evidence_ref": evidence_ref,
                    "evidence_tier": cf.get("evidence_tier"),
                    "proposed_dedup_key": proposed_dedup_key(
                        key, ftype or "", observation, evidence_ref),
                    "source_artifact": art_path.name,
                    "source_doc": doc.get("source"),
                })
    return findings


# ---- evidence excerpt resolution (optional, still read-only) ----------------

def resolve_excerpt(eid: str, ref: str) -> Optional[Dict[str, Any]]:
    """Resolve a `path#Lstart-Lend` ref to its lines in the immutable MD.

    Returns {ref, path, loc, lines:[...]} or None if the ref is unparseable /
    out of range. Read-only; guards against paths escaping the engagement dir.
    """
    m = _REF_RE.match(ref or "")
    if not m:
        return None
    rel_path = m.group("path")
    start = int(m.group("start"))
    end = int(m.group("end")) if m.group("end") else start
    if end < start or start < 1:
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
        all_lines = md_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if start > len(all_lines):
        return None
    excerpt = all_lines[start - 1:min(end, len(all_lines))]
    return {
        "ref": ref,
        "path": rel_path,
        "loc": f"L{start}-{end}" if end != start else f"L{start}",
        "lines": excerpt,
    }


# ---- bundle assembly --------------------------------------------------------

def build_bundle(eid: str, key: str, with_excerpts: bool) -> Dict[str, Any]:
    state = load_state(eid)
    node = state["nodes"].get(key)
    if node is None:
        raise SystemExit(f"Node '{key}' not found in state.json for engagement '{eid}'.")

    # Existing register rows on this node (active only — archived rows are not
    # live items the consolidation should re-cite).
    l1, l2 = node.get("l1"), node.get("l2")
    register_rows: List[Dict[str, Any]] = []
    for rec in load_register(eid):
        if not _is_active(rec):
            continue
        if rec.get("l1_cycle") == l1 and rec.get("l2_process") == l2:
            register_rows.append(rec)

    findings = gather_candidate_findings(eid, key)

    bundle: Dict[str, Any] = {
        "engagement": state["engagement"]["id"],
        "node": {
            "key": key,
            "l1": l1, "l1_name": node.get("l1_name"),
            "l2": l2, "l2_name": node.get("l2_name"),
            "coverage": node.get("coverage"),
            "lenses": {lens: node["lenses"].get(lens) for lens in LENSES},
            "evidence": node.get("evidence", []),
            "node_md": node.get("node_md"),
            "last_evidence_at": node.get("last_evidence_at"),
            "consolidated_at": node.get("consolidated_at"),
        },
        "register_rows": register_rows,
        "candidate_findings": findings,
    }

    if with_excerpts:
        # Resolve excerpts for node evidence refs + every finding evidence_ref.
        excerpts: Dict[str, Any] = {}
        for ev in node.get("evidence", []):
            src = ev.get("source")
            loc = ev.get("loc")
            ref = f"{src}#{loc}" if src and loc else None
            if ref:
                resolved = resolve_excerpt(eid, ref)
                if resolved:
                    excerpts[ref] = resolved
        for cf in findings:
            ref = cf.get("evidence_ref")
            if ref and ref not in excerpts:
                resolved = resolve_excerpt(eid, ref)
                if resolved:
                    excerpts[ref] = resolved
        bundle["evidence_excerpts"] = excerpts

    return bundle


# ---- rendering --------------------------------------------------------------

def print_human(bundle: Dict[str, Any]) -> None:
    node = bundle["node"]
    print(f"Engagement: {bundle['engagement']}  |  Node: {node['key']}")
    print(f"  {node['l1_name']} — {node['l2_name']}  (coverage={node['coverage']})")
    lenses = " ".join(f"{lens}={node['lenses'].get(lens)}" for lens in LENSES)
    print(f"  lenses: {lenses}")
    print(f"  evidence ({len(node['evidence'])}):")
    for ev in node["evidence"]:
        ref = f"{ev.get('source')}#{ev.get('loc')}" if ev.get('loc') else ev.get('source')
        tier = ev.get("tier")
        note = ev.get("note")
        print(f"    - {ref}" + (f" [{tier}]" if tier else "") + (f" — {note}" if note else ""))
    print(f"  diagnosis-dirty: last_evidence_at={node['last_evidence_at']} "
          f"consolidated_at={node['consolidated_at']}")

    rows = bundle["register_rows"]
    print(f"  existing register rows ({len(rows)}):")
    for r in rows:
        print(f"    - {r.get('id')} [{r.get('type')}] {r.get('observation_pain_point') or ''} "
              f"(dedup_key={r.get('dedup_key')})")

    findings = bundle["candidate_findings"]
    print(f"  staged candidate_findings ({len(findings)}):")
    for cf in findings:
        print(f"    - [{cf['type']}/{cf.get('tag')}] conf={cf.get('confidence')} "
              f"tier={cf.get('evidence_tier')} ref={cf.get('evidence_ref')}")
        print(f"      obs: {cf.get('observation')}")
        print(f"      proposed dedup_key: {cf['proposed_dedup_key']}")
        print(f"      from: {cf.get('source_artifact')}")

    if "evidence_excerpts" in bundle:
        print(f"  resolved excerpts ({len(bundle['evidence_excerpts'])}):")
        for ref, ex in bundle["evidence_excerpts"].items():
            print(f"    - {ref}: {' / '.join(ex['lines'])[:120]}")


def cmd_gather(eid: str, key: str, as_json: bool, with_excerpts: bool) -> None:
    bundle = build_bundle(eid, key, with_excerpts)
    if as_json:
        print(json.dumps(bundle, ensure_ascii=False, indent=2))
    else:
        print_human(bundle)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Read-only Stage-3 consolidate input gatherer (per L2 node).")
    sub = p.add_subparsers(dest="command", required=True)

    g = sub.add_parser("gather", help="Assemble the per-L2 consolidate input bundle.")
    g.add_argument("--engagement", required=True)
    g.add_argument("--node", required=True, help="L2 node key, e.g. record-to-report.close.")
    g.add_argument("--json", action="store_true", help="Emit the machine bundle as JSON.")
    g.add_argument("--excerpts", action="store_true",
                   help="Resolve cited MD lines into the bundle (reads ingested MDs; still read-only).")

    args = p.parse_args()
    if args.command == "gather":
        cmd_gather(args.engagement, args.node, args.json, args.excerpts)


if __name__ == "__main__":
    main()
