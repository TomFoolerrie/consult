# T34 — Unmapped disposition lifecycle + DoD `final` gate (merges T34+T38)

- **Slice:** 2 · **Depends:** T32 (`mark-dirty`) · **Touches:** `scripts/gates.py` (new), `skills/consult-review-comment-resolver/SKILL.md` (extend)
- **Refs:** `classify_contract.md` §5b (disposition lifecycle); spec §5 DoD + completeness rubric; spec §8 open #9.

## Goal
Make "is this engagement done?" machine-checkable: every `unmapped` row **dispositioned** (not merely owned)
and the DoD gates enforced before `final`. No new `state_machine.py` code — disposition is a register field
update via the existing upsert; the gate is a new read-only checker.

## Scope (build)
1. **Disposition set** — document/use the existing path to set an `unmapped` row's `disposition`:
   `state_machine.py add-item --type unmapped --id UNM-NNNN --field disposition=<reclassified|converted|out_of_scope> --field note=...`
   (upsert-by-id updates the row). For **reclassified**, the human supplies the target `{l1}.{l2}`; the flow
   also archives the unmapped row (`--field record_status=archived`) and calls `state_machine.py mark-dirty
   --node {target}` so the content is re-diagnosed (pipeline never auto-buckets). Document these three
   dispositions in the resolver SKILL.
2. **`scripts/gates.py final-check --engagement E [--json]`** (READ-ONLY) — reports PASS/FAIL on the DoD
   gates and refuses to bless `final` unless all pass:
   - every `type:unmapped` active row has `disposition != pending`;
   - zero open `requires_human_review` rows (excluding archived);
   - (best-effort) every node-evidence ref resolves to its ingested MD;
   - no node with `sop.status`/`improvement.status == final` lacking a path.
   Print each failing item; exit 0 only when all gates pass (nonzero otherwise).
3. **Resolver SKILL** — document the three dispositions and that `gates.py final-check` must pass before any
   deliverable is set `final`.

## Out of scope
The evidence-auditor LLM pass itself (separate skill, already exists — invoke it in the playbook later);
the coherence check (T35).

## Tests (scratch `__t34__`; do not commit)
1. Seed an engagement with 1 `unmapped` (disposition pending) → `final-check` FAILS naming it; set its
   disposition via the add-item upsert → `final-check` passes that gate.
2. **Reclassify path:** disposition=reclassified + archive + `mark-dirty {target}` → the unmapped row is
   archived and the target node is diagnosis-dirty (`orchestrate next` → consolidate).
3. A `requires_human_review=true` row → `final-check` FAILS; clearing it → passes.
4. `gates.py` is read-only; `--json` parses; compiles. Resolver SKILL documents the dispositions + the gate.

## Done when
`gates.py` + SKILL present; tests pass; report output + deviations.
