# M42 WP-D2 self-review — population-level ownership (surveyor + librarian)

Scope: `agents/consult-surveyor.md`, `agents/consult-librarian.md`. Normative
source: [`M42-callout-doctrine.md`](../M42-callout-doctrine.md) Part A3 + A6
(population-level paragraph), landing spec Part B2/B3. Intent-diff below, not a
wording diff; tensions are reported, not smoothed.

## Surveyor — the ask agenda (spec A3, Part B2)

| spec point | landing | lines |
|---|---|---|
| the engagement-level "what should we ask the client" agenda belongs to the surveyor, via its information requests, issued before drafting spends tokens | new subsection `### You own the ASK AGENDA (M42 A3)` at the end of the existing INFORMATION REQUESTS section — "THE channel … There is no second one" | `consult-surveyor.md:511–546` |
| downstream drafters mint only operation-blocking GAPs | stated as the *reason* for the ownership, with A3's own examples (number, threshold, owner, control field) and A3's "unconfirmed alone does not mint" | `:518–526` |
| so the surveyor must not leave known thinness unrequested | "thinness you know about and do not request is YOUR miss" + four concrete pre-return checks (every thin/nothing/conflicted node; every `gap_forecast` line that needs the client; a doubted material fact on an `enough` node; the never-ask-what-a-source-answers counterweight) | `:528–546` |
| propagate to the hard rules | new hard rule 11 | `:726–729` |
| do NOT touch the closed reading contract's input list | untouched — no new input admitted; the `objective` input (M41) still the only addition to that list | (no diff) |

Voice: the brief's imperative second person, table-free prose plus a checklist,
matching the surrounding sufficiency/request sections.

### Choices worth flagging

1. **Added two checks the spec does not name.** A3 says the agenda is the
   surveyor's; it does not enumerate how the surveyor proves it discharged the
   duty. The `gap_forecast`-needs-a-request check and the doubted-fact-on-an-
   `enough`-node check are mine. Both close a real hole (a surveyor could
   otherwise satisfy the letter — every thin node has a request — while the
   engagement's actual open questions sat only in a forecast field the client
   never sees). If the ticket wants the prompt to carry Part A verbatim and
   nothing more, delete `:534–543`; the ownership statement stands without them.
2. **Kept the anti-over-asking rule adjacent.** Making unrequested thinness a
   named miss pushes toward asking for everything, which the existing
   "never ask for something a source already answers" bullet forbids. I put the
   two in the same breath rather than letting the new text sit twenty lines
   above the constraint it strains against. The tension is real and is not
   resolved by prose: it is a judgment the surveyor makes per fact.
3. **"Not a safety net under you" is a paraphrase.** The spec states the
   drafter's narrow license as a bar; the surveyor prompt states its
   *consequence for the surveyor*. Same intent, different altitude — flagged
   because doctrine drift between prompts is this ticket's named review risk.

## Librarian — callout population grooming (spec A6, Part B3)

| spec point | landing | lines |
|---|---|---|
| a new trigger, alongside the existing six, same voice | trigger 7, `**CALLOUT POPULATION GROOMING (M42 A6)**`, in the numbered trigger list | `consult-librarian.md:93–142` |
| (a) near-duplicate GAPs across steps asking the same fact | first sub-bullet; names which GAP stays (the step the fact actually blocks) and routes the recurring case to the existing promote-to-register move | `:97–103` |
| (b) a GAP whose fact a tagged source likely answers (ledger holds it, owning step has not consumed it) | second sub-bullet; framed as the cross-answerable gap at callout altitude, routed to retag/adopt, with "say **likely**" | `:104–111` |
| (c) CTRL callouts missing the four minting fields, drafter contract cited as the bar's home | third sub-bullet; names all four fields, cites `agents/consult-drafter.md`, and carries the refusal rule's alternative (completion vs demotion to prose + GAP) | `:112–121` |
| all three are PROPOSALS through the notes bus to the owning drafter or the human; never edits a fragment; deletion/merge proposed never executed | closing paragraph, in the spec's own words ("proposed for deletion, never deleted", "proposed, never executed") | `:122–129` |
| return surface | new `callout_grooming` field with the three kinds as enum values | `:264–267` |

Existing filing mechanics (the `note` command, the `SCOPE PROPOSAL` opening
convention, the owning-slug rule) are reused, not restated.

### Choices worth flagging

1. **Two boundaries added beyond the spec** (`:131–140`): an explicit
   adequacy-is-the-analyst's line, and a note that the mechanical feeder is
   deferred to M43. The first is defensive — "CTRLs missing fields" is one step
   from "this step has no CTRL", which A2/A3 put behind the M39 gate, and a
   grooming trigger without that fence is the noise this ticket exists to
   prevent. The second is the spec's own Deferred entry surfaced where it
   changes behaviour (the candidates are hand-read today, so confidence is
   lower and hard rule 7 bites harder).
2. **The `SCOPE PROPOSAL` prefix does not obviously fit.** Existing convention
   opens every note with `SCOPE PROPOSAL (<move>)`, and a duplicate-GAP merge is
   not a scope move. I did not mint a second convention — one findability
   convention is worth more than precise labelling, and inventing
   `CALLOUT PROPOSAL` would have added a bus vocabulary this ticket did not
   authorise. **Reported, not fixed:** if the reviewer wants a distinct opener,
   it is a one-line change plus the corresponding line in the drafter contract.
3. **The grooming moves reuse the five-move table without extending it.** A
   duplicate-GAP merge is not `split | add | move | merge | retag` (the table's
   `merge` is nodes, not callouts). Rather than widen the table, trigger 7 routes
   its findings to existing moves where one fits (retag, adopt-as-source,
   promote-to-register) and otherwise rides in `callout_grooming`. This is a
   genuine seam: a reviewer could reasonably want a sixth move named `groom`.
4. **No new tool or write path.** Trigger 7 needs to read step fragments
   (`10_*.md`) to see callouts; the librarian already reads them under `--full`
   and via the brief's findings, and hard rule 3 already forbids writing them.
   Nothing in the tools front-matter changed.

## Verification

- `TestPopulationOwnership` 2/2 (the class's anchors: surveyor
  `operation-blocking` / `ask agenda`; librarian `duplicate` + `gap` + `notes`).
- `tests/test_dispatch_hints_m37.py`, `tests/test_objective_m41.py` green —
  `test_surveyor_admits_the_objective_input`'s anchor untouched.
- Other `test_doctrine_m42.py` classes belong to WP-D1/WP-D3 and were not
  touched; no test file edited.
