#!/usr/bin/env python3
"""test_agent_def_drift.py — T57 Part 1 Decision-A drift guard (3-part).

The five .claude/agents/ worker defs must not drift from the five real worker
skills. This test asserts the stronger guard from T57 Decision A:

  (i)  names    — the 5 defs' `name`s exactly match the 5 real skill dirs (no
                  orphan, no rename).
  (ii) preload  — each def body is a POINTER to its SKILL (references the
                  skills/<x>/SKILL.md path) and does NOT inline procedural prose
                  (no copied numbered steps), so the SKILL stays the single
                  source of behaviour.
  (iii) tool-scope — each def's `tools` covers every `python3 scripts/<x>.py`
                  (and any other `python3 .../<x>.py`) its SKILL.md invokes; a
                  too-narrow scope fails here, not at run time.

No real LLM agent is spawned; this is pure static analysis of the def + SKILL
files. Exit 0 / "PASS" on success, nonzero / "FAIL" on any drift.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
SKILLS_DIR = REPO_ROOT / "skills"

WORKERS = [
    "consult-classifier",
    "consult-consolidator",
    "consult-drafter",
    "consult-improvement-drafter",
    "consult-synthesizer",
]

# Any `python3 <path>/<name>.py <subcommand?>` invocation in a SKILL body.
SCRIPT_CALL_RE = re.compile(
    r"python3\s+(?P<path>[\w./-]+\.py)(?:\s+(?P<sub>[a-z][a-z0-9-]*))?",
)

failures: list[str] = []


def fail(msg: str) -> None:
    failures.append(msg)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Return ({name,description,tools}, body) for a def markdown file."""
    if not text.startswith("---"):
        raise ValueError("no YAML frontmatter")
    end = text.index("\n---", 3)
    fm_block = text[3:end].strip("\n")
    body = text[end + 4:]
    fm: dict = {}
    for line in fm_block.splitlines():
        if ":" in line and not line.startswith((" ", "\t", "#")):
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


def tools_permits(tools_field: str, path: str, sub: str | None) -> bool:
    """Does the def's `tools` scope permit `python3 <path> <sub>`?

    A def grants e.g. `Bash(python3 scripts/state_machine.py add-item:*)`. We
    accept the call if some Bash(...) entry's `python3 <path>` prefix matches and
    (when the entry pins a subcommand) the subcommand matches.
    """
    for m in re.finditer(r"Bash\((?P<spec>[^)]*)\)", tools_field):
        spec = m.group("spec").strip()
        # strip a trailing :* glob
        spec_core = spec[:-2] if spec.endswith(":*") else spec
        bm = re.match(r"python3\s+(?P<bpath>[\w./-]+\.py)(?:\s+(?P<bsub>[a-z][a-z0-9-]*))?", spec_core)
        if not bm:
            continue
        if bm.group("bpath") != path:
            continue
        bsub = bm.group("bsub")
        if bsub is None:
            return True  # whole-script scope covers any subcommand
        if sub is not None and bsub == sub:
            return True
    return False


def main() -> int:
    # ---- (i) names ----------------------------------------------------------
    real_skills = {
        d.name for d in SKILLS_DIR.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists() and d.name in WORKERS
    }
    if real_skills != set(WORKERS):
        fail(f"(i) worker skill dirs {sorted(real_skills)} != expected {WORKERS}")

    def_files = sorted(AGENTS_DIR.glob("*.md")) if AGENTS_DIR.is_dir() else []
    def_names = set()
    for df in def_files:
        try:
            fm, _ = parse_frontmatter(df.read_text(encoding="utf-8"))
        except ValueError as e:
            fail(f"(i) {df.name}: {e}")
            continue
        def_names.add(fm.get("name", ""))

    missing = set(WORKERS) - def_names
    orphan = def_names - set(WORKERS)
    if missing:
        fail(f"(i) missing agent defs for: {sorted(missing)}")
    if orphan:
        fail(f"(i) orphan/renamed agent defs (no matching skill): {sorted(orphan)}")

    # ---- per-worker (ii) + (iii) -------------------------------------------
    for worker in WORKERS:
        def_path = AGENTS_DIR / f"{worker}.md"
        skill_path = SKILLS_DIR / worker / "SKILL.md"
        if not def_path.exists():
            fail(f"(ii/iii) {worker}: agent def missing at {def_path}")
            continue
        if not skill_path.exists():
            fail(f"(ii/iii) {worker}: SKILL missing at {skill_path}")
            continue

        fm, body = parse_frontmatter(def_path.read_text(encoding="utf-8"))
        skill_text = skill_path.read_text(encoding="utf-8")

        # (ii) preload-only: references its SKILL path...
        skill_ref = f"skills/{worker}/SKILL.md"
        if skill_ref not in body:
            fail(f"(ii) {worker}: def body does not point at {skill_ref}")
        # ...and is short (a pointer, not a copied procedure).
        nonblank = [ln for ln in body.splitlines() if ln.strip()]
        if len(nonblank) > 25:
            fail(f"(ii) {worker}: def body too long ({len(nonblank)} non-blank "
                 f"lines) — looks like inlined procedure, not a pointer")
        # ...and does NOT inline procedural prose (copied numbered steps /
        # SKILL section headers).
        if re.search(r"(?m)^\s*(Step\s+\d|####\s+Step|###\s+Step)", body):
            fail(f"(ii) {worker}: def body contains inlined numbered Step prose")
        if re.search(r"(?m)^\s*\d+\.\s+\*\*", body):
            fail(f"(ii) {worker}: def body contains an inlined numbered procedure list")

        # (iii) tool-scope covers every python3 script call in the SKILL body.
        tools_field = fm.get("tools", "")
        seen: set[tuple[str, str | None]] = set()
        for m in SCRIPT_CALL_RE.finditer(skill_text):
            path = m.group("path")
            sub = m.group("sub")
            # state_machine.py is always invoked with a subcommand; treat the
            # captured token as the subcommand. Read-only gatherers (gather) are
            # also subcommands but live under their own script path.
            key = (path, sub)
            if key in seen:
                continue
            seen.add(key)
            if not tools_permits(tools_field, path, sub):
                fail(f"(iii) {worker}: SKILL invokes `python3 {path}"
                     f"{(' ' + sub) if sub else ''}` but def tools-scope does not "
                     f"permit it. tools={tools_field!r}")

    if failures:
        print("FAIL — agent-def drift test")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"PASS — agent-def drift test ({len(WORKERS)} workers, 3 parts: "
          f"names, preload-only, tool-scope)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
