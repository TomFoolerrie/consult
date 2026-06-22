# Record to Report — Standard Operating Procedure

**Scope Level:** L1-Level SOP Deliverable
**Engagement:** r2r-demo
**Document Version:** v0.1 (draft)
**Date:** 2026-06-21
**Status:** Draft

---

## 1. Document Profile

| Field | Value |
|---|---|
| L1 Business Cycle | Record to Report |
| Scope Level | L1-Level SOP Deliverable — covers all five L2 process areas under Record to Report |
| Output Mode | Discovery / Triage Mode — two L2 nodes (Close, Consolidation) have sufficient partial coverage to draft procedure-level documentation; three L2 nodes (Pre-Close Set Up, Reporting, Accounting Policy) have no coverage and are included as inventory stubs with gaps logged in Appendix C |
| Document Status | Draft — pending SME validation |
| Prepared By | CONSULT pipeline — Stage 5A Drafter |
| Reviewed By | TBD — confirm with engagement lead |
| Engagement | r2r-demo |
| Client / Organization | TBD — confirm with engagement lead |
| Effective Date | TBD |
| Next Review Date | TBD |

---

## 2. Source Materials

| ID | Source | Description | Coverage |
|---|---|---|---|
| SRC-001 | `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md` | Controller walkthrough — monthly close sequence, accruals workflow, recon sign-off model, handoff to consolidation | Primary source for Close (L2) |
| SRC-002 | `ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md` | Senior Accountant walkthrough — reconciliation tooling, IC eliminations, consolidation operating model | Primary source for Consolidation (L2); supplemental for Close (L2) |

**Note:** No source material was ingested for Pre-Close Set Up, Reporting, or Accounting Policy. See Appendix C for structural gap entries.

---

## 3. Process Taxonomy

**L1 Business Cycle:** Record to Report
The Record to Report cycle encompasses all activities from pre-close configuration through monthly financial close, intercompany eliminations, consolidation, and management/regulatory reporting, underpinned by an accounting policy framework.

### L2 Process Area Inventory

| # | L2 Key | L2 Process Area | Coverage | Documentation Status | Primary Owner (TBD) | Key System(s) (TBD) |
|---|---|---|---|---|---|---|
| 1 | `pre-close-set-up` | Pre-Close Set Up | none | Not yet documented — see Appendix C (GAP-STRUCT-record-to-report-pre-close-set-up-no-coverage) | TBD | TBD |
| 2 | `close` | Close | partial | Drafted — substantive procedure detail available; management review and consolidation handoff steps partially covered | Regional Controller | ERP, Reconciliation Tool |
| 3 | `consolidation` | Consolidation | partial | Drafted — IC eliminations and topside entries documented; equity accounting and variance analysis not yet covered | Corporate Consolidation Team | Consolidation System, ERP |
| 4 | `reporting` | Reporting | none | Not yet documented — see Appendix C (GAP-STRUCT-record-to-report-reporting-no-coverage) | TBD | TBD |
| 5 | `accounting-policy` | Accounting Policy | none | Not yet documented — see Appendix C (GAP-STRUCT-record-to-report-accounting-policy-no-coverage) | TBD | TBD |

---

## 4. Current-State Process Documentation

### 4.1 Process Overview

The Record to Report (R2R) cycle produces the organization's monthly financial close and consolidated financial statements. The cycle begins with pre-close configuration activities (master data, access rights, close checklist) and proceeds through entity-level close (sub-ledger close, accruals, reconciliations), consolidation (intercompany eliminations, topside entries, corporate review), and external and internal reporting. Accounting policy provides the governance framework across all steps.

### 4.2 Process Purpose

To produce accurate, timely, and auditable monthly financial statements through a controlled sequence of close, consolidation, and reporting activities, governed by documented accounting policies.

### 4.3 Process Boundaries

| Boundary | Description |
|---|---|
| Start | Pre-close configuration / close checklist activation (L2: Pre-Close Set Up) [[GAP — NOT DOCUMENTED]] |
| End | Distribution of consolidated financial statements and management reports to stakeholders (L2: Reporting) [[GAP — NOT DOCUMENTED]] |
| In Scope | Monthly financial close, account reconciliations, intercompany eliminations, topside entries, consolidated financial statements |
| Out of Scope | External audit management, statutory filing, capital allocation decisions |

### 4.4 Process Flow Summary

The R2R cycle flows sequentially across L2 process areas. Based on evidence gathered to date:

1. **Pre-Close Set Up** — [[GAP — NOT DOCUMENTED]] Configuration, access rights, close checklist, and pre-close meetings occur before period-end. Detail not yet documented.
2. **Close** — Sub-ledger close (AP/AR) initiates on business day one of close. Manual accruals are built in spreadsheets and re-keyed into the ERP. Trial balance is locked. Account reconciliations are signed off by regional controllers. Completed entity data is handed off to the consolidation team. (`SRC-001#L23-27`, `SRC-001#L35-36`)
3. **Consolidation** — Entity trial balances are loaded into the central consolidation system. Intercompany eliminations are executed automatically. Topside entries are booked manually by the corporate team. Corporate review occurs before consolidated financials are produced. (`SRC-002#L22-23`, `SRC-002#L26-28`, `SRC-002#L33-35`)
4. **Reporting** — [[GAP — NOT DOCUMENTED]] Management reports, consolidated financial statements, and regulatory reports are produced and distributed. Detail not yet documented.
5. **Accounting Policy** — [[GAP — NOT DOCUMENTED]] Policy framework governing the above steps. Detail not yet documented.

