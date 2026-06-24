#!/usr/bin/env python3
"""classify_merge.py — deterministic Stage-2b merge (CONSULT pipeline).

Reads every per-doc classify artifact under engagements/{E}/classify/, validates
each one (via validate_artifact.py), then applies the **facts** to state through
the existing state_machine.py CLI — never writing state.json/register.json
directly. Judgments (candidate findings) are NOT applied here; they stay staged
in the artifacts for Stage 3 consolidate.

What gets applied (per classify_contract.md §5):
  - Evidence  -> state_machine.py add-evidence (idempotent by ref; tier carried).
                 Source paths are canonicalized relative to engagements/{eid}/
                 (T42 fix 3) so the same line range cited absolute vs relative
                 dedups; a path that resolves outside that tree is skip-reported.
  - Lenses    -> collected per (node, lens) across all artifacts; low-confidence
                 dropped. v1 SIMPLE policy: if the remaining (med/high) signals
                 all agree on one value -> set-lens to it; if >=2 distinct values
                 remain -> leave the lens null AND add-item a contradiction gap
                 (GAP-CONFLICT-{l1}-{l2}-{lens}) with a matching dedup_key, so
                 re-runs upsert rather than duplicate.
  - Candidate findings -> NOT applied (stay staged).
  - Unmapped  -> add-item --type unmapped with dedup_key={evidence_ref + summary
                 hash}, so distinct summaries sharing a ref do not collapse and
                 re-runs do not duplicate.

Single-run atomicity (T42 fix 1): re-runs are *already* idempotent (evidence
dedups, lenses recompute, gaps/unmapped upsert by dedup_key), so there is no
merge cursor. Instead a **fail-closed pre-flight** validates ALL facts (refs
parseable + canonicalizable, nodes are `l1.l2` in the taxonomy, lens values
legal) and aborts the whole merge *before* issuing any mutation when a
structural/validation error is found. Data-quality drops (a ref that does not
parse, a lens signal missing lens/value, a path outside the engagement tree)
are NOT structural errors: they are skip-reported and the merge proceeds. A
cross-document lens conflict is NOT a failure either — it still raises a GAP and
the merge continues.

Command:
  merge --engagement E
"""
from __future__ import annotations

import argparse
import hashlib
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

# A taxonomy node key is exactly `l1.l2` (one dot, both segments non-empty).
_NODE_RE = re.compile(r"^[^.]+\.[^.]+$")


def engagement_dir(eid: str) -> Path:
    return ENGAGEMENTS_DIR / eid


def _run_state_machine(args: List[str]) -> subprocess.CompletedProcess:
    """Invoke state_machine.py as a subprocess (the only mutation path)."""
    return subprocess.run(
        [sys.executable, str(STATE_MACHINE), *args],
        capture_output=True, text=True,
    )


def _load_taxonomy_nodes() -> set:
    """Set of valid `l1.l2` node keys. Reuses state_machine's loader when
    importable; otherwise parses the taxonomy directly (mirrors
    validate_artifact._load_taxonomy_nodes)."""
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        import state_machine  # type: ignore

        tax = state_machine.load_taxonomy()
        return {f"{l1}.{l2}" for l1, _, l2, _, _ in state_machine.iter_l2(tax)}
    except Exception:
        pass
    import yaml  # type: ignore

    with (REPO_ROOT / "reference" / "taxonomy.yaml").open("r", encoding="utf-8") as f:
        tax = yaml.safe_load(f)
    nodes = set()
    for dom in tax.get("domains", []):
        for l2 in dom.get("l2", []):
            nodes.add(f"{dom['id']}.{l2['id']}")
    return nodes


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


def _canonical_source(eid: str, raw_path: str) -> Optional[str]:
    """Canonicalize an evidence source path to be relative to engagements/{eid}/.

    A path cited absolutely (or relative to the repo root, or relative to the
    engagement dir) all collapse to the same relative-to-engagement key, so the
    `(source, loc)` evidence dedup in add-evidence stops minting duplicates for
    the same line range (T42 fix 3).

    Returns the canonical relative path string, or None if the path resolves
    outside the engagement tree (caller skip-reports it; we do not clamp).
    """
    edir = engagement_dir(eid).resolve()
    p = Path(raw_path)
    if p.is_absolute():
        candidate = p
    else:
        # Try relative-to-engagement first (the canonical form), then
        # relative-to-repo-root (how a raw path is often written).
        candidate = (edir / raw_path)
        if not candidate.resolve().as_posix().startswith(edir.as_posix()):
            candidate = (REPO_ROOT / raw_path)
    try:
        rel = candidate.resolve().relative_to(edir)
    except ValueError:
        return None
    return rel.as_posix()


