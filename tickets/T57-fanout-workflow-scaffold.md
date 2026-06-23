# T57 — Fan-out Workflow scaffold (the deterministic per-stage driver)

**Slice 4 (Cost & Runtime Efficiency) · Foundation (build before T55 Phase 2 / T56 budget path) ·
Depends: — · Foundation for T55 + T56 · Touches: `.claude/workflows/consult-fanout` (new, committed
named workflow), `.claude/agents/*` (5 new worker agent defs), `scripts/consolidate_merge.py` (new,
or an equivalent serial apply step), `scripts/orchestrate.py` (read-only `next --json` consumed; no
change expected), `tests/`.**

> **Why a separate ticket.** T54 (enforcement) wires `consult-run` to *delegate*; T55 (schema
> emission) and T56 (`budget.spent()` cost map) both *plug into* the workflow. The workflow itself
> is the shared substrate — built once, reviewed once, then T55/T56 attach to its seams. This
> mirrors T40 (the shared IO util) as the Slice-3 foundation.

> **Specs LOCKED (build deferred by decision).** The four open forks are decided below (Decisions
> A–D). No implementation until the engagement owner says go.

## Problem

`consult-run`'s fan-out is prose the model can inline (T54). The durable fix is a deterministic
**Workflow** that spawns one worker per target in a JS loop, so the loop-level model never sees
document content and **cannot** inline. That workflow does not yet exist and is the foundation the
rest of Slice 4 needs.

## The per-stage dispatch model (the stages are NOT uniform — get this right first)

Each `llm_fanout` stage has a **different target key, worker count, and post-step**. From
`orchestrate.py` (`ACTION_DISPATCH` + `_action()` targets):

| stage | target key iterated | agent type(s) per item | agents issued | post-fan-out step |
|---|---|---|---|---|
| classify | `targets.docs` (ingested MDs) | `consult-classifier` | `len(docs)` | `classify_merge.py merge` (workflow supplies the `merge` subcommand) |
| consolidate | `targets.nodes` (dirty nodes) | `consult-consolidator` | `len(nodes)` | **deterministic serial apply** of per-node findings (Decision B) — a **barrier** stage |
| draft | `targets.l1s` (**not** nodes) | **two**: `consult-drafter` **and** `consult-improvement-drafter` | **`2 × len(l1s)`** | none |
| synthesize | engagement-scoped (`scope == "engagement"`) | `consult-synthesizer` | **exactly 1** (degenerate, no list) | none |

A build that loops `targets.nodes` for draft, expects one agent for draft, or applies a uniform
`then_script` to every stage is **wrong**. Encode this table.

## Decisions (LOCKED)

- **(A) Skill invocation — custom agent types.** Commit **five** agent definitions under
  `.claude/agents/` (one per worker: `consult-classifier`, `consult-consolidator`,
  `consult-drafter`, `consult-improvement-drafter`, `consult-synthesizer`), each **preloading its
  skill** and scoped to only the tools that worker needs. Each per-item `agent()` call sets
  `agentType` to the matching definition (plus the target id + the gatherer command where the stage
  has one). The agent def **preloads the SKILL** — it does not copy its logic — so the skills stay
  the single source of behaviour. **Drift guard:** a test asserts the five defs name the five real
  skills (no orphan/renamed skill).

- **(B) Consolidate apply-path — parallel emit to per-node files, deterministic serial apply
  (mirrors classify).** Concurrent consolidators must **not** each call the mutating command path
  on shared `register.json` / `state.json` — even under the engagement advisory lock that
  serializes-with-contention and invites conflicts. Generalize the classify pattern instead:
  - **During fan-out** each consolidator writes its node's confirmed findings to its **own per-node
    JSONL file** (append-only, no shared-state write → fully parallel, conflict-free), alongside the
    node MD it already authors.
  - **After the barrier** a single **deterministic** apply step folds all findings into state
    serially via the command path (`add-item` + `mark-consolidated`), once, under one lock.
  This preserves fan-out parallelism **and** removes the write-conflict a parallel apply would
  cause. Implement the apply step as a `classify_merge`-style deterministic merge
  (`scripts/consolidate_merge.py`, or a serial command-path loop the workflow runs). **NB:**
  consolidate is therefore a **barrier** stage (parallel emit → serial apply), like classify.

