# M75 — The ask loop: a curated request register, and asking before drafting

**Status: BUILT** (`2.5.0-alpha.4`, gate 77/77 — see Amendment A1).
Design settled with the human 2026-08-23 — see "The lifecycle ruling"
below, which governs where the Parts overlap it.
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
  STAGES them (`.proposed/asks.yaml`) instead of narrating them into
  a transcript. No new agent, no new dispatch — the same pass, its
  best output persisted. **Promotion is NOT free** (per review):
  confirm's promotion whitelist is fixed (`REGISTRY_FILES`,
  `scaffold.py:129`; `promote_taxonomy` reads nothing else), and
  step 6's `shutil.rmtree(proposed, …)` (`scaffold.py:1605`) would
  silently DESTROY a staged file no verb consumed — the exact M65
  failure shape. The build adds an explicit consume step to
  `confirm()`: staged asks are merged into the ENGAGEMENT-root
  register (`_registers/asks.yaml`, the `findings.py:84,116`
  mechanism — a different target tree than area `_reference/`
  promotion) BEFORE the rmtree, with the same early-check/late-move
  discipline M65 established, and confirm's report names the count.
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

`information-request` gains the accepted asks as its LEAD view; the
raw coverage/step-gap feeds **demote to an appendix — never drop**
(pre-ruled per the set review, no longer builder's choice: the
`coverage` binding's named consumer is a definitions-discipline
invariant and is pinned by `test_surveyor_m37.py:172–177`, and the
derived kinds `information-requests`/`open-validations` are pinned
by `test_views_m40.py:60–80`; needs/research feeds key off the
deliverable at `test_needs_m44.py:108,186` and
`test_research_m47.py:134` — dropping the bindings fails all four
modules). Companion edit the build must not skip:
`needs._coverage_bindings` (`needs.py:218–235`) skips unknown verbs
SILENTLY, so the new `asks:` binding produces no needs feed unless
`needs.py` learns it — amend it or the register is invisible to
needs. Named cost, per review — this is a definitions-language
change, not a re-point: `_ALLOWED_BINDING_KEYS`
(`definitions.py:105`) is a closed set with a named-consumer
discipline, so the build adds an `asks:` binding verb with its
status value-shape (the `_ALLOWED_FINDING_STATUSES`/
`_RENDERABLE_FINDING_STATUS` pattern, `definitions.py:171,180`), an
`asks.renderable()`, and an asks serviceability producer registered
in `serviceability_records` (`definitions.py:715`). The agenda (M46)
reads the same register for its ask content — a real rewrite of its
hard-coded lead prose (`agenda.py:415–430`), not a drop-in — so the
written request list and an interview agenda cannot drift.
Serviceability stays honest per M35: no accepted asks → a "not yet"
naming the register, exactly like findings-report.

