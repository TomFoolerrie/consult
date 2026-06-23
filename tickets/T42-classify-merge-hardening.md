# T42 — `classify_merge.py` hardening

**Slice 3 · Wave 2 (parallel) · Depends: T40 · Touches: `scripts/classify_merge.py`**

## Fixes (from review)
1. **Partial-failure / no rollback** — `cmd_merge` runs evidence→lenses→unmapped as many
   subprocess calls; a mid-stream `SystemExit` leaves lenses set with no conflict gaps
   raised. Make the merge re-entrant *and* fail-closed: either stage all facts under a
   single register/state lock with a pre-flight validation pass, or record a merge cursor so
   a re-run resumes cleanly. At minimum, validate **all** artifacts before applying **any**.
2. **`_raise_conflict_gap` IndexError** — `node.split(".",1)[1]` crashes on a malformed
   (dot-less) node key. Validate `l1.l2` shape in `collect_lens_signals`; skip + report
   malformed node strings instead of crashing.
3. **Evidence path canonicalization** — dedup in `add-evidence` is by `(source, loc)`;
   same line range cited with absolute vs relative path duplicates. Canonicalize the ref
   path (relative-to-engagement) before passing `--source`.
4. **Silent drops** — `_parse_ref` returning `None` and lens signals missing lens/value are
   dropped silently. Accumulate a skip-report and print it (count + first few) so dropped
   evidence is visible.
5. **Unmapped dedup collision** — in-run dedup keyed only on `evidence_ref` collapses
   distinct summaries sharing a ref. Include a summary hash in the dedup key.

## Tests
`tests/test_classify_merge_hardening.sh`:
- a genuine cross-doc lens **conflict** produces exactly one `GAP-CONFLICT-*` (closes the
  classify-contract validation gap);
- a phantom/unparseable evidence ref is reported in the skip summary, not silently lost;
- malformed node key in an artifact errors cleanly;
- re-running merge on the same artifact set is idempotent after a simulated mid-run abort.

## DoD
Tests pass; schemas valid; no scratch engagement left.
