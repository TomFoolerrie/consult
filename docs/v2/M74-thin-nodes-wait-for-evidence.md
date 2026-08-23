# M74 — Thin nodes wait for evidence: the fill wave reads the confidence call

**Status: BUILT** (`2.5.0-alpha.3`, gate 21/21 — see Amendment A1).
Origin: the second Nordhaven build run (audit 2026-08-23), cost table.
The taxonomist judged 6 nodes thin and 2 with nothing, and the fill
stage dispatched a full-price drafter for every one of them anyway:
`service-receipt` spent 97k tokens to record one fact and one GAP,
`catalog-and-contract-price-maintenance` spent 79k to refuse to
fabricate, `consumption-based-receipt` 81k for one established fact.
Roughly 400–500k of the run's 1.83M subagent tokens — a quarter —
went to confirming absences the taxonomist had already established in
the node scope prose ("no owner, no trigger, no cadence… described by
any participant").

## Why

1. **The signal exists and dies INSIDE `build_manifest`** (site
   corrected per review). The staged `procedures.yaml` carries
   `confidence: high | medium | low` per procedure (the taxonomist
   contract's own schema, `consult-taxonomist.md:804`, alongside
   `gap_forecast`). Confirm's merge (`_merge_by_key`,
   `scaffold.py:235–265`, field-wise `{**existing, **proposed}`)
   already carries `confidence` through to the procedures list — it
   is `build_manifest`'s component literal (`scaffold.py:1321–1325`,
   keys `file/role/slug/heading/l2/order` + optional `upstream`;
   note the manifest key is `heading`, the staged key is `title` —
   do not conflate) that drops it. By fill time the sufficiency
   verdict survives only as prose in the node files, which the
   advisor cannot read.

2. **The fill guard partitions on structure, never on evidence.**
   Guard 4 waves on upstream hints alone (`orchestrate.py:1103–1140`):
   every unfilled skeleton is equally dispatchable. There is no
   "these N have nothing behind them" in the action's details, so the
   orchestrator cannot even surface the choice.

3. **The stub-now path pays twice.** A thin node drafted today yields
   an honest-absence fragment whose GAPs feed the agenda — real value,
   but value the taxonomist's gap_forecast already carried. When the
   client answers the asks, the same node needs an `update` dispatch
   to become a real fragment. Draft-after-evidence is one dispatch;
   draft-then-update is two, the first of which mostly re-reads
   sources to re-discover what the node scope already says.

4. **M48's tiering has no thin lane.** First drafts ride the strong
   tier unconditionally (SKILL.md:340–346). A thin-node first draft —
   tiny source slice, output shaped in advance as "one fact plus
   evidenced absences" — is the one first-draft case that does not
   need it.

## The shape

The ruling first: **confidence gates COST, never SCOPE.** A thin node
stays in the taxonomy, keeps its manifest component and its unfilled
skeleton, and appears in every coverage view — it waits visibly. It is
drafted on new evidence or on the human's explicit "draft it anyway",
and nothing else — where "new evidence" includes its machine-readable
form once M75 lands: an ask touching the node flipping to answered IS
new evidence, and releases the node back into the wave (the M74/M75
reconciliation recorded in M75; one rule, not two). No node ever
silently drops out of the document.

### Part A — confirm carries the call into the manifest

