#!/usr/bin/env python3
"""Draft a run manifest from the consult-lint registry (discovery-output).

  manifest.py draft --registry lint/registry.yaml --out assessment/manifest.yaml \
                    [--skill PATH] [--context context/profile.md] [--ledger-dir D] [--workdir D] [--out-dir D] [--budget-words 20000]

This is a starting point, not a decision. Grouping rule, in order:
  1. `topic` in the registry (set by the human at annotation): every source
     with the same topic goes in one group - interviews, artifacts, data,
     summaries together - split only when the word budget is exceeded.
  2. `summary_of: src-NNN` keeps a summary with its transcript.
  3. Untagged sources fall back to: interviews by interviewee, then artifacts
     by kind, batched to the budget.
A group is a question a reader can answer, not a bucket of size N. Fewer,
larger, coherent groups beat many small ones: cross-source contradictions
only surface when one reader sees both sources. The drafter warns above
--max-groups (default 8).

Anything triage marked `unusable` is listed under `excluded` with its reason
so it is visible, not silently dropped.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required: pip install pyyaml")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("cmd", choices=["draft"])
    p.add_argument("--registry", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--skill", default=str(Path(__file__).resolve().parent.parent))
    p.add_argument("--context", default="context/profile.md")
    p.add_argument("--ledger-dir", default="assessment/ledgers"); p.add_argument("--workdir", default="assessment/work")
    p.add_argument("--out-dir", dest="outdir", default="assessment/out", help="deliverables dir (paths.out)")
    p.add_argument("--budget-words", type=int, default=35000, help="max source words per reader group (~50k tokens)")
    p.add_argument("--artifact-batch", type=int, default=12, help="max small untagged artifacts per reader")
    p.add_argument("--max-groups", type=int, default=8, help="warn above this many groups")
    p.add_argument("--all-groups", action="store_true", help="put every group in groups: (default: first interview group only; the rest in deferred_groups: for the first-run review)")
    a = p.parse_args()

    import os
    mdir = Path(a.out).resolve().parent
    rel = lambda x: os.path.relpath(Path(x).resolve(), mdir)  # noqa: E731  paths in the manifest are relative to the manifest
    reg = yaml.safe_load(open(a.registry, encoding="utf-8")) or {"sources": []}
    reg_path = Path(a.registry)
    lint_dir = reg_path.parent
    active = [s for s in reg["sources"] if s.get("status") == "active"]
    excluded = [{"id": s["id"], "reason": s.get("notes") or "marked unusable"} for s in active if s.get("unusable")]
    usable = [s for s in active if not s.get("unusable")]
    pre = [s for s in usable if s.get("pre_read_candidate")]
    pre_paths = [rel(lint_dir / s["file"]) for s in pre]
    pre_ids = {s["id"] for s in pre}

    def is_interview(s):
        return "interview" in (s.get("kind") or "").lower() or "transcript" in (s.get("kind") or s["file"]).lower()

    groups, n = [], 0

    def new_group(label, topic=None):
        nonlocal n
        n += 1
        g = {"id": f"G{n}", "agent": f"reader-G{n}", "pre_read": pre_paths, "sources": [],
             "note": f"TODO: {label} - what question should this reader answer? what should it look for?"}
        if topic:
            g["topic"] = topic
        return g

    def pack(items, label, topic=None):
        """Fill groups to the word budget, keeping summary_of pairs together."""
        # order inside a group: interviews first, each followed by its summary, then artifacts, then data last -
        # a reader should hear what people said before it opens the checklist or the listing that tests it
        def rank(x):
            k = (x.get("kind") or "").lower()
            if "interview" in k or "transcript" in k:
                return 0
            if k in ("data", "spreadsheet", "listing", "extract", "register", "schedule") or str(x["file"]).lower().endswith((".csv", ".tsv", ".xlsx")):
                return 3
            if k == "summary":
                return 1
            return 2
        items = sorted(items, key=lambda x: (rank(x), x["id"]))
        placed, order = set(), []
        for s in items:
            if s["id"] in placed:
                continue
            order.append(s); placed.add(s["id"])
            for t in items:
                if t.get("summary_of") == s["id"] and t["id"] not in placed:
                    order.append(t); placed.add(t["id"])
        g, words = new_group(label, topic), 0
        for s in order:
            if g["sources"] and words + s["words"] > a.budget_words:
                groups.append(g); g, words = new_group(label, topic), 0
            g["sources"].append(s["id"]); words += s["words"]
        if g["sources"]:
            groups.append(g)
        else:
            nonlocal n
            n -= 1

    # 1. topic-tagged sources: one coherent group per topic (interviews + artifacts + data together)
    pool = [s for s in usable if s["id"] not in pre_ids]
    topics = []
    for s in pool:
        t = (s.get("topic") or "").strip()
        if t and t not in topics:
            topics.append(t)
    for t in topics:
        pack([s for s in pool if (s.get("topic") or "").strip() == t], f"topic '{t}'", topic=t)
    untagged = [s for s in pool if not (s.get("topic") or "").strip()]

    # 2. untagged interviews: by interviewee/role when known, else together
    interviews = [s for s in untagged if is_interview(s)]
    roles = []
    for s in interviews:
        r = (s.get("people") or "").strip()
        if r and r not in roles:
            roles.append(r)
    if roles and len(roles) < len(interviews):  # several interviews per role -> group by role
        for r in roles:
            pack([s for s in interviews if (s.get("people") or "").strip() == r], f"interviews with {r}")
        pack([s for s in interviews if not (s.get("people") or "").strip()], "interviews (unattributed)")
    else:
        pack(sorted(interviews, key=lambda s: (s.get("people", ""), s["id"])), "interviews")

    # 3. untagged artifacts: by kind, batched
    artifacts = [s for s in untagged if not is_interview(s)]
    kinds = []
    for s in artifacts:
        k = (s.get("kind") or "document").strip()
        if k not in kinds:
            kinds.append(k)
    for k in kinds:
        items = [s for s in artifacts if (s.get("kind") or "document").strip() == k]
        for i0 in range(0, len(items), a.artifact_batch):
            pack(items[i0:i0 + a.artifact_batch], f"{k} artifacts")

    if len(groups) > a.max_groups:
        print(f"WARNING: {len(groups)} groups. That is a lot of readers, and cross-source contradictions only surface inside one "
              f"reader's context. Tag `topic:` on sources in the registry so related interviews, artifacts, and data land together, "
              f"raise --budget-words, or merge groups by hand. Aim for one group per question the assessment must answer.", file=sys.stderr)

    from common import AGENT_DEFAULTS, PATH_DEFAULTS  # noqa: E402
    paths = dict(PATH_DEFAULTS)
    paths.update({"ledger_dir": rel(a.ledger_dir), "workdir": rel(a.workdir), "out": rel(a.outdir)})
    try:
        import subprocess
        root = subprocess.run(["git", "-C", str(reg_path.parent), "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        root = ""
    if root and not str(mdir).startswith(str(Path(root).resolve())):
        print(f"WARNING: --out {a.out} is outside the engagement root {root}; every path in it will be a ../ chain. "
              f"Write the manifest inside the engagement (e.g. <root>/_synthesis/assessment/manifest.yaml).", file=sys.stderr)
    first, rest = (groups[:1], groups[1:]) if (groups and not a.all_groups) else (groups, [])
    manifest = {
        "run": "TODO-run-name",
        "skill": a.skill,
        "taxonomy": f"{a.skill}/assets/taxonomy.yaml",
        "paths": paths,          # every location the skill writes to; rename freely, {key} templates allowed
        "agents": dict(AGENT_DEFAULTS),   # agent names; reader is a pattern with {group}
        "registry": rel(reg_path),
        "context": rel(a.context),
        "citation_pattern": r"^src-\d{3}(:L\d+(-L?\d+)?)?$",
        "groups": first,
        "deferred_groups": rest,   # held back until the findings gate passes on the first group; next tells you when to restore
        "excluded": excluded,
        "story_note": "TODO: how does the client frame its own problem? Which figure meets that framing?",
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("# Drafted by manifest.py from the lint registry. Review every group and fill each TODO.\n"
                "# Relative paths are relative to THIS file's directory.\n")
        yaml.safe_dump(manifest, f, sort_keys=False, allow_unicode=True, width=120)
    print(f"{len(first)} group(s) active, {len(rest)} deferred, {len(pre)} pre-reads, {len(excluded)} excluded -> {a.out}")


if __name__ == "__main__":
    main()
