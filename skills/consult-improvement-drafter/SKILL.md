---
name: consult-improvement-drafter
description: Draft the per-L1 Process Improvement Opportunities deliverable (Stream B) from the engagement register's type:improvement rows grouped by lens, then write the deliverable status back to state.
---

# Improvement Drafter Skill (Stream B, per L1)

## Purpose

Draft the **Process Improvement Opportunities** deliverable for one **L1 business
cycle**, sourced from the engagement register's `type:improvement` rows **grouped by
lens**, and write the deliverable status back to engagement state.

This is the Stream-B parallel to `consult-drafter`'s SOP draft (Stream A). The review
unit is **one document per L1 cycle**. See `generation_review_contract.md` §1 (5B) and
spec §5 Stage 5B + the Improvement DoD.

Output: `engagements/{id}/deliverables/improvements/{l1}.md` — each item rendered
**Finding → Recommendation → Effort × Impact → Owner**, traceable to its register `id`
and evidence ref.

## Use This Skill When

Use this skill when, inside the CONSULT pipeline, the orchestrator asks to draft the
improvement / opportunities deliverable for an L1 cycle (Stage 5B). It runs as a per-L1
sub-agent brief.

Do **not** use this skill for:

- The SOP / desktop-procedure deliverable — that is `consult-drafter` (Stream A, 5A).
- The synthesis / prioritization roll-up across L1s (T17, out of scope).
- Word rendering (`consult-docx-builder`, Stage 6, out of scope).

## Source From Engagement State (do not forage raw docs)

Source everything from engagement state/register via the read-only gatherer. Do **not**
read raw transcripts or ingested docs directly.

### Step A — Gather the L1 bundle

Run the read-only helper (built in T15) to assemble the per-L1 bundle:

```bash
python3 scripts/draft_inputs.py gather --engagement {id} --l1 {l1} --json
```

`{l1}` is the L1 cycle id, e.g. `record-to-report`. `--json` emits the machine bundle.
`draft_inputs.py` is **read-only** — it never writes state, register, or deliverables.
Do not edit it; rely only on it. This skill adds no helper script of its own.

The bundle carries, for every L2 node under the L1:

- `node_md` (path) and `node_md_content` — the per-L2 narrative for context.
- `lenses` (the 5 diagnostic lenses) and `coverage`.
- `evidence` — node-level evidence entries.
- `appendices` — the node's register rows pre-bucketed (per L2), plus the L1-level
  `appendices` totals.

The bundle also exposes `l1`, `l1_name`, and the per-row `row_view` fields below.

### Step B — Select the improvement rows

From the bundle, take every **active** register row with `type == improvement`. These
arrive pre-bucketed in the gatherer's `appendices` (improvements with the process lens
land in Appendix **A** as pain points; other improvements in Appendix **B**) — but for
this deliverable you do **not** group by appendix. Take improvement rows from **both**
appendix A and appendix B across all L2 nodes under the L1, then regroup them **by lens**
per Step C. (Inactive rows — archived/deleted/removed statuses — are already filtered out
by the gatherer.)

Each improvement row carries these `row_view` fields:

- `id` — the register id (e.g. `IMP-0007`); the traceability anchor.
- `tag` — the **lens** (`process` / `automation` / `operating_model` / `capability`).
- `l3_activity` — the activity the finding sits on.
- `observation_pain_point`, `root_cause` — the Finding inputs.
- `recommended_action` — the Recommendation input.
- `effort`, `impact_type`, `estimated_impact_benefit` — the Effort × Impact inputs.
- `owner` — the Owner.
- `evidence_ref` (a `path#Lstart-Lend` ref) and `evidence_tier`
  (`verbal` / `documentary` / `system_observed`).

### Step C — Group by lens

Group the improvement rows **by lens** using each row's `tag`, into these four lens
buckets in this order:

1. `process`
2. `automation`
3. `operating_model`
4. `capability`

Render one section per lens that has rows. A row whose `tag` is missing or is not one of
the four lenses goes in an **"Unclassified lens"** section at the end — surface it; do not
guess a lens for it. State the lens scores from the bundle's per-node `lenses` as context
where useful (do not invent scores).

