# M6 — Taxonomy + registry reassessment on new sources

> **Status: DESIGNED — promoted from stub.** Deferred on the grounds that M1–M5
> had to be solid first; they now are, and the deferral has a measured cost.
> Evidence: `docs/audit-decide-exhaustiveness.md` (F7, plus F8's retirement half).

## The problem it solves

M0 does the **initial** stand-up (procedure set + `_reference/` registry) from the
first sources. M6 is the **incremental** counterpart: when new sources arrive
later, reassess both — add/split/merge/reorder procedures **and** propose registry
additions (a newly-mentioned system, a new role, a new alias). Genuine judgment
(an agent), distinct from M5, which only reacts to content changes inside an
already-decided set.

`docs/README.md:60` already promises the behaviour: a new file in `_sources/new/`
"triggers reassessment (M6) and **re-dispatch of the drafters it touches**." The
second half is what does not exist.

## Why it is no longer deferrable

Measured on the built area — drop one follow-up source informing procedures that
are already drafted:

```
drop new source → taxonomy (incremental) → confirm → scaffold creates nothing
               → taxonomy (incremental) → taxonomy (incremental) → ...
mark-processed --filled <slug> → moved 0 source(s)
```

Guard 4 dispatches on the `unfilled` sentinel, which only new skeletons carry. An
already-drafted procedure a new source `touches` has no sentinel and no note, so
no drafter is dispatched. The source then cannot retire — `mark_processed` moves a
source only when its whole `touches` set is a subset of the successfully-filled
slugs, and nothing was filled — so guard 5 re-fires forever, re-spending a
taxonomy dispatch per lap.

This is the most common workflow after the first draft: a follow-up call that
enriches procedures you already have. Today it does not converge.

## Design

### Re-dispatch rides the notes queue

No new guard. Incremental taxonomy, at confirm time, writes a
`_review/{slug}.notes.yaml` entry for each **already-drafted** procedure the new
source touches — "SRC-07 informs you; here is what is new." Guard 2 then
dispatches `consult-drafter` in `mode: update` for exactly those slugs — the mode
that already "works newly-known facts into the body and REMOVES the gaps they
close."

"Just the procedures it maps to" falls out of the `touches` list rather than
needing new machinery.

### Two consequences that must ship with it

1. **The drafter has to read the new source.** `apply_review`'s dispatch carries
   `{area, slug, mode: update, review_notes: path}` and *deliberately no* `sources`
   list. A source-originated note must therefore carry the **`SRC-` id**, which the
   drafter resolves through `sources.yaml`. Preferred over widening the dispatch
   shape: one shape, and the registry already maps ids to paths.
2. **`mark-processed` must count updates.** `--filled` currently means "slugs that
   succeeded in a fill batch." It must also accept slugs that succeeded in an
   *update* batch, or the source never retires and the loop survives the fix.

### Procedure-set diff (unchanged from the original sketch)

Diff proposed slugs against existing manifest procedures: **new** → fragment +
manifest entry; **missing** → flag for the human, never auto-delete a
human-authored procedure; **split/merge** → propose, human confirms. The
identity/number split (stable slug, derived number) is what keeps this from
causing renumbering churn.

### Retirement is part of this ticket (F8)

The "missing → flag for human" line is where retirement lives, and the audit shows
the flag is not enough. Removing a procedure leaves `[[slug]]` references in
**sibling procedures** (drafter-owned) and in `82_dependencies` / `84_raci`
(agent-owned). The Python-derived views regenerate clean; those two classes do not.

So a retirement proposal must enumerate the inbound references and write notes for
the citing procedures, exactly as for a new source — otherwise the human is left
hand-editing fragments while `reconcile` blocks. M18 fixes the *ordering* deadlock
this exposed; the workflow belongs here.

### Registry reassessment

Reuses M3's "unmatched mention" warnings as the candidate list: each flagged
system or role is a registry addition for the human to confirm at the existing
`registry_topup` gate. This catches *new* nouns only — a **renamed** noun is M20,
because an alias match suppresses the warning by design.

## Acceptance

- A new source touching only drafted procedures produces notes for exactly those
  slugs, update drafters run, and the source moves to `processed/`.
- The same source run twice does not re-notify a procedure already updated for it
  (dedupe on `SRC-` id).
- A source touching a mix of new and existing procedures fills the new ones and
  updates the existing ones in the same pass.
- A source whose touched set partially fails keeps the source in `new/`.
- A retirement proposal enumerates inbound `[[slug]]` references and writes notes
  for each citing procedure; `reconcile` passes once those drafters run.
- The advisor never returns `taxonomy` twice for an unchanged `_sources/new/`.

## Out of scope

- Cross-area reassessment (the registry and `_client/` parent config are the
  cross-area layer — M13).
- Auto-deleting a human-authored procedure.
- Re-wording prose after a canonical rename — M20.
