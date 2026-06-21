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
      `review_log.md`, then **mark the docx hash consumed**. A lens / finding
      change bumps node state, leaving the node diagnosis-dirty for the next
      `consult-run` to re-consolidate.

The docx content hash is the SHA-256 of the raw .docx bytes — a re-render produces
a new file (new hash), so a fresh review round is never mistaken for a replay.

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
ALLOWED_COMMANDS = {"set-lens", "add-item", "set-sop", "set-improvement"}

# Which state_machine arg names carry the node key, per command. Used only to
# recover the touched node for the before→after snapshot in the review log.
NODE_ARG = {
    "set-lens": "node",
    "set-sop": "node",
    "set-improvement": "node",
    # add-item names its node via --l1/--l2 (see _node_key_for_action).
}


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
    argv: List[str] = [command, "--engagement"]  # engagement injected by caller
    # Placeholder removed below; we build the real list here instead.
    argv = [command]
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

    with Path(actions_path).open("r", encoding="utf-8") as f:
        actions = json.load(f)
    if not isinstance(actions, list):
        sys.stderr.write("error: actions JSON must be a list of action objects.\n")
        return 2

    log_lines: List[str] = [
        f"\n## Round {round_n if round_n is not None else '?'} "
        f"— apply ({now_iso()})\n",
        f"- docx: `{docx_path.name}` (hash `{content_hash[:12]}…`) "
        f"— {len(actions)} action(s)\n",
    ]

    applied = 0
    failures: List[str] = []
    for idx, action in enumerate(actions):
        command = action.get("command")
        args = dict(action.get("args", {}))
        reviewer = action.get("reviewer") or "(unknown)"
        comment_id = action.get("comment_id")

        if command not in ALLOWED_COMMANDS:
            failures.append(f"action {idx}: command '{command}' not allowed "
                            f"(allowed: {sorted(ALLOWED_COMMANDS)})")
            continue

        node_key = _node_key_for_action(args)
        before = _node_snapshot(_get_node_json(eid, node_key)) if node_key else {}

        rc, out, err = _run_state_command(eid, command, args)
        if rc != 0:
            failures.append(f"action {idx} ({command}): {err.strip() or out.strip()}")
            log_lines.append(
                f"  - **FAILED** [{comment_id}] {reviewer}: `{command}` "
                f"{json.dumps(args)} — {(err or out).strip()}\n")
            continue

        after = _node_snapshot(_get_node_json(eid, node_key)) if node_key else {}
        applied += 1
        log_lines.append(
            f"  - **[{comment_id}] {reviewer}** — `{command}` "
            f"on `{node_key}`\n"
            f"    - args: `{json.dumps(args, ensure_ascii=False)}`\n"
            f"    - before: `{json.dumps(before, ensure_ascii=False)}`\n"
            f"    - after:  `{json.dumps(after, ensure_ascii=False)}`\n")

    append_review_log(eid, log_lines)

    if failures:
        # Apply is all-or-nothing on the consumed marker: if any action failed we
        # do NOT mark consumed, so a corrected re-run can still apply.
        sys.stderr.write("error: one or more actions failed:\n")
        for fmsg in failures:
            sys.stderr.write(f"  - {fmsg}\n")
        sys.stderr.write("docx NOT marked consumed (fix actions and re-run).\n")
        return 1

    mark_consumed(eid, content_hash, docx_path, round_n, applied)
    print(f"Applied {applied} action(s); review_log.md updated; "
          f"docx `{docx_path.name}` (hash {content_hash[:12]}…) marked consumed.")
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
