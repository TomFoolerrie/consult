## Non-PO Invoice Entry and Approval Routing

### Scope

This procedure covers the entry, general ledger coding and approval routing of
supplier invoices that carry no purchase order reference — utilities, legal and
insurance billing, freight billing that does not tie to a purchase order, and
purchases falling below the threshold at which a purchase order is required. It
begins with a pending Bill already captured and imaged by
[[invoice-intake-and-capture]] and ends when the Bill is fully approved and
eligible for selection in [[weekly-payment-run]]. Invoices bearing a purchase
order reference are excluded and are handled by
[[po-invoice-entry-and-three-way-match]]; employee expense reimbursements,
payroll disbursements and intercompany settlements are outside the process
entirely. The supplier record to which the Bill is posted is established by
[[new-vendor-onboarding]] and maintained by [[vendor-master-data-maintenance]].
(SRC-001, SRC-006)

### At a Glance

| Field | Value |
|---|---|
| Trigger | A pending Bill in NetSuite carrying no purchase order reference |
| Frequency | Continuous; worked daily from the pending review queue |
| Preparer | Accounts Payable Clerk |
| Reviewer | Cost Center Owner, with additional approvers by invoice value (see the approval ladder in Key Controls) |
| Systems | NetSuite |
| Key inputs | Pending Bill with attached invoice image; supplier master record; chart of accounts, department and class values |
| Key outputs | Coded and fully approved Bill, eligible for payment selection |

Non-PO invoices are understood to represent approximately 25% of total invoice
volume; the figure is an unvalidated recollection rather than a system report
(SRC-001, SRC-005).

### Before You Start

- **Pending Bill in NetSuite** — [[invoice-intake-and-capture]]; in a pending
  state with the invoice image attached and no purchase order reference
  extracted.
- **Supplier master record** — [[vendor-master-data-maintenance]]; active, with
  payment terms populated, so the Bill can be entered and dated for payment.
- **Chart of accounts, department and class values** — maintained in NetSuite;
  current, since non-PO lines are coded by hand rather than derived from a
  purchase order.
- **Approval authority schedule** — the value ladder configured in the NetSuite
  approval routing workflow; see GAP-01, which is unresolved.

### Procedure

#### Step 1: Select the pending non-PO Bill from the review queue

Pending Bills are worked from the "AP - Bills Pending Review" saved search.
Bills carrying no purchase order reference are separated from PO-backed bills
and worked under this procedure. (SRC-001)

- **Expected Result:** the Bill is identified as non-PO and will be coded by
  hand rather than matched

> **VALIDATION REQUIRED — GAP-04:** The purchase-order-requirement threshold — the value below which a purchase may proceed without a purchase order and therefore arrives as a non-PO invoice — is not established.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 2: Enter the bill without a purchase order reference

The invoice is entered on the standard bill entry screen with no purchase order
reference, so no lines are populated from a receipt. (SRC-001, SRC-006)

- **Navigation Path:** Transactions > Payables > Enter Bills
- **Fields / Parameters:** supplier; supplier invoice number; invoice date;
  invoice total; payment terms

#### Step 3: Reject and investigate a duplicate entry

- **Condition:** NetSuite rejects the entry against the unique constraint on
  supplier plus supplier invoice number

Duplicate invoice entry is prevented by the system through a unique constraint
on the combination of supplier identifier and supplier invoice number; an
attempted duplicate is rejected at entry and the rejected document is
investigated before any further entry is attempted. (SRC-006)

- **Expected Result:** no second payable is created for an invoice already
  recorded

#### Step 4: Code the invoice to the general ledger

Because there is no purchase order to derive the coding, each line is coded by
hand to the general ledger in accordance with the Company chart of accounts.
(SRC-001, SRC-006)

- **Fields / Parameters:** general ledger account; department; class (used to
  identify the plant)

> **SCREENSHOT PLACEHOLDER — SC-01:** The bill entry screen for a non-PO invoice, showing the empty purchase order reference and the manually completed account, department and class fields.

#### Step 5: Route the coded bill for approval

The coded Bill is submitted to NetSuite approval routing, which directs it to
approvers by invoice value. Approval is recorded within the system;
approval by electronic mail is not acceptable evidence. An approver does not
approve an invoice for which that approver is the requester or the beneficiary.
The value breakpoints and the approver set are unresolved — see
[[GAP-01 — NON-PO APPROVAL LADDER]]. (SRC-001, SRC-006)

- **Evidence Required:** the approval history recorded on the NetSuite Bill

> **VALIDATION REQUIRED — GAP-01:** The non-PO approval ladder differs between the prior SOP and observed practice in both its value breakpoints and its approver set.
> - **Note:** Do not operate to a stated ladder; the configured NetSuite approval workflow must be read before any breakpoint or approver is documented.
> - **Detail:** §6.1 of the prior SOP sets four bands — up to $2,500 Cost Center Owner; $2,500.01 to $10,000 adding the Functional Vice President; $10,000.01 to $50,000 adding the Corporate Controller; above $50,000 adding the Chief Financial Officer. The Accounts Payable Manager describes three bands in practice — under $5,000 Cost Center Owner only; $5,000 to $25,000 adding the Corporate Controller; above $25,000 to the Chief Financial Officer — with amounts above $100,000 additionally flagged in the monthly capital expenditure review but carrying no separate approval. The Functional Vice President layer appears in the SOP and in no account of practice. Which ladder is live in the NetSuite workflow has not been established; the configuration has not been pulled. (SRC-001, SRC-005, SRC-006)
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite approval routing history on an approved non-PO Bill, showing each approver, the approving user and the approval date.

