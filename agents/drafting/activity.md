# Drafting path — an activity (v1, seven sections)

**You are reading this because your dispatch's `YOUR UNIT` line says
`activity`, or because no unit resolved** — this is the default path,
unchanged. This document is one of the two unit paths named by
`agents/consult-drafter.md`; read this one only. Everything in the shared
contract still binds you — evidence discipline, canonical nouns, the callout
bars and callout grammar, conflicting sources, the return format, the
final-mode read-through.

## The map of homes — the seven sections

The shared contract's "say it once" rule needs a map of homes to be
enforceable rather than aspirational. Here it is (M16 move 1): **facts live in
the card (B), states live in C, actions live in D, results live in E.** Seven
sections, each with a declared job:

| | Job |
|---|---|
| **A. Scope** | what this covers, what it explicitly excludes, which procedures adjoin it. **Nothing else** — no preparer, no systems, no trigger. |
| **B. At a Glance** | **a table.** Trigger, frequency, preparer, reviewer, systems, key inputs, key outputs. The single home for those facts. |
| **C. Before You Start** | one line per artifact: what it is, where it comes from, the state it must be in. |
| **D. Procedure** | the steps. |
| **E. Outputs & Evidence** | what exists afterwards, what is retained, what is deliberately not retained. |
| **F. Key Controls** | the control record: one CONTROL callout per control that clears the four-field CTRL bar (shared law), plus prose (never a callout) for a control the sources cannot yet support. Adequacy and key-ness are not judged here. |
| **G. Known Issues & Improvement Opportunities** | **defects only** — see below. |

- **Scope is a primer, not a rundown.** 3–5 sentences: what this procedure
  covers, what it excludes, which procedures adjoin it. No preparer, no systems,
  no trigger, no step detail, no control detail, no pain-point narrative — those
  all have their own sections. A reader should finish A oriented, not informed.
- At a Glance (B) carries the at-a-glance facts, one table row each; don't
  re-narrate them in A. A four-sentence table cell is a sign the content was in
  the wrong section: the prose moves to A (if it is a scope statement) or F (if it
  is a control statement) and the row carries the short answer.
- Before You Start (C) is one line per artifact — name, source (`[[slug]]` where
  an upstream procedure supplies it), required state. Splitting "the state" from
  "the artifact" is the distinction M16 removed; do not reinvent it.
- Outputs & Evidence (E) keeps what B's `key outputs` row cannot: retention, and
  the negative findings ("no record of the exception investigation is retained").
- Controls live in Key Controls, friction in Known Issues, gaps at their step
  in Procedure. A step there may
  *name* the control it triggers; it doesn't re-describe it. Which facts earn a
  callout at all is the shared bars' question — a step break is never
  itself a control record.
- **G stays defects-only.** G records defects in the process — things that are
  wrong. A branch the process handles routinely is a conditional step, not a
  known issue.
- **The same rule governs the inline step tags and long callouts**, one scale
  down: the default system is declared in B and tagged in a step only where it
  changes, and a long callout's full account lives in its appendix register row
  while the step carries a one-line note. See "declare once, tag on change"
  below and "a long callout splits" in the shared contract.

## The M16 content wave — migrating an existing 8-section draft

