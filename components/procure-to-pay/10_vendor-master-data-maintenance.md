## Vendor Master Data Maintenance

<!-- scope note: covers variants — Record activation and payment-term setup after Coupa sync; Semi-annual supplier master file review (inactive / duplicate / incomplete). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### A. Process Overview

This procedure covers the ongoing maintenance of the vendor master in NetSuite, the
system of record for the vendor master for payment purposes, once a supplier record
exists. It has two triggers: the activation and payment-term setup of a record that
has arrived in NetSuite through the nightly synchronization from Coupa, performed on
demand as records land; and the periodic review of the supplier master file for
inactive, duplicate and incomplete records, specified as a semi-annual exercise. Both
are performed under the NetSuite Vendor Maintenance role, held by the Accounts
Payable Clerk, with the results of the periodic review reported to the Corporate
Controller. The supplier request, diligence and approval that precede a record's
arrival are covered by [[new-vendor-onboarding]]; changes to a supplier's remittance
banking are excluded here and covered by [[vendor-banking-change]]. (SRC-002,
SRC-003, SRC-005, SRC-006)

### B. Quick Reference

- **Trigger:** A supplier record arrives in NetSuite via the nightly Coupa synchronization and requires activation; or the semi-annual supplier master file review falls due.
- **Frequency:** On demand for activation; semi-annually for the master file review.
- **Preparer:** Accounts Payable Clerk (activation and record maintenance); Accounts Payable Manager (semi-annual master file review).
- **Reviewer:** Corporate Controller (recipient of the semi-annual review results).
- **Primary systems / tools:** NetSuite; Coupa (the source of the synchronized record).
- **Key outputs:** Active NetSuite vendor record with payment terms and default GL account set; semi-annual supplier master file review results reported to the Corporate Controller.

### C. Pre-Requisites

- The supplier record has been approved in Coupa and has synchronized into NetSuite (see [[new-vendor-onboarding]]).
- The person performing the maintenance holds the NetSuite Vendor Maintenance role and holds no payment preparation, payment approval, or banking portal entitlements.
- For the periodic review, the supplier master file is available for extract from NetSuite.

### D. Inputs

- **Synchronized supplier record (NetSuite):** Coupa, delivered by the nightly supplier synchronization. Carries the approved supplier data from the Coupa record.
- **Supplier master file (NetSuite):** NetSuite. Approximately 11,000 supplier records, of which roughly 4,000 have transacted in the last twenty-four months.
- **NetSuite entitlement listing for vendor edit rights:** IT Manager, in the NetSuite administrator role.
- **Prior SOP requirements (AP Invoice Processing, v3, sections 9.3 and 9.5):** The documented requirements for restriction of the Vendor Maintenance role and for the semi-annual master file review.

### E. Step-by-Step Procedure

#### Step 1: Identify the records requiring maintenance

The population depends on the trigger. For record activation, the population is the
supplier records delivered into NetSuite by the overnight Coupa synchronization since
the last pass. For the semi-annual master file review, the population is the full
supplier master file, reviewed for inactive, duplicate and incomplete records.

- **System / Tool:** NetSuite
- **Expected Result:** A defined set of vendor records is in scope for the pass.

> **VALIDATION REQUIRED — GAP-01:** How the Accounts Payable Clerk is notified that new supplier records have landed in NetSuite, and how a record synchronized with a blank payment term is identified for correction. Sources describe the synchronization and the manual correction but describe no report, queue, or notification by which either is detected.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Confirm the maintenance is performed under the Vendor Maintenance role

Additions and modifications to the supplier master record are performed only by
personnel holding the NetSuite Vendor Maintenance role, who hold no payment
preparation, payment approval, or banking portal entitlements. The Accounts Payable
Clerk holds this role and has no payment permissions — the Clerk can neither approve
a bill nor operate the Pay Bills screen. Vendor edit rights in NetSuite also sit with
the Assistant Controller on an emergency basis and with the NetSuite administrator
role held by the IT Manager, and a legacy implementation-partner login retains access
— see [[GAP-04 — VENDOR EDIT ACCESS POPULATION]].

- **System / Tool:** NetSuite
- **Expected Result:** The record is edited by an entitled preparer with no payment entitlements.

> **VALIDATION REQUIRED — GAP-04:** The complete population of NetSuite entitlements carrying vendor edit rights, and whether that population is reviewed on any cadence. Sources state that a legacy implementation-partner login remains live and that the Corporate Controller is aware of it but that it has not been remediated; sources do not state whether vendor record edits made under the NetSuite administrator role or under the Assistant Controller's emergency access are logged, reviewed, or restricted to defined circumstances.
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager

> **VALIDATION REQUIRED — GAP-05:** Whether any compensating review addresses the Accounts Payable Clerk holding both vendor master maintenance and non-PO invoice entry. The two activities in one pair of hands allow a vendor record and a payable against it to originate with the same preparer; sources record the combination but describe no detective review over it.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite role and permission listing for the Vendor Maintenance role and for every role carrying vendor edit rights, to validate which entitlements permit vendor edit and that none of them also carries payment approval or payment release.

#### Step 3: Activate the record and set payment terms and default GL account

*Activation variant.* The Accounts Payable Clerk activates the synchronized vendor
record and sets the payment terms and the default GL account. Standard payment terms
are net 45; net 60 is sought on new suppliers. Records that arrive from the
synchronization with a blank payment term are corrected manually at this point.

- **System / Tool:** NetSuite
- **Fields / Parameters:** Vendor status (active); payment terms (standard net 45); default GL account.
- **Expected Result:** The vendor record is active and transactable for requisitioning and payment.

