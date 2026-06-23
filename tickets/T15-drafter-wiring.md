# T15 — `consult-drafter` wiring: SOP from state/register, per L1

- **Slice:** 1 · **Depends:** T13 · **Touches:** `scripts/draft_inputs.py` (new), `skills/consult-drafter/SKILL.md` (extend)
- **Refs:** `generation_review_contract.md` §1 (5A); `skills/consult-drafter/SKILL.md` (existing L1-Level mode + Quality Checklist DoD); spec §5 Stage 5 + DoD.

## Goal
Wire the existing drafter to source from state/register (it predates the state model). Output one SOP per
**L1 cycle** (the drafter's existing L1-Level mode), writing status back.

## Scope (build)
1. **`scripts/draft_inputs.py gather --engagement E --l1 L1 [--json]`** (READ-ONLY): assemble the L1 bundle —
   for every L2 under the L1: its node MD (narrative), lenses, and the register rows mapped to the SOP
   appendices: improvements → **Appendix B**, gaps → **Appendix C**, screenshots → **Appendix D**, pain
   points (process lens) → **Appendix A**. Include evidence refs (`path#L-L`) for inline rendering, and each
   row's `evidence_tier`.
2. **Extend `skills/consult-drafter/SKILL.md`** with a "Source from engagement state" section: how to call
   `draft_inputs.py gather`, the register→appendix mapping, render evidence refs inline, control claims that
   are `verbal`-tier must show as a gap (Evidence DoD), and **write back** `sop.{status,path,rev}` via
   `set-sop` to `deliverables/sop/{l1}.md`. Keep the existing Quality Checklist as the DoD.

## Out of scope
The Word render (T18). Stream B (T16). Don't rewrite the canonical template; don't touch the handlebars
shell template (flagged separately for cleanup).

## Tests (scratch `__t15__`; build a node with a node MD + register rows of each type; do not commit)
1. `gather --l1 record-to-report` returns the bundle with each L2's node MD + lenses + the register rows
   correctly bucketed (improvement→B, gap→C, screenshot→D, process-pain→A); `--json` parses.
2. `draft_inputs.py` is read-only (state byte-identical before/after).
3. `set-sop --status draft --path deliverables/sop/record-to-report.md --bump-rev` writes back; `get-node`
   reflects it.
4. SKILL.md section present; the gather/set-sop commands it documents all exist (no invented flags).

## Done when
Helper + SKILL section present; tests pass; report output + deviations.
