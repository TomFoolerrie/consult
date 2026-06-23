# T57 — Fan-out Workflow scaffold (the deterministic per-stage driver)

**Slice 4 (Cost & Runtime Efficiency) · Foundation (build before T55 Phase 2 / T56 budget path) ·
Depends: — · Foundation for T55 + T56 · Touches: `.claude/workflows/consult-fanout.*` (new),
`scripts/orchestrate.py` (read-only `next --json` consumed; no change expected), `tests/`.**

> **Why a separate ticket.** T54 (enforcement) wires `consult-run` to *delegate*; T55 (schema
> emission) and T56 (`budget.spent()` cost map) both *plug into* the workflow. The workflow itself
> is the shared substrate — built once, reviewed once, then T55/T56 attach to its seams. This
> mirrors T40 (the shared IO util) as the Slice-3 foundation.

## Problem

`consult-run`'s fan-out is prose the model can inline (T54). The durable fix is a deterministic
**Workflow** that spawns one worker per target in a JS loop, so the loop-level model never sees
document content and **cannot** inline. That workflow does not yet exist and is the foundation the
rest of Slice 4 needs.

## Build

A committed workflow (`.claude/workflows/consult-fanout.*`, or a script `consult-run` invokes),
**parameterized by stage** via `args` (`{engagement, stage, targets}`). For one `llm_fanout`
action it:

1. Takes the stage's targets (from `orchestrate.py next --json`, passed in by `consult-run`).
2. `pipeline()` / `parallel()` over targets — **one `agent()` per target** — each invoking the
   named worker skill (`consult-classifier` / `consult-consolidator` / `consult-drafter` +
   `consult-improvement-drafter` / `consult-synthesizer`), each fed by its **read-only** input
   gatherer (`consolidate_inputs.py` / `draft_inputs.py` / `synthesis_inputs.py`). The worker
   writes **only its own artifact/deliverable** and **never** state — unchanged contract.
3. For **classify**, runs `classify_merge.py merge` as the post-fan-out `then_script`.
4. Returns per-target one-line summaries + a rollup to `consult-run`, which re-runs
   `orchestrate.py next` and proceeds to the next action / human gate.

**Seams to expose (the whole point of the foundation):**
- **Schema seam (T55):** the classify `agent()` call takes an optional `{schema}` arg, loaded
  from `schemas/classify_artifact.schema.json` — left as a clearly-marked, wired hook so T55
  Phase 2 only flips it on, no re-architecture.
- **Budget seam (T56):** `budget.spent()` snapshot points immediately before/after each stage's
  fan-out (and optionally per `agent()` call), emitting a per-stage Δoutput-tokens line.

**Failure / concurrency / idempotency semantics (specify explicitly):**
- Bounded concurrency (workflow default cap). A worker that skips/dies → `agent()` returns
  `null` → `filter(Boolean)`; **partial completion is safe** because `orchestrate.py` re-derives
  readiness (a doc counts classified only once its artifact exists **and** validates), so a failed
  target simply re-runs on the next `next`. No batch abort.
- The workflow writes **no engagement state** itself — only the workers' artifact/command-path
  writes + the classify `then_script`. Re-running is byte-safe (same guarantees `consult-run`
  already documents).

**Human-in-the-loop guard (hard constraint):** the workflow drives **one fan-out stage**, never
the whole engagement. It does **not** advance past the stage, render, or self-finalize. It returns
control to `consult-run`, which owns the render gate and `status.needs_human` stops.

**Standalone preserved:** worker skills remain directly invokable; the workflow is an
orchestration layer over them, not a rewrite.

## Tests

- **Determinism of dispatch (the core assertion):** a 2-target stage issues **exactly 2**
  `agent()` calls; a 3-target stage issues 3. (Assert call count via a dry-run / mock agent, not
  model discretion — real agents are non-deterministic + costly; prescribe a mock/dry-run mode in
  the harness rather than spending tokens per test run.)
- **classify `then_script`:** runs `classify_merge.py merge` exactly once, **after** the fan-out.
- **Failure isolation:** one target's worker returning `null` does **not** abort the others; the
  rollup reflects the partial set; a re-run picks up the missing target (readiness re-derived).
- **No state leakage:** running the workflow writes no `state.json` / `register.json` beyond what
  the workers + `then_script` write; re-run is byte-identical.
- **Seams present:** the schema hook and budget snapshot points exist and are exercised by T55/T56
  tests (cross-referenced, not duplicated here).

## DoD

- A committed, stage-parameterized fan-out workflow spawns exactly one worker per target,
  deterministically, with bounded concurrency and `null`-tolerant partial completion.
- The classify `then_script` runs once post-fan-out; workers still write only their own output and
  never state.
- The schema seam (T55) and budget seam (T56) are wired and clearly marked.
- Human gates preserved — workflow is per-stage, never whole-engagement.
- Worker skills remain standalone-invokable; `orchestrate.py` action contract unchanged; no scratch
  engagement left behind.
