# T56 — Per-phase cost instrumentation (measure the real hotspot)

**Slice 4 (Cost & Runtime Efficiency) · Follow-up · From field run (3 real artifacts, ~$10) ·
Depends: T54 Tier 2 (for `budget.spent()` signal) · Feeds T54 + T55 acceptance · Touches:
`.claude/workflows/consult-fanout.*` (the per-stage `budget` snapshots),
`scripts/orchestrate.py`, `scripts/consolidate_inputs.py`, `scripts/draft_inputs.py`,
`scripts/synthesis_inputs.py`, `scripts/cost_report.py` (new), `tests/`.**

> **Runtime correction.** Earlier I claimed "Desktop has no programmatic per-phase token meter, so
> instrument content size as a proxy." **That undersold the Claude Code runtime.** Under T54's
> Tier-2 fan-out **Workflow**, the script has a **`budget` object** with **`budget.spent()`**
> returning output tokens spent this turn across the main loop and all workflows (confirmed against
> the live Workflow tool contract). So **real per-phase output-token accounting is available** —
> snapshot `budget.spent()` around each fan-out stage. The size proxy below is now a *complement*
> (input-side breakdown + a fallback for the non-workflow path), not the primary signal.

> **No client content is ever emitted — only token counts, sizes, counts, and phase labels.**

## Problem

We're guessing which phase dominates the ~$10 (strong prior: T54's inlining). T54 ("did inlining
cost the most?") and T55 ("did the trim/constrained emission help?") have no acceptance signal
beyond a raw dollar total. We need a per-phase map.

## Build

**Primary — `budget.spent()` deltas in the fan-out workflow (with T54 Tier 2):**
1. In the fan-out Workflow, snapshot `budget.spent()` immediately before and after each stage's
   fan-out (classify / consolidate / draft / synthesize). The delta = output tokens that stage
   cost. `log()` a per-stage line (stage, #targets, Δoutput-tokens) and return the rollup so
   `consult-run` can surface it. This is the **acceptance artifact** T54/T55 cite.
2. Where useful, also snapshot per **target** (per `agent()` call) to spot a single pathological
   doc/node, not just the stage total.

**Complement — input-size breakdown (works on any path, content-free):**
3. In each input gatherer (`consolidate_inputs.py`, `draft_inputs.py`, `synthesis_inputs.py`),
   add a side-channel size summary (stderr or a `--measure` flag, **never** in the consumed
   bundle): total chars, an est. token count (chars/4, labelled an estimate), and a per-section
   breakdown (taxonomy slice vs evidence vs prior MD) — **sizes and section names only**.
   `budget.spent()` gives *output* tokens; this gives the *input* side the budget can't see.
4. `orchestrate.py measure --engagement E` (read-only, like `next`): walks the engagement and
   reports per phase — #targets, est. input size per target (from #3), output artifact/MD sizes on
   disk. Writes nothing.

**Reporter:**
5. `scripts/cost_report.py` (new, dependency-free, content-free): aggregates #1–#4 into a one-
   screen table (phase, #targets, output tokens (measured), est. input tokens, output bytes) with
   a field to **paste the run's measured $ total** for size→cost correlation across runs.

**Acceptance hook:** document the single command to run after a 3-artifact engagement to capture
the map; T54/T55 reference its before/after.

## Tests

- `orchestrate.py measure` / gatherer `--measure` / `cost_report.py` are **read-only** — running
  them leaves `state.json` / `register.json` / artifacts byte-identical (Slice-1 fixture).
- **Content-free assertion:** grep the measure/report output for a known content token from the
  fixture and assert **absent**; output is purely numeric/structural.
- Size estimates are **deterministic** for a fixed corpus (same fixture → same numbers).
- The gatherers' normal `--json` bundle output is **unchanged** (measurement is side-channel) —
  sub-agents consume exactly what they did before; Slice-1 e2e green.
- **Workflow budget path (with T54 Tier 2):** a 2-stage dry-run logs two non-negative
  `budget.spent()` deltas summing to ≤ the total spent; per-stage lines present in the rollup.

## DoD

- A single read-only command produces a per-phase map with **measured output tokens**
  (`budget.spent()` deltas under the workflow) + est. input sizes + output sizes, **zero client
  content**.
- The gatherers' consumed bundles are unchanged; measurement is side-channel only.
- T54 and T55 can cite a before/after from this map as their acceptance signal.
- A place exists to record the run's measured $ total alongside the map for size→cost correlation.
