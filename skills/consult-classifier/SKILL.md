---
name: consult-classifier
description: >-
  Stage 2 fan-out (2a) — a per-doc classifier sub-agent. Reads exactly one ingested MD
  (engagements/{id}/ingested/*.md) plus a taxonomy slice, and emits one per-doc artifact
  validating against schemas/classify_artifact.schema.json: node_hits (confidence, l3_hints,
  evidence refs, lens_signals, candidate_findings) plus unmapped. Writes the artifact
  atomically to classify/{hash}.artifact.json and returns a one-line summary. Read-only
  w.r.t. state — never touches state.json / register.json.
---

# Skill: Consult Classifier — One Ingested Doc to One Artifact

## Purpose

This is the **Stage 2 fan-out unit** (`classify_contract.md` §2a). One sub-agent
reads **one** ingested Markdown document and a **taxonomy slice**, then emits a
single **per-doc artifact** describing what that document says about the L2
nodes it touches. The artifact is the sub-agent's only output.

The split between this (LLM judgment) and the deterministic **merge** (Stage 2b,
`classify_merge.py`, T12) is load-bearing: this sub-agent proposes; the merge
disposes. So this sub-agent:

- **Never writes state.** It does not call `state_machine.py` and never touches
  `state.json` or `register.json`. Its artifact file *is* its output, not state.
- Emits **facts** (evidence, lens signals) and **judgments** (candidate
  findings) separately. The merge auto-applies evidence + lenses + unmapped;
  candidate findings stay staged for Stage 3 consolidate.

## When to Use

Use when the orchestrator fans out classification over the ingested set: invoke
once per ingested MD that needs an artifact (a doc counts as classified only
when its artifact exists **and** schema-validates).

**Do NOT use it for:** the merge / applying to state (Stage 2b, T12);
re-cleaning or editing ingested MDs (immutable); diagnosing at L3 (granularity
is **L2** — L3 is captured only as `l3_hints`).

## Inputs

1. **Exactly one ingested MD** at `engagements/{id}/ingested/{name}.md`, with a
   YAML header (`source_hash`, `doc_type`, …) and **stable line numbers**. Line
   numbers are immutable (Stage 1 guarantee), which is what makes evidence refs
   durable.
2. **A taxonomy slice** — L1/L2 ids and names (and optional per-L2
   `description`/`keywords` enrichment), optionally L3 lists for `l3_hints`.
   Classify **only** to nodes that exist in this slice / `reference/taxonomy.yaml`.

## Output: the per-doc artifact

One JSON artifact validating against **`schemas/classify_artifact.schema.json`**.
Shape (full contract: `classify_contract.md` §3):

- `doc` — `source` (the ingested MD path, e.g. `ingested/{name}.md`),
  `doc_type` (from the header), `classified_at` (ISO 8601).
- `node_hits[]` — one per L2 the doc touches:
  - `node` — `{l1_id}.{l2_id}`, **must exist in the taxonomy**.
  - `confidence` — `high|med|low`: how sure the doc is about this L2 at all.
  - `rationale`, optional `l3_hints[]` (taxonomy L3 names).
  - `evidence[]` — `{ ref: "path#Lstart-Lend", quote, note }`. The `ref` must
    cite **real lines** in the cited MD.
  - `lens_signals[]` — `{ lens, value, confidence, evidence_ref, rationale }`.
    The `value` must be **valid for the named lens** (see table below).
  - `candidate_findings[]` — `{ type: improvement|gap, tag, confidence,
    observation, recommended_action?, evidence_ref }`. The `tag` doubles as a
    proposed `dedup_key` seed for consolidate; pick a stable lens/gap-tag slug.
    **Type sharply — don't default to `gap`:** `improvement` = an actionable
    process-change opportunity (automate / centralize / standardize / build
    capability; signalled by pain points, "manual/re-keyed", "decentralized",
    missing capability) — `tag` = the lens, give a `recommended_action`.
    `gap` = missing info/documentation/evidence to fill. A single observation
    can yield **both** (e.g. an undocumented manual control → an `automation`
    improvement *and* a `control_not_evidenced` gap).
- `unmapped[]` — `{ summary, evidence_ref, nearest_node?, reason }` for content
  that fits **no** L2. `nearest_node` is a hint for the human, never a
  destination the merge writes to.

### Valid lens values (value MUST match its lens)

| lens              | allowed values                                   |
|-------------------|--------------------------------------------------|
| `current_state`   | `present`, `absent`                              |
| `process`         | `pain_high`, `pain_med`, `pain_low`, `strength`  |
| `automation`      | `machine`, `mixed`, `human`                      |
| `capability`      | `new`, `existing`                                |
| `operating_model` | `central`, `mixed`, `local`                      |

The schema's `value` is a flat union of all of these, so `process: machine`
passes the schema but is **invalid** — the validator and the merge both reject
it. Emit only value-valid-for-lens signals.

## Honesty rules (`classify_contract.md` §4 — non-negotiable)

1. **Real refs only.** Every `ref` / `evidence_ref` cites a line range that
   actually exists in the cited ingested MD. Never invent `#L9999`. A
   hallucinated ref is the failure mode this whole pipeline guards against.
2. **Never emit a node not in the taxonomy.** Anything that fits no L2 goes to
   `unmapped` — do not force-fit it onto the nearest node.
3. **Honest confidence.** Do not assert `high` to be helpful. `high` means the
   doc clearly establishes it; use `med`/`low` when the doc is suggestive or
   ambiguous. `low`-confidence lens signals are dropped by the merge anyway.
4. **Read-only w.r.t. state.** Never write `state.json` / `register.json`.

## Writing the artifact (atomic)

Write to `engagements/{id}/classify/{hash}.artifact.json`, where `{hash}` is the
source hash from the ingested MD's header (matching the ingest manifest). Write
**atomically** — write to a temp file in the same dir, then `os.rename` over the
target — so a truncated artifact can never be mistaken for a complete one. Then
return a **one-line summary** (e.g. node count, unmapped count).

Before returning, the artifact must **schema-validate and pass the cross-field
checks**. Self-check with:

```bash
python3 scripts/validate_artifact.py validate \
  --artifact engagements/{id}/classify/{hash}.artifact.json --engagement {id}
```

This runs all four checks (schema; node exists; lens value valid for its lens;
every evidence ref resolves to real lines). Exit 0 + `ok` means the artifact is
trustworthy for the merge. If it fails, fix and rewrite — never leave a partial
artifact behind.

## Worked example (mirrors `classify_contract.md` §6)

**Ingested excerpt** — `ingested/2026-03-01_close_walkthrough.md`:

```
L42  We close the sub-ledgers first, then accruals.
L45  Accruals are the painful part — all manual journal uploads, two analysts, three days.
L48  There's no documented checklist; people just know the order.
...
L120 Separately, the FX hedging desk has its own approval flow finance signs off on,
L123 but that's run out of the trading system, not really part of close.
```

**Artifact** (`classify/{hash}.artifact.json`):

```json
{
  "doc": {
    "source": "ingested/2026-03-01_close_walkthrough.md",
    "doc_type": "transcript",
    "classified_at": "2026-06-21T00:00:00Z"
  },
  "node_hits": [
    {
      "node": "record-to-report.close",
      "confidence": "high",
      "rationale": "Walkthrough of the monthly close sequence.",
      "l3_hints": ["Sub-Ledger Close", "Accruals"],
      "evidence": [
        { "ref": "ingested/2026-03-01_close_walkthrough.md#L42-48",
          "quote": "We close sub-ledgers first, then accruals — accruals are manual.",
          "note": "Close sequence + accrual pain." }
      ],
      "lens_signals": [
        { "lens": "process", "value": "pain_high", "confidence": "high",
          "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L45",
          "rationale": "Manual accrual uploads called out as the painful part." },
        { "lens": "automation", "value": "human", "confidence": "high",
          "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L45",
          "rationale": "All accrual journals uploaded manually." }
      ],
      "candidate_findings": [
        { "type": "gap", "tag": "not_documented", "confidence": "high",
          "observation": "No documented close checklist; order is tribal knowledge.",
          "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L48" },
        { "type": "improvement", "tag": "automation", "confidence": "med",
          "observation": "Accrual journals uploaded manually (2 analysts x 3 days).",
          "recommended_action": "Automate accrual journal upload.",
          "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L45" }
      ]
    }
  ],
  "unmapped": [
    { "summary": "FX hedging desk approval flow run out of the trading system.",
      "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L120-123",
      "nearest_node": "treasury.interest-rate-management",
      "reason": "No L2 covers a bespoke trading-desk approval workflow." }
  ]
}
```

**What the merge (not this sub-agent) does with it:** `add-evidence` for the
node ref; `set-lens` for `process=pain_high` and `automation=human` (both
high-confidence, no conflict); the unmapped entry becomes a null-node
`type:unmapped` register row. The two `candidate_findings` stay **staged** for
Stage 3 consolidate. This sub-agent does **none** of that — it only writes the
artifact above.
