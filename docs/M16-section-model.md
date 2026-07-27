# M16 — Section model: one home per fact

> **Status: BUILT — moves 3, 4, 2, and move 1's REGISTRY half.** Move 1's
> **CONTENT WAVE is PENDING** (a drafter pass per fragment). Supersedes M15,
> which is retired into this ticket (see "What M15 contributed" below).
>
> **Move 1, registry half (as built).** M23 made this a registry edit, and it
> was: `doc_model.SECTION_TITLES` is now the seven-section set, and no fragment
> was opened.
>
> Slug mapping — a slug is IDENTITY, so it changes only where the section's job
> did:
>
> | Was (slug / title) | Is (slug / title) | Letter |
> |---|---|---|
> | `overview` / Process Overview | **`scope`** / **Scope** | A |
> | `quick-reference` / Quick Reference | `quick-reference` / **At a Glance** | B |
> | `prerequisites` / Pre-Requisites | **`before-you-start`** / **Before You Start** | C |
> | `inputs` / Inputs | **`before-you-start`** (merged) | C |
> | `steps` / Step-by-Step Procedure | `steps` / **Procedure** | D |
> | `outputs` / Outputs | `outputs` / **Outputs & Evidence** | E |
> | `controls` / Key Controls | `controls` / Key Controls (job unchanged; "Controls" is an accepted alias title) | F |
> | `issues` / Known Issues & Improvement Opportunities | unchanged | G |
>
> - **`SECTION_TITLE_ALIASES` carries every pre-M16 title** (`Process Overview`,
>   `Quick Reference`, `Pre-Requisites`, `Inputs`, `Step-by-Step Procedure`,
>   `Outputs`, plus the docx builder's legacy `Known Issues / Improvement
>   Notes`), and a new **`SECTION_SLUG_ALIASES`** carries the pre-M16 SLUGS
>   (`overview`, `prerequisites`, `inputs`) as profile input. So every drafted
>   fragment and every hand-written `profile.yaml` keeps resolving: the rename
>   half cost **zero fragment edits**, exactly as M23 promised.
> - **Outputs moved ahead of Controls** (E and F), per the table below. This is
>   the one ordering change, and it is why a legacy `sections: [A…H]` letter list
>   re-letters `controls` to E: the letters are frozen at their historical
>   MEANING, not at the new positions.
> - **`body_omit: [F, H]` still means controls + known-issues.** M23 design
>   point 3 ("existing profiles keep meaning the same sections through any future
>   rename") deliberately overrides this ticket's `body_omit: [F, G]` prose:
>   `SECTION_LETTER_ALIASES` is frozen, so `G` still means `outputs` even though
>   `outputs` renders as E. Write slugs in new profiles.
> - **Mandatory set is `scope` / `quick-reference` / `steps`** (A/B/D — the card
>   and the procedure), per "Interaction with M14".
>
> **Two headings, one slug — the transition, pre-content-wave.** A fragment
> drafted before the wave carries both `### Pre-Requisites` and `### Inputs`, and
> both resolve to `before-you-start`. The behaviour is **tolerate + report, never
> fail** (`doc_model.duplicate_sections` is the one scanner):
> `aggregate.split_subsections` **concatenates** the two bodies in document order
> (no fact is lost, every register still sees its content); render letters both
> headings `C` and gives the registry title to the **first only**, so the second
> stays visibly as authored (`C. Inputs` under `C. Before You Start`);
> `reconcile` emits a **WARNING** naming the fragment, the merge and the work
> order, so the state is loud but exit stays 0. Erroring would wedge every
> already-drafted area on what was supposed to be a registry edit, and the wave
> is imminent.
>
> **The content wave's work order** is `"Content wave: 8 → 7 sections (M16 move
> 1)"` in `skills/consult-drafter/SKILL.md` — the per-fragment migration
> procedure (A keeps scope/exclusions/adjacent slugs only; B becomes the table;
> C+D merge one line per artifact; E→Procedure and G→Outputs & Evidence are
> retitles; H stays defects-only), under two standing rules: no content invented,
> no facts lost. Drafters report `sections_merged` + `facts_relocated`.
> `agents/consult-drafter.md` points at it and carries the seven declared jobs.
>
> Also as built: `parse_bullets` reads the At a Glance card as a bullet list OR a
> two-column table, so retabling B in the wave never costs a register its
> preparer. Tests: `tests/test_section_identity.py` grew the seven-section
> registry, the frozen-alias and old-model-fragment cases; suite 602 → 612.
>
> What shipped, in the recommended order:
>
> - **Move 3 — callout `note:` / `detail:`.** Both are ordinary callout
>   sub-fields (`callouts.py` owns the two field names and the set of kinds that
>   may carry a detail). `render.py` blanks `detail:` out of the procedure body,
>   line-count-preserving like every other body transform; `aggregate.py`'s
>   register builders append it to the row's description cell, reading the
>   FRAGMENT so a detail still reaches its register when `body_omit` hides its
>   home section. `reconcile.py` fails a `detail:` with no `note:` (the inline
>   view would be empty) and warns on a `detail:` on CONTROL / SCREENSHOT
>   PLACEHOLDER. Absent `detail:`, every transform is the identity.
> - **Move 4 — the `Condition:` step tag.** `Condition` heads
>   `client_config.DEFAULT_INLINE_TAGS`, and render hoists the tag to the head of
>   the step body when a fragment authored it below the prose. The drafter
>   contract asks for it to be authored there in the first place, which keeps the
>   hoist a no-op and M10's line-for-line provenance exact.
> - **Move 2 — tag on change.** Contract-only, as designed: no code. The rules
>   live in `agents/consult-drafter.md` and `skills/consult-drafter/SKILL.md`,
>   written as a pass an UPDATE-mode drafter can run against an existing
>   fragment. Python still never enforces the tag vocabulary.
>
> **Why the wave is still a wave.** The re-LETTER cost nothing (M23), but the
> CONTENT mergers cannot be mechanized: phrasing state-plus-artifact in one line,
> and deciding which of A's sentences is a scope statement and which is a card
> row, is judgment. That is ~15 drafter passes, dispatched per fragment, and the
> pipeline is correct in the meantime — which is the difference between this and
> a flag day.