- **(C) Workflow invocation surface — committed named workflow.** The workflow lives in the repo at
  `.claude/workflows/consult-fanout` and is invoked **by name** from `consult-run` (T54 Tier 2),
  parameterized by `args` (`{engagement, stage, targets}`; `consult-run` maps the action's `action`
  field → `stage`). Versioned, reviewable, reusable across sessions — not an inline script.

- **(D) JSONL as the conflict-free parallel-emit transport.** Per-worker emit files (classify
  artifacts; the new per-node consolidate findings) are the parallelism/conflict boundary: workers
  emit, a deterministic step applies. Use **JSONL** for the consolidate findings (one finding per
  line — append-friendly, per-line fault isolation, easy serial apply), consistent with the T55
  emit-efficiency direction. (Classify keeps its existing per-doc artifact shape; T55 governs its
  schema.)

## Build

A committed **named** workflow at `.claude/workflows/consult-fanout` (Decision C). For one
`llm_fanout` action it:

1. Reads the stage row from the table above to pick the **target key** and **agent type(s)**.
2. `pipeline()` / `parallel()` over the iterated targets — issuing the per-stage agent count above —
   each `agent()` using the stage's **custom agent type** (Decision A), fed (where applicable) by
   its **read-only** input gatherer: `consolidate_inputs.py` / `draft_inputs.py` /
   `synthesis_inputs.py`. **Classify has no gatherer** — the classifier reads the ingested MD + a
   taxonomy slice directly, so its prompt assembles those itself.
3. Runs the per-stage **post step**: classify → `classify_merge.py merge`; consolidate → the
   barrier + deterministic serial apply (Decision B); draft / synthesize → none.
4. Returns per-target one-line summaries + a rollup to `consult-run`, which re-runs
   `orchestrate.py next` and proceeds to the next action / human gate.

**Worker state-write contract (correct, per-worker — do NOT overgeneralize):**
- `consult-classifier` — writes **only** its artifact `classify/{hash}.artifact.json`; never state.
- `consult-consolidator` — writes **no** state during fan-out; emits per-node findings JSONL + the
  node MD. State is touched only by the post-barrier serial apply step (Decision B).
- `consult-drafter` / `consult-improvement-drafter` — **DO** write state: `state_machine.py
  set-sop` / `set-improvement … --bump-rev`. Expected and correct (per-L1 deliverables; no shared
  contention across distinct L1s).
- `consult-synthesizer` — **DOES** write state: `state_machine.py add-item` + `sync` (single
  engagement-level agent, so no concurrent-writer conflict).

The real invariant: **all state mutation goes through `state_machine.py`** (never ad-hoc JSON),
and **no two concurrent agents write shared state** — classify and consolidate defer to a
deterministic serial step; draft writes are partitioned per-L1; synthesize is a single agent.

**Seams to expose (the whole point of the foundation):**
- **Schema seam (T55):** the classify `agent()` call (agent type `consult-classifier`) takes an
  optional `{schema}` arg loaded from `schemas/classify_artifact.schema.json`. On the schema path
  the **workflow** writes the validated returned object atomically (`temp + os.rename`) to
  `classify/{hash}.artifact.json`. Left as a clearly-marked, wired hook so T55 Phase 2 only flips
  it on. (Reconciles T55 §G4: workflow owns the artifact write on the schema path.)
- **Budget seam (T56):** `budget.spent()` snapshots immediately before/after each stage's fan-out
  (and optionally per `agent()` call); persist the rollup to a **content-free** `cost_map.json` so
  T56's reporter can read it (the measured tokens are otherwise ephemeral).

