# M41 — The engagement objective: seeded skeleton + goal-aware taxonomy agents

> **Status: SPEC** — opens the 2.1.0 line. Origin: two user rulings,
> 2026-08-15 — (1) the taxonomy can start as standard business cycles
> (Treasury, O2C, P2P, tax, FSCP, …) "filled out, with a skeleton built
> on that … gives us structure up front"; (2) "the taxonomy agent(s)
> need to be given an objective up front — what is the deliverable rough
> shape, scope, etc., so it knows how to work to that goal," with the
> skeleton adjustable *through* the agents (out-of-scope cycles simply
> removed). Companions: M37 (the surveyor/librarian this ticket aims;
> closes its recorded promotion-path gap), M13 (the config layer the
> objective lives in), M35 (serviceability, whose "not yet" reports
> become the deliverable-aware sufficiency lens), M40 (whose recorded
> wants stay recorded — this ticket does not absorb them).
> Charter: [`README.md`](README.md).

## The problem this solves

Two blindnesses, one root cause: nothing in the engagement states what
the engagement is FOR.

1. **The surveyor starts from a cold read.** It proposes structure from
   whatever sources exist, with no standing frame. Finance businesses
   are not that diverse at the top: the shipped reference taxonomy
   already enumerates the standard cycles and their typical sub-areas —
   but it is consulted as advisory vocabulary, never instantiated. An
   engagement should be able to START as that skeleton: in-scope cycles
   seeded as staged taxonomy nodes on day one, every one `claimed` (known,
   zero evidence) — which makes the coverage map a work plan and the
   information-request deliverable a day-one PBC list, before the first
   interview.
2. **The taxonomy agents work goal-blind.** The surveyor's sufficiency
   judgment is generic ("is there evidence?") when the honest question is
   "is there evidence FOR WHAT WE WERE ENGAGED TO PRODUCE?" A
   controls-matrix engagement needs control detail the generic judgment
   never asks for; serviceability catches it, but only at render time,
   after drafting spent tokens. The definitions already know exactly what
   they need (their bindings); the config already has a home for
   engagement-level facts (M13). The missing piece is one declared block
   and the plumbing that carries it into the dispatches.

Both land as data + deterministic plumbing + brief prose. No new agents,
no new judgment, no new state files beyond one config block.

## Part A — The objective block (M13 config, typed accessor)

