---
name: consult-docx-builder
description: "Convert finalized consult-drafter process-documentation Markdown into a CFGI-styled Word (.docx) deliverable using the bundled Python converter. Use when the user asks to convert process documentation or a desktop procedure to Word, generate a .docx from a finalized consult-drafter draft, apply the CFGI Word house style, or produce a Word deliverable from Markdown. Do NOT use to draft or edit the content, clean transcripts, audit evidence, resolve Word comments, insert real screenshots, or build slides — this skill only renders finalized Markdown to Word."
---

# Consult DOCX Builder

## Purpose

Render a finalized process-documentation Markdown file — the output of the
`consult-drafter` skill — into a CFGI-branded `.docx` using the bundled
converter. The house style is applied automatically; this skill styles and
renders, it does not author content.

## Use This Skill When

- Convert finalized process-doc / desktop-procedure Markdown to Word.
- Generate a `.docx` from a finalized `consult-drafter` draft.
- Apply the CFGI Word house style to a Markdown deliverable.

Do not use this skill to draft or edit the process documentation, clean
transcripts, audit evidence, resolve comments, or insert real screenshots. Those
belong to `consult-drafter` or other skills.

## Required Inputs

Two input modes:

- **Component folder (primary).** An area directory containing `manifest.json`
  and its `NN_*.md` components. This is how the orchestrator renders — via the
  top-level entrypoint `"${CLAUDE_PLUGIN_ROOT}/scripts/render.py" <area>`, which imports M2's
  `doc_model.assemble(folder)` to get the structured document and hands it to
  this converter's `convert_assembled` hook.
- **Single Markdown file (back-compat).** A finalized single-file draft,
  normally produced by `consult-drafter`.
- Optional output filename.

The input should already be reconciled — run `"${CLAUDE_PLUGIN_ROOT}/scripts/reconcile.py"` first so IDs
(`CTRL-001`, `PP-001`, `IO-001`, `GAP-01`, `SC-01`, `SRC-001`) and their
appendix rows are consistent before rendering to Word.

### Folder input, numbering, and `[[slug]]` tokens

Under the flat-H2 template there is exactly one H1 (the document title, held in
the manifest — never in a fragment) and every section is `##`. For folder input:

- **Title/subtitle come from the manifest**, not from an inline H1 scan; the
  Document Profile card is lifted from the `document-profile` static section.
- **Display numbers are resolved late, here.** `"${CLAUDE_PLUGIN_ROOT}/scripts/render.py"` prefixes each
  `procedure` heading with its `{L2}.{seq}` number and resolves every `[[slug]]`
  cross-reference (in prose *and* derived tables — Systems "Related Procedures",
  Appendix A "Source Procedure") through M2's single `display_numbers` map. A
  reorder in the manifest therefore renumbers headings and cross-refs together,
  with no stale back-references.
- `<!-- derived: … -->` markers and any fenced ` ```consult-meta ` block are
  stripped before rendering — neither appears in Word.

Numbers and tokens live in exactly one place (`doc_model`); this converter
never computes them.

## Script Location

```text
${CLAUDE_SKILL_DIR}/scripts/cfgi_markdown_to_word.py     # the converter (this skill)
${CLAUDE_PLUGIN_ROOT}/scripts/render.py                  # top-level folder entrypoint (imports doc_model + this converter)
```

## Commands

Render a component folder (what the orchestrator runs):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/render.py" <area> -o <out.docx>
```

Default single-file conversion (builds a cover page):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cfgi_markdown_to_word.py" input.md
```

Named output:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cfgi_markdown_to_word.py" input.md -o output.docx
```

Insert a generated Table of Contents:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cfgi_markdown_to_word.py" input.md -o output.docx --include-toc
```

Landscape orientation (useful for wide appendix tables):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cfgi_markdown_to_word.py" input.md -o output.docx --landscape
```

Skip the generated cover page:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/cfgi_markdown_to_word.py" input.md -o output.docx --no-cover
```

The converter is opinionated and takes no JSON style configuration — the CFGI
house style is fixed.

## What the Converter Applies

- **CFGI green house style** — Calibri body, dark-green title, green headings
  with a rule under each section start, green table header rows that repeat
  across pages. Under the flat-H2 template the section-start rule is drawn under
  **H2** (the H1→H2 weight remap); single-file H1 documents still get the rule.
- **Cover page** — *folder input:* title/subtitle from the manifest, Document
  Profile card lifted from the `document-profile` section. *Single-file input:*
  the first H1 becomes the cover title and the `Document Profile` table is lifted
  onto the cover as a summary card, then suppressed inline. `--no-cover` disables
  the cover and leaves the profile in the body.
- **Canonical hierarchy preserved** — `#`/`##`/`###`/`####` map straight through
  to Heading 1–4, so the `consult-drafter` structure and the TOC stay intact.
- **Callouts colored by label** — `CONTROL` (green), `VALIDATION REQUIRED`
  (yellow), `PAIN POINT` (red), `IMPROVEMENT OPPORTUNITY` (blue), and
  `SCREENSHOT PLACEHOLDER` (gray) each render as a distinct shaded box.
- **Tables auto-styled by kind** — field/summary, control, gap (zebra),
  screenshot, and standard, detected from the table header.
- **Screenshots stay placeholders** — Markdown image links render as screenshot
  placeholder callouts; real images are never inserted.

## Workflow

1. Confirm the Markdown file exists and appears finalized.
2. Confirm it was reconciled by `consult-drafter` (no dangling IDs).
3. Choose an output filename if none was provided.
4. Run the converter.
5. Confirm the `.docx` was written.
6. Give the user the output path.

## Pre-Conversion Checklist

- Document starts with an H1 title.
- A `Document Profile` table is present (drives the cover page).
- Canonical sections and the A–H procedure subsections are present.
- Tables use GitHub-style Markdown (or clean HTML) tables.
- Screenshot references are text placeholders, not real image links.
- Appendix B (Gap / Validation Log) and Appendix C (Screenshot / Evidence
  Index) are present when the body contains gap or screenshot IDs.

## Output Naming

```text
[process-name]_process-doc_v[version].docx
```

If the version is unknown:

```text
[process-name]_process-doc_draft.docx
```
