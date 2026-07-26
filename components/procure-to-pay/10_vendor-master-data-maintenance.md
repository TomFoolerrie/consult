## Vendor Master Data Maintenance

### A. Process Overview

Vendor Master Data Maintenance is the ongoing stewardship of the NetSuite
vendor master — the system of record for the supplier from a payment
standpoint — once a supplier has been established through
[[new-vendor-onboarding]] (SRC-002). The Accounts Payable Clerk, as holder of
the NetSuite Vendor Maintenance role, corrects records that arrive incomplete
from the nightly Coupa-to-NetSuite supplier sync and enters non-banking
changes to existing vendor records; the prior AP SOP additionally requires a
semi-annual review of the supplier master file, performed by the Accounts
Payable Manager and reported to the Corporate Controller (SRC-001, SRC-002,
SRC-006). The procedure runs ad hoc, as sync fallout and change requests
arise. Changes to a supplier's remit-to banking details are excluded — they
follow the callback-and-approval regime under [[vendor-banking-change]].
Downstream, invoice matching and every disbursement, including
[[weekly-payment-run]], transact against the data this procedure keeps
accurate, and the segregation between vendor-record maintenance and payment
release is one of the three procure-to-pay controls in the external auditors'
scope (SRC-003).

### B. Quick Reference

- **Trigger:** A supplier record lands from the nightly Coupa-to-NetSuite sync with incomplete data (typically a blank payment term); a non-banking change to an existing vendor record is requested; the semi-annual master file review falls due (SRC-002, SRC-005, SRC-006).
- **Frequency:** Ad hoc for sync corrections and record changes; semi-annual for the master file review (per the prior SOP — operation unconfirmed, see GAP-03).
- **Preparer:** Accounts Payable Clerk (holder of the NetSuite Vendor Maintenance role) (SRC-001, SRC-003).
- **Reviewer:** Accounts Payable Manager (semi-annual master file review, §9.5 of the prior AP SOP, SRC-006); for individual record changes, TBD — no independent review of non-banking changes was described (see GAP-02).
- **Primary systems / tools:** NetSuite (vendor master); Coupa (sourcing-side supplier record; nightly sync into NetSuite).
- **Key outputs:** Corrected, complete vendor records in NetSuite; semi-annual master file review results reported to the Corporate Controller (per the prior SOP).

### C. Pre-Requisites

- The supplier exists as a NetSuite vendor record, created through [[new-vendor-onboarding]] (SRC-002).
- The person entering changes holds the NetSuite Vendor Maintenance role and holds no payment preparation, payment approval, or banking portal entitlements (SRC-003; §9.3 of the prior AP SOP, SRC-006).
- For sync-fallout corrections: the nightly Coupa-to-NetSuite supplier sync has run (SRC-002).
- Any request touching remit-to banking details has been separated out for processing under [[vendor-banking-change]] — it is not handled here.

### D. Inputs

- **Newly synced supplier records:** pushed from Coupa into NetSuite by the nightly supplier sync, including any that arrive with a blank payment term — source: Coupa (SRC-002, SRC-005).
- **Non-banking change requests:** requested changes to an existing vendor's master data other than remit-to banking details; how these requests arrive was not established (see GAP-02).
- **The NetSuite supplier master file:** the population reviewed semi-annually for inactive, duplicate and incomplete records (§9.5 of the prior AP SOP, SRC-006).

### E. Step-by-Step Procedure

#### Step 1: Identify the record requiring maintenance

Maintenance work arises from two recurring triggers: fallout from the nightly
Coupa-to-NetSuite supplier sync — records that land in NetSuite with a blank
payment term (SRC-002, SRC-005) — and requested changes to an existing
vendor's non-banking master data. Screen every incoming request first: if it
touches the supplier's remit-to banking details in any way, stop and process
it under [[vendor-banking-change]], which requires callback verification and
second-person approval. No monitoring or alerting exists on the sync, so how
mis-synced records come to the Accounts Payable Clerk's attention is
unconfirmed [[GAP-01 — SYNC-FALLOUT DETECTION]] (SRC-005).

- **System / Tool:** NetSuite (vendor master); Coupa-to-NetSuite nightly supplier sync.
- **Expected Result:** The record requiring correction or change is identified; banking-detail requests are routed out of this procedure.

