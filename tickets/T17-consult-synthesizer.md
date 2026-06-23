# T17 — `consult-synthesizer` (Stage 5C, the decision layer)

- **Slice:** 1 · **Depends:** T13 (populated register), T15/T16 (deliverables exist) · **Touches:** `skills/consult-synthesizer/` (new), `scripts/synthesis_inputs.py` (new)
- **Refs:** spec §5 Stage 5C + Synthesis DoD; domain review (binder→recommendation, cross-cutting themes).

## Goal
Turn the bottom-up streams into a **point of view**: the lead `deliverables/synthesis.md` (exec summary +
prioritized roadmap + current→future) and `type:theme` cross-cutting findings.

## Scope (build)
1. **`scripts/synthesis_inputs.py gather --engagement E [--json]`** (READ-ONLY): cross-cutting aggregation —
   all active `type:improvement` rows with `effort`/`priority`/`phase`/lens + the node `coverage`/lens
   scores across L1s; a simple **effort×impact bucketing** (e.g. quick-win = low-effort/high-impact) and a
   per-L1 lens roll-up (esp. `capability:new` → future-state signal). Read-only.
2. **`skills/consult-synthesizer/SKILL.md`** — sub-agent brief: from the aggregation, author
   `deliverables/synthesis.md` with: **Executive summary**; **Effort × Impact prioritization** (quick-wins /
   0–6mo / 6–18mo roadmap, sequenced by the register fields — not by lens); **per-L1 current → future
   operating model** (from lens scores). Lift **cross-cutting findings** the per-L2 grid would shred into
   `type:theme` register rows via `add-item --type theme --field related_nodes=...` (multiple node keys),
   each with a stable `dedup_key`. Cite register IDs; never invent numbers (directional).

## Out of scope
Word render (T18). The streams themselves (T15/T16).

## Tests (scratch `__t17__`; seed several improvements across L1s with effort/priority; do not commit)
1. `synthesis_inputs.py gather --json` returns the aggregation: improvements with effort/priority, an
   effort×impact bucketing, and per-L1 lens roll-up; read-only (state byte-identical before/after).
2. A `type:theme` row created via the documented `add-item --type theme --field related_nodes=...` example
   **schema-validates** (related_nodes is an array of `{l1}.{l2}` keys) and re-running same `dedup_key` →
   one row.
3. SKILL.md present; documents the synthesis sections + the theme/related_nodes path; commands exist.

## Done when
Helper + SKILL present; tests pass; report output + deviations.
