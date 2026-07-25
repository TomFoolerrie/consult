# M12 — Consolidator (cross-procedure consistency pass)

> **Status: DESIGNED — open questions settled.** Ready to build.

## Goal

A pass that reads the **whole drafted area at once** and finds what no single
drafter can see: the same report under three names, one fact stated fully in
four procedures, two procedures describing one handoff differently, drift in
recurring phrasings, a step sequence that reads oddly across an L2 bucket.

It writes **nothing to fragments**. Findings become notes in the existing
`_review/{slug}.notes.yaml` queue, and the owning drafters absorb them on their
normal update pass. The human sees the list before any drafter runs.

## Why

Drafters are isolated by design — that's what makes them parallel, cheap, and
safe. The cost is seam and terminology inconsistency, which today the human
finds by reading the assembled draft and fixing it by hand (the work this
ticket replaces).

### What the existing machinery already covers (and what it can't)

**`aggregate.py` guarantees the derived views are consistent — and is
structurally blind to prose.** It joins *markup*: callout label lines,
sub-field bullets, gap tags, and the `consult-meta` slug lists. Per its own
contract, nouns bind via those slug lists, *never* by scraping prose. So the
Systems view, Role Dictionary and appendices cannot drift — they project
identity, not language.

The consequence: **the views were never the problem.** Two procedures can both
bind `systems/netsuite` (aggregate satisfied, view perfect) while one calls a
report "AP Aging Summary" in its steps and the other calls it "the AP aging
report". Nothing mechanical can see that, because seeing it means deciding
those two strings denote one thing.

**Aggregate works on identity; M12 works on equivalence.** Identity is exact
match — decidable in Python, which is why it is a script. Equivalence is a
judgment about meaning, which is why this is an agent. The same split explains
the other categories: aggregate counts callouts, it does not weigh
explanations, so `duplication` is invisible to it; `seam` and `sequence`
require holding two procedures' described behaviour side by side, which is not
a join.

Corollary, and the reason for the fact-conflict rule below: M12 has neither
sources nor structured bindings — only prose. It can report that two
procedures disagree; it has no basis for saying which is right. Aggregate has
the opposite limitation. No component adjudicates; that is the human's job, at
the gates.

### Relationship to M11 (both survive — they do opposite things)

M11's `upstream` hints and wave ordering attack the same problem *before* text
exists. **M11 prevents; M12 detects.** Neither replaces the other:

- Waves cover only seams somebody thought to hint, and handing a drafter an
  upstream fragment risks **anchoring** (echoing the upstream's framing rather
  than drafting from its own sources).
- More decisively: **waves propagate consistency; they cannot detect that a
  chain agreed on the wrong thing.** Upstream context flows one direction, so
  if the upstream drafter used the minority name, every downstream drafter
  inherits it — consistently. Waves make a chain *agree*; only a post-draft
  pass can ask whether the agreement is right.

A post-draft pass has neither limit: full visibility, and no influence on how
the text was written.

**The integration that closes the loop:** a `naming` finding proposes an entry
in M11's `_reference/conventions/` digest as well as writing notes. Notes fix
the prose that exists; the digest stops the next re-draft from re-drifting.
Without it, M12 re-finds the same drift after every fill pass. (The digest is
human-confirmed, exactly like a registry alias — see routing below.)

## Design

### Invocation

`consolidate` — a stage the human asks for, offered at the **draft-ready gate**
(M17): every procedure filled, `aggregate` and `reconcile` done (both free), and
nothing yet spent on `synthesize` or `render`.

The advisor still never demands it — it has no way to know "ready", so the gate
asks rather than acts. M17 changes only *where* the question is asked.

**Why not at the `review` gate (the earlier design).** Offering it after render
made the derived tail run twice for every consolidation pass:

```
consolidate → notes → guard 2 apply_review → drafters update fragments
  → guard 6 aggregate → guard 8 reconcile
    → guard 9 synthesize   (dependencies + RACI re-dispatch via scope_delta)
      → guard 10 render
```

Both judgment agents and the render re-ran against text the human already knew
was about to change. At the draft-ready gate that tail runs once.

The cost argument is the weaker half. The **quality** argument is that review
kits go out to humans, and reviewer attention is scarcer than tokens: a
reviewer who spends a comment pointing out that one procedure says "AP Aging
Summary" and another "the AP aging report" has spent it on something a
mechanical majority count would have caught for free. Consolidating before kits
means the drift reviewers see is only the drift the system genuinely cannot
resolve.

This does **not** claim consolidation happens once. The review cycle (M8–M10)
churns fragments after render by design, so a later pass may find new drift —
the stage is rerunnable and dedupes to zero new notes when nothing changed. The
claim is narrower: the consolidator's *own* churn should precede the tail rather
than follow it.

Reading the draft at the gate is free: `render.py --slugs <all procedure slugs>`
renders the procedures with no front/back matter and **never writes the
`.render.json` signal**, so previewing the verbs and nouns neither requires a
derived view nor advances the state machine.

Rerunnable at any time; it only ever appends notes.

### Fan-out (context discipline)

