# T57 — Fan-out Workflow scaffold (the deterministic per-stage driver)

**Slice 4 (Cost & Runtime Efficiency) · Foundation (build before T55 Phase 2 / T56 budget path) ·
Depends: — · Foundation for T55 + T56 · Touches: `.claude/workflows/consult-fanout` (new, committed
named workflow), `.claude/agents/*` (5 new worker agent defs), `scripts/orchestrate.py` (read-only
`next --json` consumed; no change expected), `tests/`.**

> **Why a separate ticket.** T54 (enforcement) wires `consult-run` to *delegate*; T55 (schema
> emission) and T56 (`budget.spent()` cost map) both *plug into* the workflow. Built once, reviewed
> once; T55/T56 attach to its seams. Mirrors T40 as the Slice-3 foundation.

> **Specs LOCKED (build deferred). Two review passes (5-agent first pass + adversarial second pass
> on this ticket).** The second pass killed the original Decision B (JSONL→deferred apply) — it
> broke the consolidator's ID-before-citation contract and misstated its rationale against the T40
> lock. Decision B is replaced below (parallel inline apply under the lock).

## Problem

`consult-run`'s fan-out is prose the model can inline (T54). The durable fix is a deterministic
**Workflow** that spawns one worker per target in a JS loop, so the loop-level model never sees
document content and **cannot** inline. That workflow does not yet exist and is the foundation the
rest of Slice 4 needs.

## The per-stage dispatch model (the stages are NOT uniform — get this right first)

From `orchestrate.py` (`ACTION_DISPATCH` :81-90 + `_action()` targets :222-249):

| stage | target key iterated | agent type(s) per item | agents issued | post-fan-out step |
|---|---|---|---|---|
| classify | `targets.docs` (ingested MDs) | `consult-classifier` | `len(docs)` | `classify_merge.py merge` (workflow supplies the `merge` subcommand) |
| consolidate | `targets.nodes` (dirty nodes) | `consult-consolidator` | `len(nodes)` | **none** — each worker applies its own findings inline (Decision B) |
| draft | `targets.l1s` (**not** nodes) | **two**: `consult-drafter` **and** `consult-improvement-drafter` | **`2 × len(l1s)`** | none |
| synthesize | engagement-scoped (`scope == "engagement"`) | `consult-synthesizer` | **exactly 1** (degenerate, no list) | none |

A build that loops `targets.nodes` for draft, expects one agent for draft, or applies a uniform
`then_script` to every stage is **wrong**. Encode this table.

## Decisions (LOCKED)

- **(A) Skill invocation — custom agent types.** Commit **five** agent definitions under
  `.claude/agents/` (one per worker), each **preloading its skill** (pointer, not a copy — the SKILL
  stays the single source of behaviour) and **tool-scoped** to exactly what that worker runs:

  | agent def | tools it needs |
  |---|---|
  | `consult-classifier` | Read, Write*, Bash(`validate_artifact.py`) — *Write only on the standalone path; on T55's schema path the **workflow** writes the artifact, so the def's Write scope is narrowed there. **T57 ships the def with this (conditional) scope as built; T55 Phase 2 only *uses* the schema path — it does not edit the def.** |
  | `consult-consolidator` | Read, Write (node MD), Bash(`consolidate_inputs.py`, `state_machine.py add-item`/`mark-consolidated`) — **writes state inline**, see Decision B |
  | `consult-drafter` | Read, Write, Bash(`draft_inputs.py`, `state_machine.py set-sop --bump-rev`) |
  | `consult-improvement-drafter` | Read, Write, Bash(`draft_inputs.py`, `state_machine.py set-improvement --bump-rev`) |
  | `consult-synthesizer` | Read, Write, Bash(`synthesis_inputs.py`, `state_machine.py add-item`, `state_machine.py sync`) |

  **Drift guard (stronger than name-matching):** a test asserts (i) the 5 defs name the 5 real
  skills (no orphan/rename); (ii) each def body is **preload-only** (a pointer to its SKILL, no
  inlined/paraphrased procedural prose that could contradict it); (iii) each def's tool-scope
  **covers every `python3 scripts/...` the SKILL body invokes** (greppable) — so a too-narrow scope
  (e.g. classifier missing `validate_artifact.py`) fails the test, not the run.

