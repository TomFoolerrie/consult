---
name: consult-docx-builder
description: Convert finalized SOP Markdown into Word .docx files using the bundled Markdown-to-Word Python script.
---

# DOCX Builder Skill

## Purpose

Convert finalized Markdown SOP deliverables into `.docx` files using the bundled Python script.

## Use This Skill When

Use this skill when the user asks to:

- Convert SOP Markdown to Word
- Generate a `.docx` from a finalized SOP draft
- Apply the Word conversion script
- Create a Word deliverable from Markdown

Do not use this skill to draft the SOP, clean transcripts, audit evidence, or resolve comments.

## Required Inputs

- Finalized Markdown file, usually produced by `sop-drafter`
- Optional output filename
- Optional JSON style/config override

## Script Location

The conversion script should be located at:

```text
scripts/cfgi_markdown_to_word.py
```

## Commands

Default conversion:

```bash
python scripts/cfgi_markdown_to_word.py input.md
```

Named output:

```bash
python scripts/cfgi_markdown_to_word.py input.md -o output.docx
```

Include generated TOC:

```bash
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --include-generated-toc
```

Use config override:

```bash
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --config style_overrides.json
```

Use landscape orientation:

```bash
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --landscape
```

## Workflow

1. Confirm the Markdown file exists.
2. Confirm the Markdown appears finalized enough for Word conversion.
3. Select output filename if not provided.
4. Run the script.
5. Confirm the `.docx` was created.
6. Tell the user the output file path.

## Pre-Conversion Checklist

Before running conversion, check:

- Markdown has a document title.
- Canonical sections are present.
- Tables use GitHub-style Markdown tables.
- Screenshot placeholders are text placeholders, not unresolved image links unless intentionally supplied.
- Appendix C and Appendix D are present when gaps or screenshot placeholders exist.

## Output Naming

Use a clean filename:

```text
[process-name]_sop_v[version].docx
```

If version is unknown, use:

```text
[process-name]_sop_draft.docx
```