> **VALIDATION REQUIRED — GAP-01:** How records damaged by the nightly Coupa-to-NetSuite supplier sync are detected for correction. The sync has no monitoring, alerting, or named owner, and no source describes how the Accounts Payable Clerk learns that a record has landed with a blank payment term (SRC-002, SRC-005).
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Correct sync-fallout records

The Accounts Payable Clerk corrects by hand records that synced from Coupa
with a blank payment term, entering the payment term on the NetSuite vendor
record (SRC-002, SRC-005). The terms entered should reflect what was agreed
with the supplier — payment terms are initially set during NetSuite
activation under [[new-vendor-onboarding]] (SRC-002).

- **System / Tool:** NetSuite (vendor master).
- **Fields / Parameters:** Payment terms (blank on arrival).
- **Expected Result:** The vendor record carries a valid payment term before transactions process against it.

> **SCREENSHOT PLACEHOLDER — SC-01:** A NetSuite vendor record corrected after a sync failure, showing the populated payment terms field; must validate that manually corrected records carry complete payment terms.

#### Step 3: Enter non-banking changes to an existing vendor record

The Accounts Payable Clerk enters the requested change on the vendor's
NetSuite record. Additions and modifications to the supplier master record
are restricted to holders of the Vendor Maintenance role — the
segregation-of-duties control described in F — and the role carries no
payment permissions (SRC-003; §9.3 of the prior AP SOP, SRC-006). The intake,
approval, and evidence requirements for non-banking changes were not
established in fieldwork; the documented verification-and-approval regime
applies only to banking changes
[[GAP-02 — NON-BANKING CHANGE WORKFLOW]] (SRC-002, SRC-003).

- **System / Tool:** NetSuite (vendor master).
- **Evidence Required:** TBD — confirm with process owner (see GAP-02).

> **VALIDATION REQUIRED — GAP-02:** The workflow for non-banking changes to existing vendor records: how requests arrive, whether any approval is required before or after entry, what evidence of the change is retained, and whether the corresponding Coupa supplier record is also updated. Sources describe a verification-and-approval regime only for banking-detail changes (SRC-002, SRC-003).
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite role configuration for the Vendor Maintenance role; must validate that the role carries no payment preparation, payment approval, or banking portal permissions.

#### Step 4: Perform the semi-annual supplier master file review

Per §9.5 of the prior AP SOP, the Accounts Payable Manager reviews the
supplier master file semi-annually for inactive, duplicate and incomplete
records and reports the results to the Corporate Controller (SRC-006).
Fieldwork found no evidence that this review currently operates — no
interviewee described it — and the state of the record population (see PP-001
in H) indicates it has not been effective
[[GAP-03 — SEMI-ANNUAL REVIEW]] (SRC-005).

- **System / Tool:** NetSuite (vendor master).
- **Expected Result:** Review results reported to the Corporate Controller (§9.5 of the prior AP SOP).
- **Evidence Required:** TBD — no reporting format or retention location is described (see GAP-03).

> **VALIDATION REQUIRED — GAP-03:** Whether the semi-annual supplier master file review required by §9.5 of the prior AP SOP is performed at all — and if so, by whom, in what form its results are reported to the Corporate Controller, and what remediation (deactivation, merge, completion of records) follows. No evidence of the review was identified in fieldwork and no interviewee confirmed it (SRC-005, SRC-006).
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

### F. Key Controls

> **CONTROL — CTRL-001:** Segregation of duties over the vendor master — additions and modifications to the supplier master record are performed only by personnel holding the Vendor Maintenance role, which must not carry payment preparation, payment approval, or banking portal entitlements (§9.3 of the prior AP SOP, SRC-006). In the current state the role is held by the Accounts Payable Clerk, who has no payment permissions in NetSuite — cannot approve a bill and cannot access the Pay Bills screen — while payment-run preparation sits with the Accounts Payable Manager and run approval and bank release with the Corporate Controller (SRC-003). This segregation is one of the three procure-to-pay controls in the external auditors' scope; known deviations from the role restriction are recorded in H (SRC-003).
> - **Type:** Preventive
> - **Frequency:** Continuous (role-based)
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-002:** Semi-annual supplier master file review — the Accounts Payable Manager reviews the supplier master file for inactive, duplicate and incomplete records and reports the results to the Corporate Controller (§9.5 of the prior AP SOP, SRC-006). No evidence that the review currently operates was identified in fieldwork; the validation is raised at Step 4 in E (SRC-005).
> - **Type:** Detective
> - **Frequency:** Semi-annual (per the prior SOP; operation unconfirmed)
> - **Owner:** Accounts Payable Manager

