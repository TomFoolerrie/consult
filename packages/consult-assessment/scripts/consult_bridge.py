"""Explicit CONSULT mode. No registry writes or implicit standalone-ID aliases.
The tracked package uses the repository's Node CLI and evidence adapter.
Python owns assessment rules; TypeScript owns shared source integrity.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]


def node(script, args):
    run = subprocess.run(["node", "--experimental-strip-types", str(REPO / script), *map(str, args)],
                         capture_output=True, text=True)
    if run.returncode:
        raise ValueError((run.stderr or run.stdout).strip() or "CONSULT bridge failed")
    return json.loads(run.stdout)


def source(root, ref):
    if not re.fullmatch(r"SRC-\d+", ref):
        raise ValueError(f"integrated mode needs an engine source ID, not {ref}")
    return node("bin/consult", ["source", "verify", ref, "--root", root])


def cite(root, ref):
    record = re.fullmatch(r"(SRC-\d+):R(\d+)", ref)
    if record:
        return node("bin/consult", ["source", "record", record[1], "--record", record[2], "--root", root])
    match = re.fullmatch(r"(SRC-\d+)(?::L(\d+)(?:-L?(\d+))?)?", ref)
    if not match:
        raise ValueError(f"invalid engine citation: {ref}")
    sid, start, end = match.groups()
    if start is None:
        return source(root, sid)
    return node("bin/consult", ["source", "excerpt", sid, "--lines", f"{start}:{end or start}", "--root", root])


def table(root, ref):
    return node("bin/consult", ["source", "table", ref, "--root", root])


def publish(root, file, intent, inputs):
    request = {"file": str(file), "intent": intent, "inputs": inputs}
    run = subprocess.run(["node", "--experimental-strip-types", str(REPO / "harness/publish-synthesis.ts"), "--root", str(root)],
                         input=json.dumps(request), capture_output=True, text=True)
    if run.returncode:
        raise ValueError(run.stderr.strip() or "CONSULT publication failed; artifact preserved for retry")
    return json.loads(run.stdout)


def review(root, ledger_dir):
    # Failed per-citation checks still produce the structured review on stdout.
    run = subprocess.run(["node", "--experimental-strip-types", str(REPO / "harness/assessment-evidence.ts"),
                          "--root", str(root), "--findings", str(Path(ledger_dir) / "findings.jsonl")],
                         capture_output=True, text=True)
    if not run.stdout.strip():
        raise ValueError(run.stderr.strip() or "CONSULT evidence review failed")
    result = json.loads(run.stdout)
    if run.returncode not in (0, 2) or (run.returncode == 0) != result["ok"]:
        raise ValueError("CONSULT evidence review returned inconsistent status")
    return result


def registry(manifest):
    root = manifest["consult_root"]
    ids = dict.fromkeys(s for g in manifest["groups"] + manifest["deferred_groups"] for s in g.get("sources", []))
    entries = {}
    for sid in ids:
        checked = source(root, sid)
        # This is an ephemeral discovery projection, NEVER a source authority.
        entries[sid] = {"id": sid, "file": str(Path(root) / checked["file"]),
                        "kind": manifest.get("source_notes", {}).get(sid, {}).get("kind", "document")}
    return entries


if __name__ == "__main__":
    try:
        if len(sys.argv) != 4 or sys.argv[1] != "cite":
            raise ValueError("usage: consult_bridge.py cite ROOT SRC-nnn[:Lstart-Lend]")
        print(json.dumps(cite(sys.argv[2], sys.argv[3]), ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        sys.exit(str(exc))
