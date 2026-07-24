## Vendor Banking Change

### A. Process Overview

This procedure governs a change to the remit-to bank account held on an existing
supplier's vendor master record in NetSuite, the system of record for the vendor
master for payment purposes. It is performed on demand, on receipt of a request
from a supplier — typically an email stating that the supplier has changed banks.
The change is verified by a telephone callback to a contact number already held on
the vendor record, documented on that record, and approved by a second person
before it takes effect. Initial creation of a supplier and its first banking
details is out of scope and is covered by [[new-vendor-onboarding]], where banking
is supplier-entered through the Coupa Supplier Information Management portal rather
than changed by Company personnel; non-banking changes to the vendor record are
covered by [[vendor-master-data-maintenance]]. Ownership of the callback is
currently contested across sources and is unresolved — see Step 3.
(SRC-002, SRC-003, SRC-005, SRC-006)

### B. Quick Reference

- **Trigger:** A supplier requests a change to its remit-to bank account, ordinarily by email.
- **Frequency:** On demand.
- **Preparer:** TBD — confirm with process owner (the role performing the callback and keying the change is disputed across sources; see GAP-01).
- **Reviewer:** A second person approves the change before it goes active; the specific role is TBD — confirm with process owner (see GAP-02).
- **Primary systems / tools:** NetSuite (vendor master); telephone callback; AP Inbox (request receipt).
- **Key outputs:** Updated remit-to bank details on the NetSuite vendor record; documented callback note and attachment; second-person approval.

### C. Pre-Requisites

- An active vendor record exists in NetSuite for the supplier.
- A supplier contact telephone number is already held on the vendor master record, independent of the change request.
- The person performing the change holds the NetSuite Vendor Maintenance role and, per the segregation-of-duties rule in F, holds no payment preparation, payment approval, or banking portal entitlements.

### D. Inputs

- **Supplier banking change request:** Supplier, ordinarily received by email into the AP Inbox.
- **Contact telephone number on file:** NetSuite vendor master record — the number used for the callback, deliberately not a number supplied in the request.
- **Existing vendor record:** NetSuite, holding the current remit-to bank details being superseded.

### E. Step-by-Step Procedure

#### Step 1: Receive and log the change request

A request to change the supplier's remit-to bank account is received from the
supplier. Sources describe these requests arriving by email and being directed to
Accounts Payable.

- **System / Tool:** AP Inbox
- **Expected Result:** The request is identified as a banking change and held pending verification; the request is not actioned in NetSuite at this point.

> **VALIDATION REQUIRED — GAP-03:** The intake path for a banking change request — whether such requests are routed to a specific queue or role, tracked, or acknowledged to the supplier, and how a request arriving through a channel other than the AP Inbox (for example directly to a Buyer) is handled. Sources describe requests arriving by email but describe no intake handling.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Identify the callback number from the vendor master record

The telephone number used for verification is taken from the supplier record already
held in NetSuite. A number appearing in the change request itself is not used. This
is the operative point of the control: the verification must reach the supplier
through a channel the requester could not have supplied.

- **System / Tool:** NetSuite
- **Fields / Parameters:** Supplier contact telephone number as held on the vendor master record.
- **Expected Result:** A callback number sourced from the vendor record, not from the request, is identified.

> **VALIDATION REQUIRED — GAP-04:** The handling where no contact telephone number is held on the vendor record, or where the number on file is stale or unreachable. No alternative verification path was described in the sources.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 3: Perform and document the verification callback

A telephone callback is placed to the number identified in Step 2 to confirm the
banking change with the supplier. The callback is documented with the date, the
time, the person spoken to, and what was confirmed, and that documentation is
recorded as a note plus an attachment on the vendor record in NetSuite. Ownership
of this callback is stated differently by every source — see
[[GAP-01 — CALLBACK OWNER]] — and until it is resolved the performing role cannot
be stated.

- **System / Tool:** NetSuite (vendor record note and attachment); telephone
- **Fields / Parameters:** Callback date; callback time; person spoken to; what was confirmed.
- **Expected Result:** The supplier confirms the banking change through the number on file, and the verification is evidenced on the vendor record.
- **Evidence Required:** Callback note and supporting attachment on the NetSuite vendor record.

> **VALIDATION REQUIRED — GAP-01:** Which role performs and owns the verification callback. The Corporate Controller states that Procurement owns it, on the basis that Procurement holds the supplier relationship and the real contacts; the Procurement Lead states that Accounts Payable performs it, specifically the Accounts Payable Clerk; the 2023 SOP (section 9.4) requires it to be performed by an Accounts Payable Specialist. The Corporate Controller indicated the written policy may never have been operationalized. The as-configured and as-practised owner must be established before this step can be documented.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite vendor record notes and attachments pane showing a completed callback note, to validate the documented fields (date, time, person spoken to, confirmation) and that the evidence is retained on the record.

#### Step 4: Obtain second-person approval

A second person approves the banking change before it becomes active. The role
holding this approval is not stated in any source — see
[[GAP-02 — SECOND APPROVER]].

- **System / Tool:** NetSuite
- **Expected Result:** The change is approved by a person other than the one who performed the callback and keyed the change.
- **Evidence Required:** TBD — confirm with process owner. Sources state that a second approval occurs but do not describe how it is evidenced.

