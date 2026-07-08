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

- A finalized Markdown file, normally produced by `consult-drafter`.
- Optional output filename.

The input should already be reconciled — run `consult-drafter`'s `reconcile.py`
first so IDs (`CTRL-001`, `PP-001`, `IO-001`, `GAP-01`, `SC-01`, `SRC-001`) and
their appendix rows are consistent before rendering to Word.

## Script Location

```text
scripts/cfgi_markdown_to_word.py
```

## Commands

Default conversion (builds a cover page):

```bash
python scripts/cfgi_markdown_to_word.py input.md
```

Named output:

```bash
python scripts/cfgi_markdown_to_word.py input.md -o output.docx
```

Insert a generated Table of Contents:

```bash
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --include-toc
```

Landscape orientation (useful for wide appendix tables):

```bash
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --landscape
```

Skip the generated cover page:

```bash
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --no-cover
```

The converter is opinionated and takes no JSON style configuration — the CFGI
house style is fixed.

## What the Converter Applies

- **CFGI green house style** — Calibri body, dark-green title, green headings
  with a rule under each H1, green table header rows that repeat across pages.
- **Cover page from the Document Profile table** — the first H1 becomes the
  cover title and the `Document Profile` table is lifted onto the cover as a
  summary card, then suppressed inline so it is not duplicated. `--no-cover`
  disables this and leaves the profile in the body.
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