### 4.5 Sub-Process Inventory

| L2 | L3 Activity | Coverage | Notes |
|---|---|---|---|
| Pre-Close Set Up | Master Data Configuration | none | [[GAP — NOT DOCUMENTED]] |
| Pre-Close Set Up | Ledger Configuration | none | [[GAP — NOT DOCUMENTED]] |
| Pre-Close Set Up | Cost and Profit Center Reporting | none | [[GAP — NOT DOCUMENTED]] |
| Pre-Close Set Up | Manage User Access Rights (SOD) | none | [[GAP — NOT DOCUMENTED]] |
| Pre-Close Set Up | Division of Labor and Responsibilities | none | [[GAP — NOT DOCUMENTED]] |
| Pre-Close Set Up | Close Checklist | none | [[GAP — NOT DOCUMENTED]] |
| Pre-Close Set Up | Pre-Close Meetings | none | [[GAP — NOT DOCUMENTED]] |
| Pre-Close Set Up | Data Governance | none | [[GAP — NOT DOCUMENTED]] |
| Close | Sub-Ledger Close (AP/AR) | partial | Confirmed as step one; limited procedural detail |
| Close | Manual Accrual Posting | partial | Spreadsheet-built, ERP re-keyed; primary pain point (`SRC-001#L25-27`) |
| Close | Trial Balance Lock | partial | Mentioned; no procedural detail documented |
| Close | Account Reconciliations | partial | Decentralized sign-off by regional controllers (`SRC-001#L27-28`) |
| Close | Management Review | partial | Mentioned as next step; not walked through (`SRC-001#L41`) |
| Consolidation | Entity Data Collection | partial | Trial balances loaded to central system (`SRC-002#L22-23`) |
| Consolidation | IC Eliminations | partial | Automated against matched IC accounts (`SRC-002#L26-28`) |
| Consolidation | Topside Entries | partial | Manual, booked by corporate (`SRC-002#L26-28`) |
| Consolidation | Equity Accounting | none | [[GAP — NOT DOCUMENTED]] Not covered in walkthroughs |
| Consolidation | Variance Analysis | none | [[GAP — NOT DOCUMENTED]] Not covered in walkthroughs |
| Reporting | Management Reporting | none | [[GAP — NOT DOCUMENTED]] |
| Reporting | Consolidated Financial Statements | none | [[GAP — NOT DOCUMENTED]] |
| Reporting | Prepare Regulatory Reports | none | [[GAP — NOT DOCUMENTED]] |
| Reporting | Investor Relations Support | none | [[GAP — NOT DOCUMENTED]] |
| Reporting | Close & Reporting Analytics | none | [[GAP — NOT DOCUMENTED]] |
| Accounting Policy | Baseline Accounting Policies & Procedures | none | [[GAP — NOT DOCUMENTED]] |
| Accounting Policy | Revenue Recognition (606) | none | [[GAP — NOT DOCUMENTED]] |
| Accounting Policy | Lease Accounting (842) | none | [[GAP — NOT DOCUMENTED]] |
| Accounting Policy | New Accounting Standards | none | [[GAP — NOT DOCUMENTED]] |

---

## 5. Detailed Procedures

> Procedures are grouped by L2 process area. L2 nodes with coverage: none are listed as inventory stubs; their L3 activities are not-yet-documented and are logged in Appendix C.

---

### 5.1 Pre-Close Set Up

[[GAP — NOT DOCUMENTED]] This L2 process area has not been documented to date (coverage: none). No walkthrough was conducted covering master data configuration, ledger configuration, SOD / access rights management, close checklist, or pre-close meetings. See Appendix C: GAP-STRUCT-record-to-report-pre-close-set-up-no-coverage. A targeted walkthrough with the process owner is required before procedures can be drafted.

---

### 5.2 Close

#### Procedure Header

| Field | Value |
|---|---|
| L2 Process Area | Close |
| L1 Business Cycle | Record to Report |
| Coverage | Partial |
| Primary Source | SRC-001 (`ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md`) |
| Supplemental Source | SRC-002 (`ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md`) |

#### A. Process Overview

The monthly close process follows a sequential structure from sub-ledger close through account reconciliations and handoff to the consolidation team. The accrual workflow is the primary identified pain point: all accruals are built manually in spreadsheets and re-keyed into the ERP each period. Account reconciliation sign-off is decentralized across regional controllers. A dual-reviewer control for high-value reconciliations is operated in practice but is not documented in policy or enforced by system configuration.

