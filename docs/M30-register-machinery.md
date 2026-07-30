# M30 — Register machinery: conversational writes, citable vs context entries

> **Status: PROPOSED — shape agreed with the user 2026-07-30, not yet
> designed in detail, not built.** Companions: M24 (whose
> promote-to-register move this gives a real execution path), M29 (whose
> register-reference checks validate what this ticket structures), M12/A3
> (whose gap-answer deflections become standing context entries), M26
> (whose declared-identity playbook the deferred token option would be
> the third run of).

## The two problems this solves

1. **The human is doing file work.** Register content is rightly the
   human's decision — but today "the human decides" means "the human
   hand-edits markdown," the one place the system regresses from
   reviewer-at-a-gate to file editor. Users want to review and approve,
   quick and easy, in conversation.
2. **The register conflates two kinds of shared knowledge.** Publishable
   source-backed facts (thresholds, cutoffs, systems of record) and
   engagement intelligence uncovered along the way (a disputed
   ownership, an exclusion rule, an unowned integration) both need one
   home — but they have different citation semantics and different
   audiences, and one undifferentiated file serves neither well.

## Part A — Conversational register management

**The human approves in conversation; a deterministic verb writes.**

- Proposals keep arriving from the existing producers: the placement
  pass status, drafter `register_candidates`, consolidator deflections
  ("shared recurring value — belongs in a register").
- The orchestrator presents each proposal in chat: register, entry id,
  proposed content, provenance, which procedures currently restate it.
  The human answers yes / edit-to-this / no. One word each.
- On approval the orchestrator runs the new verb (names illustrative):

```
engagement.py register add <register> --id <entry-id> \
    --class citable|context --text "..." --provenance "SRC-004 (p2p), ..."
engagement.py register update <register> --id <entry-id> --text "..."
engagement.py register list [--register X] [--class citable|context]
```

- Rules carried over from everything else: the MODEL never freehand-edits
  register files (the verb validates, is idempotent at content, refuses
  id collisions); `_client/` write history stays clean; register CONTENT
  is always the human's call — the verb executes an approval, never a
  judgment.
- The verb imposes light entry structure (stable entry ids as headings +
  a class + provenance line). This is deliberate: entry identity is what
  the deferred `[[reg:...]]` token needs, so Part A buys the option
  without committing to it.
- After an add/update, the orchestrator queues the usual notes to the
  restating procedures ("reference the register") — unchanged M24 tail.

## Part B — Two entry classes

### Citable entries

Publishable, source-backed shared facts. The reference-don't-restate
targets. Prose names them; M29's checks validate the naming and warn on
restatement. **Render gains a register appendix**: citable registers
compile into the deliverable, so the reader's pointer finally resolves
to something — this closes the "no render story" gap.

### Context entries

Key facts UNCOVERED through drafting and consolidating that every
drafter needs to know to draft well — but that the deliverable never
cites by register name: the callback ownership is disputed; Plant 3 bin
stock is supplier-owned and excluded from counts; the Coupa-NetSuite
sync has no owner. The fact-shaped sibling of the conventions digest
("phrasing already decided" → "facts already established, disputes
already known"). Institutionalizes what consolidator gap-answer notes do
only transiently: a STANDING map of what is known and contested, instead
of point-in-time notes that expire off the bus.

**The two safety rules (the sharp edge, settled up front):** a context
entry is knowledge without a citation path, one step from the
evidence-free prose channel the whole system exists to prevent.

1. **Every context entry carries provenance** — the SRC id(s) and origin
   area it was uncovered from, stamped at approval time (the verb
   requires `--provenance` for class context).
2. **Context entries ALIGN, they never EVIDENCE.** Drafters use them to
   not-contradict, to frame correctly, to know a dispute exists. A
   drafter who needs to STATE the fact and whose own sources do not
   carry it follows the existing moves: within-area, transitive citation
   of the provenance SRC; cross-area, a GAP with the pointer, or adopt.
   Prose cites the UNDERLYING SOURCE, never the register. (The drafter
   contract gets this block; M29's sweep classifies it.)

Side effect worth recording: this dissolves most of the remaining
pressure for cross-L1 SRC citations (the M29 locality discussion) — the
FACT crosses areas via the register with provenance attached, while the
CITATION stays area-local.

## Consumption changes

- Drafter brief: registers listed by class — citable with the
  reference-don't-restate rule (unchanged); context entries surfaced as
  pre-read ("facts already established — align; cite the provenance
  source if you state one, GAP if you can't").
- Placement/consolidator briefs: `register list` output replaces the
  bare file listing, so proposals target entries, not files.
- Audit: a derived who-references-which-register view is cheap once
  entries have ids (same trick as the spine); include with M29's checks
  or defer — decide at build time.

## Deferred (recorded, not built)

- **`[[reg:register#entry]]` tokens** — full checkable identity for
  register references (resolve at render, hard-error on dangling, audit
  derivation). Part A's entry ids make this a small step later; take it
  only if M29's prose-level checks prove insufficient on a live run.
- Per-area register shadowing (still rejected: a fact that varies by
  area is not a shared fact).

## Acceptance sketch (firm up at design time)

- The verb round-trips: add → list → update, idempotent, id-collision
  refused, context-without-provenance refused.
- A conversational session: proposal relayed → one-word approval → entry
  written → notes queued — with the human never opening an editor.
- Citable appendix renders; context entries NEVER appear in rendered
  output.
- Drafter contract block for context entries lands with the verb (same
  commit, like the M26 opus pin).
- M29's checks pass against the structured files.
