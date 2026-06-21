# T30 — docx comment extraction helper

- **Slice:** 2 (keystone; research spike) · **Depends:** — · **Touches:** `scripts/docx_comments.py` (new)
- **Refs:** `generation_review_contract.md` §2 (Ingest the review); spec §10 hardening (S2).

## Goal
A deterministic helper that pulls **tracked comments** (and, best-effort, tracked changes) out of a
reviewed Word `.docx`, each re-associated with the body text it anchors — the input the
`consult-review-comment-resolver` needs. This is raw OOXML work (python-docx does not expose comments).

## Scope (build)
`scripts/docx_comments.py extract --docx PATH [--json]`:
- Unzip the docx; parse `word/comments.xml` (comment `id`, `author`, `date`, text) and the
  `w:commentRangeStart`/`w:commentRangeEnd` + `w:commentReference` anchors in `word/document.xml`.
- For each comment, recover the **anchored body text span** (the run text between its range start/end).
- Best-effort: also surface tracked changes (`w:ins`/`w:del`) as `{type, author, text}` entries (optional;
  note if deferred).
- Output: JSON list `[{id, author, date, comment, anchored_text, ...}]` (or a readable table without `--json`).
- Handle gracefully: a docx with no comments → empty list, exit 0; a non-docx/zip → clear error nonzero.

## Out of scope
Classifying/applying the comments (T31). Full tracked-change merge semantics.

## Tests (build the fixture; clean up; do not commit)
1. **Construct a minimal commented .docx in the test** (hand-assemble the OOXML zip: `document.xml` with a
   `commentRangeStart/End` around a run + `commentReference`, and a `comments.xml` with one authored
   comment) — then `extract` recovers the comment text, author, and the anchored body span. (If python-docx
   or a helper lib can author comments, use it; otherwise craft the zip directly.)
2. A docx with **no** comments → `extract` returns `[]`, exit 0.
3. A non-docx file → clear error, nonzero exit.
4. `--json` parses; the helper compiles.

## Done when
Helper present; tests pass (incl. the real anchored-comment recovery); report output, the OOXML approach
taken, and whether tracked-changes extraction was included or deferred.