Coverage is partial. Management review and the consolidation handoff steps were noted but not walked through in procedural detail. The `process` lens is unresolved due to a cross-document conflict between the close walkthrough (characterizing the process as a pain point) and the recon walkthrough (characterizing reconciliations as a relative strength). See Appendix C: GAP-CONFLICT-record-to-report-close-process.

#### B. Summary Card

| Field | Value |
|---|---|
| Frequency | Monthly |
| Trigger | Period-end calendar / close start signal |
| Primary Role | Regional Controller |
| Key Systems | ERP (TBD — confirm system name), Reconciliation Tool (TBD — confirm system name) |
| Key Outputs | Locked trial balance, signed-off account reconciliations, handoff package to consolidation team |
| Approver(s) | TBD — confirm with process owner |
| SLA / Deadline | TBD — confirm close calendar target dates |

#### C. Pre-Requisites

- AP and AR sub-ledgers are closed for the period.
- All pending journal entries and corrections have been posted.
- Reconciliation templates are available to regional controllers.
- [[GAP — NOT DOCUMENTED]] Pre-close checklist completion and pre-close meeting outcomes are not documented; assumed to precede close execution.

#### D. Data Inputs

| Input | Source | Format |
|---|---|---|
| AP sub-ledger | Accounts Payable module | ERP-generated |
| AR sub-ledger | Accounts Receivable module | ERP-generated |
| Accrual data | Department/cost center owners | Spreadsheet (manual) |
| Prior-period reconciliations | Reconciliation tool | TBD |

#### E. Step-by-Step Desktop Procedure

##### Step 1: Close AP and AR Sub-Ledgers

Close the accounts payable and accounts receivable sub-ledgers for the period. This is the initiating step of the monthly close sequence.

- **System / Tool:** ERP
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** [[GAP — NOT DOCUMENTED]]
- **Expected Result:** AP and AR sub-ledgers closed for the period; no further postings permitted without period reopening
- **Evidence Required:** [[GAP — EVIDENCE RETENTION UNKNOWN]]

> **SCREENSHOT PLACEHOLDER — SC-01:** Sub-ledger close confirmation screen. User to insert screenshot showing period-end close confirmation in ERP for AP and AR modules.

##### Step 2: Build and Post Accrual Journal Entries

Accrual entries are built manually in spreadsheets by the close team or department owners. Completed entries are re-keyed into the ERP. (`SRC-001#L25-27`)

**Current-state note:** The controller identified this step as the primary close pain point and the most frequent source of late adjustments. The process is entirely manual with no automated upload or ERP-native accrual workflow. See Appendix A and Appendix C (GAP-0001) for the registered finding.

- **System / Tool:** Spreadsheet application; ERP
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** Account code, cost center, amount, description, period — [[GAP — confirm required fields]]
- **Expected Result:** Accrual journal entries posted to ERP for the period
- **Evidence Required:** [[GAP — EVIDENCE RETENTION UNKNOWN]] Journal entry posting report or ERP screen capture; no current documentation requirement confirmed

> **SCREENSHOT PLACEHOLDER — SC-02:** Accrual journal entry entry screen in ERP. User to insert screenshot showing the journal entry form with representative fields populated.

##### Step 3: Lock Trial Balance

Following accrual posting, the trial balance is locked for the period to prevent further posting before reconciliations commence.

- **System / Tool:** ERP
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** [[GAP — NOT DOCUMENTED]]
- **Expected Result:** Trial balance locked for the period
- **Evidence Required:** [[GAP — EVIDENCE RETENTION UNKNOWN]]

##### Step 4: Prepare and Sign Off Account Reconciliations

Regional controllers prepare and sign off balance-sheet account reconciliations for their assigned accounts. Sign-off is performed in the reconciliation tool. There is no central sign-off or oversight layer at the completion of this step — each regional controller owns and closes their own accounts. (`SRC-001#L27-28`)

[[GAP — CONTROL NOT EVIDENCED]] A dual-reviewer control is operated in practice for reconciliations with balances above $50K: a second-level reviewer is required before sign-off. This control is not documented in any policy and is not enforced by system configuration — it exists in institutional memory only. (`SRC-001#L35-36`; evidence tier: verbal) See Appendix C: GAP-0002.

- **System / Tool:** Reconciliation Tool (TBD — confirm system name)
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** Account, period, balance, variance explanation, sign-off field
- **Expected Result:** All assigned balance-sheet accounts reconciled and signed off in the reconciliation tool
- **Evidence Required:** Reconciliation tool sign-off record (per account, per period); availability of central retrieval not confirmed

> **SCREENSHOT PLACEHOLDER — SC-03:** Reconciliation sign-off screen in the reconciliation tool. User to insert screenshot showing the sign-off workflow for a completed account reconciliation.

##### Step 5: Management Review

Management review is the next stated step in the close sequence following reconciliation sign-off. (`SRC-001#L41`) This step was noted but not walked through in procedural detail.

[[GAP — NOT DOCUMENTED]] The reviewer, review scope, system used, and any approval or sign-off mechanism for the management review step were not documented. A follow-up walkthrough is needed. See Appendix C.

