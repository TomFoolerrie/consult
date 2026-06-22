---
name: consult-synthesizer
description: Stage 5C synthesis sub-agent (the decision layer). From the cross-cutting aggregation (all active improvements with effort/priority/phase/lens, node coverage + lens scores across L1s, an effort×impact bucketing, and a per-L1 lens roll-up), authors the lead deliverables/synthesis.md — Executive summary, Effort×Impact prioritization (quick-wins / 0–6mo / 6–18mo roadmap sequenced by register fields), and per-L1 current→future operating model from lens scores — and lifts cross-cutting findings into type:theme register rows (related_nodes spanning multiple {l1}.{l2} keys, stable dedup_key). Inputs come from scripts/synthesis_inputs.py gather. Cites register IDs; directional only, never invents numbers.
---

# Skill: Consult Synthesizer — Cross-Cutting Streams to a Point of View

## Purpose

This is the **Stage 5C synthesis unit** (the decision layer). Where the drafter
works one SOP per L1 and the consolidator works one node MD per L2, the
synthesizer reads the **whole engagement** and turns the bottom-up streams into a
**point of view**:

1. **Authors the lead `deliverables/synthesis.md`** — Executive summary, an
   Effort × Impact prioritized roadmap (quick-wins / 0–6mo / 6–18mo), and a
   per-L1 current → future operating-model read from the lens scores.
2. **Lifts cross-cutting findings** — issues the per-L2 grid would shred (the
   same problem recurring across many nodes) — into **`type:theme`** register
   rows whose `related_nodes` span the multiple `{l1}.{l2}` nodes they touch,
   each with a stable `dedup_key`.

The per-L2 SOP/improvement streams (T15/T16) and the Word render (T18) are out of
scope. This skill produces the synthesis MD + the theme rows only.

## When to Use

Use when the bottom-up streams are populated (improvements carry `effort` /
`priority`, nodes carry lens scores) and the engagement needs its lead
synthesis: a prioritized roadmap and a current→future story, plus the
cross-cutting themes a node-by-node view cannot express.

**Do NOT use it for:** the per-L1 SOPs or per-L2 improvement docs (the drafter
streams); the Word render (T18); inventing effort/impact/priority values that the
register does not already hold (see Non-negotiables).

## The write split (read this first — it is load-bearing)

- **The sub-agent authors `synthesis.md` directly** (deliverable MDs are
  LLM-owned) and **lifts the cross-cutting theme rows** into the register via the
  documented `add-item --type theme` command path below.
- The synthesis is **directional**: it sequences and narrates what the register
  and lens scores already say. It **never invents numbers** (no fabricated ROI,
  headcount, or savings) and **cites register IDs** for every claim.

## Inputs — use the gatherer

Get your complete, deterministic, cross-cutting bundle from the read-only helper
(do not forage across files yourself):

```bash
python3 scripts/synthesis_inputs.py gather --engagement {E} --json
```

`synthesis_inputs.py` is **read-only** — it never writes state, register, or
deliverables. The bundle contains:

- `totals` — L1 / node / active-improvement counts.
- `improvements` — **every active `type:improvement` row across all L1s**, each
  with `effort`, `priority`, derived `impact` (p1→high, p2→med, p3→low),
  `phase`, lens `tag`, `impact_type`, `observation_pain_point`,
  `recommended_action`, its `node` key, and its `bucket`.
- `effort_impact` — the **effort × impact bucketing**: `labels`, `buckets`
  (register IDs grouped per bucket), and `counts`. Buckets: `quick_win`
  (low effort / high impact), `major_project`, `incremental`, `fill_in`,
  `thankless`, and `unranked` (rows missing effort or priority).
