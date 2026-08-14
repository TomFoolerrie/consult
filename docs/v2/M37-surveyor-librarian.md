# M37 — Surveyor + librarian: taxonomy as brain entities, derived coverage, information requests

> **Status: DRAFT — contract under review.** Companions: M33 (taxonomy nodes
> become kernel entities of a shipped type), M34 (the one ledger the
> coverage join runs over), M35 (the information-request list is a shipped
> deliverable definition), M6/M24/M25 (the v1 embryos this ticket unifies),
> and v0's retrospective (the lens-conflict rule finally lands here).
> Charter: [`README.md`](README.md).

## The problem this solves

v1's taxonomy agent secretly does two jobs, and both are underpowered:

1. **Scoping is one-shot and blind to sufficiency.** `consult-taxonomy`
   proposes the L3 set from whatever sources exist, and the engagement
   proceeds to spend its most expensive tokens — parallel drafter fan-out —
   without ever asking *"do we have enough evidence to draft this, and what
   should we ask the client for first?"* Thin nodes are discovered by
   drafters mid-fill, one GAP at a time, at maximum cost.
2. **The taxonomy is per-area config, not knowledge.** `_client/taxonomy.yaml`
   is a scoping input; nothing links nodes to evidence, nothing notices a
   new source implying a missing L3, and the reassessment (M6) and
   placement (M24) passes each re-derive their own partial picture of "how
   is this engagement organized."

The v2 shape (charter): the taxonomy becomes **first-class brain entities**
— the brain's index — and the agent work splits into the **surveyor**
(upfront: propose structure, assess sufficiency, emit information requests
*before drafting spends tokens*) and the **librarian** (ongoing: curate the
structure as knowledge accumulates).

## Part A — Taxonomy nodes as kernel entities

A third shipped type, `kernel/types/taxonomy-node.yaml` (M33 mechanism,
nothing new): slug identity, level (L1/L2/L3), a one-part prose body (what
this node covers, its boundaries), a parent `references` relation, and the
standard `consult-meta` block. Hand-authored files, one per node, human-
confirmed at the existing scope gate — **the confirm gate does not move.**

- `_client/taxonomy.yaml` survives as the REFERENCE taxonomy (the advisory
  industry-standard tree, per v1.6.1 — advisory, never refusing). The
  engagement's ACTUAL taxonomy is the node entities.
- Process steps bind to their node via a `taxonomy` relation (an M33
  `references` in a declared channel) — the join everything below runs on.
- The manifest remains membership/ordering authority per area; nodes do
  not replace it (an L3 node and a manifest procedure entry are the same
  fact seen from two sides; reconcile checks they agree).

## Part B — The coverage map (derived; the charter's hard guardrail)

`coverage(engagement) -> {node-slug: status}` — a **pure function**, never
a file:

- joins taxonomy nodes ← steps ← evidence links ← the M34 ledger
  (tagged? consumed? how many independent sources?),
- yields per node: `evidenced` (drafted content with citations) /
  `sourced` (tagged, unconsumed sources exist) / `claimed` (node exists,
  nothing tagged) / `conflicted` (Part D),
- is recomputed on demand (advisor, surveyor brief, the info-request
  definition all call it) and **cached nowhere**. A hand-maintained
  coverage file is v0's `state.json` reborn — the charter names this the
  one hard guardrail, and reconcile enforces it by having nothing to check:
  no file exists to drift.

## Part C — The surveyor (upfront)

The surveyor is `consult-taxonomy`'s successor, dispatched at the same
point in the flow, returning a strictly larger result:

1. **Structure proposal** — node entities + registry, as today.
2. **Sufficiency assessment** — per proposed node, from the coverage join
   plus judgment over the tagged sources: enough to draft / thin /
   nothing. Judgment is the agent's; the JOIN is handed to it precomputed
   (the brief carries the coverage map — the agent never re-derives
   mechanics).
