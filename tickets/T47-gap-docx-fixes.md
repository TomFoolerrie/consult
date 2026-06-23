# T47 — `gap_report.py` + `docx_comments.py` fixes

**Slice 3 · Wave 2 (parallel) · Depends: — · Touches: `scripts/gap_report.py`,
`scripts/docx_comments.py`** (disjoint from all other Wave-2 tickets)

## gap_report.py
1. **Malformed-node guard** — `detect_gaps` (`:102-105`) reads `node.get("l1")`; a null l1
   yields `GAP-STRUCT-None-None-...`. Skip + report nodes with missing l1/l2.
2. **Temp CSV leak** (`:228-247`) — the named temp file is created before a `writer.writerow`
   block that has no `try`; a write error leaks the file (the `finally` only guards the
   subprocess). Wrap creation→unlink in one `try/finally` (or `tempfile` context).
3. **`tag` overwrite on re-scan** (`:187`) — a re-detected row overwrites a human-edited
   `tag`. Preserve a human-set tag like T36 preserves `review_status`/`owner`.
4. **Dead constant** — remove unused `REGISTER_SCHEMA` (`:45`).

## docx_comments.py
5. **Unbalanced comment ranges** (`:144-152`) — an unmatched `commentRangeEnd` leaves an id
   permanently active, vacuuming all later runs into it. Guard against unbalanced start/end.
6. **Headers/footers/footnotes missed** (`:193-205`) — only `word/document.xml` is read.
   Either extend to `header*/footer*/footnotes.xml` or document the limitation explicitly in
   the SKILL + docstring.

## Tests
- `tests/test_gap_rescan_tag.sh`: a human-edited tag survives a structural re-scan;
  a malformed node is reported, not emitted as `GAP-STRUCT-None`.
- `tests/test_docx_comments_edge.sh`: a doc with an unbalanced comment range doesn't
  mis-attribute trailing text; a header-anchored comment is either extracted or the
  documented limitation is asserted.

## DoD
Tests pass; Slice-1 gap stage + Slice-2 comment extraction still green; no scratch left.
