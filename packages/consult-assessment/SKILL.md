---
name: consult-assessment
description: Runs the consulting "assessment" workflow on registered client documents - a findings ledger built by reader agents, then themes, recommendations, initiatives, and a story layered on top, with deterministic figure specs for the deck. Use whenever an engagement needs findings logged from interviews, org charts, or artifacts, a themes/root-cause analysis, a readiness or coverage heat map, prioritized initiatives, or an assessment deck narrative - even if the user just says "log findings", "build the themes", or "what did we find". Consumes discovery-output (consult-lint registry) and context-profile; produces assessment-output. Orchestrator-driven - the orchestrator names paths and agents, groups sources, and loops on run.py next; this skill owns the ledger, the taxonomy format, and the per-layer prompts.
---

# consult-assessment

## Host mode — read first

This tracked copy supports explicit CONSULT integration for **text and CSV evidence**.
When used inside a CONSULT engagement, read `INTEGRATION.md` first and use a
manifest with `mode: consult`. The generated shim routes citation checks and
versioned analysis registration through CONSULT; do not create a consult-lint
registry. Integrated CSV citations use data-record locators (`SRC-nnn:R7`),
not physical lines. Other table formats are refused, never silently handled by
standalone registration. The standalone instructions below apply outside
integrated mode.

## When invoked — do this

You are the orchestrator for this run (unless the user says another agent is). From the engagement's root directory:

1. `python3 <this skill>/scripts/run.py next --root .` — no manifest needed. It inspects the repo and prints exactly one line: `[RUN] <command>`, `[HUMAN] <what to ask for and how to record the answer>`, or `[DONE]`.
2. Do that one thing. `[RUN]` lines are commands or "render then spawn" instructions; for spawning, follow the spawn boundary in `references/runbook.md` (Agent tool with the rendered brief as `prompt`). `[HUMAN]` lines mean stop, hand the user exactly what is named, and wait; record their answer with `run.py gate` when it says so.
3. Call `next` again. Repeat until `[DONE]`.

In Claude Code, run `run.py agents --out <plugin or .claude>/agents --with-orchestrator` once so the `assess-*` subagents exist before the first spawn. Never write ledger files directly, never edit rows to satisfy a gate, never skip a `[HUMAN]` line. Everything below is context for judgment calls; the loop is the procedure.

## What this is

Findings are the source of truth. Everything above them is derived, cites the layer below by id, and can be regenerated. The deck's visuals are queries over the ledgers, not authored.

```
registered sources (src-NNN:Lnn) ─┐
context-profile ──────────────────┼─▶ findings ─▶ themes ─▶ recommendations ─▶ initiatives ─▶ story
taxonomy (the knowledge model) ───┘        │                                                   │
                                           └───────────── figures (render.py) ─────────────────┘
```

## Who owns what

**The orchestrator (its house):** every path and name outside the ledger dir (`paths:` and `agents:` in the manifest), how sources are grouped and what each reader pre-reads, when to spawn, when to checkpoint, the story framing. It drives the whole run with one loop — `run.py next` — and starts agents from the prompt files `run.py render` writes. See `references/runbook.md`.