- **System / Tool:** TBD — confirm with process owner
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** [[GAP — NOT DOCUMENTED]]
- **Expected Result:** TBD
- **Evidence Required:** [[GAP — EVIDENCE RETENTION UNKNOWN]]

##### Step 6: Handoff to Consolidation Team

Following reconciliation sign-off (and management review, pending documentation), the consolidated trial balance or entity package is handed off to the consolidation team for eliminations and topside entries. (`SRC-001#L35-36`)

[[GAP — CONTROL NOT EVIDENCED]] The handoff sequence (recon sign-off → consolidation intake) is not documented in any policy or system workflow configuration. The controller acknowledged: "it isn't written into any policy or system config — it lives in people's heads." (`SRC-001#L35-36`; evidence tier: verbal) See Appendix C: GAP-0003.

- **System / Tool:** TBD — confirm handoff mechanism (email, consolidation system portal, ERP export)
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** [[GAP — NOT DOCUMENTED]]
- **Expected Result:** Consolidation team receives entity close package; eliminations and topside process can commence
- **Evidence Required:** [[GAP — EVIDENCE RETENTION UNKNOWN]]

#### Exceptions / Escalations

[[GAP — NOT DOCUMENTED]] No exception or escalation procedures for the close process were documented in source materials. Escalation paths for late accruals, missed recon sign-offs, or period-reopening requests are unknown. Confirm with process owner.

#### Evidence Retention Requirements

[[GAP — NOT DOCUMENTED]] No formal evidence retention requirements for the monthly close process were described in source materials. Retention requirements (journal entry approvals, recon sign-offs, trial balance locks) should be confirmed with the process owner and compliance/audit function.

#### F. Key Controls

| Control ID | Control Description | Control Type | Frequency | Evidence Status |
|---|---|---|---|---|
| CTRL-CLOSE-01 | Trial balance locked prior to reconciliation sign-off | Preventive | Monthly | [[GAP — CONTROL NOT EVIDENCED]] Mentioned but not walked through in detail |
| CTRL-CLOSE-02 | Dual-reviewer sign-off for balance-sheet reconciliations above $50K | Detective / Preventive | Monthly per applicable account | [[GAP — CONTROL NOT EVIDENCED]] Verbal only — not documented in policy or enforced by system (`SRC-001#L35-36`) |
| CTRL-CLOSE-03 | Regional controller sign-off on assigned account reconciliations | Detective | Monthly | Partially evidenced (verbal) — system-enforced sign-off field in recon tool; tool name TBD (`SRC-001#L27-28`) |

**Note on CTRL-CLOSE-02:** This control was confirmed verbally only (evidence tier: verbal). It does not meet the Evidence DoD for an evidenced control. It is logged as GAP-0002 in Appendix C and flagged with [[GAP — CONTROL NOT EVIDENCED]] above.

#### G. Outputs / Deliverables

| Output | Description | Recipient | Format |
|---|---|---|---|
| Locked trial balance | Entity-level trial balance locked for the period | Consolidation team | ERP-generated (TBD) |
| Signed-off reconciliations | Account reconciliations completed and signed off by regional controllers | TBD — archive location unknown | Reconciliation tool records |
| Entity close package | Handoff package delivered to consolidation team | Corporate Consolidation Team | TBD — format and contents not documented |

#### H. Known Issues and Pain Points

| ID | Description | Impact | Source |
|---|---|---|---|
| (see Appendix A) | Manual accrual workflow: entries built in spreadsheets and re-keyed into ERP monthly; primary close pain point and leading cause of late adjustments | Close delays, late adjustments, manual error risk | `SRC-001#L25-27` |
| (see Appendix C) | Dual-reviewer control not documented or system-enforced; key-person dependency | Audit risk, single-point-of-failure | `SRC-001#L35-36` |
| (see Appendix C) | Decentralized recon sign-off with no central oversight layer; per-region control quality unassessed | Control quality inconsistency risk | `SRC-001#L27-28` |

---

### 5.3 Consolidation

#### Procedure Header

| Field | Value |
|---|---|
| L2 Process Area | Consolidation |
| L1 Business Cycle | Record to Report |
| Coverage | Partial |
| Primary Source | SRC-002 (`ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md`) |
| Supplemental Source | SRC-001 (`ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md`) |

#### A. Process Overview

Consolidation operates as a mature, centralized function at corporate. Entity-level trial balances are loaded into a central consolidation system after entity-level recons are signed off. Intercompany eliminations are executed automatically by the consolidation system against matched IC accounts. Topside entries remain fully manual at the corporate level, creating a mixed automation posture within a largely machine-driven elimination process.

The operating model is explicitly centralized: regional entities are data providers only. All consolidation judgment, IC elimination runs, topside bookings, and corporate review reside in a single central team. (`SRC-002#L33-35`)

Coverage is partial. The walkthrough covered data collection, IC eliminations, topside entries, and operating model. Equity accounting, variance analysis, and analytic-driven review were not discussed. Handoff sequencing from recon sign-off to consolidation intake is undocumented.