An `update` pass on a fragment drafted against the old eight-section model
(`Process Overview` … `Known Issues`) is a **content-wave pass**. The registry
already reads those headings, so nothing is broken — what is owed is the judgment
a script cannot do, and reconcile names the fragments still owing it ("AWAITING
THE M16 CONTENT WAVE").

Follow **"Content wave: 8 → 7 sections (M16 move 1)"** in
`skills/consult-drafter/SKILL.md` — the per-fragment procedure, step by step. Its
two standing rules are contract, not guidance: **no content is invented and no
fact is lost** (a sentence stays, moves to its declared home, or is deleted only
as a verbatim duplicate of the same fact in its home section), and callouts,
callout IDs, `SRC-` citations, `[[slug]]` tokens and the `consult-meta` block are
**unchanged** by the pass. Report `sections_merged` and `facts_relocated`.

## What you produce — structure

A finalized `{file}`: the seven-section procedure, current-state, practical for a preparer
to execute and a reviewer to validate. Follow `skills/consult-drafter/SKILL.md`
for the section-by-section prose. Two structural rules are specific to this system:

### Inline step tags (Procedure) — declare once, tag on change
Within a step, add these **bolded tags** only where the detail helps execution,
review, or auditability — not mechanically on every step:

```
- **Condition:** ...
- **System / Tool:** ...
- **Navigation Path:** ...
- **Fields / Parameters:** ...
- **Expected Result:** ...
- **Evidence Required:** ...
```

A tag is a **signal, not a form field**: it earns its place by telling the reader
something the surrounding text does not already say. The rule that decides three
of them is *declare once, tag on change*.

- **`System / Tool` — only on DEPARTURE.** `At a Glance` declares the
  procedure's default system in the card's `Systems` row; that is the fact's
  one home. A step tags `System / Tool` **only where it leaves that default** —
  to Coupa, to Chase Connect, to paper. A procedure that operates entirely in one
  system carries **zero** `System / Tool` tags in its steps. Stamped on every
  step the tag is wallpaper; used only on departure it reads as *"you are
  switching systems here"*.
- **`Expected Result` — only where the outcome is non-obvious, or is a decision
  point.** Never where it restates the step title: *"Select the pending PO
  invoice from the review queue"* → *"A pending PO bill is open for entry"* is
  the same sentence twice — delete it. Keep it where the preparer could not
  predict the outcome, or where the outcome is what the next branch tests.
- **The performing role — name it only where it CHANGES.** B names who performs
  the procedure; repeating that role in all eight steps is one fact eight times,
  and it camouflages the thing the reader actually needs to notice — the
  **handoff**. Name the role at the step where it becomes the Buyer, the
  Receiving Supervisor, the Controller, and nowhere else. (This is prose, not a
  tag; the test is the same.)

`Navigation Path` and `Fields / Parameters` are **unaffected** by this rule: they
are step-specific by nature and under-used, not over-used. `Navigation Path` is
the one thing a preparer genuinely cannot derive — where a source supports it,
write it. `Evidence Required` keeps its own judgment test (where it helps review
or audit).

### `Condition:` — a conditional step declares itself
A step that does not run every time carries a `Condition:` tag. **A step with no
`Condition:` is main path** — that is the whole contract, and it is what lets a
reader follow the normal path without re-deriving the branches on every read.

Write it as the **first line of the step body, directly under the heading, before
the prose**: the condition has to be read before the step, not after it. (Render
hoists a `Condition:` tag it finds below the prose, but authoring it in place is
the contract and the only form that keeps review provenance exact.)

```
#### Step 5: Place an out-of-tolerance bill on hold and identify the broken leg

- **Condition:** the variance exceeds the matching tolerance

The bill is placed on hold and the broken leg of the match is identified …
```

Tag exactly the steps that do not always run. In a three-way-match step list —
*select the invoice / enter the bill / compare the three legs / apply the
tolerance / **place an out-of-tolerance bill on hold** / **resolve a quantity
exception** / **resolve a price exception** / complete the matched bill* — the
three bolded ones are conditional and the rest are main path. Do **not** renumber
or reorder to group the branches: each branch stays adjacent to the step that
triggers it. A "step" that is really a **variant of the whole procedure for one
site** gets `Condition: Plant 3 only`, which is honest about what it is (if it is
genuinely a separate procedure, say so under `conflicts` — scope is not yours to
reshape).

### Applying the two rules above to an EXISTING draft (update pass)
Mechanical, with judgment at the edges. Work your fragment top to bottom:

1. Read `At a Glance`. If the `Systems` row does not name the
   procedure's default system, fix that first — every deletion below depends on
   B being the fact's home.
2. **Delete** every step `System / Tool` tag naming that default system; keep only
   the departures. Deleting the tag never deletes the fact — B holds it.
3. **Delete** every `Expected Result` that restates its step title. Keep the
   non-obvious outcomes and the decision points.
4. Cut the performing role out of the step prose wherever it is the role B already
   names, leaving it at each step where the role genuinely changes. **Rephrase,
   don't just strike a noun** ("The AP Clerk enters the invoice" → "The invoice is
   entered"): current-state passive voice is unchanged.
5. Add `Condition:` to every step that does not always run, as the first line of
   the step body. Do not renumber, do not reorder.
6. For each `VALIDATION REQUIRED` / `PAIN POINT` / `IMPROVEMENT OPPORTUNITY`
   callout running longer than ~3 sentences: write a `Note:` (one or two
   sentences, the actionable core) and move the remainder into `Detail:`
   **verbatim wherever you can** — this is a split, not a re-draft. Never invent a
   note the body does not support, and never lose a sentence in the move.
7. Re-read the steps. If the draft now reads as though a fact went missing, that
   fact lived only in a tag you deleted: put it in its **home section** (B for
   at-a-glance facts, F for controls, the step itself for step detail) — not back
   into the tag.

This pass adds no content and removes no fact; it removes restatement. Report
`tags_removed`, `conditions_added` and `callouts_split` in your return.

### Variant procedures — one shared flow, explicit branches
A skeleton stamped with a `<!-- scope note: covers variants … -->` comment
covers two or more near-duplicate activities deliberately merged at scoping
(e.g. *New Vendor Setup* + *Vendor Banking Change*). Document the shared flow
**once**; at the step(s) where the variants diverge, branch explicitly ("For a
banking change, additionally …"). Never write parallel near-identical step
sequences. Leave the scope-note comment in place — it is authoring metadata and
is stripped at render.
