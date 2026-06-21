# T13 — `consult-consolidator` skill + input-gather helper

- **Slice:** 1 · **Depends:** T02 (dedup_key upsert), T03 (mark-consolidated/dirty), T12 (merged state + staged findings) · **Touches:** `skills/consult-consolidator/` (new), `scripts/consolidate_inputs.py` (new)
- **Refs:** `consolidate_contract.md` (§2 inputs, §3 sequence + ID-before-citation, §4 confirmation policy + dedup_key, §5 node MD, §6 dirty/prose).

## Goal
Per **diagnosis-dirty L2**, turn merged signals + staged candidate findings into (a) confirmed register
rows and (b) the authored node MD. The LLM does the judgment; a small read-only helper assembles its inputs.

## Scope (build)
1. **`scripts/consolidate_inputs.py gather --engagement E --node KEY`** (read-only) → prints/【`--json`】a
   bundle for one L2: the node state (lenses, coverage, evidence list), the existing register rows for the
   node, and the **staged `candidate_findings`** from every `classify/*.artifact.json` whose `node_hit.node ==
   KEY` (each with its `evidence_ref`, `evidence_tier`, proposed `dedup_key`). Optionally include resolved
   evidence excerpts (read the cited MD lines).
2. **`skills/consult-consolidator/SKILL.md`** — the per-L2 sub-agent brief, encoding the sequence:
   - **Confirm findings:** dedup across the bundle; drop noise; for each kept finding emit a record with a
     **stable `dedup_key`** (`{node}|{type}|{normalized-observation-or-evidence-ref}`), `evidence_tier`,
     `tag`, evidence ref in `source`; fill `effort/impact/priority` only where evidence supports, else leave
     blank + `requires_human_review=true` (never invent Effort×Impact).
   - The **orchestrator add-items** these (dedup_key upsert → IDs assigned). Then **author the node MD**
     citing the now-existing **register IDs** (never restate data) + evidence refs; sections = What we
     learned / Evidence digest / Diagnosis (5 lenses, each value+rationale) / Open items (by register ID).
   - Finally `mark-consolidated`. State is authoritative; the MD is its render (§6).
   Include the ID-before-citation note and the coherence rule (cite IDs that exist; prose lenses match state).

## Out of scope
The orchestration that calls this per dirty node (T19). The `validate` coherence check itself (T35, S2).
Substantive gaps (T14).

## Tests (scratch `__t13__`; build fixtures: a node with evidence + a staged finding in an artifact + an
existing register row; remove all; do not commit)
1. `gather` for the node returns a bundle containing: the node lenses/evidence, the existing register row,
   and the staged candidate finding (assert all three present; `--json` parses).
2. **Re-consolidation idempotency:** `add-item` a confirmed finding with `dedup_key=K`; `add-item` again with
   the same `K` + a changed field → register has **one** row (updated), not two. (Proves consolidate re-runs
   don't duplicate.)
3. `mark-consolidated` then `is_diagnosis_dirty` is False; after a new `add-evidence` it is True again.
4. `consolidate_inputs.py` compiles + is read-only (state byte-identical before/after `gather`).
5. SKILL.md present; documents the confirm→IDs→author-MD order and the dedup_key/coherence rules.

## Done when
Helper + SKILL present; tests pass; report output + deviations.