#### Step 6: Pursue an approval that has not been actioned

- **Condition:** the Bill remains in an approver's queue without action

Bills awaiting approval are pursued by contacting the approver directly. Both
the Accounts Payable Manager and the Senior Accounts Payable Specialist describe
non-PO approvals remaining in approver queues for up to two weeks, with no
automated escalation observed. (SRC-001, SRC-005)

> **VALIDATION REQUIRED — GAP-02:** Automatic escalation of unactioned approvals is required by the prior SOP but is not observed in practice.
> - **Note:** No automated escalation can be relied upon; unactioned approvals are chased manually until the workflow configuration is confirmed.
> - **Detail:** §6.4 of the prior SOP requires approvals not actioned within three business days to escalate automatically to the approver's supervisor. The Accounts Payable Manager states there is no escalation and that a bill "just sits there until someone yells", and the Senior Accounts Payable Specialist independently names non-PO approvals parked in queues as a pain point. Whether the escalation is configured and inactive, or was never configured, requires the NetSuite approval workflow configuration. (SRC-001, SRC-005, SRC-006)
> - **Nature:** conflict
> - **Owner to confirm:** IT Manager

#### Step 7: Release the approved bill to the payment cycle

On completion of the approval chain the Bill becomes eligible for selection in
the weekly disbursement cycle. (SRC-001, SRC-006)

- **Expected Result:** an approved, coded payable is available for selection by
  [[weekly-payment-run]]

### Outputs & Evidence

- **Approved non-PO Bill in NetSuite** — coded to account, department and class,
  with the invoice image attached; consumed by [[weekly-payment-run]].
- **Approval history** — recorded on the Bill within NetSuite, identifying each
  approver and approval date; electronic mail approvals are not accepted as
  evidence (SRC-006).
- **Evidence retained:** the invoice image is retained as an attachment to the
  Bill for not less than seven years (SRC-005, SRC-006).
- **Not retained:** no record is kept of the manual chasing of unactioned
  approvals, so approval cycle time and the extent of the delay described by the
  team cannot be measured from the current-state evidence (SRC-001, SRC-005).

### Key Controls

> **CONTROL — CTRL-001:** Invoices entered without a purchase order reference are routed for approval within NetSuite against a value-based authority ladder before becoming eligible for payment, in place of the purchase order approval that would otherwise stand behind them.
> - **Type:** Preventive
> - **Frequency:** Each non-PO bill entered
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-002:** Approval is recorded within NetSuite on the Bill record; approval by electronic mail is not accepted as evidence of approval.
> - **Type:** Preventive
> - **Frequency:** Each non-PO bill approved
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-003:** An approver does not approve an invoice for which that approver is the requester or the beneficiary.
> - **Type:** Preventive
> - **Frequency:** Each non-PO bill approved
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-004:** Duplicate payment is prevented at entry by a unique constraint in NetSuite on the combination of supplier identifier and supplier invoice number; an attempted duplicate is rejected by the system.
> - **Type:** Preventive
> - **Frequency:** Each bill entered
> - **Owner:** IT Manager

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Non-PO approvals remain unactioned in approver queues for extended periods with no automated escalation operating.
> - **Impact:** Bills are described as sitting for up to two weeks until someone chases them, delaying the payable and consuming Accounts Payable time in manual follow-up. (SRC-001, SRC-005)
> - **Severity:** High

> **PAIN POINT — PP-002:** Non-PO invoice entry and supplier master maintenance are performed by the same Accounts Payable Clerk.
> - **Impact:** The individual able to create and edit supplier records also enters unmatched payables against those records, concentrating in one pair of hands two activities the control environment elsewhere separates. (SRC-005)
> - **Severity:** High

> **PAIN POINT — PP-003:** Every non-PO invoice is coded by hand to account, department and class because there is no purchase order from which coding can be derived.
> - **Impact:** Roughly a quarter of total invoice volume carries manual coding effort at entry and the associated miscoding exposure. (SRC-001, SRC-005)
> - **Severity:** Medium

> **PAIN POINT — PP-004:** Freight billing arising from collect shipments has no defined authorization or entry route and falls into the non-PO population by default.
> - **Impact:** TBD — the sources record that no process was described and that authorization of collect shipments is itself disputed at the receiving dock. (SRC-005)
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Configure and activate automated reminder and escalation of unactioned approvals in the NetSuite approval workflow, as the prior SOP already contemplates, so that stalled non-PO bills surface without manual chasing.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Separate non-PO invoice entry from supplier master maintenance by reassigning one of the two activities, restoring the segregation applied elsewhere in the payables process.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Bring recurring non-PO spend such as utilities, insurance and legal billing onto standing purchase orders through [[blanket-po-management]], so that coding and approval derive from the purchase order rather than being applied by hand at each invoice.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-004:** Establish a defined authorization and entry route for freight billing on collect shipments, so that such invoices are not absorbed into the non-PO population without an owner.
> - **Addresses:** PP-004

```consult-meta
systems: [netsuite]
roles:   [ap-clerk, ap-manager, senior-ap-specialist, cost-center-owner, corporate-controller, cfo, functional-vp, it-manager, procurement-lead]
```