- **(B) Consolidate apply — parallel, each worker applies inline; the T40 lock guarantees safety.**
  *(Supersedes the killed JSONL→deferred-apply design.)* The consolidate fan-out runs one
  `consult-consolidator` agent per dirty node; **each agent runs the node end-to-end inline**:
  gather (`consolidate_inputs.py`) → decide confirmed findings → `state_machine.py add-item` per
  finding (**mints the `IMP-`/`GAP-` IDs**) → author the node MD **citing those just-minted IDs** →
  `state_machine.py mark-consolidated`. This preserves the consolidator's **ID-before-citation**
  contract (all inline in one agent) — the property the deferred design broke.
  - **Why this is safe in parallel (and why the JSONL indirection was unnecessary):** `add-item`
    already wraps mint→upsert→sync in the **engagement advisory lock** (`state_machine.py:789-816`;
    the comment at :784-788 notes it "closes the concurrent-add-item id race"). Concurrent
    consolidators are therefore **correct**, just serialized on the brief apply. The write-conflict
    the old Decision B claimed to prevent does **not** threaten correctness — it was a phantom. The
    honest cost of parallel apply is minor **lock contention**, not corruption.
  - **Consolidator gains state-write responsibility** (it previously returned findings for the
    orchestrator to apply). This makes it a state-writing worker like drafter/synthesizer —
    consistent, and all via the `state_machine.py` command path (never ad-hoc JSON). The
    `consult-consolidator` SKILL + its agent-def tool-scope are updated to run `add-item`/
    `mark-consolidated` itself.
  - **No** `consolidate_merge.py`, **no** findings JSONL, **no** barrier for this stage.

