#!/usr/bin/env python3
"""state_machine.py — engagement node tracker (Layer 1).

The state machine seeds and maintains one node per L2 taxonomy node for an
engagement. It is the diagnostic backbone: per-L2 coverage, evidence, the 5
diagnostic lenses, and links to the Item Register (Layer 2, register.json,
managed by improvement_log.py).

Two coupled artifacts per engagement (under engagements/{id}/):
  - state.json   : node tracker (this script owns it)
  - register.json: flat item register (improvement_log.py owns it)
  - nodes/{l1}/{l2}.md : human-readable per-L2 synthesis (LLM owns it)

Commands:
  init      Seed state.json + register.json + empty node MDs from the taxonomy.
  sync      Roll Item Register rows up into node item links / counts; recompute
            coverage. Reports register rows whose node key is not in the taxonomy.
  show      Print a coverage summary.
  validate  Check structural invariants (one node per taxonomy L2, no orphans).
"""
from __future__ import annotations

import argparse, json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = REPO_ROOT / "reference" / "taxonomy.yaml"
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"

LENSES = ["current_state", "process", "automation", "capability", "operating_model"]
ITEM_BUCKETS = ["improvements", "gaps", "screenshots"]
TYPE_TO_BUCKET = {"improvement": "improvements", "gap": "gaps", "screenshot": "screenshots"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_taxonomy() -> Dict[str, Any]:
    with TAXONOMY_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def iter_l2(taxonomy: Dict[str, Any]):
    """Yield (l1_id, l1_name, l2_id, l2_name, l3_list) for every L2 node."""
    for dom in taxonomy.get("domains", []):
        for l2 in dom.get("l2", []):
            yield dom["id"], dom["name"], l2["id"], l2["name"], list(l2.get("l3", []))


def node_key(l1: str, l2: str) -> str:
    return f"{l1}.{l2}"


def new_node(l1: str, l1_name: str, l2: str, l2_name: str) -> Dict[str, Any]:
    return {
        "l1": l1, "l1_name": l1_name, "l2": l2, "l2_name": l2_name,
        "coverage": "none",
        "evidence": [],
        "lenses": {lens: None for lens in LENSES},
        "items": {bucket: [] for bucket in ITEM_BUCKETS},
        "counts": {bucket: 0 for bucket in ITEM_BUCKETS},
        "sop": {"status": "not_started", "path": None, "rev": 0},
        "node_md": f"nodes/{l1}/{l2}.md",
        "updated": now_iso(),
    }


def node_md_stub(l1: str, l1_name: str, l2: str, l2_name: str, l3: List[str]) -> str:
    key = node_key(l1, l2)
    activities = "\n".join(f"- {name}" for name in l3) or "- (none listed)"
    fm = (
        "---\n"
        f"node: {key}\n"
        f"l1: {l1}\n"
        f"l1_name: {l1_name}\n"
        f"l2: {l2}\n"
        f"l2_name: {l2_name}\n"
        "coverage: none\n"
        "lenses:\n"
        + "".join(f"  {lens}: null\n" for lens in LENSES)
        + "---\n"
    )
    return (
        fm
        + f"\n# {l1_name} — {l2_name}\n\n"
        "> Empty node. An empty node is itself a finding (coverage: none).\n\n"
        "## L3 activities (from taxonomy)\n\n"
        f"{activities}\n\n"
        "## What we learned\n\n_TBD_\n\n"
        "## Evidence digest\n\n_TBD_\n\n"
        "## Diagnosis (5 lenses)\n\n_TBD_\n\n"
        "## Open gaps\n\n_TBD_\n"
    )


def engagement_dir(eid: str) -> Path:
    return ENGAGEMENTS_DIR / eid


def cmd_init(eid: str, client: str, region: str, force: bool) -> None:
    edir = engagement_dir(eid)
    state_path = edir / "state.json"
    if state_path.exists() and not force:
        raise SystemExit(f"state.json already exists at {state_path}; pass --force to reseed.")
    taxonomy = load_taxonomy()
    ts = now_iso()
    nodes: Dict[str, Any] = {}
    for l1, l1_name, l2, l2_name, l3 in iter_l2(taxonomy):
        key = node_key(l1, l2)
        nodes[key] = new_node(l1, l1_name, l2, l2_name)
        md_path = edir / "nodes" / l1 / f"{l2}.md"
        md_path.parent.mkdir(parents=True, exist_ok=True)
        if force or not md_path.exists():
            md_path.write_text(node_md_stub(l1, l1_name, l2, l2_name, l3), encoding="utf-8")

    state = {
        "engagement": {
            "id": eid, "client": client, "region": region,
            "created": ts, "updated": ts,
        },
        "taxonomy_version": taxonomy.get("version"),
        "nodes": nodes,
    }
    edir.mkdir(parents=True, exist_ok=True)
    (edir / "deliverables" / "sop").mkdir(parents=True, exist_ok=True)
    (edir / "deliverables" / "improvements").mkdir(parents=True, exist_ok=True)
    (edir / "ingested").mkdir(parents=True, exist_ok=True)
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    register_path = edir / "register.json"
    if force or not register_path.exists():
        register = {"metadata": {"engagement": eid, "record_count": 0}, "records": []}
        with register_path.open("w", encoding="utf-8") as f:
            json.dump(register, f, ensure_ascii=False, indent=2)

    print(f"Initialized engagement '{eid}' with {len(nodes)} L2 nodes at {edir}")


def load_state(eid: str) -> Tuple[Path, Dict[str, Any]]:
    state_path = engagement_dir(eid) / "state.json"
    if not state_path.exists():
        raise SystemExit(f"No state.json for engagement '{eid}'. Run init first.")
    with state_path.open("r", encoding="utf-8") as f:
        return state_path, json.load(f)


def load_register(eid: str) -> List[Dict[str, Any]]:
    register_path = engagement_dir(eid) / "register.json"
    if not register_path.exists():
        return []
    with register_path.open("r", encoding="utf-8") as f:
        return json.load(f).get("records", [])


def derive_coverage(node: Dict[str, Any]) -> str:
    has_evidence = bool(node.get("evidence"))
    has_items = any(node["counts"].get(b, 0) for b in ITEM_BUCKETS)
    all_lenses = all(node["lenses"].get(lens) for lens in LENSES)
    if not has_evidence and not has_items:
        return "none"
    if has_evidence and all_lenses:
        return "covered"
    return "partial"


def cmd_sync(eid: str) -> None:
    state_path, state = load_state(eid)
    records = load_register(eid)
    nodes = state["nodes"]

    # reset item links/counts before re-rolling
    for node in nodes.values():
        node["items"] = {b: [] for b in ITEM_BUCKETS}
        node["counts"] = {b: 0 for b in ITEM_BUCKETS}

    orphans: List[str] = []
    for rec in records:
        if str(rec.get("record_status", "active")).lower() in {"archived", "inactive"}:
            continue
        l1, l2 = rec.get("l1_cycle"), rec.get("l2_process")
        if not l1 or not l2:
            orphans.append(f"{rec.get('id')} (missing l1_cycle/l2_process)")
            continue
        key = node_key(l1, l2)
        node = nodes.get(key)
        if node is None:
            orphans.append(f"{rec.get('id')} -> {key} (not in taxonomy)")
            continue
        bucket = TYPE_TO_BUCKET.get(str(rec.get("type", "improvement")).lower(), "improvements")
        node["items"][bucket].append(rec.get("id"))
        node["counts"][bucket] += 1

    ts = now_iso()
    for node in nodes.values():
        node["coverage"] = derive_coverage(node)
        node["updated"] = ts
    state["engagement"]["updated"] = ts

    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    linked = sum(sum(n["counts"].values()) for n in nodes.values())
    print(f"Synced {len(records)} register rows into {len(nodes)} nodes; {linked} active items linked.")
    if orphans:
        print(f"Orphan rows ({len(orphans)}):")
        for o in orphans:
            print(f"  - {o}")


def cmd_show(eid: str) -> None:
    _, state = load_state(eid)
    nodes = state["nodes"]
    by_cov = {"none": 0, "partial": 0, "covered": 0}
    for node in nodes.values():
        by_cov[node.get("coverage", "none")] = by_cov.get(node.get("coverage", "none"), 0) + 1
    eng = state["engagement"]
    print(f"Engagement: {eng['id']} | client: {eng.get('client')} | region: {eng.get('region')}")
    print(f"Nodes: {len(nodes)} | coverage none={by_cov['none']} partial={by_cov['partial']} covered={by_cov['covered']}")
    for key, node in sorted(nodes.items()):
        c = node["counts"]
        if c["improvements"] or c["gaps"] or c["screenshots"] or node["coverage"] != "none":
            print(f"  {key:48s} {node['coverage']:8s} "
                  f"imp={c['improvements']} gap={c['gaps']} sc={c['screenshots']} sop={node['sop']['status']}")


def cmd_validate(eid: str) -> None:
    _, state = load_state(eid)
    taxonomy = load_taxonomy()
    expected = {node_key(l1, l2) for l1, _, l2, _, _ in iter_l2(taxonomy)}
    actual = set(state["nodes"].keys())
    missing = expected - actual
    extra = actual - expected
    print(f"Taxonomy L2 nodes: {len(expected)} | state nodes: {len(actual)}")
    if missing:
        print(f"MISSING nodes ({len(missing)}): {sorted(missing)}")
    if extra:
        print(f"EXTRA nodes not in taxonomy ({len(extra)}): {sorted(extra)}")
    if not missing and not extra:
        print("OK: state nodes exactly match the taxonomy L2 set.")


def main() -> None:
    p = argparse.ArgumentParser(description="Engagement node tracker (state.json).")
    sub = p.add_subparsers(dest="command", required=True)
    i = sub.add_parser("init", help="Seed state.json + register.json + node MDs.")
    i.add_argument("--engagement", required=True)
    i.add_argument("--client", default="")
    i.add_argument("--region", default="NA")
    i.add_argument("--force", action="store_true", help="Reseed even if state.json exists.")
    for name, help_text in (("sync", "Roll register rows into nodes; recompute coverage."),
                            ("show", "Print coverage summary."),
                            ("validate", "Check node set against the taxonomy.")):
        s = sub.add_parser(name, help=help_text)
        s.add_argument("--engagement", required=True)
    args = p.parse_args()
    if args.command == "init":
        cmd_init(args.engagement, args.client, args.region, args.force)
    elif args.command == "sync":
        cmd_sync(args.engagement)
    elif args.command == "show":
        cmd_show(args.engagement)
    elif args.command == "validate":
        cmd_validate(args.engagement)


if __name__ == "__main__":
    main()
