# T31 — Review ingestion: extract → resolve → apply (+ review log, consumed marker)

- **Slice:** 2 · **Depends:** T30 (docx_comments) · **Touches:** `scripts/review_ingest.py` (new), `skills/consult-review-comment-resolver/SKILL.md` (extend)
- **Refs:** `generation_review_contract.md` §2 (Ingest the review), §3; adversarial P1 #6 (consumed marker).

## Goal
Turn a reviewed `.docx` (comments + edits) into structured updates applied through the state/register
commands, attributed, logged, and **idempotent** (a re-run must not double-apply).

## Scope (build)
1. **`scripts/review_ingest.py`** with two subcommands:
   - `extract --engagement E --docx PATH [--round N]` — run `docx_comments.py` on the docx; compute the
     docx content hash; if that hash is already in `engagements/E/review/consumed.json`, **skip** (idempotent
     — the consumed marker, resolves the crash-replay double-apply). Otherwise emit the comments bundle (JSON)
     for the resolver, and append one entry per comment to `engagements/E/deliverables/review_log.md`
     (`{round, reviewer/author, anchored_text, comment}`). Do **not** mark consumed yet (apply does).
   - `apply --engagement E --docx PATH --actions ACTIONS.json [--round N]` — given the resolver's proposed
     actions (a JSON list of `{command, args, reviewer, comment_id}`), run each via the existing commands
     (`set-lens`/`add-item`/`set-sop`/`set-improvement`), append the before→after to `review_log.md`
     attributed to the reviewer, then **mark the docx hash consumed**. Nodes whose substance changed are left
     diagnosis-dirty (a lens/finding change bumps state) for re-consolidation on the next `consult-run`.
2. **Extend `consult-review-comment-resolver/SKILL.md`** — document the flow: `review_ingest extract` →
   classify each comment (existing categories) → map to a command (lens change → `set-lens`; new finding →
   `add-item`; SOP scope/status → `set-sop`; prose-only → node-MD edit; `SME VALIDATION REQUIRED` →
   `add-item`/flag `requires_human_review`) → emit the actions JSON → `review_ingest apply`. Note a lens
   change that conflicts with an evidence-backed value should raise a `GAP-CONFLICT` (full detection is T33).

## Out of scope
Full conflict detection (T33), the `final` DoD gate (T38), state-driven loop (T37).

## Tests (scratch `__t31__`; build a tiny commented .docx like T30's fixture; do not commit)
1. `extract` on a commented docx → comments bundle (JSON) + a `review_log.md` with the entries; docx NOT yet
   consumed.
2. `apply` with a small actions JSON (e.g. one `set-sop --status revised`, one `add-item` finding) → commands
   ran (verify via `get-node`/register), `review_log.md` has before→after attributed, docx hash now in
   `consumed.json`.
3. **Idempotency:** re-run `extract` on the same docx → **skipped** (consumed); re-`apply` → no double-apply.
4. A docx with no comments → empty bundle, exit 0. Scripts compile; SKILL documents the full flow with real
   commands only.

## Done when
Helper + SKILL present; tests pass (esp. the consumed-marker idempotency); report output + deviations.
