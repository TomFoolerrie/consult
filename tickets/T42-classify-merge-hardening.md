# T42 — `classify_merge.py` hardening

**Slice 3 · Wave 2 (parallel) · Depends: T40 · Touches: `scripts/classify_merge.py`**

## Fixes (from review)
1. **Partial-failure / fail-closed (NOT a cursor)** — re-runs are *already* idempotent
   (evidence dedups, lenses recompute, gaps/unmapped upsert by dedup_key) — do **not** build a
   merge cursor. The real gap is single-run atomicity. Fix: a **pre-flight pass that validates
   ALL facts** (refs parseable, nodes are `l1.l2` in taxonomy, lens values legal) and aborts
   the whole merge *before* issuing any mutation. Boundary: structural/validation errors abort
   (fail-closed); data-quality drops (fix 4) are skip-reported and the merge proceeds. A
   conflict is **not** a failure — it still raises a GAP and continues.
2. **`_raise_conflict_gap` IndexError** — `node.split(".",1)[1]` crashes on a dot-less node.
   `collect_lens_signals` currently stores `node` verbatim with no split, so this is **new
   validation code**: have `collect_lens_signals` reject/skip-report any node not matching
   `l1.l2`-in-taxonomy (folds into the fix-1 pre-flight).
3. **Evidence path canonicalization** — dedup in `add-evidence` is by `(source, loc)`; same
   line range cited abs vs rel duplicates. Canonicalize to **relative-to-`engagements/{eid}/`**
   before `--source`; a path already outside that tree → skip-report (don't clamp).
   **Compat note:** this changes the dedup key, so existing evidence written with raw paths
   won't match on re-run → transient dupes. Accept the transient dupes (no migration); call it
   out in the report.
4. **Silent drops** — `_parse_ref` returning `None` and lens signals missing lens/value are
   dropped silently. Accumulate a skip-report and print it (count + first few) so dropped
   evidence is visible.
5. **Unmapped dedup collision** — in-run dedup keyed only on `evidence_ref` collapses
   distinct summaries sharing a ref. Include a normalized-summary hash in the dedup key.
   **Compat note:** existing unmapped rows keyed on bare `evidence_ref` won't match the new
   key → transient dupes on re-run; accept (no migration), report the count.

## Tests
`tests/test_classify_merge_hardening.sh`:
- a genuine cross-doc lens **conflict** produces exactly one `GAP-CONFLICT-*` (closes the
  classify-contract validation gap);
- a phantom/unparseable evidence ref is reported in the skip summary, not silently lost;
- malformed node key in an artifact errors cleanly;
- re-running merge on the same artifact set is idempotent after a simulated mid-run abort.

## DoD
Tests pass; schemas valid; no scratch engagement left.
