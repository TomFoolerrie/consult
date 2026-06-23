#!/usr/bin/env python3
"""review_ingest.py — turn a reviewed .docx into applied, attributed, idempotent updates.

T31 (Slice 2). Sits between the docx comment extractor (T30, `docx_comments.py`)
and the engagement state/register commands (`state_machine.py`). Two subcommands:

  extract --engagement E --docx PATH [--round N]
      Run docx_comments on the docx, compute the docx **content hash**, and if
      that hash is already recorded in `engagements/E/review/consumed.json`,
      **skip** (the consumed marker — this is what makes a crash-replay safe:
      re-running extract on an already-applied docx does nothing). Otherwise emit
      the comments bundle (JSON) for the resolver and append one entry per comment
      to `engagements/E/deliverables/review_log.md`. Does NOT mark consumed (apply
      does — extract is read-only w.r.t. the consumed marker).

  apply --engagement E --docx PATH --actions ACTIONS.json [--round N]
      Given the resolver's proposed actions (a JSON list of
      `{command, args, reviewer, comment_id}`), run each via the existing
      state_machine commands (set-lens / add-item / set-sop / set-improvement),
      capture before→after for the touched node, append the attributed move to
      `review_log.md`, then **mark the docx hash consumed**. Every node touched
      by a substance command (set-lens / add-evidence / add-item with --l1/--l2)
      is then `mark-dirty`'d so the next `consult-run` re-consolidates it; a pure
      `set-sop --status` carries no diagnostic change and does NOT dirty. The
      dirtied set is recorded in the review_log apply section.

The docx content hash is the SHA-256 of the raw .docx bytes — a re-render produces
a new file (new hash), so a fresh review round is never mistaken for a replay.

Idempotency contract (T44, minimal — no per-action ledger):
  * A pre-flight validation pass checks the whole actions batch is structurally
    well-formed (every action is an object, with an allowed `command` and a dict
    `args`) BEFORE any state mutation. A malformed batch aborts cleanly without
    touching state or the consumed marker, so nothing is half-applied.
  * The consumed marker is all-or-nothing on ACTION failures only: if any
    state_machine action fails, the docx is NOT marked consumed so a corrected
    re-run can still apply. NARROWED: `mark-dirty` failures are NON-FATAL to the
    consumed marker — the substance change is already applied to state, so a
    failed dirty-flag flip is logged loudly but must not block consuming (else a
    re-run would re-apply and double-write). A failed dirty only risks that node
    not auto-re-consolidating next run.

Reuses docx_comments.py for all OOXML work (no reimplementation here).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parent
ENGAGEMENTS_DIR = REPO_ROOT / "engagements"
DOCX_COMMENTS = SCRIPTS_DIR / "docx_comments.py"
STATE_MACHINE = SCRIPTS_DIR / "state_machine.py"

# The subset of state_machine commands this ingest path is allowed to drive.
# (Per the ticket: lens change → set-lens; new finding → add-item; SOP
# scope/status → set-sop; improvement stream → set-improvement.)
ALLOWED_COMMANDS = {"set-lens", "add-evidence", "add-item", "set-sop", "set-improvement"}

# Substance commands: a successful one changes a node's diagnostic input
# (lens / evidence / a placed finding), so the touched node must be re-marked
# diagnosis-dirty for the next consult-run to re-consolidate it. A pure
# `set-sop --status` (or set-improvement) carries no diagnostic change and so
# does NOT dirty the node. add-item only counts as substance when it places a
# finding on an L2 node (has --l1/--l2); a null-node row does not.
SUBSTANCE_COMMANDS = {"set-lens", "add-evidence", "add-item"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def engagement_dir(eid: str) -> Path:
    return ENGAGEMENTS_DIR / eid


def docx_content_hash(docx_path: Path) -> str:
    """SHA-256 of the raw .docx bytes. A re-render → new hash → new round."""
    h = hashlib.sha256()
    with docx_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# consumed.json — the idempotency marker
# ---------------------------------------------------------------------------
def consumed_path(eid: str) -> Path:
    return engagement_dir(eid) / "review" / "consumed.json"


def load_consumed(eid: str) -> Dict[str, Any]:
    path = consumed_path(eid)
    if not path.exists():
        return {"engagement": eid, "consumed": []}
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    data.setdefault("engagement", eid)
    data.setdefault("consumed", [])
    return data


def is_consumed(eid: str, content_hash: str) -> bool:
    return any(e.get("hash") == content_hash for e in load_consumed(eid)["consumed"])


def mark_consumed(eid: str, content_hash: str, docx_path: Path,
                  round_n: Optional[int], action_count: int) -> None:
    data = load_consumed(eid)
    if any(e.get("hash") == content_hash for e in data["consumed"]):
        return  # already recorded; do not double-write
    data["consumed"].append({
        "hash": content_hash,
        "docx": docx_path.name,
        "round": round_n,
        "actions_applied": action_count,
        "consumed_at": now_iso(),
    })
    path = consumed_path(eid)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# review_log.md — the canonical human-readable change record
# ---------------------------------------------------------------------------
def review_log_path(eid: str) -> Path:
    return engagement_dir(eid) / "deliverables" / "review_log.md"


def append_review_log(eid: str, lines: List[str]) -> None:
    path = review_log_path(eid)
    path.parent.mkdir(parents=True, exist_ok=True)
    new_file = not path.exists()
    with path.open("a", encoding="utf-8") as f:
        if new_file:
            f.write("# Review Log\n\n"
                    "Appended every review round: extracted comments and applied "
                    "before→after moves, reviewer-attributed.\n")
        f.write("".join(lines))


# ---------------------------------------------------------------------------
# docx_comments bridge (reuse — no OOXML here)
# ---------------------------------------------------------------------------
def run_docx_comments(docx_path: Path) -> Dict[str, Any]:
    """Call docx_comments.py extract --json and normalize to a bundle dict.

    docx_comments emits either a bare list (comments only) or a
    {comments, tracked_changes} object. We always return a dict with both keys.
    """
    result = subprocess.run(
        [sys.executable, str(DOCX_COMMENTS), "extract", "--docx", str(docx_path), "--json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit(f"docx_comments.py failed for {docx_path}.")
    payload = json.loads(result.stdout) if result.stdout.strip() else []
    if isinstance(payload, list):
        return {"comments": payload, "tracked_changes": []}
    return {
        "comments": payload.get("comments", []),
        "tracked_changes": payload.get("tracked_changes", []),
    }


# ---------------------------------------------------------------------------
# extract
# ---------------------------------------------------------------------------
def cmd_extract(eid: str, docx: str, round_n: Optional[int], out: Optional[str]) -> int:
    docx_path = Path(docx)
    if not docx_path.exists():
        sys.stderr.write(f"error: no such docx: {docx}\n")
        return 2

    content_hash = docx_content_hash(docx_path)

    if is_consumed(eid, content_hash):
        # Crash-replay safety: this exact docx was already applied. Skip — do not
        # re-emit the bundle or re-append to the log.
        skip = {
            "skipped": True,
            "reason": "docx already consumed (idempotent skip)",
            "engagement": eid,
            "docx": docx_path.name,
            "hash": content_hash,
        }
        print(json.dumps(skip, ensure_ascii=False, indent=2))
        return 0

    bundle = run_docx_comments(docx_path)
    comments = bundle["comments"]

    out_bundle = {
        "engagement": eid,
        "docx": docx_path.name,
        "hash": content_hash,
        "round": round_n,
        "comments": comments,
        "tracked_changes": bundle["tracked_changes"],
    }

    if comments:
        log_lines: List[str] = [
            f"\n## Round {round_n if round_n is not None else '?'} "
            f"— extract ({now_iso()})\n",
            f"- docx: `{docx_path.name}` (hash `{content_hash[:12]}…`) "
            f"— {len(comments)} comment(s)\n",
        ]
        for c in comments:
            reviewer = c.get("author") or "(unknown)"
            anchored = (c.get("anchored_text") or "").replace("\n", " ").strip()
            comment_txt = (c.get("comment") or "").replace("\n", " ").strip()
            log_lines.append(
                f"  - **[{c.get('id')}] {reviewer}** on “{anchored}”: "
                f"{comment_txt}\n"
            )
        append_review_log(eid, log_lines)

    emitted = json.dumps(out_bundle, ensure_ascii=False, indent=2)
    if out:
        Path(out).write_text(emitted + "\n", encoding="utf-8")
        print(f"Wrote comments bundle ({len(comments)} comment(s)) to {out}. "
              f"docx NOT yet consumed.")
    else:
        print(emitted)
    return 0


# ---------------------------------------------------------------------------
# apply
# ---------------------------------------------------------------------------
def _node_key_for_action(args: Dict[str, Any]) -> Optional[str]:
    """Best-effort node key for the before/after snapshot.

    set-lens/set-sop/set-improvement carry --node directly; add-item carries
    --l1/--l2 which compose into the same `l1.l2` node key.
    """
    if "node" in args and args["node"]:
        return str(args["node"])
    l1, l2 = args.get("l1"), args.get("l2")
    if l1 and l2:
        return f"{l1}.{l2}"
    return None


def _is_substance_action(command: str, args: Dict[str, Any]) -> bool:
    """True if this command changed a node's diagnostic input (→ dirty it).

    set-lens / add-evidence always; add-item only when it places a finding on an
    L2 node (--l1/--l2 present). set-sop/set-improvement (status/path/rev only)
    are NOT substance.
    """
    if command not in SUBSTANCE_COMMANDS:
        return False
    if command == "add-item":
        return bool(args.get("l1") and args.get("l2"))
    return True


def _run_mark_dirty(eid: str, node_key: str) -> Tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(STATE_MACHINE), "mark-dirty",
         "--engagement", eid, "--node", node_key],
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout, result.stderr


def _get_node_json(eid: str, node_key: str) -> Optional[Dict[str, Any]]:
    result = subprocess.run(
        [sys.executable, str(STATE_MACHINE), "get-node",
         "--engagement", eid, "--node", node_key, "--json"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


# ---------------------------------------------------------------------------
# Review-path conflict detection (T33): the reviewer is authoritative (human >
# machine), so a review `set-lens` always APPLIES. But when it overrides a
# *non-null* state lens with a *different* value, that disagreement is not silent
# — we record a GAP-CONFLICT audit row so the override is visible. (The
# classify-side conflict, where signals disagree and the lens is left null, is a
# different mechanism owned by classify_merge.py / GAP-CONFLICT-{l1}-{l2}-{lens}.)
def _node_lens_value(node: Optional[Dict[str, Any]], lens: str) -> Optional[Any]:
    """The current value of one lens on a node, or None if absent/unset."""
    if not node:
        return None
    return (node.get("lenses") or {}).get(lens)


def _review_conflict_dedup_key(node_key: str, lens: str) -> str:
    """Stable dedup_key for a review-override conflict row.

    Distinct from the classify-side id (GAP-CONFLICT-{l1}-{l2}-{lens}) by the
    trailing `|review`, so a review override and a classify contradiction on the
    same (node, lens) are tracked as two separate audit rows.
    """
    return f"conflict|{node_key}|{lens}|review"


def _review_conflict_id(node_key: str, lens: str) -> str:
    """Stable, flat register id for a review-override conflict row.

    Mirrors the classify-side GAP-CONFLICT id but suffixed `-REVIEW` so the two
    sources never collide on a single id (both carry distinct dedup_keys too)."""
    flat_node = node_key.replace(".", "-")
    return f"GAP-CONFLICT-{flat_node}-{lens}-REVIEW"


def _upsert_review_conflict(eid: str, node_key: str, lens: str,
                            prior_value: Any, reviewer_value: Any,
                            reviewer: str, comment_id: Any) -> Tuple[int, str, str]:
    """Upsert a GAP-CONFLICT register row recording a reviewer override.

    type:gap, tag:unconfirmed, source:review, stable dedup_key
    `conflict|{node}|{lens}|review` (so re-applying the same override in a later
    round upserts the one row rather than minting a duplicate). The override
    facts (prior_value/reviewer_value/reviewer/comment_id) live in
    observation_pain_point. Goes through add-item like every other mutation.
    """
    l1, _, l2 = node_key.partition(".")
    dedup_key = _review_conflict_dedup_key(node_key, lens)
    gap_id = _review_conflict_id(node_key, lens)
    observation = (
        f"Review override on lens '{lens}' for node '{node_key}': reviewer "
        f"'{reviewer}' (comment {comment_id}) set value to '{reviewer_value}', "
        f"overriding the prior evidence-backed value '{prior_value}'. The "
        f"reviewer's value was applied (human > machine); this row audits the "
        f"override for human review."
    )
    args: Dict[str, Any] = {
        "type": "gap",
        "l1": l1, "l2": l2,
        "id": gap_id,
        "field": {
            "tag": "unconfirmed",
            "dedup_key": dedup_key,
            "source": "review",
            "observation_pain_point": observation,
        },
    }
    return _run_state_command(eid, "add-item", args)


def _node_snapshot(node: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """A compact, comparable view of the fields review actions move."""
    if node is None:
        return {"exists": False}
    return {
        "coverage": node.get("coverage"),
        "lenses": node.get("lenses"),
        "sop": {k: node.get("sop", {}).get(k) for k in ("status", "rev")},
        "improvement": {k: node.get("improvement", {}).get(k)
                        for k in ("status", "rev")},
        "counts": node.get("counts"),
    }


def _args_to_argv(command: str, args: Dict[str, Any]) -> List[str]:
    """Render an actions-JSON arg dict into a state_machine.py argv tail.

    --field / --field-json take repeatable KEY=VALUE specs and may be supplied
    in the action as a dict (preferred) or a pre-formatted list.
    """
    argv: List[str] = [command]  # engagement injected by the caller
    for key, value in args.items():
        flag = f"--{key.replace('_', '-')}"
        if key in ("field", "field_json"):
            specs = value
            if isinstance(specs, dict):
                specs = [f"{k}={v}" for k, v in specs.items()]
            for spec in specs:
                argv.extend([flag, str(spec)])
        elif isinstance(value, bool):
            if value:
                argv.append(flag)
        elif value is None:
            continue
        else:
            argv.extend([flag, str(value)])
    return argv


def _run_state_command(eid: str, command: str, args: Dict[str, Any]) -> Tuple[int, str, str]:
    argv = [sys.executable, str(STATE_MACHINE)]
    tail = _args_to_argv(command, args)
    # Inject --engagement right after the subcommand.
    argv.append(tail[0])
    argv.extend(["--engagement", eid])
    argv.extend(tail[1:])
    result = subprocess.run(argv, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def _preflight_validate_actions(actions: List[Any]) -> List[str]:
    """Validate the whole action batch BEFORE any state mutation begins.

    Returns a list of human-readable problems (empty == well-formed). Catching
    malformed actions up front means the batch only starts applying once every
    action is structurally sound, so we never half-apply a batch and then refuse
    to mark consumed (which would leave applied moves to be replayed on re-run).
    Pure structural checks only — value-level validity is still the
    state_machine command's job and surfaces as a per-action failure below.
    """
    problems: List[str] = []
    for idx, action in enumerate(actions):
        if not isinstance(action, dict):
            problems.append(f"action {idx}: not an object (got {type(action).__name__}).")
            continue
        command = action.get("command")
        if command not in ALLOWED_COMMANDS:
            problems.append(
                f"action {idx}: command {command!r} not allowed "
                f"(allowed: {sorted(ALLOWED_COMMANDS)}).")
        raw_args = action.get("args", {})
        if not isinstance(raw_args, dict):
            problems.append(
                f"action {idx}: 'args' must be an object "
                f"(got {type(raw_args).__name__}).")
    return problems


def cmd_apply(eid: str, docx: str, actions_path: str,
              round_n: Optional[int]) -> int:
    docx_path = Path(docx)
    if not docx_path.exists():
        sys.stderr.write(f"error: no such docx: {docx}\n")
        return 2

    content_hash = docx_content_hash(docx_path)

    if is_consumed(eid, content_hash):
        # Already applied — refuse to double-apply (idempotent).
        print(json.dumps({
            "skipped": True,
            "reason": "docx already consumed (no double-apply)",
            "engagement": eid,
            "docx": docx_path.name,
            "hash": content_hash,
        }, ensure_ascii=False, indent=2))
        return 0

    try:
        with Path(actions_path).open("r", encoding="utf-8") as f:
            actions = json.load(f)
    except FileNotFoundError:
        sys.stderr.write(f"error: no such actions file: {actions_path}\n")
        return 2
    except json.JSONDecodeError as e:
        sys.stderr.write(f"error: actions JSON is malformed ({actions_path}): {e}\n")
        return 2
    if not isinstance(actions, list):
        sys.stderr.write("error: actions JSON must be a list of action objects.\n")
        return 2

    # Pre-flight: validate the whole batch is well-formed before mutating any
    # state. If anything is malformed we abort cleanly without touching state or
    # the consumed marker, so there is nothing to replay on a corrected re-run.
    preflight = _preflight_validate_actions(actions)
    if preflight:
        sys.stderr.write("error: actions batch failed pre-flight validation:\n")
        for problem in preflight:
            sys.stderr.write(f"  - {problem}\n")
        sys.stderr.write("docx NOT marked consumed (no actions applied).\n")
        return 2

    log_lines: List[str] = [
        f"\n## Round {round_n if round_n is not None else '?'} "
        f"— apply ({now_iso()})\n",
        f"- docx: `{docx_path.name}` (hash `{content_hash[:12]}…`) "
        f"— {len(actions)} action(s)\n",
    ]

    applied = 0
    failures: List[str] = []
    dirty_nodes: List[str] = []  # nodes touched by a successful substance command
    for idx, action in enumerate(actions):
        command = action.get("command")
        args = dict(action.get("args", {}))
        reviewer = action.get("reviewer") or "(unknown)"
        comment_id = action.get("comment_id")
        # command/args shape already guaranteed well-formed by the pre-flight pass.

        node_key = _node_key_for_action(args)
        before_node = _get_node_json(eid, node_key) if node_key else None
        before = _node_snapshot(before_node) if node_key else {}

        # Review-path conflict detection (T33): for a set-lens action, capture the
        # node's CURRENT lens value before applying. The reviewer is authoritative
        # so the value is always applied; but if the prior value is non-null and
        # DIFFERS, the override must be audited (a GAP-CONFLICT row), not silent.
        conflict_lens = args.get("lens") if command == "set-lens" else None
        prior_lens_value = (
            _node_lens_value(before_node, conflict_lens) if conflict_lens else None
        )

        rc, out, err = _run_state_command(eid, command, args)
        if rc != 0:
            failures.append(f"action {idx} ({command}): {err.strip() or out.strip()}")
            log_lines.append(
                f"  - **FAILED** [{comment_id}] {reviewer}: `{command}` "
                f"{json.dumps(args)} — {(err or out).strip()}\n")
            continue

        after = _node_snapshot(_get_node_json(eid, node_key)) if node_key else {}
        applied += 1

        # Audit the override if it changed a non-null lens to a different value.
        # (current null → first assertion, no conflict; current == new → no-op-ish,
        # no conflict.) The reviewer's value is already applied above.
        if conflict_lens is not None and node_key:
            new_lens_value = args.get("value")
            if (prior_lens_value is not None
                    and str(prior_lens_value) != str(new_lens_value)):
                crc, cout, cerr = _upsert_review_conflict(
                    eid, node_key, conflict_lens, prior_lens_value,
                    new_lens_value, reviewer, comment_id)
                if crc != 0:
                    failures.append(
                        f"action {idx} (conflict-audit {node_key}.{conflict_lens}): "
                        f"{(cerr or cout).strip()}")
                    log_lines.append(
                        f"    - **FAILED to audit override** "
                        f"{node_key}.{conflict_lens} — {(cerr or cout).strip()}\n")
                else:
                    log_lines.append(
                        f"    - **OVERRIDE AUDITED**: lens `{conflict_lens}` "
                        f"`{prior_lens_value}` → `{new_lens_value}` overrode a "
                        f"non-null evidence-backed value; upserted GAP-CONFLICT "
                        f"`{_review_conflict_id(node_key, conflict_lens)}` "
                        f"(dedup_key `{_review_conflict_dedup_key(node_key, conflict_lens)}`, "
                        f"source review).\n")
        if node_key and _is_substance_action(command, args) and node_key not in dirty_nodes:
            dirty_nodes.append(node_key)
        log_lines.append(
            f"  - **[{comment_id}] {reviewer}** — `{command}` "
            f"on `{node_key}`\n"
            f"    - args: `{json.dumps(args, ensure_ascii=False)}`\n"
            f"    - before: `{json.dumps(before, ensure_ascii=False)}`\n"
            f"    - after:  `{json.dumps(after, ensure_ascii=False)}`\n")

    # Mark every node touched by a substance command diagnosis-dirty, so the
    # next consult-run re-consolidates it. A pure set-sop --status does not
    # appear here. Done after all actions applied; record the set in the log.
    #
    # NARROWED CONTRACT (T44): mark-dirty failures are NON-FATAL to the consumed
    # marker. The substance change has *already been applied* to state by the
    # action above; failing to flip the dirty flag must not block marking the
    # docx consumed, or a re-run would re-apply the (already-applied) actions and
    # double-write. A failed dirty only means that node may not auto-re-
    # consolidate next run — it is logged loudly for follow-up, not treated as an
    # apply failure. (Action failures — `failures` — DO still block consuming.)
    dirty_failures: List[str] = []
    for node_key in dirty_nodes:
        rc, out, err = _run_mark_dirty(eid, node_key)
        if rc != 0:
            dirty_failures.append(f"mark-dirty {node_key}: {(err or out).strip()}")
    if dirty_nodes:
        log_lines.append(
            f"  - dirtied (re-consolidate next run): "
            f"{', '.join(f'`{n}`' for n in dirty_nodes)}\n")
    else:
        log_lines.append("  - dirtied: none (no substance changes)\n")
    if dirty_failures:
        # Logged, but NON-FATAL: does not block the consumed marker (see above).
        for fmsg in dirty_failures:
            log_lines.append(
                f"  - **WARN (non-fatal)** {fmsg} — actions already applied; "
                f"node may not auto-re-consolidate next run.\n")

    append_review_log(eid, log_lines)

    if failures:
        # Apply is all-or-nothing on the consumed marker for ACTION failures: if
        # any action failed we do NOT mark consumed, so a corrected re-run can
        # still apply. (mark-dirty failures are deliberately NOT in `failures`.)
        sys.stderr.write("error: one or more actions failed:\n")
        for fmsg in failures:
            sys.stderr.write(f"  - {fmsg}\n")
        sys.stderr.write("docx NOT marked consumed (fix actions and re-run).\n")
        return 1

    mark_consumed(eid, content_hash, docx_path, round_n, applied)
    dirtied = (", ".join(dirty_nodes) if dirty_nodes else "none")
    print(f"Applied {applied} action(s); dirtied node(s): {dirtied}; "
          f"review_log.md updated; docx `{docx_path.name}` "
          f"(hash {content_hash[:12]}…) marked consumed.")
    if dirty_failures:
        sys.stderr.write(
            "warning: docx consumed, but some mark-dirty calls failed "
            "(non-fatal — actions already applied):\n")
        for fmsg in dirty_failures:
            sys.stderr.write(f"  - {fmsg}\n")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Ingest a reviewed .docx: extract comments (idempotent) and "
                    "apply resolver actions through the state/register commands.")
    sub = p.add_subparsers(dest="command", required=True)

    e = sub.add_parser("extract", help="Extract comments; emit bundle + log; "
                                       "skip if docx already consumed.")
    e.add_argument("--engagement", required=True)
    e.add_argument("--docx", required=True)
    e.add_argument("--round", type=int, dest="round_n")
    e.add_argument("--out", help="Write the bundle JSON to this path (default: stdout).")

    a = sub.add_parser("apply", help="Apply resolver actions; log before→after; "
                                     "mark docx consumed.")
    a.add_argument("--engagement", required=True)
    a.add_argument("--docx", required=True)
    a.add_argument("--actions", required=True, help="Path to the actions JSON list.")
    a.add_argument("--round", type=int, dest="round_n")

    args = p.parse_args(argv)
    if args.command == "extract":
        return cmd_extract(args.engagement, args.docx, args.round_n, args.out)
    if args.command == "apply":
        return cmd_apply(args.engagement, args.docx, args.actions, args.round_n)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
