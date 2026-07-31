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

## Amendment A1 — tier rejection, promotion rule, the citation loop
## (agreed 2026-07-30)

### L1 (per-area) registers: CONSIDERED AND REJECTED

The proposal: area-level registers as a staging/fact-check gate so the
engagement register stays quiet. Rejected on the two-homes argument: a
register entry exists BECAUSE the fact is shared across areas — a fact
one area knows has its home in that area's prose, so an L1 register
holds facts with one consumer and gives every fact a second home on the
way to its third (the procedure states it AND the L1 register holds it;
one of them drifts). It also re-opens the rejected per-area-shadowing
door, and its machinery bill (promotion between tiers, shadowing
semantics, dual brief listings, a which-register-do-I-cite judgment call
on every drafter) buys nothing the rules below don't.

### The kernel adopted as rules (noise control at the existing gate)

1. **The two-areas promotion rule.** A CITABLE entry requires evidence
   that 2+ areas need the fact — the proposer names the restating
   procedures (it already does). One-area facts bounce back to prose at
   the approval conversation.
2. **Entry lifecycle (DEFERRED, build only if noise materializes).** A
   `proposed` → `confirmed` status inside the one register: pending
   entries visible in `register list`, excluded from the render appendix
   and from reference-don't-restate enforcement until confirmed. A
   probation STATE, not a probation PLACE.
3. **The context class is the low bar.** A real-but-unsettled fact
   (disputed ownership, uncertain threshold) is a context entry, not a
   lower tier.

### The citation loop — entry cites sources; prose cites the entry

Bootstrap sequence (prose usually exists before the entry):

1. **Fact enters prose normally** — sourced, cited to the local SRC id;
   the drafter flags it in `register_candidates` WITH its SRC ids (the
   placement pass likewise proposes with per-area SRC ids + restating
   procedures).
2. **Approval stamps provenance.** The verb writes what the proposer
   supplied; provenance is the entry's citation chain to the ledger.
   **The verb REFUSES a citable entry without provenance** (same
   discipline as `--peers` on consolidation notes) — an unprovenanced
   citable entry is the evidence-free channel by another name.
3. **The tail swaps citations.** Approval queues the usual notes; the
   restating drafters' edits replace the prose SRC citation with the
   register reference (operative values stay when essential to executing
   the step — existing rule). One fact, one home, one citation chain.
4. **Late drafters cite at first draft** — their brief lists the entry,
   so bootstrap churn only ever touches areas drafted before the entry
   existed, healed once by the note tail.

**The never-un-consumes rule (state it so nobody "fixes" it):** swapping
a prose SRC citation for a register reference never un-consumes the
source — consumption is the durable per-source record of a read that
happened; the register reference is downstream of it.

**Entry ids in proposals:** agents name entries as
`<register>#<entry-id>` at proposal time (the verb requires ids anyway).
Prose MAY use the same form; M29's checks can then validate to entry
level. This is the trivial upgrade path to the still-deferred `[[reg:]]`
token — the convention costs nothing now.

### Complexity accounting (why this passes the standing test)

New state files: zero. New gates: zero (approval rides a conversation
the human is already in; the advisor loop untouched). New agent
judgment: ONE rule — the drafter's align-vs-evidence call on context
entries — and it carries the safety payload. Everything else is
deterministic-layer: the verb's refusals are if-statements, the brief
formats by class, render gains one derived appendix. The M29 rules
sweep must classify the align-never-evidence paragraph explicitly
(enforced-at-verb + contract-side) so discipline drift is visible from
day one.

## Amendment A2 — system-review fixes (2026-07-30)

1. **One writer, settled: the verb is the ONLY writer of register files
   — humans included.** The review caught the drift: Part A quietly gave
   register files two writers (hand edits + the verb) while the
   ownership doctrine says one. Settled: once the verb exists, ALL
   register writes go through it — the human's authorship is the
   approval conversation, not the text editor. Hand edits remain
   physically possible (it's a file) but are out-of-contract, exactly
   like hand-editing a fragment. The README ownership table is updated
   in the SAME COMMIT as the verb.
2. **The align-never-evidence rule gets a mechanical backstop** (moved
   from prompt to gate, per the house doctrine the review quoted back at
   us): a prose reference naming a class-context entry is a reconcile
   ERROR — context entries are never cited by name. Lands as M29 Part
   2.1(c), which builds after this ticket.
3. **Sequencing confirmed:** M28 → M29 (sweep + checks 2–4) → M30 →
   M29 Part 2.1 (register checks last — they validate structure only
   this ticket creates).
