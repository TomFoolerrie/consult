# M38 — The second deliverable: the generality proof

> **Status: BUILT (2.0.0-alpha.8)** — the process & controls matrix
> renders end-to-end over the IPO fixture engagement (frozen fixture #2,
> all five awkward cases mechanically verified) through the ordinary plan
> path: `kernel/deliverables/process-controls-matrix.yaml` +
> `scripts/matrix_views.py` (all vocabulary derived from declarations —
> zero audit entries) + one `count` verb + landscape capability plumbing
> keyed on the capability name. Gates: `tests/test_matrix_m38.py` 13/13 +
> `tests/test_matrix_roundtrip_m38.py` 8/8 + 1 strict xfail; suite 1045
> passed. Build record: [`M38-build-plan.md`](M38-build-plan.md).
>
> **Amendment A1 (build notes, 2026-08-15):** (1) the zero-engine-edit
> ruling held — the builder registers through the existing registry
> (import + entry + a generic ctx key); the one candidate special-case
> (materializing a manifest-absent view in render_glue) was REFUSED by
> the implementer for lacking an honest discriminator and resolved
> fixture-side instead; (2) LANGUAGE GAP recorded: nothing reflects a
> definition's view blocks into an area manifest — the matrix needed its
> derived component authored in the fixture, and M37's
> information-request views have no builders/manifest entries (that
> definition has never rendered); closing this is a named follow-up
> ticket candidate; (3) review round-trip: markup + extraction + the
> view-rebuild loop all prove out; row-level comment ROUTING lands in
> _unassigned today — the exact fix (table-row first-cell slug
> resolution) is pinned as a strict xfail and needs its own small ticket
> with v1 appendix-table routing characterized first; (4) node grouping
> is mechanical (slug identity, then naming, then Ungrouped); the
> fixture's l2 == node-slug convention keeps the join total. Companions: M35 (the language
> this ticket stress-tests with a shape v1 never had), M33 (the IPO type
> this ticket is the first real consumer of), M36 (the gate proved the
> language can express the OLD deliverable; this ticket proves it can
> express a NEW one). Charter: [`README.md`](README.md).

## The one-sentence contract

Ship one deliverable definition that v1 could not produce — matrix-shaped,
IPO-fed, cross-step — end to end: definition → plan → views → rendered
docx → review round-trip, with **zero engine edits** beyond declared
binding-vocabulary growth.

"Zero engine edits" is the proof. If M38 needs a special case in the
loader, the compiler, or the renderer, M35's language failed its purpose
and gets amended THERE, not patched here.

## The chosen deliverable: the process & controls matrix

Chosen over a narrative because it exercises everything a narrative
wouldn't (a narrative is close to the desktop procedure's shape; a matrix
is orthogonal to it):

- **repeat-over a join**, not an entity walk: rows are process steps,
  grouped by taxonomy node,
- **columns from four different kernel surfaces**: step identity + owner
  (roles channel), system(s) (systems channel), inputs/outputs (IPO
  edges), controls (CTRL callouts), open pains/gaps (PAIN/GAP callouts,
  counted),
- **a table-first skin**: landscape docx, repeated header rows, a shape
  the v1 renderer never drew.

The definition ships as `kernel/deliverables/process-controls-matrix.yaml`
— the second worked example users copy from, and the first that shows a
NON-document-shaped deliverable.

## What this ticket is allowed to add

- **Binding vocabulary**: only verbs the matrix demands and M35 reserved
  headroom for (the join/group/count family). Each addition is named in
  the landing note with its consuming binding — the M35 discipline,
  enforced at review.
- **Docx skin capabilities**: landscape, table-heavy layout, header-row
  repetition — declared renderer capabilities (M35's mechanism), so the
  loader's skin-check learns them for free.
- **Nothing else.** No new entity types, no new agents, no new gates, no
  new state.

## The prerequisite honesty clause

The matrix reads IPO-shaped content — but at this point in the spine no
real engagement content is IPO-shaped (the p2p fixture is `activity`-
typed; M37+ authors new content as `process-step`). So M38 proves
generality against **a purpose-built IPO fixture engagement** (hand-
authored, small — one taxonomy node, four to six steps, seeded pains/
controls/conflicts), which becomes the repo's second standing fixture:
the v2-native counterpart of the p2p fixture. The matrix over real client
content is an outcome of running v2 on a real engagement, not of this
ticket.

## Review round-trip (the half of generality that's easy to skip)

The matrix is a docx, so it inherits the docx skin's review pipeline
(M35: review attaches to the skin). This ticket proves that inheritance
holds for a table-first document: reviewer edits a cell + comments a row
→ extract → notes bus → the OWNING step's drafter is re-dispatched → the
matrix view rebuilds → re-render. The matrix itself is a VIEW — no
reviewer edit ever lands in the matrix; it lands in the step that feeds
it (the v1 doctrine, now proven for a deliverable whose reading order is
nothing like its storage order).

## Acceptance sketch (firm up at build time)

- The definition passes all four loader stages; the plan builds the join
  view python-side; the docx renders from the IPO fixture with correct
  grouping, counts, and cross-references (golden file).
- Zero-engine-edit audit: the diff touches `kernel/deliverables/`, binding
  vocabulary (each verb named + consumed), renderer capability
  declarations, the fixture, and tests — nothing else.
- The review round-trip test above, end to end on the fixture.
- Serviceability honesty: the matrix definition against the (activity-
  typed) p2p fixture reports "not yet" with the missing type named — the
  M35 gate doing its job on a real case.
- Both shipped definitions coexist in one engagement and render
  independently (the M35 independence claim, now with a real second
  subject).
- v1 suite green.

## Complexity accounting (the standing test)

New state files: zero (one committed fixture). New gates: zero. New agent
judgment: zero — the matrix is entirely python-writer views over existing
judgment. The bill is binding verbs (each with a named consumer), renderer
capabilities, and the fixture. The review risk to police: **fixture
convenience** — a fixture subtly shaped to what the binding verbs already
do, instead of what real process content looks like; the fixture must
include at least one of each awkward case (a step with no controls, a
shared input, an unresolved conflict, a pain with no gap).

## Deferred (recorded, not built)

- **The process narrative** as deliverable #3 — closer to the desktop
  procedure's shape, so it proves little; ships when a user wants it.
- **xlsx skin for the matrix** — the obvious eventual home for a matrix;
  waits for the xlsx adapter (M35 deferred list), and the definition's
  shape/bindings layers are already skin-agnostic by construction.
