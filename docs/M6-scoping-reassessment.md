# M6 — Taxonomy + registry reassessment on new sources

> **Status: BUILT** (`scripts/notes_util.py`, `scripts/sources.py`,
> `scripts/scaffold.py`, `scripts/orchestrate.py`, `scripts/review_extract.py`,
> `agents/consult-taxonomy.md`, `skills/consult-taxonomy/SKILL.md`; tests in
> `tests/test_notes_bus.py` (21) and `tests/test_m6_reassessment.py` (27) — the
> suite goes 413 → 461).
> Deltas from this design:
>
> - **The promote step DERIVES the source-note set from `touches`; the proposal
>   supplies only the wording.** The ticket has the taxonomy agent authoring notes
>   and confirm writing them, but a note list that stood on its own would break
>   the veto this ticket specifies: "the sanctioned veto is upstream, at the
>   confirm gate, by editing the proposal's `touches`" only works if `touches` is
>   what decides. So `scaffold.py` walks the promoted `sources.yaml`, and for each
>   outstanding source writes one `kind: source` note per `touches` slug that is
>   already drafted, using the wording keyed `(slug, src)` in
>   `.proposed/notes.yaml` (or a generated line if the agent supplied none).
>   Wording for a pair `touches` does not claim is reported and dropped. Editing
>   `touches` at the gate therefore really does cancel the dispatch, and a pass
>   converges even if the agent writes no `notes.yaml` at all.
> - **"Already drafted" is the `unfilled` sentinel, not the manifest.** A slug
>   already in the manifest but never drafted must take the `fill` path (which
>   hands the drafter its whole tagged source list); notes outrank fill, so
>   notifying it would send an update drafter at an empty skeleton. `scaffold.py`
>   borrows `orchestrate.UNFILLED_RE` rather than restating the grammar.
> - **The cross-batch record is `consumed:` on each source entry** —
>   `sources.py` accumulates it and never resets it, which is what makes the
>   mixed new/existing case work in either batch order and doubles as the dedupe
>   trace (see "Design decisions", below).
> - **`mark-processed` grew `--updated`, and reads archived notes as evidence.**
>   `--filled` keeps its meaning (first-draft fills, unconditional credit);
>   update credit requires a `kind: source` item naming the source, found in
>   `_review/processed/{slug}.notes.yaml` — the archive IS the success signal,
>   since the driver archives only after a batch succeeds. `--updated <slugs>` is
>   optional and additionally trusts the still-live note, for a driver that
>   credits before it archives.
> - **Guard 5's discriminator collapsed to one question.** The design has the
>   gate check "touches all drafted, no pending source notes"; by the time guard 5
>   is reached, guard 2 has already ruled out every pending note and guard 4 every
>   `unfilled` sentinel. So the only question left is whether `_sources/new/` holds
>   a file `sources.yaml` does not know at its current **hash** — unassessed →
>   `taxonomy`, otherwise every source there is stranded → `unresolvable` naming
>   the `SRC-` ids. Numbered **5a** in the ladder docstring.
> - **The gate also catches two states the ticket did not name:** a source with an
>   empty `touches` list, and one whose `touches` names a slug the manifest does
>   not carry (audit F14's livelock — `taxonomy` used to re-fire forever). Both
>   are stranded sources, and `human_action` already says "edit `touches`".
> - **"In the same pass" means the same build RUN, not one dispatch batch.** For a
>   mixed source the ladder returns `apply_review` and then `fill` on consecutive
>   laps, because notes outrank fill (guard 2 > guard 4) — by design, and
>   unchanged here. Both complete within one `continue <area>` run and the source
>   retires at the end of it.
> - **Unknown *fields* are loud, so one existing-test pin moved.**
>   `test_notes_util.py::test_dedupe_ignores_unknown_keys` asserted the old silent
>   drop; it is now `test_unknown_key_is_a_loud_error` (rule 2 verbatim). Four
>   other edits stamped `kind: review` into that module's fixtures (the shared
>   `ITEM` plus three inline items), and `test_review_extract.py` gained one line
>   asserting the stamp end to end.
> - **Two unowned producers needed their stamp**: `review_apply.py` fallback
>   notes and `gaps_ingest.py` workbook answers are reviewer-originated items on
>   the same bus, so each gained one line (`"kind": "review"`). Without it the
>   first load after an ingest would fail loud.
> - **Discovered while testing retirement:** removing a procedure also strands
>   every source whose `touches` names it (F14 → a blocking reconcile error).
>   The retirement guidance now tells the agent to re-emit those `touches` lists
>   without the retired slug.
> - **Not done here (out of ownership):** `skills/consult-orchestrate/SKILL.md`
>   has no `unresolvable` handler, does not call `mark-processed` after an
>   `apply_review` batch, and does not mention `--updated` — until it lands, a
>   driver following the skill will apply source notes and never retire the
>   source (it then rests at 5a's gate, which names the command).
>   `agents/consult-drafter.md` does not yet describe the `kind` field, so a drafter
>   reads a source note as ordinary prose instruction — correct behaviour, but
>   undocumented.
>
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

### Notes carry a `kind` (the bus contract)

This ticket turns `_review/{slug}.notes.yaml` from a single-producer queue into
a bus: after the outstanding set lands it has **five producers** — M8 review
extraction, this ticket's source notes and retirement notes, M12 consolidation
findings, M20 rename notes — and one consumer, guard 2. Undifferentiated items
break two things that each producer's ticket assumes:

- **Retirement accounting goes kind-blind.** If `mark-processed` counts every
  successful update slug, a *reviewer comment* on a procedure retires a source
  no drafter ever read — silent loss of client material, the worst failure
  class in a provenance system.
- **The veto stops being safe.** M12 and M20 advertise "delete any note you
  disagree with" as the human control point. Deleting a *source* note strands
  its source: it can never retire, and guard 5 re-fires forever.

The contract, three rules:

1. **Every item carries `kind:`** — `review | source | retirement | rename |
   consolidation` — stamped by its producer. Source-kind items also carry
   `src: SRC-<id>`. An item with no `kind` fails loud at load; there is no
   default.
2. **`notes_util` preserves these fields.** Today `_emit` silently strips any
   field outside its fixed key tuple on merge, which would delete `kind` and
   `src` the first time a second producer appends to the same file. The tuple
   is extended, and an unknown field becomes a loud error rather than a silent
   drop.
3. **Retirement counts only source-kind consumption.** `mark-processed` credits
   a slug toward a source's `touches` only when the consumed note was
   `kind: source` with a matching `src:`. Review, rename, and consolidation
   updates never move a source.

Veto semantics follow from the kinds: review, consolidation, and rename notes
may be deleted freely — that is their design. The sanctioned veto for a
*source* note is upstream, at the confirm gate, by editing the proposal's
`touches`. If a human deletes the note instead, the source sits unretirable in
`new/` — and the advisor must surface that state, naming the `SRC-` id (M18's
`unresolvable` shape), never re-loop taxonomy over it.

### Additional acceptance (bus contract)

- A reviewer-comment update on a procedure a source touches does **not** move
  that source to `processed/`.
- Deleting a source-kind note yields a gate naming the stranded `SRC-` id, not
  a `taxonomy` re-fire.
- Two producers appending to one slug's notes file lose no fields; `kind:` and
  `src:` survive the merge.
- A note item without `kind:` fails loud at load.

### Where the accounting lives (build decisions)

`sources.py` is the single owner: `sources.yaml` is the only place a consumption
fact is recorded, and the only place the retirement rule is evaluated.

**Cross-batch retirement — a durable per-slug record, not a batch set.** The
tempting shape (`--filled` grows to mean "filled or updated") cannot work: a
source touching `{new procedure A, existing procedure B}` is consumed in *two
different batches* — B by `apply_review`, A by `fill` — and guard 2 outranks
guard 4, so they are always at least one pass apart. A per-invocation set has no
memory of the other batch. So each source entry carries

```yaml
consumed: [bank-rec]      # written by sources.py, never reset, never authored
```

the union of everything credited so far, intersected with `touches`. Retirement is
`touches ⊆ consumed`, evaluated on every `mark-processed` call, so the two batches
can land in either order, any number of passes apart. Rejected alternative: a
separate `.consumed.json` signal file — it would be git-ignored (advisor state),
and losing it would silently re-dispatch every drafter, while `consumed` is
engagement state that belongs beside the `touches` it accounts against.

**Credit requires kind-matched evidence, except for fills.** A `fill` dispatch
carries the slug's whole tagged source list, so a successful fill *did* consume
every source touching it — `--filled` credit is unconditional and needs no note.
An update dispatch carries only `review_notes`, so its credit is only as good as
the note that drove it: `sources.py` reads the slug's **archived** notes
(`_review/processed/{slug}.notes.yaml`) and credits a source only where a
`kind: source` item names it. The archive is the success signal — the driver
archives after a batch succeeds, exactly as it passes `--filled` only for fills
that succeeded — so no new "did it work?" channel was invented. `--updated
<slugs>` additionally trusts the live note, for a driver that credits before it
archives.

**The dedupe trace is that same `consumed` record.** At the confirm gate,
`scaffold.py` skips any `(source, slug)` pair already in `consumed`, so the same
source cannot re-notify a procedure that already absorbed it — even many passes
later, and even while the source is still outstanding for its *other*
procedures. Two cheaper layers sit above it: a source already in `processed/` is
never considered, and `notes_util`'s fingerprint dedupe (which now covers `kind`
and `src`) absorbs a re-confirmed proposal whose note is still pending. All three
are folder state, so `decide()` stays pure — it reads `sources.yaml` and the
`_review/` tree, and remembers nothing.

