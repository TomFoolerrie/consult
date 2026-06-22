# T37 — State-driven orchestration: full lifecycle + post-review re-entry + final gate

- **Slice:** 2 · **Depends:** T19, T32, T34 · **Touches:** `scripts/orchestrate.py`, `skills/consult-run/SKILL.md`
- **Refs:** `orchestration_contract.md` §3 (the readiness loop), §5, §6; spec §10.

## Goal
Generalize the Slice-1 **linear** advisor into the full **state-driven** lifecycle: it must handle the
**review re-entry** (after review edits dirty a node, loop back to consolidate → redraft → re-render →
re-review) and terminate at a `final` action **gated by `gates.py final-check`** — not stop at the first render.

## Scope (build)
1. `orchestrate.py next` — keep the readiness-predicate model, but extend the order so it doesn't dead-end at
   `render`: after render, if any node is **diagnosis-dirty** again (e.g. review marked it) → `consolidate`
   (re-entry); if deliverables are stale vs node `reviewed_rev`/`rev` → `draft`/`render` again; once
   everything is rendered/reviewed and **`gates.py final-check` passes** → `final` (the terminal action,
   `kind=deterministic`, sets deliverable statuses `final`); if `final-check` FAILS → `gate_blocked` listing
   the failing gates (do not advance to `final`).
2. Add `orchestrate.py next --all` — list **every** ready action (not just the first), so a multi-session run
   can see the whole frontier.
3. `consult-run` SKILL — document the full loop (Slice 1 path + the review re-entry + the final gate); make
   clear re-running is always safe and resumes from state.

## Out of scope
Applying the actions (the agent/scripts do that). The review ingestion itself (T31).

## Tests (scratch `__t37__`; do not commit)
1. Slice-1 walk still works: init→ingest→…→render→ then with all gates **failing** (e.g. an `unmapped` pending)
   → `next` = `gate_blocked` (NOT `final`/`done`), naming the failing gate.
2. **Re-entry:** with deliverables rendered, `mark-dirty` a node → `next` = `consolidate` (loops back), not done.
3. With gates passing (no pending unmapped, no open human-review) and deliverables rendered → `next` = `final`;
   after applying it, `next` = `done`.
4. `--all` lists multiple ready actions when several exist; `orchestrate.py` stays read-only; compiles.

## Done when
Lifecycle + re-entry + final gate in `next`; SKILL updated; tests pass; report output + deviations.
