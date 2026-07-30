# M25 — Engagement intake (one drop point, agent-routed, loud when parked)

> **Status: DESIGNED — decisions settled with the user; APPROVED, build
> sequenced AFTER M26** (tokens/taxonomy/spine first — M25 is independent
> of it but M26 is the priority). Companions: M24 (the placement pass this
> REDUCES traffic for — misfiled evidence is a chunk of what `adopt`
> would otherwise repatriate after the fact) and M0/taxonomy (the
> within-area allocation this feeds; under M26 the taxonomy pass also
> emits the gap forecast, so well-routed intake directly improves the
> earliest client ask-list).

## Goal

Fieldwork does not arrive organized by L1 — one walkthrough covers the
receiving dock AND inventory valuation; the AP manager interview covers
payment runs AND the bank-reconciliation handoff (the user's real-project
seam analysis is one long demonstration). Today the routing decision is
made IMPLICITLY, by which `components/<area>/_sources/new/` folder a file
is dropped into, BEFORE the system has seen the content. A transcript
filed only under one area leaves its other area drafting from an
impoverished pool: gaps open for things the client already said, and the
M24 placement pass later patches with `adopt` what better intake would
have prevented.

This ticket gives the engagement ONE drop point (`intake/` at the
engagement root), an agent that routes each document to its area(s), and a
mechanical guarantee that nothing can be silently lost on the way.

## Decisions that settled the shape (user + design history)

1. **Routing is agent judgment; the human is a reviewer, not a router.**
   The user's words: "I don't want to route it manually." The earlier
   human-routed draft protected against silent loss; the settled design
   fixes the SILENCE mechanically (rules below) and hands the judgment to
   an agent — same reviewer-not-gatekeeper stance as M24.
2. **Intake may DESCRIBE a source's relevance, never REDUCE its content.**
   No excerpting: whoever cuts a transcript decides relevance before
   drafting (the planner/anchoring problem in sharper form), and an
   over-aggressive cut is the one failure NOTHING downstream can ever
   detect — no dangling ref, no reconcile warning, no audit signal.
   Silent loss of client material is the failure class the retirement
   machinery exists to prevent; intake must not reintroduce it upstream.
   Splitting at NATURAL DOCUMENT BOUNDARIES (a file that is really three
   separate meetings) is legitimate segmentation, not reduction — a human
   call, out of the classifier's hands.
3. **Area-local source architecture is untouched.** `SRC-` ids, `touches`,
   hashes, retirement accounting stay per-area. Intake is a STAGING layer
   in front of the per-area stores: routing COPIES the document into each
   target area's `_sources/new/` (frozen, hash-stamped — the `adopt`
   mechanics pointed at raw material). A doc spanning two areas becomes
   two copies, each entering its area's ordinary confirm/touches/
   retirement flow unchanged.
4. **Sources are client material: the copies and the archive live inside
   the engagement folder only,** committed by the ordinary checkpoints to
   the engagement's private repo. Nothing new leaves the folder.

## Design

### 1. The staging folder

`intake/` at the engagement root (sibling of `components/`). Everything
from fieldwork lands there; zero decisions at drop time. Processed files
move to `intake/routed/` (with a one-line manifest of where each went);
unplaceable files move to `intake/parked/` with a stated reason. The
folder's state is therefore self-describing: anything still at top level
is unprocessed, anything in `parked/` awaits a human, nothing is ever
deleted.

### 2. `engagement.py route` — the deterministic verb, the ONLY writer

```
engagement.py route intake/<file> --to <area>[,<area>...] \
    [--note-for <area> "relevance pointer"] 
engagement.py park  intake/<file> --reason "..."
```

`route`: for each target area, copy the file to
`<area>/_sources/new/intake-<basename>` **and write NOTHING else — no
sources.yaml entry, no hash stamp.** (Sanity-check finding, M6 contract:
a hash at the file's current content means "already assessed" at guard 5.
Pre-stamping would silently SKIP source assessment, so `touches` would
never be proposed and the source would strand unconsumed. `adopt` stamps
deliberately — flow-through for derived prose — but raw client material
must enter the ordinary assess/confirm flow exactly like a hand-dropped
file.) Idempotency is at the file layer: an identical copy already
present in the target's `_sources/new/` (or its ledger, by content) is a
no-op. The per-area relevance pointer is a SIDECAR note file beside the
copy (`intake-<basename>.route.md`), which scaffold's assess step folds
into the eventual sources.yaml `note:` — the pointer must reach the
drafter's brief. Then move the original to `intake/routed/`. `park`: move
to `intake/parked/` with the reason recorded. Both usable by hand — the
human override is one line.