### Part C2 — the matcher is a contract change, not an improvisation
(added per the set review — this was the set's biggest hole)

The lifecycle ruling's matcher runs "as part of intake" — but
`consult-intake.md` is ROUTING-ONLY by its own contract ("routing
judgment only — you never scope, never draft, never summarize"), and
the ledger entry shape has no `answers:` field. Two named edits:

- `agents/consult-intake.md` gains the match duty: after routing a
  file, read it against the OPEN asks' text (the one summarization
  license the contract grants, scoped to "which asks does this
  artifact answer") and record the match through the verb — never
  free-prose. The trust-boundary section already covers ingested
  content; the duty slots under it.
- The ledger entry gains the `answers: [ASK-…]` field, written by a
  deterministic verb (`asks.py match SRC-… ASK-…` or an
  `engagement.py` flag — builder picks the host, `engagement.py`
  stays the one ledger writer either way). Advisory metadata, per
  the lifecycle ruling: no gate on the match, the settle dispatch it
  drives still surfaces in the advisor first.

Companion contract line (review gap a): `consult-drafter.md`'s
update-mode trigger list (three today: new source, review,
reprofile) gains the fourth — **answered ask**: the settle work
order names the gap ids and the answering SRC id, and the drafter's
update edit is scoped to exactly those.

### Part C3 — the confirm surface, owned here
(added per the set review — four tickets add confirm lines, none
owned the inventory)

Confirm's report after this set, in one place: the M65 lines
(`promoted taxonomy nodes: <slugs>` / `no staged taxonomy nodes` —
stdout strings pinned by `test_confirm_survey_m65.py:98,200,215,226`,
ADDITIVE ONLY, never reworded), the M66 capture notice, the M74
confidence passthrough (silent — manifest content, no new line
needed), and this ticket's ask-consume count (`promoted N staged
ask(s) to the engagement register` / nothing when none staged). The
ask-first offer at the confirm gate is NEW SHAPE: guard 1's result
carries no `answers` list today (unlike guard 8.5) — the build
introduces it as a new key on the confirm action, additive, with the
two entries (fill now / ask first + the hold edit text).

### Part D — the ask-first sequencing (the gate offers the loop)

The confirm gate's answers gain the second path, first-class:

- **fill now** — today's behavior, untouched, still the default shape.
- **ask first** — the gate OFFERS the path; **the human writes the
  hold** (correction, per review: holds are human-owned config with
  no programmatic writer — `SKILL.md:166,319`, `client_config.holds()`
  read-only, zero `_client/` YAML writers in `scripts/` — and that
  doctrine stands; nothing in this build writes `consult.yaml`). The
  answer carries the exact edit ("add `fill` to `hold:` in
  `<area>/_client/consult.yaml`"), the same shape as the skill's
  existing release instruction. With the hold in place the loop runs
  as many rounds as the human wants: information-request renders from
  the promoted asks → client material arrives → `route` → taxonomist
  curation dispatch (M45 — refreshed sufficiency + refreshed asks) →
  updated register → re-render → ask again. Removing the hold is the
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
   is real). A gap id in neither is an ERROR — **scoped, per review:
   the check runs ONLY where `_registers/asks.yaml` exists.** Every
   pre-M75 area and every existing fixture carries GAP callouts and
   no register; an unscoped check fails all of them and the compat
   gate with them. No register = the invariant is not in force, the
   same conditional shape as every central-mode seam.
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

**M74 reconciliation (per review — the two release rules are one
rule):** M74 Part B says a thin node drafts "on new evidence or on
the human's explicit draft-anyway, and nothing else." This ticket's
automatic release is not a second rule: an ask flipping to answered
IS the arrival of new evidence, made machine-readable — the matcher's
`answers:` metadata is how "new evidence for THIS node" gets a
signal at all. M74's "nothing else" is amended to read: new evidence
(of which an answered ask is the recorded form) or the human's
explicit go. Whichever ticket builds second wires the join;
built together, guard 4's partition reads one predicate:
`confidence == low AND no answered-unsettled asks touching the node`.

**M76 boundary (per review — two queues, one ownership rule):**
`_registers/asks.yaml` owns CLIENT-FACING questions;
`_reference/flags.yaml` (M76) owns INTERNAL judgment — split
candidates, register candidates, policy observations. A flag never
renders for a client; an ask never carries internal work. The bridge
is one-directional: the curator MAY propose an ask from a flag
(a "policy item surfaced, not closed" often becomes a confirm-ask),
and then the flag records the ask id as its actioning reference —
the M76 close discipline, no duplication.

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
- Sequencing: confirm gate carries both answers; "ask first" hands the
  human the exact hold edit (no script writes `consult.yaml` — pinned
  by test: zero `_client/` YAML writers); route → taxonomist-refresh →
  updated register loop exercised across two rounds in fixture (the
  hold applied by the fixture as the human would); removing the hold
  restores guard 4 exactly as today.
- Confirm consumption: a staged `.proposed/asks.yaml` lands in the
  engagement register BEFORE the step-6 rmtree; a confirm that fails
  late leaves it staged (M65 discipline); confirm's report carries the
  ask count and the M65 stdout strings verbatim.
- Matcher: intake contract carries the match duty; the ledger
  `answers:` field round-trips through the verb; the drafter
  contract's trigger list carries "answered ask".
- Known test movement, budgeted: `test_agenda_m46.py:64–96` renders
  agenda output from the `LEAD_*` constants Part C rewrites — those
  assertions are EXPECTED to be updated with the feature, not
  worked around.
- Lifecycle invariants: a register-less gap id (in no ask, not in
  `unasked`) is a reconcile ERROR; an answered ask with unsettled gap
  ids surfaces at the next gate; the matcher's `answers:` metadata on
  a routed source produces the work-order join (asserted mechanically,
  no dispatch).
- v1 areas: byte-identical advisor output; no new dispatch fires from
  any handler without the human's answer.
- Full suite + compat gate untouched.

## Amendment A1 — build rulings (2026-08-23)

* `renderable()` = accepted + sent (a sent ask is still the
  outstanding request the client answers from); answered/retired
  never render. The DEFINITIONS binding still admits only `accepted`
  — the human gate; the widening is the register's own.
* `settled` is a FLAG on an answered ask, not a status — it is what
  the M74 join and invariant 2 read.
* Match host: `asks.py match` owns register + judgment; the ledger
  write goes through NEW `ledger.record_answers` (idempotent).
  Ticket error corrected: `ledger.py`, not `engagement.py`, is the
  one ledger writer — pinned by test.
* Needs feed BUILT (`open-ask`, leading `KIND_ORDER`, conditional on
  the register file) — the silent unknown-verb skip is fixed.
* Join shape: node-level through the ask's own gap references (bare
  slug = whole node); no display-id resolution, no corpus walk.
* Reconcile check is 15.6, beside the node guard; area-scoped gap
  addresses (other areas' gaps are not this area's business); the
  writer also refuses `unask` on a gap already inside an ask.
* Agenda deviation: register-less byte-identity made the LEAD_*
  prose load-bearing, so asks land as a new leading section emitted
  only when curated asks exist — `test_agenda_m46` needed no
  movement; the budgeted change was not spent.
* Staged asks promote as `proposed` — confirm approves the survey,
  not client-facing wording.
* `asks` joined the M67 entry-point gate (new CLI). Suite 1636 →
  1713, zero skips/xfails.
