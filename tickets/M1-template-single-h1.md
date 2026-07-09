# M1 — Template rewrite: single-H1, flat-H2, A–H skeleton source

**Depends on:** none. **Blocks:** M0 (scaffold), M2, M3, M4.

## Goal

Rewrite `skills/consult-drafter/reference/Template.md` and the drafter
`SKILL.md` structure rules to the heading contract in `tickets/README.md`:
one `#` title, every section `##`, procedures as `##` with A–H at `###` and
steps at `####`, derived sections as un-numbered `##`. The per-procedure A–H
block doubles as the **skeleton M0's `scaffold.py` stamps out** — so the
template is the single definition of procedure shape, consumed by both the
drafter and the scaffolder.

## Why

The current template mixes H1 as both title and section divider, with
procedures as H2 nested under H1 group headers. That mixed hierarchy is what
forces the splitter's heuristics. Flattening to one-title + flat-H2 is the
precondition for the dead-simple splitter (M2) and for a clean scaffold (M0).

## Changes

`skills/consult-drafter/reference/Template.md`:
- Single `#` title at top (the only H1), with the italic tagline immediately
  under it as the **subtitle** (both are carried into the manifest by M2 —
  neither must evaporate; the docx cover reads title + subtitle).
- **Delete** the pure wrapper headers that own no content of their own —
  `# Current-State Process Documentation` and `# Step-by-Step Procedures`. Their
  child sections become top-level `##` directly.
- **Promote** the content-owning sections to `##`: Roles & Responsibilities,
  Systems & Data Inputs, Key Dependencies, each Appendix. Their subsections
  (e.g. Role Dictionary, RACI) become `###`.
- Assign a role to the former Current-State children explicitly:
  - **Process Overview / Purpose** → a `## Process Overview` section, `role:
    static` (human-authored narrative).
  - **In-Scope Sub-Processes / L3 Procedures** table → **removed from the
    human template**; it becomes the python-owned derived `procedure-index`
    (M3). Do not leave a hand-edited copy.
  - **Process Flow Summary** → **dropped for the MVP** (note it as deferred; it
    has no clean owner and isn't needed for a working system).
- Frontmatter sections (Document Profile, How to Use, Document Control, Source
  Materials) become `##`, `role: static`.
- Each procedure becomes `## <Plain Title>` — **no leading `1.1` in the
  heading** (the number is derived and rendered late). A–H sub-sections `###`,
  steps `####`.
- Each procedure ends with an empty **`consult-meta` end-matter block** (fenced,
  info-string `consult-meta`, YAML body with empty `systems: []` / `roles: []`)
  per the README contract. The fill agent populates the registry slugs; the docx
  builder skips it. State in the SKILL that this block is the machine binding for
  nouns and must list the registry slugs the procedure uses.
- Derived sections carry a one-line marker so humans/reviewers know not to
  hand-edit them and so reconcile can verify ownership:
  `<!-- derived: gap-log; writer: python -->`,
  `<!-- derived: roles; writer: agent -->`, etc.
- Optional per-procedure grouping marker `<!-- group: 2 -->` when an area needs
  the `2.x` cluster; absent → group 1.

`skills/consult-drafter/SKILL.md`:
- Update "Canonical Structure", "Procedure Module Rules", and "Numbering
  Convention" to the flat-H2 model.
- State explicitly: procedure headings carry the plain title only; the `N.M`
  number is derived downstream and rendered by the docx builder, never typed
  into the heading or into any cross-reference.
- State that cross-references to another procedure use the `[[slug]]` token, and
  that systems/roles are written as **canonical plain text** (normalized via the
  `_reference/` registry), **not** tokens.
- State the derived sections are generated, not drafted by hand; the H. Known
  Issues section is free narrative and is **not** a data source for Appendix A
  (the inline `PP-`/`IO-` callouts are).
- State that callout IDs are **procedure-local** (`CTRL-001` restarts per
  procedure), safe under parallel fill.

Split the per-procedure A–H block into a standalone, parameterizable snippet
(`reference/procedure_skeleton.md` or a clearly-delimited region) so M0's
`scaffold.py` can stamp it per procedure without re-parsing the whole template.

## Acceptance

- `Template.md` contains exactly one `#` line, with its subtitle tagline on the
  next non-blank line.
- No wrapper H1s remain; every non-title section heading is `##`.
- A procedure's A–H are `###` and its steps `####`.
- Each derived section carries a `<!-- derived: KIND; writer: W -->` marker.
- No In-Scope table and no Process Flow table remain hand-editable in the
  template.
- The drafter SKILL text no longer instructs typing `1.1` into headings, no
  longer references group-header H1s, and documents `[[slug]]` cross-refs.
- Manual check: splitting the template at every `##` (M2) yields exactly one
  fragment per intended section with **no empty wrapper fragments** and no
  orphaned content.

## Out of scope

Assigning numbers, generating derived content — M2/M3/M5.

## Adversarial review resolutions

- **#6 (subtitle):** title + tagline preserved and routed to the manifest.
- **#12 (drop-vs-promote contradiction):** wrapper H1s are *deleted*; only
  content-owning sections are *promoted*. No empty wrappers.
- **#5 (orphaned Process Overview / In-Scope / Process Flow):** Process Overview
  = `static`; In-Scope = python-derived (M3); Process Flow = dropped.
- **#9 (Appendix A double source):** H. Known Issues declared narrative-only,
  not parsed.
