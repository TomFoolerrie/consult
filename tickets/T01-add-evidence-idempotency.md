# T01 — `add-evidence` idempotency + `last_evidence_at` + dirty predicate

- **Slice:** 1 (correctness floor) · **Depends:** — · **Touches:** `scripts/state_machine.py`
- **Refs:** spec §10 hardening (S1, first item); `classify_contract.md` §5; `consolidate_contract.md` §3; adversarial review P0 #1, #2.

## Goal
Make `add-evidence` idempotent and have it stamp the timestamp the diagnosis-dirty signal needs.
Today `cmd_add_evidence` appends unconditionally and never sets `last_evidence_at`, so (a) routine
merge re-runs duplicate every evidence entry and (b) the dirty predicate can never fire → consolidate
would never run.

## Scope (build)
1. **Dedup by ref:** an evidence entry is identified by `source` + `loc` (composing to
   `path#Lstart-Lend`). If an entry with the same `(source, loc)` already exists on the node,
   `add-evidence` is a **no-op** (do not append, do not bump timestamps). Print a clear "already
   present" message, exit 0.
2. **Stamp `last_evidence_at`:** on a real (non-duplicate) add, set `node.last_evidence_at = now_iso()`
   (in addition to `node.updated`). The field already exists in `engagement_state.schema.json`.
3. **Optional `--tier`:** accept `--tier {verbal,documentary,system_observed}` and store it on the
   evidence entry (schema already allows `tier`). Default null.
4. Keep recompute-coverage behavior.

## Out of scope
The dirty *predicate consumer* (status/next, consolidate) — those are T04/T13. Just produce the stamp.

## Tests (write + run; scratch engagement `__t01__`, remove at end; do not commit)
1. `add-evidence` once → evidence count 1, `last_evidence_at` set, coverage `partial`.
2. **Idempotency:** the identical `add-evidence` again → still count 1, message says already-present,
   `last_evidence_at` unchanged from the first add (capture and compare).
3. A different `--loc` on the same node → count 2 (distinct ref), `last_evidence_at` advances.
4. `--tier documentary` persists on the entry; `get-node --json` shows it.
5. State stays schema-valid (`validate`).

## Done when
All tests pass; `state_machine.py` compiles; no scratch engagement left; report test output.