### Step D — Author the deliverable

Write `engagements/{id}/deliverables/improvements/{l1}.md`. For **each improvement item**, render the
Stream-B DoD shape:

- **Finding** — from `observation_pain_point` (+ `root_cause` if present). What is true today.
- **Recommendation** — from `recommended_action`. What to change.
- **Effort × Impact** — from `effort` × (`impact_type` / `estimated_impact_benefit`).
  Render as **`directional`** unless a **quantified** source backs the value (a number /
  measured benefit in the register). **Never invent a number.** A bare qualitative
  label with no quantified backing is still `directional`.
- **Owner** — from `owner`.
- **Traceability** — cite the register `id` and the `evidence_ref` inline so a reviewer
  can trace the item back to source. Note the `evidence_tier`.

**Missing fields are surfaced, not invented.** If `effort`, `impact_type` /
`estimated_impact_benefit`, or `owner` is absent, render the field as **needs input**
(e.g. `Owner: needs input — confirm with process owner`) rather than fabricating a value.
Do not invent systems, owners, effort sizings, or benefit numbers.

Suggested document shape:

```markdown
# Process Improvement Opportunities — {l1_name}

> Engagement: {id} · L1 cycle: {l1} · Source: register type:improvement rows
> (via draft_inputs.py gather), grouped by lens. Effort × Impact is directional
> unless a quantified source backs it.

## Process

### IMP-0007 — {short title}
- **Finding:** {observation_pain_point} ({root_cause})
- **Recommendation:** {recommended_action}
- **Effort × Impact:** directional   <!-- or a quantified value when the register backs it -->
- **Owner:** {owner or "needs input — confirm with process owner"}
- **Traceability:** register IMP-0007 · evidence {path#L10-L18} (tier: documentary)

## Automation
...

## Operating Model
...

## Capability
...

## Unclassified lens (needs input)
- {id}: lens tag missing — route for lens classification.
```

Keep it neutral, current-state consulting language. Each item must be traceable to a
register id and an evidence ref.

### Step E — Write back the improvement status

After writing the deliverable, record the deliverable state via the state machine
(`set-improvement`, from T03). Apply it to **each L2 node** under the L1 that the doc
covers (the L1-Level deliverable spans them):

```bash
python3 scripts/state_machine.py set-improvement --engagement {id} --node {l2_key} \
  --status draft --path engagements/{id}/deliverables/improvements/{l1}.md --bump-rev
```

- `{l2_key}` is the node key `{l1}.{l2}` (e.g. `record-to-report.close`).
- `--status` choices: `not_started`, `drafting`, `draft`, `in_review`, `revised`, `final`.
  Use `draft` for a first draft.
- `--bump-rev` increments `improvement.rev` by 1 (first draft → rev 1).
- `set-improvement` updates the node's `improvement.{status,path,rev}` block.

Confirm the write-back with `get-node`:

```bash
python3 scripts/state_machine.py get-node --engagement {id} --node {l2_key} --json
```

The node's `improvement.status` should read `draft`, `improvement.path` the deliverable
path, and `improvement.rev` the bumped value.

Do **not** invent flags. The only `set-improvement` flags are
`--engagement`, `--node`, `--status`, `--path`, `--bump-rev`, `--bump-rendered-rev`,
`--bump-reviewed-rev`. The only `draft_inputs.py gather` flags are `--engagement`,
`--l1`, `--json`.

## Definition of Done

- The bundle came from `draft_inputs.py gather` (read-only); no raw-doc foraging.
- `engagements/{id}/deliverables/improvements/{l1}.md` exists, with improvement items **grouped by lens**.
- Each item is **Finding → Recommendation → Effort × Impact → Owner**, traceable to its
  register `id` + `evidence_ref`.
- Effort × Impact is `directional` unless a quantified source backs it; no invented numbers.
- Items missing Effort / Impact / Owner are surfaced as **needs input**, not fabricated.
- `improvement.{status,path,rev}` is written back per L2 node via `set-improvement`, and
  `get-node` reflects it.
