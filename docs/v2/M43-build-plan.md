# M43 build plan — drafting path + hygiene feeder

> Foundation for [`M43-drafting-path-hygiene.md`](M43-drafting-path-hygiene.md).
> Gate: `tests/test_hygiene_m43.py` (per-package skip gates — each class
> unskips on ITS package's files, so packages commit independently with
> the suite green). Ground rules as ever.

## Design pins

- The unit line derives from `definitions.resolve_definition(area)`'s
  entity-part binding type; unresolvable → "activity (default)". No
  hand-minted dispatch key, no config.
- The four CTRL field names live on the CONTROL callout declaration
  (`fields:` — kernel's callout-key allowlist +1, parse behavior
  unchanged; documentation + consumer vocabulary only).
- hygiene.py: engagement-scoped, analysis.py's conventions verbatim
  (grounds, deterministic order, no cache, HygieneError only for
  declaration failures). Gap/control kinds via definition bindings +
  declaration — zero shape-audit entries. `ledger.outstanding` is the
  answered-gap primitive. Duplicate detection: normalized token overlap
  (lowercase, whitespace collapse, [[slug]] flattened, SRC ids
  stripped) at a fixed documented threshold — candidates, not verdicts.
- placement_brief's CALLOUT HYGIENE section: after the open-gap
  register; counts + samples, never walls; return contract gains
  `callout_grooming` (sync with the librarian contract's existing key).

## Work packages

### WP-H1 — declaration + generators (code)
Owns `kernel/types/process-step.yaml` (CONTROL gains `fields:`),
`scripts/kernel.py` (additive: callout-key allowlist + CalloutDecl
field), `scripts/hygiene.py` (new).
Targets: TestDeclaredFields, TestDuplicateGaps, TestAnsweredGaps,
TestThinCtrls, TestGeneratorDiscipline.

### WP-H2 — brief + librarian wiring (code)
Owns `scripts/brief.py` (the YOUR UNIT line), `scripts/engagement.py`
(the CALLOUT HYGIENE section + return-contract sync),
`agents/consult-librarian.md` (the feeder named; "does not exist yet"
retired). Sequenced AFTER WP-H1 (imports hygiene).
Targets: TestUnitLine, TestLibrarianWiring.

### WP-H3 — the drafting path (prose)
Owns `agents/consult-drafter.md` + `docs/v2/notes/m43-path-self-review.md`.
Parallel with WP-H1.
Targets: TestDraftingPath.

## Sequencing
WP-H1 ∥ WP-H3 → WP-H2 → close-out (2.1.0-alpha.6).