> **VALIDATION REQUIRED — GAP-02:** The identity of the required second approver on a vendor banking change, and the mechanism by which the approval is captured (NetSuite workflow, email, or manual record). No source states the role; the Corporate Controller speculated that it may be her, and separately that the Accounts Payable Clerk may be performing the callback and treating her as the second approver.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 5: Update the remit-to bank details in NetSuite

The remit-to bank account on the vendor master record is updated. The update is
performed by a holder of the Vendor Maintenance role, which per the
segregation-of-duties control in F carries no payment preparation, payment
approval, or banking portal entitlement.

- **System / Tool:** NetSuite
- **Fields / Parameters:** Vendor remit-to bank account details.
- **Expected Result:** The vendor record carries the new remit-to bank account and subsequent payments are directed to it.

> **VALIDATION REQUIRED — GAP-05:** Whether the callback and the second approval are enforced as system prerequisites in NetSuite before the bank detail fields can be saved, or whether the sequence is procedural only and the fields can be edited at any time by a Vendor Maintenance role holder.
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite vendor record banking detail fields together with any approval or audit-trail indicator, to validate how the change and its approval are recorded on the record.

### F. Key Controls

> **CONTROL — CTRL-001:** Verification callback — any change to a supplier's remit-to bank account is verified by telephone callback to a contact number already held on the vendor master record, and never to a number supplied in the change request. The callback is documented with date, time, person spoken to, and what was confirmed, retained as a note and attachment on the NetSuite vendor record.
> - **Type:** Preventive
> - **Frequency:** Each banking change request
> - **Owner:** TBD — confirm with process owner (disputed; see GAP-01)

> **CONTROL — CTRL-002:** Second-person approval — a second person approves the banking change before it becomes active on the vendor record.
> - **Type:** Preventive
> - **Frequency:** Each banking change request
> - **Owner:** TBD — confirm with process owner (see GAP-02)

> **CONTROL — CTRL-003:** Segregation of duties over the vendor master — personnel holding the NetSuite Vendor Maintenance role hold no payment preparation, payment approval, or banking portal entitlements, so the individual who can change remit-to banking cannot release funds to it. This is one of the three Procure to Pay controls in the external audit scope.
> - **Type:** Preventive
> - **Frequency:** Continuous (entitlement-based)
> - **Owner:** Corporate Controller

### G. Outputs

- **Updated NetSuite vendor record:** Carries the new remit-to bank account; subsequent disbursements in [[weekly-payment-run]] and [[wire-and-manual-payment]] pay to the updated details.
- **Callback documentation:** Note and attachment on the NetSuite vendor record recording date, time, person spoken to, and what was confirmed.
- **Evidence retained:** Callback note and attachment on the NetSuite vendor record. The retention basis and period for banking-change evidence specifically were not stated in the sources — TBD — confirm with process owner.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Ownership of the verification callback is not settled. The Corporate Controller understands Procurement performs it, the Procurement Lead understands Accounts Payable performs it, and the 2023 SOP assigns it to an Accounts Payable Specialist. The Corporate Controller acknowledged that the policy as written may never have been operationalized.
> - **Impact:** A control in the audit-adjacent vendor master population has no confirmed owner, so there is no assurance it is performed consistently, and no single role is accountable when it is not.
> - **Severity:** High

> **PAIN POINT — PP-002:** Evidence of the banking change control is not readily producible. The Corporate Controller stated she wants the control operating as written with evidence she can hand an auditor without exchanging several emails first.
> - **Impact:** Audit and quarterly review support must be assembled reactively; the control cannot currently be demonstrated on demand.
> - **Severity:** High

> **PAIN POINT — PP-003:** Vendor edit access in NetSuite extends beyond the designated Vendor Maintenance role. It is additionally held by the Assistant Controller for emergency use, by the NetSuite administrator role held by the IT Manager, and through a legacy implementation partner login that remains active and unremediated.
> - **Impact:** The population able to change remit-to banking is wider than the segregation-of-duties control contemplates, and the implementation partner login is an access path outside the Company.
> - **Severity:** High

> **PAIN POINT — PP-004:** The vendor master has no dedicated owner; maintenance is performed by the Accounts Payable Clerk alongside other duties.
> - **Impact:** Banking changes are actioned as incidental work rather than under a defined accountability, across a master of approximately 11,000 records.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Establish and publish a single owner for the verification callback, reconcile the SOP text to the decision, and confirm the identity of the required second approver, so that the control as written matches the control as operated.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Capture the banking change workflow in NetSuite so that the callback documentation and the second approval are recorded as system-enforced prerequisites to saving the bank detail change, producing a retrievable audit trail without manual assembly.
> - **Addresses:** PP-001, PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Review and restrict vendor master edit entitlements in NetSuite, remove the legacy implementation partner login, and place emergency and administrator access under periodic recertification.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-004:** Define vendor master data ownership as an accountable role rather than an incidental duty, covering banking change execution and evidence quality.
> - **Addresses:** PP-004

```consult-meta
systems: [netsuite, coupa, ap-inbox]
roles:   [corporate-controller, procurement-lead, ap-clerk, senior-ap-specialist, assistant-controller, it-manager, ap-manager, supplier]
```