## Goal

Make the document less tiring to read by ensuring **every fact has exactly one
home**, and that a reader can tell what applies to them without doing branch
analysis. This is a *repetition* fix, not a *length* fix — the two were
conflated in M15 and the distinction matters (see Why).

## Why

The complaint that motivated this was "the reader gets tired and overwhelmed
reading the same fact multiple times, not necessarily because the fact is
long." Measurement on the live P2P area supports the framing and rules out the
alternative explanation.

Words per section across 15 procedures, 35,054 words total:

| | A | B | C | D | E | F | G | H |
|---|---|---|---|---|---|---|---|---|
| words | 2365 | 1768 | 1128 | 1277 | 16847 | 2940 | 1296 | 7433 |
| share | 7% | 5% | 3% | 4% | **48%** | 8% | 4% | **21%** |

So collapsing sections is not a volume lever — C+D+G together are 11% of the
document, and E+H are 69%. If the goal were a shorter document, this ticket
would be the wrong instrument. The goal is a document that doesn't state the
same thing four times before Step 1.

**A is the redundancy engine.** In ~157 words the average `A. Process Overview`
states the preparer, the systems, the trigger, the frequency, the inputs, the
outputs and the scope boundaries. `B. Quick Reference` then restates preparer,
trigger, frequency, systems and outputs. `C` and `D` restate the inputs. `G`
restates the outputs. `E` restates all of it operationally. The reader meets
the same fact three or four times before reaching the first step.

**The structural cause:** A–H is one linear stream serving three different
readers — the preparer (steps, prerequisites, navigation), the reviewer/auditor
(controls, evidence, gaps), and the newcomer (orientation, once). No section
declares its audience, so every section hedges by restating enough context to
stand alone. The repetition is not drafters being verbose; it is the shape
asking each section to be self-contained.

