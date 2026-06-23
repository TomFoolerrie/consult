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

## The per-stage dispatch model (the stages are NOT uniform — get this right first)

Each `llm_fanout` stage has a **different target key, worker count, and post-step**. The "one
`agent()` per target" framing only holds per-stage with the right key. From
`orchestrate.py` (`ACTION_DISPATCH` + `_action()` targets):

| stage | target key iterated | skill(s) per item | agents issued | post-fan-out step |
|---|---|---|---|---|
| classify | `targets.docs` (ingested MDs) | `consult-classifier` | `len(docs)` | run `classify_merge.py merge` (workflow supplies the `merge` subcommand) |
| consolidate | `targets.nodes` (dirty nodes) | `consult-consolidator` | `len(nodes)` | **apply** each returned finding (see Decision B) |
| draft | `targets.l1s` (**not** nodes) | **two** skills: `consult-drafter` **and** `consult-improvement-drafter` | **`2 × len(l1s)`** | none |
| synthesize | engagement-scoped (`scope == "engagement"`) | `consult-synthesizer` | **exactly 1** (degenerate, no list) | none |

A build that loops `targets.nodes` for draft, or expects one agent for draft, or one merge-style
`then_script` for every stage, is **wrong**. Encode this table.

## Decisions (recorded — these were under-specified; defaults set here, flag to override)

