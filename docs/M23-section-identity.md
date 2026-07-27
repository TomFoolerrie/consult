# M23 — Section identity by slug (letters become display)

> **Status: DESIGNED.** Prep for M16 move 1; makes it the LAST section
> migration that ever costs drafter passes.

## Goal

Sections get the same identity/display split procedures and callouts already
have: a **stable slug** is the identity; the **letter** is a render-time
display transform. `[[slug]]` : display number :: section slug : section
letter.

## Why

The thesis review flagged M16 move 1 as the ticket set's one real drift:
sections are identified by their letter — display position baked into every
`###` heading. Consequences, all measured or reproduced this session:

- Re-lettering (M16 move 1's A–H → seven-section rename) costs a ~15-pass
  full re-draft, and would cost the same again on the NEXT reshape.
- M14 profiles silently re-key: `body_omit: [F, H]` means different sections
  before and after the rename — config whose meaning depends on which ticket
  has landed.
- Every home-section rule (CONTROL→F, PP/IO→H) is written against a letter
  that is really a position.

## Design

1. **A section registry** (natural home: the shared spine, `doc_model.py` /
   `client_config.py` — builder's call, document it): slug → canonical title,
   e.g. `overview`, `quick-reference`, `prerequisites`, `inputs`, `steps`,
   `controls`, `outputs`, `issues`. The current A–H set maps 1:1; M16 move 1
   later becomes a registry edit (merge/rename entries) plus a content wave.
2. **Fragments carry the title, never the letter**: `### Process Overview`,
   not `### A. Process Overview`. The letter is assigned at render from the
   profile's `sections:` order — same machinery as procedure display numbers.
3. **Profiles reference slugs.** `sections:`, `body_omit:` and the mandatory
   set are slug lists; the letter aliases (`A`, `F`, `H`) remain accepted at
   parse time and are canonicalized to slugs, so existing profiles keep
   meaning the same sections through any future rename.
4. **Home-section rules re-key to slugs** (CONTROL→`controls`, PP/IO→`issues`)
   in callouts/aggregate/reconcile — grep for letter literals; each is a bug
   of exactly this class.
5. **Migration is mechanical**: strip the letter prefix from every existing
   fragment heading (a script, not a drafter — titles are unchanged, so this
   is pure identity work; zero judgment, zero content). Scaffold emits
   letterless headings from the registry. The `reprofile` drift detector keys
   on slugs and keeps working.

## Acceptance

- A rendered document is byte-identical in lettering to today (A–H assigned
  from default profile order).
- Reordering `sections:` in a profile re-letters the render with zero
  fragment edits.
- `body_omit: [controls]` and `body_omit: [F]` mean the same section.
- The migration script converts the live run-2 area; reconcile clean; render
  letter-identical.
- No letter literal survives in scripts/ home-section logic (grep-clean).
- M16 move 1's re-letter is demonstrably a registry + profile edit (a test
  renames/merges in the registry and re-renders without touching fragments —
  the CONTENT mergers stay a drafter wave, out of scope here).

## Out of scope

- M16 move 1's content changes (A-shrink, B-table, C+D merge) — the wave
  that follows this ticket.
- Changing any section's title or count (this ticket is identity plumbing;
  the current A–H maps 1:1).
