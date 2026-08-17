# M51 — Structured serviceability: the "not yet" report becomes data

**Status: SPECCED** (backlog line, unscheduled — build on the human's go).
Origin: M44 A2 item 1 ("a structured serviceability return is now wanted
by two consumers — brief.py renders the sentences, needs.py re-derives
their attribution"), plus M44 A2 item 4 (the broken-area posture, worth
revisiting now that the render has real consumers).

## Why

`definitions.serviceability(defn, area)` returns flat sentences. That was
honest for its one original reader (a human), but it now has two
programmatic consumers working around the shape:

- `needs.py` cannot learn WHICH binding a gap sentence belongs to, so it
  calls serviceability once per binding on a single-binding copy of the
  definition — N loader passes to recover attribution the function had
  and threw away.
- `brief.py` renders the sentences verbatim and could not attribute them
  if it wanted to.

And the broken-area posture is now load-bearing: an area outside an
engagement tree, or with an unreadable manifest, renders EMPTY
coverage/recorded feeds ("thin is not a defect"), so a genuinely broken
area reads as "no needs" — fine when a human read the render, wrong now
that the taxonomist and the agenda consume it.

## The shape

### Part A — the structured return

`serviceability` returns a list of records — `{"binding", "gap"}` at
minimum (binding name as declared; the existing sentence unchanged) —
with the current flat-sentence rendering derived FROM the records (one
place formats, so brief.py's output is byte-identical). Additive shape
decision at build: either a new verb (`serviceability_records`) with the
old verb delegating, or a changed return with the callers repointed in
the same commit — whichever keeps the M35 loader contract tests
untouched.

### Part B — needs.py consumes it

The `binding-unserved` feed reads the records directly: one loader pass
per definition, attribution from the record's `binding` key. The
per-binding single-binding-copy loop is deleted. Entries byte-identical
(same keys, same order, same sentences) — pinned by the existing M44
fingerprint, which this part must NOT re-pin: identical output is the
point.

### Part C — the broken-area refusal

A named posture instead of a silent empty: an area path that resolves to
no engagement root, or a manifest that exists but cannot be read, REFUSES
by name (the `_root_of` idiom, `DefinitionError` or a sibling) rather
than rendering "no needs". A merely thin area — real root, real manifest,
nothing captured yet — still renders its honest near-empty report ("thin
is not a defect" survives; BROKEN is now a defect). agenda.py inherits
the refusal through its needs call.

## Test impact

New gate: `tests/test_serviceability_m51.py` (committed with this spec,
skip-gated on the structured return existing). Licensed edits: none
expected — Part B is pinned byte-identical by the existing M44
fingerprint, brief.py output is pinned byte-identical by its existing
gates; if the build cannot hold byte-identity it stops and amends the
spec. **Zero v1 tests change.**

## Acceptance gate

`tests/test_serviceability_m51.py`: the records carry binding attribution
matching declaration order; the flat rendering is derived from the
records and byte-equal to today's; needs.py makes one loader pass per
definition (mechanical: the single-binding-copy helper is gone); the M44
fingerprint is unchanged; a rootless area and an unreadable manifest
refuse by name while a thin-but-real area still renders.
