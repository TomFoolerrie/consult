#!/usr/bin/env python3
"""The orchestrator's entry point. Everything up to the spawn boundary.

  run.py next     [--manifest M] [--root DIR]   # inspect state, print the next step (command or gate)
                                               # without a manifest it inspects the engagement dir and prints
                                               # the pre-loop step: register, annotate, profile, init, draft
  run.py render   --manifest M --op OP [--group G] [--format full|brief]
                                               # full: self-contained prompt (any harness). brief: the per-run
                                               # part only, for a Claude Code subagent produced by `agents`
  run.py agents   --out DIR [--prefix assess-] [--model inherit]
                                               # write Claude Code subagent files (frontmatter + static body)
  run.py check    --manifest M [--gate LAYER]  # validate + trace with the manifest's paths
  run.py gate     --manifest M --name findings|revise --status passed|rerun [--note "..."]
                                               # record a human decision
  run.py status   --manifest M                 # counts, gates, groups extracted

`render` is the wiring: it resolves every {{placeholder}} in prompts/<op>.md
from the manifest and the registry, prepends the exact script paths, and
writes <workdir>/prompts/<agent>.md. The orchestrator's only job after that
is to start an agent whose instructions are that file.

`next` reads the ledgers, the manifest, and gates.json in the ledger dir and
prints one thing to do. Loop on it.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import LAYERS, axes, current, finding_example, load_taxonomy, resolve_manifest  # noqa: E402

try:
    import yaml
except ImportError:
    sys.exit("pyyaml is required: pip install pyyaml")

SKILL = Path(__file__).resolve().parent.parent
# Claude Code subagent definitions: role -> (prompt body, frontmatter)
AGENT_DEFS = {
    "reader": ("reader.md", {
        "description": "Reads one group of registered client sources and logs findings to the assessment ledger; in edit mode revises its own findings against proposals. Only spawn with a brief written by run.py render --format brief.",
        "tools": "Read, Write, Bash, Grep, Glob"}),
    "normalizer": ("normalize.md", {
        "description": "Finds duplicate, split, drifted, or vague findings across reader groups and files proposals for their authors. Never edits. Spawn with a brief from run.py render.",
        "tools": "Read, Bash, Grep"}),
    "themer": ("themes.md", {
        "description": "Builds the theme ledger (root-cause diagnoses citing finding ids) from the findings ledger and the client context. Spawn with a brief from run.py render.",
        "tools": "Read, Write, Bash, Grep"}),
    "recommender": ("recommend.md", {
        "description": "Builds recommendations (what should be different) that cite themes. Spawn with a brief from run.py render.",
        "tools": "Read, Write, Bash, Grep"}),
    "planner": ("plan.md", {
        "description": "Turns recommendations into owned, sized, sequenced initiatives. Spawn with a brief from run.py render.",
        "tools": "Read, Write, Bash, Grep"}),
    "storyteller": ("story.md", {
        "description": "Writes the assessment narrative from the rendered tables and figure catalog, every claim id-cited. Spawn with a brief from run.py render.",
        "tools": "Read, Write, Bash, Grep"}),
    "retrospector": ("retro.md", {
        "description": "Writes the post-phase report (bugs, efficiency, findings quality, coverage, notes) from the ledgers, trace, and the session's own experience. Spawn after fan-out and after the story.",
        "tools": "Read, Write, Bash, Grep"}),
    "digester": ("digest.md", {
        "description": "Condenses the engagement's shared pre-reads (profile, objective, org chart, notes) into one compact context digest that every reader loads instead of the raw files. Spawn once per engagement, before extract.",
        "tools": "Read, Write, Grep"}),
}
OP_ROLE = {"extract": "reader", "revise": "reader", "normalize": "normalizer", "themes": "themer",
           "recommend": "recommender", "plan": "planner", "story": "storyteller", "digest": "digester", "retro": "retrospector"}

OPS = {  # op -> (prompt file, agents key)
    "extract": ("reader.md", "reader"),
    "revise": ("reader.md", "reader"),
    "normalize": ("normalize.md", "normalize"),
    "themes": ("themes.md", "themes"),
    "recommend": ("recommend.md", "recommend"),
    "plan": ("plan.md", "plan"),
    "story": ("story.md", "story"),
    "digest": ("digest.md", "digest"),
    "retro": ("retro.md", "retro"),
}


# ------------------------------------------------------------------ helpers
def load(mpath):
    return resolve_manifest(mpath, SKILL)


def P(m, key, **fmt):
    return m["paths"][key].format(**fmt) if fmt else m["paths"][key]


def root_of(m):
    """The engagement root every relative path is shown against: the git root if there is one, else the manifest dir."""
    from common import git_root
    return Path(m["consult_root"]) if m.get("mode") == "consult" else (git_root(m["_root"]) or m["_root"])


def rel(m, path):
    """Display form of a path: relative to the engagement root, forward slashes."""
    import os
    try:
        r = os.path.relpath(os.path.normpath(str(path)), str(root_of(m))).replace("\\", "/")
        return os.path.normpath(str(path)) if r.startswith("..") else r   # outside the root: show it whole rather than ../../..
    except ValueError:  # different drive on Windows
        return str(path)


def py_cmd():
    n = Path(sys.executable).name
    return n[:-4] if n.lower().endswith(".exe") else n


def write_shim(m):
    """A tiny wrapper with every long path baked in, so agents run short commands from the engagement root."""
    shim = Path(P(m, "shim"))
    shim.parent.mkdir(parents=True, exist_ok=True)
    reg = m.get("registry") or ""
    src = f'''#!/usr/bin/env python3
# Generated by consult-assessment run.py render. Do not edit; re-rendered every op.
# Usage (from anywhere): {py_cmd()} {rel(m, shim)} <command> [args]
#   ledger <ledger.py args>        ledger dir + taxonomy pre-set   e.g. ledger append findings --author reader-G1 --group G1 --from <rows.jsonl>
#   validate [--gate LAYER]        validate.py with registry
#   trace                          trace.py
#   check [--gate LAYER]           validate + trace
#   render tables|figures|bundle   render.py with the manifest
#   cite src-NNN:Lnn[-Lnn]         print the cited source lines
#   taxonomy                       print the taxonomy (axes, scales, rules)
#   playbook                       print the data-analysis playbook (which procedures for which dataset)
#   data profile <src>             columns, types, ranges, samples of a tabular source
#   data run <proc> <src> [opts]   a standard procedure; output saved under analysis/ and registered as a citable source
#   data procedures                list procedures
#   next                           run.py next
import os, subprocess, sys
from pathlib import Path
ROOT = r"{root_of(m)}"
SKILL = r"{m["skill"]}"
LINT = r"{m["lint_skill"]}"
LEDGER = r"{P(m, "ledger_dir")}"
TAX = r"{m["taxonomy"]}"
REG = r"{reg}"
MANIFEST = r"{m["_path"]}"
ANALYSIS = r"{P(m, "analysis")}"
CONSULT_ROOT = {m.get("consult_root")!r}
CAPTURE_INTENT = {m.get("capture_intent", [])!r}
os.environ.setdefault("PYTHONUTF8", "1"); os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.chdir(ROOT)
S = lambda n: str(Path(SKILL) / "scripts" / n)
cmd, rest = (sys.argv[1] if len(sys.argv) > 1 else "help"), sys.argv[2:]
if cmd == "ledger":     args = [sys.executable, S("ledger.py"), "--ledger-dir", LEDGER, "--taxonomy", TAX] + rest
elif cmd == "validate": args = [sys.executable, S("validate.py"), "--ledger-dir", LEDGER, "--taxonomy", TAX] + (["--consult-root", CONSULT_ROOT] if CONSULT_ROOT else (["--registry", REG] if REG else [])) + rest
elif cmd == "trace":    args = [sys.executable, S("trace.py"), "--ledger-dir", LEDGER, "--taxonomy", TAX] + rest
elif cmd == "check":    args = [sys.executable, S("run.py"), "check", "--manifest", MANIFEST] + rest
elif cmd == "next":     args = [sys.executable, S("run.py"), "next", "--manifest", MANIFEST] + rest
elif cmd == "render":   args = [sys.executable, S("render.py")] + rest[:1] + ["--manifest", MANIFEST] + rest[1:]
elif cmd == "cite":     args = ([sys.executable, S("consult_bridge.py"), "cite", CONSULT_ROOT] if CONSULT_ROOT else [sys.executable, str(Path(LINT) / "scripts" / "lint.py"), "cite", "--registry", REG]) + rest
elif cmd == "taxonomy": print(open(TAX, encoding="utf-8").read()); sys.exit(0)
elif cmd == "playbook": print(open(str(Path(SKILL) / "references" / "data-playbook.md"), encoding="utf-8").read()); sys.exit(0)
elif cmd == "data":
    if CONSULT_ROOT:
        args = [sys.executable, S("data.py"), "--consult-root", CONSULT_ROOT, "--analysis-dir", ANALYSIS] + [item for target in CAPTURE_INTENT for item in ("--intent", target)] + rest
    else:
        args = [sys.executable, S("data.py"), "--registry", REG, "--analysis-dir", ANALYSIS] + rest
else:
    print(open(__file__, encoding="utf-8").read().split("import os")[0]); sys.exit(2)
sys.exit(subprocess.call(args))
'''
    shim.write_text(src, encoding="utf-8")
    return shim


def registry(m):
    if m.get("mode") == "consult":
        from consult_bridge import registry as engine_registry
        return engine_registry(m)
    if not m.get("registry"):
        return {}
    reg = yaml.safe_load(open(m["registry"], encoding="utf-8")) or {}
    return {s["id"]: s for s in reg.get("sources", [])}


def group_coverage(m, st, group):
    """Declared sources vs sources actually cited by the group's author.
    A group is complete only when every declared source has at least one finding."""
    cited = set()
    for f in st["findings_all"].values():
        if f.get("author") == group["agent"]:
            for src in f.get("sources", []):
                cited.add(src.split(":")[0])
    declared = list(group.get("sources", []))
    done = [x for x in declared if x in cited]
    remaining = [x for x in declared if x not in cited]
    return {"done": done, "remaining": remaining,
            "state": "complete" if not remaining else ("partial" if done else "not started")}


def prior_index(m, st, group, tax):
    """Compact index of findings from the groups this group builds on, plus open items and coverage gaps.
    Rendered into the brief AFTER the sources, and the reader is told to consult it only after its own
    blind pass. Returns (text, count)."""
    from common import EVIDENCE_TYPES, primary_axis
    deps = group.get("builds_on") or []
    all_groups = m["groups"] + m["deferred_groups"]
    if deps == "all" or deps == ["all"]:
        deps = [x["id"] for x in all_groups if x["id"] != group["id"]]
    if not deps:
        return "", 0
    authors = {x["agent"] for x in all_groups if x["id"] in deps}
    pa = primary_axis(tax)
    rows = [f for f in st["findings"].values() if f.get("author") in authors]
    rows.sort(key=lambda f: (str(f.get(pa, "")), -(f.get("severity") or 0), f["id"]))
    lines = []
    opens = []
    for f in rows:
        cat = f.get(pa)
        cat = "; ".join(cat) if isinstance(cat, list) else (cat or "")
        obs = f["observation"].replace("\n", " ")
        obs = obs[:140] + ("…" if len(obs) > 140 else "")
        src = ", ".join(f["sources"][:2]) + (" …" if len(f["sources"]) > 2 else "")
        if f["type"] == "open_item":
            opens.append(f"  - {f['id']}: {obs}  [{src}]")
        else:
            lines.append(f"  - {f['id']} · {f['type']} · sev {f.get('severity')} · {f['evidence_basis']} · {cat}: {obs}  [{src}]")
    # coverage gaps so far
    counts = {c: 0 for c in tax["axes"][pa]["values"]}
    for f in st["findings"].values():
        if f["type"] in EVIDENCE_TYPES:
            v = f.get(pa)
            for c in (v if isinstance(v, list) else [v]):
                if c in counts:
                    counts[c] += 1
    uncovered = [c for c, n in counts.items() if n == 0]
    text = (f"Findings so far from {', '.join(deps)} ({len(lines)}). Consult ONLY after your blind pass; use for `related`, "
            f"corroboration, contradiction, and to answer open questions - not as a checklist to confirm.\n" + "\n".join(lines))
    if opens:
        text += f"\n\nOpen questions earlier readers left ({len(opens)}) - if your sources answer one, log the answer as a finding and set `related` to the open item:\n" + "\n".join(opens)
    if uncovered:
        text += f"\n\nNothing logged yet on: {', '.join(uncovered)}. If your sources touch these, that is worth a finding even if minor."
    return text, len(lines)


def ledger_state(m):
    ld = Path(P(m, "ledger_dir"))
    if not (ld / ".assessment-ledger").exists():
        return None
    st = {k: current(ld, k) for k in LAYERS}
    st["findings_all"] = current(ld, "findings", include_retired=True)
    st["proposals_open"] = {k: v for k, v in current(ld, "proposals", include_retired=True).items() if v.get("status") == "open"}
    st["authors"] = {f.get("author") for f in st["findings"].values()}
    return st


def gates(m):
    p = Path(P(m, "gates"))
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def q(x):
    """Quote a path for display in a command line. Paths with spaces or
    parentheses (OneDrive, 'Client (2026)') must be quoted or the orchestrator
    will paste a broken command."""
    x = str(x)
    return f'"{x}"' if any(c in x for c in " ()&") else x


def script(m, name):
    return f"{py_cmd()} {q(Path(m['skill']) / 'scripts' / name)}"


def script_argv(m, name):
    return [sys.executable, str(Path(m["skill"]) / "scripts" / name)]


def ledger_cmd(m, rest):
    return f"{script(m, 'ledger.py')} --ledger-dir {q(P(m, 'ledger_dir'))} {rest}"


def validate_argv(m, gate=None):
    argv = script_argv(m, "validate.py") + ["--ledger-dir", P(m, "ledger_dir"), "--taxonomy", m["taxonomy"]]
    if m.get("mode") == "consult":
        argv += ["--consult-root", m["consult_root"]]
    elif m.get("registry"):
        argv += ["--registry", m["registry"]]
    if gate:
        argv += ["--gate", gate]
    return argv


def validate_cmd(m, gate=None):
    argv = validate_argv(m, gate)
    return script(m, "validate.py") + " " + " ".join(q(x) for x in argv[2:])


# ------------------------------------------------------------------ render
def fill(text, values):
    missing = set()

    def sub(mo):
        k = mo.group(1)
        if k in values:
            return str(values[k])
        missing.add(k)
        return mo.group(0)
    out = re.sub(r"\{\{(\w+)\}\}", sub, text)
    return out, missing


def cmd_render(a):
    m = load(a.manifest)
    if a.op not in OPS:
        sys.exit(f"unknown op {a.op}; one of {list(OPS)}")
    pfile, akey = OPS[a.op]
    reg = registry(m)
    group = None
    if a.op in ("extract", "revise"):
        if not a.group:
            sys.exit("--group required for extract/revise")
        group = next((g for g in m["groups"] if g["id"] == a.group), None) or sys.exit(f"no group {a.group}")
    agent = group["agent"] if group else m["agents"][akey]
    mode = "edit" if a.op == "revise" else "read"

    tax = load_taxonomy(m["taxonomy"])
    t_axes = axes(tax, on_theme=True)
    theme_ex = {"theme": "<pattern named as a diagnosis>", "root_cause": "<one sentence a CFO would accept>"}
    theme_ex.update({n: (ax["values"] or ["<value>"])[0] for n, ax in t_axes.items()})
    theme_ex.update({"impact": "<what the combination of these findings does to the client>", "findings": ["F-003", "F-011", "F-027"]})
    shim = write_shim(m)
    R = lambda x: rel(m, x)  # noqa: E731
    sh = f"{py_cmd()} {q(R(shim))}"
    values = {
        "sh": sh,
        "root": str(root_of(m)),
        "finding_example": finding_example(tax).replace("src-", "SRC-") if m.get("mode") == "consult" else finding_example(tax),
        "theme_axes": ", ".join(f"`{n}`" for n in t_axes) or "(none declared)",
        "theme_example": json.dumps(theme_ex, ensure_ascii=False),
        "agent": agent, "group": a.group or "", "mode": mode, "skill": R(m["skill"]),
        "ledger_dir": R(P(m, "ledger_dir")), "workdir": R(P(m, "workdir")), "out": R(P(m, "out")),
        "tables": R(P(m, "tables")), "figures": R(P(m, "figures")), "story": R(P(m, "story")), "bundle": R(P(m, "bundle")),
        "taxonomy": f"`{sh} taxonomy` (prints it)", "registry": R(m.get("registry", "")) if m.get("registry") else "", "context": R(m.get("context", "")) if m.get("context") else "",
        "note": (group or {}).get("note") or m.get("story_note") or "(none)",
        "src": "<src-id>",  # per-document variable inside the reader prompt; the reader fills it
    }
    if group:
        ctx = str(Path(m["context"]).resolve()) if m.get("context") else None
        pre = [p for p in group.get("pre_read", [])
               if not (ctx and str((m["_root"] / p).resolve() if not Path(p).is_absolute() else Path(p).resolve()) == ctx)]
        digest = Path(P(m, "digest"))
        if digest.exists():
            values["pre_read"] = (f"  - {R(digest)}   (context digest - read this INSTEAD of the raw pre-reads; "
                                  f"the raw files are listed under reference in case you need a detail)")
            values["reference"] = "\n".join(f"  - {R(m['_root'] / p) if not Path(p).is_absolute() else R(p)}"
                                             for p in pre + group.get("reference", [])) or "  (none)"
        else:
            values["pre_read"] = "\n".join(f"  - {R(m['_root'] / p) if not Path(p).is_absolute() else R(p)}" for p in pre) or "  (none)"
            values["reference"] = "\n".join(f"  - {R(m['_root'] / p) if not Path(p).is_absolute() else R(p)}"
                                             for p in group.get("reference", [])) or "  (none)"
        st_now = ledger_state(m) or {"findings": {}, "findings_all": {}, "proposals_open": {}}
        cov = group_coverage(m, st_now, group)
        lines = []
        for sid in group["sources"]:
            e = reg.get(sid)
            if not e:
                lines.append(f"  - {sid} → (NOT IN REGISTRY - stop and tell the orchestrator)")
                continue
            path = Path(e["file"]) if m.get("mode") == "consult" else Path(m["registry"]).parent / e["file"]
            n = int(e.get("lines") or 0)
            kind = (e.get("kind") or "").lower()
            if kind in ("spreadsheet", "listing", "data", "extract", "register", "schedule") or str(e.get("file", "")).lower().endswith((".csv", ".tsv", ".xlsx")):
                strat = ("CSV ONLY in integrated mode: data profile then data run; cite data records as SRC-nnn:R<number>, not physical lines. XLSX/TSV and normalized-text mappings are not supported; never use standalone registration" if m.get("mode") == "consult" else "TABULAR: `data profile` first, then `data run` procedures per the playbook; cite source rows AND the analysis; never read linearly")
            elif kind in ("interview", "transcript", "summary") or (n and n <= 1500):
                strat = "read fully"
            else:
                strat = "LARGE: headings/structure first, then grep for what the note asks; never read linearly"
            state = "  [DONE - already logged by you; do not re-read]" if sid in cov["done"] else ""
            lines.append(f"  - {sid} → {R(path)}  ({e.get('kind') or 'kind?'}, {e.get('words', '?')} words, {n or '?'} lines) — {strat}{state}")
        values["sources"] = "\n".join(lines)
        pi_text, pi_n = prior_index(m, st_now if st_now.get("findings") is not None else {"findings": {}}, group, tax) \
            if st_now.get("findings") is not None else ("", 0)
        values["prior"] = pi_text or "(none - this group reads blind; builds_on is not set)"
        if mode == "read" and cov["state"] == "partial":
            values["resume"] = (f"RESUME: you (or a previous {agent}) already logged findings for {', '.join(cov['done'])}. "
                                f"Do not re-read those. Start at {cov['remaining'][0]} and work through the remaining "
                                f"{len(cov['remaining'])}. `ledger show findings` lists your existing ids for `related`.")
        else:
            values["resume"] = "(fresh start)"
        if mode == "edit":
            st = ledger_state(m) or {"proposals_open": {}}
            mine = [p for p in st["proposals_open"].values() if p.get("target_author") == agent]
            values["proposals"] = "\n".join(
                f"  - {p['id']}: {p['kind']} on {p['target']} — {p['reason']}"
                + (f" | set {p['set']}" if p.get("set") else "") + (f" | absorb {p['absorb']}" if p.get("absorb") else "")
                for p in mine) or "  (none open for you)"
        else:
            values["proposals"] = "(read mode)"
    else:
        values.update({"reference": "", "resume": ""})

    values["manifest"] = str(m["_path"])
    if a.op == "retro":
        values["phase"] = a.phase or "extract"
        values["retro"] = R(P(m, "retro", phase=values["phase"]))
    if a.op == "digest":
        allpre = []
        for g in m["groups"] + m["deferred_groups"]:
            for pth in g.get("pre_read", []):
                pp = (m["_root"] / pth) if not Path(pth).is_absolute() else Path(pth)
                if pp not in allpre:
                    allpre.append(pp)
        if m.get("context"):
            cp = Path(m["context"])
            if cp not in allpre:
                allpre.insert(0, cp)
        values["pre_read"] = "\n".join(f"  - {R(x)}" for x in allpre) or "  (none)"
        values["digest"] = R(P(m, "digest"))
    brief_t = (SKILL / "prompts" / pfile.replace(".md", ".brief.md")).read_text(encoding="utf-8")
    brief, missing = fill(brief_t, values)
    if missing:
        sys.exit(f"unfilled placeholders in {pfile.replace('.md', '.brief.md')}: {sorted(missing)} - fix the manifest or run.py")
    if a.format == "brief":
        body = brief
    else:
        static, m2 = fill((SKILL / "prompts" / pfile).read_text(encoding="utf-8"), values)
        body = static + "\n\n---\n\n" + brief

    header = f"""<!-- rendered by run.py from {m['_path']} | op={a.op} agent={agent} format={a.format} -->
