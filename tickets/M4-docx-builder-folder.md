# M4 — docx builder: single-H1 + structured folder input

**Depends on:** M1 (heading contract), M2 (`doc_model.assemble` + `display_numbers`).
Independent of M3.

## Goal

Update `cfgi_markdown_to_word.py` for the single-H1 template and let it consume a
component **folder** via M2's structured `assemble`, rendering procedure numbers
and resolving `[[slug]]` tokens at build time.

## Why

The converter currently keys visual structure off H1 (first H1 = cover title,
rule under every H1). Under flat-H2 there is one H1 (title) and all sections are
H2, so section weight moves to H2. And numbers are resolved **late, here** — the
builder is the single place that turns the manifest into visible `1.1`/`2.3` on
both procedure headings and `[[slug]]` cross-references (review #1, #2, #4).

## Changes

`skills/consult-docx-builder/scripts/cfgi_markdown_to_word.py`:
- **Input:** accept either a single `.md` (back-compat) or a folder containing
  `manifest.json`. For a folder, call `doc_model.assemble(folder)` (import, don't
  shell out) → `AssembledDoc` with `title`, `subtitle`, and ordered
  `{heading, role, slug, number, body}` sections.
- **Numbering & tokens:** for `role: procedure` sections, prefix the rendered
  heading with `number` (`1.1 Bank Reconciliation`). In **every** section body,
  resolve `[[slug]]` tokens via `doc_model.resolve_tokens` using the one shared
  `display_numbers` map — so derived tables (Systems "Related Procedures",
  Appendix A "Source Procedure") show current numbers even though the source
  files store only slugs. A single reorder therefore renumbers headings *and*
  cross-refs consistently, with no stale back-references (review #2).
- **Cover:** branch cover construction on input mode (review r3 #10). *Folder
  input* → title/subtitle come from the **manifest**, and the Document Profile
  card from the `00_document-profile` section (the current `extract_cover_data`
  line-scan for a `# ` H1 does not apply — there is no inline H1). *Single-file
  input* → keep the legacy H1/tagline scan. `--no-cover` leaves Document Profile
  inline.
- **H1/H2 remap:** H2 sections get the section-break / heading weight formerly
  carried by H1 (rule under each H2 start, page-break policy as appropriate);
  H3/H4 unchanged. Verify this does not disturb the existing table-kind and
  callout detection (which key off content, not heading level).
- **Markers & meta:** strip `<!-- derived: … -->` comments, and **skip any fenced
  `consult-meta` block** entirely, so neither appears in Word.
- Keep CFGI green house style, callouts colored by label, tables auto-styled by
  kind, screenshots as placeholders, `--include-toc` / `--landscape` / `--no-cover`.

`skills/consult-docx-builder/SKILL.md` + `references/docx_build_contract.md`:
- Document folder input, single-H1 expectation, manifest-derived numbering, and
  `[[slug]]` token resolution.

## Acceptance

- `python cfgi_markdown_to_word.py <folder>` renders a `.docx` in manifest order
  with a cover (title + subtitle) and correct hierarchy.
- Single-file input still works (back-compat).
- Procedure headings show `1.1`, `1.2`, `2.1`, … from the shared helper; a
  `[[slug]]` in a derived table renders as the matching number.
- Reordering procedures in the manifest and re-rendering updates headings **and**
  cross-references together (no stale numbers).
- No `<!-- derived -->` text and no `consult-meta` block appears in the output.
- H2 sections render with section-level weight; TOC / landscape / no-cover still
  function.
- Folder input builds the cover from the manifest title/subtitle (no inline H1);
  single-file input still uses the legacy scan.

## Out of scope

Generating content; aggregator (M3); agents (M5).

## Adversarial review resolutions

- **#1:** consumes structured `AssembledDoc`, not a flat string.
- **#2 / #4:** numbers resolved once, at render, on headings and `[[slug]]`
  tokens alike, from the single shared helper — no stale cross-refs, no drift.
- **#6:** cover subtitle sourced from the manifest.
- **r3 #10:** cover construction branches on folder vs single-file input.
