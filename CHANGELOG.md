# Changelog

All notable changes to CONSULT (the `consult-skill-suite` plugin) are recorded
here. Versions track `.claude-plugin/plugin.json`; each entry ties back to the
design ticket(s) under [`docs/`](docs/) where the contract is specified.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).
This project is pre-1.0 in spirit despite the `1.x` line — the `1.x` numbers
count feature milestones of the second (current) architecture, not a stability
guarantee.

## [Unreleased — 2.2.0]
The engagement-lens line: the 2026-08-16 architecture review's rulings
(D1–D6), ticketed as M44–M48.

- **M47 — the research pass** (`2.2.0-alpha.4`): day-zero public
  research enters staged — files under `components/_client/.proposed/`
  (company_profile.md and friends), promoted at the human's review gate
  by `scaffold --promote-client` (collision-refusing, `_client/`-only).
  Ledger entries carry `provenance: public`, and coverage_map excludes
  them from every status-advancing join: public sources inform the
  needs view, they never discharge it. Specified as a dispatch recipe
  for a web-capable session, not a new resident agent. Suite 1175.

- **M46 — the interview agenda** (`2.2.0-alpha.3`): the first consumer
  of the needs view — kernel/deliverables/interview-agenda.yaml (zero
  new binding verbs) + scripts/agenda.py render(area, role): a
  client-facing per-role agenda joining the needs view, the roles
  registry and the source ledger (confirm / missing / not yet asked /
  owed a read; never asks for what the ledger holds). Human-triggered
  only — no agent may generate one. Suite 1167.

- **M45 — the taxonomist** (`2.2.0-alpha.2`): surveyor + librarian
  merged into one `consult-taxonomist` (1,012 lines vs 1,079 combined,
  one dispatch context instead of two): objective intake, coverage/
  sufficiency, the ask agenda rendered from the needs view, placement,
  scoping reassessment, hygiene-fed grooming. The ruled change: it
  writes `_taxonomy/` and `_reference/.proposed/` directly as its files
  under one-writer — a fresh node set still stages for the human
  confirm gate; only live-node refinement is in-place. Everything
  outside its files stays notes-bus proposals. M44's A3 grammar
  amendment (`2.2.0-alpha.1` rider): `Grounds:` minted on the
  process-step GAP, `Nature:` aligned to the two mints,
  `Owner to confirm:` retired on process steps (v1 activity grammar
  untouched behind the compatibility gate). Suite 1158.

- **M44 — the needs view + the two-mint GAP** (`2.2.0-alpha.1`): gaps
  become a per-deliverable RENDER over the brain — `scripts/needs.py`
  computes, on demand and objective-driven, what each target
  deliverable still needs (binding-unserved via serviceability,
  coverage via the target's own coverage binding, recorded-gap via the
  open GAP callouts), registered as the `engagement-needs` derived
  view; and the drafter's GAP shrinks to two mints — a conflict or an
  evidenced absence — losing its ask half entirely (blocking is
  computed, the ask agenda is a render the surveyor shapes from the
  needs view, priority words never appear at capture). Suite 1144.

## [2.1.0] — M41–M43
The capture-layer line: the engagement gains a stated objective and a
starting skeleton, and the callout layer gains a doctrine, a bar, and a
groomer — so what the brain records is aimed at what the engagement is
for. Merged to `main` 2026-08-15.

- **M43 — the drafting path + the hygiene feeder** (`2.1.0-alpha.6`):
  the drafter contract finally teaches the kernel's own backbone type —
  the process-step path written from the fixture's grammar (LAW vs
  house style, the — from/— to edge lines as dependency facts,
  narrative + numbered sub-steps, honest absence as content), selected
  by a YOUR UNIT line derived mechanically from the area's deliverable
  components; the four CTRL fields declared on the callout declaration
  (their one home); and scripts/hygiene.py — three engagement-scoped,
  read-only candidate generators (duplicate-gaps at a
  fixture-calibrated threshold, gap-likely-answered via
  ledger.outstanding, ctrl-missing-field via the declared names)
  feeding the librarian's grooming trigger through the placement
  brief's CALLOUT HYGIENE section. Candidates, never verdicts. Suite
  1123 passing.