### G. Outputs

- **Corrected, complete vendor master records in NetSuite** — every downstream payable and payment activity transacts against them, including invoice matching and [[weekly-payment-run]] (SRC-002, SRC-003).
- **Semi-annual master file review results** reported to the Corporate Controller (§9.5 of the prior AP SOP, SRC-006; operation unconfirmed — see GAP-03).
- **Evidence retained:** TBD — no evidence requirements were described for sync corrections or non-banking record changes (see GAP-02), and no reporting or retention location for the master file review is described (see GAP-03).

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The supplier master population has degraded without an operating hygiene process: roughly 11,000 vendor records exist, only about 4,000 of which have been active in the last 24 months, with some vendors present multiple times under different spellings; there is no de-duplication project and no owner of the cleanup — the Procurement Lead has carried it as an unactioned to-do — and the semi-annual file review that should catch inactive, duplicate and incomplete records is not evidenced as operating (SRC-002, SRC-005, SRC-006).
> - **Impact:** Duplicate and stale records fragment spend history, make the onboarding duplicate check unreliable, and expand the surface for duplicate or misdirected payments; the Corporate Controller flagged an 11,000-record master file with no owner as a material exposure (SRC-002, SRC-003).
> - **Severity:** High

> **PAIN POINT — PP-002:** Vendor master maintenance has no dedicated owner — it is performed by the Accounts Payable Clerk between other duties (non-PO invoice entry, credit card statements), and the Corporate Controller explicitly asked for the vendor master to be owned "as a real job" (SRC-001, SRC-003).
> - **Impact:** Hygiene tasks — de-duplication, the semi-annual file review, sync-failure resolution — have no accountable owner and do not happen systematically (SRC-003, SRC-005).
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Vendor record edit access extends beyond the Vendor Maintenance role: the Assistant Controller holds emergency edit access, the NetSuite administrator role held by the IT Manager can edit vendor records, and a legacy implementation-partner login remains active and unremediated — a deviation from §9.3 of the prior AP SOP, which restricts edits to the Vendor Maintenance role (SRC-003, SRC-005, SRC-006).
> - **Impact:** Vendor records — including remit-to details — could be modified outside the maintained change paths, undermining an auditor-scoped segregation-of-duties control (SRC-003).
> - **Severity:** High

> **PAIN POINT — PP-004:** The holder of the Vendor Maintenance role also enters non-PO invoices, concentrating vendor-record edit and invoice entry in one pair of hands — a segregation-of-duties concern flagged in fieldwork (SRC-001, SRC-005).
> - **Impact:** One person could both modify a vendor record and enter a non-PO invoice against it; compensating separation remains at payment approval and release, which the role does not hold (SRC-003, SRC-005).
> - **Severity:** Medium

> **PAIN POINT — PP-005:** Records damaged by the intermittently failing nightly Coupa-to-NetSuite supplier sync (blank payment terms) are found and fixed by hand, with no monitoring, alerting, or named interface owner (SRC-002, SRC-005).
> - **Impact:** Each failure consumes roughly an hour each for three people, and a record can sit incomplete until noticed (SRC-002, SRC-005).
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Run a dedicated supplier master de-duplication and cleanup project with a named owner, reducing the roughly 11,000-record population to the genuinely active supplier base (SRC-002, SRC-003).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish vendor master ownership as a defined responsibility rather than a task performed between other duties, and re-operationalize the semi-annual master file review with retained evidence of its performance and results (SRC-003, SRC-006).
> - **Addresses:** PP-002, PP-001

> **IMPROVEMENT OPPORTUNITY — IO-003:** Deactivate the legacy implementation-partner login and re-examine the remaining vendor-edit access outside the Vendor Maintenance role — the Assistant Controller's emergency access and the NetSuite administrator role — against the restriction in §9.3 of the prior AP SOP (SRC-003, SRC-005, SRC-006).
> - **Addresses:** PP-003

```consult-meta
systems: [netsuite, coupa]
roles:   [ap-clerk, ap-manager, corporate-controller, assistant-controller, it-manager, procurement-lead]
```
