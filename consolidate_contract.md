# CONSULT — Consolidate Contract (Stage 3)

> Status: **DESIGN DRAFT** (no code yet). See `spec.md` §5 Stage 3. Upstream:
> `classify_contract.md` (staged findings, merged lenses/evidence). This is where the
> **structured ↔ narrative coupling** is enacted.

## 1. What consolidate does

Per **dirty L2 node** (evidence newer than its last synthesis), one LLM sub-agent:
1. **Confirms staged findings** from the classify artifacts into the register (the gate that
   keeps the register clean — judgments, not raw signals).
2. **Authors the node MD** — the human-readable diagnosis narrative for that L2 — citing
   register IDs and evidence refs.

Facts (lenses, evidence) were already merged deterministically in Stage 2b; consolidate is the
*judgment* layer that turns them into confirmed findings + prose.

## 2. Inputs (one L2)

- The state node: lenses, coverage, evidence list (refs `path#L-L`).
- The register rows already on the node.
- The **staged `candidate_findings`** from every classify artifact whose `node_hit` is this L2.
- The current node MD (if any) and the resolved **evidence excerpts** (refs → ingested text).

## 3. Sequence (resolves the ID-before-citation gotcha)

Because `add-item` assigns the register ID, findings must be confirmed **before** the MD can
cite them:

```
1. dedup + confirm candidate_findings  → orchestrator add-items → IDs assigned
2. author node MD citing the now-existing register IDs + evidence refs
3. set node.consolidated_at = now      (clears the diagnosis-dirty signal)
```

**Diagnosis-dirty is evidence-specific:** a node needs (re)consolidation when
`node.last_evidence_at > node.consolidated_at` — i.e. *new evidence* since the last synthesis.
It is **not** keyed off the generic `node.updated`, because `set-sop`, lens edits, and
review-applied changes also bump `updated`; using that would re-synthesize (and risk prose
loss, §6) on changes that aren't new evidence. `add-evidence` stamps `last_evidence_at`;
consolidate stamps `consolidated_at`.

**Write split (keeps the discipline):** the sub-agent **authors the node MD directly**
(node MDs are LLM-owned) and **returns the confirmed findings as structured data**; the
**orchestrator** applies them via `add-item` (register writes stay on the command path). Step 2
runs after step 1 so IDs exist.

## 4. Findings confirmation policy

- **Dedup** candidate findings across docs by (node, near-duplicate observation); merge their
  evidence refs.
- **Confirm** a finding when it is evidence-backed and substantive; **drop** vague/noise.
- Fill `effort` / `impact_type` / `priority` / `recommended_action` where the evidence
  supports it; otherwise leave blank and set `requires_human_review=true` (don't invent
  Effort×Impact).
- Confirmed improvements/gaps get `add-item`'d with their evidence ref in `source`
  (`path#L-L`) and `tag` (lens for improvements, gap-tag for gaps).
- A finding the LLM judges *unmappable to this L2* is left for the unmapped path, not forced.

## 5. The node MD (what it must contain)

Markdown + YAML frontmatter mirroring the node's key fields. Sections (seeded stub already has
the skeleton): **What we learned**, **Evidence digest** (cited via refs), **Diagnosis (5
lenses)** (each lens value + rationale, tied to evidence), **Open items** (improvements/gaps as
a short list, **each citing its register ID — never restating the data**).

**Coherence (enforced by `validate`):** every register ID cited exists; every lens asserted in
prose matches the state value. Structured state is authoritative; the MD is its narrative.

## 6. Re-consolidation, human edits & the prose-vs-state tension

- Consolidate runs **only on diagnosis-dirty nodes** (`last_evidence_at > consolidated_at`).
  A node a human reviewed but that has had **no new evidence** is **not** re-consolidated — so
  review prose is not silently clobbered by an unrelated `set-sop` or lens edit (this is why the
  signal must be evidence-specific, §3).
- When new evidence *does* arrive and re-consolidation runs, the MD is **regenerated from
  state**. Human *substance* survives because review edits flow back into **state** (via Stage 6
  ingestion); pure prose polish that wasn't a state change may be regenerated. The
  **change log is a hard output of every consolidate and review round** —
  `engagements/{id}/deliverables/review_log.md`, appended (reviewer/agent, node, item,
  before→after) — so any regeneration is visible, never silent. This artifact is what makes the
  "structured wins" tradeoff defensible to a reviewer; it is required, not optional.
- This is the deliberate consequence of "structured state wins": the MD is a render of state,
  not a parallel source of truth.

## 7. Substantive gaps (Stage 4 LLM, sibling step)

`consult-gap-analyzer` operates on the **consolidated** node (MD + evidence) and adds gaps the
structural scan can't see — contradictions, thin/!single-source evidence, undocumented
controls, conflicting lens signals — as `type:gap` register rows (same confirm/add-item path).
It runs after consolidate (it needs the synthesis) and before drafting.

## 8. To validate during the vertical slice

- Is per-L2 the right consolidation unit, or does cross-L2 context (shared systems/roles)
  matter enough to batch by L1?
- Does the dedup/confirm policy keep the register clean without dropping real findings?
- Is "regenerate MD from state on dirty" acceptable to reviewers, or do we need prose-preserving
  merges (harder)? Exercise a re-consolidation after a review round in the slice.
- Are the seeded MD sections the right shape for the downstream drafter to consume?
