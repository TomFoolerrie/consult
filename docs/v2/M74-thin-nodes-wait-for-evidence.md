# M74 — Thin nodes wait for evidence: the fill wave reads the confidence call

**Status: TICKETED.**
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

1. **The signal exists and dies at the confirm gate.** The staged
   `procedures.yaml` carries `confidence: high | medium | low` per
   procedure (the taxonomist contract's own schema,
   `consult-taxonomist.md:804`, alongside `gap_forecast`). Confirm
   consumes the staged registry (`scaffold.py:1425–1450`) and builds
   manifest components with slug/title/l2/order/upstream only — the
   confidence call is read for nothing and discarded. By fill time
   the sufficiency verdict survives only as prose in the node files,
   which the advisor cannot read.

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
and nothing else; no node ever silently drops out of the document.

### Part A — confirm carries the call into the manifest

`build_manifest` copies the staged registry's `confidence` onto each
procedure component (absent stays absent — a pre-M74 or hand-built
registry entry without the key reads as no-opinion, which behaves as
high). Nothing else consumes it yet; this is the persistence seam.

### Part B — the fill action partitions the wave

Guard 4 splits the ready wave by confidence: `unfilled` (the
dispatchable wave, as today) now carries only nodes with evidence
behind them; a new `details.thin` names the low-confidence remainder,
each with its confidence value. The action stays `fill` and is a gate
only when the READY wave is empty and thin nodes are all that remain
— then the human is asked once: draft the thin set anyway, or leave
it unfilled for the agenda to chase (the M46 agenda and the needs
view already speak "cannot yet document with confidence",
`agenda.py:422` — no new machinery, the waiting state is already
rendered to the client as asks). `medium` stays in the ready wave —
only `low` waits; the boundary is one word in one place so a later
ruling can move it.

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
  gate with the two answers; human "draft anyway" path dispatches
  them (asserted via the action's details, the advisor stays
  read-only).
- Scope guard: a thin node is present in the manifest, the coverage
  map and the agenda feed while held (nothing disappears).
- v1 areas and confidence-free manifests: fill output byte-identical
  to today's.
- Full suite + compat gate untouched.
