# M26 — The engagement seam model (taxonomy-declared, token-carried, audit-derived)

> **Status: DESIGNED — decisions settled with the user.** Not yet built.
> **BUILD PRIORITY: first** — ahead of M25 (intake) and the M24 `--full`
> read, in this order: tokens → taxonomy (with the Opus pin and the gap
> forecast) → briefs → derived spine. Then M25, then the legacy-migration
> playbook on the user's real engagement.
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
- **Integration facts (sanity-check pass, verified against the code):**
  - The token grammar lives in ONE place — `doc_model`'s `XREF_RE` (M23's
    centralization) — and every consumer (resolve_tokens, reconcile's
    dangling check, kits anchors) inherits from it. The current regex has
    no `/`, so an unextended `[[area/slug]]` would MATCH NOTHING and pass
    through to the .docx as literal text — extending `XREF_RE` is the
    load-bearing edit, and "a raw token survives to render" is the
    failure the acceptance tests must rule out.
  - `scaffold.py` currently DROPS unknown upstream hints with a WARNING
    (its slug-validation loop) — an `area/slug` entry would be silently
    discarded at the confirm promote. Scaffold must learn the form:
    validate the area/slug against the sibling manifest, keep it.
  - `orchestrate`'s wave logic defers a slug only when an upstream hint is
    in the area's own `pending` set — a cross-area entry is naturally
    NON-BLOCKING (never in pending). This is the desired behavior
    (cross-area waves rejected) but it is currently accidental: pin it
    with a test so a future wave refactor cannot start deferring on
    cross-area hints.
  - **Rename propagation, corrected:** the per-area rename-notes flow
    (M20) cannot write other areas' notes and MUST NOT (one writer per
    file). The actual mechanism: a rename makes every holder area's
    cross-area token DANGLE, which is a hard reconcile ERROR in the
    holder on its next pass — loud by construction; the audit's derived
    spine enumerates the holders BEFORE the rename so the blast radius is
    known, and the fix is an `engagement.py note` per holder (human/
    orchestrator-run, the existing cross-area fix path).

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
- **The gap forecast.** The proposal gains, per proposed procedure, the
  questions its sources visibly do NOT answer ("no approver named for the
  payment run", "retention location never stated"). Same read, new
  output: gap discovery moves BEFORE prose, so the client ask-list goes
  out while fieldwork access is hot — drafting proceeds in parallel and
  is never hostage to answers (settled: the two-phase scout-then-write
  model was REJECTED — scouts double the read spend, "all inputs
  gathered" never arrives, and blind seams are already handled by this
  ticket's drafting-order rules; the forecast captures the same early
  discovery at ~zero marginal cost on the scoping read).
- **Model pin: `model: opus` lands in `agents/consult-taxonomy.md`
  frontmatter IN THE SAME COMMIT as this contract.** Settled reasoning:
  M26 makes taxonomy the engagement's single point of judgment, with four
  mechanical consumers that ENFORCE its output rather than second-guess
  it — concentrated judgment gets funded deliberately. Once per area, so
  the premium is bounded; and a pin (unlike a "use a strong session"
  habit) transfers to teammates, making the quality floor structural. No
  other agent is pinned; agents otherwise inherit the session model.

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
- The taxonomy proposal carries a gap forecast naming a fact the fixture
  sources visibly omit; `consult-taxonomy.md` carries `model: opus`.
- The drafter brief resolves a cross-area upstream to the sibling
  fragment read-only, and to the honest "scoped, not yet drafted" line
  when the fragment is a skeleton.
- The audit INTERFACES section lists tokens as from→to pairs; an
  asymmetric seam and a prose-mention-upgrade candidate are each flagged.
- Rename of a tokened procedure makes the holder's token a hard reconcile
  ERROR (not silence, not prose passthrough); the audit's spine names the
  holder before and after.
- A raw `[[area/slug]]` token NEVER survives to rendered output (the
  XREF_RE extension reaches every consumer).
- Scaffold PRESERVES an `area/slug` upstream entry (today's code would
  drop it with a warning — regression-tested).
- The advisor never defers a drafter on a cross-area upstream hint
  (pinning today's accidental non-blocking behavior).
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