The same pattern repeats below the section level. Inline tag frequency across
the area:

```
80  Expected Result:      ~one per step
74  System / Tool:        almost always "NetSuite"
40  Evidence Required:
25  Fields / Parameters:
11  Navigation Path:      ← the rarest
```

The most useful tag is the rarest. `Navigation Path` is the one thing a
preparer genuinely cannot derive; it appears 11 times. `System / Tool: NetSuite`
is stamped on 74 steps of procedures whose own summary already says the system
is NetSuite — a form field filled because it exists.

## Design

Four coordinated moves. All four are the same principle — *this fact has one
home* — applied at four scales.

### 1. Sections — seven, with declared jobs

| New | Job | From |
|---|---|---|
| **A. Scope** | what this covers, what it explicitly excludes, which procedures adjoin it. **Nothing else** — no preparer, no systems, no trigger. | A, reduced |
| **B. At a Glance** | **a table.** Trigger, frequency, preparer, reviewer, systems, key inputs, key outputs. The single home for those facts. | B, tabled |
| **C. Before You Start** | one line per artifact: what it is, where it comes from, the state it must be in. | C + D merged |
| **D. Procedure** | the steps. | E |
| **E. Outputs & Evidence** | what exists afterwards, what is retained, what is deliberately not retained. | G |
| **F. Controls** | unchanged. | F |
| **G. Known Issues & Improvement Opportunities** | **defects only** — see "H stays defects-only". | H |

The map that makes "say it once, in its home section" enforceable rather than
aspirational: **facts live in the card (B), states live in C, actions live in D,
results live in E.** The rule exists today with no map of homes; this is the
map.

**Why C+D merge.** Nearly every prerequisite is "artifact X exists in state Y",
so splitting state (C) from artifact (D) forces the drafter to invent a
distinction on every entry. Live example, same noun in both sections:

- C: "An item receipt has been posted against the purchase order lines being billed."
- D: "**NetSuite item receipt:** [[goods-receipt]] — supplies the quantity received per line."

Merged: `**NetSuite item receipt** — [[goods-receipt]]; posted against the PO
lines being billed, supplies quantity received per line.` One decision, one
place to read, and the upstream `[[slug]]` links land in one list instead of
split across two.

**Why A shrinks rather than disappears.** Scope boundaries — what is *out*, and
which procedure has it instead — are real content with no other home, and they
carry the `[[slug]]` seam links. Everything else in A today belongs to B.

**Why E (Outputs) survives rather than folding into B.** "Evidence retained"
and negative findings ("no record of the exception investigation is retained")
appear nowhere else and are audit-relevant. What was duplicative is B's
`Key outputs:` summary line — B keeps the one-line headline as a table row,
E keeps the detail.

**B is a table.** Decided. The cost: fields that currently run to prose — the
live `Reviewer:` that spends four sentences explaining that there is no
reviewer — no longer fit. That prose moves to A (if it is a scope statement) or
F (if it is a control statement); the row carries the short answer. Forcing
that split is a feature: a four-sentence table cell is a sign the content was
in the wrong section.

### 2. Tags — declare once, tag on change

`B. At a Glance` declares the procedure's default system. A step tags
`System / Tool` only when it **departs** from that default — to Coupa, to Chase
Connect, to paper. The tag becomes a signal ("you are switching systems here")
instead of wallpaper.

