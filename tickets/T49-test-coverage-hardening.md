# T49 — Test coverage hardening

**Slice 3 · Wave 3 (after Wave 2 code fixes) · Depends: T41–T47, **T50** · Touches: `tests/`,
`fixtures/`**

> **Sequence after T50** — item 5 (xlsx) and item 1 (schema-validate, which surfaces the
> fixture-vocab violations) both depend on T50's outcome. Run T50 first.

## Problem (from review)
The only regression (`tests/test_slice1_e2e.sh`) is a deterministic **spine** test with every
LLM stage stubbed by canned outputs. It proves plumbing + idempotency, not judgment, and
covers **zero of Slice 2** despite Slice 2 being marked complete.

## Build — add regressions for the unexercised paths
1. **Schema-validation assertion** — the e2e never runs `state_machine.py validate`; add it so
   produced `state.json`/`register.json` are asserted schema-conformant. (This will surface the
   fixture-vocab violations called out in T50 — coordinate.)
2. **Lens-conflict path** — a canned two-doc fixture that genuinely disagrees on a lens →
   assert exactly one `GAP-CONFLICT-*` and a null lens (closes classify-contract gap).
3. **Phantom evidence ref** — assert a `#L9999` out-of-range ref is rejected/reported at merge.
4. **Slice-2 regression** (`tests/test_slice2_e2e.sh`) — drive a **committed** reviewed
   `.docx` fixture (not LLM-produced, so the path is deterministic) through `docx_comments.py`
   → `review_ingest.py extract/apply` → `mark-dirty` → **stubbed** re-consolidate (canned
   output, same pattern as Slice-1 — not a live LLM call) → `gates.py final-check`; assert
   dirtied nodes, applied actions, consumed marker, and the `final` gate. Idempotent on rerun.
5. **xlsx snapshot path** — minimal assertion that `build-xlsx` produces a valid workbook.

## DoD
New tests pass and are idempotent; both e2e suites green with `requirements.txt` installed;
fixtures synthetic only; no scratch left.