# Environment

Engagement root: `{root_of(m)}` — run every command from here; every path below is relative to it.
Command shim (all long paths are baked in; never call the skill scripts directly): `{sh} <command>`
Quote any path that contains a space when you pass it on a command line.

- `{sh} ledger <args>`            ledger.py with ledger dir and taxonomy pre-set
- `{sh} validate [--gate L]`      validate.py with the registry
- `{sh} trace`                    traceability and orphans
- `{sh} cite src-NNN:Lnn`         print the cited lines of a source
- `{sh} taxonomy`                 print the taxonomy (axes, scales, rules) — read it this way
- `{sh} data profile <src>`       tabular source: columns, types, ranges, samples
- `{sh} data run <proc> <src> …`  a standard procedure; output is saved under `{R(P(m, 'analysis'))}` and registered as a citable source
- `{sh} playbook`                 which procedures fit which dataset (JE listing, bank rec, aging, TB, payroll, commissions)
- `{sh} render tables|figures|bundle`
- context: `{R(m['context']) if m.get('context') else '(none)'}`
- workdir: `{R(P(m, 'workdir'))}` (yours)   tables/figures/story: `{R(P(m, 'tables'))}` / `{R(P(m, 'figures'))}` / `{R(P(m, 'story'))}`

Never write ledger files directly.

