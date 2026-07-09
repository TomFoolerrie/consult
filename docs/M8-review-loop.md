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
- Output: **one notes file per procedure that has feedback**, named by slug —
  `{area}/_review/{slug}.notes.yaml`. A single reviewed `.docx` spans many
  procedures, so the extractor **splits** the changes/comments by the procedure
  each is anchored to and writes them into that procedure's file:
  ```yaml
  # _review/bank-reconciliation.notes.yaml
  procedure: bank-reconciliation
  items:
    - type: tracked-change            # or: comment
      location: "E · Step 3"
      anchor: "…the CFO approves…"
      change: "CFO → Controller"      # tracked-change edits
      note: "who actually signs off?" # comment text
      author: J. Smith
  ```
  One file per slug is what makes dispatch trivial (below) — the filename *is* the
  routing key.
- Archive the consumed `.docx` (e.g. `_review/processed/`) after extraction.

### Implementation notes (as built)

- **CLI:** `python3 scripts/review_extract.py <reviewed.docx> [--area <folder>]
  [--no-archive] [--dry-run]`. `--area` defaults to the docx's parent (or its
  grandparent when the docx sits in `_review/`, the normal drop location); the
  manifest is loaded from `{area}/manifest.json`.
- **XML backend:** `lxml` is preferred; the script falls back to stdlib
  `xml.etree.ElementTree` when lxml is absent (verified identical output on both).
- **Number/title → slug mapping** uses `doc_model.load_manifest` +
  `display_numbers` (the single numbering authority — never re-derived here). A
  rendered H2 like `1.1 Bank Reconciliation` is resolved by its number prefix
  first, then by a normalized title match against the manifest component headings.
  Non-procedure H2s (Document Profile, derived views) resolve to no slug.
- **Heading stack** is read from paragraph `w:pStyle` values (`Heading1..4`):
  H1 = document title (ignored), H2 = procedure/section, H3 = A–H subsection,
  H4 = step. `location` renders as `"<A–H letter> · <step>"` (e.g. `E · Step 3`),
  or `(procedure body)` when neither is set.
- **Tracked changes:** `w:ins` / `w:del` are collected in document order per
  paragraph; an adjacent `del`→`ins` pair is collapsed into a single replacement
  (`change: "CFO → Controller"`), otherwise emitted as `inserted: …` /
  `deleted: …`. Author + date come from the `w:ins`/`w:del` attributes.
- **Comments:** `commentRangeStart/End` (matched by `w:id`, may span paragraphs)
  fix the anchor span + location; the comment body (author/date/text) comes from
  `word/comments.xml`. `w:commentReference` runs are ignored.
- **Anchor** is the enclosing span/paragraph visible text (inserted text kept,
  deleted text dropped), squeezed and clipped to ~160 chars.
- **Unattributable feedback** (a change/comment anchored outside any procedure —
  e.g. in a static or derived section) is **skipped with a WARNING to stderr**,
  never silently dropped and never written to a bogus slug.

### Notes file schema (what the drafter reads)

```yaml
procedure: bank-reconciliation      # == the slug (matches the filename)
source_docx: Fixed-Assets_process-doc.docx
items:
  - type: tracked-change            # or: comment
    location: "E · Step 3"          # procedure → A–H subsection → step
    anchor: "The Controller approves the reconciliation."
    change: "CFO → Controller"      # tracked-change only
    author: "J. Smith"              # omitted when absent
    date: "2026-07-08T10:00:00Z"    # omitted when absent
  - type: comment
    location: "E · Step 3"
    anchor: "The Controller approves the reconciliation."
    note: "Who actually signs off?"  # comment only
    author: "J. Smith"
```

`change` appears only on `tracked-change` items; `note` only on `comment` items —
matching the drafter's "tracked changes = high-authority SME input; comments =
instructions/questions" split. YAML is emitted dependency-free (quoted scalars)
and parses cleanly under PyYAML.

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

The orchestrator lists `{area}/_review/*.notes.yaml` and dispatches
`consult-drafter` (`mode: update`) once per slug, pointing each at its own
`_review/{slug}.notes.yaml`. The drafter already has `area` + `slug`, so it reads
its file directly — no searching. It treats tracked changes as **high-authority
SME input** (apply them) and comments as instructions/questions (answer in the
body, or raise a GAP if unresolved), then emits a clean finished procedure. After
a successful pass the orchestrator archives that procedure's applied notes.

## Orchestrator wiring (M7 state table)

Add: `_review/` notes present → next action `apply_review` = re-dispatch
`consult-drafter` (update) for the annotated procedures, skip taxonomy → then
`aggregate` → `render`. Route strictly by folder.

## Acceptance

- A reviewed `.docx` with both a tracked change and a comment yields review notes
  correctly attributed to the right procedure + subsection/step, with anchor text.
- A single `.docx` spanning multiple procedures **splits** into one
  `{slug}.notes.yaml` per procedure, with each item mapped to its slug via the
  rendered heading's display number (or title) through `display_numbers`.
- A `del`→`ins` replacement collapses to one `X → Y` change; a bare insert/delete
  renders as `inserted:`/`deleted:`; author + date are preserved.
- Feedback anchored outside any procedure is reported as a WARNING, not dropped
  silently and not misfiled.
- Notes land in `_review/`, never `_sources/new/`; the orchestrator routes them to
  the drafter without invoking taxonomy.
- The drafter update pass applies the tracked change, addresses the comment, and
  leaves no resolved-gap artifacts.
- Consumed `.docx` and applied notes are archived, not left as live work.

## Out of scope

Reverse-applying edits into source (rejected); auto-detecting scope-changing
comments (human-escalated).
