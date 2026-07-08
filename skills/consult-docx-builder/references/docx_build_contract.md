# DOCX Build Contract

The builder renders finalized `consult-drafter` process-documentation Markdown
into a CFGI-styled Word document. It styles and renders only — it does not author,
edit, or reconcile content.

## Supported Input

- `.md`
- `.markdown`
- `.txt`

## Script Interface

```bash
python scripts/cfgi_markdown_to_word.py input.md
python scripts/cfgi_markdown_to_word.py input.md -o output.docx
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --include-toc
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --landscape
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --no-cover
```

If `-o/--output` is omitted, the output path is the input stem plus
`_process-doc.docx`.

## Input Expectations

- The document opens with an H1 title.
- A `Document Profile` table supplies the cover-page summary card. Recognized
  rows include Client / Organization, Process Name, Version, Date, Prepared By,
  Document Owner, Classification, and Status.
- Headings follow the canonical `consult-drafter` hierarchy (`#`–`####`).
- Callouts use the canonical labels: `CONTROL`, `VALIDATION REQUIRED`,
  `PAIN POINT`, `IMPROVEMENT OPPORTUNITY`, `SCREENSHOT PLACEHOLDER`.
- Tables are GitHub-style Markdown or simple HTML tables.

## Styling Guarantees

- Fixed CFGI green house style (no JSON config override).
- Cover page generated from the H1 title and `Document Profile` table, then that
  section is suppressed inline (unless `--no-cover`).
- Heading levels map straight through to Word Heading 1–4.
- Callout boxes are colored by label; table shading is chosen by table header
  (field, control, gap, screenshot, standard).
- Screenshot references render as placeholder callouts; images are never
  inserted.

## Out of Scope

- Drafting or editing content
- Cleaning transcripts
- Reconciling or validating IDs (done upstream by `consult-drafter`)
- Resolving comments
- Inserting real screenshots or evidence
- Slide or graphic production
