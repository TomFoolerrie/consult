# T53 — docx structure reconstruction (list numbering + nested tables)

**Slice 3 (Remediation & Hardening) · Follow-up · Depends: T52 · Touches:
`scripts/ingest_normalize.py`, `tests/`**

## Problem
T52 makes `.docx` fidelity loss *visible* (an omission marker counts dropped images, flattened
lists, and nested tables) but does **not** recover that structure. This ticket does the
deterministic reconstruction T52 deliberately deferred:

- **List numbering** — paragraphs with `w:numPr` currently emit as plain text, losing
  bullet/number prefixes (bad for SOP-type procedure steps). Map them to Markdown `-` (bullets)
  / `1.` (ordered), using the paragraph's numbering properties; preserve nesting/indent level
  where resolvable. Fall back to plain text (and keep counting it as flattened) when the
  numbering definition can't be resolved from `numbering.xml`.
- **Nested tables** — a `w:tbl` inside a table cell is currently flattened by `cell.text`
  (`handle_docx`, `ingest_normalize.py:273`). Recurse so nested tables render as their own
  Markdown tables in document order.

## Build
Extend `handle_docx`. Keep all T52 invariants: hash is over source bytes, output stays
deterministic, immutability/dedup untouched. The omission marker from T52 should drop the
counts it now reconstructs (a recovered list is no longer "flattened").

## Tests
Fixtures (generated deterministically with `python-docx`): a numbered + bulleted (nested) list
→ correct Markdown list markers and nesting; a table-within-a-cell → nested Markdown table;
re-ingest of the same bytes still dedup-skips.

## DoD
List numbering and nested tables are reconstructed deterministically; T52's marker reflects only
genuinely-unrecoverable omissions; tests pass; no scratch left; no regression to T52's suite.
