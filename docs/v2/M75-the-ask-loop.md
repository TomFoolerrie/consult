# M75 — The ask loop: a curated request register, and asking before drafting

**Status: TICKETED** (design settled with the human 2026-08-23 —
see "The lifecycle ruling" below, which governs where the Parts
overlap it).
Origin: the second Nordhaven build run (audit 2026-08-23) plus the
design conversation after it. Three observations, one missing organ:

1. Gaps live in THREE homes with no link between them — the staged
   `gap_forecast` (dies at confirm, like M74's confidence), the
   taxonomist's node GAPs in `_taxonomy/` (persistent, read-only), and
   the drafters' fragment GAP callouts (the machine-readable
   population, M50 `Nature:` enum). Run 2's 9 cross-source conflicts
   exist twice — node GAPs AND re-minted fragment GAPs — untracked as
   the same fact.
2. The best gap artifact the run produced — the taxonomist's 13
   grouped asks A–M, where ask A alone settles 6 of the 9 conflicts —
   lived only in the agent's return transcript. The synthesis the
   engagement most needs to send a client was paid for and thrown
   away.
3. The `information-request` deliverable renders the raw feeds
   (`writer: python` over coverage + step-gaps) — a fifty-item noise
   list no client should receive. Client-relations reality: asks must
   be consolidated, grouped by who can answer and what artifact
   settles them, and one good ask should close many gaps.

And the sequencing fact that makes it urgent: the taxonomist does its
best gap work BEFORE any drafter runs, the deliverable was born to
render before confirm ("the gate does not move"), and the refresh loop
already exists as verbs (route new sources → taxonomist curation
dispatch, M45) — yet the ladder drives from confirm straight to `fill`,
so the cheap ask-gather-ask rounds are never offered and the engagement
pays the drafter fan-out against evidence it knew was thin.

## Why (the mechanics, precisely)

- `gap_forecast` is consumed once for confirm's printed forecast and
  persisted nowhere (`scaffold.py` confirm path; manifest components
  carry no ask state).
- `information-request`'s two bindings (`requests` via
  `coverage_map.coverage()`, `step-gaps` via the declared GAP kind) are
  both mechanical; no judgment layer exists between the registers and
  the render. The agenda (M46) re-derives from the same raw GAPs
  independently — two client-facing surfaces that can drift.
- Post-confirm, guard 4 fires on unfilled skeletons unconditionally
  (`orchestrate.py:1103–1140`). Ask-first is technically expressible
  today as `hold: fill` (M17, `HOLDABLE_ACTIONS`,
  `orchestrate.py:747`) — machinery no gate ever surfaces as a choice.
- Nothing routes a client's ANSWER back: when ask A is answered, the
  six gaps it settles are re-discovered by hand.

## The shape

### Part A — the ask register (the convergence point)

A new engagement register, sibling to `_registers/findings.yaml`:
`_registers/asks.yaml`, written only by `scripts/asks.py` (the
findings.py pattern: proposed → accepted/sent → answered/retired, with
provenance). Each ask carries:

- client-voiced text, grouped by WHO can answer and WHAT artifact
  settles it (a config pull, a walkthrough, an SOP, a written answer);
