# T18 — Render deliverables to Word, per L1

- **Slice:** 1 · **Depends:** T15, T16, T17 (deliverable MDs exist) · **Touches:** `scripts/render_deliverables.py` (new)
- **Refs:** `generation_review_contract.md` §2 (Render); spec §5 Stage 6 (one-way render for Slice 1); `skills/consult-docx-builder/scripts/cfgi_markdown_to_word.py` (the existing MD→docx engine — reuse).

## Goal
Convert the deliverable Markdown into CFGI-branded Word, **one-way** (Slice 1 has no review ingestion).
Evidence refs are already inline in the MDs; rendering preserves them.

## Scope (build)
`scripts/render_deliverables.py render --engagement E [--l1 L1] [--what synthesis|sop|improvements|gap_report|all]`:
- For each target deliverable MD under `engagements/{E}/deliverables/` (`synthesis.md`, `sop/{l1}.md`,
  `improvements/{l1}.md`, `gap_report.md`), call the existing `cfgi_markdown_to_word.py` to produce the
  sibling `.docx`. Reuse that script (import or subprocess); do **not** reimplement MD→docx.
- After a successful render of a stream's per-L1 doc, bump `rendered_rev` via
  `set-sop`/`set-improvement --bump-rendered-rev` for the L2 nodes of that L1.
- Print what was rendered. Missing MDs are skipped with a note (not an error).

## Out of scope
docx **comment extraction** / review ingestion (S2, T30+). The change log / review_log (S2). Any LLM step.

## Tests (scratch `__t18__`; write tiny sample deliverable MDs with an inline evidence ref; do not commit)
1. A sample `deliverables/sop/record-to-report.md` → renders a `.docx` sibling that exists and is non-empty;
   `cfgi_markdown_to_word.py` is the engine (no reimplementation).
2. `--what synthesis` on a sample `synthesis.md` → `synthesis.docx` produced.
3. After rendering an L1's SOP, the L1's nodes show `sop.rendered_rev == 1`.
4. A missing target MD is skipped with a note, exit 0 (not a crash).
5. `render_deliverables.py` compiles.

## Done when
Script present; tests pass; report output + deviations. (If `python-docx`/the docx engine needs deps, install them.)
