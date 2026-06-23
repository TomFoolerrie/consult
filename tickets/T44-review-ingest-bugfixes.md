# T44 — `review_ingest.py` bug fixes

**Slice 3 · Wave 2 (parallel) · Depends: T40 · Touches: `scripts/review_ingest.py`**

## Fixes (from review)
1. **`add-evidence` unreachable** (priority) — `SUBSTANCE_COMMANDS` includes `add-evidence`
   but `ALLOWED_COMMANDS` does not (`:52` vs `:60`), so the action is rejected at `:453`
   despite the docstring promising it. Decide and make consistent: either add `add-evidence`
   to `ALLOWED_COMMANDS` (preferred — reviewers should be able to add evidence) or remove it
   from `SUBSTANCE_COMMANDS` + docstring.
2. **Re-apply double-write** — if state commands succeed but a `mark-dirty` fails, the docx
   is not marked consumed and a re-run re-applies every already-committed action (no
   per-action idempotency) → duplicate evidence/items. Either make `mark-dirty` failures
   non-fatal to the consumed marker, or record per-action applied-state so replay is a no-op.
3. **Unguarded `json.load(actions)`** (`:431`) — wrap in a clean error like the isinstance
   check right after.
4. **Dead code** — remove the `_args_to_argv` leftover first two lines (`:379-381`) and the
   unused `NODE_ARG` constant (`:64-69`).
5. **Verify `add-item --field dedup_key=...` path** — the conflict upsert routes register
   fields through `--field`; confirm `add-item` accepts them (or the upsert fails silently
   and blocks consumed-marking). Add a regression.

## Tests
`tests/test_review_ingest_bugfixes.sh`:
- an `add-evidence` review action applies and dirties the node;
- a forced `mark-dirty` failure does not cause double-application on re-run (evidence count
  stable);
- malformed actions JSON errors cleanly;
- the `GAP-CONFLICT...REVIEW` upsert succeeds end-to-end.

## DoD
Tests pass; Slice-2 review loop still works on the r2r-demo fixture; no scratch left.