### What the orchestrator's prompt must gain (NOT built here)

`skills/consult-orchestrate/SKILL.md` was outside this pass's ownership. Until it
lands, a driver following the skill applies source notes and then never retires
the source (it rests at guard 5a's gate, which names the command it skipped). It
needs exactly four things:

1. **`apply_review` gains a source-note branch.** After the batch and the existing
   `archive-review --slugs <slugs…>`, run
   `sources.py mark-processed <area> --updated <slugs…>` — the slugs whose update
   drafter **succeeded**. Retirement is credited from the notes' `kind: source` +
   `src:` fields, so this is what moves a source that only enriched drafted
   procedures. Never pass those slugs as `--filled`: that credits every source
   touching them regardless of kind, which is precisely the kind-blind accounting
   the bus contract forbids.
2. **The dispatch shape is unchanged, and SRC- resolution is the drafter's job.**
   `{area, slug, mode: update, review_notes: _review/{slug}.notes.yaml}` — still
   no `sources` list. Add one line to the handler: a note item may carry
   `kind: source` with `src: SRC-<id>`, and the drafter resolves that id through
   `_reference/sources.yaml` to find the file. Do not paste source paths into the
   prompt; do not widen the dispatch.
3. **`fill` keeps `--filled`** (first-draft credit, unconditional) — unchanged
   wording, but the "Moving inputs" section should say *why* the two flags differ.
4. **An `unresolvable` handler** (still missing from M18 as well): stop, print
   `details.state` / `details.human_action`, and for guard 5a name the
   `details.stranded_ids`. It is a resting gate (exit 0), not a failure.

Signals-dictionary rows worth adding: `sources.yaml` `hash` ("what the advisor
compares to decide a source has already been assessed — editing it buys a
redundant taxonomy dispatch"), `sources.yaml` `consumed` ("which slugs have
absorbed the source; written by mark-processed, and the dedupe trace"), and
`_review/*.notes.yaml` `kind` ("who queued this item; only `source` items retire a
source").

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
