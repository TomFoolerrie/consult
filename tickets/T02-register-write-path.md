# T02 — Register write-path overhaul (JSON-native upsert, dedup_key, unmapped null-node)

- **Slice:** 1 (floor) · **Depends:** T01 (sequential — shared files) · **Touches:** `skills/consult-improvement-log/scripts/improvement_log.py`, `scripts/state_machine.py`
- **Refs:** spec §4, §8 open #1, §10 hardening; `classify_contract.md` §5/§5b; `consolidate_contract.md` §4; adversarial P0 #1/#3, P1 #5.

## Goal
Replace the temp-CSV transport with a JSON-native upsert; support `dedup_key` upsert, `type:unmapped`
null-node rows, and stop two latent bugs (forced `requires_human_review` on insert; backup-per-write churn).

## Scope (build)
1. **JSON-native upsert in `improvement_log.py`:** add an `upsert` path that takes records as JSON
   (a list of dicts) — not CSV — and upserts by `id`. Keep `update-json` (CSV) working for back-compat
   but stop `add-item`/`gap_report` from using the CSV temp-file route.
2. **`dedup_key` upsert:** if a record carries `dedup_key`, upsert by `dedup_key` (match an existing row
   with the same key → update in place; else insert). This is what stops re-consolidation from minting a
   duplicate `IMP-/GAP-NNNN` for the same finding.
3. **Type carry / unmapped:** never default a missing `type` to `improvement` when the caller passed one;
   support `type:unmapped` rows with **null** `l1_cycle`/`l2_process`. Add `add-item --type unmapped`
   (no `--l1/--l2` required) generating `UNM-NNNN` ids; set `disposition:pending`, `owner:TBD`.
4. **`sync` orphan-exclusion:** in `state_machine.py cmd_sync`, a row that is `type:unmapped` with null
   node is **not** an orphan — exclude it from the orphan report (and don't roll it into any node bucket).
   Genuine orphans (a non-unmapped row pointing at a missing node) still report.
5. **Insert flags fix:** stop force-setting `requires_human_review=true` on *every* inserted row — honor
   a value the caller provides; default to `true` only when the caller omits it.
6. **Backup churn:** write at most one timestamped backup per command invocation, not per record.

## Out of scope
Disposition lifecycle/gate (T34); the classifier/merge that *calls* these (T12).

## Tests (scratch `__t02__`, remove at end; do not commit)
1. `add-item --type unmapped` (no l1/l2) → creates `UNM-0001`, null node, `disposition:pending`; register
   schema-valid; a 2nd → `UNM-0002`.
2. `sync` with an unmapped row present → it is **not** listed as orphan; a genuinely mis-nodal row
   (`type:gap` with a bad node) **is**.
3. Upsert with a `dedup_key`: insert a finding with `dedup_key=K`; upsert again with the same key + a
   changed field → **one** row, updated (not two). Different key → two rows.
4. Insert a row with `requires_human_review=false` explicitly → it is preserved (not forced true).
   Omit it → defaults true.
5. A multi-record upsert writes ≤1 backup file.
6. Existing `add-item`/`gap_report.py` flows still pass their behavior (re-run gap_report scan idempotent;
   counts unchanged).

## Done when
All tests pass; both scripts compile; schemas valid; report output + any deviation.
