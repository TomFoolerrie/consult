# CONSULT v2 — Architecture Charter

**Status: RELEASED AS 2.4.0 (2026-08-22)** — the spine (M33–M39) plus
M40 shipped as 2.0.0; M41–M43 shipped as 2.1.0; M44–M49 (the
engagement-lens line) shipped as 2.2.0; M50–M55 (the backlog line: the
gap discriminator, structured serviceability, the merged taxonomist
brief, engine housekeeping, table-row comment routing, the recorded
wants) shipped as 2.3.0; the hardening line M56–M64 shipped as
2.3.1; the brain line M65–M70 (capture is the brain, documents are
renders — from the first live run and its audit) shipped as 2.4.0. **Authoritative suite count: 1,588 collected, all
passing** (`python3 -m pytest --collect-only -q`; the release checklist
owns this number) with ZERO xfails (the standing M38 table-routing
xfail retired in M54) and ZERO skips (the M64 skip budget enforces
this structurally), the
compatibility gate green, every shipped definition rendering
end-to-end. All merges made on the human's explicit go.
v1.20.0 is preserved on `v1.20-stable`.
The recorded backlog shipped as **M50–M55** (2.3.0): the gap discriminator
(M50), structured serviceability (M51), the merged taxonomist brief
(M52), engine housekeeping (M53), table-row comment routing (M54), and
the recorded wants — ledger verb + appendix optionality (M55).
The hardening line **M56–M64** shipped as **2.3.1** (2026-08-20),
written from an adversarial review of 2.3.0 at `main` @ 8b22e9e — 29
verified findings folded into nine tickets by shared root cause:
evidence identity in the ledger (M56, carries the review's one
critical), callout addressing (M57), the drafter trust boundary (M58),
docx text fidelity (M59), notes-bus integrity (M60), the xlsx round
trip (M61), loader vocabulary honesty (M62), fail-loud edges (M63),
and suite/CI guardrails (M64).
Items NOT ticketed, each waiting on a ruling or a trigger: the
PAIN↔CTRL cross-reference field names (M42 A1 — an open human ruling);
the deeper cut into the drafter's shared law (M48 A1 — a candidate,
worth it only if dispatch cost bites); a definitions.py binding verb
for derived-view feeds (M46 A1 — waits for a third consumer); the
raci/dependencies fold (M48 roster — lands with the v1 retirement,
not before); typing `company_profile.md` (M47 — waits until something
needs to bind it); and a de-dupe rule for multiple `coverage:` bindings
on one definition (M44 A2 — waits until such a definition exists).

## The shift

v1 turns messy finance-process sources into **one deliverable shape**: a
CFGI-branded desktop-procedure Word document, one per L1 area. v2 inverts the
emphasis: the product is the **process-knowledge model** ("the brain"), and
the desktop procedure becomes *one deliverable definition among several* —
the first of any number of user-supplied shapes (narratives, controls/gap
matrices, analyses, future-state comparisons).

What v1 got right and v2 keeps unchanged in spirit:

- **Two hand-authored databases; everything else a regenerated view.**
- **Drift-free rules:** numbers only at render; cross-refs as stable slug
  tokens; nouns bound by explicit meta blocks, never prose-scraping.
- **Fail-loud parsing.** Ambiguity refuses with a precise error; it never
  renders half-empty.
- **One writer per file; isolated subagents; a read-only state advisor.**
- **Contract-first M-tickets, one capability at a time, tests as the law.**

## The pipeline inversion

v1's pipeline is *route sources to areas, draft documents*. v2's is:

> **intake (tag) → survey (taxonomy + coverage + information requests) →
> capture (fill the brain, IPO-shaped, evidence-linked) → project (any
> deliverable definition)**

Four decisions, agreed 2026-08-14:

### Centralized sources

