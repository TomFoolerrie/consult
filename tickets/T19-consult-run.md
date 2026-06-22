# T19 — `consult-run` orchestration (Slice-1 linear)

- **Slice:** 1 · **Depends:** T04 (status) + all stages T10–T18 · **Touches:** `scripts/orchestrate.py` (new), `skills/consult-run/` (new)
- **Refs:** `orchestration_contract.md` (§1 decision, §3 loop, §5 dispatch, §6 gates) — but build the **Slice-1 linear** form (the state-driven loop is S2/T37).

## Goal
The single entry the user invokes to advance an engagement, plus a testable "what's next" advisor. Slice 1
is **one-way, linear** and **stops at the render gate** (no review ingestion).

## Scope (build)
1. **`scripts/orchestrate.py next --engagement E [--json]`** (READ-ONLY) — reads `status` and returns the
   single next action in the Slice-1 order, one of:
   `ingest` (nothing ingested) → `classify` (N unclassified docs — fan-out) → `merge` (artifacts present,
   lenses/evidence not yet applied) → `consolidate` (N diagnosis-dirty nodes) → `gap` (consolidated, scan not
   run / dirty) → `draft` (draftable L1s) → `synthesize` → `render` → `done` (render gate reached).
   For each, report the targets (which docs / nodes / L1s) and whether it's a **deterministic** step (agent
   runs the script) or an **LLM fan-out** (agent spawns the named sub-agent skill per target).
2. **`skills/consult-run/SKILL.md`** — the playbook the agent follows: call `orchestrate.py next`; if
   deterministic, run the script (`ingest_normalize.py`, `classify_merge.py`, `gap_report.py scan`,
   `render_deliverables.py`); if LLM, fan out the matching skill (`consult-classifier` per doc →
   then `classify_merge`; `consult-consolidator` per dirty node; `consult-gap-analyzer`; `consult-drafter`
   + `consult-improvement-drafter` per L1; `consult-synthesizer`); loop until `done`. Document the **render
   gate** (stop + report; no auto-finalize) and that re-running is safe (status re-derives).

## Out of scope
The state-driven readiness loop (S2/T37), review ingestion, DoD `final` gates.

## Tests (scratch `__t19__`; do not commit)
1. Fresh `init` (nothing ingested) → `next` = `ingest`.
2. After dropping an ingested MD with no artifact → `next` = `classify`, lists the doc, kind=llm-fanout.
3. After dropping a classify artifact (unmerged) → `next` = `merge` (deterministic).
4. After `classify_merge` produces evidence+dirty nodes → `next` = `consolidate`, lists dirty nodes.
5. With a drafted/covered state and deliverables rendered → `next` = `done`.
6. `orchestrate.py` is read-only (state byte-identical before/after `next`).
7. SKILL.md present; documents the full linear sequence, the deterministic-vs-fanout split, the render gate,
   and idempotency; every script/skill it names exists.

## Done when
Advisor + SKILL present; tests pass; report output + deviations.
