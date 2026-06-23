# T51 — `validate` also schema-checks `register.json`

**Slice 3 · Follow-up (post-review) · Depends: — · Touches: `scripts/state_machine.py`,
possibly `tests/test_schema_validate.sh`**

## Problem
`state_machine.py validate` only schema-checks **`state.json`** against
`engagement_state.schema.json` (`_validate_structure`, `state_machine.py:454-465` —
`schema_check(json.load(f), STATE_SCHEMA_PATH)`). **`register.json` is never validated against
`schemas/item_register.schema.json`.** Surfaced by T49: off-vocab register values (e.g.
`effort=medium` vs schema `low|med|high`; `priority=high` vs `p1|p2|p3`;
`impact_type=cycle_time` vs the `cost|time|risk|quality|control` enum) pass `validate` clean.

Those values are real `item_register.schema.json` violations. Today the *only* thing that
flags them is the register engine's **intentionally soft** validation
(`improvement_log.py` sets `requires_human_review=true` rather than rejecting). That soft path
is by design (spec §… controlled-vocab is advisory, not enforced) — so this ticket must
**not** turn it into a hard reject. The gap is purely that `validate`'s *structural* section
is silent about the register's structure.

## Decision required (pick one before building)
- **(A) Report-only register schema section** *(recommended)* — add a register block to
  `_validate_structure` that runs `schema_check(register, ITEM_REGISTER_SCHEMA_PATH)` and
  prints the errors as an **informational** section (like the existing "Schema: OK" line),
  but does **not** set `issues = True` for vocab violations — so `validate` (and the `final`
  gate) stay green on soft-flagged rows. This makes the violations *visible* without changing
  the soft contract. Optionally only escalate to a hard failure for **structural** breaks
  (missing required keys, wrong types, bad `type` enum), keeping *vocabulary* enums advisory.
- **(B) Strict-only enforcement** — keep `validate` green by default, but under the existing
  `--strict` flag, treat register schema errors as `issues` (non-zero exit). Leaves default
  behavior identical; gives a hard gate on demand.

Recommend **A** (visibility now, contract unchanged), or **A + B** combined (report by
default, escalate structural breaks always and all-enums under `--strict`).

## Build
1. Add `ITEM_REGISTER_SCHEMA_PATH = REPO_ROOT / "schemas" / "item_register.schema.json"`
   (mirror `STATE_SCHEMA_PATH`, `state_machine.py:45`).
2. In `_validate_structure`, after the state-schema block, load `register.json` (reuse
   `load_register`/the register path from `cmd_init`) and run `schema_check` against the
   register schema. Note `item_register.schema.json` validates the **whole** register object
   (`metadata` + `records`), so feed it the full doc, not just `records`. Print a
   `Register schema: …` section consistent with the existing `Schema:` output.
3. Wire the chosen escalation policy (A / B) into the `issues` return.
4. Keep the soft `requires_human_review` path in `improvement_log.py` **untouched**.

## Tests
Extend `tests/test_schema_validate.sh` (already asserts the soft-flagging path):
- `validate` prints a register-schema section and **lists** the off-vocab errors on the
  canonical r2r-demo / Slice-1 fixture;
- default `validate` still exits 0 on soft-flagged vocab rows (contract preserved);
- a register row with a **structural** break (missing `id`, or `type` outside the enum) is
  reported, and — per the chosen policy — fails appropriately (always for A's structural
  escalation, or only under `--strict` for B);
- `validate --strict` behavior matches the decision.

## DoD
Register schema conformance is visible from `validate`; the soft controlled-vocab contract is
unchanged; default `validate` + the `final` gate stay green on the existing fixtures;
decision (A/B) recorded in the ticket; tests pass; no scratch left.
