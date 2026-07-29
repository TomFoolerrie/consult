# M24 — Gap pollination (cross-L1 gap resolution)

> **Status: DESIGNED — decisions settled with the user.** Ready to build.
> Companion amendment: M12's `gap-answer` category covers the WITHIN-area
> half of the same idea (see M12 "Amendments"); this ticket is the
> cross-area half, where sources do not travel and resolution is a routing
> decision.

## Goal

A gap opened in one L1 is often already answered by another L1's
documentation: inventory carries `GAP — how the goods receipt posts is
unconfirmed` while procure-to-pay's goods-receipt procedure documents
exactly that, fully sourced. Today nothing connects them — the gap goes
out in a review kit and spends a process owner's scarcest resource on a
question the engagement already answered. This ticket surfaces those
matches and resolves them through machinery that already exists.

## Why the shape below (the constraints that settled it)

**Simplicity is a requirement, not a preference.** The user's words: "the
more compute we throw at this the harder it will be to keep track of."
So: no new agent type, no new note kind, no new state file, no new gate,
no scheduled pass, no per-area fan-out. Total new surface is two
subcommands, one single-agent pass, and one drafter-contract line.

**The human is a reviewer, not a gatekeeper.** The user identified
themselves as the bottleneck. Every step below defaults to FLOW THROUGH:
notes route to drafters on the ordinary loop (delete-at-triage is a right,
never a duty), and the source-adoption verb is run by the orchestrator as
part of absorbing a note — the human reviews checkpoint diffs and rendered
drafts, which they were reviewing anyway. Git checkpoints are the safety
net: reverting a bad auto-decision is cheaper than pre-approving every
good one. An engagement that wants the gate back gets it with the EXISTING
sticky-hold mechanism (`hold: [adopt]` in `_client/consult.yaml`, M17) —
config, not new machinery.

**Prose becomes a source by REGISTERING it, never by citing it invisibly.**
Cross-area, a `SRC-` id does not resolve in the other area's
`sources.yaml`, so "just cite theirs" breaks the dangling-citation checks
in reconcile and render. The settled mechanism makes prose-as-source
literal: the answering fragment is copied into the gap area's `_sources/`
and gets an ordinary `SRC-` entry (marked second-hand, hash-stamped).
Every invariant then survives for free — citation resolution, `.maps`
provenance, retirement accounting — because it IS a source. The copy is a
feature: it freezes what was relied on, so the sibling's later edits
cannot silently invalidate the citation.

## Design

### 1. `engagement.py gaps` — the register (free, read-only, layer 1)

Run from the engagement root. Walks `components/`, extracts every open GAP
per area/procedure (aggregate's existing GAP parser — never a new regex),
prints one line each, grouped by area, with a total:

```
ENGAGEMENT GAP REGISTER — components/
inventory · [[month-end-inventory-reconciliation]]
  GAP — how the goods receipt posts to the sub-ledger is unconfirmed
...
47 open gaps · 6 areas
```

No state, no notes, no agents. This layer ships standalone value: the
consultant who sat the walkthroughs is the best pollination engine on the
engagement, and today the open questions are scattered across N documents
where nobody sees them side by side.

### 2. The pollination pass — one agent, human-invoked (layer 2)

A single judgment agent (dispatched by the orchestrate skill; no new agent
`.md` — the dispatch prompt carries the contract inline, it is one
paragraph). Its brief is script-computed: the gap register plus each
area's procedure titles + scope digests (the bounded-digest discipline
from M12's cross pass). It proposes matches as ordinary `kind: review`
notes through the EXISTING `engagement.py note` command — same bus, same
dedupe, same fix path. Each note names the answering area's `[[slug]]` and
recommends exactly one move:

| Move | When | Executes as |
|---|---|---|
| **reduce to handoff** | the gap was a scope question about work owned elsewhere (expected majority) | ordinary drafter note — the retroactive ownership-map rule |
| **adopt as source** | the sibling's documentation genuinely answers a question inside this area's scope | the note names the `adopt` command below; the orchestrator runs it, then the drafter consumes the new source with standard mechanics |

A match the agent cannot place confidently is reported in its return
status, not queued — same report-don't-guess discipline as M12's
conflicts.

### 3. `engagement.py adopt <area> --from <area>/<slug>` — the verb

Deterministic: copies the named fragment into `<area>/_sources/`, appends
a `SRC-` entry to `<area>/_reference/sources.yaml` (hash-stamped;
`note:` marks it second-hand — "internal: drafted <area> procedure"), tags
`touches` with the gap's procedure. Idempotent (re-adopting the same
fragment at the same hash is a no-op). Runs unattended by default; the
M17 sticky hold `adopt` turns it into a human gate per engagement.

### Resolution flow (nothing new after the note lands)

pollinate → notes queued → advisor's ordinary `apply_review` loop →
drafter closes the GAP citing the adopted `SRC-` id (or reduces to a
handoff sentence) → aggregate/reconcile → checkpoint. The human sees a
diff.

## Where the human stays (the load-bearing bottlenecks)

1. Factual conflicts between areas — no component may pick a side.
2. Ownership calls in the engagement audit — client-org questions.
3. Review kits — the engagement's bottleneck, not the system's.

All three are batched and asynchronous; none is a synchronous approval.

## Settled decisions

1. **Prose-as-source is allowed, via registration only** (user decision,
   over the earlier three-move design that required re-reading primary
   sources). The invisible version — closing a gap from sibling prose with
   no ledger entry — stays forbidden: it manufactures the exact dangling
   statements reconcile exists to flag.
2. **Flow-through defaults; sticky hold is the brake.** No new approval
   gate anywhere in this ticket.
3. **One agent per pass, engagement-scoped.** Value scales with migrated
   L1s; cost does not.

## Acceptance

- `gaps` prints every open GAP across a two-area fixture, grouped by
  area, and writes nothing.
- `adopt` creates the copy + `SRC-` entry + `touches` exactly once across
  two invocations (idempotent), and the entry survives
  `reconcile`/`render` with no dangling-citation errors after a drafter
  cites it.
- A pollination note recommending `adopt` carries the exact command; one
  recommending handoff names the owning `[[slug]]`.
- With `hold: [adopt]` set, the orchestrator stops instead of running the
  verb (M17 semantics, unchanged).
- A gap with no cross-area answer produces no note (report-don't-guess).
- Rerunning the pass with unchanged folders queues zero new notes.

## Out of scope

- Within-area gap resolution — M12's `gap-answer` category (cheaper:
  the area's source pool is shared, so transitive citation suffices).
- Auto-adoption without a queued note (the note is the audit trail).
- Any scheduled/recurring invocation — the pass is run like the audit,
  occasionally, from the root, on a human's word.