- **the gap ids it would settle** — fragment GAP display ids and/or
  node/forecast references. This mapping is the whole point: it is
  what lets an answer be routed back (answered ask → the named gaps'
  update dispatches), what deduplicates the three homes WITHOUT moving
  the gaps (each home keeps its owner; the register is where "is this
  being asked about?" lives), and what makes "one ask, many gaps"
  visible and rewarded.

The three gap homes are unchanged. The register references; it never
duplicates.

### Part B — who curates (two moments, two agents, one register)

- **Pre-drafting:** the taxonomist. It already synthesizes grouped
  asks in its return (run 2's A–M); the contract change is that it
  STAGES them (`.proposed/asks.yaml`, promoted at confirm like every
  other proposal) instead of narrating them into a transcript. No new
  agent, no new dispatch — the same pass, its best output persisted.
- **Post-drafting (draft-ready and later):** a curator pass over the
  full GAP population — the fragment callouts with `Nature:`, the
  node GAPs, the open register. It consolidates, regroups, merges new
  gaps into existing asks, proposes retirement of asks whose gaps
  closed. Builder's choice whether this is a slim new agent or a
  taxonomist verb (it sees the mechanical feeds and display ids, NEVER
  raw sources — it synthesizes the record, it does not re-investigate;
  the analyst precedent, `analysis.py brief`).
- **Human gate, always:** asks are proposed; the human accepts/edits
  before anything renders for a client. Same doctrine as findings —
  `renderable()` returns accepted asks only, structurally.

### Part C — the renders read the register

`information-request` re-binds its lead view to the accepted asks
(the curated list is the document; the raw coverage/step-gap feeds
demote to an appendix or drop — build decides, recorded in the
amendment). The agenda (M46) reads the same register for its ask
content, so the written request list and an interview agenda cannot
drift. Serviceability stays honest per M35: no accepted asks → a
"not yet" naming the register, exactly like findings-report.

### Part D — the ask-first sequencing (the gate offers the loop)

The confirm gate's answers gain the second path, first-class:

- **fill now** — today's behavior, untouched, still the default shape.
- **ask first** — the gate applies `hold: fill` (existing M17
  machinery, now surfaced), renders the information-request from the
  taxonomist's promoted asks, and the loop runs as many rounds as the
  human wants: client material arrives → `route` → taxonomist
  curation dispatch (M45 — refreshed sufficiency + refreshed asks) →
  updated register → re-render → ask again. Releasing the hold is the
  human's "I have what I need — draft"; the fill fan-out then runs
  ONCE against full evidence.

Drafting and asking are NOT exclusive: the register tracks open asks
regardless of drafting state, and rendering the outstanding list is
always available — mid-drafting, at draft-ready, after. A partially
answered engagement can draft what is evidenced (M74's thin partition
composes here: thin nodes are precisely the ones whose asks are still
open) while the remaining asks stay live.

## The lifecycle ruling (2026-08-23, sketched with the human)

One route for every gap, one purpose for every token:

```
discover ──► record ──► curate ──► ask ──► answer ──► route back ──► settle
(agent)      (files)    (agent)    (human) (client)   (mechanical)   (agent)
```

- **Discover:** only the taxonomist and the drafters ever read raw
  sources; every gap is born in one of those two passes. No third
  discoverer.
- **Record:** a gap EXISTS only if it has an id the register can hold.
  Drafter gaps have ids today; the taxonomist's gaps get ids at
  staging (the id-less prose forecast is the loss hole this closes).
  **Ruling (a):** node prose stays — it is capture, the node is the
  brain — but the id'd entry is the canonical fact; prose without an
  id is commentary, not a gap. Reconcile's invariants run over ids
  only.
- **Curate:** the taxonomist (pre-draft) or curator (post-draft) reads
  ONLY the recorded gap population — ids and one-line texts, never
  fragments, never sources. Cheapest agent in the system, by
  construction.
- **Ask:** human gate; accepted asks render (Part C).
- **Answer — ruling (c): humans just drop artifacts.** The drop is the
  whole human interface. File lands in `_sources/new/` → `route` mints
  the SRC id → the MATCHER runs as part of intake: a cheap-tier
  dispatch that reads the new source (the one ask-loop agent allowed
  to read a raw source — someone must know what the artifact is) plus
  the open asks' text, and records `answers: [ASK-…]` on the source's
  ledger entry. No human typing, no approval gate on the match — it is
  advisory metadata; the settle dispatch it drives still surfaces in
  the advisor before any spend, so a wrong match costs a wrong line,
  never a wrong dispatch. The next gate reports the machine's reading:
  "SRC-007 → answers ASK-003, ASK-007 → touches 4 nodes."
- **Route back:** mechanical join, zero tokens: ask → gap ids → the
  nodes/fragments those gaps live in. The output is a WORK ORDER.
- **Settle:** the work order drives the dispatch — taxonomist refresh
  over touched nodes (pre-draft) or update-mode drafters over exactly
  the touched fragments (post-draft, cheap tier per M48). Never a
  full-area rescan to learn what a source changed.

**The two not-lost invariants** (reconcile-enforced):

1. Every gap id appears in the register exactly once — inside some
   ask, or in the explicit `unasked` bucket with a recorded reason
   ("ours to resolve, not the client's" — **ruling (b):** the bucket
   is real). A gap id in neither is an ERROR.
2. An answered ask either settles its gaps or re-opens: the settle
   dispatch closes the ids, or the curator splits the remainder into
   a follow-up ask. No zombie answered-asks with live gaps behind
   them.

**Signal:** the advisor reads open/answered counts per node — the
confirm gate sizes the ask-first path, the fill wave releases a thin
node automatically when its asks flip to answered (M74 composed:
thin ≈ open asks), the draft-ready gate says whether accepting ships
known holes, and the analyst brief can distinguish
"asked, unanswered" from "never asked" — a finding-grade distinction.

## The gate

- Register round-trip: taxonomist-staged asks promoted at confirm;
  each ask's gap-id mapping resolves against live gaps; answering an
  ask surfaces the named gaps (asserted via `asks.py` queries, no
  auto-dispatch).
- Curator fixture: a GAP population with overlapping asks → consolidated
  proposals carrying merged gap-id sets; accepted-only reaches
  `renderable()`.
- Render: information-request over an accepted register renders the
  curated list; empty register → honest "not yet"; agenda and
  information-request draw ask text from the same entries (asserted by
  shared-source, not byte-equality).
- Sequencing: confirm gate carries both answers; "ask first" writes the
  fill hold; route → taxonomist-refresh → updated register loop
  exercised across two rounds in fixture; releasing the hold restores
  guard 4 exactly as today.
- Lifecycle invariants: a register-less gap id (in no ask, not in
  `unasked`) is a reconcile ERROR; an answered ask with unsettled gap
  ids surfaces at the next gate; the matcher's `answers:` metadata on
  a routed source produces the work-order join (asserted mechanically,
  no dispatch).
- v1 areas: byte-identical advisor output; no new dispatch fires from
  any handler without the human's answer.
- Full suite + compat gate untouched.