Same test for `Expected Result`: keep where the outcome is non-obvious or is a
decision point; drop where it restates the step title (live example — *"Select
the pending PO invoice from the review queue"* → *"A pending PO bill is open
for entry."*).

Same for the performing role. The card names who performs the procedure;
naming the role in all eight steps is the same fact eight times. Name it only
where it **changes** — the Buyer, the Receiving Supervisor, the Controller —
which is precisely where the reader needs to notice a handoff and where the
constant restatement currently camouflages it.

`Navigation Path` and `Fields / Parameters` are unaffected: they are
step-specific by nature and under-used, not over-used.

This move costs no content and requires no re-drafting judgment beyond the
tags themselves.

### 3. Callouts — `note` inline, `detail` in the appendix

The live `GAP-01` callout is ~300 words — four conflicting accounts of the
match tolerance plus a resolution path — sitting between Step 4 and Step 5.
Excellent content, wrong place: a preparer at Step 4 needs *"tolerance
unconfirmed — do not operate to a figure; see GAP-01"*. The evidence dossier is
for whoever resolves the gap.

The destination already exists (Appendix B is the gap log), but the split is
currently **backwards**: the dossier is inline and the summary is in the
appendix.

Give the callout two fields:

- `note:` — one or two sentences, renders **in the step**.
- `detail:` — the full account, renders **only in the appendix**.

One source of truth, two views — the same projection discipline the rest of the
system uses. No content is lost and `D. Procedure` stops being interrupted by
research memos. Applies to `VALIDATION REQUIRED` and `PAIN POINT`, which are the
two callout kinds that run long; `CONTROL` and `SCREENSHOT PLACEHOLDER` are
already short and take `note` only.

Absent `detail:` → today's behavior (the whole body renders inline).

### 4. Steps — declare conditions, so branches stop reading as sequence

Live step list for PO invoice entry:

```
Step 1  Select the pending PO invoice from the review queue
Step 2  Enter the bill by reference to the purchase order
Step 3  Compare the three legs of the match
Step 4  Apply the matching tolerance
Step 5  Place an out-of-tolerance bill on hold …     ← only if out of tolerance
Step 6  Resolve a quantity exception with receiving  ← only if quantity broke
Step 7  Resolve a price exception with the Buyer     ← only if price broke
Step 8  Complete the matched bill
```

On the normal path a preparer performs 1-2-3-4 then 8. But "Step 5" reads as
"next, do this", so the reader must work out which steps apply to them on every
read. Goods receipt is worse: 11 numbered steps of which 2, 4, 6 and 7 are
conditional, and **Step 8, "Consumption-based automatic receipt at Plant 3", is
not a step at all** — it is a variant of the entire procedure for one site,
sitting at position 8 of 11 as though it follows step 7.

This is a distinct cause of reader fatigue from repetition: the document is
making the reader do branch analysis it should have done for them.

Fix — a `Condition:` inline tag, consistent with move 2:

```
Step 5: Place an out-of-tolerance bill on hold and identify the broken leg
  Condition: the variance exceeds the matching tolerance
```

A step with no condition is main path. Cheap, no renumbering, each branch stays
adjacent to the step that triggers it, and at render the condition leads the
step body so it is visible before the prose. The Plant 3 case gets
`Condition: Plant 3 only`, which is honest about what it is.

### H stays defects-only (considered and ruled out)

A split of H into *defects* vs *normal exception branches* was considered and
rejected: exception **handling** already lives in D as conditional steps, where
it belongs, and H already holds only defects. What H's definition lacks is a
sentence saying so. Added to the drafter contract: *G (formerly H) records
defects in the process — things that are wrong. A branch the process handles
routinely is a conditional step in D, not a known issue.*

### Voice: passive, unchanged

Considered and decided against changing. The active/imperative form ("Enter the
bill by reference to the PO") is ~30% shorter than the current passive, and D is
48% of the document, so this is the largest single length lever available. It is
rejected because this is **current-state documentation, not a work
instruction**: third-person passive describes what the organization does, and
imperative changes the genre in a way that affects how the document reads as an
audit artifact. Recorded here so it is not re-proposed as an oversight.

### Source citations

`(SRC-006 §5.1)` mid-paragraph is scholarly apparatus in an operational text.
Citations move to the end of the step body. Traceability is unchanged; the
sentence stops being broken. Minor and mechanical.

## What M15 contributed (retired into this ticket)

M15 proposed measuring verbosity (`stats.py`, outliers at ≥2× the area median).
Retired: with 15 procedures the median is a thin sample, one legitimately heavy
procedure masks a second, and the ≤0.4× thin-flag mostly fires on procedures
that are short because the process is short — so the output is a thing to
triage rather than a thing that saves time. The signal it was reaching for
(total words per procedure, sorted) needs no median, ratio or outlier
machinery.

Two parts are kept and carried here:

- **Bounded field caps as definitions, not limits** — `A. Scope` 3–5 sentences,
  `Impact:` one sentence, `Severity:` enum (already validated), never restate
  the section title as the first clause of its body. These stay prose rules in
  the drafter contract because they define a field's *job*.
- **No length checks in reconcile.** Reconcile is the correctness gate;
  a style warning there dilutes the signal that currently means "something is
  broken". Recorded as a standing decision.

M15's core reasoning — that the real bloat drivers are structural and belong to
a section's role, not to word budgets — is the premise this whole ticket is
built on.

## Interaction with M14

M14 explicitly puts section identity out of scope ("reordering or renaming
sections — A–H identity is the heading contract"), so this is a separate
ticket, not an M14 setting. But **M14 supplies the migration mechanism for
free**: its drift detector fires on a fragment missing a heading the profile
requires, which is exactly the state a re-lettered area is in. Build M14 first
and the `reprofile` guard reports the dispatch count for M16's migration
before it is spent.

M14's `profile.yaml` `sections:` list becomes the seven-section set; the
mandatory subset changes from A/B/E to **A/B/D** (scope, card, procedure).

M14's `body_omit:` re-letters with them: controls and known-issues become **F** and
**G** in this model (from F and H), so an engagement omitting both from the
procedure body writes `body_omit: [F, G]` after this ticket lands rather than
`[F, H]` before it. The two features are orthogonal — `body_omit` decides whether
a section renders in the body, move 3 decides how much of a *callout* renders
inline — but both are "one home per fact" and should not be confused: move 3 is
for callouts inline in `D`, `body_omit` is for whole sections.

## Cost

The four moves have very different prices, and they are independently
shippable — this is deliberate.

| Move | Cost |
|---|---|
| 3 — callout `note`/`detail` | **render change only**; a drafter pass to split existing long bodies, but no rewriting |
| 4 — `Condition:` tags | one cheap drafter pass; purely additive |
| 2 — tag on change | one cheap drafter pass; mostly deletion |
| 1 — sections | **full re-draft**, ~15 drafter passes. A and C+D cannot be merged mechanically — phrasing state-plus-artifact in one line is a judgment. |

Recommended order: **3, 4, 2, 1** — cheapest and highest readability return
first, and move 1 (the expensive one) can be decided after the others are in
and their effect on the document is visible.

## Acceptance

- **Sections:** a rendered procedure has seven sections; no fact from the B
  table is restated in A; C carries one line per artifact with source and
  required state; reconcile is clean.
- **Tags:** `System / Tool` appears only on steps departing from the card's
  default system; a procedure operating entirely in one system has zero
  `System / Tool` tags in its steps.
- **Callouts:** a `VALIDATION REQUIRED` with `note` + `detail` renders the note
  in the step and the detail in Appendix B, and appears in full exactly once in
  the document. Absent `detail`, output is byte-identical to today.
- **Steps:** every conditional step carries a `Condition:`; reading only the
  unconditioned steps of the three-way-match procedure yields a coherent
  main path.
- **No regression:** `[[slug]]` resolution, display numbering, callout IDs and
  the derived views are unaffected by any of the four moves.

## Out of scope

- Shortening `D. Procedure` or `G. Known Issues` prose — 69% of the document,
  and governed by drafter judgment, not structure.
- Changing voice (decided: passive stays).
- Splitting H (decided: defects-only, definition tightened instead).
- Per-procedure section sets — engagement/area granularity only, per M14.
- Any metric, gate or automatic dispatch derived from length (M15's retired
  half).
