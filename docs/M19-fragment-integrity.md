# M19 — Fragment integrity in reconcile

> **Status: DESIGNED.** Small, no dependencies.
> Evidence: `docs/audit-decide-exhaustiveness.md` (F2, F5).

## Goal

Close two holes where a structurally broken area passes every check and renders
anyway. `reconcile.py` owns structural integrity and already parses every
fragment; both checks belong there.

## Why

### An empty fragment is indistinguishable from a finished one (F2)

A zero-byte procedure file carries no `unfilled` sentinel, so `unfilled_slugs()`
skips it and guard 4 never re-fills it. Measured downstream: `aggregate.py` exits
0 and `reconcile.py` reports **"No blocking errors."** The procedure renders as an
empty section.

So a drafter that crashes or is interrupted mid-write leaves behind a procedure the
system believes is complete and empty, and **no component anywhere detects it**.
This is the only finding in the audit that reaches the deliverable silently — the
others stall loudly or loop.

The sentinel cannot be the check. It is written by the scaffolder and removed by
the drafter, so its absence proves a drafter *started*, not that it finished.
Substance has to be verified independently.

### A duplicate slug shadows one file's change signal (F5)

`reconcile` already catches duplicate slugs correctly (exit 1, naming the duplicate
`order` and `slug`), so the pipeline stops. The gap is upstream: `proc_hashes()` is
a dict comprehension keyed by slug, so 16 procedure entries over 15 unique slugs
yields 15 hashes — one file's hash is silently dropped, and guard 6 cannot see
edits to the shadowed file. `basis_hash()` appends per file and is unaffected.

Only reachable if reconcile is bypassed, so this is defense-in-depth rather than a
live defect. It is cheap to remove and the asymmetry between the two hash functions
is a trap for whoever next touches them.

## Design

- **Substance check.** A procedure fragment that is zero-byte, or that contains
  no content beyond its heading(s), is a **blocking error** in reconcile, naming
  the file. Deliberately not a length threshold — this is a "did the writer
  finish" check, not a verbosity check (M15's retirement into M16 settled that
  length checks do not belong in reconcile).
- **Detect collision at the source.** `proc_hashes()` returns a mapping keyed by
  slug; where two entries share a slug, the collision must surface rather than
  resolve by last-write-wins. Keying on the manifest `file` (unique by
  construction) removes the asymmetry with `basis_hash()`; whatever shape is
  chosen, a duplicate must not silently vanish from the change signal.

## Acceptance

- A zero-byte fragment fails reconcile, naming the file.
- A heading-only fragment fails reconcile.
- A fragment with real content and no sentinel passes (the normal drafted state).
- A duplicate slug still fails reconcile, and the change signal accounts for both
  files rather than 15 of 16.
- No length- or verbosity-based failure is introduced.

## Out of scope

- Judging draft *quality* or completeness of content (drafter + M12).
- Length caps (M16).
- Re-filling a detected empty fragment automatically — reconcile reports; the
  human or M18's `unresolvable` gate routes it.