The edit is a one-key passthrough in `build_manifest`'s component
literal (`scaffold.py:1321–1325`) — the merge already delivers
`confidence` on each proposed procedure (see Why #1); the literal
just copies it (absent stays absent — a pre-M74 or hand-built
registry entry without the key reads as no-opinion, which behaves as
high). `doc_model.validate_manifest` runs positive checks only and
rejects no unknown keys (verified per review), so no schema change.
The taxonomist schema's OTHER `confidence` carriers
(registry entries, `consult-taxonomist.md:821,829`) are out of scope
— only the procedure one persists. Nothing else consumes it yet;
this is the persistence seam.

### Part B — the fill action partitions the wave

Guard 4 splits the ready wave by confidence: `unfilled` (the
dispatchable wave, as today) now carries only nodes with evidence
behind them; a new `details.thin` names the low-confidence remainder,
each with its confidence value. **The action stays `fill` and stays
a NON-gate — ruling per the set review:** an earlier draft made it a
conditional gate when only thin nodes remain, but `fill` is a
HOLDABLE action and the HOLDABLE ∩ GATE disjointness doctrine
(`orchestrate.py:751–753`, pinned by `test_sticky_holds.py:261`)
forbids a sometimes-gate holdable — and the gate bought nothing the
existing machinery lacks: when only thin nodes remain, the advisor
returns `fill` with an empty `unfilled` wave and a `details`
sentence naming the choice ("N thin nodes remain: dispatch them
[details.thin], or hold `fill` and chase the asks — see M75
ask-first"), and the ORCHESTRATOR relays it and stops for the human
exactly as it does for any empty work order. The human's brake is
the M17 hold; the human's go is dispatching the thin list. No new
gate, no doctrine change, same behavior (the M46 agenda and the
needs view already speak "cannot yet document with confidence",
`agenda.py:422` — the waiting state is already rendered to the
client as asks). `medium` stays in the ready wave —
only `low` waits; the boundary is one word in one place so a later
ruling can move it. Build constraint, per review: `details.unfilled`
keeps its name and shape — it is asserted across four test modules
(`test_decide_states`, `test_m26_seams`, `test_m6_reassessment`,
`test_orchestrate`), all on confidence-free fixtures, so the split
is additive (`thin` is a new key) and those fixtures stay
byte-identical.

### Part C — the skill routes the thin dispatch to the cheap tier

The M48 tier table gains the thin lane: a `low`-confidence first
draft the human ordered anyway is a cheaper-tier hint (slim source
slice, absence-shaped output), like `update` mode. Dispatch
documentation, not engine machinery — same as the rest of M48.

### Part D — downstream honesty

A thin node's unfilled skeleton must not wedge the ladder: the wave
logic already defers on upstream hints, so a ready node whose
UPSTREAM is thin-and-held would strand. The build decides the rule
(likeliest: a held-thin upstream is treated as absent for wave
release, and the drafter's seam read degrades to the node scope
prose) and records it in the amendment. `draft_ready` remains
reachable with thin nodes still unfilled ONLY via the human's
explicit leave-them ruling at the Part B gate — the advisor otherwise
keeps returning `fill` for them, exactly as today.

## The gate

- Confirm fixture: staged registry with per-procedure confidence →
  manifest components carry it; an entry without the key round-trips
  without it.
- Fill fixture: mixed-confidence area → `unfilled` wave excludes
  `low`, `details.thin` names them with values; all-thin remainder →
  `fill` with empty `unfilled`, populated `thin`, and the choice
  sentence (NOT a gate — HOLDABLE ∩ GATE disjointness pinned by
  `test_sticky_holds.py:261` stands untouched); the advisor stays
  read-only.
- Scope guard: a thin node is present in the manifest, the coverage
  map and the agenda feed while held (nothing disappears).
- v1 areas and confidence-free manifests: fill output byte-identical
  to today's.
- Full suite + compat gate untouched.

## Amendment A1 — build rulings (2026-08-23)

* Upstream ruling (Part B/D): a thin-and-excluded upstream is ABSENT
  for wave release — blockers are `pending − thin`, so a downstream
  chain never strands behind a node that is by design waiting
  indefinitely; its seam read degrades to the node scope prose. A
  non-thin unfilled upstream still defers, unchanged. Pinned by two
  tests.
* All-thin is checked BEFORE the cycle branch (an empty wave with no
  dispatchable nodes is not a cycle), and cycle degradation sweeps
  only dispatchable slugs, never the thin remainder.
* Fail-safe direction pinned: anything not exactly `low` (medium,
  high, unrecognized, keyless) dispatches.
* Hold path verified: `hold: [fill]` on an all-thin remainder gates
  with `held_by`, `thin`, empty `unfilled` intact.
* Scope guard asserted structurally (component + confidence + file +
  ownership survive while waiting); coverage/agenda read no
  confidence, so no filter exists for them to acquire.
* Guard 4 now sits at ~1195–1235 (ticket's 1103–1140 predated
  M72/M73 shifts); v1-identity tests compare details minus the
  advisory keys added since M65/M73 — `unfilled`/`deferred` and both
  reason strings byte-identical, the four pinned modules untouched.
* Suite 1615 → 1636, zero skips/xfails.
