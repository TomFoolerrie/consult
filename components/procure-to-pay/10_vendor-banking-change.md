## Vendor Remit-To Banking Change

### Scope

This procedure covers changes to the remittance bank account of a supplier that is
already established at Nordhaven Industrial Group: receipt of the change request,
telephone callback verification against a contact already held on file, second
approval, and update of the remit-to banking details on the NetSuite vendor record.
It covers banking details only. Establishment of a first-time supplier, including
the supplier's initial entry of its own banking details, is excluded and is
documented in [[new-vendor-onboarding]]; non-banking edits to an existing record —
payment terms, addresses, contacts, deactivation and periodic review — are excluded
and are documented in [[vendor-master-data-maintenance]]. The updated remit-to
account is consumed by [[weekly-payment-run]] and [[wire-and-manual-payment]].
(SRC-002, SRC-003, SRC-005, SRC-006)

### At a Glance

| Field | Value |
|---|---|
| Trigger | A supplier notifies the Company that its bank account has changed |
| Frequency | Ad hoc, on supplier request; volume not established |
| Preparer | `TBD — confirm with process owner` (disputed between the Accounts Payable Clerk and procurement — see GAP-01) |
| Reviewer | Second approver required before the change goes active; identity unconfirmed — see GAP-02 |
| Systems | NetSuite (vendor master for payment purposes); telephone, outside any system, for the callback |
| Key inputs | Supplier's banking change request; contact telephone number held on the supplier record |
| Key outputs | Updated remit-to bank account on the NetSuite vendor record; callback note and attachment evidencing the verification |

### Before You Start

- **Supplier banking change request** — received from the supplier, typically by
  email to the Company; identifies the supplier and the new bank account.
- **Active NetSuite vendor record** — [[new-vendor-onboarding]]; existing and
  active, carrying the remit-to banking details to be changed.
- **Supplier contact telephone number on file** — held on the supplier master
  record from onboarding; must be a number already on file and not a number
  supplied in the change request.
- **Vendor Maintenance role in NetSuite** — held by the person keying the change;
  per the prior SOP this role holds no payment preparation, payment approval or
  banking portal entitlement (§9.3 of the prior SOP).

### Procedure

#### Step 1: Receive the banking change request

A supplier notifies the Company that it has changed banks. Requests are described
as arriving by email and are directed to accounts payable.

> **VALIDATION REQUIRED — GAP-03:** No controlled intake channel for banking change requests is established.
> - **Note:** Requests are accepted as inbound email — do not treat receipt of the request as any form of authentication; the callback in Step 3 is the only verification described.
> - **Detail:** The Procurement Lead described the trigger as a "vendor emails saying 'we changed banks'" (SRC-002). Supplier-entered banking through the Coupa Supplier Information Management portal is described only for initial onboarding (SRC-002); no source states whether an existing supplier can submit a banking change through that portal, nor whether a request arriving through any other channel is accepted or rejected. Resolution sits jointly with the Procurement Lead, who owns the Coupa supplier portal, and the Corporate Controller, who owns the banking change policy.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 2: Obtain the callback number from the supplier record

The telephone number used for verification is taken from the supplier master
record. A number appearing in the change request itself is not used.

- **Fields / Parameters:** supplier contact telephone number as held on the
  vendor record.

#### Step 3: Perform the telephone callback verification

The supplier is called on the number obtained in Step 2 and the banking change is
confirmed with the supplier directly.

- **System / Tool:** telephone, outside NetSuite.
- **Expected Result:** the supplier confirms, or does not confirm, that it
  requested the change — this is the decision point on which the change proceeds.

> **VALIDATION REQUIRED — GAP-01:** Ownership of the callback verification is disputed across the sources.
> - **Note:** Who performs the callback is unresolved — do not assign the step from this document; confirm the operating owner before relying on the control.
> - **Detail:** The Corporate Controller stated that procurement performs the callback, on the basis that the Procurement Lead's team owns the supplier relationship and holds the real contacts (SRC-003). The Procurement Lead stated the opposite — that he believed the Accounts Payable Clerk makes the call today, described the ownership question as "murky," and recalled the Corporate Controller proposing procurement ownership without it ever being implemented (SRC-002). The prior SOP assigns the callback to an Accounts Payable Specialist (§9.4 of the prior SOP, SRC-006). On being told of the conflict the Corporate Controller responded that the policy she wrote may never have been operationalized and asked that it be flagged (SRC-003, SRC-005). Resolution sits with the Corporate Controller as owner of the control, jointly with the Procurement Lead.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

#### Step 4: Document the callback on the vendor record

The callback is documented with the date, the time, who was spoken to, and what
was confirmed. The documentation is recorded as a note on the NetSuite vendor
record with a supporting attachment.

- **Fields / Parameters:** date; time; person spoken to; what was confirmed.
- **Evidence Required:** callback note plus attachment on the NetSuite vendor
  record.

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite vendor record showing the callback note and attachment, evidencing date, time, person spoken to and what was confirmed.

#### Step 5: Obtain second approval before the change goes active

A second person approves the banking change before it takes effect.

> **VALIDATION REQUIRED — GAP-02:** The identity of the second approver on a banking change is unconfirmed.
> - **Note:** The second approver role is unconfirmed — obtain the operating approver before treating the dual-approval requirement as evidenced.
> - **Detail:** The Corporate Controller stated that a second person approves the change before it goes active but did not name the role, and speculated that the Accounts Payable Clerk may be performing the callback and naming her as the second approver (SRC-003). The prior SOP requires the verification to be documented on the supplier record but does not describe a second approval at all (§9.4 of the prior SOP, SRC-006). The working notes record the second approver as unclear (SRC-005). Resolution sits with the Corporate Controller.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 6: Update the remit-to banking details in NetSuite

