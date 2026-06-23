# CONSULT — Classify Artifact Contract (Stage 2)

> Status: **BUILT** (implemented by `scripts/validate_artifact.py` + `scripts/classify_merge.py`). This is the keystone contract: consolidate,
> gap-analyzer, and both drafters all bind to what classify produces. Companion schema:
> `schemas/classify_artifact.schema.json`. See `spec.md` §5 Stage 2.

## 1. What classify does

Stage 2 turns ingested documents into structured diagnosis. It has **two halves**, by the
"Python for determinism, LLM for judgment" principle:

- **2a — fan-out (LLM):** one sub-agent per ingested MD. Each *reads its one document* and a
  taxonomy slice, and emits a **per-doc artifact** (this contract). It writes the artifact to
  `engagements/{id}/classify/{hash}.artifact.json` (keyed by source hash, written atomically)
  and returns a one-line summary. **A
  sub-agent never touches `state.json` / `register.json`** — its artifact file is its output,
  not state.
- **2b — merge (Python):** a deterministic `classify_merge.py` reads *all* artifacts, resolves
  signals across documents, and applies the result to state via the existing commands
  (`add-evidence`, `set-lens`, and — for unmapped — the register). Determinism here is what
  makes Stage 2 **idempotent and auditable**: re-running re-resolves from the full artifact
  set rather than appending.

This split also draws the line between **facts** (evidence, lenses → auto-merged) and
**judgments** (candidate findings → *not* auto-added; gated by consolidate, Stage 3).

## 2. Four locked decisions

1. **Granularity = L2.** Classification targets L2 nodes (the unit of work, where lenses
   live). L3 activities are captured as `l3_hints` and in evidence detail — we do **not**
   diagnose at L3.
2. **Confidence + conflict.** Every lens signal and candidate finding carries a `confidence`
   (`high|med|low`). The merge sets a lens only when corroborated (see §5); genuine
   cross-doc disagreement is **never silently resolved** — it leaves the lens null and raises
   a contradiction gap, so the diagnosis is never confidently wrong.
3. **Evidence line-stability.** Evidence refs are `path#Lstart-Lend` into the ingested MD, so
   **ingest must produce stable line numbers** (Stage 1 constraint: do not reflow/renumber a
   document on re-ingest, or refs silently rot).
4. **Findings are staged, not auto-added.** Candidate improvements/gaps live in the artifacts;
   **consolidate** (Stage 3) dedups and confirms them into the register via `add-item`. The
   merge auto-applies only evidence and lenses (and unmapped). This keeps the register clean.

## 3. The per-doc artifact (shape)

One artifact per ingested document. Schema: `schemas/classify_artifact.schema.json`.

```jsonc
{
  "doc": {
    "source": "ingested/2026-03-01_close_walkthrough.md",  // the ingested MD this describes
    "doc_type": "transcript",                              // from the ingested YAML header
    "classified_at": "2026-06-21T00:00:00Z"
  },
  "node_hits": [
    {
      "node": "record-to-report.close",        // {l1}.{l2}; must exist in taxonomy.yaml
      "confidence": "high",                     // how sure this doc is about this L2 at all
      "rationale": "Walkthrough of the monthly close sequence.",
      "l3_hints": ["Sub-Ledger Close", "Accruals"],   // taxonomy L3 names touched (optional)
      "evidence": [
        { "ref": "ingested/2026-03-01_close_walkthrough.md#L42-48",
          "quote": "We close sub-ledgers first, then accruals — accruals are manual.",
          "note": "Close sequence + accrual pain." }
      ],
      "lens_signals": [
        { "lens": "process",    "value": "pain_high", "confidence": "high",
          "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L45", "rationale": "..." },
        { "lens": "automation", "value": "human",     "confidence": "high",
          "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L45", "rationale": "..." }
      ],
      "candidate_findings": [
        { "type": "gap", "tag": "not_documented", "confidence": "high",
          "observation": "No documented close checklist; order is tribal knowledge.",
          "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L48" },
        { "type": "improvement", "tag": "automation", "confidence": "med",
          "observation": "Accrual journals uploaded manually (2 analysts × 3 days).",
          "recommended_action": "Automate accrual journal upload.",
          "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L45" }
      ]
    }
  ],
  "unmapped": [
    { "summary": "FX hedging desk approval flow run out of the trading system.",
      "evidence_ref": "ingested/2026-03-01_close_walkthrough.md#L120-123",
      "nearest_node": "treasury.interest-rate-management",   // suggestion only — never auto-applied
      "reason": "No L2 covers a bespoke trading-desk approval workflow." }
  ]
}
```

