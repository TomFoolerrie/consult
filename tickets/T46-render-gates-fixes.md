# T46 — `render_deliverables.py` + `gates.py` fixes

**Slice 3 · Wave 2 (parallel) · Depends: T40 · Touches: `scripts/render_deliverables.py`,
`scripts/gates.py`** (disjoint from all other Wave-2 tickets)

## render_deliverables.py
1. **`--l1` validation is a dead no-op** (`:59-61`) — both branches return `[l1_filter]`, so
   an invalid `--l1` silently looks for a missing file and exits 0. Reject unknown L1 with a
   clean error listing valid ids.
2. **Partial render leaves inconsistent state** (`:108-120`) — if `bump_rendered_rev` fails
   after a docx is written, earlier L1s are committed and this one isn't. Bump revs atomically
   (T40) and/or render-then-bump per L1 with a clear partial-failure report.
3. (Doc nit) clarify `rendered_rev` is a render-count, not a content hash, in the docstring.

## gates.py
4. **Evidence path-escape** (`:84`) — `edir / source` isn't normalized; a `../..`-style
   `source` resolves outside the engagement. **Mirror the existing idiom** in
   `consolidate_inputs.py:168-170` / `draft_inputs.py:89-91` (`(edir/rel).resolve()` +
   `try: relative_to(edir.resolve())`), not `is_relative_to`, for consistency. Fail the gate
   on escape.
5. **`final` artifacts never existence-checked** (`:99`) — `final_artifacts_have_path` only
   checks `path` truthiness. Assert the file exists (symmetry with the evidence-file gate).
6. **Unused import** — drop unused `Path` (`:31`). NOTE: `sys` is **not** imported in gates.py
   (the original ticket text was wrong); only `Path` is unused. `Dict/List/Any` are used.

## Tests
`tests/test_render_gates.sh`:
- invalid `--l1` errors (non-zero) instead of exit-0 no-op;
- a `final` node whose `path` points at a missing file fails the gate;
- an evidence `source` with `../` fails the gate.

## DoD
Tests pass; render still produces the r2r-demo docx set; no scratch left.