3. **Information requests** — for thin/empty nodes: what to ask the
   client, phrased as requests ("the AP aging process: who runs it, from
   which system — a walkthrough or the SOP if one exists"). The request
   list is fed from TWO altitudes (ruling, 2026-08-14): node-level
   coverage (thin / claimed / conflicted) and step-level GAP callouts —
   one list, two feeders. Written as
   entities? No — **written as the surveyor's structured return**, and
   materialized by the *information-request deliverable definition*
   (shipped with this ticket: an M35 definition binding
   `{coverage: thin|claimed, of: taxonomy}` + the request prose), rendered
   before the human confirm gate so the client ask goes out while scoping
   is still cheap.

The gate sequence gains nothing new: the human confirms scope exactly as
today, now with a coverage-annotated proposal and a ready-to-send request
list in hand. **Drafting a node the human confirms despite thin evidence
is allowed** — the system informs, the human decides (M17/M18 doctrine).

## Part D — The lens-conflict rule (v0's debt, paid here)

The rule (retrospective-v0): **when two sources disagree, raise a gap —
never guess.** It lands in the surveyor's sufficiency pass and the drafter
contract simultaneously:

- The surveyor flags nodes whose tagged sources conflict on a material
  fact (owner, system, sequence) → coverage status `conflicted`, and the
  conflict is written as a GAP-style callout on the node entity, naming
  both SRC ids and both claims in their own framing (the PAIN discipline:
  observation, never adjudication).
- Drafters inherit the same rule per step: conflicting sources on a fact
  → state neither, raise the GAP naming both. The drafter contract gets
  this block verbatim; the M29-style rules sweep classifies it.
- Adjudication is human (at review) or analytical (M39) — never the
  drafter's, never the surveyor's.

## Part E — The librarian (ongoing)

The librarian unifies M6's scoping reassessment and M24's placement pass
into one recurring curation dispatch over the brain:

- **Triggers** (advisor-sequenced, as today): new sources registered after
  confirm; a drafter GAP naming an unscoped activity; consolidator/
  placement-style findings that a fact or step sits in the wrong node.
- **Proposes, never executes**: split this node / add an L3 / move this
  step / merge these — each as a note on the M6 bus targeted at the scope
  gate, with evidence. Structural change still flows human-confirm →
  scaffold/manifest edits by the deterministic layer (rename propagation
  per M20).
- M24's one-fact-one-home judgment continues inside the librarian's brief
  (placement was always curation); `consult-placement` and the M6
  reassessment path retire as separate dispatches.

## Acceptance sketch (firm up at build time)

- `taxonomy-node.yaml` loads and parses through the M33 paths; node
  entities round-trip; manifest↔node agreement checked by reconcile with
  a named error.
- `coverage()` golden tests over a synthetic engagement: all four statuses
  produced from ledger + entity fixtures; no coverage artifact written
  anywhere (asserted: the function leaves the tree untouched).
- Surveyor return contract validates: structure + per-node sufficiency +
  requests; the info-request definition loads (M35 stages) and renders a
  docx from a thin-coverage fixture.
- Lens-conflict: a two-source disagreement fixture yields `conflicted` +
  a both-claims GAP callout; the drafter contract block lands in the same
  commit (the M26/M30 pattern).
- Librarian: each trigger type produces a scope-gate note with evidence;
  no file mutated by the agent; `consult-placement` retirement leaves no
  orphaned advisor state.
- v1 suite still green (the standing rule).

## Complexity accounting (the standing test)

New state files: node entities are hand-authored knowledge (the brain's
own category), not state; coverage is deliberately NOT a file. New gates:
zero — the confirm gate is reused, twice as well-informed. New agent
judgment: the sufficiency call and the conflict flag — both bounded by
"observe and propose, never adjudicate." Agents net: two v1 dispatches
(placement, reassessment) fold into one librarian; the surveyor replaces
the taxonomy agent. The review risk to police: **coverage cache creep** —
the moment someone persists the coverage map "for performance," the
guardrail is breached; the join must stay cheap enough that nobody is
tempted (it is: one ledger, one entity walk).

## Deferred (recorded, not built)

- **Cross-engagement taxonomy reuse** (a standard finance tree shipped as
  reference nodes) — the reference taxonomy already covers the advisory
  half; entity-level reuse waits for a second real engagement.
- **Coverage as a rendered dashboard deliverable** — trivially an M35
  definition over the same binding once someone asks; not shipped
  speculatively.
- **Surveyor-initiated interview scheduling** (requests → calendar) — out
  of scope for the plugin, recorded because someone will ask.