**Greenfield ordering:** sources normally arrive BEFORE an area is
scoped, so the classifier (which routes against scoped areas' manifests)
will park the first documents of any brand-new L1 — correct behavior,
loud, with the reason naming the unscoped content. `route` itself accepts
an explicit not-yet-scoped area name on HUMAN direction (creating
`components/<area>/_sources/new/`), which is exactly today's hand-drop,
formalized.

### 3. The intake classifier — taxonomy's little sibling

One light agent per batch, dispatched when the user says "process intake"
(or when the orchestrate skill notices unprocessed files at the start of
an engagement-root invocation — surfaced like the git-health note, never
a gate). It reads each staged document plus every area's manifest (titles
+ procedure lists — its target vocabulary), then RUNS the `route`/`park`
commands itself (agent judgment, deterministic writer — the consolidator/
note pattern). It writes the relevance pointers, being best placed to:
it just read the document.

**Contract rules (the anti-silent-loss core):**

- **Zero-routes is forbidden.** Every staged file ends the pass in
  `routed/` or `parked/` — parked ALWAYS carries a reason ("mentions
  treasury operations; no scoped area covers this"). A file it cannot
  classify is parked, never skipped.
- **Bias to over-route (recall over precision).** Torn between one area
  and two → route to two. Costs are asymmetric: an extra copy costs a
  bounded drafter read that `touches` may never trigger; a missed copy
  costs invisible gaps in the un-routed area.
- **No content judgment beyond routing.** It never summarizes into the
  copy, never excerpts, never merges documents, never proposes new areas
  (a doc for an unscoped area is parked — scoping is the human's and the
  taxonomy stage's business).
- Compact status: routed (file → areas, one line each), parked (+ reason),
  pointers written. Never paste document text.

### 4. Loudness — parked/unprocessed material cannot be silent

- The classifier's status headlines parked count.
- `engagement.py audit` gains an INTAKE line: unprocessed and parked
  counts, with reasons — every audit, until empty (the no-silent-caps
  standard applied to evidence).
- The orchestrate skill relays unprocessed/parked intake once per session
  when invoked from an engagement root (informational, like `details.git`;
  never a gate).

### 5. Self-healing for imperfect routing (existing machinery, no build)

- Over-routed copy → never consumed → the retirement ledger already flags
  never-consumed sources; the human removes or ignores.
- Under-routed (missed area) → surfaces as gaps in that area → the M24
  placement pass matches them and `adopt` repatriates — the detection
  layer remains the backstop it already is.
- Misrouted pointer (too narrow) → harmless: the full document is there;
  the drafter reads past the pointer.

## Cost

One classifier read per document per batch — cheaper than a drafter pass,
and it replaces reads NOBODY was doing (unlike the rejected planner, which
duplicated reads every drafter must make anyway). Downstream it SAVES
spend: fewer misfiled-evidence gaps, less placement-pass/adopt traffic.

## Acceptance

- `route` copies to each named area's `_sources/new/`, hash-stamped,
  moves the original to `routed/`, and is a per-area no-op at the same
  content hash. `park` records the reason. Both work by hand.
- A routed doc's relevance pointer reaches the drafter's brief for the
  procedures that touch it.
- Content is byte-identical between intake original and every area copy
  (the no-reduction rule, mechanically checked).
- `audit` reports unprocessed + parked counts with reasons; empty intake
  reports nothing.
- Classifier live-test (run-4 style): a spanning document routes to both
  areas with pointers; an off-scope document parks with a reason; zero
  files remain at intake top level after a pass.
- Nothing in `components/<area>/_sources/` flows differently than a
  hand-dropped source: taxonomy touches-tagging, scaffold confirm,
  retirement accounting all unchanged.

## Out of scope

- Excerpting/summarizing intake content (settled decision 2 — permanent).
- The classifier proposing new L1 areas (parking + human is the path).
- Automatic batch scheduling (runs on the user's word or the skill's
  session-start notice, like the audit).
- Intake for non-document evidence (screenshots ride the existing
  `_assets/` flow).