**The taxonomy (the house's knowledge):** the axes a finding is classified by, which axis themes carry as the diagnosis, the scales, and which axes get plotted against which. Nothing in the scripts or prompts knows an axis by name; validation, tables, figure specs, and the examples in the prompts are generated from it. The shipped default is pre-audit readiness; `tests/fixture/taxonomy-itgc.yaml` shows a different engagement type on the same scripts. See `references/taxonomy.md`.

**This skill (the method):** the ledger format and its only writer, author ownership, the layer-below citation rule, gates, the six agents (static prompt + per-run brief), the figure engine and method figures. These don't bend per engagement.

## Ops

| op | prompt | agent | writes |
|---|---|---|---|
| extract | `reader.md` (mode=read) | one per group | findings |
| normalize | `normalize.md` | one | proposals only |
| revise | `reader.md` (mode=edit) | the original reader | its own findings; resolves proposals |
| themes | `themes.md` | one | themes |
| recommend | `recommend.md` | one | recommendations |
| plan | `plan.md` | one | initiatives |
| story | `story.md` | one | the story file |
| digest | `digest.md` | one, once | compact context digest readers load instead of raw pre-reads |
| retro | `retro.md` | one per phase | post-phase report: bugs, efficiency, quality, coverage, notes |

Readers extract blind, then — if the group declares `builds_on:` — situate against a compact index of earlier groups' findings: link, corroborate, contradict, answer open questions. `next` spawns groups in dependency waves. See `references/manifest.md`.

Readers are analysts for tabular sources: `data profile` and `data run <procedure>` (via the shim) with a playbook mapping dataset kinds to procedures; outputs are registered as citable sources with provenance. See `references/data-playbook.md`.

Each prompt is split: `prompts/<op>.md` is the static system prompt, `prompts/<op>.brief.md` the per-run template. `run.py agents` packages the static halves as Claude Code subagents (frontmatter: name, description, tools, model) for the plugin or `.claude/agents/`; `run.py render --format brief` writes the per-run brief the orchestrator passes as the task message. `run.py render` alone writes both halves as one self-contained file for any other harness.

Around them: `run.py next` (what to do), `run.py check` (validate + trace), `run.py gate` (record a human decision), `ledger.py checkpoint` (git commit after every op that wrote), `render.py tables|figures|bundle`.

Sequence, in short: init → extract one group → **human reviews findings** → extract the rest → normalize → revise → **human second look** → themes → recommend → plan → render → story → bundle. Full detail, gates, and rollback: `references/runbook.md`.

## Invariants the tools enforce

- Ledgers live in git. `init` refuses a dir outside a repo; every write refuses a dir `init` didn't mark, so a mistyped path fails instead of starting a second ledger.
- A finding with no source is refused. With `--registry`, cited ids must be active, the file unchanged since registration, and cited lines within the file.
- Themes cite findings; recommendations cite themes (optionally findings); initiatives cite recommendations. Never a raw source above findings.
- Only the author can `edit`, `retire`, or `merge`; anyone can `propose`. Author = the agent name in the manifest, so a re-spawned reader keeps ownership.
- `merge` is refused across authors and across evidence bases; cross-group duplicates are **linked**, both rows survive, the theme binds them.
- Values on `on_theme` axes are provisional on a finding; the theme's value is the diagnosis. Figures count themes for "how many problems", findings for "how much evidence", and say which.
- No layer builds on open proposals against a lower layer (`--gate`).
- Every write appends a new version; history is never rewritten. Writes take a file lock, so parallel readers never collide on ids.

## Scripts

```
python3 scripts/run.py      next|render|check|gate|status --manifest M
python3 scripts/run.py      agents --out <plugin>/agents [--prefix assess-] [--model inherit] [--with-orchestrator]
python3 scripts/ledger.py   --ledger-dir D [--taxonomy T]  init|checkpoint|append|edit|retire|merge|propose|resolve|show|next-id
python3 scripts/validate.py --ledger-dir D --taxonomy T [--registry R] [--gate LAYER]
python3 scripts/trace.py    --ledger-dir D [--json]
python3 scripts/render.py   tables|figures|bundle --manifest M
python3 scripts/manifest.py draft --registry R --out M [--ledger-dir --workdir --out-dir] [--all-groups]
python3 scripts/data.py     --registry R --analysis-dir A  profile|run|procedures   # normally via the shim: assess.py data ...
```
Python 3.9+ and `pyyaml`. `ASSESS_LEDGER_DIR` / `ASSESS_TAXONOMY` can replace the flags. Both smoke tests (`tests/smoke.sh`, `tests/smoke-house.sh`) should pass after any change to scripts or taxonomy format.

## References

- `runbook.md` — the orchestrator's loop, gates, rollback. **Start here to run an engagement.**
- `review-rubric.md` — what the human checks at the findings gate
- `manifest.md` — what the orchestrator writes: paths, agents, groups
- `taxonomy.md` — how to declare a knowledge model: axes, scales, figures
- `ledgers.md` — row schema, ownership, merge vs link
- `figures.md` — house and method figures, units
- `story-template.md` — narrative skeleton
- `data-playbook.md` — which procedures for which dataset; how to write a data finding
- `../CHANGELOG.md` — what changed per drop and what the orchestrator must do differently
