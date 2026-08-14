# Changelog

All notable changes to CONSULT (the `consult-skill-suite` plugin) are recorded
here. Versions track `.claude-plugin/plugin.json`; each entry ties back to the
design ticket(s) under [`docs/`](docs/) where the contract is specified.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/).
This project is pre-1.0 in spirit despite the `1.x` line — the `1.x` numbers
count feature milestones of the second (current) architecture, not a stability
guarantee.

## [Unreleased — 2.0.0]
The v2 line: generalize from desktop procedures to a deliverable-agnostic
process-knowledge model ("the brain") projected through user-supplied
deliverable definitions. Charter and ticket index: [`docs/v2/README.md`](docs/v2/README.md).
Milestones accumulate here as they land (M33+).

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
