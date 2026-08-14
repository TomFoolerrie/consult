# M34 — Centralized sources: one ledger, per-consumer consumption, intake as tagging

> **Status: DRAFT — contract under review.** Companions: M33 (whose
> engagement-scoped evidence API this ticket physically implements), M25
> (whose intake judgment survives and whose copy-routing this ticket
> retires), M29 (whose cross-area citation-locality tension this ticket
> dissolves), M30 (whose register provenance gains engagement-global SRC
> ids to point at). Charter: [`README.md`](README.md).

## The problem this solves

v1 stores sources **per area**: each `components/<area>/_sources/` tree with
its own `_reference/sources.yaml` registry and its own area-local SRC ids.
That layout forced three workarounds, each carrying real cost:

1. **Intake is a copy-router.** M25's `route` verb COPIES a staged document
   into every area it informs. A transcript spanning P2P and R2R exists
   twice on disk, with two SRC ids, two `touches` sets, and two independent
   processed lifecycles — the same evidence, forked.
2. **Citation locality is a doctrine because it has to be.** M29's
   cross-area citation rules exist because "another area's source" is a
   real category in v1 — an area cannot cite what its own ledger doesn't
   hold, so facts cross areas by register-with-provenance workarounds even
   when both areas read the same physical document.
3. **`SRC-004` is ambiguous at engagement scope.** Register provenance
   writes `SRC-004 (p2p)` because the bare id collides across areas; every
   engagement-level consumer (placement, consolidator, the coming surveyor)
   must carry area qualifiers by hand.

The v2 shape (charter, agreed 2026-08-14): **one `_sources/` tree and one
SRC ledger at the engagement root; areas hold no source files** — only
consumption records. A source is registered once, tagged to what it
informs, consumed per-consumer, and **moved never** until every tagged
consumer is done: *consumed twice, moved never*.

## Part A — The layout and the ledger

```
<engagement root>/
  _sources/
    sources.yaml        THE ledger — engagement-global SRC ids (one minter)
    new/                unconsumed-by-someone source files
    processed/          fully-consumed source files
    parked/             staged files declined with a reason (absorbs
                        intake/parked/)
  components/
    <area>/             NO _sources/, NO source registry
```