#### B. Summary Card

| Field | Value |
|---|---|
| Frequency | Monthly |
| Trigger | Entity close completion and recon sign-off handoff |
| Primary Role | Corporate Consolidation Team |
| Key Systems | Consolidation System (TBD — confirm system name), ERP |
| Key Outputs | Consolidated trial balance, eliminated IC balances, topside-adjusted consolidated financials |
| Approver(s) | TBD — confirm with corporate consolidation team |
| SLA / Deadline | TBD — confirm consolidation calendar targets |

#### C. Pre-Requisites

- Entity-level account reconciliations signed off by regional controllers.
- Entity trial balances finalized and available for loading.
- IC account matching configuration is current in the consolidation system.
- [[GAP — NOT DOCUMENTED]] No formal policy documenting the handoff prerequisite check exists; the sequence relies on institutional knowledge.

#### D. Data Inputs

| Input | Source | Format |
|---|---|---|
| Entity trial balances | Regional entity ERP instances | TBD — confirm file format / system submission method |
| IC account data | All entity ERP instances | TBD — confirm IC matching configuration |
| Topside entry data | Corporate finance team | Manual (spreadsheet or ERP entry) — TBD |

#### E. Step-by-Step Desktop Procedure

##### Step 1: Receive and Load Entity Trial Balances

Once entity close is complete and recon sign-offs are confirmed, each entity submits its trial balance / reconciliation package into the consolidation system. The corporate consolidation team loads or confirms receipt. (`SRC-002#L22-23`)

- **System / Tool:** Consolidation System (TBD — confirm system name)
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** Entity identifier, period, trial balance data — [[GAP — confirm submission format]]
- **Expected Result:** All entity trial balances loaded and available for elimination processing
- **Evidence Required:** [[GAP — EVIDENCE RETENTION UNKNOWN]]

> **SCREENSHOT PLACEHOLDER — SC-04:** Consolidation system entity data loading screen. User to insert screenshot showing the trial balance load or entity submission confirmation view.

##### Step 2: Run Intercompany Eliminations

IC eliminations are executed automatically within the consolidation system based on matched intercompany account configurations. The Senior Accountant described this as "fairly mature, machine-driven." (`SRC-002#L26-28`)

- **System / Tool:** Consolidation System (TBD — confirm system name)
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** IC account matching rules — [[GAP — confirm configuration]]
- **Expected Result:** Intercompany balances eliminated; elimination journal entries generated by the system
- **Evidence Required:** [[GAP — EVIDENCE RETENTION UNKNOWN]] System-generated elimination report assumed available; confirm archiving requirement

> **SCREENSHOT PLACEHOLDER — SC-05:** IC elimination run output in consolidation system. User to insert screenshot showing the elimination journal or IC balance summary post-elimination.

##### Step 3: Book Topside Entries

Topside entries are booked manually by the corporate team following IC elimination. This step represents the automation gap within the consolidation process. (`SRC-002#L26-28`; evidence tier: verbal)

[[GAP — CONTROL NOT EVIDENCED]] No documented approval, review, or segregation-of-duties control for topside entries was described in source materials. Topside entries carry material misstatement risk if uncontrolled. Confirm with corporate consolidation team. See Appendix C: GAP-0004.

- **System / Tool:** Consolidation System or ERP (TBD — confirm where topside entries are booked)
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** Account, entity, period, amount, description, approver — [[GAP — confirm required fields and approval workflow]]
- **Expected Result:** Topside entries posted to consolidated trial balance
- **Evidence Required:** [[GAP — EVIDENCE RETENTION UNKNOWN]]

> **SCREENSHOT PLACEHOLDER — SC-06:** Topside entry screen in consolidation system or ERP. User to insert screenshot showing the topside entry form.

##### Step 4: Corporate Review

Following elimination and topside posting, a corporate review of the consolidated financials occurs before final financial statements are produced.

[[GAP — NOT DOCUMENTED]] The corporate review process — scope, reviewer, system, approval mechanism, and documentation standard — was not walked through in detail. Confirm with corporate consolidation team.

- **System / Tool:** TBD
- **Navigation Path:** [[GAP — NOT DOCUMENTED]]
- **Fields / Parameters:** [[GAP — NOT DOCUMENTED]]
- **Expected Result:** Consolidated financials approved for reporting
- **Evidence Required:** [[GAP — EVIDENCE RETENTION UNKNOWN]]

##### Step 5: Equity Accounting and Variance Analysis

[[GAP — NOT DOCUMENTED]] Equity accounting and analytic-driven variance analysis were not discussed in source walkthroughs. These L3 activities are assumed to occur within or following the consolidation process. A targeted walkthrough is required. See Appendix C.

#### Exceptions / Escalations

[[GAP — NOT DOCUMENTED]] No exception or escalation procedures for the consolidation process were documented. Procedures for late entity submissions, IC imbalances, or period-reopening requests are unknown.

#### Evidence Retention Requirements

