# M24 — Knowledge placement (the engagement pass: duplication + gaps, one problem)

> **Status: DESIGNED — decisions settled with the user.** Ready to build.
> Supersedes this ticket's earlier draft ("gap pollination"), which treated
> gap resolution as a sibling of the duplication audit. The user's
> observation collapsed the two: they are the SAME problem, so they are one
> register, one pass, one report. M12's `gap-answer` category (see M12
> "Amendments", A2) is the within-area instance of the same principle.

## Goal — one fact, one home

The system's standing rule (ownership maps, "say it once") is that **every
fact has exactly one home.** The engagement's two chronic diseases are the
two directions of violating it:

- **Duplication** — a fact with TWO homes (over-sharing): the same activity
  scoped twice, the same explanation drafted twice.
- **A cross-answerable gap** — a fact with a home but a BROKEN POINTER
  (under-sharing): inventory carries `GAP — how the goods receipt posts is
  unconfirmed` while procure-to-pay documents exactly that, fully sourced.
  The gap goes out in a review kit and spends a process owner's scarcest
  resource on a question the engagement already answered.

The proof they are one problem is that the resolution verbs are the same
set: **reduce to a handoff reference** (duplication: trim the non-home copy
to a pointer; gap: the question was about work owned elsewhere), **adopt
the source** (gap: import the evidence; occasionally duplication's cousin),
and **pick the owner** — the only genuinely human verb in either direction.
The two lenses also feed each other: a shared-prose match sitting next to
an open GAP is often the same fact caught mid-migration between homes.

This ticket makes the engagement-wide sweep report BOTH directions from one
read, and resolve both through machinery that already exists.

## Constraints that settled the shape (user decisions)

**Simplicity is a requirement, not a preference.** "The more compute we
throw at this the harder it will be to keep track of." So: no new agent
type, no new note kind, no new state file, no new gate, no scheduled pass,
no per-area fan-out. New surface: two `engagement.py` subcommands (`brief`,
`adopt`), one section added to `audit`, one shared gap parser, one
single-agent pass.

**The human is a reviewer, not a gatekeeper.** The user identified
themselves as the bottleneck. Everything below defaults to FLOW THROUGH:
notes route to drafters on the ordinary loop (delete-at-triage is a right,
never a duty) and `adopt` runs unattended when a note names it. The review
moment is the checkpoint diff and the rendered draft — where the human
already was. Git is the safety net: reverting a bad auto-decision is
cheaper than pre-approving every good one. An engagement that wants the
gate back gets it with the EXISTING sticky-hold mechanism
(`hold: [adopt]` in `_client/consult.yaml`, M17) — config, not machinery.

**Prose becomes a source by REGISTERING it, never by citing it invisibly.**
Cross-area, a `SRC-` id does not resolve in the other area's
`sources.yaml`, so "just cite theirs" breaks the dangling-citation checks.
The settled mechanism makes prose-as-source literal: `adopt` copies the
answering fragment into the gap area's `_sources/` and gives it an
ordinary `SRC-` entry (hash-stamped, marked second-hand). Every invariant
survives for free — citation resolution, provenance maps, retirement
accounting — because it IS a source. The copy is a feature: it freezes
what was relied on, so the sibling's later edits cannot silently
invalidate the citation. The forbidden move stays forbidden: closing a gap
from sibling prose with NO ledger entry manufactures exactly the dangling
statements reconcile exists to flag.

## Design

### 1. The register — `engagement.py audit` grows a fourth section (free)

The audit already walks every area for its three duplication shapes (twin
L3s, cross-area mentions, shared prose). It gains:

```
4. OPEN GAPS — the engagement's unanswered questions, by area:
  inventory/month-end-inventory-reconciliation
    GAP-01 — how the goods receipt posts to the sub-ledger is unconfirmed
  ...
  47 open gap(s) across 6 area(s)
```

Extraction is mechanical and shared: a parser in `callouts.py` (the
callout-grammar home) yields each fragment's open gaps — `VALIDATION
REQUIRED` callout lines AND `[[GAP-NN — …]]` body tags — so this register,
M12's cross-brief gap register, and any future consumer read gaps one way.
Layer-1 value is standalone: the consultant who sat the walkthroughs is
the best matching engine on the engagement, and today the open questions
are scattered across N documents where nobody sees them side by side.

### 2. The placement pass — one agent, human-invoked

`engagement.py brief` prints the work order: the audit's mechanical
findings, the gap register, each area's procedure titles + scope digests
(the bounded-digest discipline from M12), the finding rules, and the two
command templates below. One judgment agent reads it and raises BOTH
directions as ordinary notes through the existing commands — no new agent
`.md`; the orchestrate skill's dispatch prompt carries the one-paragraph
contract:

| Direction | Finding | Queued as |
|---|---|---|
| over-sharing | this fact/procedure is doubled; owner is X | `engagement.py note <area> --slug <loser> --note "reduce to handoff; owner …"` (kind: review — unchanged) |
| under-sharing | this GAP is answered in `<area>/[[slug]]` | same `note` command; the note text names the answering slug and, where adoption is warranted, the exact `adopt` command |

Report-don't-guess holds: a match the agent cannot place confidently rides
back in its return status, never the bus. Ownership calls stay human (the
audit's existing gate).

### 3. `engagement.py adopt <area> --from <other-area>/<slug>` — the verb

Deterministic, idempotent, and it feeds the EXISTING source pipeline
rather than inventing one:

1. copies `components/<other-area>/<fragment>` to
   `<area>/_sources/new/adopted-<other-area>-<slug>.md`;
2. appends a `sources.yaml` entry via `sources.py`'s loaders/dumpers —
   next `SRC-` id, `hash` stamped now (sha256, same as scaffold),
   `state: new`, `touches: [--touches slugs]`, `note:` marking it
   second-hand ("internal: drafted <other-area> procedure");
3. queues a `kind: source` note (with the new `src:` id) on each touched
   procedure — so the advisor's ordinary `apply_review` loop dispatches
   the drafter with standard evidence discipline, no confirm gate.

Re-adopting the same fragment at the same content hash is a no-op (entry
and notes both dedupe). Holds: before writing anything, `adopt` resolves
`client_config.holds(area, ...)`; if `adopt` is held, it prints the hold
(area or engagement layer) and exits nonzero without touching the folder —
M17 semantics, enforced at the verb since the advisor never schedules it.

### Resolution flow (nothing new after a note lands)

pass → notes queued (+ adoptions executed) → each area's ordinary
`apply_review` → drafter reduces to a handoff OR closes the GAP citing the
adopted `SRC-` id → aggregate / reconcile → checkpoint → the human reads a
diff.

## Where the human stays (the load-bearing bottlenecks)

1. Factual conflicts between areas — no component may pick a side.
2. Ownership calls — client-org questions, not text questions.
3. Review kits — the engagement's bottleneck, not the system's.

All three are batched and asynchronous; none is a synchronous approval.

## Settled decisions

1. **Duplication and gaps are one pass** (user insight): one register, one
   agent read, one report — two symmetric finding directions.
2. **Prose-as-source via registration only**; transitive citation covers
   the within-area case (M12/A2), adoption covers cross-area.
3. **Flow-through defaults; sticky hold `adopt` is the brake.**
4. **One agent per pass, engagement-scoped.** Value scales with migrated
   L1s; cost does not.

## Acceptance

- `audit` on a two-area fixture prints section 4 with every open gap
  (callout AND body-tag forms), grouped by area, and still writes nothing.
- `brief` prints mechanical findings + gap register + scope digests +
  both command templates, read-only.
- `adopt` creates copy + `SRC-` entry + `kind: source` notes exactly once
  across two invocations (idempotent at the content hash); the entry's id
  is fresh, its hash matches the copy, and a drafter citing it survives
  reconcile with no dangling-citation error.
- With `hold: [adopt]` in `_client/consult.yaml` (either layer), `adopt`
  refuses, names the layer, and the folder is untouched.
- A gap with no cross-area answer produces no note (report-don't-guess —
  agent-side, exercised in the live pass rather than unit-tested).
- Rerunning `adopt` and re-queueing identical notes adds zero new items.

## Out of scope

- Within-area gap resolution — M12/A2 (`gap-answer`; the area's source
  pool is shared, so transitive citation suffices there).
- Auto-adoption without a queued note naming it (the note is the audit
  trail).
- Scheduled/recurring invocation — run like the audit: occasionally, from
  the engagement root, on a human's word.
- Tuning the audit's heuristics (thresholds await real client-run data).