A new top-level config key, following the `profile:`/`hold:` template
exactly (typed accessor, fail-loud parser, field allowlist,
`configured=False` when absent — absent means today's behavior):

```yaml
# components/_client/objective.yaml
objective:
  goal: >-
    Document the purchasing cycle and deliver a process & controls
    matrix with an information-request round up front.
  deliverables: [process-controls-matrix, information-request]
  cycles: [procure-to-pay]
```

- `client_config.objective(area) -> Objective(goal, deliverables,
  cycles, configured, layer)` + `ObjectiveError` + `report_line()`.
- **Validated, not decorative**: each `deliverables:` name must load
  through `definitions.load_definition(name, area)` (a typo'd name
  refuses by name — the silent-no-objective failure mode is the one to
  kill); each `cycles:` slug must be an L1 `slug` in the effective
  reference taxonomy (client override wins, shipped default otherwise).
- All three fields optional; an empty block is `configured=True` with
  empty lists (a stated "no target yet" is different from unstated).

## Part B — The skeleton: seed and promote

Cycles are the reference taxonomy's L1 categories; their typical
sub-areas are its L2 subcategories. The skeleton is that data projected
into staged taxonomy-node fragments — no second cycle library is
shipped, ever (one source of truth for name→slug).

- `scaffold.seed_taxonomy(area, l1_slug, taxonomy_path=None) ->
  report`: for the given L1, write one node file per L2 subcategory to
  `{area}/_reference/.proposed/_taxonomy/<l2-slug>.md` — the surveyor's
  own staging path and template shape (`# <Name>` + `### Scope` with a
  one-line reference-derived scope sentence + an empty `consult-meta`
  block). Idempotent: an existing staged OR live node of that slug is
  never overwritten (the agents' refinements outrank the skeleton).
  Missing L1 in the reference: warn-and-proceed is wrong here (the
  caller *named* the cycle) — refuse by name.
- `scaffold.promote_taxonomy(area) -> report`: move staged node files
  to `{area}/_taxonomy/` — the promotion path M37 A1 recorded as
  missing. Same discipline as `promote_reference`: never overwrites a
  live node (collision refuses by name), removes nothing else, returns
  what moved. The human gate does not move: promotion still happens AT
  the confirm gate, on the human's go — this verb is what the human's
  go *runs* instead of hand-moving files.
- Seeded nodes carry no evidence, so coverage reports them `claimed` —
  true, and exactly the day-one work plan. Out-of-scope cycles are
  never seeded; a seeded node the client's business contradicts is the
  LIBRARIAN's to propose removing (adjustability through the agents,
  per the ruling — deletion stays a proposed, human-executed move).

## Part C — The objective reaches the agents

- `brief.objective_block(area) -> str` (deterministic, read-only): the
  goal line, the in-scope cycles, and — the deliverable-aware half —
  per target deliverable, `definitions.serviceability(defn, area)`'s
  named gaps, prefixed with the deliverable's name. Guards the
  no-manifest case (an initial survey runs before the area has one):
  a missing manifest reports as "area not yet scaffolded", never a
  traceback. Unconfigured objective returns the explicit line "no
  engagement objective configured" — the block always renders, so a
  reader can tell absent-by-choice from absent-by-bug.
- **Surveyor dispatch** gains one key, `objective` (the block above),
  admitted in the brief's input list AND its closed reading contract.
  The sufficiency table gains the lens: a node serving a target
  deliverable's unserved binding is asked-about FIRST, and information
  requests may cite the deliverable ("the controls matrix needs the
  approval controls on payment steps — none are documented").
  The advisor's decision payload is UNTOUCHED (the orchestrator skill
  assembles the dispatch, as it does coverage today) — the M37
  hint-additivity pin stays exactly as it is.
- **Librarian**: the objective rides `engagement.py placement_brief`'s
  printed output (its input channel today) as one section; its triggers
  gain "a live node outside the objective's cycles → propose removal or
  scope amendment to the human."
- **Orchestrator skill**: the taxonomy dispatch row learns to include
  the objective block; the confirm-gate row learns `promote_taxonomy`.

## Acceptance sketch (pinned in tests/test_objective_m41.py, first)

- Objective accessor: parses, validates deliverable names (bad name
  refuses naming it) and cycle slugs (bad slug refuses naming it),
  absent → `configured=False`, area-layer shadowing works, unknown
  field refuses.
- Seed: L2 nodes staged with slug-stem filenames and parseable
  taxonomy-node shape (kernel.parse_entity accepts them); idempotent;
  never overwrites staged or live; unknown L1 refuses by name;
  seeded-then-promoted nodes coverage as `claimed`.
- Promote: staged nodes land live; live collision refuses; nothing
  else in `_reference/.proposed/` is touched; second call no-op.
- Objective block: contains goal + cycles + per-deliverable serviceability
  gap lines over the IPO fixture; no-manifest guard; unconfigured line;
  read-only (fingerprint).
- Agent prose: surveyor lists `objective` among inputs and inside the
  closed reading contract; librarian brief output carries the section.
- M37 dispatch-hint tests untouched and green; v1 suite green; zero v1
  tests edited.

## Complexity accounting (the standing test)

New state files: zero (one config block; staged nodes ride the existing
staging path). New gates: zero (promotion serves the EXISTING confirm
gate; it does not add one). New agent judgment: zero — the agents get
better INPUT, not new licenses; the objective narrows attention, the
skeleton gives a starting shape, and both are human-stated or
human-gated. The review risks to police: **skeleton worship** (a
surveyor that force-fits the client to the seeded shape instead of
refining it — the brief must say the skeleton is a proposal like any
other, and the reference stays advisory) and **objective creep** (the
objective block becoming a second profile that silently shades
rendering — it informs judgment upstream, it never touches the
plan/render path).

## Deferred (recorded, not built)

- Objective-driven deliverable scheduling (auto-materialize the
  targets) — the objective informs agents; verbs stay human-invoked.
- Cycle-level (L1) seeding of AREAS — scaffold already creates areas;
  wiring `objective.cycles` into engagement-level area scaffolding is
  a separate, larger intake-flow question.
- The M40-recorded wants (`expand_coverage_statuses`, a published
  root helper) — still recorded, still not absorbed here.