[[GAP — NOT DOCUMENTED]] No formal evidence retention requirements for consolidation activities were described in source materials. Retention requirements for elimination journals, topside entries, and corporate review approvals should be confirmed.

#### F. Key Controls

| Control ID | Control Description | Control Type | Frequency | Evidence Status |
|---|---|---|---|---|
| CTRL-CONS-01 | Automated IC elimination via matched intercompany accounts | Preventive / Detective | Monthly | Partially evidenced (verbal) — system-driven (`SRC-002#L26-28`) |
| CTRL-CONS-02 | Corporate review of consolidated financials prior to reporting | Detective | Monthly | [[GAP — CONTROL NOT EVIDENCED]] Verbal — no detail on reviewer, scope, or approval record |
| CTRL-CONS-03 | Topside entry approval or segregation of duties control | Preventive | Monthly per topside entry | [[GAP — CONTROL NOT EVIDENCED]] No control described in source materials |

**Note on CTRL-CONS-01:** IC elimination automation was confirmed verbally (evidence tier: verbal). System-observed or documentary evidence of the elimination run configuration has not been obtained.

**Note on CTRL-CONS-02 and CTRL-CONS-03:** These are verbal-tier claims only. They do not meet the Evidence DoD for evidenced controls and are logged as gaps in Appendix C.

#### G. Outputs / Deliverables

| Output | Description | Recipient | Format |
|---|---|---|---|
| Consolidated trial balance | Post-elimination, post-topside consolidated trial balance | Reporting team | TBD |
| Elimination journals | System-generated IC elimination entries | Archive / audit | Consolidation system output (TBD) |
| Consolidated financial statements | Preliminary consolidated financials for management review / reporting | TBD | TBD |

#### H. Known Issues and Pain Points

| ID | Description | Impact | Source |
|---|---|---|---|
| (see Appendix C: GAP-0004) | Topside entries fully manual at corporate level while IC eliminations are automated — inconsistent automation maturity | Manual error risk, efficiency gap | `SRC-002#L26-28` |
| (see Appendix C) | Handoff from recon sign-off to consolidation intake undocumented; relies on institutional knowledge | Sequencing risk, key-person dependency | `SRC-001#L35-36` |

---

### 5.4 Reporting

[[GAP — NOT DOCUMENTED]] This L2 process area has not been documented to date (coverage: none). No walkthrough was conducted covering management reporting, consolidated financial statement preparation, regulatory reporting, investor relations support, or close and reporting analytics. See Appendix C: GAP-STRUCT-record-to-report-reporting-no-coverage. A targeted walkthrough with the process owner is required before procedures can be drafted.

---

### 5.5 Accounting Policy

[[GAP — NOT DOCUMENTED]] This L2 process area has not been documented to date (coverage: none). No walkthrough was conducted covering the baseline accounting policies and procedures, revenue recognition (ASC 606), lease accounting (ASC 842), or new accounting standards adoption. See Appendix C: GAP-STRUCT-record-to-report-accounting-policy-no-coverage. A targeted walkthrough with the Chief Accounting Officer or VP Controller is required before procedures can be drafted.

---

## 6. Roles

| Role | Description | L2 Involvement |
|---|---|---|
| Regional Controller | Owns entity-level close; prepares and signs off account reconciliations; initiates accrual entries | Close |
| Corporate Consolidation Team | Executes IC eliminations (via system), books topside entries, performs corporate review | Consolidation |
| Senior Accountant (Corporate) | Described consolidation data collection and IC elimination process; supplemental source for close recon characterization | Consolidation |
| Department / Cost Center Owners | TBD — provide accrual input data for manual accrual workflow | Close |
| Process Owner — Pre-Close Set Up | TBD — confirm with engagement lead | Pre-Close Set Up |
| Process Owner — Reporting | TBD — confirm with engagement lead | Reporting |
| Process Owner — Accounting Policy | TBD — confirm with engagement lead (CAO / VP Controller) | Accounting Policy |

---

## 7. Systems

| System | Usage | L2 | Notes |
|---|---|---|---|
| ERP | Sub-ledger close, journal entry posting (accruals, topsides), trial balance | Close, Consolidation | System name TBD — confirm with process owner |
| Reconciliation Tool | Account reconciliation preparation and sign-off | Close | System name TBD — described as standardized with clear ownership model (`SRC-002#L30-31`) |
| Consolidation System | Entity data loading, IC elimination automation, topside entry booking (TBD) | Consolidation | System name TBD — confirm with corporate consolidation team |
| Spreadsheet Application | Accrual entry construction (current-state manual workflow) | Close | Identified as a process weakness; accrual data is re-keyed into ERP (`SRC-001#L25-27`) |

---

## 8. Cross-Reference Matrix

