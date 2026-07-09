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
- **Per-procedure A–H — callout homes (no separate callout block):** each callout
  type lives in its semantic section, with the formalized structure defined in
  `.claude/agents/consult-drafter.md`:
  - `A. Process Overview` · `B. Quick Reference` · `C. Pre-Requisites` ·
    `D. Inputs` unchanged.
  - `E. Step-by-Step` — steps carry judgment-placed inline bolded tags
    (System/Tool · Navigation Path · Fields/Parameters · Expected Result ·
    Evidence Required). **GAP (VALIDATION REQUIRED) and SCREENSHOT callouts live
    inline** at the step they attach to; body gap refs `[[GAP-01 — …]]`.
  - `F. Key Controls` — **CONTROL callouts replace the old controls table.**
  - `G. Outputs` unchanged.
  - `H. Known Issues & Improvement Opportunities` — **PAIN POINT + IMPROVEMENT
    callouts** (this section is the structured source for Appendix A).
- **Appendix A retitled** "Pain Points & Improvement Opportunities" (drop "Risks";
  fed by PP + IO callouts only). Appendix B = gaps, C = screenshots, D = glossary.
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

`skills/consult-drafter/SKILL.md` — **refocus from whole-document to
single-procedure.** The current SKILL drafts an entire multi-procedure document;
the MVP drafter owns ONE procedure and none of the surrounding scaffolding. This
is a rewrite, not a tweak. It must stay consistent with
`.claude/agents/consult-drafter.md` (the def is the contract; the SKILL is the
how-to).

**Remove** (no longer the drafter's job in the MVP):
- Whole-document / front-matter authoring (Document Profile, How to Use, Control,
  Sources) — those are `static` files, human-owned.
- Appendix authoring (A–D) — Appendices are derived views (M3 + the judgment
  agents), never hand-drafted here.
- `split_doc` / `assemble_doc` / "iterating on a large draft" guidance — folders
  are born via M0 scaffold; the drafter fills one fragment.
- Multi-procedure numbering / "In-Scope" / "Process Flow" authoring.

**Keep / refocus onto the single procedure:**
- Evidence discipline (no fabrication; `TBD` + GAP; conflict → GAP) — unchanged
  and central.
- The A–H module rules, updated to the **callout homes**: CONTROL in `F`,
  PAIN POINT + IMPROVEMENT in `H`, GAP + SCREENSHOT **inline in `E`** at their
  step; inline bolded step tags (System/Tool · Navigation Path · Fields/Parameters
  · Expected Result · Evidence Required) by judgment.
- Style, quick-reference, and callout grammar (strict ID grammar, tolerant
  delimiter).

**State explicitly:**
- Procedure headings carry the plain title only; the `N.M` number is derived
  downstream and rendered by the docx builder — never typed into a heading or a
  cross-reference.
- Cross-references to another procedure use the `[[slug]]` token; systems/roles
  are **canonical plain text** (normalized via `_reference/`), with the machine
  binding in the `consult-meta` block — **not** tokens.
- **`H. Known Issues & Improvement Opportunities` IS the structured source for
  Appendix A** (its PP-/IO- callouts) — it is not free narrative to be ignored.
  (Appendix A is retitled "Pain Points & Improvement Opportunities"; no "Risks".)
- Callout IDs are **procedure-local** (`CTRL-001` restarts per procedure), safe
  under parallel fill, and are **never renumbered** on update (removals leave the
  number retired).
- The drafter is the procedure's **durable owner** (first-draft and update): on
  update it works newly-known facts in and **removes** the GAPs they close,
  leaving no resolved-gap artifacts.

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
- The drafter SKILL no longer contains whole-document, appendix-authoring, or
  split/assemble guidance; it describes a single-procedure fill with the callout
  homes (CONTROL→F, PP/IO→H, GAP/SC inline in E) and inline step tags.
- The drafter SKILL and `.claude/agents/consult-drafter.md` are consistent (no
  contradiction — e.g. H is stated as the Appendix-A source in both).
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
- **#9 (Appendix A double source — superseded):** originally H was declared
  narrative-only to avoid a double-write. Now PP/IO **callouts live in H** as the
  single structured source for Appendix A — so there is no free narrative to
  compete with them, and the double-write is avoided by there being one source,
  not by ignoring H.
