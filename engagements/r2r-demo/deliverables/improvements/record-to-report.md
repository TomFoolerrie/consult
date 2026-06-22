# Process Improvement Opportunities — Record to Report

> Engagement: r2r-demo · L1 cycle: record-to-report · Source: register type:improvement rows
> (via draft_inputs.py gather), grouped by lens. Effort × Impact is directional
> unless a quantified source backs it.
>
> L2 nodes covered: record-to-report.close, record-to-report.consolidation
> (nodes with type:improvement rows; three other L2 nodes have no improvement rows).
>
> Cross-cutting theme: THM-0001 (undocumented controls, priority p1) — verbal-only controls
> that cannot be independently evidenced surface across both close and consolidation. Items
> IMP-0002 and IMP-0005 are the primary instantiations of this theme within this L1 cycle.

---

## Process

### IMP-0002 — Undocumented dual-reviewer control for reconciliations above $50K

- **Finding:** The dual-reviewer control for balance-sheet reconciliations above $50K exists in
  practice but is not documented in any policy and is not enforced by the reconciliation tool —
  "it lives in people's heads." This creates key-person dependency and an audit/SOX evidencing
  risk. (Root cause not captured in register — needs input.)
- **Recommendation:** Document the dual-review threshold in a formal controls policy and configure
  the reconciliation tool to enforce the $50K approval requirement systematically, converting the
  control from verbal to system-observed.
- **Effort × Impact:** directional — Effort: low; Impact type: needs input — confirm with process
  owner; Estimated benefit: needs input — confirm with process owner.
- **Owner:** TBD — needs input; confirm with process owner (likely Controller or Accounting Policy).
- **Traceability:** register IMP-0002 · evidence
  `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L35-36` (tier: needs input —
  evidence tier not recorded). Also relates to cross-cutting theme THM-0001 (undocumented controls,
  p1) and GAP-0002.

---

### IMP-0005 — Undocumented recon-to-consolidation handoff sequence

- **Finding:** The handoff sequencing from reconciliation sign-off to consolidation intake is not
  captured in any policy or system workflow — the controller acknowledged it "isn't written into
  any policy or system config — it lives in people's heads." This creates execution risk and an
  absence of an auditable control point at the recon-to-consolidation boundary.
  (Root cause not captured in register — needs input.)
- **Recommendation:** Document the recon-to-consolidation handoff sequence in a formal close
  checklist or SOP, and configure a workflow gate in the consolidation system so that the
  elimination run cannot begin until all required recon sign-offs are confirmed complete.
- **Effort × Impact:** directional — Effort: low; Impact type: needs input — confirm with process
  owner; Estimated benefit: needs input — confirm with process owner.
- **Owner:** TBD — needs input; confirm with process owner (likely Controller or Consolidation
  team lead).
- **Traceability:** register IMP-0005 · evidence
  `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L35-36` (tier: needs input —
  evidence tier not recorded). Also relates to cross-cutting theme THM-0001 (undocumented controls,
  p1).

---

## Automation

### IMP-0001 — Manual accrual spreadsheet-to-ERP re-key workflow

- **Finding:** Accrual entries are built in spreadsheets and manually re-keyed into the ERP each
  month — the controller's primary stated pain point and the leading cause of late close
  adjustments. Automation lens for the Close node is rated `human`, indicating no automated
  workflow is present for this step. (Root cause not captured in register — needs input.)
- **Recommendation:** Automate the accrual workflow: evaluate ERP-native recurring accrual
  templates or a structured journal-upload integration to eliminate the spreadsheet-to-ERP re-key
  step.
- **Effort × Impact:** directional — Effort: med; Impact type: needs input — confirm with process
  owner; Estimated benefit: needs input — confirm with process owner.
- **Owner:** TBD — needs input; confirm with process owner (likely Controller or ERP team).
- **Traceability:** register IMP-0001 · evidence
  `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L25-27` (tier: needs input —
  evidence tier not recorded). Also corresponds to GAP-0001.

---

### IMP-0004 — Manual topside entries alongside fully automated IC eliminations

- **Finding:** Topside entries are still booked manually by the corporate team while IC
  eliminations in the same consolidation step are fully automated — creating an inconsistency in
  automation maturity within a single L2 process. Automation lens for the Consolidation node is
  rated `mixed`, reflecting this split posture. (Root cause not captured in register — needs input.)
- **Recommendation:** Assess whether recurring or templated topside entries can be configured in
  the consolidation tool (e.g., as standing journals or rule-based postings), reducing the manual
  intervention to exception-only topsides.
- **Effort × Impact:** directional — Effort: med; Impact type: needs input — confirm with process
  owner; Estimated benefit: needs input — confirm with process owner.
- **Owner:** TBD — needs input; confirm with process owner (likely Consolidation team lead or
  Corporate Accounting).
- **Traceability:** register IMP-0004 · evidence
  `ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L26-28` (tier: needs input —
  evidence tier not recorded). Also corresponds to GAP-0004.

---

## Operating Model

### IMP-0003 — Decentralized reconciliation sign-off with no central oversight layer

- **Finding:** Reconciliation sign-off is distributed across regional controllers with no central
  oversight layer — each regional controller signs off their own accounts in the recon tool with
  no corporate-level review step described. Operating model lens for the Close node is rated
  `local`. Whether this is a risk depends on per-region control quality, which was not assessed.
  (Root cause not captured in register — needs input.)
- **Recommendation:** Evaluate whether a central sign-off or exception-review layer should sit
  above regional recon completion, particularly for material accounts, to provide a consolidated
  quality gate before the consolidation handoff.
- **Effort × Impact:** directional — Effort: med; Impact type: needs input — confirm with process
  owner; Estimated benefit: needs input — confirm with process owner.
- **Owner:** TBD — needs input; confirm with process owner (likely Controller or CFO).
- **Traceability:** register IMP-0003 · evidence
  `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L27-28` (tier: needs input —
  evidence tier not recorded). Also corresponds to GAP-0003.

---

## Capability

_No type:improvement rows with tag `capability` were present in the register for this L1 cycle.
If a capability improvement is identified in subsequent walkthroughs, it will appear here._

---

## Notes on missing fields

All five improvement items (IMP-0001 through IMP-0005) have the following fields absent in the
register: `root_cause`, `impact_type`, `estimated_impact_benefit`, `owner`, `evidence_tier`. These
are surfaced above as "needs input" per the Improvement DoD rather than fabricated. The register
should be updated by the process owner or engagement lead before this deliverable moves to
`in_review` status.

## Cross-cutting theme reference

**THM-0001 — Undocumented controls (priority: p1):** The dual-review control (recons above $50K)
and the recon-to-consolidation handoff sequence both rely on verbal institutional knowledge rather
than documented policy or system-enforced workflow. This theme surfaces in
record-to-report.close (IMP-0002, IMP-0005) and also has a related instance in
risk-policy-controls.internal-controls (out of scope for this document). The recommended
resolution path — formalize in policy and configure system enforcement — is consistent across
IMP-0002 and IMP-0005 above.
