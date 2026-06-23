# T12 — `classify_merge.py` (deterministic Stage-2b merge)

- **Slice:** 1 · **Depends:** T01 (add-evidence dedup), T02 (upsert/unmapped/dedup_key), T11 (validator) · **Touches:** `scripts/classify_merge.py` (new)
- **Refs:** `classify_contract.md` §1, §5 (Evidence / Lenses / Candidate findings / Unmapped / Idempotency), §5b; spec §10 hardening; scope-review item 4 (ship the simple lens policy for v1).

## Goal
The deterministic half of classify: read all per-doc artifacts, resolve across documents, and apply
**facts** to state via the existing commands. Idempotent — re-running re-resolves from the full artifact
set, never duplicating. Judgments (candidate findings) are **not** applied here.

## Scope (build)
`scripts/classify_merge.py merge --engagement E`:
1. **Load + validate** every `engagements/{E}/classify/*.artifact.json` via `scripts/validate_artifact.py`
   (subprocess, `--engagement E`). **Skip + report** any artifact that fails (truncated/invalid → must not
   poison the merge); never crash on a bad artifact.
2. **Evidence** — for each `node_hit.evidence[].ref`, call `state_machine.py add-evidence` (subprocess)
   with `--source`/`--loc` parsed from `path#L-L`, `--tier` from the artifact, `--note` from quote/note.
   T01 makes this idempotent (dup ref = no-op). (Refs already validated to resolve in step 1.)
3. **Lenses** — collect all `lens_signals` per `(node, lens)` across artifacts. Drop `low` confidence.
   **v1 policy (simple, per scope review):** if the remaining (med/high) signals **all agree** on one value
   → `set-lens` to it. If **≥2 distinct values** remain → **do not set** the lens (leave null) and
   `add-item` a contradiction gap: `--type gap --tag unconfirmed`, stable `--id GAP-CONFLICT-{l1}-{l2}-{lens}`,
   `--field dedup_key=GAP-CONFLICT-{l1}-{l2}-{lens}` (so re-runs upsert, not duplicate), observation listing
   the conflicting values + evidence refs, `source=classify-merge`. (Defer numeric thresholds.)
4. **Candidate findings** — **NOT applied.** Leave them staged in the artifacts for consolidate (T13).
5. **Unmapped** — for each `unmapped` entry, `add-item --type unmapped` with `--field dedup_key={evidence_ref}`
   (dedup across re-runs), `--field source={evidence_ref}`, observation from `summary`, `disposition` defaults
   pending. (T02 gives null-node + dedup_key upsert.)
6. Print a compact summary: artifacts merged / skipped, evidence added, lenses set, conflicts, unmapped.

All mutations go through the `state_machine.py` CLI (subprocess), like `gap_report.py` — never write state
directly. `add-item` auto-syncs.

## Out of scope
The classifier sub-agent + fan-out (T11/T19). Applying findings (T13). Threshold tuning.

## Tests (scratch `__t12__`; write fixture artifacts + a fake ingested MD with real lines; remove all; do not commit)
1. Two artifacts **agree** on `record-to-report.close` `process=pain_high` (med+med) → lens set to pain_high.
2. Two artifacts **disagree** (`pain_high` vs `strength`, both high) → lens stays null AND a
   `GAP-CONFLICT-record-to-report-close-process` row exists. **Re-run merge → still one** such row (upsert).
3. Evidence refs from artifacts are added; **re-run merge → evidence counts unchanged** (idempotent).
4. An `unmapped` entry → one `UNM-` row; re-run → **not** duplicated (dedup_key = evidence_ref).
5. `candidate_findings` present → **no** improvement/gap rows from them in the register (still staged).
6. A `low`-confidence-only lens → stays null (not set).
7. An invalid artifact (bad node) in the dir → reported as skipped; the merge still applies the valid ones.
8. After merge, `state_machine.py validate` and register schema-validate both pass.

## Done when
Tests pass; `classify_merge.py` compiles; report output + any deviation.