def _norm_summary_hash(summary: str) -> str:
    """Short stable hash of a normalized summary (whitespace-collapsed,
    lowercased) — used to disambiguate distinct unmapped summaries that share an
    evidence_ref (T42 fix 5)."""
    norm = " ".join((summary or "").split()).lower()
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()[:12]


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


# ---- pre-flight: fail-closed validate-ALL (T42 fix 1 + fix 2) ----------------

class SkipReport:
    """Accumulates data-quality drops so they are visible, not silently lost
    (T42 fix 4). A drop is a recoverable per-fact omission; the merge proceeds."""

    def __init__(self) -> None:
        self.items: List[Tuple[str, str]] = []  # (category, detail)

    def add(self, category: str, detail: str) -> None:
        self.items.append((category, detail))

    def __len__(self) -> int:
        return len(self.items)

    def print(self) -> None:
        if not self.items:
            return
        print(f"  skipped (data-quality drops): {len(self.items)}")
        by_cat: Dict[str, List[str]] = {}
        for cat, detail in self.items:
            by_cat.setdefault(cat, []).append(detail)
        for cat in sorted(by_cat):
            details = by_cat[cat]
            print(f"    - {cat}: {len(details)}")
            for d in details[:3]:
                print(f"        * {d}")
            if len(details) > 3:
                print(f"        * ... and {len(details) - 3} more")


def preflight_validate(
    eid: str, artifacts: List[Tuple[Path, Dict[str, Any]]], valid_nodes: set
) -> Tuple[List[str], SkipReport]:
    """Validate ALL facts across every artifact BEFORE any mutation is issued.

    Returns (structural_errors, skip_report).

    Structural errors (fail-closed — caller aborts before mutating):
      - a node_hit/lens node that is not a `l1.l2` key present in the taxonomy.
        (collect_lens_signals stores `node` verbatim and _raise_conflict_gap
        splits on '.', so a malformed node would crash mid-merge: reject here.)

    Data-quality drops (skip-reported; merge proceeds):
      - an evidence/unmapped ref that does not parse to `path#Lstart-Lend`.
      - an evidence source path that canonicalizes outside engagements/{eid}/.
      - a lens signal missing its lens or value.
    """
    errors: List[str] = []
    skips = SkipReport()

    for path, instance in artifacts:
        name = path.name
        for hi, hit in enumerate(instance.get("node_hits", []) or []):
            node = hit.get("node")
            # fix 2: a node must be `l1.l2` AND present in the taxonomy.
            if node is None or not _NODE_RE.match(str(node)) or node not in valid_nodes:
                errors.append(
                    f"{name}: node_hits[{hi}].node '{node}' is not a valid "
                    f"`l1.l2` taxonomy node."
                )
                continue
            for ei, ev in enumerate(hit.get("evidence", []) or []):
                ref = ev.get("ref")
                parsed = _parse_ref(ref) if ref else None
                if parsed is None:
                    skips.add("unparseable evidence ref",
                              f"{name} node_hits[{hi}].evidence[{ei}] ref={ref!r}")
                    continue
                raw_path, _loc = parsed
                if _canonical_source(eid, raw_path) is None:
                    skips.add("evidence path outside engagement tree",
                              f"{name} node_hits[{hi}].evidence[{ei}] path={raw_path!r}")
            for si, sig in enumerate(hit.get("lens_signals", []) or []):
                conf = str(sig.get("confidence") or "").lower()
                if conf not in KEPT_CONFIDENCE:
                    continue  # low/other is an intentional drop, not reportable
                lens = sig.get("lens")
                value = sig.get("value")
                if not lens or value is None:
                    skips.add("lens signal missing lens/value",
                              f"{name} node_hits[{hi}].lens_signals[{si}] "
                              f"lens={lens!r} value={value!r}")
        for ui, um in enumerate(instance.get("unmapped", []) or []):
            ref = um.get("evidence_ref")
            if ref and _parse_ref(ref) is None:
                skips.add("unparseable unmapped ref",
                          f"{name} unmapped[{ui}] ref={ref!r}")

    return errors, skips


# ---- step 2: evidence -------------------------------------------------------

