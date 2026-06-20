# DOCX Build Contract

The builder expects finalized Markdown as input.

## Supported Input

- `.md`
- `.markdown`
- `.txt`

## Script Interface

```bash
python scripts/cfgi_markdown_to_word.py input.md
python scripts/cfgi_markdown_to_word.py input.md -o output.docx
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --include-generated-toc
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --config style_overrides.json
python scripts/cfgi_markdown_to_word.py input.md -o output.docx --landscape
```

## Out of Scope

- Drafting content
- Cleaning transcripts
- Resolving comments
- Inserting screenshots
- Creating missing evidence
