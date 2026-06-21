---
engagement: r2r-demo
date: 2026-06-21
stage: synthesis
---

# Synthesis — r2r-demo

**Demo Manufacturing Co | Record-to-Report Focus**

---

## 1. Executive Summary

This engagement's diagnostic work is currently concentrated in two Record-to-Report nodes — `record-to-report.close` and `record-to-report.consolidation` — and one Risk, Policy & Controls node — `risk-policy-controls.internal-controls`. Thirty-four of thirty-seven nodes across the remaining six L1 cycles carry zero coverage, so the findings below represent an early-stage read on a single functional strand, not a whole-enterprise picture.

Within that strand, the finance function shows a meaningful split between what works and what is fragile.

**Strengths identified in the evidence:**

- Account reconciliations run on a standardized tool with clear ownership per regional controller, described by the senior accountant as "one of our stronger areas" (`ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L30-31`).
- Intercompany eliminations are fully automated within the consolidation tool — a notably mature automation posture for that sub-step (`record-to-report.consolidation`, automation: mixed; GAP-0004 calls out the manual residual against this otherwise machine-driven step).
- The consolidation function itself is centralized at corporate with a single team holding all elimination, topside, and review authority — a clean operating-model design that avoids fragmented consolidation judgment (`record-to-report.consolidation`, operating_model: central).

**Weaknesses (the fragile half):**

- Monthly accruals are entirely manual: built in spreadsheets and re-keyed into the ERP each cycle. The controller identified this as the primary close pain point and the most frequent source of late adjustments (GAP-0001; `record-to-report.close`, automation: human).
- The dual-review control for reconciliations above $50K operates in practice but is documented nowhere — no policy, no system configuration, entirely oral/tribal. This theme recurs across both `record-to-report.close` (GAP-0002) and `risk-policy-controls.internal-controls` (GAP-0005), and is lifted as a cross-cutting theme (THM-0001, see below).
- Recon sign-off is decentralized across regional controllers with no described central oversight layer — the quality of that local control regime is unassessed (GAP-0003).
- Manual topside entries at corporate sit alongside an otherwise automated elimination process, creating a maturity inconsistency within the same consolidation step (GAP-0004).

**The three to five moves that matter:**

1. Automate the accrual workflow — eliminate the spreadsheet-to-ERP re-key loop (GAP-0001).
2. Document and system-enforce the dual-review control — verbal-only controls carry audit and SOX risk and cannot be independently evidenced (THM-0001 / GAP-0002 / GAP-0005).
3. Assess topside entry systemization — the automation gap inside an otherwise machine-driven consolidation step is the most actionable incremental gain in that L2 (GAP-0004).
4. Resolve the `process` lens conflict on `record-to-report.close` — the cross-document tension between pain-level and strength characterizations of the recon process must be adjudicated by a human reviewer before the node can be fully diagnosed (GAP-CONFLICT-record-to-report-close-process).
5. Expand coverage — thirty-four nodes with zero coverage represent the engagement's largest blind spot; the synthesis below is directional but incomplete until broader discovery occurs.

---

## 2. Effort x Impact Prioritization

### Note on the register state

The register currently holds **zero `type:improvement` rows**. All substantive findings are registered as `type:gap`. The effort-impact bucketing in the synthesis inputs is therefore empty across all buckets (quick_win: 0, major_project: 0, incremental: 0, fill_in: 0, thankless: 0, unranked: 0). The quantified prioritization that would normally sequence this section from register fields cannot be produced from the current state.

The roadmap below is derived from the gap observations (GAP-0001 through GAP-0005 and THM-0001) and is **directional only**. Effort and priority assignments are qualitative reads from the gap text, not register-field values. These should be confirmed and promoted to `type:improvement` rows (with explicit `effort` and `priority` fields) before the roadmap is treated as authoritative.

### Candidate roadmap (directional)

**Quick wins (low effort / high impact — candidate)**

| Candidate | Source | Rationale |
|---|---|---|
| Document the dual-review threshold in a controls policy | GAP-0002, GAP-0005, THM-0001 | Policy authorship is a writing task with no system dependency; removes audit risk immediately |

**0–6 months**

| Candidate | Source | Rationale |
|---|---|---|
| Configure the reconciliation tool to enforce the $50K dual-review threshold systematically | GAP-0005 (recommended_action) | Converts an oral control to a system-observed one; tool is already in use, so configuration scope is bounded |
| Resolve `record-to-report.close` process lens conflict | GAP-CONFLICT-record-to-report-close-process | Blocks full close diagnosis and any SOP for the node |

**6–18 months**

| Candidate | Source | Rationale |
|---|---|---|
| Automate the accrual journal upload / ERP-native accrual workflow | GAP-0001 (recommended_action) | Largest stated pain point and leading cause of late adjustments; ERP configuration or accrual-tool integration likely required |
| Assess and systemize topside entry types in the consolidation tool | GAP-0004 (recommended_action) | Medium effort; requires volume/type analysis before design; natural follow-on once IC elimination maturity is leveraged |

**Needs human review before placement**

All five GAP rows and the THM-0001 theme require promotion to `type:improvement` with explicit `effort` and `priority` values before they can be placed on a calibrated roadmap. Until then, the horizon assignments above should be treated as directional sequencing, not commitments.

