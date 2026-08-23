# M76 — Returns feed the record: agent judgment gets a home, the audit gets a contract

**Status: TICKETED.**
Origin: the full-cycle data-flow trace (2026-08-23) run after M71–M75
were queued. Every other leak found in the trace was already ticketed;
these two were new. Principle under both: a token spent on judgment
must land somewhere the machine reads — a transcript is not a home.

## Why

1. **Agent return judgment has no home on disk.** Run 2's returns
   carried exactly the content the next passes need, and none of it
   persisted:
   - drafter structural flags — supplier-onboarding spans 5 performers
     / 2 systems (split candidate); return-to-vendor's mid-sequence
     performer change (Buyer → Receiving);
   - a register candidate — `sod-matrix#vendor-master-vs-payment` as
     the eventual home for the vendor-master/payment SoD barrier;
   - the taxonomist's four policy observations (AP-clerk SoD overlap,
     Controller approve-and-release, stale implementation-partner
     login, paper-only packing slips) — surfaced, not closed, and
     finding-grade.

   All of it survives only in the session audit the orchestrator chose
   to write. The existing notes bus cannot carry it: `notes_util.KINDS`
   (`review, source, retirement, rename, consolidation` —
   `notes_util.py:48`) is DRAFTER-bound by contract — a notes item is
   a work order for an `apply_review` fragment edit, while a
   structural flag targets a NODE, a REGISTER, or the analysis — and
   the orchestrator's write-nothing rule means it has no verb to file
   judgment anywhere else. Paid-for signal, discarded by construction.

2. **The session audit is heroics, not contract.** Both Nordhaven runs
   produced excellent audits because the orchestrator chose to write
   them; nothing mandates one, no schema, no home, no consumer. The
   run-2 audit's "findings on the output" section §7 is literally the
   leak from item 1 caught by hand.

## The shape

### Part A — the flag queue

A per-area flag queue, DELIBERATELY NOT a notes kind (the notes bus
drives `apply_review` drafter dispatches; putting flags there would
either dispatch drafters at fragment altitude for node-altitude work
or demand a filtered exemption in every notes consumer — wrong bus).
Likeliest shape, builder confirms: `_reference/flags.yaml`, written
only by a new deterministic verb —

    notes_util.py flag --area <area> --target <node-slug | register:{name} | area>
        --origin <agent-kind>/<slug> --text "…"

(home of the verb is the builder's call; the contract is that the
ORCHESTRATOR runs it verbatim from each return's flag block, staying
inside write-nothing-except-scripts). Each flag: target, origin,
text, state (`open | actioned | declined`), and the actioning
reference when closed (the taxonomy change, the register entry, the
finding id, or the human's declared decline — a flag never just
disappears; state changes are as append-only as the ledger's).

### Part B — the agents' contracts name the flag block

`consult-drafter` and `consult-taxonomist` return contracts gain a
structured `flags:` block (target/text pairs) replacing today's
narrate-it-and-hope; the orchestrate skill's return-handling row makes
filing them a numbered duty, one verb call per flag, before
`mark-processed`. A return with no flags files nothing — the block is
optional, never padded.

### Part C — the queue feeds the readers that need it

- The taxonomist's curation brief (`brief.py … --kind` taxonomist
  path, M52) lists open flags targeting nodes/area — a split
  candidate is IN the work order of the next taxonomy pass, not in a
  transcript it never saw.
- `analysis.py brief` lists open flags beside its four feeds — the
  SoD observation reaches the analyst as candidate material with
  provenance.
- The M75 curator reads them too where a flag implies an ask
  ("policy item surfaced, not closed" is often a confirm-ask).
- Reconcile check (advisory WARNING, not error): open flags at the
  draft-ready gate are counted in the gate's report, so accepting a
  draft with unactioned flags is a visible choice.

### Part D — the audit becomes a contract with an empty-by-design core

The orchestrate skill names the session audit a standing duty of every
orchestration session (a dated file at the engagement root, as run 2
did by instinct), with a slim expected shape: timeline, dispatch/cost
table, deviations, end-state checks. Its "findings on the output"
section is EXPECTED EMPTY — anything that would land there should have
been filed as a flag (Part A) or a ticket-worthy defect while the
session ran. The audit verifies nothing leaked; it is no longer the
leak's last resort. Skill prose, not engine machinery; asserted where
testable (the duty text present, the flag verb referenced).

## The gate

- Flag round-trip: verb writes a valid item; open flags surface in the
  taxonomist brief, the analysis brief, and the draft-ready gate
  count; `actioned`/`declined` close with a reference and drop from
  the open views while remaining in the file.
- Wrong-bus guard: a `flag` kind is refused by `notes_util`
  validation (KINDS unchanged); the notes bus and the flag queue
  cannot cross-contaminate.
- Contract text: drafter and taxonomist return contracts carry the
  `flags:` block; the skill carries the filing duty and the audit
  duty (presence-asserted).
- v1 areas: no flags file → every brief and gate byte-identical to
  today.
- Full suite + compat gate untouched.
