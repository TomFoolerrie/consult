# T54 — Orchestrator delegation enforcement (stop inline self-execution)

**Slice 4 (Cost & Runtime Efficiency) · Follow-up · From field run (3 real artifacts, ~$10) ·
Depends: T57 (the fan-out workflow Tier 2 invokes) · Keystone-pair with T57 for T55 + T56 ·
Touches: `skills/consult-run/SKILL.md`, dispatch contract docs. (The workflow itself is built in
**T57**; this ticket wires `consult-run` to invoke it.)**

> **Runtime confirmed (was an open fork; now resolved).** The engagement runs in **Claude Code
> hosted in the Claude Desktop app** — which **has** sub-agents (the Agent/Task primitive), skills
> callable inside sub-agents, and the **Workflow** tool. The earlier "branch B: Desktop has no
> sub-agents" is **dead** — delete it from your mental model. Inlining was **instruction drift**,
> not a missing substrate.

> **Field observation (load-bearing).** On a real 3-artifact run the orchestrator did the fan-out
> work itself — classify/consolidate/draft inline instead of dispatching to the sub-agent skills.
> ~$10 for three artifacts. Suspected dominant cost driver (T56 will confirm).

## Problem

`consult-run` is **prose** describing a dispatch loop ("if `kind == llm_fanout`, spawn the named
sub-agent once per target"). Nothing **structurally** forces delegation, so on small batches the
model inlines the work. Cost consequence, compounding:

1. **Context bloat, re-billed every turn.** Every stage's full inputs (ingested MD, taxonomy
   slice, per-doc reasoning) pile into the **single** orchestrator context instead of isolated
   sub-agent contexts returning a one-liner. Later stages re-read the bloat. Cost scales with
   accumulated context, not work done.
2. **No isolation / no parallelism** — the entire point of the fan-out architecture is defeated.
3. **Silent correctness drift** — an inline classifier skips the per-doc artifact schema +
   `validate_artifact.py` gate a real `consult-classifier` sub-agent must pass.

## Decision (recorded)

Two tiers; **Tier 2 is the durable fix and the keystone that also unlocks T55/T56.**

- **Tier 1 — prose hardening + content-starvation (cheap stopgap, do regardless).** Make
  `consult-run` dispatch **imperative + blocking**, and forbid the orchestrator from reading
  content itself. Weaker (adherence-dependent) but a one-skill change with immediate effect.
- **Tier 2 — deterministic Workflow fan-out (the real fix — chosen as the target).** Replace
  "spawn N sub-agents via prose" for each `llm_fanout` stage with a committed **Workflow** the
  orchestrator invokes. The workflow loops `agent()` per target in a JS driver — delegation is
  **structural**: the loop-level model never sees document content, so it **cannot** inline. This
  is what makes T55 (schema-validated emission) and T56 (`budget.spent()` per-phase cost) possible.
- **Scope guard (important):** the Workflow drives **one fan-out stage at a time** (classify the
  N docs / consolidate the N nodes / draft the N L1s), **not** the whole engagement. CONSULT is
  human-in-the-loop — the render gate is a deliberate hand-off. A whole-engagement workflow would
  blow past the gates and the `status.needs_human` stops. `consult-run` stays the interactive,
  gate-respecting orchestrator; it merely delegates each fan-out *action* to a sub-workflow.

## Build

**Tier 1 (always):**
- Rewrite the dispatch section of `consult-run` from descriptive to **imperative + blocking**:
  for `kind == llm_fanout` the orchestrator **MUST** delegate; performing classify / consolidate
  / draft / synthesize reasoning itself is a **contract violation**, not a shortcut for small
  batches. State the *reason* (context isolation / cost) so it isn't "optimized" away.
- **Content-starvation:** forbid the orchestrator from reading `ingested/*.md`, taxonomy slices,
  or calling the input-gatherers (`consolidate_inputs.py`, `draft_inputs.py`,
  `synthesis_inputs.py`) **itself** — those feed the delegated workers. Starved of content, it
  cannot inline. It handles only `orchestrate.py next` output (`{action, kind, targets}`) + the
  workers' one-line summaries.

**Tier 2 (the keystone — wiring; the workflow is built in T57):**
- Wire `consult-run` so that for each `llm_fanout` action it **invokes the deterministic fan-out
  workflow (T57)** with `{engagement, stage, targets}` from `orchestrate.py next --json`, instead
  of hand-spawning N sub-agents via prose. The workflow returns per-target one-line summaries;
  `consult-run` then re-runs `orchestrate.py next` and proceeds to the next action / human gate.
- `consult-run` remains the **interactive, gate-respecting** layer: it owns the render gate and the
  `status.needs_human` stops; the workflow only handles the bounded per-stage fan-out (see T57's
  human-in-the-loop guard). `orchestrate.py` stays read-only; the action contract (`kind`,
  `targets`) is unchanged — this ticket changes *how the orchestrator obeys the tags*, not the tags.
- The workflow exposes the seams **T55** (classify `agent({schema})`) and **T56**
  (`budget.spent()` per-stage snapshot) plug into — built in T57, switched on by T55/T56.

## Tests

- `orchestrate.py next --json` still emits `kind` + `targets` per stage (dispatch contract intact)
  — exercise via the Slice-1 e2e fixture.
- Grep/lint: `consult-run` no longer instructs the orchestrator to read `ingested/*.md` or invoke
  the gatherers directly; the blocking-delegation language is present.
- **Delegation wiring (Tier 2):** for an `llm_fanout` action, `consult-run` invokes the T57
  workflow (with the action's `targets`) rather than reading content itself. (The per-target
  `agent()` call-count assertion lives in T57.)
- **Manual re-measure (real acceptance, via T56):** re-run the 3-artifact engagement; record per
  stage whether it dispatched, and total cost vs the ~$10 baseline. **Counts + cost only, no
  client content.**

## DoD

- Tier 1 shipped: `consult-run` dispatch is blocking + content-starved.
- Tier 2 shipped: `consult-run` delegates each `llm_fanout` stage to the deterministic T57
  workflow; the orchestrator can no longer perform fan-out work in its own context.
- Human gates (render, `needs_human`) are preserved — the workflow is per-stage, never
  whole-engagement.
- `orchestrate.py` action contract unchanged; Slice-1 e2e green.
- A re-run shows intended dispatch + a recorded cost delta vs ~$10 (acceptance measured by T56).