---

## 3. Per-L1 Current to Future Operating Model

Only two L1 cycles carry covered nodes. The remaining five (fpa, order-to-cash, procure-to-pay, tax, treasury) have zero lens data and cannot be assessed.

### Record to Report

**Current state (from lens data):**

- `record-to-report.close` — automation: `human`; operating_model: `local`. The close step is entirely human-executed on the accrual side, with decentralized recon sign-off across regional controllers. No automation is present in the described close steps.
- `record-to-report.consolidation` — automation: `mixed`; operating_model: `central`. IC eliminations are machine-driven; topside entries are manual. Consolidation authority is centralized — a clean structural strength.
- Both nodes: process lens null (one due to conflict, one due to coverage gap); capability lens null across both.

**Future-state signal:** No `capability:new` nodes exist in the current register — there are no explicit future-state flags. The directional read comes from the gap recommendations.

**The current-to-future story for Record to Report:**

Today the close cycle is split: a manual, locally-owned accrual and recon close (`record-to-report.close`) feeds a centralized, partially-automated consolidation (`record-to-report.consolidation`). The operating model contrast between local close and central consolidation is structurally sound — the fragility is in execution quality, not design.

The move that matters is shifting `record-to-report.close` automation from `human` toward `mixed` (at minimum) by introducing an automated accrual journal upload or ERP-native accrual workflow (GAP-0001). That change removes the leading source of late adjustments without restructuring the operating model. Separately, converting the decentralized recon sign-off from an unmonitored local control to a centrally-observable one — via reconciliation tool configuration (GAP-0002, THM-0001) — closes the oversight gap without requiring organizational restructuring.

For `record-to-report.consolidation`, the delta between IC eliminations (automated) and topside entries (manual) is the target: moving topside entries toward systemization (GAP-0004) would bring consolidation automation from `mixed` to `mostly automated` within the existing centralized operating model.

### Risk, Policy and Controls

**Current state (from lens data):**

- `risk-policy-controls.internal-controls` — current_state: `present`; process: `pain_med`; automation: null; capability: null; operating_model: null. A control intent exists and is verbally asserted; the process is characterized as moderate pain due to its informal, tribal nature.
- All other Risk, Policy & Controls nodes (policies-and-procedures, risk-assessment, monitoring, reporting) carry zero coverage.

**The current-to-future story for Risk, Policy & Controls:**

Today the internal controls function operates on verbal institutional knowledge for at least its key close-related control (the $50K dual-review threshold). Evidence tier is `verbal` across all internal-controls findings (GAP-0005). The process lens reading of `pain_med` reflects the fragility of an informal norm rather than a designed control.

The future state for this L1 is: controls that currently live in people's heads move to documented policy and system-observed enforcement. The reconciliation tool is already in use and is the natural enforcement point (GAP-0005 recommended_action). This is not a structural redesign — it is formalization of a practice that already exists informally. The cross-cutting theme (THM-0001) makes this the same root action as what is needed in `record-to-report.close`.

The four uncovered nodes in this L1 (policies-and-procedures, risk-assessment, monitoring, reporting) cannot be assessed. Given that the one covered node shows verbal-only controls, it is a reasonable working hypothesis — not an assertion — that documentation gaps extend more broadly across the controls framework. Additional discovery is needed before a fuller picture can be drawn.

### Remaining L1 Cycles (fpa, order-to-cash, procure-to-pay, tax, treasury)

No lens data. No current or future state can be assessed. Thirty nodes across these five cycles are empty. The engagement's diagnostic scope will need to expand significantly before synthesis can speak to these areas.

---

## 4. Cross-Cutting Themes

### THM-0001 — Verbal-only / undocumented controls (cross-cutting)

The single most significant cross-cutting pattern in the current evidence set is the same control deficiency appearing independently in two different L1 nodes:

- In `record-to-report.close` (GAP-0002): the dual-review control for recons above $50K exists in practice but is not documented or system-enforced — "lives in people's heads."
- In `risk-policy-controls.internal-controls` (GAP-0005): the same control, assessed from the controls lens, confirmed by the same evidence source, characterized as `control_not_evidenced` — verbal attestation only, cannot be independently evidenced.

Both findings cite the same evidence (`ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L33-35`). The same root problem — reliance on tribal knowledge rather than documented and system-enforced controls — also appears in the consolidation handoff description (`record-to-report.consolidation`, open items: handoff from recons to consolidation undocumented).

A per-node view shreds this into three separate items. The synthesis view names it as a single pattern: **this organization has a broader tendency to operate on institutional knowledge in places where documented, system-observable controls are required.** The audit and SOX exposure of a control that cannot be independently evidenced is not confined to a single L2 node — it is a governance posture question.

THM-0001 has been lifted as a `type:theme` row in the register (see Step 2 below). The recommended action for that theme is: document all controls currently relying on verbal attestation, beginning with the $50K dual-review threshold, and systematically configure enforcement in the relevant tools (reconciliation tool, consolidation system) so controls are observable, auditable, and not person-dependent.

---

*Synthesis authored by Stage 5C. All claims cite register IDs or node keys. No numbers (ROI, headcount, savings) are invented. Items flagged as directional require human confirmation and promotion to `type:improvement` before roadmap placement is treated as authoritative.*
