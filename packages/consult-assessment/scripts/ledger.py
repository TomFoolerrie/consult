#!/usr/bin/env python3
"""Ledger operations. The only writer to the ledger files.

  ledger.py init    --ledger-dir D [--git-init [PATH]] [--allow-no-git]
  ledger.py checkpoint --ledger-dir D [--message "..."]     # git commit of the ledgers
  ledger.py append  <layer> --author A [--group G] --from rows.jsonl
  ledger.py edit    <id> --author A --set field=value [...] --reason "..."
  ledger.py retire  <id> --author A --reason "..."
  ledger.py merge   <keep-id> <absorb-id>... --author A --reason "..."
  ledger.py propose --proposer X --target <id> --kind edit|retire|merge|link --reason "..." [--set f=v] [--absorb id...]
  ledger.py resolve <P-id> --status accepted|rejected [--note "..."]
  ledger.py show    <layer> [--md] [--all]
  ledger.py next-id <layer>

Ownership: edit/retire/merge require --author to equal the row's author.
Any agent may `propose`; only the author applies. Every write appends a new
row version; history is never rewritten.
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import (LAYERS, MARKER, SCHEMA, coerce, coerce_axes, current, git_root,  # noqa: E402
                    ledger_dir, load_taxonomy, locked, md_table, next_id, now, write_row)
import subprocess  # noqa: E402


def layer_of(id_):
    prefix = id_.split("-")[0]
    for name, spec in LAYERS.items():
        if spec["prefix"] == prefix:
            return name
    sys.exit(f"unknown id prefix: {id_}")


def parse_set(pairs):
    out = {}
    for p in pairs or []:
        if "=" not in p:
            sys.exit(f"--set expects field=value, got {p}")
        k, v = p.split("=", 1)
        out[k] = v
    return out


def require_author(row, author):
    if row.get("author") != author:
        sys.exit(f"REFUSED: {row['id']} is owned by {row.get('author')}, not {author}. "
                 f"Use `ledger.py propose` instead.")


def cmd_init(a):
    d = a.ledger_dir or os.environ.get("ASSESS_LEDGER_DIR") or sys.exit("--ledger-dir required")
    p = Path(d)
    p.mkdir(parents=True, exist_ok=True)
    if a.git_init is not None:
        target = Path(a.git_init) if a.git_init else p.parent
        if git_root(target) is None:
            subprocess.run(["git", "init", "-q", str(target)], check=True)
            print(f"git init {target}")
    root = git_root(p)
    if root is None and not a.allow_no_git:
        sys.exit(f"REFUSED: {p} is not inside a git repository. Use --git-init [PATH] to create one "
                 f"(default: {p.parent}), or --allow-no-git if you really mean it.")
    if (p / MARKER).exists():
        print(f"{p} already initialized")
    else:
        (p / MARKER).write_text(json.dumps({"initialized_at": now(), "allow_no_git": bool(a.allow_no_git),
                                             "git_root": str(root) if root else None}) + "\n", encoding="utf-8")
        print(f"initialized {p}" + (f" (git root {root})" if root else " (NO GIT - allow_no_git recorded)"))
    if root:
        (p / ".gitattributes").write_text("*.jsonl -diff merge=union\n", encoding="utf-8") if not (p / ".gitattributes").exists() else None


def cmd_checkpoint(a):
    p = ledger_dir(a.ledger_dir)
    root = git_root(p)
    if root is None:
        sys.exit("checkpoint needs a git repository; this ledger was initialized with --allow-no-git")
    subprocess.run(["git", "-C", str(root), "add", "-A", "--", str(p)], check=True)
    st = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--", str(p)],
                        capture_output=True, text=True).stdout
    if not st.strip():
        print("nothing to checkpoint")
        return
    counts = {k: len(current(p, k, include_retired=True)) for k in LAYERS}
    msg = a.message or "ledger checkpoint"
    msg += " | " + " ".join(f"{LAYERS[k]['prefix']}={v}" for k, v in counts.items())
    subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", msg, "--", str(p)], check=True)
    h = subprocess.run(["git", "-C", str(root), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    print(f"{h} {msg}")


def cmd_append(a):
    ldir = ledger_dir(a.ledger_dir, for_write=True)
    layer = a.layer
    tax = load_taxonomy(a.taxonomy) if a.taxonomy and layer in ("findings", "themes") else None
    # Read and check every row BEFORE taking the lock: never hold the lock
    # while blocked on stdin, and never write a partial batch.
    rows = []
    if a.src == "-" and hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    src = sys.stdin if a.src == "-" else open(a.src, encoding="utf-8")
    for line in src:
        line = line.strip()
        if not line:
            continue
        row = coerce(layer, json.loads(line))
        if tax:
            row = coerce_axes(tax, row)
        missing = [k for k in SCHEMA[layer]["required"] if not row.get(k)]
        if missing:
            sys.exit(f"REFUSED row {len(rows) + 1}: missing required {missing}: {json.dumps(row)[:200]}")
        if layer == "findings" and not row.get("sources"):
            sys.exit(f"REFUSED row {len(rows) + 1}: findings must cite at least one source")
        rows.append(row)
    with locked(ldir):
        for row in rows:
            row.update({
                "id": row.get("id") or next_id(ldir, layer),
                "version": 1,
                "author": a.author,
                "group": a.group,
                "status": "active",
                "created_at": now(),
            })
            write_row(ldir, layer, row)
            print(row["id"])
    print(f"appended {len(rows)} {layer}", file=sys.stderr)


def _bump(ldir, layer, row, author, reason, **changes):
    new = dict(row)
    new.update(changes)
    new["version"] = row["version"] + 1
    new["edited_at"] = now()
    new["edit_reason"] = reason
    write_row(ldir, layer, new)
    return new


def cmd_edit(a):
    ldir = ledger_dir(a.ledger_dir, for_write=True)
    with locked(ldir):
        layer = layer_of(a.id)
        rows = current(ldir, layer, include_retired=True)
        row = rows.get(a.id) or sys.exit(f"no such id {a.id}")
        require_author(row, a.author)
        changes = coerce(layer, parse_set(a.set), partial=True)
        if a.taxonomy and layer in ("findings", "themes"):
            changes = coerce_axes(load_taxonomy(a.taxonomy), changes)
        # any field is editable; classification axes are validated by validate.py against the taxonomy
        _bump(ldir, layer, row, a.author, a.reason, **changes)
        print(f"{a.id} v{row['version'] + 1}")


def cmd_retire(a):
    ldir = ledger_dir(a.ledger_dir, for_write=True)
    with locked(ldir):
        layer = layer_of(a.id)
        row = current(ldir, layer, include_retired=True).get(a.id) or sys.exit(f"no such id {a.id}")
        require_author(row, a.author)
        _bump(ldir, layer, row, a.author, a.reason, status="retired")
        print(f"{a.id} retired")


def cmd_merge(a):
    ldir = ledger_dir(a.ledger_dir, for_write=True)
    with locked(ldir):
        layer = layer_of(a.keep)
        rows = current(ldir, layer, include_retired=True)
        keep = rows.get(a.keep) or sys.exit(f"no such id {a.keep}")
        require_author(keep, a.author)
        absorbed = list(keep.get("absorbed", []))
        merged_sources = list(keep.get("sources", []))
        for aid in a.absorb:
            r = rows.get(aid) or sys.exit(f"no such id {aid}")
            require_author(r, a.author)
            if layer == "findings" and r.get("evidence_basis") != keep.get("evidence_basis"):
                sys.exit(f"REFUSED: {aid} is '{r.get('evidence_basis')}' evidence, {a.keep} is "
                         f"'{keep.get('evidence_basis')}'. Merging would misreport the evidence base. "
                         f"Link them with `edit --set related=...` instead.")
            _bump(ldir, layer, r, a.author, f"merged into {a.keep}: {a.reason}", status="retired")
            absorbed.append(aid)
            for s in r.get("sources", []):
                if s not in merged_sources:
                    merged_sources.append(s)
        changes = {"absorbed": absorbed}
        if layer == "findings":
            changes["sources"] = merged_sources
        _bump(ldir, layer, keep, a.author, f"absorbed {a.absorb}: {a.reason}", **changes)
        print(f"{a.keep} absorbed {a.absorb}")


def cmd_propose(a):
    ldir = ledger_dir(a.ledger_dir, for_write=True)
    with locked(ldir):
        layer = layer_of(a.target)
        target = current(ldir, layer, include_retired=True).get(a.target) or sys.exit(f"no such id {a.target}")
        row = {
            "id": next_id(ldir, "proposals"), "version": 1, "status": "open",
            "proposer": a.proposer, "target": a.target, "target_author": target.get("author"),
            "kind": a.kind, "reason": a.reason, "set": parse_set(a.set), "absorb": a.absorb or [],
            "created_at": now(),
        }
        write_row(ldir, "proposals", row)
        print(row["id"])


def cmd_resolve(a):
    ldir = ledger_dir(a.ledger_dir, for_write=True)
    with locked(ldir):
        row = current(ldir, "proposals", include_retired=True).get(a.id) or sys.exit(f"no such proposal {a.id}")
        _bump(ldir, "proposals", row, None, a.note or a.status, status=a.status, resolution=a.note)
        print(f"{a.id} {a.status}")


def cmd_show(a):
    ldir = ledger_dir(a.ledger_dir)
    rows = current(ldir, a.layer, include_retired=a.all)
    if a.md:
        meta = {"version", "created_at", "edited_at", "edit_reason", "absorbed", "group", "layer", "target_author", "proposer"}
        cols = ["id", "author", "status"]
        for r in rows.values():
            for k in r:
                if k not in cols and k not in meta:
                    cols.append(k)
        print(md_table(cols, [[
            "; ".join(r.get(c, [])) if isinstance(r.get(c), list) else r.get(c, "")
            for c in cols] for r in rows.values()]))
    else:
        for r in rows.values():
            print(json.dumps(r, ensure_ascii=False))


def cmd_next_id(a):
    print(next_id(ledger_dir(a.ledger_dir), a.layer))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    common = argparse.ArgumentParser(add_help=False)  # accepted before or after the subcommand
    common.add_argument("--ledger-dir", default=argparse.SUPPRESS)
    common.add_argument("--taxonomy", default=argparse.SUPPRESS,
                        help="optional; lets append/edit list-ify multi-valued axes given as 'a; b'")
    p.add_argument("--ledger-dir", default=None)
    p.add_argument("--taxonomy", default=None)
    sub = p.add_subparsers(dest="cmd", required=True)
    _add = sub.add_parser
    sub.add_parser = lambda name, **kw: _add(name, parents=[common], conflict_handler="resolve", **kw)

    s = sub.add_parser("init"); s.add_argument("--git-init", nargs="?", const="", default=None,
                                               help="git init PATH (default: parent of ledger dir) if not already in a repo")
    s.add_argument("--allow-no-git", action="store_true"); s.set_defaults(fn=cmd_init)

    s = sub.add_parser("checkpoint"); s.add_argument("--message", "-m"); s.set_defaults(fn=cmd_checkpoint)

    s = sub.add_parser("append"); s.add_argument("layer", choices=list(LAYERS))
    s.add_argument("--author", required=True); s.add_argument("--group")
    s.add_argument("--from", dest="src", default="-"); s.set_defaults(fn=cmd_append)

    s = sub.add_parser("edit"); s.add_argument("id"); s.add_argument("--author", required=True)
    s.add_argument("--set", action="append"); s.add_argument("--reason", required=True); s.set_defaults(fn=cmd_edit)

    s = sub.add_parser("retire"); s.add_argument("id"); s.add_argument("--author", required=True)
    s.add_argument("--reason", required=True); s.set_defaults(fn=cmd_retire)

    s = sub.add_parser("merge"); s.add_argument("keep"); s.add_argument("absorb", nargs="+")
    s.add_argument("--author", required=True); s.add_argument("--reason", required=True); s.set_defaults(fn=cmd_merge)

    s = sub.add_parser("propose"); s.add_argument("--proposer", required=True); s.add_argument("--target", required=True)
    s.add_argument("--kind", choices=["edit", "retire", "merge", "link"], required=True); s.add_argument("--reason", required=True)
    s.add_argument("--set", action="append"); s.add_argument("--absorb", nargs="*"); s.set_defaults(fn=cmd_propose)

    s = sub.add_parser("resolve"); s.add_argument("id"); s.add_argument("--status", choices=["accepted", "rejected"], required=True)
    s.add_argument("--note"); s.set_defaults(fn=cmd_resolve)

    s = sub.add_parser("show"); s.add_argument("layer", choices=list(LAYERS))
    s.add_argument("--md", action="store_true"); s.add_argument("--all", action="store_true"); s.set_defaults(fn=cmd_show)

    s = sub.add_parser("next-id"); s.add_argument("layer", choices=list(LAYERS)); s.set_defaults(fn=cmd_next_id)

    a = p.parse_args()
    a.ledger_dir = getattr(a, "ledger_dir", None) or os.environ.get("ASSESS_LEDGER_DIR")
    a.taxonomy = getattr(a, "taxonomy", None) or os.environ.get("ASSESS_TAXONOMY")
    a.fn(a)


if __name__ == "__main__":
    main()
