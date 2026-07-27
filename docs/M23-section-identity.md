# M23 — Section identity by slug (letters become display)

<<<<<<< HEAD
> **Status: DESIGNED.** Prep for M16 move 1; makes it the LAST section
> migration that ever costs drafter passes.
=======
> **Status: BUILT.** All five design points; prep for M16 move 1, which is now
> the LAST section migration that ever costs drafter passes. Deltas from this
> design:
> - **Registry home: `doc_model.py`** (the shared spine), for the reason
>   `display_numbers` lives there — it is read by every engine and must have one
>   definition. `client_config.py` imports it and keeps owning the PROFILE
>   (`ALL_SECTIONS` is now `doc_model.SECTION_SLUGS`); the letter is to a section
>   what `1.1` is to a procedure, so identity and display sit in one module.
> - **One heading parser, `doc_model.section_of_heading`.** Render, aggregate,
>   scaffold, kits and the advisor's drift guard all ask it, so "which section is
>   this heading?" cannot be answered two ways.
> - **TRANSITION CONTRACT — both forms parse; the migration is NOT a
>   prerequisite.** `### Process Overview` resolves by title; `### A. Process
>   Overview` resolves by title too; `### F. <local wording>` resolves by the
>   LETTER (frozen alias). An unmigrated area renders, aggregates, reconciles and
>   drift-checks exactly as before, and a HALF-migrated area is coherent (tested).
>   The alternative — migration as a hard gate — was rejected: it would have made
>   this ticket a flag day across every existing area for zero behavioral gain.
> - **Rendered TITLE comes from the registry when the heading resolved by title**
>   (which is what makes a future rename a registry edit that shows up in the
>   document with zero fragment edits), and is left exactly as authored when only
>   the letter resolved it — local wording is not this transform's business.
> - **`SECTION_TITLE_ALIASES`** (empty today) is the hook a rename uses so
>   already-drafted fragments keep resolving after their title changes. Acceptance
>   bullet 6's test performs a rename + a merge through it and re-renders without
>   opening a fragment.
> - **Reordering/dropping now RE-LETTERS.** M14 canonicalized `sections:` to
>   document order and left letter gaps when a section was dropped; the letter is
>   position now, so `sections:` order is honored and dropping `controls` makes
>   `outputs` F rather than leaving F empty. That is acceptance bullet 2, and it
>   supersedes M14's "reordering is out of scope".
> - **Letter literals found and re-keyed** beyond the ticket's list: `kits.py`
>   (`subs["B"]` for the Quick Reference preparer) and `orchestrate.py` (guard
>   4.5's `### [A-Z].` drift regex — the `reprofile` detector, now slug-keyed).
>   `review_extract.py` keeps its letter regex on purpose: it reads the RENDERED
>   docx, where letters are the truth. A grep-clean test guards the class.
> - **One reader-visible text change:** the two mechanical registers' captions
>   said "from the `H` section callouts"; they now name the section by TITLE
>   ("from the Known Issues & Improvement Opportunities section callouts").
>   Lettering itself is byte-identical.
> - **`report_line` reports both halves** (`sections A=overview B=quick-reference
>   …`): sections are slugs now, so the diagnostic has to say what the profile
>   means AND what the reader will see.
> - The migration script is **dry-run by default** (`--write` applies), verifies
>   per file that nothing but the letter prefix changed, and leaves any heading it
>   cannot migrate safely alone.
>
> Tests: `tests/test_section_identity.py` (47). Suite 555 → 602.
>>>>>>> main

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
<<<<<<< HEAD
=======

## Transition contract (as built)

Both heading forms are read correctly, everywhere:

| Fragment heading | Resolves to | How |
|---|---|---|
| `### Process Overview` | `overview` | the registry TITLE |
| `### A. Process Overview` | `overview` | the title (the letter is ignored) |
| `### F. Locally Reworded Controls` | `controls` | the frozen LETTER alias |
| `### Steps` | — | nobody's title, no letter: not a section heading |

So migration is a tidy-up, not a gate. Run it per area when convenient:

    python3 scripts/migrate_sections.py components/<area>            # dry run
    python3 scripts/migrate_sections.py components/<area> --write    # apply

It is idempotent, touches only `role: procedure` fragments, changes nothing but
the `X. ` prefix, and preserves line count (so M10 provenance stays aligned).
>>>>>>> main
