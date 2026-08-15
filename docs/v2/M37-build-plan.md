# M37 build plan — surveyor + librarian

> Foundation for [`M37-surveyor-librarian.md`](M37-surveyor-librarian.md).
> Deterministic gate: `tests/test_surveyor_m37.py` (skips until
> `scripts/coverage_map.py` exists). The agent-brief half is prose,
> reviewed by the orchestrator against the ticket. Ground rules as ever;
> the M34 A2 carry-in applies: **sources enter central engagements only
> through route/adopt — the surveyor refines TAGS (ledger.retag), it
> never mints registry entries.**

## Design pins (from the ticket + rulings)

- Taxonomy nodes: hand-authored entity files under `<area>/_taxonomy/`,
  type `kernel/types/taxonomy-node.yaml` (level via a `level` relation or
  part? keep v1-simple: a `scope` prose part + optional metadata in
  consult-meta; level/parent expressible later — the gate only pins scope
  parsing). Human-confirmed at the existing scope gate.
- `coverage_map.coverage(root, node_steps) -> {node-slug: status}` — PURE:
  no writes, no caches (both pinned). `node_steps` maps node slug to its
  step slugs (the caller derives it from node entities' relations; the
  explicit parameter keeps the function testable and the join visible).
  Statuses: `conflicted` (the node fragment carries a GAP callout naming
  ≥2 SRC ids — the lens-conflict record) > `evidenced` (some step drafted
  with an SRC citation) > `sourced` (a tagged source is outstanding) >
  `claimed`.
- `kernel/deliverables/information-request.yaml` — the first born-v2
  definition: binds coverage (the `coverage` binding verb gains its named
  consumer), renders thin/claimed/conflicted nodes as client requests.
- Agent prose (the M34-deferred debt lands here): the surveyor brief
  replaces `agents/consult-taxonomy.md` (structure + sufficiency + info
  requests; enumerate ledger-staged sources via `ledger.assess`; propose
  tags, never entries); the librarian brief replaces
  `agents/consult-placement.md` + the M6 reassessment dispatch; intake
  and drafter briefs get their central-mode path updates; the
  consult-orchestrate SKILL's ~15 v1-path sites gain central-mode prose.
  The lens-conflict block lands in the drafter contract verbatim.

## Work packages

### WP-S1 — the deterministic core
Owns `scripts/coverage_map.py` (new), `kernel/types/taxonomy-node.yaml`
(new), `kernel/deliverables/information-request.yaml` (new), plus the
`coverage` binding verb admitted in `definitions.py` (vocabulary +
serviceability handling — served by computing over the engagement; a
v1 area with no taxonomy nodes reports "not yet").
Targets: the whole gate file.

### WP-S2 — surveyor + librarian briefs (prose; orchestrator reviews)
Owns `agents/consult-surveyor.md` (new), `agents/consult-librarian.md`
(new), retirement notes on consult-taxonomy/consult-placement, the
drafter contract's lens-conflict block, intake brief central-mode
update. Deliverable includes a self-review against the ticket's Part
C/D/E contracts, cited line by line.

### WP-S3 — skill wiring (prose + advisor glue)
consult-orchestrate SKILL central-mode sites; advisor dispatch renames
(taxonomy -> surveyor mode names stay stable where tests pin them —
check test_decide_states; if pinned, the surveyor rides the existing
`taxonomy` action name and only the BRIEF changes — prefer that).

## Sequencing
WP-S1 → {WP-S2 ∥ WP-S3} → orchestrator integration + close-out
(alpha.7). Full suite green at every step; the golden + audit run in
every suite pass now, guarding everything.
