# M26 — The engagement seam model (taxonomy-declared, token-carried, audit-derived)

> **Status: DESIGNED — decisions settled with the user.** Not yet built.
> Supersedes the two earlier shapes this idea passed through: a
> human-curated `interfaces.yaml` (rejected: the user must not own
> engagement plumbing) and an agent-maintained one (superseded: a curated
> file is state; the settled design derives the same model from prose, the
> safest artifact class the system has). Companions: M24 (whose matching
> heuristics this demotes to backstops), M25 (intake — approved,
> independent), M11 (whose `upstream` mechanism this extends across areas),
> M20 (rename propagation — extends to the new token form).

## The diagnosis this answers

Every engagement-cohesion feature to date has STATISTICALLY INFERRED the
engagement's structure from prose — shingles to guess shared material,
title-grepping to guess mentions, digest-matching to guess gap answers —
because nothing could DECLARE that structure. Within an area the system
never guesses: `[[slug]]` is checkable identity, dangling refs are hard
errors, renames propagate. The engagement level had no equivalent. Root
cause, in the user's words: "we are still fighting to get the engagement
to be cohesive as a whole." The fight is inference; the fix is
declaration.

## The model in one paragraph

**Taxonomy declares** (cross-area seams in the manifest, reviewed at the
existing confirm gate) → **drafters align** (bounded read-only seam
context; `[[area/slug]]` tokens in handoff sentences) → **reconcile
verifies** (a dangling cross-area token is a mechanical ERROR) → **the
audit derives** (the interface catalog / "spine" is READ OFF the tokens,
fresh each run — owned by nobody, maintained by nobody, never stale) →
**M12 / the placement pass** shrink to catching what slipped past
declaration. Judgment enters once, at a gate the human already stands at;
four mechanical consumers carry it forever. The human is in the loop
exactly once (confirm), which is the standing requirement.

## Build items (the order matters — each makes the next smaller)

### 1. Cross-area reference tokens — `[[area/slug]]` (the foundation)

- **Grammar:** `[[<area>/<slug>]]` (and `[[#area/slug]]` if the number-only
  form proves needed; defer). Area = the sibling folder name under
  `components/`.
- **Resolution (render):** resolves to the target's heading + area title —
  e.g. "the Goods Receipt procedure (Procure to Pay)". NEVER a display
  number: numbers are area-local render artifacts and another document's
  numbering is not stable from here.
- **Validation (reconcile):** the token must name an existing sibling
  area's manifest procedure — validated against the sibling MANIFEST, not
  its draft (identity exists from scoping; see "drafting order" below). A
  dangling cross-area token is a hard ERROR, exactly like a local one.
  Outside a `components/` engagement root, any cross-area token is an
  ERROR with a layout explanation (same gating as every cross-L1 feature).
- **Rename propagation (M20 extension):** a renamed/retired procedure
  propagates to cross-area token holders through the same rename-notes
  flow; the audit's derived spine names every holder, so the blast radius
  is enumerable, not discovered.
- Check 17 (title-grep mention heuristic) and the audit's MENTIONS shape
  remain as backstops for UNDECLARED references, with upgraded fix text:
  "use a `[[area/slug]]` token" once the target is scoped.

### 2. Taxonomy as the declarer (the glue, at declaration time only)

- The taxonomy dispatch feeds every sibling manifest as the starting map
  (it already Globs them, v1.6.0); it reads deeper — a sibling fragment or
  two — only where its sources describe a handoff whose counterpart it
  must identify. Bounded investigation, never browsing.
- Its proposal gains, per procedure, cross-area **`upstream`** entries in
  the existing M11 field, new notation: `upstream: ["bank-rec",
  "p2p/goods-receipt"]` — local slugs and `area/slug` refs side by side.
  Optionally a `downstream` mirror if build experience wants it; defer.
- Posture change in the contract: from defensive (don't scope what others
  own) to constructive (declare how my procedures CONNECT to theirs).
- The human reviews seam declarations at the **existing confirm gate** —
  structure is destiny; the connective tissue is part of the structure.
  No new gate.
- **Anchoring guard (absolute):** taxonomy prescribes WHAT TO READ, never
  what to write. Upstream context is seam alignment only; drafters draft
  from their own sources. This is the line that kept the planner out and
  it is not negotiable here either.

### 3. Cross-area upstream in the drafter brief

- `brief.py` resolves `area/slug` upstream entries across the tree and
  lists the counterpart fragment READ-ONLY, same rules as within-area
  upstream (M11): align the seam — artifact names, timing, state — and
  write the handoff with the `[[area/slug]]` token.
