# M22 — Enforce the constitution

> **Status: DESIGNED.** No dependencies; build early — every later ticket's
> drafter passes get policed by it.
> Evidence: `docs/audit-decide-exhaustiveness.md` Part 3 (F12–F18).

## Goal

Make `reconcile` police what the docs claim. The system's method is
*correctness by construction, not by instruction* — but the audit's Part 3
shows the core invariants are currently instruction: stated in
`docs/README.md`, restated in tickets, enforced nowhere. This ticket converts
the checkable ones into blocking reconcile errors.

## Why

Two of the unenforced invariants are not hygiene, they are the product:

- **Traceability is the headline claim** ("every claim traces back to a
  source"), and today no script even recognizes an `SRC-` citation. A fragment
  citing `SRC-99` — or nothing — renders into a client document whose
  bibliography implies otherwise. For an audit-facing deliverable this is the
  difference between "traceable" and "decorated with ids".
- **F14 is a live livelock**, not a style issue: one typo'd slug in a source's
  `touches` list makes that source permanently unretirable, and guard 5
  re-fires `taxonomy` forever — the M18 failure shape, selected by a state M18
  does not enumerate.

The rest are the classic silent-drift class this system exists to make
unrepresentable: a second writer, a baked display number, a stray H1 — each
invisible until a reorder or a rerun makes it wrong in front of a client.

## Design

Six checks, all in `reconcile.py` (it owns structural integrity and already
parses every fragment), all **blocking errors** naming file and line, per the
fail-loud contract.

1. **SRC- citations resolve.** Every `SRC-\d+` mentioned in a fragment must
   exist in `_reference/sources.yaml`. A procedure fragment citing **no**
   `SRC-` id at all is likewise an error — the drafter contract mandates Source
   Materials, and a citation-free procedure is either an interrupted draft
   (M19's territory) or untraceable text (this ticket's).
2. **`touches` ⊆ manifest procedure slugs.** Checked both at `sources.py` load
   (fail loud at the source) and in reconcile (fail loud at the gate). Kills
   F14: the typo is named the first time any stage reads the file, instead of
   living forever as an unretirable source.
3. **Ownership markers match the manifest.** Each derived file's
   `<!-- derived: kind; writer: w -->` must match the manifest entry's
   `derived_kind` and `writer`; missing or mismatched is an error. This is the
   *detection* layer for one-writer-per-file — write-time enforcement would
   mean path-scoping every agent's `Write` tool, which is worth doing but is a
   hardening, not a gate; a violation that slips past it is still caught here.
4. **The heading contract.** Any fragment line beginning `# ` (an H1) is an
   error. "The one rule" finally has a police officer.
5. **No baked display numbers.** A narrow contextual pattern —
   `(see|per|step|section)\s+\d+\.\d+` — in fragment or agent-derived prose is
   an error; the sanctioned form is `[[slug]]`. The pattern is deliberately
   narrow: a false positive costs one rewritten sentence, a false negative goes
   silently stale on the first reorder. Fail-loud wins.
6. **Callout IDs stay out of agent-view prose.** `CTRL-`/`GAP-`/etc. ids in
   `82`/`84` outside derived-table rows are an error — render only rewrites ids
   inside procedure sections, so a quoted local id disagrees with the
   document's display numbering.

### What this deliberately does not check

- **Citation truth.** Whether a statement is actually supported by the source
  it cites is judgment, not a join — the human review loop and M12's
  conflict-reporting own that. This ticket checks *existence*, which is the
  precondition for anyone auditing truth.
- **Registry description sourcing (F18).** Uncheckable until registry entries
  carry a citation field; recorded as a schema gap, adjacent to M20's registry
  work, not smuggled in here.
- **Reviewer-derived text.** Facts entering via tracked changes and gap
  answers have no `SRC-` vocabulary today; check 1 must not force drafters to
  fake citations for them. The review-loop provenance gap is real and separate
  (reviewer-as-source); until it is designed, text absorbed from notes cites
  the ids the note carries, and check 1 validates only that cited ids exist.

## Migration

The live P2P area predates every check. First run of the new reconcile is a
**census, not a gate**: run the checks in report mode against
`build/p2p-run-1`, fix what they find (expected: mostly clean — spot-checks
during the audit found citations present), then flip to blocking. Seeded
violations for each check land in `tests/` alongside the audit's state corpus
(the M18 acceptance vehicle), so the constitution stays enforced by regression
rather than by memory.

## Acceptance

- A fragment citing `SRC-99` (unregistered) fails reconcile naming file, line,
  and id.
- A procedure fragment with zero `SRC-` citations fails.
- A `touches` list naming a non-manifest slug fails at `sources.py` load AND
  at reconcile.
- A derived file whose marker kind or writer disagrees with the manifest fails.
- A fragment containing an H1 fails.
- `see 3.2` in prose fails; the same sentence with `[[slug]]` passes.
- A `GAP-` id quoted in `82_dependencies.md` prose fails; the same id in a
  derived-table row passes.
- The P2P area, after census fixes, passes clean.
- Every check has a seeded-violation regression test in `tests/`.

## Out of scope

- Path-scoping agent `Write` tools (hardening; do it, but it is not this gate).
- A citation field on registry entries (schema change; with M20's territory).
- Reviewer-as-source ids (needs its own design; see the audit Part 3 closing
  notes).
- Any length, style, or verbosity check (M15's retirement stands).
