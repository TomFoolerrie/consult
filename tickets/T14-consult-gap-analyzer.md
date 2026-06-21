# T14 — `consult-gap-analyzer` skill (substantive gaps)

- **Slice:** 1 · **Depends:** T13 (consolidated node MD) · **Touches:** `skills/consult-gap-analyzer/` (new)
- **Refs:** `consolidate_contract.md` §7; spec §5 Stage 4; `gap_report.py` (structural, already built — this is the LLM sibling).

## Goal
The LLM layer of Stage 4: read a **consolidated** node (MD + evidence + register rows) and add the
substantive gaps the mechanical scan can't see — contradictions, thin / single-source evidence,
undocumented controls, verbal-only control claims, conflicting lens signals.

## Scope (build)
`skills/consult-gap-analyzer/SKILL.md` — per-L2 (or per-L1) sub-agent brief:
- Runs **after consolidate** (needs the synthesis). Reads the node MD + the node's evidence (with
  `evidence_tier`) + existing register rows (reuse `consolidate_inputs.py gather`).
- Emits substantive gaps as `type:gap` register rows via `add-item`, each with a stable `dedup_key`
  (so re-runs upsert, not duplicate), a `tag` from the gap vocab, evidence ref in `source`, and an
  observation. Specifically flag: a **control or procedure-critical claim with `evidence_tier:verbal`**
  (per the Evidence DoD), single-source procedural steps, and internal contradictions.
- Never invents evidence; cites register IDs / evidence refs. Does not duplicate structural gaps
  (those are `GAP-STRUCT-*`); substantive gaps get `GAP-<dedup>` ids via the normal `add-item` path.

## Out of scope
Structural scan (`gap_report.py`, done). The disposition/gate (S2).

## Tests (scratch `__t14__`; do not commit)
1. SKILL.md present; names `consolidate_inputs.py gather`, the `add-item` + `dedup_key` path, and the
   `evidence_tier:verbal` control-claim rule; no invented flags (every command/flag it shows exists).
2. Run its documented `add-item` example for a substantive gap against a scratch engagement → the row lands,
   register schema-validates, and re-running the same `add-item` (same `dedup_key`) yields **one** row.
3. Confirm it does not collide with `GAP-STRUCT-*` ids (its example uses a distinct id/dedup_key).

## Done when
SKILL present; tests pass; report output + deviations.
