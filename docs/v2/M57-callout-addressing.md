# M57 — One address per callout: grounding stops crossing id namespaces

**Status: RECORDED** (not scheduled).
Origin: the adversarial review of `main` @ 8b22e9e (2026-08-20),
findings F-06, F-12, F-11 — all reproduced on the standing fixtures.

## Why

Two id namespaces coexist by design — procedure-LOCAL callout ids
(`GAP-01` restarts per procedure) and document-global DISPLAY ids
(`doc_model.callout_display_ids` renumbers for rendering). The design
is fine; the defects are three seams where one module emits one
namespace and its consumer resolves the other:

1. **The analyst loop cannot be followed** (`analysis.py:552` vs
   `findings.py:299–307`). `conflict_records()` labels each conflict
   with its DISPLAY id; `resolve_grounds()` builds its valid-ground
   universe from LOCAL ids. On p2p-complete, grounding a finding on the
   id the brief displays fails for 26 of 28 conflict records ("ground
   'GAP-07' does not resolve") — and the 2 that do resolve bind the
   WRONG callout in a different procedure. `analyst_brief` instructs
   exactly this grounding; the instruction is unfollowable.

2. **`findings.for_area` misattributes across areas**
   (`findings.py:441–449`). Area membership is a flat-string join of a
   finding's grounds against `callouts | slugs`, where callout ids are
   LOCAL — reused across procedures and areas. A finding grounded on
   "GAP-01" surfaces in EVERY area whose corpus contains a GAP-01, so
   one area's finding lands in another's analyst brief, and the brief's
   "already on the register is not a new finding" rule then suppresses
   legitimate findings there.

3. **Same family, adjacent key: `node_steps` keys by TITLE**
   (`plan_views.py:178–188`). The node→step relation maps group titles
   back to slugs via a title-keyed dict built with `setdefault`; two
   taxonomy nodes sharing an H2 title (two "Exceptions" sub-cycles)
   both resolve to the FIRST slug and the second assignment overwrites
   the first. Coverage — which feeds the information request, needs,
   and agenda — then reports the losing node as covered when it isn't.
   Reproduced on a retitled IPO-fixture copy.

## The shape

### Part A — one grounding currency, stated and enforced

Rule: **a ground is a procedure-qualified callout address** —
`<procedure-slug>:<LOCAL-id>` — or an entity slug. Unqualified local
ids remain accepted ONLY while unambiguous within the corpus (exactly
one procedure carries that id); ambiguous unqualified grounds are
refused with the candidate qualified forms listed. `resolve_grounds`
resolves the qualified form; `conflict_records` emits it (keeping the
display id alongside for the human, clearly labeled as display-only).
The analyst instruction and skill passages quote the qualified form.

### Part B — `for_area` joins on qualified addresses

`_area_corpus_ids` carries qualified callout addresses; membership is
by qualified match (or entity slug). A finding grounded in procedure
`confirming-po`'s GAP-01 belongs to exactly the area holding that
procedure — never to a stranger area that happens to also count to 1.

### Part C — `node_steps` keys by slug

`group_steps` already knows the slugs it grouped; carry the slug
through instead of round-tripping via title. Where two nodes share a
title, both keep their own steps. (If a hygiene rule should also
discourage duplicate node titles, that is a separate groomer note —
the relation must be correct regardless.)

## The gate

- On p2p-complete: every id `conflict_records` shows resolves through
  `resolve_grounds` — 28 of 28 — and binds the callout in the procedure
  the record came from.
- Two-area fixture with colliding local ids: a finding grounded in area
  A appears in `for_area(root, A)` only.
- Ambiguous unqualified ground → refusal listing qualified candidates.
- Duplicate-title fixture: `node_steps` maps both slugs; `coverage()`
  unchanged for the untouched node; the retitled-IPO repro from the
  review passes.
- Frozen fixtures and the register lifecycle tests pass untouched
  (existing single-procedure grounds remain unambiguous → accepted).
