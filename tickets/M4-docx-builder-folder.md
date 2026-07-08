# M4 — docx builder: single-H1 + folder input

**Depends on:** M1 (heading contract), M2 (internal assemble). Independent of M3.

## Goal

Update `cfgi_markdown_to_word.py` for the single-H1 template and let it consume
a component **folder** (assemble-in-memory → render), not just a single `.md`.

## Why

The converter currently keys visual structure off H1 (first H1 = cover title,
rule under every H1). Under the flat-H2 contract there is exactly one H1 (title)
and all sections are H2, so section-level visual weight must move to H2. And
since the assembled `.md` is no longer an artifact (M2/M3), the builder should
render straight from the folder.

## Changes

`skills/consult-docx-builder/scripts/cfgi_markdown_to_word.py`:
- **Input:** accept either a single `.md` (back-compat) or a folder containing
  `manifest.json`. For a folder, assemble in memory via M2's
  `assemble(folder)` (import, don't shell out) then render.
- **H1/H2 remap:** the single `#` title still drives the cover. H2 sections now
  get the section-break / heading weight formerly carried by H1 (rule under
  each H2 section start, page-break policy as appropriate). H3/H4 unchanged.
- **Derived-section markers:** strip the `<!-- derived: … -->` HTML comments so
  they don't leak into the Word output.
- **Procedure numbering:** render the derived display number (`1.1`) as a prefix
  on each procedure section heading, computed from the manifest (`{group}.{seq}`)
  — the number appears in Word even though it isn't in the source heading.
- Keep everything else: CFGI green house style, cover from Document Profile,
  callouts colored by label, tables auto-styled by kind, screenshots as
  placeholders, `--include-toc` / `--landscape` / `--no-cover`.

`skills/consult-docx-builder/SKILL.md` + `references/docx_build_contract.md`:
- Document folder input, the single-H1 expectation, and manifest-derived
  numbering.

## Acceptance

- `python cfgi_markdown_to_word.py <folder>` renders a `.docx` from the manifest
  order with a cover page and correct section hierarchy.
- Single-file input still works (back-compat).
- Procedure headings in the `.docx` show `1.1`, `1.2`, `2.1`, … derived from the
  manifest; no `<!-- derived -->` comment text appears anywhere in the output.
- H2 sections render with section-level weight (not buried as sub-headings).
- TOC / landscape / no-cover flags still function.

## Out of scope

Generating any content; the aggregator (M3) and agents (M5).
