# M41 build plan — engagement objective + skeleton

> Foundation for [`M41-engagement-objective.md`](M41-engagement-objective.md).
> Deterministic gate: `tests/test_objective_m41.py` (per-class skips until
> each verb exists). Ground rules as ever: exclusive file ownership, zero
> v1 tests edited, friction reported verbatim, suite green per commit.
> Opens the 2.1.0 line (`2.1.0-alpha.N`).

## Design pins

- Objective accessor follows client_config's `profile:`/`hold:` template
  TO THE LETTER (typed dataclass, `OBJECTIVE_FIELDS` allowlist,
  fail-loud parser, `configured=False` when the key is absent,
  `report_line()`, layer provenance). Deliverable names validate via
  `definitions.load_definition(name, area)`; cycle slugs against the
  effective reference taxonomy's L1 slugs (client `taxonomy:` override
  wins; `scaffold.DEFAULT_TAXONOMY` otherwise). Import definitions
  lazily inside the parser (client_config must stay cheap).
- Seed/promote live in scaffold.py (the module that owns staging and
  promotion today). Seeded node files use the surveyor's own template
  shape and MUST parse via `kernel.parse_entity` with the taxonomy-node
  declaration. Never overwrite staged or live; promote never removes
  anything else from `.proposed/`.
- `brief.objective_block(area)` composes: goal, cycles, then per target
  deliverable its `definitions.serviceability` gap lines. Guard the
  missing/corrupt-manifest case (initial surveys pre-date manifests).
  The ADVISOR (orchestrate.py) is not touched — the skill assembles the
  dispatch. Do not trip test_dispatch_hints_m37's additivity pin.
- Agent prose: the surveyor's closed reading contract ("your inputs are
  EXACTLY these") must ADMIT the objective key or the agent is
  instructed to ignore it. Skeleton-worship guard language per the spec.

## Work packages

### WP-O1 — the objective accessor
Owns `scripts/client_config.py`. Targets: TestObjective.

### WP-O2 — seed + promote
Owns `scripts/scaffold.py` (additive: `seed_taxonomy`,
`promote_taxonomy`, CLI verbs if scaffold exposes verbs that way — read
its main() first). Targets: TestSeed, TestPromote.

### WP-O3 — the objective block
Owns `scripts/brief.py` (additive: `objective_block` + CLI exposure
consistent with the module) and the objective section in
`scripts/engagement.py`'s `placement_brief`. Depends on WP-O1's
accessor landing first (reads `client_config.objective`).
Targets: TestObjectiveBlock, TestLibrarianBrief.

### WP-O4 — agent + skill prose (orchestrator reviews)
Owns `agents/consult-surveyor.md`, `agents/consult-librarian.md`,
`skills/consult-orchestrate/SKILL.md` (taxonomy dispatch row + confirm
gate row), + a self-review note `docs/v2/notes/m41-prose-self-review.md`.
Targets: TestAgentProse (mechanical greps).

## Sequencing
WP-O1 ∥ WP-O2 → WP-O3 → WP-O4 → close-out (2.1.0-alpha.4): ticket BUILT
+ amendment, CHANGELOG opens 2.1.0, charter spine row, version bump.