def apply_evidence(
    eid: str, artifacts: List[Tuple[Path, Dict[str, Any]]], skips: SkipReport
) -> int:
    """add-evidence for every node_hit evidence ref (idempotent via T01).

    Source paths are canonicalized relative to engagements/{eid}/ (T42 fix 3);
    a path outside that tree, or an unparseable ref, is dropped to the skip
    report rather than written. Tier is carried from the node_hit's
    `evidence_tier` if present. Note comes from the evidence quote/note. Returns
    the count of add-evidence calls issued.
    """
    calls = 0
    for path, instance in artifacts:
        name = path.name
        for hi, hit in enumerate(instance.get("node_hits", []) or []):
            node = hit.get("node")
            if not node:
                continue
            # Tier may live on the node_hit or per-evidence entry (forward-compat;
            # schema allows neither today, but carry it when present).
            hit_tier = hit.get("evidence_tier") or hit.get("tier")
            for ei, ev in enumerate(hit.get("evidence", []) or []):
                ref = ev.get("ref")
                parsed = _parse_ref(ref) if ref else None
                if parsed is None:
                    skips.add("unparseable evidence ref",
                              f"{name} node_hits[{hi}].evidence[{ei}] ref={ref!r}")
                    continue
                raw_path, loc = parsed
                source = _canonical_source(eid, raw_path)
                if source is None:
                    skips.add("evidence path outside engagement tree",
                              f"{name} node_hits[{hi}].evidence[{ei}] path={raw_path!r}")
                    continue
                # Prefer `note`; `quote` is a LEGACY/optional fallback (T55 trim
                # drops it from the emit contract). When `quote` is absent this
                # returns None gracefully and no --note is passed below.
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

    low-confidence signals are dropped, as are signals missing a lens/value.
    Nodes are assumed already validated as `l1.l2`-in-taxonomy by the pre-flight,
    but we re-guard defensively so a malformed node can never reach the
    dot-split in _raise_conflict_gap. Returns {(node, lens): [signal, ...]}.
    """
    collected: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for _, instance in artifacts:
        for hit in instance.get("node_hits", []) or []:
            node = hit.get("node")
            if not node or not _NODE_RE.match(str(node)):
                continue  # pre-flight already aborts on this; belt-and-braces
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
    """add-item a GAP-CONFLICT row (upsert by dedup_key, never duplicated).

    `node` is guaranteed `l1.l2` by the pre-flight, so the dot-split below is
    safe (T42 fix 2).
    """
    gap_id = _conflict_id(node, lens)
    refs = sorted({s.get("evidence_ref") for s in signals if s.get("evidence_ref")})
    observation = (
        f"Cross-document conflict on lens '{lens}' for node '{node}': "
        f"signals disagree ({', '.join(distinct)}). Lens left null pending human "
        f"resolution. Conflicting evidence: {', '.join(refs) if refs else '(none cited)'}."
    )
    l1, l2 = node.split(".", 1)
    args = [
        "add-item", "--engagement", eid, "--type", "gap",
        "--l1", l1, "--l2", l2,
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

def apply_unmapped(
    eid: str, artifacts: List[Tuple[Path, Dict[str, Any]]]
) -> int:
    """add-item --type unmapped for each unmapped entry.

    dedup_key = `{evidence_ref}:{normalized-summary-hash}` (T42 fix 5) so two
    distinct summaries that happen to share an evidence_ref do NOT collapse into
    one row, while a re-run still upserts the same row rather than minting a
    duplicate. Returns the count of add-item calls issued.
    """
    calls = 0
    seen_keys: set = set()
    for _, instance in artifacts:
        for um in instance.get("unmapped", []) or []:
            evidence_ref = um.get("evidence_ref")
            if not evidence_ref:
                continue
            summary = um.get("summary") or "(no summary)"
            dedup_key = f"{evidence_ref}:{_norm_summary_hash(summary)}"
            # Within one merge run the same (ref, summary) should collapse to one
            # upsert; dedup_key handles cross-run.
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)
            args = [
                "add-item", "--engagement", eid, "--type", "unmapped",
                "--field", f"dedup_key={dedup_key}",
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

    # --- fail-closed pre-flight: validate ALL facts before any mutation ------
    valid_nodes = _load_taxonomy_nodes()
    errors, skips = preflight_validate(eid, valid, valid_nodes)
    if errors:
        sys.stderr.write(
            f"classify_merge '{eid}': pre-flight FAILED — "
            f"{len(errors)} structural error(s); no mutations issued:\n"
        )
        for e in errors:
            sys.stderr.write(f"  - {e}\n")
        raise SystemExit("Aborting merge (fail-closed).")

    # --- mutations (only after the pre-flight passes) ------------------------
    # Note: apply_evidence re-runs the same parse/canon checks and folds any
    # newly-observed drops into the SAME skip report instance.
    evidence_calls = apply_evidence(eid, valid, skips)
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
    skips.print()
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