- **M42 — the callout doctrine** (`2.1.0-alpha.5`): what earns a
  callout, written once and encoded everywhere — the boundary rule
  never records a control (structure is not a fact), the four-field
  CTRL minting bar (performer / comparison / trigger / evidence; weak
  statements stay prose + one GAP), the operation-blocking GAP bar
  (the ask agenda belongs to the surveyor, enforced in its contract as
  a named miss), PAIN voiced-only, sub-steps carry no callouts
  (cross-owner performer = split signal), and the interaction contract
  (one fact one home, cross-referenced, joined only by the analyst).
  Librarian gains callout-population grooming (propose-never-edit);
  the drafter brief carries the engagement objective. Suite 1104
  passing.
- **M41 — the engagement objective + seeded skeleton**
  (`2.1.0-alpha.4`): the `objective:` config block (goal, target
  deliverables, in-scope cycles — validated, not decorative); the
  business-cycle skeleton seeded from the reference taxonomy's L1/L2s
  into the surveyor's staging path and promoted at the existing confirm
  gate (`seed_taxonomy` / `promote_taxonomy` — closing M37 A1's
  recorded promotion-path gap); `brief.objective_block` carrying the
  goal, the scope, and each target deliverable's serviceability gaps
  into the surveyor/librarian dispatches, so the taxonomy agents work
  toward a stated goal (deliverable-aware sufficiency, sharper client
  asks, out-of-scope-node proposals). Suite 1091 passing.

## [2.0.0] — M33–M40
The v2 line: generalize from desktop procedures to a deliverable-agnostic
process-knowledge model ("the brain") projected through user-supplied
deliverable definitions. Charter and ticket index: [`docs/v2/README.md`](docs/v2/README.md).
Merged to `main` 2026-08-15 with the compatibility gate green (M36): v1's
desktop procedure runs as a deliverable definition on the kernel,
normalized-identical to the v1 golden, with all v1 tests intact.

- **M40 — definition views to manifest** (`2.0.0-alpha.10`): the gap
  M38 recorded is closed — `definitions.materialize_views` reflects a
  definition's view blocks into an area manifest as canonical six-key
  derived components (plan-driven sync_profile: idempotent, preserving,
  never deleting, validate-before-replace, mechanical file/order
  policy), and `scripts/plan_views.py` ships the three missing python
  writers (information-requests via on-demand coverage,
  open-validations with SRC attribution, findings-by-theme accepted-
  only) through the ordinary PY_BUILDERS registry with zero shape-audit
  allowlist entries. The information-request and findings-report
  definitions render end-to-end for the first time. Suite 1071 passing.
- **M39 — analysis verbs: the spine complete** (`2.0.0-alpha.9`):
  findings as a register-class citizen with the lifecycle M30 deferred
  (grounds-or-refused, terminal reject, accepted-only rendering, the
  one-direction rule structural); three declaration-driven candidate
  generators over the brain (control gaps, handoff friction, pain
  inventory); the consult-analyst brief — the system's single
  assessment license (assess and propose; never write, never resolve,
  never rephrase). With this, every ticket of the v2 charter (M33–M39)
  is BUILT. Suite 1056 passing.
- **M38 — the second deliverable: generality proven** (`2.0.0-alpha.8`):
  the process & controls matrix — a table-first, IPO-fed, cross-step
  document v1 could never produce — ships as a definition + one new
  view-builder module through the existing registry, with zero engine
  special-cases (the one candidate was refused for lacking an honest
  discriminator). The IPO fixture engagement lands as frozen fixture #2
  with the five mandatory awkward cases. Review round-trip proven for
  the rebuild loop; row-comment routing pinned as a strict xfail with
  the exact fix identified. Suite 1045 passing.