The new bank account is keyed onto the NetSuite vendor record, which is the vendor
master for payment purposes. Additions and modifications to the supplier master
record are restricted to personnel holding the Vendor Maintenance role (§9.3 of
the prior SOP).

- **Evidence Required:** the updated NetSuite vendor record, carrying the callback
  note and attachment from Step 4.

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite vendor record remit-to banking fields after update, with the audit trail of the change.

#### Step 7: Correct or re-key the change where the request cannot be verified

- **Condition:** the callback does not confirm the change

No source describes what is done when a callback fails to confirm a requested
banking change.

> **VALIDATION REQUIRED — GAP-04:** The handling of an unverified or failed banking change request is undocumented.
> - **Note:** There is no described disposition for a request the supplier does not confirm — confirm whether such requests are rejected, escalated or investigated before assuming any handling exists.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

### Outputs & Evidence

- **Updated NetSuite vendor record** — carries the new remit-to bank account;
  consumed by [[weekly-payment-run]] and [[wire-and-manual-payment]].
- **Evidence retained:** the callback note and its attachment on the NetSuite
  vendor record, recording date, time, who was spoken to and what was confirmed.
  No retention period specific to this evidence was established.
- **Not retained:** no evidence of the second approval is described as being
  retained separately from the vendor record, and no record of a rejected or
  unverified change request was identified (see GAP-02, GAP-04). The Corporate
  Controller stated she cannot produce evidence of this control for an auditor
  without several rounds of email (SRC-003).

### Key Controls

> **CONTROL — CTRL-001:** Any change to a supplier's remit-to bank account is verified by telephone callback to a contact number already held on the supplier record, and never to a number supplied in the change request.
> - **Type:** Preventive
> - **Frequency:** each banking change request
> - **Owner:** TBD — disputed between procurement and accounts payable (see GAP-01)

> **CONTROL — CTRL-002:** The callback is documented on the NetSuite vendor record — date, time, who was spoken to and what was confirmed — as a note with a supporting attachment.
> - **Type:** Detective
> - **Frequency:** each banking change request
> - **Owner:** TBD — follows the callback owner (see GAP-01)

> **CONTROL — CTRL-003:** A second person approves the banking change before it goes active.
> - **Type:** Preventive
> - **Frequency:** each banking change
> - **Owner:** TBD — second approver unconfirmed (see GAP-02)

> **CONTROL — CTRL-004:** Modification of the supplier master record, including remit-to banking, is restricted to the Vendor Maintenance role, which holds no payment preparation, payment approval or banking portal entitlement.
> - **Type:** Preventive
> - **Frequency:** continuous (entitlement-based)
> - **Owner:** Corporate Controller

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The banking change control is not demonstrably operating as written, and no source could confirm who performs it.
> - **Note:** The policy owner, the procurement owner and the prior SOP each name a different performer, and the policy owner acknowledged it may never have been operationalized.
> - **Detail:** The Corporate Controller assigns the callback to procurement, the Procurement Lead believes the Accounts Payable Clerk performs it, and the prior SOP assigns it to an Accounts Payable Specialist (SRC-003, SRC-002, §9.4 of the prior SOP, SRC-006). Told of the conflict, the Corporate Controller responded that she did not know the policy she wrote had ever been operationalized (SRC-003). The working notes carry the same item as an open conflict with the second approver also unresolved (SRC-005). See GAP-01 and GAP-02.
> - **Impact:** A remit-to banking change — the highest-value target for payment fraud in the process — rests on a control with no confirmed performer, no confirmed second approver, and therefore no assurance that the callback occurs before funds are redirected.
> - **Severity:** High

> **PAIN POINT — PP-002:** Evidence of the banking change control cannot be produced on demand.
> - **Note:** The Corporate Controller identified assembling auditable evidence of this control as one of the three things she would most want changed.
> - **Detail:** She stated that she wants the vendor banking change control operating the way it is written, "with evidence I can hand an auditor without three emails first" (SRC-003). The callback evidence is a free-form note plus attachment on the vendor record, with no standard form and no described completeness check (SRC-003, SRC-005).
> - **Impact:** Audit and quarterly review effort is expended reconstructing whether the control operated; an omitted note cannot be distinguished from an omitted callback.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Banking change requests are accepted as inbound email rather than through an authenticated supplier channel.
> - **Note:** Unlike initial onboarding, where the supplier enters its own banking in the Coupa SIM portal, a change to an existing account starts from an email.
> - **Detail:** The Procurement Lead contrasted the two directly, describing supplier self-entry of banking in the SIM portal as the part of onboarding he likes precisely because "we're not keying it off an emailed PDF," while describing banking changes as arriving as a "vendor emails saying 'we changed banks'" (SRC-002). No source states whether the SIM portal supports a banking change on an existing supplier. See GAP-03.
> - **Impact:** The Company keys bank account details from an unauthenticated inbound message, leaving the telephone callback as the sole barrier to a fraudulent redirection.
> - **Severity:** High

> **IMPROVEMENT OPPORTUNITY — IO-001:** Assign a single named owner for the callback verification and a named second approver, and confirm both against the NetSuite and Coupa entitlements actually in force.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Standardise the callback evidence as a structured record on the vendor record — date, time, person spoken to, confirmation, performer, approver — so that the control can be evidenced without reconstruction.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Route banking changes on existing suppliers through the Coupa Supplier Information Management portal, so the new account is entered by the authenticated supplier rather than keyed from an email.
> - **Addresses:** PP-003

```consult-meta
systems: [netsuite, coupa]
roles:   [corporate-controller, procurement-lead, ap-clerk, senior-ap-specialist]
```
