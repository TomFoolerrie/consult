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
- Intercompany eliminations are fully automated within the consolidation tool — a notably mature automation posture for that sub-step (`record-to-report.consolidation`, automation: mixed).
- The consolidation function itself is centralized at corporate with a single team holding all elimination, topside, and review authority — a clean operating-model design that avoids fragmented consolidation judgment (`record-to-report.consolidation`, operating_model: central).

**Weaknesses (the fragile half):**

- Monthly accruals are entirely manual: built in spreadsheets and re-keyed into the ERP each cycle. The controller identified this as the primary close pain point and the most frequent source of late adjustments (IMP-0001; `record-to-report.close`, automation: human).
- The dual-review control for reconciliations above $50K operates in practice but is documented nowhere — no policy, no system configuration, entirely oral/tribal. This theme recurs across both `record-to-report.close` (IMP-0002) and `risk-policy-controls.internal-controls`, and is lifted as a cross-cutting theme (THM-0001, see below).
- Recon sign-off is decentralized across regional controllers with no central oversight layer — the quality of that local control regime is unassessed (IMP-0003).
- Manual topside entries at corporate sit alongside an otherwise automated elimination process, creating a maturity inconsistency within the same consolidation step (IMP-0004).
- The recon-to-consolidation handoff is not captured in any policy or system workflow — an unauditable control boundary (IMP-0005).

**The three to five moves that matter:**

1. Document and system-enforce the dual-review control — verbal-only controls carry audit and SOX risk and cannot be independently evidenced (IMP-0002 / THM-0001). This is actionable immediately.
2. Automate the accrual workflow — eliminate the spreadsheet-to-ERP re-key loop (IMP-0001). The primary stated pain point, medium effort, high impact.
3. Document and gate the recon-to-consolidation handoff — convert an undocumented hand-off into an auditable workflow control point (IMP-0005).
4. Assess and systemize topside entry types in the consolidation tool (IMP-0004).
5. Evaluate a central oversight layer above regional recon sign-off for material accounts (IMP-0003).
6. Expand coverage — thirty-four nodes with zero coverage represent the engagement's largest blind spot; the synthesis below is directional but incomplete until broader discovery occurs.

---

## 2. Effort x Impact Prioritization

All five active improvements carry explicit `effort` and `priority` register fields. The roadmap below is sequenced directly from those fields via the effort × impact bucketing — no qualitative re-estimation has been applied. Impact is derived from `priority` (p1 → high, p2 → med, p3 → low). No items are unranked.

### Quick Wins (low effort / high impact)

These items can be initiated immediately. Low effort signals a writing or configuration task, not a system integration.

| Register ID | Node | Effort | Impact | Action |
|---|---|---|---|---|
| **IMP-0002** | `record-to-report.close` | low | high (p1) | Document the dual-review threshold ($50K) in a formal controls policy and configure the reconciliation tool to enforce the approval requirement systematically — converting a verbal, tribal control to a system-observed one. Closes audit/SOX evidencing risk. |

IMP-0002 also directly advances THM-0001 (undocumented controls), making it the highest-leverage first action in the engagement.

### 0–6 Months (major project, p1)

Medium-effort, high-impact items at priority p1 belong in the first planning wave.

| Register ID | Node | Effort | Impact | Action |
|---|---|---|---|---|
| **IMP-0001** | `record-to-report.close` | med | high (p1) | Automate the accrual workflow: evaluate ERP-native recurring accrual templates or a structured journal-upload integration to eliminate the spreadsheet-to-ERP re-key step. Primary stated pain point and leading source of late close adjustments. |

IMP-0001 is the largest automation uplift available in the covered nodes. Scoping of ERP-native accrual templates versus a journal-upload integration is a prerequisite design step.

### 6–18 Months (incremental, p2)

Three incremental improvements carry p2 priority and medium or low effort. Within this tier, lower-effort items are sequenced first.

| Sequence | Register ID | Node | Effort | Impact | Action |
|---|---|---|---|---|---|
| 1 | **IMP-0005** | `record-to-report.consolidation` | low | med (p2) | Document the recon-to-consolidation handoff sequence in a formal close checklist or SOP, and configure a workflow gate in the consolidation system so that the elimination run cannot begin until all required recon sign-offs are confirmed complete. Converts an undocumented handoff into an auditable control point. |
| 2 | **IMP-0003** | `record-to-report.close` | med | med (p2) | Evaluate whether a central sign-off or exception-review layer should sit above regional recon completion for material accounts — providing a consolidated quality gate before the consolidation handoff. |
| 3 | **IMP-0004** | `record-to-report.consolidation` | med | med (p2) | Assess whether recurring or templated topside entries can be configured in the consolidation tool as standing journals or rule-based postings, reducing manual intervention to exception-only topsides. |

IMP-0005 is sequenced ahead of IMP-0003 and IMP-0004 despite equal priority because its lower effort makes it a natural lead-in; it also creates the formal handoff gate that the operating-model review in IMP-0003 then quality-assures.

### No Unranked Items

All five improvements carry explicit `effort` and `priority` values. No items require human review for roadmap placement.

---

## 3. Per-L1 Current to Future Operating Model

Only two L1 cycles carry covered nodes. The remaining five (fpa, order-to-cash, procure-to-pay, tax, treasury) have zero lens data and cannot be assessed.

### Record to Report

**Current state (from lens data):**