One `consult-consolidator` subagent **per L2 bucket** (dispatched in parallel),
each reading only the fragments in its bucket — that keeps each context bounded
and matches how a reader experiences the document. Then **one cross-bucket
pass**.

The per-bucket agents catch seam and sequence mismatches, which are almost
always local to a bucket. The cross-bucket agent catches global noun and
report-name drift, plus the duplication the per-bucket agents cannot see.

**Cross-bucket input (revised — the earlier A+B-only scope had a blind spot).**
Reading only `A. Process Overview` and `B. Quick Reference` misses any
full-treatment duplication living in the step section, which is where most
duplication actually is. The cross-bucket agent reads:

- every procedure's `A` and `B` (the primer + at-a-glance layer, where
  cross-area drift surfaces),
- every procedure's **step headings plus the first line of each step body** —
  enough to recognise "this fact is explained here too" without pulling 48% of
  the document into one context, and
- the `_reference/` registry.

An area with one L2 bucket runs one agent and skips the second phase.

### What it may raise (the finding taxonomy — the anti-noise contract)

**Allowed categories, each requiring two or more procedures as evidence:**

| Category | Definition | Routed to |
|---|---|---|
| `naming` | the same artifact/report/system referred to differently across procedures | see routing below |
| `duplication` | the same fact given full treatment in 2+ procedures | the procedure that is NOT its home section (per "say it once") |
| `seam` | two procedures describe one handoff inconsistently (artifact, timing, state, system) | both sides |
| `phrasing` | a recurring formulation done differently for no reason (nav paths, date/period formats) | the minority-form procedures |
| `sequence` | procedures in a bucket whose described order contradicts each other | both sides |

**Explicitly out of bounds** — the noise sources:

- Anything visible in ONE procedure alone. Single-procedure quality is the
  drafter's job and the human's read; a consolidator finding must be a
  *relationship*.
- Style, tone, word choice, length. (Structural verbosity is M16's business,
  and it is governed by section role, not judged here.)
- Facts. It has no sources; it cannot know which of two conflicting statements
  is right. **A conflict is reported as a conflict, never resolved**, and is
  segregated from findings in the report.
- New GAPs, callouts, IDs, or scope changes. Not its office.
- Registry edits. It may *recommend* an alias or a conventions entry; the human
  confirms.

### `naming` — mechanical majority, and where the fix goes

**Counted over `consult-meta` slug bindings, not over prose.**
`aggregate.parse_consult_meta()` already returns each procedure's declared
system and role slugs; majority usage is counted from those. Counting over
prose would rebuild exactly the fuzzy scraping the architecture rejects.

Agent judgment applies only to artifacts the registry does not cover (report
names, file names, status labels), and to overriding a mechanical majority —
permitted, but the note must justify why the minority form is the better term.
No majority (an even split) is **not** resolved: it is reported as requiring a
human decision.

**Routing — registry/digest first, text second.** Three names for one report is
usually a vocabulary problem, not eight prose problems:

| Situation | Fix |
|---|---|
| noun is in `_reference/` but a procedure used a non-canonical form | notes to the minority-form procedures |
| noun is in `_reference/` and the form used is a legitimate synonym | **alias top-up** proposed on the registry entry; no drafter dispatch |
| noun is NOT in `_reference/` at all | registry top-up proposed (the existing human loop), plus notes |
| a recurring phrasing rather than a noun | **`conventions/` entry** proposed, plus notes to the minority forms |

This deliberately meets `aggregate.py`'s existing behaviour at the boundary:
aggregate already WARNs on a *declared* `consult-meta` slug absent from the
registry. M12 catches the complementary case — a noun that was never declared
because the drafter simply wrote it into a sentence. Both feed the same human
registry top-up loop; M12 does not invent a parallel path.

### Finding cap

**Per category, per bucket — 10.** A per-area cap lets one noisy category
crowd out the others; per-bucket keeps the review bounded without hiding a
whole class of finding. When a cap truncates, the report says what was dropped
(the standing no-silent-caps rule).

### Output

Notes via `notes_util.append_items` (merge-append + dedupe, so a rerun is
idempotent), shaped like the existing tracked-change/comment notes so drafters
need no new instructions:

```yaml
- type: consolidation
  category: naming
  location: 10_payment-run.md (E. Step-by-Step)
  anchor: "the AP aging report"
  note: >-
    Called "AP Aging Summary" in [[invoice-intake]] and [[vendor-statements]];
    this is the minority form. Use the majority name unless your sources
    specifically say otherwise.
  peers: invoice-intake, vendor-statements
  source: consolidate
```

**Note on `notes_util`:** its `_KEYS` tuple is a fixed superset and must be
extended with `category` and `peers`. `peers` is stored as a **comma-joined
string**, not a list — `_scalar()` would otherwise emit Python list syntax into
the YAML.

### The human-facing report

Printed at the point the human decides whether to spend the stage. Three
things it does deliberately: **the dispatch count is the headline**, because it
is the cost; **conflicts are segregated** from findings, because they are
reported and never resolved; and a seam finding **names when waves already had
a hint and missed it**, which is the evidence for judging whether the stage
earns its keep in this area.

