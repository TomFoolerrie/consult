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

The CFGI converter stays the `consult-docx-builder` skill's script, but the
orchestrator invokes rendering as `python3 scripts/render.py <area>` — a thin
top-level entrypoint that imports `doc_model.assemble` + the converter (keeps all
orchestrator-invoked scripts under `scripts/`, per the README script layout).

`skills/consult-docx-builder/scripts/cfgi_markdown_to_word.py` (+ `scripts/render.py` wrapper):
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

### `scripts/render.py` (the assembly glue — new)

Thin top-level entrypoint: `python3 scripts/render.py <area> -o <out.docx>`
(pass-through `--include-toc` / `--landscape` / `--no-cover`). It does the real
assembly glue and delegates all styling to the converter:

1. Resolve input: an area **folder** is a dir containing `manifest.json` (looked
   up as `<area>`, then `components/<area>`); anything else is a single `.md`
   for back-compat.
2. Folder path: `doc_model.load_manifest` + `validate_manifest`,
   `doc_model.display_numbers(manifest)` (the ONE number map),
   `doc_model.assemble(folder)` → `AssembledDoc(title, subtitle, sections[])`.
3. For each section: strip the fenced `consult-meta` block, strip
   `<!-- derived: … -->` markers, resolve `[[slug]]` via `doc_model.resolve_tokens`
   against the number map; prefix `role == "procedure"` headings with their
   `number`. Lift the `document-profile` static section into the cover card
   (unless `--no-cover`, which leaves it inline).
4. Hand the assembled body + manifest title/subtitle/profile to the converter's
   `convert_assembled` hook. Single-file input calls the legacy `convert`.

### Converter change points (minimal, in `cfgi_markdown_to_word.py`)

Precise edits — **not** a rewrite of the 774-line converter:

- **H1→H2 weight remap:** in the heading branch of the render loop, the
  section-start green rule was `if style == "Heading 1": para_bottom_border(p)`.
  Broaden to `if style in ("Heading 1", "Heading 2"):` so flat-H2 sections carry
  the section weight while single-file H1 docs still get the rule. H3/H4 and the
  Heading-2 style spec are unchanged; table-kind and callout detection key off
  content (not heading level), so they are undisturbed. (A heavier restyle of
  the `Heading 2` spec, or a page-break-before policy, is optional and deferred —
  the rule hook is the load-bearing change.)
- **Loop extraction:** the render `while`-loop is lifted verbatim into
  `render_body(doc, lines, do_cover)`; the TOC block into `_emit_toc(doc)`.
  `convert` is unchanged behaviourally (calls both).
- **Additive `convert_assembled(body_md, out, *, title, subtitle, profile_md,
  include_toc, landscape, do_cover)`:** builds the cover from the passed
  manifest title/subtitle (no inline-H1 scan) and parses `profile_md` into the
  Document Profile card via the existing `md_table`; renders `body_md` through
  `render_body(..., do_cover=False)` (nothing to suppress — the assembled body
  has no inline H1 and the profile is already lifted by `render.py`).

### `skills/consult-docx-builder/SKILL.md` + `references/docx_build_contract.md`:
- Document folder input, single-H1 expectation, manifest-derived numbering, and
  `[[slug]]` token resolution.

### Assumptions on the M2 `doc_model` contract (verify at integration)

M2 owns `doc_model.py`; M4 imports it. `render.py` assumes:
- `AssembledDoc` exposes `.title`, `.subtitle`, and an ordered `.sections`
  iterable; each section exposes `heading`, `role`, `slug`, `number`, `body`.
  `render.py` reads these tolerantly (dataclass *or* dict; `.sections` falls back
  to `.components`) so a minor shape difference doesn't break it.
- `resolve_tokens(text, numbers, mode)` — `render.py` calls it with `mode`
  `"number"` and falls back to a two-arg call if M2's signature has no mode.
If M2 finalizes different names, adjust the shims in `render.py` (`_attr`,
`_sections`, `_resolve_tokens`) only.

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