**Failure / concurrency / idempotency semantics:**
- Bounded concurrency (workflow default cap). A worker that skips/dies → `agent()` returns `null`
  → `filter(Boolean)`; **partial completion is safe** because `orchestrate.py` re-derives readiness
  every `next` call (classify: a doc is classified only once its artifact exists **and** validates;
  draft: a node is draftable while its `sop`/`improvement` block is `not_started`), so a failed
  target simply re-runs. No batch abort.
- **classify post-step** is idempotent over on-disk artifacts; the standalone deterministic `merge`
  **action** (re-fires while there is unmerged evidence) is the safety net. **consolidate apply**
  runs only over findings JSONL that landed; a node whose consolidator failed has no findings file,
  stays diagnosis-dirty, and re-runs next `next`. No race.

**Human-in-the-loop guard (hard constraint, testable):** the workflow drives **one fan-out stage**
and returns. It **MUST NOT** call `orchestrate.py next`, `render_deliverables.py`, or any
`final`/finalize path — it has no loop over `next`. That structural absence keeps the render gate
and `status.needs_human` stops owned by `consult-run`.

**Standalone preserved:** worker skills remain directly invokable; the agent defs preload them, and
the workflow is an orchestration layer, not a rewrite.

## Tests

- **Per-stage dispatch count (the core assertion — use the table):** classify with 2 docs → **2**
  agents; consolidate with 3 nodes → **3**; **draft with 2 L1s → 4**; synthesize → **1**. Assert via
  a dry-run / mock agent (real agents are non-deterministic + costly — prescribe a mock mode).
- **Agent-def drift (Decision A):** the five `.claude/agents/` defs name the five real skills; no
  orphan or renamed skill.
- **classify post-step:** `classify_merge.py merge` runs once, **after** the fan-out; partial
  fan-out merges only on-disk artifacts.
- **consolidate emit→apply (Decision B):** N consolidators write N per-node findings JSONL files
  with **no shared-state write during fan-out** (assert `register.json` unchanged mid-fan-out);
  the post-barrier serial apply then adds the register rows and marks nodes consolidated. A missing
  findings file (failed worker) leaves that node dirty, not half-applied.
- **Concurrency-conflict guard:** running the consolidate fan-out concurrently produces no
  interleaved `register.json` writes (the whole point of Decision B) — assertable because no agent
  touches state during fan-out.
- **State writes via `state_machine.py` only:** draft/synth mutations + the consolidate apply step
  all use the command path; **do not** assert "zero state writes" (false for draft/synth).
- **Human-gate guard:** the workflow issues **no** `orchestrate.py next` / `render` / `final` call
  (structural, via the mock harness).
- **Seams present:** schema hook + budget snapshot + `cost_map.json` exist (exercised by T55/T56).

## DoD

- A committed **named** workflow (`.claude/workflows/consult-fanout`, Decision C) issues the correct
  per-stage agent count (classify=#docs, consolidate=#nodes, draft=2×#L1s, synthesize=1),
  deterministically, with bounded concurrency and `null`-tolerant partial completion.
- Five `.claude/agents/` worker defs exist, each preloading its skill and tool-scoped (Decision A);
  drift test green.
- Classify runs `merge` post-fan-out; **consolidate emits per-node JSONL findings and applies them
  via a deterministic serial step** (Decision B/D) — no concurrent shared-state writes, no silent
  no-op; draft/synthesize have no post-step.
- All state mutation goes through `state_machine.py`; no two concurrent agents write shared state.
- The schema seam (T55) and budget seam (T56, persisted to content-free `cost_map.json`) are wired
  and clearly marked.
- Human gates preserved structurally — the workflow makes no `next`/`render`/`final` call.
- Worker skills remain standalone-invokable; `orchestrate.py` action contract unchanged; no scratch
  engagement left behind.