- `per_l1` — the **per-L1 lens roll-up**: per L1, the `coverage_counts`, a
  `lens_rollup` (value→count for each of the 5 lenses across the L1's nodes),
  `future_state_nodes` (nodes where `capability:new` — the **future-state
  signal**), and `improvement_buckets`.
- `node_coverage` — per node: `coverage`, the 5 `lenses`, and improvement count.

The bucketing and roll-up are **pre-derived** for you; do not re-compute them.
Impact is read from the register `priority` field (the deliberate prioritization
signal), not invented.

## Step 1 — Author `deliverables/synthesis.md`

Write `engagements/{E}/deliverables/synthesis.md` (the `synthesis_path` in the
bundle) with these sections, in order. Markdown + a short YAML frontmatter
(engagement id, date). **Cite register IDs (IMP-NNNN / THM-NNNN) for every claim;
directional only.**

### Section 1 — Executive summary

The point of view in prose: the few cross-cutting themes that define the
engagement (drawn from the `type:theme` rows you lift in Step 2), the headline
quick-wins, and the current→future arc. Reference theme/improvement IDs; do not
restate their data.

### Section 2 — Effort × Impact prioritization (the roadmap)

Sequence the roadmap **by the register fields** (`effort` / `priority` →
`bucket`), **not by lens**. Use the `effort_impact` buckets:

| Roadmap horizon | Source | Sequenced by |
| --- | --- | --- |
| **Quick wins** | `effort_impact.buckets.quick_win` (low effort / high impact) | take first |
| **0–6 months** | `major_project` + `incremental` at `priority=p1` (and `phase` if set) | priority, then effort |
| **6–18 months** | remaining `major_project` / `incremental` / `fill_in` | priority, then effort |

List each item by its **register ID** with its node, effort, and impact. Flag any
`unranked` item (missing `effort` or `priority`) as **needing human review** —
**do not invent** the missing field to place it on the roadmap. Honor a row's
`phase` when present as the explicit sequencing hint.

### Section 3 — Per-L1 current → future operating model

For each L1 in `per_l1`, read the **current state** from the `lens_rollup` /
`coverage_counts`, and the **future-state signal** from `future_state_nodes`
(the `capability:new` nodes) plus the `automation` / `operating_model` lens
tallies. Tell the current → future story per L1 directionally: where the cycle is
manual/local/pain-heavy today and where `capability:new` points the future
operating model. Cite the node keys and the IMP-/THM- IDs that drive each move.

## Step 2 — Lift cross-cutting findings into `type:theme` rows

A finding the per-L2 grid would **shred** — the same root issue recurring across
many nodes (e.g. "manual spreadsheet close steps across record-to-report") — is a
**theme**. Lift it into a `type:theme` register row whose `related_nodes` lists
**every `{l1}.{l2}` node it spans**, with a **stable `dedup_key`** so re-running
synthesis upserts the one row instead of minting duplicates.

### The invocation (related_nodes lands as a JSON array)

`related_nodes` is an **array** of `{l1}.{l2}` node keys (see
`schemas/item_register.schema.json` — `related_nodes: array, items pattern
^[a-z0-9-]+\.[a-z0-9-]+$`). Use `add-item --type theme` with **`--field-json`**
(values parsed as JSON, so arrays land as arrays). Theme is a **null-node** type:
do **not** pass `--l1/--l2`.

```bash
python3 scripts/state_machine.py add-item --engagement {E} --type theme \
  --field-json related_nodes='["record-to-report.close","record-to-report.consolidation","procure-to-pay.procurement"]' \
  --field dedup_key="theme|manual-spreadsheet-close" \
  --field observation_pain_point="Core close steps run in manual spreadsheets across cycles" \
  --field recommended_action="Standardize and automate the cross-cycle close checklist" \
  --field effort=med --field priority=p1
```

- `--field-json` stores `related_nodes` as a real **JSON array** (schema-validates
  against the `related_nodes` array type); plain `--field` would store a scalar
  string. Scalar fields still use `--field KEY=VALUE`.
- `dedup_key` makes the row **idempotent**: re-running synthesis with the same
  `dedup_key` **upserts the one row** — it does not mint a second THM-NNNN. The
  `THM-` id is auto-assigned.
- `add-item` auto-assigns the `THM-NNNN` id (pass `--id` only to target a
  specific existing row).
- Validate after lifting:

```bash
python3 skills/consult-improvement-log/scripts/improvement_log.py validate \
  --json engagements/{E}/register.json --schema schemas/item_register.schema.json
```

After lifting theme rows, run `state_machine.py sync --engagement {E}` so node
counts stay consistent (theme rows do not roll into improvement/gap/screenshot
buckets, but sync keeps the register↔state link clean).

## Non-negotiables

1. **Directional only — never invent numbers.** No fabricated ROI / savings /
   headcount. Every claim cites a register ID (IMP-/THM-) or a node key.
2. **Sequence the roadmap by register fields** (`effort` / `priority` / `phase` →
   bucket), **not** by lens. Lenses drive the current→future narrative, not the
   roadmap order.
3. **`unranked` items need human review** — never invent the missing
   `effort`/`priority` to place an item on the roadmap.
4. **`related_nodes` is an array** of `{l1}.{l2}` keys, passed via the
   `upsert-json --records-json` array literal above (not a scalar string).
5. **Stable `dedup_key`** on every theme row, so re-running synthesis upserts one
   row, never duplicates.
6. **Read the gatherer, don't forage.** The bucketing and lens roll-up are
   pre-derived by `synthesis_inputs.py gather`; do not re-compute them from raw
   files.