One `_sources/` tree and one SRC registry at the **engagement root**; area
folders hold **no source files**, only consumption records ("this area read
SRC-004 into this step"). *Processed* becomes per-consumer, not per-file — a
transcript spanning two areas is consumed twice, moved never. Intake
(`consult-intake`) stops copy-routing and becomes pure tagging; its judgment
(what does this document inform?) survives unchanged. Per-area "which sources
are mine to read" scoping — the discipline that keeps drafter context flat —
becomes a tag query instead of a folder listing. The M29 cross-area
citation-locality tension dissolves: there are no "another area's sources,"
only sources, with consumption records showing who read what.

### Process understanding is the backbone; IPO is the neutral shape

The brain's core entity is the **process step**, shaped as
**inputs → transformation → outputs** (what arrives and from where; what is
decided/calculated/checked, by whom, in which system; what exists afterward
and where it goes) plus the governance layer v1 already captures: controls,
exceptions/gaps, evidence. v1's seven-section model is a *presentation*
schema; in v2 it is a deliverable-definition mapping over the IPO core
("Before You Start" projects inputs; "Outputs & Evidence" projects outputs).
**Pain points are first-class observations**: what interviewees voice as
pains, worries, or risks is captured in their framing — attributed and
evidenced, recorded by drafters as a callout, never assessed by them
(assessment is the analysis layer's job; these callouts are its raw
material). Desktop-procedure specifics — navigation clicks, screenshots —
are an **optional detail layer** on a transformation: present when sources
carry it and a deliverable requests it, never demanded by the brain. IPO edges make
cross-step dependency derivation mechanical (inputs/outputs ARE the arrows),
which pressures `consult-dependencies` to shrink from judgment agent toward
derived view.

**The step-granularity rule (RATIFIED, visual review 2026-08-14):** a step
is the unit at which **owner, system, or control changes** — where
accountability shifts. The "how" inside a step is an ordered list of
**sub-steps** (structured, optional, same owner/system throughout);
deliverables choose their altitude — the desktop procedure unfolds
sub-steps, a controls matrix reads only step lines. The surveyor coaches
drafters on where the breaks go.

### The taxonomy agent multiplies: surveyor + librarian

v1's taxonomy agent secretly does two jobs; v2 names and splits them.

- **The surveyor (upfront):** proposes the business taxonomy AND assesses
  evidence sufficiency per node — outputting a **coverage map** and an
  **information-request list** *before any drafting tokens are spent*. The
  info-request list is itself an early deliverable definition. The
  sufficiency pass is the natural home for v0's unpaid lens-conflict debt
  (two sources disagree → raise a gap, never guess).
- **The librarian (ongoing):** curates the brain's organization as knowledge
  accumulates — a new source revealing a missing L3, a step that should
  split, two areas claiming one process. Unifies v1's scoping-reassessment
  (M6) and placement (M24) embryos.

The taxonomy stops being per-area config and becomes **first-class brain
entities** — taxonomy nodes with slugs, evidence links, and coverage status,
organizing the steps beneath them. Human gates stay where they are: taxonomy
confirmation remains the human's call; what multiplies is the agent work
feeding the gates.

### The one hard guardrail

The coverage map is **derived** — computed from evidence links per taxonomy
node — never a hand-maintained status file. A hand-edited coverage file is
v0's `state.json` reborn, and it is how this architecture would die.

## The three layers

### 1. The brain kernel (deliverable-agnostic)

The kernel contains **no domain schema**. It knows only:

- **Typed entities** with declared fields (the IPO process step is the
  shipped default *instance*; the v1 A–H activity is another instance kept
  for the compatibility gate — neither is the schema).
- **Relations** between entities (typed, slug-addressed).
- **Evidence links** — every claim traces to a SRC- registered source in the
  **engagement-level** registry (centralized sources).
- **Identity** — stable slugs assigned once at creation.
- **Derived views** — regenerated projections, never hand-maintained.
- **Reconcile gates** — integrity checks over IDs, tokens, bindings.

Most of this exists in v1 already (doc_model, sources, callouts, reconcile);
the kernel work is extraction and generalization, not invention.

### 2. Deliverable definitions (user-space, declarable)

A deliverable definition is data a user brings, in three layers:

1. **Shape** — the section/structure spec: what sections exist, hand-authored
   vs. generated, repeat-per-what.
2. **Bindings** — declared queries against the brain ("this table = roles ×
   activities join"), never inferred.
3. **Skin** — docx/pptx/xlsx formatting, branding, numbering.

Definitions are validated fail-loud at load time: a binding the model cannot
serve refuses with a precise error. v1's document profile (M14) and
engagement config (M13) are the embryo of this layer.

### 3. Renderers and analyses (pluggable consumers)

- The docx builder becomes one **deliverable adapter** among N, each declaring
  what it needs from the model.
- **Analysis verbs** are a new consumer class: they read the graph and emit
  *findings* into engagement registers (M30 machinery), rather than views.
- Review loops are **per-deliverable-type** (the tracked-changes/kits pipeline
  is the Word one), not universal.

## The compatibility gate

v2 is not done — and does not merge to `main` — until the existing v1
desktop procedure is re-expressed as a **user-space deliverable definition**
running on the kernel, producing **semantically identical** output
(normalized-XML comparison, per M36 A1) under the existing 800+ v1 tests,
unchanged. If v1's own deliverable cannot be expressed in the definition
language, no user's can. The completed procure-to-pay run on
`claude/repo-primer-bidlgp` is the standing regression fixture.

**The old-engagement question (RESOLVED, visual review 2026-08-14):** new
engagements are born step-shaped; existing v1 engagements live on the
adapter indefinitely. Converting one real engagement (e.g. the P2P run) is
an optional **validation exercise** once M37 lands — a good test, never a
migration requirement.

## Ticket spine (provisional — specs to be written)

Numbering continues from v1 (M0–M32 under [`../`](../)).

| Ticket | Scope |
|---|---|
| [M33](M33-brain-kernel.md) | Brain kernel: declared types, generic parse_entity, can_serve; ships `activity` + `process-step` (**BUILT**, 2.0.0-alpha.2, gate 21/21) |
| [M34](M34-centralized-sources.md) | Centralized sources: ledger + adapter + centralize + full consumer wiring (**BUILT**, alpha.4, gates 34/34; agent prose lands with M37) |
| [M35](M35-deliverable-definitions.md) | Deliverable-definition language: four-stage loader, compile-to-plan, profile alias, shipped desktop-procedure.yaml (**BUILT**, alpha.5, gates 26/26) |
| [M36](M36-compatibility-gate.md) | **Compatibility gate: GREEN** — definition-assembled docx golden-equal, advisor replay equal, audit armed (**BUILT**, alpha.6; v2.0.0 merge awaits human go) |
| [M37](M37-surveyor-librarian.md) | Surveyor + librarian: taxonomy-node entities, pure coverage, info-request deliverable, lens-conflict landed (**BUILT**, alpha.7, gates 19/19) |
| [M38](M38-second-deliverable.md) | Second deliverable — the matrix renders over the IPO fixture with zero engine special-cases (**BUILT**, alpha.8, gates 21/21 + 1 pinned xfail) |
| [M39](M39-analysis-verbs.md) | Analysis verbs: findings lifecycle, candidate generators, the analyst license (**BUILT**, alpha.9, gate 11/11) |
| [M40](M40-definition-views.md) | Definition views to manifest: the materialize verb + the missing writers; every shipped definition renders (**BUILT**, alpha.10, gate 15/15) |
| [M41](M41-engagement-objective.md) | The engagement objective: seeded cycle skeleton + goal-aware taxonomy agents (**BUILT**, 2.1.0-alpha.4, gate 20/20) |
| [M42](M42-callout-doctrine.md) | The callout doctrine: minting bars, sub-step rules, the interaction contract; population judgment moves to surveyor/librarian (**BUILT**, 2.1.0-alpha.5, gate 13/13) |
| [M43](M43-drafting-path-hygiene.md) | The process-step drafting path + the hygiene feeder: YOUR UNIT line, declared CTRL fields, three grooming generators (**BUILT**, 2.1.0-alpha.6, gate 19/19) |
| [M44](M44-needs-view.md) | The needs view: per-deliverable gaps as a render + the two-mint GAP (**BUILT**, 2.2.0-alpha.1, gate 21/21) |
| [M45](M45-taxonomist-merge.md) | The taxonomist: surveyor + librarian merged, direct write over `_taxonomy/`, confirm gate unchanged (**BUILT**, 2.2.0-alpha.2, gate 10/10) |
| [M46](M46-interview-agenda.md) | The interview agenda: a definition over the needs view × roles × ledger; generation human-triggered, ad hoc (**BUILT**, 2.2.0-alpha.3, gate 9/9) |
| [M47](M47-research-pass.md) | The research pass: staged `_client/.proposed/` files, public provenance never discharges a need, day-zero PBC list (**BUILT**, 2.2.0-alpha.4, gate 8/8) |
| [M48](M48-efficiency-pass.md) | The efficiency pass: drafter contract split by unit, cheap-tier revise path, roster audit (**BUILT**, 2.2.0-alpha.5, gate 10/10) |
| [M49](M49-analyst-dispatch.md) | The analyst dispatch path: `analysis.py brief` CLI, the conflict-records extractor, `findings.for_area`, the skill passage (**BUILT**, 2.2.0-alpha.6, gate 14/14) |
| [M50](M50-gap-discriminator.md) | The gap discriminator: the `Nature:` enum declared on the type, needs/agenda consume it, the unconsumed-source fixture (**BUILT**, 2.3.0-alpha.1, gate 18/18) |
| [M51](M51-structured-serviceability.md) | Structured serviceability: the "not yet" report becomes attributed records; the broken-area refusal (**BUILT**, 2.3.0-alpha.2, gate 10/10) |
| [M52](M52-taxonomist-brief.md) | One taxonomist brief: survey + curation work orders assembled in one place, a kind line selects emphasis (**BUILT**, 2.3.0-alpha.3, gate 9/9) |
| [M53](M53-engine-housekeeping.md) | Engine housekeeping: the kind resolvers' public home, docstring refresh, the root helper, the ordering flake (**BUILT**, 2.3.0-alpha.4, gate 8/8) |
| [M54](M54-table-row-routing.md) | Table-row comment routing: v1 appendix routing characterized, first-cell slug resolution, the M38 xfail retires (**BUILT**, 2.3.0-alpha.6, gate 7/7, zero xfails) |
| [M55](M55-recorded-wants.md) | Recorded wants: the human-readable ledger verb + appendix-controls optionality in user space (**BUILT**, 2.3.0-alpha.5, gate 9/9) |
| [M56](M56-evidence-identity.md) | Evidence identity: the ledger stops keying bytes by basename — credit/centralize/status collision fixes (**BUILT**, 2.3.1-alpha.1, gate 10/10) |
| [M57](M57-callout-addressing.md) | One address per callout: procedure-qualified grounds, `for_area` joins fixed, `node_steps` keyed by slug (**BUILT**, 2.3.1-alpha.2, gate 8/8) |
| [M58](M58-drafter-trust-boundary.md) | The drafter trust boundary: review items are client data, not orders; the agent grant audit (**BUILT**, 2.3.1-alpha.3, gate 18/18) |
| [M59](M59-docx-text-fidelity.md) | Docx text fidelity: angle-bracket prose survives, escapes stay literal, lists keep their depth (**BUILT**, 2.3.1-alpha.4, gate 10/10) |
| [M60](M60-notes-bus-integrity.md) | Notes-bus integrity: control-char-safe emitter, store-form dedup, atomic writes, no silent-empty load (**BUILT**, 2.3.1-alpha.5, gate 74/74) |
| [M61](M61-xlsx-round-trip.md) | The xlsx round trip: XML-legal writer, date/bool-aware reader, size caps on client files (**BUILT**, 2.3.1-alpha.6, gate 8/8) |
| [M62](M62-loader-vocabulary-honesty.md) | Loader vocabulary honesty: declared callout prefixes parse, `repeat.over` validated, one `order` rule (**BUILT**, 2.3.1-alpha.7, gate 9/9) |
| [M63](M63-fail-loud-edges.md) | Fail-loud edges: front matter preserved, per-anchor deletion warnings, aggregate refuses the unlisted L2, the render's no-op validate_manifest call gets teeth (**BUILT**, 2.3.1-alpha.8, gate 8/8) |
| [M64](M64-guardrails-that-guard.md) | Guardrails that guard: the skip budget, pinned deps, named assertions, CI triggers, README counts (**BUILT**, 2.3.1-alpha.9, gate 6/6) |
| [M65](M65-confirm-gate-consumes-the-survey.md) | The confirm gate promotes the survey: staged taxonomy nodes survive `--confirm`, collision refuses whole, advisor flags uncommitted proposals (**BUILT**, 2.4.0-alpha.1, gate 12/12) |
| [M66](M66-objective-shaped-capture.md) | Capture is the brain: process-step is the v2 capture unit, documents are renders, furniture leaves capture, the node guard (**BUILT**, 2.4.0-alpha.6, gate 77/77 across two work packages) |
| [M67](M67-interpreter-honesty.md) | Interpreter honesty: version gates before first-party imports, missing PyYAML refuses by name, the floor documented (**BUILT**, 2.4.0-alpha.2, gate 48/48) |
| [M68](M68-central-mode-finishes-the-move.md) | Central mode finishes the move: root-resolved paths, engagement-wide checkpoints, route-before-scope, honest messages (**BUILT**, 2.4.0-alpha.3, gate 13/13) |
| [M69](M69-derived-views-read-the-type.md) | The derived views read the type: view slots from the declaration, declared-Performer preparer, honest absences (**BUILT**, 2.4.0-alpha.7, gate 14/14) |
| [M70](M70-vocabulary-floor-leftovers.md) | Vocabulary-floor leftovers: aggregate/reconcile/render build callout grammars from declarations (**BUILT**, 2.4.0-alpha.4, gate 12/12) |
| [M71](M71-the-tail-reads-the-objective.md) | The tail reads the objective: draft-ready/render prose becomes deliverable-aware, names the analyst path (**TICKETED**) |
| [M72](M72-one-id-width.md) | One id width: drafter contract and skeletons teach 2-digit local callout ids; display transform tolerance pinned (**TICKETED**) |
| [M73](M73-run-2-paper-cuts.md) | Run-2 paper cuts: taxonomist contract catches up to M65, first-checkpoint sweep disclosure, missing-folder error states both readings (**TICKETED**) |

This spine is provisional; tickets get full contract specs (in the v1 M-ticket
style) before implementation, and the list will grow as v2 ideas land.

## Version discipline

`plugin.json` carried `2.0.0-alpha.N` during the build. Landed milestones
accumulated under the 2.0.0 section in [`../../CHANGELOG.md`](../../CHANGELOG.md).
`2.0.0` is stamped at the merge to `main`.
