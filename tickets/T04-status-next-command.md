# T04 — `status`/`next` reporting command

- **Slice:** 1 (floor) · **Depends:** T03 · **Touches:** `scripts/state_machine.py`
- **Refs:** `orchestration_contract.md` §4; spec §4.

## Goal
One compact, read-only command the orchestrator polls to decide the next step — so the agent never scans
whole files. Reads state + register + the ingest manifest/dir + the `classify/` artifacts.

## Scope (build)
`state_machine.py status --engagement E [--json]` reports, for the engagement:
- **un-classified docs:** ingested MDs (from `ingested/` or the manifest's active set) with **no**
  `classify/{hash}.artifact.json`.
- **diagnosis-dirty nodes:** `is_diagnosis_dirty(node)` true (from T03).
- **gap state:** nodes with open structural/conflict gaps (count).
- **draftable nodes:** coverage `partial|covered` with `sop.status`/`improvement.status` still `not_started`.
- **per-stream progress:** counts by `sop.status` and `improvement.status`.
- **needs-human:** open `requires_human_review` rows, `unmapped` with `disposition==pending`, conflict gaps.
Default output: a compact human-readable summary. `--json`: a machine object with the same fields (this is
what `consult-run` consumes).

## Out of scope
Acting on the report (that's T19 orchestration). This is read-only.

## Tests (scratch `__t04__`, remove at end; do not commit)
1. Fresh `init` → all docs un-classified count 0 (none ingested), 0 dirty nodes, draftable 0.
2. After `add-evidence` on a node → that node appears in diagnosis-dirty; `--json` includes it.
3. After `add-item --type unmapped` → needs-human shows 1 unmapped pending.
4. Drop a fake `ingested/x.md` + matching manifest/dir entry but no artifact → un-classified shows it; add a
   `classify/{hash}.artifact.json` → it drops off.
5. `--json` parses and carries every documented field; command is read-only (state byte-identical before/after).

## Done when
Tests pass; compiles; report output.
