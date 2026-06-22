# T32 — Review-dirty: applied review changes trigger re-consolidation

- **Slice:** 2 · **Depends:** T31, T13 · **Touches:** `scripts/state_machine.py` (add `mark-dirty`), `scripts/review_ingest.py` (wire it)
- **Refs:** `generation_review_contract.md` §2 ("substance changes mark nodes dirty"); demo follow-up.

## Goal
When review ingestion applies a lens/finding change to a node, that node must become **diagnosis-dirty** so
the next `consult-run` re-consolidates it (regenerating the node MD to reflect the corrected state). Today the
dirty signal is evidence-specific (`last_evidence_at > consolidated_at`) and a review `set-lens` doesn't bump
it, so corrected lenses never flow into the narrative.

## Scope (build)
1. **`state_machine.py mark-dirty --node KEY`** — sets `node.last_evidence_at = now_iso()` (and `updated`),
   so `is_diagnosis_dirty` fires. (Semantics: `last_evidence_at` = "last time the node's diagnostic input
   changed" — new evidence OR an applied review correction; document this in the function/command help.)
2. **`review_ingest.py apply`** — after applying the resolver actions, collect the set of nodes touched by a
   **substance** command (`set-lens`, `add-evidence`, or `add-item` with `--l1/--l2`) and call `mark-dirty`
   for each. A pure `set-sop --status` (no diagnostic change) does NOT mark dirty. Record the dirtied nodes in
   the `review_log.md` apply section.

## Out of scope
The re-consolidation itself (that's `consult-run`/`consult-consolidator`, already built). Conflict detection (T33).

## Tests (scratch `__t32__`; build a tiny commented .docx as T31's test did; do not commit)
1. `mark-dirty` on a consolidated node (set `consolidated_at`, then `mark-dirty`) → `is_diagnosis_dirty` True;
   `orchestrate.py next` lists it under consolidate.
2. `review_ingest apply` with a `set-lens` action on a consolidated node → that node is dirty afterward and
   named in `review_log.md`; a review whose only action is `set-sop --status revised` does **not** dirty its
   nodes.
3. State stays schema-valid; both scripts compile.

## Done when
`mark-dirty` + wiring present; tests pass; report output + deviations.
