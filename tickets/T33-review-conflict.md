# T33 — Review-path conflict detection (audit the override)

- **Slice:** 2 · **Depends:** T31, T32 · **Touches:** `scripts/review_ingest.py`, `skills/consult-review-comment-resolver/SKILL.md`
- **Refs:** `generation_review_contract.md` §2 ("or a contradiction gap if it conflicts"); adversarial P2 #11.

## Goal
A reviewer is authoritative (human > machine), so a review `set-lens` **applies**. But when it **overrides a
non-null, evidence-backed** state lens with a *different* value, that disagreement must be **recorded**, not
silent — an audit trail so the override is visible.

## Scope (build)
In `review_ingest.py apply`, for each `set-lens` action:
- If the node's current lens value is **null** → just apply (no conflict; first assertion).
- If current is **non-null and equals** the new value → apply (idempotent no-op-ish).
- If current is **non-null and differs** → apply the reviewer's value **and** upsert a `GAP-CONFLICT` register
  row (`type:gap`, `tag:unconfirmed`, `source:review`, stable `dedup_key` like
  `conflict|{node}|{lens}|review`) recording `{node, lens, prior_value, reviewer_value, reviewer,
  comment_id}` in `observation_pain_point`. Note it in `review_log.md`.
Document this in the resolver SKILL (the override-is-applied-but-audited rule).

## Out of scope
Auto-resolving the conflict (the human already decided); the classify-side conflict (already `GAP-CONFLICT-*`).

## Tests (scratch `__t33__`; tiny commented .docx as before; do not commit)
1. Node lens `process=pain_med` (set, simulating evidence-backed); review action `set-lens process strength`
   → lens becomes `strength` AND a `GAP-CONFLICT...review` row exists citing prior `pain_med` + reviewer value.
2. Node lens `null`; review `set-lens process pain_high` → applied, **no** conflict row.
3. Re-apply the same override (new round) → conflict row **upserts** (one row, by dedup_key), not duplicated.
4. review_log notes the override; scripts compile; register schema-valid.

## Done when
Conflict detection in `apply` + SKILL note; tests pass; report output + deviations.
