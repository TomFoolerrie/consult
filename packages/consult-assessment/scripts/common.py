"""Shared helpers: ledger I/O, schema, taxonomy loading.

Ledgers are JSONL, append-only. Each line is a full row version. The
current state of an id is the line with the highest `version`. Nothing is
ever rewritten in place; edits, retirements and merges append new versions.
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("pyyaml is required: pip install pyyaml")

# Windows consoles default to cp1252; findings contain em-dashes and arrows.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass

LAYERS = {
    "findings": {"prefix": "F", "file": "findings.jsonl"},
    "themes": {"prefix": "T", "file": "themes.jsonl"},
    "recommendations": {"prefix": "R", "file": "recommendations.jsonl"},
    "initiatives": {"prefix": "I", "file": "initiatives.jsonl"},
    "proposals": {"prefix": "P", "file": "proposals.jsonl"},
}

# Which lower layer each layer must cite (the layer-below rule).
CITES = {
    "themes": "findings",
    "recommendations": "themes",
    "initiatives": "recommendations",
}
REF_FIELD = {"themes": "findings", "recommendations": "themes", "initiatives": "recommendations"}

# Method schema: the fields every house shares. Classification axes on
# findings (and the axes themes carry) come from the taxonomy, not from here;
# ledger.py accepts any extra field and validate.py checks them against the axes.
# open_item: a topic that was not discussed, a PBC still outstanding, a question to ask -
# a fact about the ENGAGEMENT, not about the client. Kept in the ledger for traceability,
# excluded from evidence counts, themes, and the heat maps; rendered as its own list.
FINDING_TYPES = ["gap", "risk", "strength", "observation", "open_item"]
EVIDENCE_TYPES = ["gap", "risk", "observation"]   # what figures and themes count as evidence
EVIDENCE_BASIS = ["stated", "observed", "inferred"]
SCHEMA = {
    "findings": {
        "required": ["type", "severity", "evidence_basis", "observation", "sources"],
        "optional": ["related", "note"],
        "lists": ["sources", "related"],
    },
    "themes": {
        "required": ["theme", "root_cause", "impact", "findings"],
        "optional": ["note"],
        "lists": ["findings"],
    },
    "recommendations": {
        "required": ["solution", "principle", "themes"],
        "optional": ["what_changes", "what_stops", "findings", "note"],
        "lists": ["themes", "findings"],
    },
    "initiatives": {
        "required": ["initiative", "owner", "impact", "effort",
                     "time_required", "success_measure", "recommendations"],
        "optional": ["dependencies", "cost_effort_analysis", "note"],
        "lists": ["recommendations", "dependencies"],
    },
    "proposals": {
        "required": ["target", "kind", "reason"],
        "optional": ["set", "absorb", "resolution"],
        "lists": ["absorb"],
    },
}
META = ["id", "version", "author", "group", "status", "created_at", "edited_at",
        "edit_reason", "absorbed", "layer", "target_author", "proposer"]

DEFAULT_CITATION = r"^src-\d{3}(:L\d+(-L?\d+)?)?$"


class locked:
    """Exclusive lock on the ledger dir for the duration of an id-assigning write.
    Parallel readers append at the same time; without this two of them can
    compute the same next id. Uses fcntl on POSIX and msvcrt on Windows."""
    def __init__(self, ldir):
        self.path = Path(ldir) / ".lock"

    def __enter__(self):
        self.fh = open(self.path, "a+")
        try:
            import fcntl
            fcntl.flock(self.fh, fcntl.LOCK_EX)
            self._unlock = lambda: fcntl.flock(self.fh, fcntl.LOCK_UN)
        except ImportError:  # Windows
            import msvcrt
            import time
            fd = self.fh.fileno()
            self.fh.seek(0)
            deadline = time.time() + 120
            while True:
                try:
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                    break
                except OSError:
                    if time.time() > deadline:
                        raise SystemExit(f"could not acquire ledger lock {self.path} within 120s")
                    time.sleep(0.05)
            def _unlock():
                self.fh.seek(0)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            self._unlock = _unlock
        return self

    def __exit__(self, *a):
        try:
            self._unlock()
        finally:
            self.fh.close()


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


MARKER = ".assessment-ledger"


def git_root(path):
    """Path of the enclosing git work tree, or None."""
    import subprocess
    try:
        out = subprocess.run(["git", "-C", str(path), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True).stdout.strip()
        return Path(out) if out else None
    except Exception:  # noqa: BLE001
        return None


def ledger_dir(arg=None, for_write=False):
    """Resolve the ledger dir. Never creates it: `ledger.py init` does that, and
    writes a marker so a mistyped --ledger-dir fails instead of silently
    starting a second ledger somewhere. Writes additionally require the dir to
    be inside a git repo unless init recorded allow_no_git."""
    d = arg or os.environ.get("ASSESS_LEDGER_DIR")
    if not d:
        sys.exit("ledger dir required: --ledger-dir or ASSESS_LEDGER_DIR")
    p = Path(d)
    if not (p / MARKER).exists():
        sys.exit(f"REFUSED: {p} is not an initialized ledger dir (no {MARKER}). "
                 f"Run `ledger.py init --ledger-dir {p}` - or check the path; this is the guard "
                 f"against writing to the wrong directory.")
    if for_write:
        marker = json.loads((p / MARKER).read_text(encoding="utf-8") or "{}")
        if not marker.get("allow_no_git") and git_root(p) is None:
            sys.exit(f"REFUSED: {p} is not inside a git repository. The ledgers are the deliverable; "
                     f"put the engagement under version control before logging findings "
                     f"(`git init` the engagement dir, then `ledger.py checkpoint` after each op). "
                     f"To proceed without git, re-run `ledger.py init --allow-no-git`.")
    return p


def load_taxonomy(path):
    with open(path, encoding="utf-8") as f:
        tax = yaml.safe_load(f)
    if "axes" not in tax:
        sys.exit(f"{path}: taxonomy has no `axes` block - see references/taxonomy.md")
    for name, ax in tax["axes"].items():
        ax.setdefault("label", name.replace("_", " ").capitalize())
        ax.setdefault("values", [])
    return tax


def axes(tax, on_theme=None):
    """Axis name -> spec. on_theme=True filters to axes themes carry."""
    out = {}
    for name, ax in tax["axes"].items():
        if on_theme is None or bool(ax.get("on_theme")) == on_theme:
            out[name] = ax
    return out


def primary_axis(tax):
    for name, ax in tax["axes"].items():
        if ax.get("primary"):
            return name
    return next(iter(tax["axes"]))


def multi_axes(tax):
    return [n for n, a in tax["axes"].items() if a.get("multi")]


def coerce_axes(tax, row):
    """List-ify multi axes given as 'a; b'."""
    for n in multi_axes(tax):
        v = row.get(n)
        if isinstance(v, str):
            row[n] = [x.strip() for x in v.split(";") if x.strip()]
        elif v is None and n in row:
            row[n] = []
    return row


def finding_example(tax):
    """A JSON example row for the reader prompt, built from the axes."""
    ex = {"type": "gap"}
    for n, ax in tax["axes"].items():
        vals = ax.get("values") or ["<value>"]
        if ax.get("required_when"):
            k, v = next(iter(ax["required_when"].items()))
            if ex.get(k) not in (None, v):
                continue
            ex[k] = v
        ex[n] = [vals[0]] if ax.get("multi") else vals[0]
    ex.update({"severity": 2, "evidence_basis": "stated",
               "observation": "<one specific, sourced sentence>", "sources": ["src-002:L118-L124"], "related": []})
    return json.dumps(ex, ensure_ascii=False)


def load_manifest(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


# The orchestrator names everything. These are only the defaults it gets if it
# says nothing. Templates may reference earlier keys with {key}.
PATH_DEFAULTS = {
    "ledger_dir": "assessment/ledgers",
    "workdir": "assessment/work",
    "out": "assessment/out",
    "prompts": "{workdir}/prompts",
    "gates": "{ledger_dir}/gates.json",
    "tables": "{out}/tables",
    "figures": "{out}/figures",
    "story": "{out}/story.md",
    "bundle": "{out}/assessment-output.json",
    "review_pack": "{workdir}/review-{group}.md",
    "shim": "{workdir}/assess.py",          # command shim written by run.py render; agents call this, never the skill paths
    "digest": "{workdir}/context-digest.md", # compact pre-read digest written once by the digest op; readers get this instead of raw pre-reads
    "analysis": "{out}/analysis",            # registered analysis outputs from data.py (deliverable side: they are cited evidence)
    "retro": "{workdir}/retro-{phase}.md",   # post-phase report written by the retro op
}
AGENT_DEFAULTS = {
    "reader": "reader-{group}",
    "normalize": "normalizer",
    "themes": "themer",
    "recommend": "recommender",
    "plan": "planner",
    "story": "storyteller",
    "digest": "digester",
    "retro": "retrospector",
}


def resolve_manifest(path, skill_root):
    """Load a manifest and resolve paths/agents/skill/taxonomy into absolute,
    fully-templated values under m['paths'] and m['agents']. Top-level
    ledger_dir/workdir/out are accepted as shorthand for paths.*."""
    mpath = Path(path).resolve()
    m = load_manifest(mpath) or {}
    root = mpath.parent
    m["_path"], m["_root"] = mpath, root
    mode = m.get("mode", "standalone")
    if mode not in ("standalone", "consult"):
        raise ValueError(f"unknown assessment mode: {mode}")
    if mode == "consult":
        if m.get("registry"):
            raise ValueError("CONSULT mode cannot use a standalone registry")
        if not m.get("consult_root"):
            raise ValueError("CONSULT mode requires consult_root")
        m["consult_root"] = str((root / m["consult_root"]).resolve())
        if not (Path(m["consult_root"]) / "_sources").is_dir():
            raise ValueError("consult_root is not an engagement (_sources missing)")
        m["citation_pattern"] = r"^SRC-\d+(:(L\d+(-L?\d+)?|R\d+))?$"
        intent = m.get("capture_intent", [])
        if not isinstance(intent, list) or any(not isinstance(x, str) or not x.strip() for x in intent):
            raise ValueError("capture_intent must be a list of genuine capture target slugs")

    if not m.get("skill") or "<" in str(m["skill"]) or not Path(m["skill"]).exists():
        m["skill"] = str(skill_root)
    if not m.get("taxonomy") or "<" in str(m["taxonomy"]):
        m["taxonomy"] = str(Path(skill_root) / "assets" / "taxonomy.yaml")
    m.setdefault("lint_skill", str(Path(skill_root).parent / "consult-lint"))

    paths = dict(PATH_DEFAULTS)
    if mode == "consult":
        paths = {k: (v.replace("assessment/", "_synthesis/assessment/", 1) if v.startswith("assessment/") else v) for k, v in paths.items()}
    for k in ("ledger_dir", "workdir", "out"):
        if m.get(k):
            paths[k] = m[k]
    paths.update(m.get("paths") or {})
    # resolve templates in dependency order, then make absolute
    resolved = {}
    for _ in range(4):
        for k, v in paths.items():
            try:
                resolved[k] = str(v).format(**{**paths, **resolved, "group": "{group}", "phase": "{phase}"})
            except KeyError:
                resolved[k] = str(v)
        paths = dict(resolved)
    for k, v in paths.items():
        if "{group}" in v or "{phase}" in v:  # per-group/phase template; leave relative parts intact but anchor
            paths[k] = v if Path(v).is_absolute() else str(root / v)
        else:
            paths[k] = str((root / v).resolve()) if not Path(v).is_absolute() else v
    if mode == "consult":
        boundary = Path(m["consult_root"]) / "_synthesis"
        for name, path in paths.items():
            try:
                Path(path).resolve().relative_to(boundary.resolve())
            except ValueError:
                raise ValueError(f"CONSULT method path {name} must stay under _synthesis: {path}")
    m["paths"] = paths
    for k in ("taxonomy", "registry", "context", "skill", "lint_skill"):
        if m.get(k) and not Path(m[k]).is_absolute():
            m[k] = str((root / m[k]).resolve())

    agents = dict(AGENT_DEFAULTS)
    agents.update(m.get("agents") or {})
    m["agents"] = agents
    for g in m.get("groups", []) + m.get("deferred_groups", []):
        g.setdefault("agent", agents["reader"].format(group=g["id"]))
        g.setdefault("pre_read", [])
        g.setdefault("reference", [])
    m.setdefault("deferred_groups", [])
    return m


def read_rows(ldir, layer):
    """All row versions for a layer, in file order."""
    f = ldir / LAYERS[layer]["file"]
    if not f.exists():
        return []
    rows = []
    with open(f, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def current(ldir, layer, include_retired=False):
    """dict id -> latest version row."""
    latest = {}
    for r in read_rows(ldir, layer):
        if r["id"] not in latest or r["version"] > latest[r["id"]]["version"]:
            latest[r["id"]] = r
    if not include_retired:
        latest = {k: v for k, v in latest.items() if v.get("status") != "retired"}
    return latest


def write_row(ldir, layer, row):
    with open(ldir / LAYERS[layer]["file"], "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def next_id(ldir, layer):
    prefix = LAYERS[layer]["prefix"]
    ids = [r["id"] for r in read_rows(ldir, layer)]
    nums = [int(i.split("-")[1]) for i in ids if re.match(rf"^{prefix}-\d+$", i)]
    return f"{prefix}-{(max(nums) + 1 if nums else 1):03d}"


def coerce(layer, row, partial=False):
    """Normalize list fields and ints. partial=True leaves absent keys absent."""
    for k in SCHEMA[layer]["lists"]:
        v = row.get(k)
        if v is None:
            if not partial:
                row[k] = []
        elif isinstance(v, str):
            row[k] = [s.strip() for s in v.split(";") if s.strip()]
    for k in ("severity", "impact", "effort"):
        if k in row and row[k] is not None and layer != "themes":
            try:
                row[k] = int(row[k])
            except (TypeError, ValueError):
                pass
    return row


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in r) + " |")
    return "\n".join(out)