Notes: `node` keys and `tag` values reuse the existing controlled vocab (taxonomy slugs;
lens enums; gap-tag / lens tags from the register). `nearest_node` on unmapped is a *hint
for the human*, never a destination the merge writes to.

> Schema limitation: the schema's `lens_signal.value` is a flat union of all lens values, so
> it cannot enforce *value-valid-for-the-named-lens* (e.g. `process: machine` passes
> structurally). That cross-field check is enforced at **merge time** by `classify_merge.py`
> (mirroring the register's soft-validation), and a `node` not in the taxonomy is rejected
> there too — the schema only guarantees shape.

## 4. Classifier sub-agent I/O

- **Inputs:** exactly one ingested MD (with stable line numbers) + a **taxonomy slice** —
  L1/L2 ids, names, and the optional per-L2 `description`/`keywords` enrichment (which is why
  that enrichment is worth doing alongside this). Optionally the L3 lists for `l3_hints`.
- **Output:** one artifact validating against the schema, written **atomically**
  (temp + rename) to `classify/{hash}.artifact.json` — keyed by the source **hash** (matching
  the ingest manifest), so the "classified set = artifacts vs manifest active hashes" derivation
  holds across re-ingest. A doc counts as classified only when its artifact exists **and
  schema-validates** (a truncated artifact must be retried, not silently dropped). The sub-agent
  returns a one-line summary.
- **Guarantees:** read-only w.r.t. state; cites real line ranges (no invented refs); never
  emits a `node` not in the taxonomy (anything that doesn't fit → `unmapped`); confidence is
  honest (don't assert `high` to be helpful).

## 5. Orchestrator merge rules (`classify_merge.py`, deterministic)

Reads every `classify/*.artifact.json` and resolves per node:

**Evidence** — for each `node_hit.evidence[].ref`, the merge first **checks the ref resolves**
to real lines in the cited (immutable) MD — a hallucinated `#L9999` is dropped/flagged here, not
discovered at the final gate as a phantom citation. Then `add-evidence` if that exact ref isn't
already on the node. **`add-evidence` must dedup by ref string** (a node never holds the same
ref twice) — this is a **required behavior** the merge's idempotency depends on, implemented in
the command itself (not in `classify_merge.py`), so every caller benefits. *Prerequisite build
task — `add-evidence` currently appends unconditionally.* Each add also stamps
`node.last_evidence_at` (the diagnosis-dirty signal, §orchestration).

**Lenses** — collect all `lens_signals` for each `(node, lens)` across artifacts:
1. Drop `low` confidence signals.
2. If the remaining signals **agree** (or one value dominates by corroboration count) and meet
   the threshold (**≥1 `high`, or ≥2 `med`**): `set-lens` to that value.
3. If they **disagree** (≥2 distinct values both pass threshold): **do not set the lens**
   (leave null) and emit a contradiction **gap** (`type:gap`, `tag:unconfirmed`,
   `source:classify-merge`, stable id `GAP-CONFLICT-{l1}-{l2}-{lens}`) citing the conflicting
   evidence refs. The human resolves it via `set-lens` during review. (Null also trips the
   structural-gap scan — double safety.) **Lens-value validity** (`process: machine` is
   invalid) is checked here before any write, agreeing with the register's soft-validation —
   a malformed signal is dropped/flagged, never written.

> **Gap-ID namespaces:** `classify_merge.py` owns `GAP-CONFLICT-*` (lens conflicts);
> `gap_report.py` owns `GAP-STRUCT-*` (structural). Distinct prefixes → the two generators
> never collide on the same row (resolves `spec.md` §8 open item).

**Candidate findings** — **not applied.** They remain in the artifacts for Stage 3 consolidate
to dedup/confirm into the register via `add-item`. (Judgments are LLM-gated.)

**Unmapped** — each entry becomes a register `type:unmapped` row (**null** `l1_cycle`/
`l2_process`, `owner:TBD`, `review_status:needs_review`), deduped by `evidence_ref`. Surfaced
in the gap report's Unmapped Triage. Auto-adding is safe — these are explicitly "needs triage."
*Prerequisite build task:* `type:unmapped` is now in the register schema, but `add-item`
rejects null-node rows — a **null-node add path** (`add-item --type unmapped` with no `--l1/--l2`)
must be built. Resolution lifecycle in §5b.

**Idempotency** — re-classifying a doc overwrites its artifact; re-running merge re-resolves
from the full set. Evidence deduped by ref; lenses recomputed from scratch each run;
contradiction gaps use stable ids (`GAP-CONFLICT-{l1}-{l2}-{lens}`) so they upsert rather than
duplicate.

### 5b. Unmapped resolution lifecycle

An `unmapped` row is only *closed* when its content is accounted for — "owned" is necessary but
not sufficient (an owned-but-unactioned row still means client reality was dropped). During
review (Stage 6) a human dispositions each row to one of:

- **Reclassify → an L2** — the human names the right `{l1}.{l2}`; the orchestrator re-opens
  classify/consolidate for that content (sets the node dirty) and **archives** the unmapped row
  (`record_status:archived`, noting the destination). The reclassification is *human* — the
  pipeline never auto-buckets.
- **Convert → improvement/gap** — the content is in-scope but is itself a finding; it becomes a
  normal register row and the unmapped row is archived.
- **Out of scope** — explicitly accepted as not part of this engagement; archived with a reason.

The **DoD gate** is "every unmapped row *dispositioned*" (reclassified/converted/out-of-scope),
not merely assigned an owner. Open (un-dispositioned) unmapped rows block `final`.

## 6. Worked example (end to end)

**Ingested excerpt** — `ingested/2026-03-01_close_walkthrough.md`:
```
L42  We close the sub-ledgers first, then accruals.
L45  Accruals are the painful part — all manual journal uploads, two analysts, three days.
L48  There's no documented checklist; people just know the order.
...
L120 Separately, the FX hedging desk has its own approval flow finance signs off on,
L123 but that's run out of the trading system, not really part of close.
```

**Artifact** → the JSON in §3 above (one `node_hit` for `record-to-report.close`, one
`unmapped` entry).

**Merge actions (deterministic):**
```bash
# evidence
state_machine.py add-evidence --engagement E --node record-to-report.close \
  --source ingested/2026-03-01_close_walkthrough.md --loc L42-48 --note "Close sequence + accrual pain."
# lenses (both high-confidence, no conflict → set)
state_machine.py set-lens --engagement E --node record-to-report.close --lens process    --value pain_high
state_machine.py set-lens --engagement E --node record-to-report.close --lens automation --value human
# unmapped → register (null-node type:unmapped, owner TBD)
#   (via the planned null-node add path)
```

**Not done by merge:** the two `candidate_findings` (the checklist gap, the accrual-automation
improvement) stay staged; **consolidate** confirms them into the register and writes the
`record-to-report.close` node MD narrative citing their register ids.

## 7. To validate during the vertical slice

- Does the `(node, lens)` corroboration/threshold policy feel right on real transcripts, or do
  we need per-lens thresholds?
- Is `add-evidence` ref-dedup enough, or do we want a content hash?
- Confirm ingest line-number stability holds across a re-ingest.
- Does staging findings (vs auto-add) create too much work in consolidate, or is the cleaner
  register worth it?
- Exercise one genuine cross-doc lens **conflict** and one **unmapped** item — these are the
  paths that protect against confidently-wrong output.