```
CONSOLIDATION — procure-to-pay
15 procedures · 5 L2 buckets · 6 agents (5 bucket + 1 cross-bucket)

naming                                                        3 findings
  "AP Aging Summary"          majority 4  ·  minority 1
    minority form in weekly-payment-run ("the AP aging report")
    → registry: alias top-up proposed on systems/netsuite
  "Match Exception - Hold"    majority 3  ·  minority 1
    minority form in goods-receipt ("exception hold status")
  "positive pay exception file"  no majority — 2 v 2, agent flagged
    → JUDGMENT: no canonical form; human decision needed

duplication                                                   2 findings
  three-way match tolerance explained in full in 3 procedures
    home: po-invoice-entry-and-three-way-match
    → cross-reference only: goods-receipt, weekly-payment-run
  vendor banking callback described in full in 2 procedures
    home: vendor-banking-change
    → cross-reference only: vendor-master-data-maintenance

seam                                                          2 findings
  goods-receipt ↔ po-invoice-entry-and-three-way-match
    artifact named differently either side of the handoff
    (upstream hint present — waves did not catch this)
  weekly-payment-run ↔ positive-pay-exception-handling
    timing stated inconsistently (same-day vs next-day file)

phrasing                                                      1 finding
sequence                                                      0 findings

CONFLICTS — reported, not resolved                                     1
  wire-and-manual-payment and weekly-payment-run disagree on who
  releases an ACH batch. No source available to this pass.

────────────────────────────────────────────────────────────
8 findings · 7 procedures touched
ACCEPTING IMPLIES 7 DRAFTER DISPATCHES  (one per slug, batched)
2 registry alias top-ups proposed · 1 conventions entry proposed
1 human decision required before dispatch (no-majority naming)

Notes written to _review/{slug}.notes.yaml — nothing else changed.
Delete any note you disagree with before apply_review runs.
```

The human can delete notes they disagree with before the advisor's
`apply_review` picks them up (the existing triage path — no new gate).
**Dispatches are per slug, not per finding:** `apply_review` already batches a
slug's notes into one drafter pass, so eight findings across seven procedures
is seven passes.

### What the drafter does with them

Nothing new to teach: a `consolidation` note is an instruction like a comment.
The existing rule already covers the hard case — a note that contradicts the
drafter's own sources becomes a GAP naming the mismatch, never a silent
harmonization. Worth one added line in the drafter contract: *a consolidation
note is a peer's observation, not evidence; your sources still win.*

### Cost

The most expensive stage in the system, and it should say so up front:
one full read of the area (chunked, parallel) plus one drafter update per
touched procedure. Roughly comparable to a fill pass on the procedures it
touches. That is the trade for work currently done by hand.

**Placement is part of the cost.** The stage's own price is the read plus the
drafter updates; running it at the `review` gate instead of the draft-ready gate
silently added a second `synthesize` + `render` on top. See Invocation.

## Settled decisions (were open questions)

1. **Propose only — never writes fragments.** The earlier justification (an
   agent rewriting eight fragments silently degrades good text) is true but
   unprovable. The decisive reason is **provenance**: a consolidator reads the
   drafted area, not the sources, so anything it wrote would be the only text
   in the deliverable with no evidentiary parent — and indistinguishable in the
   fragment from text a drafter derived from a transcript. The system's core
   claim is that every statement traces to a source. Secondary but real: the
   one-writer-per-file rule is what makes `.maps/` provenance sidecars and
   review anchors work; a second writer makes a line's owner unknowable.
   **Not revisitable on note-volume grounds** — volume is addressed by
   per-slug batching, above.
2. **`naming` majority is mechanical**, counted over `consult-meta` bindings,
   with a justified agent override and no auto-resolution of ties. See above.
3. **Cap is per category per bucket (10)**, with truncation reported.

## Acceptance

- On the live area: consolidation emits notes only, `git diff` on fragments is
  empty, and reconcile is unaffected.
- Every finding cites ≥2 procedures; a seeded single-procedure nit is NOT
  raised.
- A seeded naming drift (one procedure renaming a report) is caught and routed
  to the minority-form procedure only.
- A seeded duplication **inside the step section** (not in A or B) is caught by
  the cross-bucket pass.
- A seeded even-split naming case is reported as requiring a human decision,
  not silently resolved.
- A seeded factual conflict appears under CONFLICTS and produces no
  harmonizing note.
- A category exceeding its per-bucket cap reports what was dropped.
- Rerunning immediately produces zero new notes (dedupe).
- Reached via the draft-ready gate, `consolidate` runs with `.render.json`
  absent and the `scope_delta` baselines untouched — proof the tail has not run
  yet.
- Accepting the notes → drafters run → the reported dispatch count matches what
  actually ran (per slug, not per finding).

## Out of scope

- Cross-area consolidation (per-area first; the registry and `_client/`
  parent config are the cross-area consistency layer — see M13).
- Auto-applying findings.
- Reordering procedures (manifest `order` is a human/scoping decision).
- Retiring M11 — waves prevent, this detects; both stay (see Why).
