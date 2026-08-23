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
   `notes_util.py:48`) is FRAGMENT-ALTITUDE by contract — every item
   lives in a per-slug `_review/<slug>.notes.yaml` and is a work
   order consumed by an `apply_review` drafter edit (producers vary:
   reviewers, `consolidate.py:713`, scaffold at confirm — the
   consumer is what binds the bus), while a structural flag targets a
   NODE, a REGISTER, or the analysis — and the orchestrator's
   write-nothing rule means it has no verb to file judgment anywhere
   else. Paid-for signal, discarded by construction.

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
only by a new deterministic verb hosted in a NEW `scripts/flags.py`
(the `findings.py` pattern: library + CLI in one module) —

    flags.py add --area <area> --target <node-slug | register:{name} | area>
        --origin <agent-kind>/<slug> --text "…"

Correction, per review: `notes_util.py` is a LIBRARY with no CLI (no
argparse, no `main()`) and stays that way — the verb does not live
there; `flags.py` may import `notes_util.validate_item`-style
helpers but owns its own file and schema. Each flag: target, origin,
text, state (`open | actioned | declined`), and the actioning
reference when closed (the taxonomy change, the register entry, the
finding id, or the human's declared decline — a flag never just
disappears; state changes are as append-only as the ledger's).

### Part B — the agents file their own flags (tenancy ruling, 2026-08-23)

**The agent that formed the judgment runs the verb** — not the
orchestrator transcribing it. Drafters and the taxonomist already
carry `Bash(python3:*)` and already run `reconcile.py` themselves;
the verb layer, not the invoker, is the safety mechanism, and the
orchestrator's clerical relay is where this system historically
fumbles. So: `consult-drafter` and `consult-taxonomist` contracts
gain a filing duty — before returning, run `flags.py add` once per
flag formed during the pass — and their RETURN carries only the
filed flag ids (compact, verifiable), replacing today's
narrate-it-and-hope. The orchestrate skill's return-handling row
becomes a CHECK, not a transcription: if a return narrates judgment
that names no flag id, send it back or file it — the fallback duty,
not the default path. A pass with no flags files nothing — the duty
is conditional, never padded.

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
  Ownership boundary, settled in M75's "M76 boundary" section:
  flags = internal judgment, asks = client-facing questions; the
  curator may propose an ask FROM a flag, and the flag then records
  the ask id as its actioning reference. One direction, no
  duplication.
- The open-flag count at the draft-ready gate is an ADVISOR change
  (guard 8.5 adds a `details` count — `test_stage_gates.py:172` pins
  the answers list, not the details keys, so this is additive-safe),
  NOT a reconcile check; reconcile is untouched (correction, per
  review: the earlier draft named both surfaces for one duty).
  Accepting a draft with unactioned flags stays a visible choice.

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

## Build order for the M71–M76 set (recorded here as the last ticket)

Per the adversarial review: M72, M73 and M76 all edit
`agents/consult-taxonomist.md` (M72 and M76 also
`agents/consult-drafter.md`) — they build sequentially, each rebasing
on the last, in ticket order (M72 → M73 → M76). M74 builds before
M75 (M75's release rule reads M74's confidence partition); M75
before M76's Part C curator hook and before M71's serviceability
read where possible (M71's Part A must otherwise handle both
serviceability shapes). Recommended: M72 → M73 → M74 → M75 → M71 →
M76.

## The gate

- Flag round-trip: verb writes a valid item; open flags surface in the
  taxonomist brief, the analysis brief, and the draft-ready gate
  count; `actioned`/`declined` close with a reference and drop from
  the open views while remaining in the file.
- Wrong-bus guard: a `flag` kind is refused by `notes_util`
  validation (KINDS unchanged); the notes bus and the flag queue
  cannot cross-contaminate.
- Contract text: drafter and taxonomist contracts carry the
  file-your-own-flags duty and the return-ids shape; the skill
  carries the check-not-transcribe duty and the audit duty
  (presence-asserted).
- v1 areas: no flags file → every brief and gate byte-identical to
  today.
- Full suite + compat gate untouched.
