# T39 — Rewrite `consult-improvement-log` SKILL (drop CSV workflow; agent-driven register engine)

- **Slice:** 2 (doc-debt) · **Depends:** — · **Touches:** `skills/consult-improvement-log/SKILL.md`
- **Refs:** spec §3 Layer 2, §4, §10; the actual `improvement_log.py` commands (`upsert-json`, `build-xlsx`, `remove`, `validate`).

## Goal
The SKILL.md still documents the **dropped** human CSV/Excel review round-trip ("Path A — JSON + CSV",
`build-xlsx` as the review workbook, `update-json` from a hand-edited CSV). Recast it as the **agent-driven
register JSON engine** matching how the pipeline actually writes the register.

## Scope (build)
Rewrite `skills/consult-improvement-log/SKILL.md` to document, accurately against the current code:
- The register is the unified item store (types: improvement/gap/screenshot/unmapped/theme); rows carry
  `dedup_key`, `evidence_tier`, `disposition`, `related_nodes`, etc.
- **Writes are agent-driven** via `upsert-json` (JSON records, upsert by `dedup_key` then `id`) — typically
  through `state_machine.py add-item`. **No human CSV import.**
- `validate` (vocab + optional `--schema`), `remove` (archive/delete). `build-xlsx` retained only as an
  **optional read-only snapshot**, not a review round-trip. The legacy CSV `update-json` exists for
  back-compat but is not the workflow.
- Cross-reference: humans review via Word (Stage 6), not Excel.
Keep it tight and accurate; no invented flags.

## Out of scope
Any code change to `improvement_log.py` (this is a doc rewrite only).

## Tests (no scratch engagement; do not commit)
1. Every command/flag the rewritten SKILL names exists in `improvement_log.py` (grep-verify each).
2. No remaining reference to a human CSV/Excel **review** round-trip (no "Path A — JSON + CSV" review cycle,
   no "edit the workbook and re-import"); `build-xlsx` framed read-only.
3. The five register `type` values and the new fields (`dedup_key`/`evidence_tier`/`disposition`/
   `related_nodes`) are documented.

## Done when
SKILL rewritten + accurate; the three checks pass; report what changed + any deviation.