- `record-to-report.close` — automation: `human`; operating_model: `local`. The close step is entirely human-executed on the accrual side, with decentralized recon sign-off across regional controllers. No automation is present in the described close steps. Three active improvements (IMP-0001, IMP-0002, IMP-0003) target this node.
- `record-to-report.consolidation` — automation: `mixed`; operating_model: `central`. IC eliminations are machine-driven; topside entries are manual. Consolidation authority is centralized — a clean structural strength. Two active improvements (IMP-0004, IMP-0005) target this node.
- Both nodes: process lens null (one due to conflict, one due to coverage gap); capability lens null across both.

**Future-state signal:** No `capability:new` nodes exist in the current register — there are no explicit future-state flags. The directional read comes from the improvement recommendations.

**The current-to-future story for Record to Report:**

Today the close cycle is split: a manual, locally-owned accrual and recon close (`record-to-report.close`) feeds a centralized, partially-automated consolidation (`record-to-report.consolidation`). The operating model contrast between local close and central consolidation is structurally sound — the fragility is in execution quality and control formalization, not design.

The move that matters first is formalization before automation: IMP-0002 converts the most critical existing control (dual-review above $50K) from a verbal norm to a documented, system-enforced one — without requiring any new tooling. That unblocks clean audit evidence and removes key-person dependency.

The medium-horizon automation move (IMP-0001) then shifts `record-to-report.close` from `human` toward `mixed` automation by introducing an automated accrual journal workflow or ERP-native accrual templates. That change removes the leading cause of late adjustments without restructuring the operating model.

For `record-to-report.consolidation`, the path runs in two steps: first, document and gate the recon-to-consolidation handoff so the boundary becomes auditable (IMP-0005); then reduce the manual topside entry residual within an otherwise machine-driven consolidation by configuring standing journals or rule-based postings (IMP-0004). Both moves extend the existing centralized operating model's automation posture without restructuring its governance.

### Risk, Policy and Controls

**Current state (from lens data):**

- `risk-policy-controls.internal-controls` — current_state: `present`; process: `pain_med`; automation: null; capability: null; operating_model: null. A control intent exists and is verbally asserted; the process is characterized as moderate pain due to its informal, tribal nature.
- All other Risk, Policy & Controls nodes (policies-and-procedures, risk-assessment, monitoring, reporting) carry zero coverage.

**The current-to-future story for Risk, Policy & Controls:**

Today the internal controls function operates on verbal institutional knowledge for at least its key close-related control (the $50K dual-review threshold). The process lens reading of `pain_med` reflects the fragility of an informal norm rather than a designed control.

The future state for this L1 is: controls that currently live in people's heads move to documented policy and system-observed enforcement. IMP-0002 (tagged `process`, `record-to-report.close`) is the direct action for this node's primary identified control gap, and its execution closes the audit/SOX evidencing exposure surfaced at `risk-policy-controls.internal-controls`. This is not a structural redesign — it is formalization of a practice that already exists informally. The cross-cutting theme THM-0001 makes this the same root action as what is needed in `record-to-report.close`.

The four uncovered nodes in this L1 (policies-and-procedures, risk-assessment, monitoring, reporting) cannot be assessed. Given that the one covered node shows verbal-only controls, it is a reasonable working hypothesis — not an assertion — that documentation gaps extend more broadly across the controls framework. Additional discovery is needed before a fuller picture can be drawn.

### Remaining L1 Cycles (fpa, order-to-cash, procure-to-pay, tax, treasury)

No lens data. No current or future state can be assessed. Thirty nodes across these five cycles are empty. The engagement's diagnostic scope will need to expand significantly before synthesis can speak to these areas.

---

## 4. Cross-Cutting Themes

### THM-0001 — Verbal-only / undocumented controls (cross-cutting)

The single most significant cross-cutting pattern in the current evidence set is the same control deficiency appearing independently across two nodes in different L1 cycles:

- In `record-to-report.close` (IMP-0002): the dual-review control for recons above $50K exists in practice but is not documented or system-enforced — "lives in people's heads." The same observation is the source condition for IMP-0005 as well (the recon-to-consolidation handoff is similarly undocumented).
- In `risk-policy-controls.internal-controls`: the same control, assessed from the controls lens, confirmed by the same evidence source, characterized as `control_not_evidenced` — verbal attestation only, cannot be independently evidenced.

Both findings cite the same evidence (`ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L33-35`). The same root problem — reliance on tribal knowledge rather than documented and system-enforced controls — also appears in the consolidation handoff description (IMP-0005, `record-to-report.consolidation`).

A per-node view shreds this into three separate items. The synthesis view names it as a single pattern: **this organization has a broader tendency to operate on institutional knowledge in places where documented, system-observable controls are required.** The audit and SOX exposure of a control that cannot be independently evidenced is not confined to a single L2 node — it is a governance posture question.

THM-0001 is registered as a `type:theme` row (dedup_key: `theme|undocumented-controls`), spanning `record-to-report.close` and `risk-policy-controls.internal-controls`. The recommended action for that theme is: document all controls currently relying on verbal attestation, beginning with the $50K dual-review threshold, and systematically configure enforcement in the relevant tools (reconciliation tool, consolidation system) so controls are observable, auditable, and not person-dependent. IMP-0002 is the immediate execution vehicle for this theme.

---

*Synthesis authored by Stage 5C. All claims cite register IDs (IMP-NNNN / THM-NNNN) or node keys. No numbers (ROI, headcount, savings) are invented. Roadmap sequencing is derived exclusively from register `effort` and `priority` fields via the effort × impact bucketing in synthesis_inputs.py.*