---

"""
    if m.get("mode") == "consult":
        header = header.replace("src-NNN", "SRC-NNN").replace("validate.py with the registry", "local schema/layer checks plus engine evidence verification")
        header = "\n".join(line for line in header.split("\n") if not any(x in line for x in ("data profile", "data run", "playbook`")))
        header += ("\n## CONSULT integration boundary\nUse uppercase engine SRC IDs from this brief. Legacy lower-case examples in static prompts are syntax examples, not aliases. "
                   "`cite` returns verified JSON with text and location. Do not create or edit a source registry. "
                   "CSV data profile/run use verified snapshots, versioned synthesis publication and manifest capture_intent; use :R<number> for data records and :Lstart-Lend for analysis text. Non-CSV tables are not supported. "
                   "Run registrations serially; on an intake-busy refusal preserve the artifact and retry publication, never delete another writer's lock. "
                   "Use the shim data profile/run commands, never fall back to standalone registration. "
                   "Method review does not authorize client sends or accept engine findings.\n\n")
        body = body.replace("src-", "SRC-")
    outdir = Path(P(m, "prompts"))
    outdir.mkdir(parents=True, exist_ok=True)
    outp = outdir / (f"{agent}.brief.md" if a.format == "brief" else f"{agent}.md")
    outp.write_text(header + body, encoding="utf-8")
    print(outp)


def cmd_agents(a):
    outdir = Path(a.out)
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for role, (pfile, fm) in AGENT_DEFS.items():
        name = f"{a.prefix}{role}"
        front = {"name": name, "description": fm["description"], "tools": fm["tools"], "model": a.model}
        body = (SKILL / "prompts" / pfile).read_text(encoding="utf-8")
        note = ("\n\n---\nYou were started with a brief (the task message). It names your author identity, every path, "
                "and every command. Use those exactly; do not guess paths or write ledger files directly.\n")
        text = "---\n" + "\n".join(f"{k}: {v}" for k, v in front.items()) + "\n---\n\n" + body + note
        (outdir / f"{name}.md").write_text(text, encoding="utf-8")
        written.append(name)
    if a.with_orchestrator:
        name = f"{a.prefix}orchestrator"
        roles = ", ".join(f"{a.prefix}{r}" for r in AGENT_DEFS)
        front = {"name": name,
                 "description": "Runs a consult-assessment engagement end to end: loops on run.py next, renders briefs, spawns the assess-* subagents, checkpoints, and stops at the human gates. Invoke with the path to a run manifest.",
                 "tools": f"Agent({roles}), Read, Write, Bash, Grep, Glob", "model": a.model}
        runbook = (SKILL / "references" / "runbook.md").read_text(encoding="utf-8")
        body = (f"# Orchestrator\n\nYou run one engagement from a manifest the user names. Your loop is "
                f"`python3 {SKILL}/scripts/run.py next --manifest <M>`: do the one thing it prints, then call it again. "
                f"When it says spawn, render the brief with `--format brief`, read it, and call the Agent tool with "
                f"`subagent_type` set to the matching {a.prefix}* subagent and the brief's text as `prompt` "
                f"(`run_in_background: true` for parallel readers; wait for all before `check`). "
                f"When it says [HUMAN], stop and hand the user exactly what it names; do not proceed until they answer "
                f"and you have recorded it with `run.py gate`. Never write ledger files directly; never fix ledger rows to "
                f"pass a gate; roll back with git as the runbook says.\n\nThe runbook you follow:\n\n" + runbook)
        (outdir / f"{name}.md").write_text("---\n" + "\n".join(f"{k}: {v}" for k, v in front.items()) + "\n---\n\n" + body, encoding="utf-8")
        written.append(name)
    print(f"{len(written)} agents -> {outdir}: {', '.join(written)}")
    print("map ops to subagents: " + ", ".join(f"{op}->{a.prefix}{role}" for op, role in OP_ROLE.items()))


# ------------------------------------------------------------------ check / gate / status
def cmd_check(a):
    m = load(a.manifest)
    rc = subprocess.run(validate_argv(m, a.gate)).returncode
    subprocess.run(script_argv(m, "trace.py") + ["--ledger-dir", P(m, "ledger_dir"), "--taxonomy", m["taxonomy"]])
    sys.exit(rc)


def cmd_gate(a):
    m = load(a.manifest)
    p = Path(P(m, "gates"))
    p.parent.mkdir(parents=True, exist_ok=True)
    g = gates(m)
    g[a.name] = {"status": a.status, "note": a.note or ""}
    p.write_text(json.dumps(g, indent=2) + "\n", encoding="utf-8")
    print(f"gate {a.name}: {a.status}")


def cmd_status(a):
    m = load(a.manifest)
    st = ledger_state(m)
    if st is None:
        print("ledger not initialized")
        return
    print({k: len(st[k]) for k in LAYERS} | {"open_proposals": len(st["proposals_open"])})
    for grp in m["groups"] + [dict(x, id=x["id"] + " (deferred)") for x in m["deferred_groups"]]:
        c = group_coverage(m, st, grp)
        extra = f"  remaining: {c['remaining']}" if c["state"] == "partial" else ""
        print(f"  {grp['id']:<16} {c['state']:<12} {len(c['done'])}/{len(grp.get('sources', []))} sources{extra}")
    print("paths:", m["paths"]); print("agents:", m["agents"])
    print("gates:", gates(m) or "(none)")


# ------------------------------------------------------------------ next
def find_manifest(root):
    hits = [p for p in Path(root).rglob("manifest.yaml") if "skill" in (p.read_text(encoding="utf-8", errors="ignore")[:2000]) and ".git" not in p.parts]
    return hits


def R_(m, path):
    return rel(m, path)


def cmd_next(a):
    say = lambda kind, msg: print(f"[{kind}] {msg}")  # noqa: E731
    if not a.manifest:
        root = Path(a.root or ".").resolve()
        found = find_manifest(root)
        if len(found) == 1:
            a.manifest = str(found[0])
            print(f"(using manifest {a.manifest})")
        elif len(found) > 1:
            return say("HUMAN", f"several manifests under {root}: {[str(p) for p in found]} - which one? pass --manifest")
        else:
            if (root / "_sources").is_dir():
                return say("RUN", "CONSULT engagement detected. Prepare an explicit mode: consult manifest using engine source IDs (see INTEGRATION.md); do not create a standalone registry.")
            regs = [p for p in root.rglob("registry.yaml") if ".git" not in p.parts]
            if not regs:
                return say("RUN", f"no registry under {root}. Register the sources first: "
                                  f"{py_cmd()} <consult-lint>/scripts/lint.py register --in <sources dir> [--in ...] [--ext md,csv] --registry <sources dir>/registry.yaml")
            reg_path = regs[0]
            reg = yaml.safe_load(open(reg_path, encoding="utf-8")) or {}
            active = [x for x in reg.get("sources", []) if x.get("status") == "active"]
            unkinded = [x["id"] for x in active if not x.get("kind")]
            if unkinded:
                return say("HUMAN", f"{len(unkinded)} of {len(active)} sources in {reg_path} have no `kind` ({unkinded[:6]}{'...' if len(unkinded) > 6 else ''}). "
                                    f"Ask the human to fill kind, people (interviews), pre_read_candidate (context docs), and above all `topic` "
                                    f"(the question each source bears on - this is what makes the reader groups coherent) and `summary_of` on summaries; then re-run.")
            profiles = [p for p in root.rglob("profile.md") if ".git" not in p.parts]
            if not profiles:
                return say("HUMAN", f"no client profile found under {root}. Ask for a one-page context-profile (business, size, finance team, systems, "
                                    f"why the engagement exists, what the client thinks the problem is) and save it, e.g. {reg_path.parent}/profile.md; then re-run.")
            return say("RUN", f"draft the manifest: {py_cmd()} {q(SKILL / 'scripts' / 'manifest.py')} draft --registry {q(reg_path)} "
                              f"--out <where you keep it>/manifest.yaml --context {q(profiles[0])} [--ledger-dir --workdir --out-dir]  "
                              f"then review the groups against references/manifest.md (fewer, larger, coherent - one per question; merge if the draft made more than ~8), "
                              f"edit: run name, paths/agents to your layout, each group's note, engagement_objective/notes in pre_read. Commit. Re-run next --manifest.")
    m = load(a.manifest)
    st = ledger_state(m)

    if st is None:
        return say("RUN", ledger_cmd(m, "init") + "  (then: ledger.py checkpoint -m 'before extract')")
    g = gates(m)
    groups = m["groups"]
    cov = {x["id"]: group_coverage(m, st, x) for x in groups + m["deferred_groups"]}
    complete = [x for x in groups if cov[x["id"]]["state"] == "complete"]
    partial = [x for x in groups if cov[x["id"]]["state"] == "partial"]
    todo = [x for x in groups if cov[x["id"]]["state"] == "not started"]

    # A partial group is a coverage hole that looks like completion. Always finish it first.
    if partial:
        x = partial[0]; c = cov[x["id"]]
        return say("RUN", f"group {x['id']} is PARTIAL: {len(c['done'])}/{len(x['sources'])} sources logged, remaining {c['remaining']}. "
                          f"run.py render --manifest {q(m['_path'])} --op extract --group {x['id']} --format brief → the brief is a RESUME brief "
                          f"(done sources marked, remaining listed) → spawn {x['agent']} again; then run.py check; checkpoint")

    # Digest before the first reader if the shared pre-reads are big
    digest = Path(P(m, "digest"))
    if not complete and not digest.exists():
        total = 0
        for x in groups[:1]:
            for pth in x.get("pre_read", []):
                pp = (m["_root"] / pth) if not Path(pth).is_absolute() else Path(pth)
                if pp.exists():
                    total += pp.read_text(encoding="utf-8", errors="ignore").count("\n")
        if m.get("context") and Path(m["context"]).exists():
            total += Path(m["context"]).read_text(encoding="utf-8", errors="ignore").count("\n")
        if total > 250:
            return say("RUN", f"shared pre-reads are {total} lines and every reader would load them all. "
                              f"run.py render --manifest {q(m['_path'])} --op digest --format brief → spawn {m['agents']['digest']} once; "
                              f"it writes {q(R_(m, digest))}; readers then get the digest instead. (Skip by creating an empty digest file.)")

    # Phase 3/4: extraction, with the first-run gate
    if not complete:
        first = groups[0]["id"]
        return say("RUN", f"run.py render --manifest {q(m['_path'])} --op extract --group {first} [--format brief]  → spawn {groups[0]['agent']} with that file; "
                          f"then run.py check; then ledger.py checkpoint -m 'extract {first}'")
    if g.get("findings", {}).get("status") != "passed":
        if g.get("findings", {}).get("status") == "rerun":
            if m.get("mode") == "consult":
                return say("RUN", "Apply the human's correction through author-owned revisions; preserve earlier rows and registered outputs. Show a revised sample before requesting findings review again. Do not delete the run or roll back the whole engagement.")
            return say("RUN", f"git checkout -- {q(P(m, 'ledger_dir'))} && rm -rf {q(P(m, 'workdir'))}  → apply the prompt change from the gate note "
                              f"→ run.py gate --name findings --status pending → render/extract {complete[0]['id']} again")
        return say("HUMAN", f"findings gate: hand over `{ledger_cmd(m, 'show findings --md')}` plus five `cite` spot checks; "
                            f"human reviews against references/review-rubric.md; record with "
                            f"`run.py gate --manifest {q(m['_path'])} --name findings --status passed|rerun`")
    if m["deferred_groups"]:
        ids = [x["id"] for x in m["deferred_groups"]]
        return say("RUN", f"findings gate passed: restore the {len(ids)} deferred groups {ids} - move them from `deferred_groups:` to `groups:` "
                          f"in the manifest (they were held back for the first-run review) - then re-run next")
    if todo:
        complete_ids = {x["id"] for x in complete}
        def ready(x):
            deps = x.get("builds_on") or []
            if deps in ("all", ["all"]):
                deps = [y["id"] for y in groups if y["id"] != x["id"]]
            return all(d in complete_ids for d in deps)
        wave = [x for x in todo if ready(x)]
        waiting = [x for x in todo if not ready(x)]
        if not wave:
            return say("HUMAN", f"no spawnable group: {[x['id'] for x in waiting]} all wait on builds_on groups that are not complete "
                                f"(circular or mis-typed dependency?). Fix the manifest.")
        ids = " ".join(x["id"] for x in wave)
        tail = (f" — then {[x['id'] for x in waiting]} become spawnable (they build on this wave)" if waiting else "")
        return say("RUN", f"fan out wave: for G in {ids}: run.py render --op extract --group G → spawn in parallel; "
                          f"when all finish: run.py check; ledger.py checkpoint -m 'extract wave'{tail}")

    # retro after the fan-out: the report that turns one run's pain into the next run's fixes
    retro_x = Path(P(m, "retro", phase="extract"))
    if not retro_x.exists():
        return say("RUN", f"all groups complete. run.py render --manifest {q(m['_path'])} --op retro --phase extract --format brief → spawn "
                          f"{m['agents']['retro']}; it writes {q(R_(m, retro_x))} (bugs / efficiency / quality / coverage / notes). "
                          f"Hand it to the human with the findings. (Skip by creating the file empty.)")

    # normalize / revise
    normalized = g.get("normalized", {}).get("status") == "done"
    if not normalized:
        return say("RUN", "run.py render --op normalize → spawn; then `run.py gate --name normalized --status done`; checkpoint")
    if st["proposals_open"]:
        by_author = sorted({p.get("target_author") for p in st["proposals_open"].values() if p.get("target_author")})
        return say("RUN", f"revise: for each of {by_author}: run.py render --op revise --group <its group> → spawn; "
                          f"checkpoint after each. Then run.py check --gate themes")
    if g.get("revise", {}).get("status") != "passed":
        return say("HUMAN", "second look at findings after revise; record `run.py gate --name revise --status passed`")

    # layers
    if not st["themes"]:
        return say("RUN", "run.py render --op themes → spawn; run.py check --gate themes; checkpoint; surface orphans to the human")
    if not st["recommendations"]:
        return say("RUN", "run.py render --op recommend → spawn; run.py check --gate recommendations; checkpoint")
    if not st["initiatives"]:
        return say("RUN", "run.py render --op plan → spawn; run.py check --gate initiatives; checkpoint")
    if not (Path(P(m, "figures")) / "catalog.md").exists():
        return say("RUN", f"{script(m, 'render.py')} figures --manifest {q(m['_path'])} && {script(m, 'render.py')} tables --manifest {q(m['_path'])}; "
                          f"check {q(Path(P(m, 'figures')) / 'catalog.md')} for empty figures")
    if not Path(P(m, "story")).exists():
        if not m.get("story_note") or m["story_note"].startswith("TODO"):
            return say("HUMAN", "fill story_note in the manifest (client's own framing) before rendering the story prompt")
        return say("RUN", "run.py render --op story → spawn; then render.py bundle; final checkpoint")
    if not Path(P(m, "bundle")).exists():
        return say("RUN", f"{script(m, 'render.py')} bundle --manifest {q(m['_path'])}; final checkpoint")
    retro_l = Path(P(m, "retro", phase="layers"))
    if not retro_l.exists():
        return say("RUN", f"run.py render --manifest {q(m['_path'])} --op retro --phase layers --format brief → spawn {m['agents']['retro']}; "
                          f"it writes {q(R_(m, retro_l))}. (Skip by creating the file empty.)")
    return say("DONE", f"{P(m, 'bundle')} — hand to the deck renderer")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("next"); s.add_argument("--manifest"); s.add_argument("--root", help="engagement dir to inspect when no manifest is given (default: cwd)")
    s.set_defaults(fn=cmd_next)
    s = sub.add_parser("status"); s.add_argument("--manifest", required=True); s.set_defaults(fn=cmd_status)
    s = sub.add_parser("render"); s.add_argument("--manifest", required=True); s.add_argument("--op", required=True)
    s.add_argument("--group"); s.add_argument("--format", choices=["full", "brief"], default="full")
    s.add_argument("--phase", help="for --op retro: which phase this report covers (extract|layers)"); s.set_defaults(fn=cmd_render)
    s = sub.add_parser("agents"); s.add_argument("--out", required=True); s.add_argument("--prefix", default="assess-")
    s.add_argument("--model", default="inherit")
    s.add_argument("--with-orchestrator", action="store_true", help="also write an orchestrator subagent that runs the runbook loop")
    s.set_defaults(fn=cmd_agents)
    s = sub.add_parser("check"); s.add_argument("--manifest", required=True); s.add_argument("--gate"); s.set_defaults(fn=cmd_check)
    s = sub.add_parser("gate"); s.add_argument("--manifest", required=True); s.add_argument("--name", required=True)
    s.add_argument("--status", required=True); s.add_argument("--note"); s.set_defaults(fn=cmd_gate)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
