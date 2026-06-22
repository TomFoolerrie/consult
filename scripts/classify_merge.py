#!/usr/bin/env python3
"""classify_merge.py — deterministic Stage-2b merge (CONSULT pipeline).

Reads every per-doc classify artifact under engagements/{E}/classify/, validates
each one (via validate_artifact.py), then applies the **facts** to state through
the existing state_machine.py CLI — never writing state.json/register.json
directly. Judgments (candidate findings) are NOT applied here; they stay staged
in the artifacts for Stage 3 consolidate.

What gets applied (per classify_contract.md §5):
  - Evidence  -> state_machine.py add-evidence (idempotent by ref; tier carried).
  - Lenses    -> collected per (node, lens) across all artifacts; low-confidence
                 dropped. v1 SIMPLE policy: if the remaining (med/high) signals
                 all agree on one value -> set-lens to it; if >=2 distinct values
                 remain -> leave the lens null AND add-item a contradiction gap
                 (GAP-CONFLICT-{l1}-{l2}-{lens}) with a matching dedup_key, so
                 re-runs upsert rather than duplicate.
  - Candidate findings -> NOT applied (stay staged).
  - Unmapped  -> add-item --type unmapped with dedup_key={evidence_ref}, so
                 re-runs do not duplicate.

Idempotency: re-running re-resolves from the full artifact set. Evidence dedups
by ref (T01), lenses recompute from scratch, conflict gaps + unmapped rows upsert
by dedup_key (T02). All mutations go through the CLI like gap_report.py does.

Command:
  merge --engagement E
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"
STATE_MACHINE = REPO_ROOT / "scripts" / "state_machine.py"
VALIDATE_ARTIFACT = REPO_ROOT / "scripts" / "validate_artifact.py"

SOURCE = "classify-merge"
CONFLICT_PREFIX = "GAP-CONFLICT-"

# Confidence levels we keep for lens resolution (low is always dropped).
KEPT_CONFIDENCE = {"high", "med"}

# Parse a `path#Lstart-Lend` (or `path#Lstart`) evidence ref into (path, loc).
_REF_RE = re.compile(r"^(?P<path>.+?)#L(?P<start>[0-9]+)(?:-(?P<end>[0-9]+))?$")


def engagement_dir(eid: str) -> Path:
    return ENGAGEMENTS_DIR / eid


def _run_state_machine(args: List[str]) -> subprocess.CompletedProcess:
    """Invoke state_machine.py as a subprocess (the only mutation path)."""
    return subprocess.run(
        [sys.executable, str(STATE_MACHINE), *args],
        capture_output=True, text=True,
    )


def _parse_ref(ref: str) -> Optional[Tuple[str, str]]:
    """Split a `path#Lstart-Lend` ref into (source_path, loc_label).

    loc_label is e.g. `L42-48` or `L45`. Returns None if unparseable.
    """
    m = _REF_RE.match(ref or "")
    if not m:
        return None
    path = m.group("path")
    start = m.group("start")
    end = m.group("end")
    loc = f"L{start}-{end}" if end else f"L{start}"
    return path, loc


# ---- step 1: load + validate artifacts --------------------------------------

def load_valid_artifacts(eid: str) -> Tuple[List[Tuple[Path, Dict[str, Any]]], List[Tuple[Path, str]]]:
    """Return (valid_artifacts, skipped) for the engagement.

    valid_artifacts: list of (path, parsed_json) that pass validate_artifact.py.
    skipped: list of (path, reason) for artifacts that fail to load or validate.
    Never raises on a bad artifact.
    """
    classify_dir = engagement_dir(eid) / "classify"
    valid: List[Tuple[Path, Dict[str, Any]]] = []
    skipped: List[Tuple[Path, str]] = []
    if not classify_dir.is_dir():
        return valid, skipped

    for art_path in sorted(classify_dir.glob("*.artifact.json")):
        result = _run_state_machine_validate(art_path, eid)
        if result.returncode != 0:
            reason = (result.stdout or result.stderr or "validation failed").strip()
            skipped.append((art_path, reason.splitlines()[0] if reason else "validation failed"))
            continue
        # Validated OK -> safe to parse.
        try:
            with art_path.open("r", encoding="utf-8") as f:
                instance = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            skipped.append((art_path, f"unreadable after validate: {e}"))
            continue
        valid.append((art_path, instance))
    return valid, skipped


def _run_state_machine_validate(art_path: Path, eid: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATE_ARTIFACT), "validate",
         "--artifact", str(art_path), "--engagement", eid],
        capture_output=True, text=True,
    )


# ---- step 2: evidence -------------------------------------------------------

def apply_evidence(eid: str, artifacts: List[Tuple[Path, Dict[str, Any]]]) -> int:
    """add-evidence for every node_hit evidence ref (idempotent via T01).

    Tier is carried from the node_hit's `evidence_tier` if present (the schema is
    permissive on extra doc fields; we only pass --tier when valid). Note comes
    from the evidence quote/note. Returns the count of add-evidence calls issued.
    """
    calls = 0
    for _, instance in artifacts:
        for hit in instance.get("node_hits", []) or []:
            node = hit.get("node")
            if not node:
                continue
            # Tier may live on the node_hit or per-evidence entry (forward-compat;
            # schema allows neither today, but carry it when present).
            hit_tier = hit.get("evidence_tier") or hit.get("tier")
            for ev in hit.get("evidence", []) or []:
                ref = ev.get("ref")
                parsed = _parse_ref(ref) if ref else None
                if parsed is None:
                    continue
                source, loc = parsed
                note = ev.get("note") or ev.get("quote")
                tier = ev.get("tier") or ev.get("evidence_tier") or hit_tier
                args = ["add-evidence", "--engagement", eid, "--node", node,
                        "--source", source, "--loc", loc]
                if note:
                    args += ["--note", note]
                if tier in {"verbal", "documentary", "system_observed"}:
                    args += ["--tier", tier]
                res = _run_state_machine(args)
                if res.returncode != 0:
                    sys.stderr.write(res.stdout)
                    sys.stderr.write(res.stderr)
                    raise SystemExit(f"add-evidence failed for {node} {ref}.")
                calls += 1
    return calls


# ---- step 3: lenses ---------------------------------------------------------

def collect_lens_signals(
    artifacts: List[Tuple[Path, Dict[str, Any]]]
) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    """Collect all (med/high) lens signals keyed by (node, lens).

    low-confidence signals are dropped. Returns {(node, lens): [signal, ...]}.
    """
    collected: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for _, instance in artifacts:
        for hit in instance.get("node_hits", []) or []:
            node = hit.get("node")
            if not node:
                continue
            for sig in hit.get("lens_signals", []) or []:
                conf = str(sig.get("confidence") or "").lower()
                if conf not in KEPT_CONFIDENCE:
                    continue  # drop low (and anything not med/high)
                lens = sig.get("lens")
                value = sig.get("value")
                if not lens or value is None:
                    continue
                collected.setdefault((node, lens), []).append(sig)
    return collected


def _conflict_id(node: str, lens: str) -> str:
    """Stable GAP-CONFLICT id: GAP-CONFLICT-{l1}-{l2}-{lens}.

    node is `{l1}.{l2}`; we replace the dot with a dash so the id is flat.
    """
    flat_node = node.replace(".", "-")
    return f"{CONFLICT_PREFIX}{flat_node}-{lens}"


def apply_lenses(
    eid: str, collected: Dict[Tuple[str, str], List[Dict[str, Any]]]
) -> Tuple[int, int]:
    """Apply the v1 SIMPLE lens policy. Returns (lenses_set, conflicts_raised)."""
    lenses_set = 0
    conflicts = 0
    for (node, lens), signals in sorted(collected.items()):
        distinct = sorted({s.get("value") for s in signals})
        if len(distinct) == 1:
            # All agree -> set the lens.
            value = distinct[0]
            res = _run_state_machine(
                ["set-lens", "--engagement", eid, "--node", node,
                 "--lens", lens, "--value", value]
            )
            if res.returncode != 0:
                sys.stderr.write(res.stdout)
                sys.stderr.write(res.stderr)
                raise SystemExit(f"set-lens failed for {node} {lens}={value}.")
            lenses_set += 1
        else:
            # >=2 distinct values -> leave null, raise a contradiction gap.
            _raise_conflict_gap(eid, node, lens, signals, distinct)
            conflicts += 1
    return lenses_set, conflicts


def _raise_conflict_gap(eid: str, node: str, lens: str,
                        signals: List[Dict[str, Any]], distinct: List[str]) -> None:
    """add-item a GAP-CONFLICT row (upsert by dedup_key, never duplicated)."""
    gap_id = _conflict_id(node, lens)
    refs = sorted({s.get("evidence_ref") for s in signals if s.get("evidence_ref")})
    observation = (
        f"Cross-document conflict on lens '{lens}' for node '{node}': "
        f"signals disagree ({', '.join(distinct)}). Lens left null pending human "
        f"resolution. Conflicting evidence: {', '.join(refs) if refs else '(none cited)'}."
    )
    args = [
        "add-item", "--engagement", eid, "--type", "gap",
        "--l1", node.split(".", 1)[0], "--l2", node.split(".", 1)[1],
        "--id", gap_id,
        "--field", "tag=unconfirmed",
        "--field", f"dedup_key={gap_id}",
        "--field", f"source={SOURCE}",
        "--field", f"observation_pain_point={observation}",
    ]
    res = _run_state_machine(args)
    if res.returncode != 0:
        sys.stderr.write(res.stdout)
        sys.stderr.write(res.stderr)
        raise SystemExit(f"add-item (conflict gap) failed for {gap_id}.")


# ---- step 5: unmapped -------------------------------------------------------

def apply_unmapped(eid: str, artifacts: List[Tuple[Path, Dict[str, Any]]]) -> int:
    """add-item --type unmapped for each unmapped entry (dedup by evidence_ref).

    Returns the count of add-item calls issued. dedup_key = evidence_ref so a
    re-run upserts the same row rather than minting a duplicate.
    """
    calls = 0
    seen_keys: set = set()
    for _, instance in artifacts:
        for um in instance.get("unmapped", []) or []:
            evidence_ref = um.get("evidence_ref")
            if not evidence_ref:
                continue
            # Within one merge run, the same evidence_ref across artifacts should
            # collapse to one upsert (dedup_key handles cross-run; this avoids a
            # redundant in-run write).
            if evidence_ref in seen_keys:
                continue
            seen_keys.add(evidence_ref)
            summary = um.get("summary") or "(no summary)"
            args = [
                "add-item", "--engagement", eid, "--type", "unmapped",
                "--field", f"dedup_key={evidence_ref}",
                "--field", f"source={evidence_ref}",
                "--field", f"observation_pain_point={summary}",
            ]
            res = _run_state_machine(args)
            if res.returncode != 0:
                sys.stderr.write(res.stdout)
                sys.stderr.write(res.stderr)
                raise SystemExit(f"add-item (unmapped) failed for {evidence_ref}.")
            calls += 1
    return calls


# ---- driver -----------------------------------------------------------------

def cmd_merge(eid: str) -> None:
    state_path = engagement_dir(eid) / "state.json"
    if not state_path.exists():
        raise SystemExit(f"No state.json for engagement '{eid}'. Run init first.")

    valid, skipped = load_valid_artifacts(eid)

    evidence_calls = apply_evidence(eid, valid)
    collected = collect_lens_signals(valid)
    lenses_set, conflicts = apply_lenses(eid, collected)
    unmapped_calls = apply_unmapped(eid, valid)

    # Compact summary.
    print(f"classify_merge '{eid}':")
    print(f"  artifacts merged: {len(valid)} | skipped (invalid): {len(skipped)}")
    for path, reason in skipped:
        print(f"    - SKIP {path.name}: {reason}")
    print(f"  evidence add-evidence calls: {evidence_calls}")
    print(f"  lenses set: {lenses_set} | conflicts (gaps raised): {conflicts}")
    print(f"  unmapped rows: {unmapped_calls}")
    print("  candidate findings: not applied (staged for consolidate)")


def main() -> None:
    p = argparse.ArgumentParser(description="Deterministic Stage-2b classify merge.")
    sub = p.add_subparsers(dest="command", required=True)
    m = sub.add_parser("merge", help="Merge all classify artifacts into state.")
    m.add_argument("--engagement", required=True)
    args = p.parse_args()
    if args.command == "merge":
        cmd_merge(args.engagement)


if __name__ == "__main__":
    main()
