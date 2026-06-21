# T03 — Node status shape: `improvement.*` + render/review rev markers + `consolidated_at`

- **Slice:** 1 (floor) · **Depends:** T02 (sequential) · **Touches:** `scripts/state_machine.py`, `schemas/engagement_state.schema.json`
- **Refs:** spec §8 open #11c, §10; `orchestration_contract.md` §4/§8; `generation_review_contract.md` §1/§2; buildability #3.

## Goal
Give Stream B its own node status (parallel to `sop`) and add the render/review progress markers and the
`consolidated_at` stamp the resumable loop and the dirty signal need.

## Scope (build)
1. **`new_node()` additions:** `improvement: {status:"not_started", path:null, rev:0}` plus
   `rendered_rev:0, reviewed_rev:0` on **both** `sop` and `improvement`. (`consolidated_at`/`last_evidence_at`
   already in schema; ensure `new_node` initializes `consolidated_at:null`.)
2. **Schema:** add `improvement` (same shape as `sop`) and the `rendered_rev`/`reviewed_rev` fields to the
   node definition in `engagement_state.schema.json`. `sop.status`/`improvement.status` share the enum
   `not_started→drafting→draft→in_review→revised→final`.
3. **Commands:** add `set-improvement` (mirrors `set-sop`: `--status/--path/--bump-rev`), and extend both
   `set-sop`/`set-improvement` with `--bump-rendered-rev` / `--bump-reviewed-rev`. Add `mark-consolidated
   --node KEY` that sets `node.consolidated_at = now_iso()` (consolidate calls this).
4. **Diagnosis-dirty helper:** add a function/predicate `is_diagnosis_dirty(node)` =
   `last_evidence_at is not None and (consolidated_at is None or last_evidence_at > consolidated_at)`.
   Used by T04. Handle the null cases explicitly (a node with no evidence is **not** dirty).

## Out of scope
The status/next command (T04); consolidate calling `mark-consolidated` (T13).

## Tests (scratch `__t03__`, remove at end; do not commit)
1. `init` → every node has `improvement.status==not_started`, `sop.rendered_rev==0`, `consolidated_at==null`.
2. `set-improvement --status draft --bump-rev` → status draft, rev 1; `--bump-rendered-rev` → rendered_rev 1.
3. `mark-consolidated` sets `consolidated_at`; `is_diagnosis_dirty` is False right after (no new evidence),
   True after an `add-evidence` (last_evidence_at > consolidated_at), and False on a fresh node with no evidence.
4. State stays schema-valid.

## Done when
Tests pass; compiles; schema re-validated; report output.