| L2 | Procedure / L3 | Controls | Pain Points (App. A) | Gaps (App. C) | Screenshots (App. D) | Key Outputs |
|---|---|---|---|---|---|---|
| Pre-Close Set Up | All L3 activities | N/A — not documented | N/A | GAP-STRUCT-r2r-pre-close-set-up-no-coverage | None | N/A |
| Close | Sub-Ledger Close | CTRL-CLOSE-01 | None | — | SC-01 | Locked sub-ledgers |
| Close | Manual Accrual Posting | — | PAIN-CLOSE-01 (manual accruals) | GAP-0001 | SC-02 | Posted accrual JEs |
| Close | Trial Balance Lock | CTRL-CLOSE-01 | — | — | — | Locked trial balance |
| Close | Account Reconciliations | CTRL-CLOSE-02, CTRL-CLOSE-03 | — | GAP-0002, GAP-0003 | SC-03 | Signed-off recons |
| Close | Management Review | — | — | GAP-MGMT-REVIEW (not documented) | — | TBD |
| Close | Consolidation Handoff | — | — | GAP-0003 | — | Entity close package |
| Consolidation | Entity Data Collection | — | — | — | SC-04 | Loaded trial balances |
| Consolidation | IC Eliminations | CTRL-CONS-01 | — | — | SC-05 | Elimination journals |
| Consolidation | Topside Entries | CTRL-CONS-03 | — | GAP-0004 | SC-06 | Topside-adjusted consolidated TB |
| Consolidation | Corporate Review | CTRL-CONS-02 | — | GAP-CORP-REVIEW (not documented) | — | Approved consolidated financials |
| Consolidation | Equity Accounting | — | — | GAP — not documented | — | N/A |
| Consolidation | Variance Analysis | — | — | GAP — not documented | — | N/A |
| Reporting | All L3 activities | N/A — not documented | N/A | GAP-STRUCT-r2r-reporting-no-coverage | None | N/A |
| Accounting Policy | All L3 activities | N/A — not documented | N/A | GAP-STRUCT-r2r-accounting-policy-no-coverage | None | N/A |

---

## Appendix A — Risks and Pain Points Log

> Pain points are sourced from register rows with `type: improvement` and `tag: process`. The current register for this engagement contains **no rows of type: improvement** for any Record to Report L2 node. All process weaknesses in the source material are currently typed as `gap` in the register. The following pain point is surfaced from the gap register as a process execution issue, consistent with its characterization in source materials. It is presented here for reviewer awareness; the register classification should be confirmed and updated as appropriate.

| ID | L2 | Description | Impact | Evidence Ref | Evidence Tier |
|---|---|---|---|---|---|
| PAIN-CLOSE-01 | Close | Accrual workflow is fully manual: entries built in spreadsheets and re-keyed into ERP each period. Controller's primary stated pain point; most frequent cause of late adjustments. | Close delays, elevated error risk, late adjustments | `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L25-27` | verbal |

**Note:** Appendix B (Process Improvement Opportunities) is empty because the register holds no rows of `type: improvement` for Record to Report nodes. All findings are classified as `type: gap`. If improvement recommendations exist, they should be entered into the register and will populate Appendix B on next draft cycle.

---

## Appendix B — Process Improvement Opportunities

> No rows of `type: improvement` exist in the register for any Record to Report L2 node. Appendix B is intentionally empty at this draft revision. The manual accrual workflow (GAP-0001) and manual topside entry process (GAP-0004) are candidates for improvement opportunities but are currently registered as gaps. The engagement team should evaluate whether these warrant `type: improvement` register entries for inclusion here in a subsequent draft cycle.

*No improvement opportunities registered at this time.*

---

## Appendix C — Gap / Validation Log

