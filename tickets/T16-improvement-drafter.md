# T16 — `consult-improvement-drafter` (Stream B, per L1)

- **Slice:** 1 · **Depends:** T13, T15 (reuses `draft_inputs.py` read-only — does NOT edit it) · **Touches:** `skills/consult-improvement-drafter/` (new)
- **Refs:** `generation_review_contract.md` §1 (5B); spec §5 Stage 5B + Improvement DoD.

## Goal
Draft the Process Improvement Opportunities deliverable per **L1**, from the register's
`type:improvement` rows grouped **by lens**, writing status back.

## Scope (build)
`skills/consult-improvement-drafter/SKILL.md` — per-L1 sub-agent brief:
- Source via `scripts/draft_inputs.py gather --engagement E --l1 L1 --json` (read-only; built in T15) — use
  its register rows; **group the `type:improvement` rows by lens** (`process`/`automation`/`operating_model`/
  `capability`).
- Output `deliverables/improvements/{l1}.md`: each item **Finding → Recommendation → Effort × Impact →
  Owner**, traceable to its **register ID** + evidence ref. Effort×Impact rendered as **`directional`**
  unless a quantified source backs it (never invent a number). Items missing Effort/Impact/Owner are
  surfaced as needing input, not fabricated.
- **Write back** `improvement.{status,path,rev}` via `set-improvement` to that deliverable path.

## Out of scope
The synthesis/prioritization roll-up (T17). Word render (T18). Do not edit `draft_inputs.py`.

## Tests (scratch `__t16__`; seed improvements of different lenses; do not commit)
1. SKILL.md present; documents `draft_inputs.py gather`, by-lens grouping, the directional Effort×Impact
   rule, and `set-improvement` write-back; every command/flag it shows exists.
2. Run its documented `set-improvement --status draft --path deliverables/improvements/record-to-report.md
   --bump-rev` against a scratch engagement → `get-node` reflects `improvement.status==draft`, rev 1.
3. (If it adds any helper) that helper is read-only / tested; otherwise confirm it relies only on the
   existing read-only `draft_inputs.py`.

## Done when
SKILL present; tests pass; report output + deviations.