#### Step 4: Review the supplier master file for inactive, duplicate and incomplete records

*Periodic review variant.* A review of the supplier master file for inactive,
duplicate and incomplete records is performed semi-annually by the Accounts Payable
Manager. The review is a documented requirement of the prior SOP; no participant was
able to describe it being performed — see [[GAP-02 — SEMI-ANNUAL REVIEW OPERATION]].

- **System / Tool:** NetSuite
- **Expected Result:** Inactive, duplicate and incomplete supplier records are identified for disposition.

> **VALIDATION REQUIRED — GAP-02:** Whether the semi-annual supplier master file review required by section 9.5 of the prior SOP is performed. The SOP specifies the review and its owner; no interview participant described performing or receiving it, and no evidence of a completed review was identified.
> - **Nature:** conflict
> - **Owner to confirm:** Accounts Payable Manager

> **VALIDATION REQUIRED — GAP-03:** The criteria applied in the review to classify a record as inactive, duplicate or incomplete, the disposition applied to each (deactivation, merge, completion), and who approves a deactivation or merge. Sources state the review's subject matter but describe no method or disposition path.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 5: Report the review results to the Corporate Controller

*Periodic review variant.* The results of the master file review are reported to the
Corporate Controller. The form, content and retention of that reporting are TBD —
confirm with process owner, contingent on [[GAP-02 — SEMI-ANNUAL REVIEW OPERATION]].

- **Expected Result:** The Corporate Controller receives the review results.
- **Evidence Required:** TBD — confirm with process owner.

> **SCREENSHOT PLACEHOLDER — SC-02:** The output of a completed supplier master file review as reported to the Corporate Controller, to validate that the review is performed, what it covers, and what is retained as evidence of it.

### F. Key Controls

> **CONTROL — CTRL-001:** Segregation of duties over the vendor master — additions and modifications to the supplier master record are made only by personnel holding the NetSuite Vendor Maintenance role, and that role carries no payment preparation, payment approval, or banking portal entitlement. The Accounts Payable Clerk holding the role can neither approve a bill nor operate the payment run.
> - **Type:** Preventive
> - **Frequency:** Continuous (entitlement-based)
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-002:** Supplier master file review — the supplier master file is reviewed for inactive, duplicate and incomplete records and the results are reported to the Corporate Controller. Operation of this control is unconfirmed; see Step 4.
> - **Type:** Detective
> - **Frequency:** Semi-annual
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-003:** Activation completeness — a synchronized vendor record is set to active only once payment terms and a default GL account have been recorded, so that a record arriving from the synchronization with a blank payment term is corrected before the vendor transacts.
> - **Type:** Preventive
> - **Frequency:** Each synchronized record
> - **Owner:** Accounts Payable Clerk

### G. Outputs

- **Active NetSuite vendor record:** Payment terms and default GL account set; the vendor becomes transactable for requisitioning and payment.
- **Supplier master file review results:** Reported to the Corporate Controller; form and retention TBD — confirm with process owner.
- **Evidence retained:** TBD — confirm with process owner. Sources describe no evidence retained for record activation or for the master file review.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The vendor master has no dedicated owner. Maintenance is performed by the Accounts Payable Clerk alongside other duties rather than as a defined role.
> - **Impact:** Data quality and access hygiene over an approximately 11,000-record master are not actively managed. The Corporate Controller named establishing real ownership of the vendor master as one of three top priorities.
> - **Severity:** High

> **PAIN POINT — PP-002:** The semi-annual supplier master file review for inactive, duplicate and incomplete records is required by the prior SOP but no participant could describe it being performed and no evidence of a completed review was identified.
> - **Impact:** A documented periodic control over an approximately 11,000-record master — of which roughly 4,000 have transacted in the last twenty-four months — cannot be evidenced, and inactive and incomplete records accumulate without remediation.
> - **Severity:** High

> **PAIN POINT — PP-003:** Vendor edit rights in NetSuite extend beyond the Vendor Maintenance role: the Assistant Controller holds them for emergency use, the NetSuite administrator role held by the IT Manager carries them, and a legacy implementation-partner login from the system implementation remains live.
> - **Impact:** The segregation of duties asserted over the vendor master is narrower in practice than the entitlement population supports. The implementation-partner login is a third-party credential outside the Company's role design; the Corporate Controller is aware of it and it has not been remediated.
> - **Severity:** High

> **PAIN POINT — PP-004:** The Accounts Payable Clerk who holds vendor master maintenance also performs non-PO invoice entry.
> - **Impact:** A vendor record and a payable raised against it can originate with the same preparer, without a detective review described over the combination.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Establish vendor master data ownership as a defined role, with accountability for activation standards, record completeness, the periodic review cadence, and the entitlement population permitted to edit vendor records.
> - **Addresses:** PP-001, PP-002

> **IMPROVEMENT OPPORTUNITY — IO-002:** Operationalize the supplier master file review — define the inactive, duplicate and incomplete criteria, the disposition and approval path for deactivation and merge, and a retained reporting deliverable to the Corporate Controller — so the control can be evidenced rather than asserted.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Perform a vendor master access review: revoke the legacy implementation-partner login, restrict emergency and administrator-role vendor edit to defined circumstances, and log and review edits made outside the Vendor Maintenance role on a set cadence.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-004:** Separate vendor master maintenance from non-PO invoice entry, or where headcount does not permit separation, implement a detective review of vendor records created or modified by a preparer who also enters invoices against them.
> - **Addresses:** PP-004

```consult-meta
systems: [netsuite, coupa]
roles:   [ap-clerk, ap-manager, corporate-controller, assistant-controller, it-manager, supplier, implementation-partner]
```
