# M8 — Review loop: Word tracked-changes + comments → drafter

**Depends on:** M4 (renders the doc reviewers mark up), M0/M3 (drafter update mode).
**Blocks:** none.

## Goal

Let reviewers work the way they actually work — Microsoft Word, a mix of
**tracked changes and comments in the same `.docx`** — and get that feedback back
into the source procedures without a brittle round-trip. A Python step extracts
the markup into **procedure-anchored review notes**; the drafter (update mode)
works them in.

## Why extract-as-feedback (not reverse-apply)

The `.docx` is a *generated view*; the Markdown procedure is the source of truth.
Mechanically patching rendered-Word edits back into the source fragment is the
classic brittle round-trip. Instead we **extract** the edits/comments as anchored
feedback and let the drafter — the procedure's owner — apply them with judgment
(keeping the procedure clean: closed gaps removed, `consult-meta` updated, IDs not
renumbered).

## `review_extract.py` (Python)

- Input: a reviewed `.docx` (rendered by M4, marked up by a reviewer).
- A `.docx` is a zip of XML; `python-docx` doesn't expose tracked changes/comments,
  so parse the XML directly (via `lxml`):
  - **Comments** — text in `word/comments.xml`, anchored in `document.xml` by
    `commentRangeStart/End` around the span.
  - **Tracked changes** — inline `w:ins` / `w:del` in `document.xml`, with author +
    date.
- **Placement:** because we generated the doc, walk the heading stack while parsing
  and attribute every change/comment to **procedure → A–H subsection → step**, plus
  the exact anchor text. (The procedure heading carries its number/title; map back
  to the `slug` via the manifest.)
- Output: **procedure-anchored review notes** under `_review/` (see below), one
  entry per change/comment:
  ```yaml
  procedure: bank-reconciliation
  items:
    - type: tracked-change            # or: comment
      location: "E · Step 3"
      anchor: "…the CFO approves…"
      change: "CFO → Controller"      # tracked-change edits
      note: "who actually signs off?" # comment text
      author: J. Smith
  ```
- Archive the consumed `.docx` (e.g. `_review/processed/`) after extraction.

## Where notes land — and why it matters

Review notes land in **`_review/`**, NOT `_sources/new/`. This is deliberate: the
folder is the **routing signal**.
- `_sources/new/*` (raw documents) → **taxonomy incremental** (it must read them to
  tag `touches` / detect scope deltas).
- `_review/*` (already procedure-anchored) → **straight to the drafter, skipping
  taxonomy.** Review notes are content corrections to *existing* procedures, so
  there's nothing for taxonomy to scope.

(Edge case: a comment that implies new scope — "this is really two procedures." Not
handled automatically; the human escalates by dropping a note in `_sources/new/`
or re-invoking taxonomy. Default review path is content → drafter.)

## Drafter update mode (already specified in the drafter def)

The orchestrator dispatches `consult-drafter` (`mode: update`) for each procedure
with `_review/` notes, handing it that procedure's notes. The drafter treats
tracked changes as **high-authority SME input** (apply them) and comments as
instructions/questions (answer in the body, or raise a GAP if unresolved), then
emits a clean finished procedure. After a successful pass the orchestrator clears
the applied notes (archives them).

## Orchestrator wiring (M7 state table)

Add: `_review/` notes present → next action `apply_review` = re-dispatch
`consult-drafter` (update) for the annotated procedures, skip taxonomy → then
`aggregate` → `render`. Route strictly by folder.

## Acceptance

- A reviewed `.docx` with both a tracked change and a comment yields review notes
  correctly attributed to the right procedure + subsection/step, with anchor text.
- Notes land in `_review/`, never `_sources/new/`; the orchestrator routes them to
  the drafter without invoking taxonomy.
- The drafter update pass applies the tracked change, addresses the comment, and
  leaves no resolved-gap artifacts.
- Consumed `.docx` and applied notes are archived, not left as live work.

## Out of scope

Reverse-applying edits into source (rejected); auto-detecting scope-changing
comments (human-escalated).
