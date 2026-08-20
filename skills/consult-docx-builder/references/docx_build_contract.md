# DOCX Build Contract — single-file CLI

This file documents the converter's **single-file CLI** only. The primary
production path is the folder pipeline (`scripts/render.py <area>`, which calls
`convert_assembled` with modes, subset renders, tracked changes, and
provenance) — see SKILL.md for that. The builder styles and renders only — it
does not author, edit, or reconcile content.

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
- An image link whose file exists on disk is embedded (scaled to page width,
  italic caption below); a dangling path renders as a screenshot placeholder
  callout, never a broken image.
- Ordered lists follow CommonMark semantics: a contiguous run is one list
  seeded by its first literal number; any break restarts numbering.
- Nested lists keep their depth (M59): the nesting unit is **2 spaces** of
  leading indentation per level, capped at 3 levels (deeper indentation clamps
  to the third level); each level adds 0.25" of left indent past the 0.25"
  base. Bullets and numbers both follow the rule.
- Text fidelity (M59): only tag-shaped tokens are stripped — HTML comments,
  `<br>`, `<span>`, and the whitelist `</?(b|i|em|strong|u|sub|sup)>` — so
  angle-bracket prose (`<5k`, `debit < credit`, `<client name>`) renders as
  written, and `&lt;`-style entities unescape to literal text after the
  stripping decision. Backslash escapes (`\*`, `\_`, `\|`, `\\`) always render
  as the literal character, never as emphasis or structure.

## Out of Scope

- Drafting or editing content
- Cleaning transcripts
- Reconciling or validating IDs (done upstream by `scripts/reconcile.py`)
- Resolving comments
- Slide or graphic production