- Drafter contract: one added block. Handoff sentences at declared seams
  use the token; the no-documenting-others'-work rule is unchanged (the
  token names, the sentence hands off, nothing else crosses).

### 4. The derived spine (M26's namesake, now nearly free)

- `engagement.py audit` gains an INTERFACES section: every cross-area
  token in the prose, listed as from → to with its holding fragment —
  the interface catalog as a derived view. Plus two mechanical findings:
  - **asymmetric seam** — declared/tokened from one side only (expected
    during mixed scoping order; the fix is an incremental taxonomy pass
    on the older area);
  - **prose mention where a token could stand** — the upgraded check-17
    finding.
- The placement pass's brief carries the spine; its matching work shrinks
  to what the spine doesn't already answer.

## Drafting order — a seam whose upstream is not yet drafted

Scoping order constrains TOKENS; drafting order constrains NOTHING.
Cross-area waves are explicitly rejected — they would serialize entire
L1s. Three cases:

1. **Upstream scoped and drafted:** brief lists the fragment; drafter
   aligns; token resolves. The happy path.
2. **Upstream scoped, not drafted:** the downstream drafter PROCEEDS. The
   token is valid (identity is manifest-based, like local tokens pointing
   at unfilled skeletons). The brief says so honestly — "scoped, not yet
   drafted — seam context UNAVAILABLE; draft the handoff from your own
   sources" — and the drafter returns `seam_unverified` so the blindness
   is on the record. When the upstream later drafts, the audit (both
   sides now exist) and M12's `seam` category verify the seam
   mechanically; worst case is one targeted-edit note. A blind seam can
   never SILENTLY stay blind.
3. **Upstream not scoped:** no manifest entry → no token (it would be a
   hard error, correctly). The handoff stays plain prose. When the area is
   scoped later, the audit's mention check flags the upgrade and the NEW
   area's taxonomy pass declares the seam from its side (an agent never
   writes another area's manifest — one writer per file survives M26).

**Deferred (build only if M12's seam findings prove insufficient):** a
seam-staleness signal — record the upstream fragment's hash when a
downstream drafter reads it (the scope_delta pattern applied to seams), so
a later upstream REWRITE mechanically flags downstream seams aligned
against an older version.

## What this demotes

- M24's digest/candidate matching machinery: backstop for the undeclared,
  no longer the mechanism. The `--full` placement read (one strong agent,
  whole fragments, mechanical size guard) remains the MIGRATION instrument
  for legacy prose and the periodic deep sweep.
- The earlier "taxonomy boundary block" idea: absorbed — the upstream
  declarations ARE the boundary block, landing in the manifest instead of
  prose.
- The curated-spine designs: superseded entirely (see status note).

## Migration (the mixed-version engagement this was diagnosed on)

One-time per legacy area, using machinery that exists: audit → `--full`
placement pass → M12 pass → notes flow through drafters. As handoff
sentences are touched they adopt tokens, so the spine GROWS OUT OF the
cleanup already being done. An incremental taxonomy pass per legacy area
back-fills the manifest `upstream` declarations once its neighbors exist.

## Acceptance

- A `[[p2p/goods-receipt]]` token renders as heading + area title and
  round-trips reconcile clean; the same token with a typo'd slug or area
  is a reconcile ERROR naming the sibling's known slugs; the same token in
  an area outside a components/ root is an ERROR explaining the layout.
- A token pointing at a scoped-but-unfilled sibling procedure is VALID.
- Taxonomy proposal on a fixture with a described handoff declares
  `area/slug` upstream; the confirm gate surfaces it; scaffold writes it
  to the manifest.
- The drafter brief resolves a cross-area upstream to the sibling
  fragment read-only, and to the honest "scoped, not yet drafted" line
  when the fragment is a skeleton.
- The audit INTERFACES section lists tokens as from→to pairs; an
  asymmetric seam and a prose-mention-upgrade candidate are each flagged.
- Rename of a tokened procedure reaches cross-area holders via the rename
  flow.
- The seam-staleness signal is NOT built (deferred), and cross-area waves
  do NOT exist: a downstream drafter is never deferred on an undrafted
  cross-area upstream.

## Out of scope

- Cross-area display numbers in tokens (another document's numbering is
  not stable from here).
- Agents writing sibling manifests (asymmetry is flagged, then fixed by
  the OWNING area's incremental taxonomy pass).
- Cross-area waves / build-order constraints between L1s.
- The seam-staleness hash signal (deferred pending evidence).
