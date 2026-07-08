# M1 — Template rewrite: single-H1, flat-H2

**Depends on:** none. **Blocks:** M2, M3, M4.

## Goal

Rewrite `skills/consult-drafter/reference/Template.md` and the drafter
`SKILL.md` structure rules to the heading contract in `tickets/README.md`:
one `#` title, every section `##`, procedures as `##` with A–H at `###` and
steps at `####`, derived sections as un-numbered `##`.

## Why

The current template mixes H1 as both title and section divider, with
procedures as H2 nested under H1 group headers. That mixed hierarchy is what
forces the splitter's heuristics. Flattening to one-title + flat-H2 is the
precondition for the dead-simple splitter (M2).

## Changes

`skills/consult-drafter/reference/Template.md`:
- Single `#` title at top (the only H1).
- Drop the group-header H1s (`# Current-State Process Documentation`,
  `# Step-by-Step Procedures`, `# Roles & Responsibilities`, `# Systems…`,
  `# Key Dependencies`, `# Appendix …`) — promote each to `##`. Grouping is now
  carried by manifest `group`, not by headers.
- Frontmatter sections (Document Profile, How to Use, Document Control, Source
  Materials) become `##`.
- Each procedure becomes `## <Plain Title>` (NO leading `1.1` in the heading —
  the number is derived). A–H sub-sections `###`, steps `####`.
- Derived sections (Roles & Responsibilities, Systems & Data Inputs, Key
  Dependencies, Appendix A–D) become `##`, each annotated as tool-owned with a
  one-line HTML comment marker, e.g. `<!-- derived: gap-log; writer: python -->`
  so the drafter and reviewers know not to hand-edit them.
- Keep the "In-Scope Sub-Processes / L3 Procedures" table and "Process Flow
  Summary" — mark whether they are human- or tool-maintained (recommend:
  tool-maintained index, derived from the procedure set).

`skills/consult-drafter/SKILL.md`:
- Update "Canonical Structure", "Procedure Module Rules", and "Numbering
  Convention" sections to the flat-H2 model.
- State explicitly: procedure headings carry the plain title only; the `N.M`
  number is assigned/derived downstream, not typed into the heading.
- State the derived sections are generated, not drafted by hand.

## Acceptance

- `Template.md` contains exactly one `#` line.
- Every non-title section heading is `##`; no `#` other than the title.
- A procedure's A–H are `###` and its steps `####`.
- Each derived section carries a `<!-- derived: … -->` marker.
- The drafter SKILL text no longer instructs typing `1.1` into headings and no
  longer references group-header H1s.
- Manual check: the template, when split at every `##` (M2), yields exactly one
  fragment per intended section with no orphaned content.

## Out of scope

Assigning numbers, generating derived content — those are M2/M3/M5.
