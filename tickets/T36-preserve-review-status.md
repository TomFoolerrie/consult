# T36 — Structural re-scan preserves human review fields

- **Slice:** 2 (correctness nicety) · **Depends:** — · **Touches:** `scripts/gap_report.py`
- **Refs:** adversarial review P2 #13.

## Goal
`gap_report.py scan` re-writes every `GAP-STRUCT-*` row with `review_status=needs_review` +
`requires_human_review=true` on every scan. If a human had reviewed/dispositioned a structural gap, the next
scan silently re-opens it. Preserve human review fields on already-existing active rows; only set the defaults
on a **new** insert.

## Scope (build)
In `gap_report.py build_csv_rows` (or wherever it composes the active `GAP-STRUCT` rows): when a detected
structural gap's id **already exists as an active row** in the loaded register, carry that row's existing
`review_status`, `requires_human_review`, and `owner` into the upsert instead of the hardcoded defaults.
Newly-detected (not-yet-present) gaps still get `review_status=needs_review` / `requires_human_review=true`.
Stale rows being archived (the self-heal path) are unchanged. The observation text may still refresh.

## Out of scope
Changing the self-healing archival logic or the gap detection rules.

## Tests (scratch `__t36__`; do not commit)
1. `scan` → a `GAP-STRUCT` row exists with `review_status=needs_review`.
2. Set that row `review_status=reviewed` (via add-item upsert by id); re-`scan` → the row **keeps**
   `review_status=reviewed` (not reset to needs_review).
3. A node that newly becomes a structural gap on a later scan still gets `needs_review`.
4. Idempotency intact (re-scan record counts stable); compiles; register schema-valid.

## Done when
Preservation logic in `gap_report.py`; tests pass; report output + deviations.
