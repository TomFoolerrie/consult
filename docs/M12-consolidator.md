# M12 — Consolidator (cross-procedure consistency pass)

> **Status: DESIGNED.** Build after the design questions below are settled.

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

M11's `upstream` hints attack the same problem *before* text exists, and they
have two limits: they only cover seams somebody thought to hint, and handing a
drafter an upstream fragment risks **anchoring** (echoing the upstream's framing
instead of drafting from its own sources). A post-draft pass has neither
problem: full visibility, and no influence on how the text was written. M11
stays for the pre-draft case; M12 is the instrument that does the real work.

## Design

### Invocation

`consolidate` — a stage the human asks for when the draft feels ready, not an
automatic step in the fill loop. The advisor never demands it (it has no way to
know "ready"); the orchestrate skill offers it at the `review` gate:
"the draft is complete — run a consolidation pass before sending kits?"

Rerunnable at any time; it only ever appends notes.

### Fan-out (context discipline)

One `consult-consolidator` subagent **per L2 bucket** (dispatched in parallel),
each reading only the fragments in its bucket — that keeps each context bounded
and matches how a reader experiences the document. Then **one cross-bucket pass**
reading only:

- every procedure's `A. Process Overview` and `B. Quick Reference` (the primer +
  at-a-glance layer, where cross-area drift shows up), and
- the `_reference/` registry.

The cross-bucket agent catches global noun/report-name drift; the per-bucket
agents catch duplication and seam mismatches, which are almost always local to
a bucket. An area with one L2 bucket runs one agent and skips the second phase.

### What it may raise (the finding taxonomy — the anti-noise contract)

**Allowed categories, each requiring two or more procedures as evidence:**

| Category | Definition | Routed to |
|---|---|---|
| `naming` | the same artifact/report/system referred to differently across procedures | every procedure using the non-canonical form (registry alias top-up if the registry lacks it) |
| `duplication` | the same fact given full treatment in 2+ procedures | the procedure that is NOT its home section (per "say it once") |
| `seam` | two procedures describe one handoff inconsistently (artifact, timing, state, system) | both sides |
| `phrasing` | a recurring formulation done differently for no reason (nav paths, date/period formats) | the minority-form procedures |
| `sequence` | procedures in a bucket whose described order contradicts each other | both sides |

**Explicitly out of bounds** — the noise sources:

- Anything visible in ONE procedure alone. Single-procedure quality is the
  drafter's job and the human's read; a consolidator finding must be a
  *relationship*.
- Style, tone, word choice, length. (Verbosity is M15, and it's measured, not
  judged.)
- Facts. It has no sources; it cannot know which of two conflicting statements
  is right. A conflict is reported as a conflict, never resolved.
- New GAPs, callouts, IDs, or scope changes. Not its office.
- Registry edits. It may *recommend* an alias; the human confirms.

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
  peers: [invoice-intake, vendor-statements]
  source: consolidate
```

Plus a compact human-facing report: findings per category, procedures touched,
and **the drafter-dispatch count that accepting them implies** — the cost, shown
before it's spent. The human can delete notes they disagree with before the
advisor's `apply_review` picks them up (the existing triage path — no new gate).

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

## Open design questions (settle before building)

1. **Propose vs decide.** Position taken above: *propose only.* An agent
   rewriting eight fragments for consistency is exactly the change class that
   silently degrades good text. Revisit only if note volume proves tedious.
2. **Majority rule for `naming`.** Pick the majority form mechanically, or let
   the agent judge? Leaning mechanical-with-override: count usages, name the
   majority, let the agent flag when the minority form is clearly the better
   term (a judgment it must justify in the note).
3. **Finding cap.** A hard per-category cap (say 10) forces prioritization and
   bounds the review; risk is silent truncation. If capped, the report must say
   what was dropped (the existing no-silent-caps rule).

## Acceptance

- On the live area: consolidation emits notes only, `git diff` on fragments is
  empty, and reconcile is unaffected.
- Every finding cites ≥2 procedures; a seeded single-procedure nit is NOT
  raised.
- A seeded naming drift (one procedure renaming a report) is caught and routed
  to the minority-form procedure only.
- Rerunning immediately produces zero new notes (dedupe).
- Accepting the notes → drafters run → the reported dispatch count matches what
  actually ran.

## Out of scope

- Cross-area consolidation (per-area first; the registry and `_client/`
  parent config are the cross-area consistency layer — see M13).
- Auto-applying findings.
- Reordering procedures (manifest `order` is a human/scoping decision).
