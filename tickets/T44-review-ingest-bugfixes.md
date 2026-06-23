# T44 — `review_ingest.py` bug fixes

**Slice 3 · Wave 2 (parallel) · Depends: T40 · Touches: `scripts/review_ingest.py`**

## Fixes (from review)
1. **`add-evidence` unreachable** (priority) — **DECISION: add `add-evidence` to
   `ALLOWED_COMMANDS`** (`:52`) so reviewers can add evidence as the docstring promises.
   `cmd_add_evidence` exists in `state_machine.py`. Confirm the resolver emits `{"node": ...}`
   (handled by `_node_key_for_action`'s `"node"` branch); `cmd_add_evidence(eid, key, ...)`
   takes `--node`. Delete the dead `NODE_ARG` (fix 4) rather than resurrecting it.
2. **Re-apply double-write** — **DECISION: minimal fix.** (a) Add a **pre-flight validation
   pass** so the batch only starts applying once all actions are well-formed; (b) make
   `mark-dirty` failures **non-fatal to the consumed marker** (a node failing to dirty is
   logged but doesn't block marking the docx consumed). Do **not** build a per-action ledger.
   Document the narrowed contract: consumed-marking now tolerates mark-dirty failures only.
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
