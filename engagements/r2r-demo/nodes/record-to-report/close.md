---
node: record-to-report.close
l1: record-to-report
l1_name: Record to Report
l2: close
l2_name: Close
coverage: partial
lenses:
  current_state: present
  process: null
  automation: human
  capability: null
  operating_model: local
---

# Record to Report — Close

## What we learned

The monthly close for this entity follows a conventional sequence: sub-ledger close (AP/AR) on business day one, manual accrual posting, trial balance lock, account reconciliations, and handoff to the consolidation team. Coverage is partial — management review and the consolidation handoff were noted but not walked through in detail.

Two process weaknesses stand out. First, the accrual workflow is entirely manual: entries are built in spreadsheets, then re-keyed into the ERP each month. The controller identified this as the primary pain point and the most frequent cause of late adjustments. Second, the dual-reviewer control for balance-sheet reconciliations above $50K exists in practice but is not documented in policy or enforced by the system — it lives in institutional memory, creating single-point-of-failure risk if key personnel change.

Recon ownership is decentralized across regional controllers. A separate interview described the recon tool and escalation process as a relative strength, which conflicts with the pain-point characterization of the accrual-adjacent process in the close walkthrough. Because these two signals apply to overlapping but distinct sub-processes (accruals vs. recon completeness), the `process` lens has been left null pending human resolution of the conflict.

## Evidence digest

The close walkthrough transcript documents the end-to-end close sequence and identifies accruals as the leading pain point (`ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L23-27`). The controller explicitly confirmed that accruals are "fully manual today" with teams building entries in spreadsheets and re-keying them — the most common source of late adjustments.

The dual-review control (recons above $50K require a second-level reviewer) was confirmed verbally but the controller acknowledged it is not captured in any policy or system configuration: "It lives in people's heads" (`ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L35-36`).

Decentralized recon sign-off was described directly: each balance-sheet account owner (by regional controller) signs off in the recon tool with no central sign-off layer (`ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L27-28`).

The recon walkthrough transcript provides a conflicting signal: the senior accountant characterized reconciliations as "one of our stronger areas" with standardized tooling and clear ownership (`ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L30-31`). This signal is not inherently inconsistent with decentralized ownership — regional ownership with a mature tool can coexist — but the two sources were classified against the same `process` lens at different valence levels (pain_high vs. strength), producing a cross-document conflict that prevents lens resolution.

## Diagnosis (5 lenses)

**Current state: `present`**
A close process exists and was walkable in the interview. The full sequence — sub-ledger close, accruals, recons, handoff to consolidation — is operational. Coverage is partial because management review and the consolidation handoff steps were not examined in depth. Evidence: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L23-27`.

**Process: `null`**
This lens was left null by the classify-merge layer due to a cross-document conflict. The close walkthrough signals a pain-level process (accruals manual, late adjustments, no documentation of key controls), while the recon walkthrough describes reconciliations specifically as a strength. Because the two transcripts cover partially overlapping scope and the conflict was not resolvable deterministically, the lens requires human review before a value can be set. See `GAP-CONFLICT-record-to-report-close-process` in the register.

**Automation: `human`**
The accrual workflow is fully human-executed. Entries are constructed in spreadsheets and manually re-entered into the ERP with no automated upload or ERP-native accrual workflow. The controller described this as the most common source of late adjustments. No automation is present in the described close steps. Evidence: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L25-27`.

**Capability: `null`**
Insufficient evidence to assess the team's capability level. The interviews described process mechanics but did not speak to staffing depth, skill mix, or capacity constraints in a way that would support a reliable capability rating. Requires additional evidence.

**Operating model: `local`**
Account reconciliation sign-off is decentralized: each regional controller owns and signs off their own balance-sheet accounts. There is no described central oversight layer over the recon sign-off step. Consolidation happens downstream at corporate, but the close itself — including recon completion — is locally owned. Evidence: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L27-28`.

## Open items

The following findings are confirmed for this node; the orchestrator will assign register IDs after this MD is authored. Items are referenced by dedup_key.

- **`record-to-report.close|gap|manual-accruals-spreadsheet-rekeying`** — Accruals are fully manual (spreadsheet-built, ERP re-keyed); the controller's primary stated pain point and leading cause of late adjustments. Evidence: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L25-27`.

- **`record-to-report.close|gap|undocumented-dual-review-control`** — The dual-reviewer control for reconciliations above $50K is operated in practice but not documented in policy or enforced by system configuration. Relies entirely on institutional memory. Evidence: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L35-36`.

- **`record-to-report.close|gap|decentralized-recon-sign-off`** — Recon sign-off is distributed across regional controllers with no central oversight described. Whether this represents a risk depends on control quality per region, which was not assessed. Evidence: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L27-28`.

- **`GAP-CONFLICT-record-to-report-close-process`** (existing register row) — Cross-document conflict on the `process` lens; requires human resolution before the lens can be set and before a process-quality finding can be confirmed. Evidence refs: `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L25-27`, `ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L30-31`.