- **M37 — surveyor + librarian** (`2.0.0-alpha.7`): the taxonomy
  becomes brain entities (`taxonomy-node` type, files under
  `_taxonomy/`); coverage is a pure, cache-free function (four statuses;
  conflicted = the lens-conflict record, v0's debt paid); the
  information-request deliverable ships (coverage's named consumer);
  the surveyor and librarian briefs replace taxonomy/placement for
  central mode (tag refinement, never minting; propose, never execute);
  drafter gains the conflicting-sources rule; intake becomes tagging;
  22 central-mode skill passages; advisor dispatch hints
  (initial→surveyor, incremental→librarian). Suite 1024 passing.
- **M36 — the compatibility gate: GREEN** (`2.0.0-alpha.6`): v1's
  desktop procedure runs as a deliverable definition on the kernel with
  all four proofs holding — 803 v1 tests untouched, the docx assembled
  FROM the plan normalized-identical to the committed v1 golden (v1
  render proven byte-deterministic; harness calibration-tested), advisor
  replay equivalence, aggregate set+byte equality. The deterministic
  layer follows the definition (hard-coded view list dead, skeletons
  from type declarations), duplicates retired, and a permanent
  allowlist audit bans hard-coded document shape outside kernel data.
  Suite 1005 passing. v2 has earned its v2.0.0 merge; the merge awaits
  the human go.
- **M35 — the deliverable-definition language** (`2.0.0-alpha.5`):
  `scripts/definitions.py` — deliverables as user files (shape /
  bindings / skin) with a four-stage fail-loud loader (syntax,
  vocabulary vs type declarations, serviceability as a "not yet"
  report, skin vs renderer capabilities), compile-to-plan, `_client/
  deliverables/` shadowing, and the M14 profile as a subtractive alias.
  Ships `kernel/deliverables/desktop-procedure.yaml` (v1 written down)
  and `render_glue.py` proving compiled plans executable against the
  real docx path. Suite 959 passing.
- **M34 — consumer wiring, central mode complete** (`2.0.0-alpha.4`):
  the engine is dual-layout behind one seam (`sources.central_root`) —
  advisor guards, briefs, the confirm gate, and the intake/adopt verbs
  all read the engagement ledger in central mode (route = register+tag,
  no copies, no sidecars; confirm gate = tag refinement via
  `ledger.retag`; `ledger.assess` answers guard 5 at engagement scope);
  v1 engagements byte-identical, guarded by 48 new characterization
  tripwires. Suite 933 passing.
- **M34 — centralized sources, ledger core** (`2.0.0-alpha.3`):
  `scripts/ledger.py` — the engagement-root SRC ledger: global minting
  with hash idempotence, loud per-area touches validation, park/status,
  the v1 consumption evidence rules one scope up (filled unconditional,
  updated needs an archived kind:source note, never-un-consumes), the
  all-areas move rule (file position is display; the ledger is truth),
  the read-only dual-layout adapter for v1 areas, and the `centralize`
  fold (hash dedupe, merged maps, remap table). Consumer wiring is the
  ticket's second build. Gate 17/17; suite 844 passing.
- **M33 — the brain kernel** (`2.0.0-alpha.2`): `scripts/kernel.py` —
  declared entity types loaded from `kernel/types/*.yaml` with a fail-loud
  loader; generic type-declaration-driven `parse_entity` (byte-equal to
  the v1 parsers over the frozen p2p corpus); `can_serve` serviceability
  checks. Ships `activity` (v1 written down) and `process-step` (the IPO
  backbone, sub-steps ratified). Frozen test corpus + acceptance gate
  added (`tests/fixtures/p2p-complete/`, `tests/test_kernel_m33.py`);
  suite 827 passing, zero v1 tests edited.
- Repo staged for v2: `v2` integration branch cut from `main`; v1.20.0
  preserved on the `v1.20-stable` branch; plugin version moved to
  `2.0.0-alpha.1`.

## [1.20.0] — M32
- Advisor guard-2 step-aside: when review notes and unassessed sources both
  wait and every queued note is merge-safe, they fold into **one** drafter
  batch instead of two consecutive passes.

## [1.19.1] — M31.1
- Orchestrator reuses warm agents for same-invocation follow-ups (fewer cold
  dispatches within a single build).

## [1.19.0] — M31
- Mode-scoped reading contract for update drafts: an update drafter reads only
  what its mode requires, keeping context flat on re-dispatch.

## [1.18.3] — [1.18.0]
- **1.18.3** — Appendix A bolds the PP id to match the paired IO id.
- **1.18.2** — kit filename budget: long slugs shorten on whole-word boundaries
  in kit paths.
- **1.18.1** — justified body prose; Role Dictionary "Reports To" shows the
  role name.
- **1.18.0** — final-render client readiness: TOC fix, Document Control block,
  readiness scorecard, register grooming.

## [1.17.4] — [1.17.0]
- **1.17.4** — taxonomy input discipline: coverage attestation, exclusive read
  fence, fail-loud on blocked source access.
- **1.17.3** — pin `model: sonnet` on the six worker agent defs (proven tier,
  no session-model inheritance).
- **1.17.2** — run-5 acceptance findings: placement-agent contract, honest
  free-form register refusal, nested-orchestrator guidance.
- **1.17.1** — M25 greenfield audit reports the intake block before the
  two-areas early return.
- **1.17.0** — M12/A3: cross-boundary seam block in group briefs;
  `consolidation_rejected` outcome.

## [1.16.0] — M30
- Register machinery: the `register` verb, citable-vs-context entry classes,
  and the rendered register appendix.

## [1.15.0] — M29
- Constitution coverage: a rules sweep plus three constitution checks over the
  M28 check registry — the engagement-level citation gate.

## [1.14.0] — M28
- Reconcile internals refactor: read-once cache, a check registry, a single
  sibling scanner, and a fence-handling fix.

## [1.13.0] — M24
- `brief --full`: whole-fragment placement read with a mechanical size guard.

## [1.12.0] — M25
- Engagement intake: one drop point at the engagement root, `route`/`park`
  verbs, and the `consult-intake` classifier contract.

## [1.11.0] — M26
- Engagement seams: `[[area/slug]]` cross-area tokens, taxonomy as the seam
  declarer, and a derived cross-area spine.

## [1.10.1] — [1.10.0]
- **1.10.1** — advisor emits a git-health advisory on every decision (warns
  once when checkpoints are off).
- **1.10.0** — knowledge placement (M24) + M12/A2: one-fact-one-home pass over
  the whole engagement.

## [1.9.0] — [1.8.0] — M12 consolidator
- **1.9.0** — `consolidate` packs buckets into agent groups (~5 fragments each).
- **1.8.1** — consolidator anchors must fit one hard-wrapped line.
- **1.8.0** — the M12 consolidator: cross-procedure consistency pass emitting
  review notes without touching fragments.

## [1.7.3] — [1.7.0]
- **1.7.3** — Windows console encoding fix (never crash on cp1252).
- **1.7.2** — sibling procedures appear in the ownership map.
- **1.7.1** — shingle-based shared-prose detection; loud note when cross-area
  checks are inactive.
- **1.7.0** — engagement-wide duplication audit.

## [1.6.1] — [1.6.0]
- **1.6.1** — the reference taxonomy is advisory: an unlisted L1 proceeds,
  never refuses.
- **1.6.0** — cross-procedure / cross-area dedup ownership boundaries.

## [1.5.0]
- Subagent work-order brief (`brief.py`): a deterministic per-area work order
  handed to each dispatched subagent.

## [1.4.6] — [1.4.0]
- Reviewer-round upgrades across the render and drafter path: targeted-edit
  update mode (update = Edit, never full regeneration), synthesis-agent edit
  discipline, table-cell pipe guards, `Grep`/`Glob` granted to subagents, and
  Fixed Assets added as an L1 in the reference taxonomy.

## [1.3.0]
- Format, safeguard, and review-flow upgrades: American-English enforcement,
  a mandatory TOC on every folder render, untracked-edit detection in the
  return trip, and register vanish/drift/dangle protections generalized to
  every register pairing.

## [1.0.0] — [1.2.x] — the second-architecture build (M0–M11)
The initial rebuild on the **two-database model** (procedures = verbs,
reference registry = nouns; everything else a regenerated view):
- **M0** taxonomy + scaffold, **M1** single-H1 template, **M2** splitter +
  manifest, **M3** mechanical aggregator, **M4** docx builder,
  **M5** synthesis agents (dependencies + RACI), **M6** scoping reassessment
  and the notes bus, **M7** the read-only orchestrator/state advisor,
  **M8** review loop, **M9** per-owner review kits + dual-mode render,
  **M10** deterministic tracked-changes apply, **M11** ordered drafters
  (dependency waves).
- Later hardening folded in: M13 engagement config, M14 document profile,
  M16 seven-section model, M17 stage gates + sticky holds, M18 advisor honesty,
  M19/M22 reconcile substance + constitution, M21 render-signal, M23 section
  identity by slug.

## v0 — the first architecture (archived)
The original taxonomy-driven diagnostic engine, built on a shared
`state.json` / `register.json` state machine, is preserved at commit
**`a119d22`** (`git checkout a119d22` to read the v0 tree). Its shared mutable
state and central ID minter are the two costs the current architecture was
designed to remove — see [`docs/retrospective-v0.md`](docs/retrospective-v0.md).
