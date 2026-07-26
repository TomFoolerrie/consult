## Vendor Banking Change

### A. Process Overview

This procedure governs changes to an existing supplier's remittance (remit-to) banking details on the NetSuite vendor master — the record every subsequent disbursement pays against. It is event-driven: it runs when a supplier requests a banking change, typically by email to Accounts Payable (SRC-002). Before a change takes effect, the request must be verified by telephone callback to a contact number already held on the vendor record — never one supplied in the request — with the verification documented on the record and the change approved by a second person (SRC-003). Which role performs the callback is contested across the sources and is raised for validation at the callback step (GAP-01). Upstream, initial banking details are captured through supplier self-registration during [[new-vendor-onboarding]], and broader stewardship of the vendor record sits with [[vendor-master-data-maintenance]]; downstream, [[weekly-payment-run]] and [[wire-and-manual-payment]] disburse to whatever details this procedure has made active.

### B. Quick Reference

- **Trigger:** A supplier requests a change to its remittance banking details, typically by email stating it has changed banks (SRC-002).
- **Frequency:** Ad hoc — on supplier request; volume is not quantified in the sources.
- **Preparer:** TBD — the sources conflict on who performs the callback and the change (see GAP-01).
- **Reviewer:** TBD — a second person must approve the change before it goes active; the approver's identity is unconfirmed (SRC-003; see GAP-02).
- **Primary systems / tools:** NetSuite (vendor master); telephone callback; Coupa (supplier record — see GAP-04).
- **Key outputs:** Updated remit-to banking details on the NetSuite vendor record; documented callback verification (note plus attachment); second-person approval.

### C. Pre-Requisites

- The supplier exists as an active record on the NetSuite vendor master; its initial banking details were captured through supplier self-registration in Coupa during [[new-vendor-onboarding]] (SRC-002).
- A supplier contact telephone number, independent of the change request, is already held on the NetSuite vendor record (SRC-003).
- The person entering the change holds the Vendor Maintenance role in NetSuite (SRC-003; §9.3 of the prior AP SOP, SRC-006).

### D. Inputs

- **Banking-change request:** the supplier's request to change its remittance banking details, typically received by email into Accounts Payable — source: the supplier (SRC-002).
- **Callback contact number:** the telephone number already held on the supplier's NetSuite vendor record — sourced from the vendor master record, never from the change request (SRC-003; §9.4 of the prior AP SOP, SRC-006).
- **Confirmed banking details:** the new remittance details as confirmed directly with the supplier during the callback (SRC-003).

### E. Step-by-Step Procedure

#### Step 1: Receive the banking-change request

The supplier submits a request to change its remittance banking details — typically an email stating that it has changed banks — and the request is directed to Accounts Payable (SRC-002). Treat every detail in the request, including any telephone number or contact person it offers, as unverified until the callback in Step 3 is complete.

- **System / Tool:** Email to Accounts Payable (specific mailbox or queue TBD — confirm with process owner).

> **VALIDATION REQUIRED — GAP-03:** The intake channel for banking-change requests. Requests are described only as vendor emails that go to Accounts Payable (SRC-002); the specific mailbox or queue that receives them, and how a request arriving to a Procurement or plant contact is redirected, was not established.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Retrieve the callback contact from the vendor record

Open the supplier's record on the NetSuite vendor master and obtain the contact telephone number already held on file. The callback number must come from the vendor record, not from the change request (SRC-003; §9.4 of the prior AP SOP, SRC-006).

- **System / Tool:** NetSuite (vendor master).
- **Expected Result:** A callback number sourced entirely independently of the change request.

#### Step 3: Perform the callback verification

Call the number on file and confirm the requested change directly with the supplier: that the request is genuine and that the new banking details are as stated. Capture the date and time of the call, the person spoken to, and what was confirmed (SRC-003). Which role performs this callback is contested across the sources — [[GAP-01 — CALLBACK OWNER]].

- **Evidence Required:** Date and time of the call, person spoken to, and details confirmed — recorded on the vendor record in Step 4.

> **VALIDATION REQUIRED — GAP-01:** Who performs the banking-change callback. The Corporate Controller states the policy assigns it to the Procurement Lead's team, which holds the genuine supplier contacts (SRC-003); the Procurement Lead believes the Accounts Payable Clerk performs it in current practice (SRC-002); §9.4 of the prior AP SOP assigns it to the Senior Accounts Payable Specialist (SRC-006). The Corporate Controller was surprised by the discrepancy and acknowledged the written policy may never have been operationalized (SRC-003, SRC-005).
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

#### Step 4: Document the verification on the vendor record

Record the callback on the supplier's NetSuite vendor record as a note, and attach the supporting documentation, so that the verification is retrievable from the record itself (SRC-003, SRC-005).

- **System / Tool:** NetSuite (vendor master).
- **Evidence Required:** Callback note plus attachment on the vendor record.

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite vendor record showing the callback note and attachment; must validate that the verification (date, time, person spoken to, details confirmed) is documented on the record itself.

#### Step 5: Enter the updated banking details