- **`intake/` is retired as a folder; its job survives as a state.** The
  drop point IS `_sources/new/`. A file in `new/` without a ledger entry is
  *unregistered* (v1's "unprocessed intake") — the loud-until-empty block
  moves from intake-folder scanning to a ledger/folder diff. `park` moves
  to `_sources/parked/` with a reason, unchanged in spirit.
- **One SRC minter.** Ids are engagement-global, minted at registration in
  ledger order — the same discipline the area registry has today, at one
  scope up. Register provenance drops its hand-written area qualifier.
- **Ledger entry shape** (generalizing today's entry): id, file, hash
  (idempotent re-drop detection, kept verbatim from M25), registration
  date, and **tags** — the per-area `touches` sets, now namespaced:
  `touches: {p2p: [receive-invoice, match-po], r2r: [accrue-ap]}`.
  Entity slugs stay area-scoped (M33's identity model is unchanged); the
  tag map is the engagement-global view of them.
- **Ownership**: `sources.yaml` keeps exactly the v1 writer set — the
  intake/registration verb and `mark-processed`. Never an agent, never a
  hand edit in contract. `touches ⊆ manifest-slugs` validation (M22 check
  2, the F14 typo trap) now checks each area's slice against that area's
  manifest — same defect, same message, per slice.

## Part B — Per-consumer consumption; the move rule generalizes

v1's consumption accounting survives **verbatim, one scope up**:

- `consumed:` on a ledger entry becomes a namespaced map mirroring
  `touches` — the durable, never-reset, per-slug record, exactly as today
  (cross-batch crediting, `--filled` unconditional / `--updated`
  evidence-required, the never-un-consumes rule — all unchanged).
- **The move rule is the same sentence at engagement scope**: a file moves
  `new/` → `processed/` when its ENTIRE touches map is covered by its
  consumed map — across all areas, not within one. Folder state stays
  self-describing (a file in `new/` means *someone still owes it a read*),
  and the per-area question "is this source outstanding FOR ME?" becomes a
  ledger query (`touches[area] ⊄ consumed[area]`), not a folder listing.
- The advisor's guard that re-fires `taxonomy` on unassessed sources reads
  the same query — per-area outstanding-ness is derived from the ledger,
  never from file position. **File position is display; the ledger is
  truth.** (This is the numbers-only-at-render rule applied to lifecycle.)

## Part C — Intake becomes tagging

`consult-intake`'s judgment — *what does this document inform?* — survives
untouched. What changes is what the verb does with the answer:

- `route <file> --to p2p,r2r` **registers and tags**: mints the SRC id,
  writes the touches map (slugs supplied per area, or area-level pending
  taxonomy refinement), writes the relevance sidecar content INTO the
  ledger entry (the `.route.md` sidecar file is retired — its content was
  always ledger-shaped), and moves the file nowhere. Idempotency by hash,
  kept.
- **No copies exist**, so nothing forks: one file, one id, one hash, N
  tags. The drafter's brief lists "your sources" by ledger query — the
  same flat-context discipline as today's folder listing, better substrate.
- A source arriving mid-engagement for an already-drafted area follows the
  existing update path (M6 notes bus) — unchanged; only the lookup moved.

## Part D — What this dissolves and what it feeds

- **M29 citation locality**: mostly dissolved. There is no "another area's
  source"; there are sources, and consumption records showing who read
  what. A drafter cites any SRC id its brief handed it. The register
  bootstrap (M30 A1's citation loop) is unchanged but its provenance ids
  are now unambiguous. The residual rule worth keeping: a drafter still
  reads ONLY sources tagged to it — scoping discipline is about context
  flatness now, not ledger reachability.
- **The surveyor (M37)** gets its substrate for free: coverage per taxonomy
  node is a join over one ledger (which nodes have tagged sources, which
  tagged sources are unconsumed, which nodes have none) — impossible to
  compute cheaply across N per-area ledgers, trivial over one.

## Migration stance

- **Dual-layout adapter, centralized canonical.** M33's kernel evidence API
  is the seam: it serves the centralized layout natively and reads a v1
  per-area layout through an adapter (per-area ids presented as
  `<area>/SRC-nnn`, per-area registries as slices). New engagements get the
  centralized layout from scaffold-time.
- **The procure-to-pay fixture stays v1-layout forever** — it is the M36
  compatibility gate's regression target and proves the adapter.
- **An optional one-time `sources centralize <engagement>` verb** folds a
  v1 engagement's per-area trees into one ledger (dedupe by hash, remint
  ids, merge touches/consumed maps, write a remap table for register
  provenance strings). Optional because the adapter makes it a convenience,
  not a prerequisite.

## Acceptance sketch (firm up at build time)

- Register → tag → consume-per-area → auto-move round-trip: a two-area
  source moves to `processed/` only after BOTH areas' touches are covered;
  a one-area source behaves byte-identically to v1's lifecycle.
- Idempotent re-drop by hash; id collision impossible by construction (one
  minter); park with reason; loud-until-empty on unregistered files.
- The consumption evidence rules replay against the centralized ledger:
  `--filled` credits unconditionally, `--updated` requires a `kind: source`
  note naming the id, non-source notes credit nothing.
- Adapter: the p2p fixture reads through the kernel evidence API with zero
  fixture edits; `touches`-validation defects report identically in both
  layouts.
- `centralize` verb: golden test folding a synthetic two-area v1 engagement
  — hash-dedupe collapses the double-routed file to one entry with a merged
  touches map and both areas' consumed history intact.
- Drafter brief source listing is byte-equivalent (same sources, same
  order) whether served from v1 folders or the central ledger.

## Complexity accounting (the standing test)

New state files: **net negative** — N area registries + sidecars collapse
into one ledger. New gates: zero (loud-until-empty and the taxonomy guard
re-point at ledger queries). New agent judgment: zero — intake's classifier
judgment is unchanged; drafters see the same brief. The bill is the
adapter (retired after v1 support sunsets) and the move-rule
generalization. The review risk to police: **truth leaking back into file
position** — any code path that answers an outstanding-ness question by
listing folders instead of querying the ledger rebuilds the split brain
this ticket removes.

## Deferred (recorded, not built)

- **Cross-engagement source reuse** (same client, next engagement) — the
  hash + ledger design doesn't preclude it; no consumer demands it yet.
- **Source-level access classes** (privileged interviews restricted to
  certain areas) — tags could carry it; wait for a real engagement to ask.
- **Retiring the dual-layout adapter** — after M36 passes and at least one
  real engagement runs centralized end-to-end.
