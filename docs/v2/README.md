# CONSULT v2 — Architecture Charter

**Status: charter drafted; ticket specs pending.**
v2 development happens on the `v2` branch. v1.20.0 is preserved on
`v1.20-stable`. `main` stays v1 until v2 passes the compatibility gate
(see below), then merges as `v2.0.0`.

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

**The step-granularity rule (to pressure-test at design time):** a step is
the unit at which **owner, system, or control changes**; anything finer is
detail inside a transformation.

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
running on the kernel, producing byte-compatible output under the existing
800+ v1 tests, unchanged. If v1's own deliverable cannot be expressed in the
definition language, no user's can. The completed procure-to-pay run on
`claude/repo-primer-bidlgp` is the standing regression fixture.

## Ticket spine (provisional — specs to be written)

Numbering continues from v1 (M0–M32 under [`../`](../)).

| Ticket | Scope |
|---|---|
| [M33](M33-brain-kernel.md) | Brain kernel: typed entities, relations, evidence, identity — extracted from doc_model/callouts/sources/aggregate; ships the IPO `process-step` type sketch (spec drafted) |
| [M34](M34-centralized-sources.md) | Centralized sources: one engagement-root ledger, per-consumer consumption, intake becomes tagging (spec drafted) |
| [M35](M35-deliverable-definitions.md) | Deliverable-definition language: shape/bindings/skin, four-stage fail-loud loader, compile-to-plan (spec drafted) |
| [M36](M36-compatibility-gate.md) | **Compatibility gate:** v1 re-expressed as a definition over the kernel; 803 tests + byte-identical render (spec drafted) |
| [M37](M37-surveyor-librarian.md) | Surveyor + librarian: taxonomy as brain entities, derived coverage, info-request deliverable, lens-conflict rule (spec drafted) |
| [M38](M38-second-deliverable.md) | Second deliverable — process & controls matrix over an IPO fixture; zero engine edits (spec drafted) |
| [M39](M39-analysis-verbs.md) | Analysis verbs → findings register class, consult-analyst, findings report (spec drafted) |

This spine is provisional; tickets get full contract specs (in the v1 M-ticket
style) before implementation, and the list will grow as v2 ideas land.

## Version discipline

`plugin.json` carries `2.0.0-alpha.N` on the `v2` branch. Landed milestones
accumulate under `## [Unreleased — 2.0.0]` in [`../../CHANGELOG.md`](../../CHANGELOG.md).
`2.0.0` is stamped at the merge to `main`.
