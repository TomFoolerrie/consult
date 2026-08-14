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

## The three layers

### 1. The brain kernel (deliverable-agnostic)

The kernel contains **no domain schema**. It knows only:

- **Typed entities** with declared fields (an "activity" with A–H sections is
  a schema *instance*, not the schema).
- **Relations** between entities (typed, slug-addressed).
- **Evidence links** — every claim traces to a SRC- registered source.
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
| [M33](M33-brain-kernel.md) | Brain kernel: typed entities, relations, evidence, identity — extracted from doc_model/callouts/sources/aggregate (spec drafted) |
| M34 | Deliverable-definition language + fail-loud loader (document profile promoted to user space) |
| M35 | **Compatibility gate:** A–H + docx renderer re-expressed as definition #1; v1 tests pass unchanged |
| M36 | Second deliverable type (generality proof) |
| M37 | Analysis verbs → findings registers |

This spine is provisional; tickets get full contract specs (in the v1 M-ticket
style) before implementation, and the list will grow as v2 ideas land.

## Version discipline

`plugin.json` carries `2.0.0-alpha.N` on the `v2` branch. Landed milestones
accumulate under `## [Unreleased — 2.0.0]` in [`../../CHANGELOG.md`](../../CHANGELOG.md).
`2.0.0` is stamped at the merge to `main`.