Update the remit-to banking details on the supplier's NetSuite vendor record. Entry is restricted to holders of the Vendor Maintenance role — held by the Accounts Payable Clerk, who has no payment permissions (SRC-003) — and under §9.3 of the prior AP SOP the role must not carry payment preparation, payment approval, or banking portal entitlements (SRC-006). The change does not take effect until the approval in Step 6.

- **System / Tool:** NetSuite (vendor master).
- **Fields / Parameters:** Remit-to banking details on the vendor record; specific field names TBD — confirm with process owner.

> **VALIDATION REQUIRED — GAP-04:** Whether the Coupa supplier record is updated to reflect the banking change. Suppliers enter their own banking details in Coupa at onboarding, and Coupa is the sourcing-side system of record with a nightly supplier sync into NetSuite (SRC-002); no source describes whether or how a post-onboarding banking change is reflected in Coupa, or whether the change is made in NetSuite only.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 6: Obtain second-person approval before the change goes active

A second person approves the banking change before it becomes active on the vendor record (SRC-003). The approver's identity and the way the approval is recorded are unconfirmed — [[GAP-02 — SECOND APPROVER]].

- **Expected Result:** The new remit-to banking details are active only after the second-person approval.

> **VALIDATION REQUIRED — GAP-02:** The identity of the second approver and how the approval is evidenced. The Corporate Controller requires a second person to approve the change before it goes active, and speculated — without confirming — that the second approver in current practice is the Corporate Controller (SRC-003, SRC-005). The mechanism by which the approval is recorded or enforced in NetSuite was not described.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite vendor record after approval, showing the active remit-to banking details; must validate that the active details match those confirmed on the callback.

### F. Key Controls

> **CONTROL — CTRL-001:** Callback verification of every supplier banking-change request against a contact number already held on the vendor master record — never a number supplied in the request — documented with date, time, person spoken to, and details confirmed (SRC-003; §9.4 of the prior AP SOP, SRC-006).
> - **Type:** Preventive
> - **Frequency:** Each banking-change request
> - **Owner:** TBD — the performing role is contested; see GAP-01

> **CONTROL — CTRL-002:** Second-person approval of a banking change before it becomes active on the vendor record (SRC-003).
> - **Type:** Preventive
> - **Frequency:** Each banking-change request
> - **Owner:** TBD — the approver is unconfirmed; see GAP-02

> **CONTROL — CTRL-003:** Segregation of duties over the change itself: vendor record edits are restricted to the Vendor Maintenance role, whose holders carry no payment preparation, payment approval, or banking portal entitlements; the Accounts Payable Clerk holds the role with no payment permissions (SRC-003; §9.3 of the prior AP SOP, SRC-006).
> - **Type:** Preventive
> - **Frequency:** Continuous — role-based access restriction
> - **Owner:** Corporate Controller

### G. Outputs

- **Updated remit-to banking details** on the supplier's NetSuite vendor record — consumed downstream by [[weekly-payment-run]] and [[wire-and-manual-payment]], which disburse to the details held on the record (SRC-002, SRC-003).
- **Callback verification evidence** — note plus attachment retained on the NetSuite vendor record (SRC-003, SRC-005).
- **Second-person approval** of the change — the form and retention location of the approval evidence are TBD (see GAP-02).
- **Evidence retained:** the callback note and attachment on the vendor record (SRC-003, SRC-005); approval evidence TBD — confirm with process owner.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The banking-change verification control has drifted from its written design: the Corporate Controller, the Procurement Lead and the prior AP SOP each name a different owner for the callback, and the Corporate Controller — the policy's author — acknowledged it may never have been operationalized (SRC-002, SRC-003, SRC-005, SRC-006).
> - **Impact:** A fraudulent banking-change request could be actioned without independent verification, diverting supplier payments; the Corporate Controller also cannot hand auditors control evidence without ad-hoc effort (SRC-003).
> - **Severity:** High

> **PAIN POINT — PP-002:** Vendor record edit access extends beyond the Vendor Maintenance role: the Assistant Controller holds emergency edit access, the NetSuite administrator role is held by the IT Manager, and a legacy implementation-partner login remains active and unremediated (SRC-003, SRC-005).
> - **Impact:** Banking details could be changed outside the callback-and-approval path, undermining the vendor-master segregation of duties that sits within the auditors' scope (SRC-003).
> - **Severity:** High

> **IMPROVEMENT OPPORTUNITY — IO-001:** Assign a single accountable owner for banking-change verification, re-operationalize the callback and second-approval control as written, and standardize the callback evidence (note plus attachment on the vendor record) so it can be produced for auditors on demand — an outcome the Corporate Controller explicitly asked for (SRC-003).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Deactivate the legacy implementation-partner login and re-examine the remaining vendor-edit access outside the Vendor Maintenance role (the Assistant Controller's emergency access and the NetSuite administrator role) against the segregation-of-duties requirement (SRC-003, SRC-005).
> - **Addresses:** PP-002

```consult-meta
systems: [netsuite, coupa]
roles:   [supplier, ap-clerk, senior-ap-specialist, procurement-lead, corporate-controller, assistant-controller, it-manager, ap-manager]
```
