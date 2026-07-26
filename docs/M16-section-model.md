# M16 — Section model: one home per fact

> **Status: DESIGNED.** Supersedes M15, which is retired into this ticket
> (see "What M15 contributed" below).

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