| Gap ID | L2 Node | Tag | Description | Recommended Action | Evidence Ref | Evidence Tier |
|---|---|---|---|---|---|---|
| GAP-STRUCT-record-to-report-pre-close-set-up-no-coverage | Pre-Close Set Up | not_documented | Node record-to-report.pre-close-set-up is empty / undocumented (coverage: none). Pre-close configuration, SOD management, close checklist, and pre-close meetings not yet documented. An empty node is itself a finding. | Schedule targeted walkthrough with Pre-Close Set Up process owner | — | — |
| GAP-CONFLICT-record-to-report-close-process | Close | unconfirmed | Cross-document conflict on `process` lens for record-to-report.close. Close walkthrough signals pain_high; recon walkthrough characterizes reconciliations as a relative strength. Lens left null pending human resolution. | Engage process owners from both sources to resolve; determine whether signals apply to overlapping or distinct sub-processes | `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L25-27`; `ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L30-31` | verbal |
| GAP-0001 | Close | not_documented | Accruals fully manual: built in spreadsheets and re-keyed into ERP monthly; primary close pain point and source of late adjustments. No automated upload or ERP-native accrual workflow exists. | Evaluate automated accrual journal upload or ERP-native accrual workflow | `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L25-27` | verbal |
| GAP-0002 | Close | control_not_evidenced | Dual-reviewer control for reconciliations above $50K is operated in practice but is not documented in policy or enforced by system configuration. Exists in institutional memory only. Key-person dependency and audit risk. [[GAP — CONTROL NOT EVIDENCED]] | Document the control in policy; configure system enforcement in the reconciliation tool; validate with internal audit | `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L35-36` | verbal |
| GAP-0003 | Close | not_documented | Reconciliation sign-off decentralized across regional controllers with no central oversight layer described. Risk depends on per-region control quality, which has not been assessed. Handoff from recon sign-off to consolidation intake is also undocumented. | Assess central oversight model; document handoff sequencing in policy or system workflow | `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L27-28` | verbal |
| GAP-STRUCT-record-to-report-close-incomplete-diagnosis | Close | unconfirmed | Node record-to-report.close diagnosis incomplete: `process` and `capability` lenses are null. Process lens blocked by cross-document conflict (see GAP-CONFLICT above); capability lens requires additional evidence on staffing and skill mix. | Resolve process lens conflict; conduct capability-focused interview | — | — |
| GAP-STRUCT-record-to-report-close-sop-not-started | Close | not_documented | Node record-to-report.close was covered enough to draft SOP — resolved by this document. Retained for traceability. | Resolved by this SOP draft | — | — |
| GAP-0004 | Consolidation | unconfirmed | Topside entries booked manually by corporate while IC eliminations are fully automated — inconsistent automation maturity within consolidation. No documented approval or SOD control for topside entries was described. [[GAP — CONTROL NOT EVIDENCED]] | Assess whether topside entry types / volumes are candidates for systemization in the consolidation tool; document topside entry approval control | `ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L26-28` | verbal |
| GAP-STRUCT-record-to-report-consolidation-incomplete-diagnosis | Consolidation | unconfirmed | Node record-to-report.consolidation diagnosis incomplete: `process` and `capability` lenses are null. Requires additional walkthrough coverage of equity accounting, variance analysis, and consolidation procedures. | Schedule follow-up walkthrough with corporate consolidation team | — | — |
| GAP-STRUCT-record-to-report-consolidation-sop-not-started | Consolidation | not_documented | Node record-to-report.consolidation was covered enough to draft SOP — resolved by this document. Retained for traceability. | Resolved by this SOP draft | — | — |
| GAP-STRUCT-record-to-report-reporting-no-coverage | Reporting | not_documented | Node record-to-report.reporting is empty / undocumented (coverage: none). Management reporting, consolidated financial statements, regulatory reporting, investor relations, and analytics not yet documented. An empty node is itself a finding. | Schedule targeted walkthrough with Reporting process owner | — | — |
| GAP-STRUCT-record-to-report-accounting-policy-no-coverage | Accounting Policy | not_documented | Node record-to-report.accounting-policy is empty / undocumented (coverage: none). Baseline policies, ASC 606, ASC 842, and new standards adoption not yet documented. An empty node is itself a finding. | Schedule targeted walkthrough with Chief Accounting Officer or VP Controller | — | — |
| GAP-MGMT-REVIEW-close | Close | not_documented | Management review step noted as occurring after reconciliation sign-off (`SRC-001#L41`) but not walked through. Reviewer, scope, system, and approval mechanism are unknown. | Document management review procedure in follow-up walkthrough | `ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L41` | verbal |
| GAP-CONS-EQUITY-VARIANCE | Consolidation | not_documented | Equity accounting and variance analysis / analytic-driven review not covered in source walkthroughs. Assumed to occur within or following the consolidation process. | Include in follow-up consolidation walkthrough | — | — |
| GAP-CONS-TOPSIDE-CTRL | Consolidation | control_not_evidenced | No approval, review, or segregation-of-duties control for topside entries was described in source materials. Topside entries carry material misstatement risk if uncontrolled. [[GAP — CONTROL NOT EVIDENCED]] | Confirm with corporate consolidation team whether topside entry approval control exists; document or implement as appropriate | `ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L26-28` | verbal |

**Evidence DoD Note:** All control claims in this document are backed by verbal-tier evidence only. No documentary or system-observed evidence has been obtained for any control in the Record to Report cycle. All controls are therefore presented as [[GAP — CONTROL NOT EVIDENCED]] or pending validation.

---

## Appendix D — Screenshot / Evidence Index

| Screenshot ID | L2 | Location in Document | Caption | Status |
|---|---|---|---|---|
| SC-01 | Close | §5.2.E Step 1 | Sub-ledger close confirmation screen in ERP showing period-end AP/AR close | Pending user input |
| SC-02 | Close | §5.2.E Step 2 | Accrual journal entry form in ERP with representative fields | Pending user input |
| SC-03 | Close | §5.2.E Step 4 | Reconciliation sign-off screen in reconciliation tool | Pending user input |
| SC-04 | Consolidation | §5.3.E Step 1 | Consolidation system entity data loading / submission confirmation screen | Pending user input |
| SC-05 | Consolidation | §5.3.E Step 2 | IC elimination run output / IC balance summary post-elimination | Pending user input |
| SC-06 | Consolidation | §5.3.E Step 3 | Topside entry screen in consolidation system or ERP | Pending user input |

---

*End of Document — Record to Report SOP v0.1 Draft*
*Generated by CONSULT pipeline Stage 5A — 2026-06-21*