- **(C) Workflow invocation surface — committed named workflow.** Lives at
  `.claude/workflows/consult-fanout`, invoked **by name** from `consult-run` (T54 Tier 2), with
  `args` `{engagement, stage, targets}` (`consult-run` maps the action's `action` field → `stage`).
  Versioned, reviewable, reusable — not an inline script.

## Concurrency & the CPU-bound observation

The field machine ran **CPU-bound**. Two consequences baked in here:
- **Concurrency is a tunable knob, defaulted conservatively.** The workflow cap is
  `min(16, cores−2)`; this ticket sets the fan-out concurrency **lower than the cap by default** so
  isolation benefits land without saturating a constrained machine. Expose it as one constant.
- **Hypothesis (confirm via T56, not asserted):** the slowdown is plausibly the *same* context
  bloat as the $10 — one giant orchestrator context re-processed every turn. If so, fan-out into
  isolated sub-agent contexts **reduces** the orchestrator's local context and should *help*
  responsiveness, not just cost. T56's per-phase map is how we'd confirm where the CPU actually goes.

## Build

A committed **named** workflow at `.claude/workflows/consult-fanout` (Decision C). For one
`llm_fanout` action it:

1. Reads the stage row from the table to pick the **target key** and **agent type(s)**.
2. `pipeline()` / `parallel()` over the iterated targets (at the conservative default concurrency)
   — issuing the per-stage agent count above — each `agent()` using the stage's **custom agent
   type** (Decision A), fed (where applicable) by its **read-only** input gatherer. **Classify has
   no gatherer** — the classifier reads the ingested MD + a taxonomy slice directly.
3. Runs the per-stage **post step**: classify → `classify_merge.py merge`; consolidate / draft /
   synthesize → none (consolidate applies inline per Decision B).
4. Returns per-target one-line summaries + a rollup to `consult-run`, which re-runs
   `orchestrate.py next` and proceeds to the next action / human gate.

**Worker state-write contract (per-worker — do NOT overgeneralize):**
- `consult-classifier` — writes **only** its artifact; never state.
- `consult-consolidator` — **writes state inline** (`add-item`/`mark-consolidated`) + the node MD,
  per Decision B; lock-serialized.
- `consult-drafter` / `consult-improvement-drafter` — write state (`set-sop`/`set-improvement
  --bump-rev`); partitioned per-L1 (no cross-L1 contention).
- `consult-synthesizer` — writes state (`add-item` + `sync`); single engagement-level agent.

The real invariant: **all state mutation goes through `state_machine.py`** (never ad-hoc JSON), and
**concurrent writers are made safe by the T40 engagement lock** (consolidate), or partitioned
(draft per-L1), or single (synthesize). Only classify writes no state at all.

**Seams to expose:**
- **Schema seam (T55):** the classify `agent()` (agent type `consult-classifier`) takes an optional
  `{schema}` loaded from `schemas/classify_artifact.schema.json`; on the schema path the **workflow**
  writes the validated object atomically (`temp + os.rename`) to `classify/{hash}.artifact.json`.
  (Reconciles T55 Phase 2's "Write owner" bullet.)
- **Budget seam (T56):** `budget.spent()` snapshots before/after each stage's fan-out; persist the
  rollup to a **content-free** `cost_map.json` (measured tokens are otherwise ephemeral).

**Failure / idempotency:** bounded concurrency; a worker that skips/dies → `agent()` returns `null`
→ `filter(Boolean)`. Partial completion is safe — `orchestrate.py` re-derives readiness each `next`
(classify: doc classified only once artifact exists **and** validates; **consolidate: a node whose
worker died never gets `mark-consolidated`, so it stays diagnosis-dirty (`last_evidence_at >
consolidated_at`) and re-fans next `next`** — and because that node's apply is inline, a failure
leaves it cleanly un-consolidated, not half-applied; draft: node draftable while its block is
`not_started`). classify `merge` is idempotent over on-disk artifacts (standalone `merge` action is
the safety net).

**Human-in-the-loop guard (hard constraint, testable):** the workflow drives **one fan-out stage**
and returns. It **MUST NOT** call `orchestrate.py next`, `render_deliverables.py`, or any
`final`/finalize path. That structural absence keeps the render gate + `status.needs_human` stops
owned by `consult-run`.

## Tests

- **Per-stage dispatch count (use the table):** classify/2 docs → **2**; consolidate/3 nodes → **3**;
  **draft/2 L1s → 4**; synthesize → **1**. Assert via a dry-run / mock agent (no real-token spend).
- **Agent-def drift (Decision A):** the 3-part guard above — names match, preload-only, tool-scope
  covers every script each SKILL invokes.
- **classify post-step:** `classify_merge.py merge` runs once, after fan-out; partial fan-out merges
  only on-disk artifacts.
- **consolidate inline apply (Decision B):** each consolidator mints its IDs and authors an MD that
  cites **existing** IDs (ID-before-citation holds); the `validate` coherence check passes (no
  invented IDs, no restated data). A failed node is left un-consolidated (stays dirty), never
  half-applied.
- **Parallel-apply safety:** running consolidate concurrently produces a correct register (no lost
  IDs / no dup `IMP-` numbers) — the T40 lock serializes the mints. Assert the register is
  well-formed after a concurrent run.
- **State writes via `state_machine.py` only:** consolidate/draft/synth mutations all use the
  command path; **do not** assert "zero state writes" (false for 4 of 5 workers).
- **Human-gate guard:** the workflow issues **no** `next` / `render` / `final` call (structural).
  The mock harness **exposes this assertion** so **T58 can reuse it** to prove the run halts where a
  human is owed (not just dispatch counts).
- **Seams present:** schema hook + budget snapshot + `cost_map.json` exist (exercised by T55/T56).

## DoD

- A committed **named** workflow (`.claude/workflows/consult-fanout`, Decision C) issues the correct
  per-stage agent count (classify=#docs, consolidate=#nodes, draft=2×#L1s, synthesize=1),
  deterministically, with **conservative default concurrency** and `null`-tolerant partial
  completion.
- Five `.claude/agents/` worker defs exist, each preloading its skill and tool-scoped (Decision A);
  the 3-part drift test is green.
- Classify runs `merge` post-fan-out; **consolidate applies inline (mint→cite→mark) under the T40
  lock** (Decision B) — ID-before-citation preserved, no concurrent-write corruption, no silent
  no-op; draft/synthesize have no post-step.
- All state mutation goes through `state_machine.py`; concurrent writers are lock-safe / partitioned
  / single.
- Schema seam (T55) + budget seam (T56, persisted to content-free `cost_map.json`) wired and marked.
- Human gates preserved structurally — workflow makes no `next`/`render`/`final` call.
- Worker skills remain standalone-invokable; `orchestrate.py` action contract unchanged; no scratch
  engagement left behind.
