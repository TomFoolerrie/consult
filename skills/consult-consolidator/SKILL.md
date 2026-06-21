---
name: consult-consolidator
description: Stage 3 per-L2 consolidation sub-agent. For one diagnosis-dirty L2 node, dedups and confirms the staged candidate_findings into structured records (stable dedup_key, evidence_tier, no invented Effort×Impact) for the orchestrator to add-item, then authors the node MD (nodes/{l1}/{l2}.md) citing the now-existing register IDs + evidence refs — sections What we learned / Evidence digest / Diagnosis (5 lenses) / Open items by ID. Inputs come from `scripts/consolidate_inputs.py gather`. Enforces ID-before-citation and the structured↔prose coherence rule. Never writes state.json/register.json directly.
---

# Skill: Consult Consolidator — One Diagnosis-Dirty L2 to Confirmed Findings + Node MD

## Purpose

This is the **Stage 3 consolidation unit** (`consolidate_contract.md` §1). One
sub-agent works **one diagnosis-dirty L2 node** and does the *judgment* layer:

1. **Confirms** the staged `candidate_findings` (from classify artifacts) into a
   clean set of structured finding records — dedup, drop noise, attach a stable
   `dedup_key`, `evidence_tier`, `tag`, and evidence ref in `source`.
2. **Authors the node MD** — the human-readable per-L2 diagnosis narrative —
   citing **register IDs** and evidence refs.

Facts (lenses, evidence) were already merged deterministically in Stage 2b
(`classify_merge.py`). Consolidate turns the staged judgments into confirmed
register rows + prose. **State is authoritative; the MD is its render** (§6).

A node is **diagnosis-dirty** when `last_evidence_at > consolidated_at` (new
evidence since the last synthesis) — `state_machine.is_diagnosis_dirty`. Only
those nodes are (re)consolidated, so a node a human reviewed but that got no new
evidence is **not** clobbered by an unrelated `set-sop`/lens edit (§3, §6).

## When to Use

Use when the orchestrator finds a diagnosis-dirty L2 (e.g. via
`state_machine.py status --json` → `diagnosis_dirty_nodes`) and needs that node
consolidated: staged findings confirmed and the node MD authored.

**Do NOT use it for:** the orchestration that selects dirty nodes and applies
`add-item` / `mark-consolidated` (that is the command path, T19); the merge
(Stage 2b); substantive-gap analysis (`consult-gap-analyzer`, runs *after*
consolidate); the `validate` coherence check itself (T35).

## The write split (read this first — it is load-bearing)

- **The sub-agent authors the node MD directly** (node MDs are LLM-owned) and
  **returns the confirmed findings as structured data**. It does **not** call
  `add-item`, `mark-consolidated`, or write `state.json` / `register.json`.
- **The orchestrator** applies the returned findings via `state_machine.py
  add-item` (register writes stay on the command path) and stamps
  `mark-consolidated`.

This keeps register writes deterministic and auditable, exactly like the
classifier↔merge split in Stage 2.

## Inputs — use the gatherer

Get your complete, deterministic input bundle from the read-only helper (do not
forage across files yourself):

```bash
python3 scripts/consolidate_inputs.py gather \
  --engagement {E} --node {KEY} --json --excerpts
```

The bundle contains, for the one node:

- `node` — `coverage`, the 5 `lenses` (already set by the merge), the `evidence`
  list (`source`/`loc`/`tier`/`note`), `node_md` path, and the
  `last_evidence_at` / `consolidated_at` dirty markers.
- `register_rows` — the **existing active register rows already on this node**
  (so you upsert/extend rather than duplicate them).
- `candidate_findings` — the **staged findings** from every classify artifact
  whose `node_hit.node == KEY`. Each carries: `type`, `tag`, `confidence`,
  `observation`, `recommended_action`, `evidence_ref`, `evidence_tier`, a
  `proposed_dedup_key` (`{node}|{type}|{normalized-observation-or-ref}`), and the
  `source_artifact` / `source_doc` it came from.
- `evidence_excerpts` (with `--excerpts`) — the cited MD lines resolved from the
  immutable ingested docs, so you can quote/verify without re-reading files.

## Sequence — ID-before-citation (the gotcha this resolves)

`add-item` assigns the register ID, so findings must be **confirmed before** the
MD can cite them. The order is fixed (`consolidate_contract.md` §3):

```
1. dedup + confirm candidate_findings   → (you return them)
   → orchestrator add-items them          → IDs assigned (IMP-/GAP-NNNN)
2. author node MD citing the now-existing register IDs + evidence refs
3. orchestrator mark-consolidated         → clears the diagnosis-dirty signal
```

**You cannot cite a register ID in the MD before step 1 has assigned it.** If you
were to author the MD first, you would either invent IDs (coherence failure) or
restate the data inline (forbidden — §5). So: confirm findings → wait for the
orchestrator's assigned IDs → then author the MD against those IDs.

## Step 1 — Confirm the findings (the register-clean gate)

This is the gate that keeps the register clean: judgments, not raw signals.

1. **Dedup across the bundle.** Collapse near-duplicate `observation`s for this
   node (same finding seen in two docs) into **one** record; **merge their
   evidence refs**. Two findings are duplicates when they describe the same
   underlying issue, even if worded differently.
