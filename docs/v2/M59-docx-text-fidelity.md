# M59 — Docx text fidelity: the builder stops eating prose

**Status: RECORDED** (not scheduled).
Origin: the adversarial review of `main` @ 8b22e9e (2026-08-20),
findings F-04, F-09, F-20 — F-04 reproduced end-to-end through a real
docx build.

## Why

Three defects in `skills/consult-docx-builder/scripts/
cfgi_markdown_to_word.py` mutilate authored content on its way into the
client deliverable — the worst kind of failure here, because the docx
is what the client actually reads:

1. **`clean()` deletes prose between `<` and `>`** (lines 348–353).
   Every rendered unit passes through `re.sub(r"<[^>]+>", "", t)`,
   meant to strip HTML tags — but it matches across arbitrary prose.
   Finance content routinely uses angle brackets for thresholds and
   comparisons: *"Approval ladder: <5k the cost-center owner approves;
   5–25k adds the Controller; >25k routes to the CFO"* renders as
   *"Approval ladder: 25k routes to the CFO"* — not just deletion but
   an affirmatively wrong control description. `html.unescape()` runs
   FIRST (line 349), so even `&lt;`-escaping authors are hit.

2. **Escaped emphasis renders as emphasis** (line 353). `clean()`
   unescapes `\*` and `\_` BEFORE the bold/italic regexes run
   (lines 360–397), so deliberately-literal markers are re-styled and
   deleted: `Mark \*required\* fields` renders "required" in italics
   with both asterisks gone; `use \*.xlsx` loses its asterisk. The
   escape mechanism is silently defeated.

3. **Nested lists render flat** (lines 1178–1179). Every list item gets
   a fixed 0.25" indent regardless of markdown depth; authored
   hierarchy — sub-steps under a step — collapses to one level.

## The shape

### Part A — tag stripping becomes tag-shaped

The HTML-strip regex either goes entirely (survey the corpus: if
nothing legitimately embeds HTML, deletion is pure hazard) or narrows
to *tag-shaped tokens only*: a known-tag whitelist
(`</?(b|i|em|strong|br|u|sub|sup)\b[^>]*>`), case-insensitive, nothing
else. A literal `<5k`, `<client name>`, `debit < credit` passes
through untouched and renders as text. `html.unescape` moves AFTER any
stripping decision so `&lt;` survives as a literal.

### Part B — escapes survive until after emphasis

Backslash escapes are tokenized (placeholder substitution) before the
emphasis regexes run and restored as literal characters in the final
run text. `\*`, `\_`, and `\\` mean what the author wrote, in every
unit type (paragraph, cell, callout, heading).

### Part C — list depth maps to indent

`_is_list_item` / the list branch measure leading indentation (2-space
or 4-space unit, pick one and document it) and set
`left_indent = base + depth * step`. Depth is capped (3 levels) rather
than unbounded. Numbering/bullet glyphs per level follow the CFGI
style contract in `references/docx_build_contract.md`, which gets the
rule written into it.

## The gate

- The approval-ladder repro renders every character: `<5k`, `5–25k`,
  `>25k` present in the extracted document text.
- `&lt;5k` in source renders `<5k`.
- `\*required\*` renders literal asterisks, no italics; `use \*.xlsx`
  keeps its glob.
- A 3-level nested list round-trips with three distinct indents
  (docx_compare or direct XML assertion on `w:ind`).
- The v1 golden compat gate passes untouched — these are new
  assertions over inputs the golden corpus never exercised; any golden
  diff means Part A cut too wide and the ticket stops for a ruling.
