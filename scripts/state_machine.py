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
  init          Seed state.json + register.json + empty node MDs from the taxonomy.
  sync          Roll Item Register rows up into node item links / counts; recompute
                coverage. Reports register rows whose node key is not in the taxonomy.
  show          Print a coverage summary.
  validate      Check structural invariants (one node per taxonomy L2, no orphans).
  get-node      Print one node (compact lines, or --json for the full dict).
  query         List node keys matching coverage/lens/gap/improvement/l1 filters.
  set-lens      Set or clear one of the 5 diagnostic lenses on a node.
  add-evidence  Append an evidence entry to a node.
  set-coverage  Set/clear a manual coverage override (or recompute via auto).
  set-sop       Update a node's SOP status / path / rev.
  add-item      Add a register row (via improvement_log.py) and resync counts.
"""
from __future__ import annotations

import argparse, csv, json, subprocess, sys, tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = REPO_ROOT / "reference" / "taxonomy.yaml"
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"
STATE_SCHEMA_PATH = REPO_ROOT / "schemas" / "engagement_state.schema.json"


def schema_check(instance: Dict[str, Any], schema_path: Path) -> List[str]:
    """Validate instance against a JSON Schema. Returns error messages.

    Gracefully returns a single note if jsonschema or the schema file is absent.
    """
    if not schema_path.exists():
        return [f"(skipped: schema not found at {schema_path})"]
    try:
        import jsonschema
    except ImportError:
        return ["(skipped: jsonschema not installed — pip install jsonschema)"]
    with schema_path.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = jsonschema.Draft7Validator(schema)
    return [f"{'/'.join(str(p) for p in e.path) or '<root>'}: {e.message}"
            for e in sorted(validator.iter_errors(instance), key=lambda e: list(e.path))]

LENSES = ["current_state", "process", "automation", "capability", "operating_model"]
ITEM_BUCKETS = ["improvements", "gaps", "screenshots"]
TYPE_TO_BUCKET = {"improvement": "improvements", "gap": "gaps", "screenshot": "screenshots"}
# Buckets that count as "content" for coverage derivation. Gaps are absences
# (open questions / todos), NOT coverage — they must never lift a node out of
# `none`, or writing structural gaps (gap_report.py) would flip every empty node
# to `partial` and break the "empty node ↔ coverage:none" invariant.
COVERAGE_BUCKETS = ["improvements", "screenshots"]
# Allowed values per diagnostic lens (mirrors engagement_state.schema.json).
LENS_VALUES = {
    "current_state": ["present", "absent"],
    "process": ["pain_high", "pain_med", "pain_low", "strength"],
    "automation": ["machine", "mixed", "human"],
    "capability": ["new", "existing"],
    "operating_model": ["central", "mixed", "local"],
}
# ID prefix per register item type (for auto-generating add-item ids).
TYPE_TO_PREFIX = {"improvement": "IMP", "gap": "GAP", "screenshot": "SC"}
IMPROVEMENT_LOG = (REPO_ROOT / "skills" / "consult-improvement-log" / "scripts"
                   / "improvement_log.py")
# Register rows in these statuses do not roll up into node counts (aligned with
# improvement_log.py ARCHIVE_STATUSES ∪ DELETE_STATUSES).
INACTIVE_STATUSES = {"archived", "inactive", "deleted_candidate", "deleted",
                     "delete", "removed", "remove"}


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
        "coverage_override": None,
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
    """Derive a node's coverage from its contents.

    A manual `coverage_override` (set via the set-coverage command) takes
    precedence and is preserved across sync. Otherwise (gaps never count as
    content — they are absences, see COVERAGE_BUCKETS):
      - none    : no evidence AND no substantive items (improvements/screenshots)
      - covered : has evidence AND all 5 lenses set
      - partial : anything in between (items but no evidence, evidence but
                  incomplete lenses, etc.)
    """
    override = node.get("coverage_override")
    if override:
        return override
    has_evidence = bool(node.get("evidence"))
    has_items = any(node["counts"].get(b, 0) for b in COVERAGE_BUCKETS)
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
        if str(rec.get("record_status", "active")).lower() in INACTIVE_STATUSES:
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

    state_path, _ = load_state(eid)
    with state_path.open("r", encoding="utf-8") as f:
        errors = schema_check(json.load(f), STATE_SCHEMA_PATH)
    if errors and errors[0].startswith("(skipped"):
        print(f"Schema: {errors[0]}")
    elif errors:
        print(f"Schema: {len(errors)} error(s):")
        for e in errors[:20]:
            print(f"  - {e}")
    else:
        print("Schema: OK (validates against engagement_state.schema.json).")


def _save_state(state_path: Path, state: Dict[str, Any]) -> None:
    with state_path.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def _require_node(state: Dict[str, Any], key: str) -> Dict[str, Any]:
    node = state["nodes"].get(key)
    if node is None:
        raise SystemExit(f"Node '{key}' not found in state.json.")
    return node


def _touch(state: Dict[str, Any], node: Dict[str, Any]) -> None:
    ts = now_iso()
    node["updated"] = ts
    state["engagement"]["updated"] = ts


def cmd_get_node(eid: str, key: str, as_json: bool) -> None:
    _, state = load_state(eid)
    node = _require_node(state, key)
    if as_json:
        print(json.dumps(node, ensure_ascii=False, indent=2))
        return
    c = node["counts"]
    sop = node["sop"]
    lenses = " ".join(f"{lens}={node['lenses'].get(lens)}" for lens in LENSES)
    print(f"{key}: {node.get('l1_name')} — {node.get('l2_name')}")
    print(f"  coverage={node['coverage']} override={node.get('coverage_override')}")
    print(f"  lenses: {lenses}")
    print(f"  counts: imp={c['improvements']} gap={c['gaps']} sc={c['screenshots']}")
    print(f"  sop: status={sop.get('status')} rev={sop.get('rev')} path={sop.get('path')}")
    print(f"  evidence: {len(node.get('evidence', []))}")


def cmd_query(eid: str, coverage: str | None, lens_missing: str | None,
              has_gaps: bool, has_improvements: bool, l1: str | None,
              count: bool) -> None:
    _, state = load_state(eid)
    matches: List[str] = []
    for key, node in state["nodes"].items():
        if coverage is not None and node.get("coverage") != coverage:
            continue
        if lens_missing is not None and node["lenses"].get(lens_missing) is not None:
            continue
        if has_gaps and not node["counts"].get("gaps", 0):
            continue
        if has_improvements and not node["counts"].get("improvements", 0):
            continue
        if l1 is not None and node.get("l1") != l1:
            continue
        matches.append(key)
    matches.sort()
    if count:
        print(len(matches))
    else:
        for key in matches:
            print(key)


def cmd_set_lens(eid: str, key: str, lens: str, value: str) -> None:
    if lens not in LENS_VALUES:
        raise SystemExit(f"Unknown lens '{lens}'. Choose from: {', '.join(LENS_VALUES)}.")
    if value.lower() in {"null", "none", "clear"}:
        resolved: Any = None
    elif value in LENS_VALUES[lens]:
        resolved = value
    else:
        raise SystemExit(f"Invalid value '{value}' for lens '{lens}'. "
                         f"Allowed: {', '.join(LENS_VALUES[lens])} (or null/none/clear).")
    state_path, state = load_state(eid)
    node = _require_node(state, key)
    node["lenses"][lens] = resolved
    node["coverage"] = derive_coverage(node)
    _touch(state, node)
    _save_state(state_path, state)
    print(f"{key}: lens {lens}={resolved}; coverage={node['coverage']}.")


def cmd_add_evidence(eid: str, key: str, source: str, loc: str | None, note: str | None) -> None:
    state_path, state = load_state(eid)
    node = _require_node(state, key)
    entry: Dict[str, Any] = {"source": source}
    if loc:
        entry["loc"] = loc
    if note:
        entry["note"] = note
    node.setdefault("evidence", []).append(entry)
    node["coverage"] = derive_coverage(node)
    _touch(state, node)
    _save_state(state_path, state)
    print(f"{key}: added evidence (count={len(node['evidence'])}); coverage={node['coverage']}.")


def cmd_set_coverage(eid: str, key: str, value: str) -> None:
    state_path, state = load_state(eid)
    node = _require_node(state, key)
    if value == "auto":
        node["coverage_override"] = None
        node["coverage"] = derive_coverage(node)
    else:
        node["coverage_override"] = value
        node["coverage"] = value
    _touch(state, node)
    _save_state(state_path, state)
    print(f"{key}: coverage={node['coverage']} override={node.get('coverage_override')}.")


def cmd_set_sop(eid: str, key: str, status: str | None, path: str | None, bump_rev: bool) -> None:
    if status is None and path is None and not bump_rev:
        raise SystemExit("set-sop requires at least one of --status, --path, --bump-rev.")
    state_path, state = load_state(eid)
    node = _require_node(state, key)
    sop = node["sop"]
    if status is not None:
        sop["status"] = status
    if path is not None:
        sop["path"] = path
    if bump_rev:
        sop["rev"] = int(sop.get("rev", 0)) + 1
    _touch(state, node)
    _save_state(state_path, state)
    print(f"{key}: sop status={sop.get('status')} rev={sop.get('rev')} path={sop.get('path')}.")


def _next_item_id(eid: str, prefix: str) -> str:
    highest = 0
    for rec in load_register(eid):
        rid = str(rec.get("id") or "")
        if rid.startswith(prefix + "-"):
            tail = rid[len(prefix) + 1:]
            if tail.isdigit():
                highest = max(highest, int(tail))
    return f"{prefix}-{highest + 1:04d}"


def cmd_add_item(eid: str, item_type: str, l1: str, l2: str, item_id: str | None,
                 fields: List[str]) -> None:
    taxonomy = load_taxonomy()
    valid = {node_key(d1, d2) for d1, _, d2, _, _ in iter_l2(taxonomy)}
    key = node_key(l1, l2)
    if key not in valid:
        raise SystemExit(f"Orphan: node '{key}' is not in the taxonomy; refusing to add item.")

    extra: Dict[str, str] = {}
    for spec in fields:
        if "=" not in spec:
            raise SystemExit(f"Invalid --field '{spec}'; expected KEY=VALUE.")
        fkey, fval = spec.split("=", 1)
        fkey = fkey.strip()
        if not fkey:
            raise SystemExit(f"Invalid --field '{spec}'; empty key.")
        extra[fkey] = fval

    prefix = TYPE_TO_PREFIX[item_type]
    rid = item_id or _next_item_id(eid, prefix)

    headers = ["id", "type", "l1_cycle", "l2_process"] + [k for k in extra if k not in
               {"id", "type", "l1_cycle", "l2_process"}]
    row = {"id": rid, "type": item_type, "l1_cycle": l1, "l2_process": l2}
    row.update(extra)

    register_path = engagement_dir(eid) / "register.json"
    if not register_path.exists():
        raise SystemExit(f"No register.json for engagement '{eid}'. Run init first.")

    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False,
                                     newline="", encoding="utf-8") as tmp:
        writer = csv.DictWriter(tmp, fieldnames=headers)
        writer.writeheader()
        writer.writerow({h: row.get(h, "") for h in headers})
        csv_path = Path(tmp.name)

    try:
        result = subprocess.run(
            [sys.executable, str(IMPROVEMENT_LOG), "update-json",
             "--json", str(register_path), "--csv", str(csv_path),
             "--out-json", str(register_path), "--modified-by", "add-item"],
            capture_output=True, text=True,
        )
    finally:
        csv_path.unlink(missing_ok=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"improvement_log.py update-json failed for {rid}.")

    cmd_sync(eid)
    print(f"Added {item_type} {rid} to {key}.")


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

    gn = sub.add_parser("get-node", help="Print one node (compact, or --json).")
    gn.add_argument("--engagement", required=True)
    gn.add_argument("--node", required=True)
    gn.add_argument("--json", action="store_true", help="Dump the full node dict as JSON.")

    q = sub.add_parser("query", help="List node keys matching filters (AND).")
    q.add_argument("--engagement", required=True)
    q.add_argument("--coverage", choices=["none", "partial", "covered"])
    q.add_argument("--lens-missing", choices=LENSES)
    q.add_argument("--has-gaps", action="store_true")
    q.add_argument("--has-improvements", action="store_true")
    q.add_argument("--l1")
    q.add_argument("--count", action="store_true", help="Print just the match count.")

    sl = sub.add_parser("set-lens", help="Set or clear one of the 5 lenses.")
    sl.add_argument("--engagement", required=True)
    sl.add_argument("--node", required=True)
    sl.add_argument("--lens", required=True)
    sl.add_argument("--value", required=True)

    ae = sub.add_parser("add-evidence", help="Append an evidence entry to a node.")
    ae.add_argument("--engagement", required=True)
    ae.add_argument("--node", required=True)
    ae.add_argument("--source", required=True)
    ae.add_argument("--loc")
    ae.add_argument("--note")

    sc = sub.add_parser("set-coverage", help="Set/clear coverage override (or auto).")
    sc.add_argument("--engagement", required=True)
    sc.add_argument("--node", required=True)
    sc.add_argument("--value", required=True, choices=["none", "partial", "covered", "auto"])

    ss = sub.add_parser("set-sop", help="Update a node's SOP status/path/rev.")
    ss.add_argument("--engagement", required=True)
    ss.add_argument("--node", required=True)
    ss.add_argument("--status", choices=["not_started", "drafting", "draft",
                                         "in_review", "revised", "final"])
    ss.add_argument("--path")
    ss.add_argument("--bump-rev", action="store_true")

    ai = sub.add_parser("add-item", help="Add a register row and resync node counts.")
    ai.add_argument("--engagement", required=True)
    ai.add_argument("--type", required=True, choices=["improvement", "gap", "screenshot"])
    ai.add_argument("--l1", required=True)
    ai.add_argument("--l2", required=True)
    ai.add_argument("--id")
    ai.add_argument("--field", action="append", default=[], help="KEY=VALUE register field (repeatable).")

    args = p.parse_args()
    if args.command == "init":
        cmd_init(args.engagement, args.client, args.region, args.force)
    elif args.command == "sync":
        cmd_sync(args.engagement)
    elif args.command == "show":
        cmd_show(args.engagement)
    elif args.command == "validate":
        cmd_validate(args.engagement)
    elif args.command == "get-node":
        cmd_get_node(args.engagement, args.node, args.json)
    elif args.command == "query":
        cmd_query(args.engagement, args.coverage, args.lens_missing,
                  args.has_gaps, args.has_improvements, args.l1, args.count)
    elif args.command == "set-lens":
        cmd_set_lens(args.engagement, args.node, args.lens, args.value)
    elif args.command == "add-evidence":
        cmd_add_evidence(args.engagement, args.node, args.source, args.loc, args.note)
    elif args.command == "set-coverage":
        cmd_set_coverage(args.engagement, args.node, args.value)
    elif args.command == "set-sop":
        cmd_set_sop(args.engagement, args.node, args.status, args.path, args.bump_rev)
    elif args.command == "add-item":
        cmd_add_item(args.engagement, args.type, args.l1, args.l2, args.id, args.field)


if __name__ == "__main__":
    main()