- **(A) Skill-invocation mechanism — the `agent()` prompt names the skill to follow.** A workflow
  `agent(prompt)` runs a *prompt*, not a skill. Each per-item `agent()` call passes a prompt that
  (i) instructs the sub-agent to load and follow the named SKILL (e.g. "Follow the
  `consult-classifier` skill."), (ii) passes the target identifier, and (iii) passes the gatherer
  command to run for its inputs (where the stage has a gatherer). *Alternative considered:* a
  custom agent type (`agentType`) bound to each skill — cleaner but requires committing five agent
  definitions; defer unless the prompt-names-skill path proves unreliable. **Pin this before
  build.**
- **(B) Consolidate apply-path — the workflow applies returned findings post-fan-out.** The
  consolidator does **not** write state; it *returns* findings to be applied via the command path
  (`state_machine.py add-item` + `mark-consolidated`). Classify has a `then_script` (`merge`);
  consolidate needs the analogous step or **consolidation is a silent no-op** and nothing
  downstream (gap/draft) becomes ready. Default: the workflow runs the apply step
  (`add-item` per finding, then `mark-consolidated` for the node) after each node's `agent()`
  returns. *Alternative:* hand findings back to `consult-run` to apply. Choose the workflow path
  for symmetry with classify; flag to override.

## Build

A committed workflow (`.claude/workflows/consult-fanout.*`, or an inline script `consult-run`
invokes — pin the invocation surface jointly with **T54 Tier 2**), **parameterized by stage** via
`args` (`{engagement, stage, targets}`; note `consult-run` maps the action's `action` field →
`stage`). For one `llm_fanout` action it:

1. Reads the stage row from the table above to pick the **target key** and **skill(s)**.
2. `pipeline()` / `parallel()` over the iterated targets — issuing the per-stage agent count above
   — each `agent()` invoking the named worker skill via Decision (A), fed (where applicable) by its
   **read-only** input gatherer: `consolidate_inputs.py` / `draft_inputs.py` /
   `synthesis_inputs.py`. **Classify has no gatherer** — the classifier reads the ingested MD + a
   taxonomy slice directly, so its prompt assembles those itself.
3. Runs the per-stage **post step**: classify → `classify_merge.py merge`; consolidate → the
   apply step (Decision B); draft/synthesize → none.
4. Returns per-target one-line summaries + a rollup to `consult-run`, which re-runs
   `orchestrate.py next` and proceeds to the next action / human gate.

**Worker state-write contract (correct, per-worker — do NOT overgeneralize):**
- `consult-classifier` — writes **only** its artifact `classify/{hash}.artifact.json`; never state.
- `consult-consolidator` — writes **no** state directly; returns findings the workflow applies (B).
- `consult-drafter` / `consult-improvement-drafter` — **DO** write state: `state_machine.py
  set-sop` / `set-improvement … --bump-rev`. Expected and correct.
- `consult-synthesizer` — **DOES** write state: `state_machine.py add-item` + `sync`.

So "the workflow writes no state" is **false** for draft/synthesize. The real invariant is: **all
state writes still go through `state_machine.py`** (never ad-hoc JSON), whether issued by a draft/
synth worker or by the workflow's consolidate apply step. The merge/classify path writes no state
(merge stages into register/state via its own command path; classify writes only an artifact).

**Seams to expose (the whole point of the foundation):**
- **Schema seam (T55):** the classify `agent()` call takes an optional `{schema}` arg, loaded from
  `schemas/classify_artifact.schema.json`. For the schema path, the **workflow** writes the
  validated returned object atomically (`temp + os.rename`) to `classify/{hash}.artifact.json` (the
  classifier sub-agent returns the object; the workflow persists it). Left as a clearly-marked,
  wired hook so T55 Phase 2 only flips it on. (Reconcile with T55 §G4: workflow owns the artifact
  write on the schema path.)
- **Budget seam (T56):** `budget.spent()` snapshot points immediately before/after each stage's
  fan-out (and optionally per `agent()` call), emitting a per-stage Δoutput-tokens line. Persist
  the rollup to a **content-free** `cost_map.json` so T56's reporter can read it (T56 §Gap-1).

**Failure / concurrency / idempotency semantics:**
- Bounded concurrency (workflow default cap). A worker that skips/dies → `agent()` returns `null`
  → `filter(Boolean)`; **partial completion is safe** because `orchestrate.py` re-derives readiness
  every `next` call (classify: a doc is classified only once its artifact exists **and** validates,
  `state_machine.py` `_classified_hashes`; draft: a node is draftable while its `sop`/`improvement`
  block is `not_started`), so a failed target simply re-runs. No batch abort.
- **classify post-step is safe after a partial fan-out:** `classify_merge.py merge` is idempotent
  over whatever artifacts exist on disk, and the standalone deterministic `merge` **action**
  (re-fires while there is unmerged evidence) is the safety net if the workflow's then_script run
  is skipped. So running merge after a partial classify is correct, not racy.

**Human-in-the-loop guard (hard constraint, make it testable):** the workflow drives **one fan-out
stage** and returns. It **MUST NOT** call `orchestrate.py next`, `render_deliverables.py`, or any
`final`/finalize path — it has no loop over `next`. That structural absence (not just prose) is
what keeps the render gate and `status.needs_human` stops owned by `consult-run`.

**Standalone preserved:** worker skills remain directly invokable; the workflow is an orchestration
layer over them, not a rewrite.

## Tests

- **Per-stage dispatch count (the core assertion — use the table):** classify with 2 docs → **2**
  agents; consolidate with 3 nodes → **3**; **draft with 2 L1s → 4** (two skills × two L1s);
  synthesize → **1**. Assert via a dry-run / mock agent (real agents are non-deterministic +
  costly — prescribe a mock mode, don't spend tokens per test run).
- **classify post-step:** `classify_merge.py merge` runs exactly once, **after** the fan-out;
  with a partial fan-out, merge still runs and only on-disk artifacts are merged.
- **consolidate apply-step (Decision B):** for N returned-finding nodes, the workflow issues the
  command-path `add-item`/`mark-consolidated` calls so the register gains rows and the node is
  marked consolidated; without it the test must fail (guards against the silent no-op).
- **Failure isolation:** one target's worker returning `null` does **not** abort the others; the
  rollup reflects the partial set; a re-run picks up the missing target (readiness re-derived).
- **State writes go through `state_machine.py` only:** assert draft/synth workers' state mutations
  and the consolidate apply step all use `state_machine.py` (no ad-hoc JSON writes). Do **not**
  assert "zero state writes" — that is false for draft/synthesize.
- **Human-gate guard:** assert the workflow issues **no** `orchestrate.py next`, `render`, or
  `final` calls (structural, via the mock harness).
- **Seams present:** schema hook + budget snapshot + `cost_map.json` exist and are exercised by
  T55/T56 tests (cross-referenced, not duplicated here).

## DoD

- A committed, stage-parameterized fan-out workflow issues the **correct per-stage agent count**
  (classify=docs, consolidate=nodes, draft=2×l1s, synthesize=1), deterministically, with bounded
  concurrency and `null`-tolerant partial completion.
- Classify runs `merge` post-fan-out; **consolidate applies returned findings** (no silent no-op);
  draft/synthesize have no post-step.
- The per-worker state-write contract is honored: classify/consolidate write no state; draft/
  synthesize write state **via `state_machine.py`**; the consolidate apply step uses the command
  path. All state mutation goes through `state_machine.py`.
- The schema seam (T55, workflow owns the artifact write on the schema path) and budget seam
  (T56, persisted to a content-free `cost_map.json`) are wired and clearly marked.
- Human gates preserved structurally — the workflow makes no `next`/`render`/`final` call.
- Skill-invocation mechanism (Decision A) and the invocation surface (with T54) are pinned;
  worker skills remain standalone-invokable; `orchestrate.py` action contract unchanged; no scratch
  engagement left behind.
