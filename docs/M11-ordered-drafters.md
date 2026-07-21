# M11 — Ordered drafters (dependency waves + upstream context)

> **Status: BUILT.** See deltas at the bottom.

## Goal

Let drafting exploit real process order — a downstream drafter (payment run)
sees the finished fragment of its upstream (invoice intake) — **without**
giving up parallelism, the one-writer rule, or the zero-state idempotent loop.
Used lightly: ordering happens only where the sources clearly show a
producer→consumer handoff; an area with no hints behaves exactly as today.

## Why

Full isolation is what makes drafting cheap, parallel, and safe — but it costs
consistency at the seams: adjacent procedures describe the same handoff in
different words, and terminology drifts across drafters. Full sequential
drafting with everyone reading everyone would fix that at ~8× wall-clock,
position-dependent quality, and a standing temptation to rewrite other files.
The 90/10 point: **dependency-ordered waves + scoped read-only upstream
context + a cheap shared conventions digest**.

## Design

### Who decides what (the usual token boundary)

- **Taxonomy** (judgment): emits optional `upstream:` hints per L3 and applies
  the variant-vs-separate test. It is the only agent that sees the whole area
  with sources in hand *before* drafting — the drafters' `dependencies.yaml`
  is a product of drafting and cannot order round one.
- **Scaffold** (mechanics): validates the hints (known slugs only, no self)
  and bakes them into `manifest.json` procedure components.
- **Orchestrate advisor** (mechanics): computes the current wave from the
  manifest + the existing `unfilled` sentinels. **No new state files** — wave
  progress *is* which fragments are still unfilled, so the loop stays a pure
  function of folder state.

### `upstream:` hints (taxonomy → procedures.yaml)

```yaml
procedures:
  - slug: payment-run
    upstream: [invoice-intake]   # optional; only when sources clearly show
                                 # this procedure consuming another's output
```

Rules for the agent: hint **only** on a clear producer→consumer handoff
evidenced in the sources; when in doubt, omit — no hint means "no opinion",
never "no relationship". Hints never cross the L1 boundary.

### Variant vs separate procedure (the decision test)

Sharpened wording in the taxonomy agent (extends the M-existing near-duplicate
merge rule):

- **Variant** (one procedure): same trigger, same preparer role, same core
  system, same output — divergence is a conditional branch at a few steps
  (entity, region, payment method, vendor type). *A diamond inside one box.*
- **Separate**: different trigger, different preparer role, a real handoff
  between them (one's output is the other's input), or a distinct
  control/review point. *An arrow between two boxes.* The handoff arm of this
  test is exactly what triggers an `upstream:` hint on the downstream one.

Variants never need ordering between themselves — one file, one drafter.

### Wave scheduling (orchestrate `fill` guard)

`fill` now returns only the **current wave**: unfilled slugs whose upstream
slugs are not themselves unfilled. Everything else is reported as `deferred`.
The driver dispatches the wave in one parallel batch, the fragments lose their
`unfilled` sentinel, the advisor re-runs, and the next wave surfaces — the
normal loop, unchanged. Safety valves:

- Unknown/self upstream slugs are dropped at scaffold time (warned).
- A cycle (or a wave that computes empty while work remains) falls back to
  dispatching everything — degraded to today's behavior, never deadlocked.
- Partial-batch failure already works: failed procedures keep their sentinel
  and land in the next wave.

For each wave slug, the advisor also reports `upstream_files` — the filled
upstream fragment paths — so the driver can hand them to the drafter verbatim.

### Drafter: upstream context (read-only)

New optional dispatch input `upstream: [paths]`. The drafter reads those
fragments **only** to align the seams: how the handoff artifact is named, in
what system/state it arrives, and the registry nouns already in use. Hard
rules: never edit an upstream file (one writer per file); if the upstream
contradicts this procedure's own sources, do **not** silently harmonize —
document per own sources and raise a GAP naming the mismatch (precision over
recall, same as everywhere else).

### Conventions digest (terminology glue for everything ordering can't reach)

- Each drafter may write `_reference/conventions/{slug}.md` — ≤ ~10 lines of
  reusable phrasing decisions (report names as titled, date formats, recurring
  step formulations). Facts and nouns do NOT belong here (registry owns nouns).
- Every drafter reads all existing `_reference/conventions/*.md` before
  writing.
- One writer per file holds (per-slug files); the folder is advisory — it is
  **not** hashed into the registry hash, so writing a digest never churns the
  aggregate/reconcile signals.

## Acceptance

- Area with `upstream` hints: advisor emits fill waves in topological order;
  each wave lists correct `upstream_files`; final area reconciles clean.
- Area without hints: single wave containing all unfilled slugs — byte-for-byte
  the pre-M11 decision minus the new (empty) fields.
- Cycle in hints: advisor falls back to all-at-once and says so.
- Scaffold drops unknown/self upstream slugs with a warning; manifest carries
  only validated hints.

## Out of scope

- Ordering `apply_review` re-drafts (updates are targeted; seams already
  exist in the fragments being updated).
- Auto-deriving hints from `dependencies.yaml` on rebuilds (possible later:
  feed the previous area's dependencies view to taxonomy as a source).
- Cross-area / cross-L1 ordering.

## Deltas from design (post-build)

- None of substance; `deferred`/`upstream_files` naming as above.