2. **Confirm vs drop.** Keep a finding only when it is **evidence-backed and
   substantive**. **Drop** vague/noise/non-actionable observations. A finding
   you judge **unmappable to this L2** is left for the unmapped path — do not
   force-fit it onto this node.
3. **Emit one record per kept finding** with:
   - **`dedup_key`** — a **stable** key, `{node}|{type}|{normalized-observation-
     or-evidence-ref}`. Start from the bundle's `proposed_dedup_key`; keep it
     deterministic so re-consolidation **upserts** the same row instead of
     minting a new `IMP-/GAP-NNNN`. This is the LLM-finding analogue of stable
     gap ids — **without it a 2nd evidence wave duplicates every finding**.
   - **`type`** — `improvement` or `gap`.
   - **`tag`** — the diagnostic **lens** for improvements; the **gap-tag** for
     gaps (reuse the controlled vocab).
   - **`source`** — the evidence ref (`path#L-L`); merge multiple refs if you
     deduped.
   - **`evidence_tier`** — carry the tier through from the bundle
     (`verbal`/`documentary`/`system_observed`). **Do not invent it.**
   - **`observation_pain_point`**, and `recommended_action` for improvements.
   - **`effort` / `impact_type` / `priority`** — fill **only where the evidence
     supports it**. Otherwise **leave blank and set
     `requires_human_review=true`**. **Never invent Effort×Impact** to look
     complete (`consolidate_contract.md` §4).

Return these records as structured data for the orchestrator. The orchestrator
runs, per record:

```bash
python3 scripts/state_machine.py add-item --engagement {E} \
  --type improvement --l1 {l1} --l2 {l2} \
  --field dedup_key='{node}|improvement|{norm}' \
  --field tag=automation \
  --field source='ingested/...md#L45' \
  --field evidence_tier=verbal \
  --field observation_pain_point='...' \
  --field recommended_action='...'
  # effort/impact_type/priority ONLY where evidence supports; else
  #   --field requires_human_review=true
```

`add-item` **upserts by `dedup_key`** (T02): a same-`dedup_key` add updates the
existing row in place — it does **not** create a second `IMP-/GAP-NNNN`. This is
why re-consolidation (a 2nd evidence wave) does not duplicate.

## Step 2 — Author the node MD (after IDs exist)

Now that the orchestrator has assigned register IDs, author
`engagements/{E}/nodes/{l1}/{l2}.md` (overwriting the stub/prior render).
Markdown + YAML frontmatter mirroring the node's key fields. Sections
(`consolidate_contract.md` §5):

- **What we learned** — the diagnosis narrative for this L2 in prose.
- **Evidence digest** — what the evidence shows, **cited via refs** (`path#L-L`);
  quote from the resolved excerpts.
- **Diagnosis (5 lenses)** — each lens **value + rationale**, tied to evidence.
  The asserted value **must equal the state value** (from the bundle's
  `node.lenses`).
- **Open items** — the improvements/gaps as a short list, **each citing its
  register ID** (the IDs the orchestrator just assigned) — **never restating the
  data**. Cite `IMP-0007`, do not re-type its observation/effort/impact.

## Coherence rule (enforced later by `validate`, §5)

The MD is a render of authoritative state, so it must cohere with state:

- **Cite IDs that exist.** Every register ID cited in the MD must be a real row
  (this is *why* step 1 precedes step 2 — IDs must already be assigned).
- **Prose lenses match state.** Every lens value asserted in prose must equal the
  state node's lens value. Do not assert a lens the state leaves null; do not
  contradict a set lens.
- **Never restate structured data.** Cite the register ID; the row is the source
  of truth, the MD points at it.

## Step 3 — mark consolidated (orchestrator)

After the MD is authored, the orchestrator stamps:

```bash
python3 scripts/state_machine.py mark-consolidated --engagement {E} --node {KEY}
```

This sets `consolidated_at = now`, clearing the diagnosis-dirty signal
(`last_evidence_at` no longer exceeds it). The change is logged to
`deliverables/review_log.md` (a hard output of every consolidate round, §6), so
any MD regeneration is visible, never silent.

## Re-consolidation & the prose-vs-state tension (§6)

When **new evidence** later arrives, the node goes dirty again and the MD is
**regenerated from state**. Human *substance* survives because review edits flow
back into **state** (Stage 6 ingestion); pure prose polish that was not a state
change may be regenerated. Confirmed findings are **not** re-duplicated because
they upsert by `dedup_key`. This is the deliberate consequence of "structured
state wins": the MD is a render of state, not a parallel source of truth.

## Non-negotiables

1. **ID-before-citation.** Confirm findings → orchestrator add-items → IDs → only
   then author the MD citing those IDs.
2. **Stable `dedup_key`** on every confirmed finding, so re-consolidation upserts
   (one row), never duplicates.
3. **Never invent Effort×Impact** — blank + `requires_human_review=true` when the
   evidence does not support it.
4. **Carry `evidence_tier` through** from the bundle; do not fabricate it.
5. **Coherence:** cite IDs that exist; prose lenses match state; never restate
   structured data.
6. **Write split:** author the MD; **return** findings — do not call `add-item` /
   `mark-consolidated` / write `state.json` / `register.json` yourself.
