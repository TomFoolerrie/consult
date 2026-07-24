## Non-PO Invoice Entry and Approval

### A. Process Overview

This procedure covers the entry, general ledger coding and approval routing of supplier invoices that carry no purchase order reference — utilities, legal and insurance billing, freight not tied to a purchase order, and other spend below the purchase order threshold, together roughly a quarter of total invoice volume. It runs continuously each business day as pending Bills accumulate, and is performed by the Accounts Payable Clerk under the Accounts Payable Manager, with approval performed outside Accounts Payable by the Cost Center Owner and, above defined dollar breakpoints, more senior approvers. It begins with a pending NetSuite Bill captured in [[invoice-intake-and-capture]] that carries no purchase order reference, and ends when the Bill is approved and eligible for selection in [[weekly-payment-run]]. Because no purchase order approval sits behind the spend, the approval routing in this procedure is the sole authorization control over it; invoices bearing a purchase order reference are handled in [[po-invoice-entry-and-three-way-match]] (SRC-001, SRC-005, SRC-006).

### B. Quick Reference

- **Trigger:** A NetSuite Bill in a pending state with no purchase order reference appears in the "AP - Bills Pending Review" saved search.
- **Frequency:** Continuous / daily as invoices arrive; approximately twenty-five percent of invoice volume (SRC-005, unvalidated).
- **Preparer:** Accounts Payable Clerk.
- **Reviewer:** Cost Center Owner, with additional approvers by invoice value through NetSuite approval routing (ladder disputed — see [[GAP-01 — NON-PO APPROVAL LADDER]]).
- **Primary systems / tools:** NetSuite.
- **Key outputs:** Approved NetSuite Bill with general ledger coding and a recorded approval trail.

### C. Pre-Requisites

- The invoice has been captured and exists as a NetSuite Bill in a pending state with the invoice image attached, per [[invoice-intake-and-capture]].
- The supplier is an active record in the NetSuite vendor master, maintained in [[vendor-master-data-maintenance]].
- The Accounts Payable Clerk holds the NetSuite permissions to enter Bills and to apply general ledger, department and class coding.
- NetSuite approval routing is configured for non-PO Bills and the responsible Cost Center Owner is identified for the coding applied.

### D. Inputs

- **Pending NetSuite Bill (no purchase order reference):** Created by the Ephesoft push in [[invoice-intake-and-capture]]; carries captured header values and the invoice image.
- **Supplier invoice image:** Attached to the Bill; the source for the coding decision and the supporting document for approval.
- **NetSuite chart of accounts, department and class values:** Used to code the expense (SRC-006 §5.5).
- **NetSuite vendor master record:** Supplies the supplier identifier, payment terms and remit-to details.

### E. Step-by-Step Procedure

#### Step 1: Identify non-PO invoices in the pending Bill population

The Accounts Payable Clerk works the pending Bill population created by capture and identifies the invoices carrying no purchase order reference. These are handled outside the three-way match flow because there is no purchase order and no goods receipt to match against.

- **System / Tool:** NetSuite.
- **Navigation Path:** The "AP - Bills Pending Review" saved search on the Accounts Payable dashboard.
- **Expected Result:** A working population of pending Bills with no purchase order reference.

> **VALIDATION REQUIRED — GAP-05:** How a Bill is distinguished as genuinely non-PO rather than as a purchase order invoice whose reference Ephesoft failed to extract. Capture is known to miss a purchase order reference printed outside a standard position (see [[invoice-intake-and-capture]]), but no source describes a check performed before an invoice is coded manually as non-PO.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Enter and code the invoice

The Accounts Payable Clerk opens the Bill and completes entry without a purchase order reference. Because no purchase order populates the lines, the expense is coded manually: general ledger account, department, and class, which the Company uses to identify the plant. Coding follows the Company chart of accounts (SRC-006 §5.5).

- **System / Tool:** NetSuite.
- **Navigation Path:** Transactions > Payables > Enter Bills (or by opening the pending Bill directly from the saved search).
- **Fields / Parameters:** Vendor; supplier invoice number; invoice date; invoice total; general ledger account; department; class (plant). No purchase order reference is entered.
- **Expected Result:** A coded Bill ready to enter approval routing.
- **Evidence Required:** The invoice image attached to the Bill supports the coding applied.

> **SCREENSHOT PLACEHOLDER — SC-01:** A non-PO Bill open in NetSuite showing the coding fields completed (account, department, class) and no purchase order reference — validates the manual coding step and the field set.

#### Step 3: Submit the invoice into NetSuite approval routing

On entry, the Bill routes for approval through NetSuite approval routing. The Cost Center Owner approves at every value; additional approvers are added as the invoice value rises. The dollar breakpoints and the approver set at each tier are stated differently by the current process owner and by the prior standard operating procedure and are not documented here as a single ladder — see [[GAP-01 — NON-PO APPROVAL LADDER]]. Approval is recorded in NetSuite; approval by electronic mail is not accepted as evidence of approval, and an approver may not approve an invoice for which that approver is the requester or the beneficiary (SRC-006 §§6.2–6.3).

- **System / Tool:** NetSuite approval routing.
- **Expected Result:** The Bill sits in the approver's NetSuite queue and cannot be released for payment until approval is recorded.
- **Evidence Required:** The approval recorded against the Bill in NetSuite.

> **VALIDATION REQUIRED — GAP-01:** The approval ladder in force for non-PO invoices — both the dollar breakpoints and the approver set at each tier. The Accounts Payable Manager describes Cost Center Owner alone up to $5,000; Cost Center Owner plus Corporate Controller from $5,000 to $25,000; and Chief Financial Officer above $25,000, with invoices above $100,000 flagged in the monthly capital expenditure review but not separately approved, and no Functional Vice President layer at any tier. SRC-006 §6.1 states a different ladder: Cost Center Owner up to $2,500; adding a Functional Vice President to $10,000; adding the Corporate Controller to $50,000; and adding the Chief Financial Officer above $50,000. The two differ in both breakpoints and approver set. The Corporate Controller, who sits in the ladder under both versions, did not indicate awareness that the documented and described ladders diverge. Resolution path: export the non-PO Bill approval routing configuration from NetSuite and document the ladder as configured; do not resolve by preference between sources.
> - **Nature:** conflict
> - **Owner to confirm:** IT Manager (configuration export), confirmed with Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite non-PO Bill approval routing configuration showing the value breakpoints and approver roles — the evidentiary basis for closing GAP-01.

#### Step 4: Monitor invoices awaiting approval

Approved Bills leave the queue and become eligible for the payment run. Invoices awaiting approval remain in the approver's NetSuite queue. The prior standard operating procedure requires automatic escalation to the approver's supervisor where an approval is not actioned within three business days (SRC-006 §6.4); Accounts Payable describes non-PO approvals sitting in approver queues for approximately two weeks with no escalation occurring, chased only by direct follow-up. Whether the escalation is not configured or is configured and not functioning is not established — see [[GAP-02 — APPROVAL ESCALATION]].

- **System / Tool:** NetSuite.
- **Expected Result:** Aged approvals are identified and pursued.
- **Evidence Required:** TBD — confirm with process owner. No source describes a report, aging view or log used to monitor pending non-PO approvals.

> **VALIDATION REQUIRED — GAP-02:** Whether the three-business-day automatic escalation required by SRC-006 §6.4 is configured in NetSuite, and if configured why it is not operating. Accounts Payable reports approvals sitting approximately two weeks with no escalation. The NetSuite approval routing export requested for GAP-01 should also evidence the escalation rule.
> - **Nature:** conflict
> - **Owner to confirm:** IT Manager

> **VALIDATION REQUIRED — GAP-03:** Whether any monitoring of the pending non-PO approval population exists — a saved search, aging report or cadence — and which role owns it. No source describes one; follow-up is currently ad hoc.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 5: Release the approved invoice to the payment population

Once approval is recorded, the Bill is eligible for selection in the weekly payment proposal built in [[weekly-payment-run]]. No further Accounts Payable action occurs within this procedure.

- **System / Tool:** NetSuite.
- **Expected Result:** An approved Bill with complete coding, available to the payment proposal by due date.

> **VALIDATION REQUIRED — GAP-04:** The treatment of freight bills and collect shipments that carry no purchase order. These appear to fall into the non-PO population by default, but no source describes who authorizes the freight charge or validates it before coding, and the authorization of collect shipments was raised as an open question at the receiving dock.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

### F. Key Controls

> **CONTROL — CTRL-001:** Non-PO Bills route through NetSuite approval routing and cannot be released for payment until approval is recorded in NetSuite; the Cost Center Owner approves at every value and additional approvers are added as invoice value rises. Approval by electronic mail is not accepted as evidence.
> - **Type:** Preventive
> - **Frequency:** Each non-PO invoice
> - **Owner:** Cost Center Owner (additional approvers by value — ladder disputed, see [[GAP-01 — NON-PO APPROVAL LADDER]])

> **CONTROL — CTRL-002:** An approver may not approve an invoice for which that approver is the requester or the beneficiary (SRC-006 §6.3).
> - **Type:** Preventive
> - **Frequency:** Each non-PO invoice
> - **Owner:** TBD — confirm with process owner. No source describes whether this restriction is enforced by NetSuite configuration or relies on approver conduct.

> **CONTROL — CTRL-003:** NetSuite rejects duplicate entry through a unique constraint on the combination of supplier identifier and supplier invoice number, preventing the same non-PO invoice from being recorded twice (SRC-006 §5.6).
> - **Type:** Preventive
> - **Frequency:** Each invoice entered
> - **Owner:** IT Manager

> **CONTROL — CTRL-004:** Approvals not actioned within three business days escalate automatically to the approver's supervisor (SRC-006 §6.4). This control is documented but is not observed to operate — see [[GAP-02 — APPROVAL ESCALATION]].
> - **Type:** Detective
> - **Frequency:** Continuous, per pending approval
> - **Owner:** TBD — confirm with process owner

### G. Outputs

- **Approved NetSuite Bill:** Coded to general ledger account, department and class, with the approval recorded in NetSuite; consumed by [[weekly-payment-run]].
- **Approval trail in NetSuite:** The record of who approved at each tier and when; the sole authorization evidence for spend with no purchase order behind it.
- **Evidence retained:** The supplier invoice image attached to the Bill (retention addressed in [[invoice-intake-and-capture]]) and the NetSuite approval record.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Non-PO invoices sit in approver NetSuite queues for approximately two weeks. The three-business-day automatic escalation required by the standard operating procedure does not operate, and invoices move only when Accounts Payable chases the approver directly.
> - **Impact:** Delayed approval pushes invoices past due date, exposes the Company to late payment and lost discounts, and consumes Accounts Payable effort on manual follow-up.
> - **Severity:** High

> **PAIN POINT — PP-002:** One Accounts Payable Clerk holds both vendor master maintenance and non-PO invoice entry. The same individual can create or amend a supplier record — including remit-to details — and originate a payable against that supplier with no purchase order, receipt or match behind it.
> - **Impact:** A segregation of duties weakness across the two activities most exposed to payment fraud. The compensating factors are the NetSuite approval routing on the non-PO Bill and the absence of any payment release entitlement in the same hands, but no source describes a detective review of non-PO invoices raised against recently created or amended vendor records.
> - **Severity:** High

> **PAIN POINT — PP-003:** The documented approval ladder and the ladder described in practice differ in both dollar breakpoints and approver set, and no party has read the configuration in NetSuite to establish which is in force.
> - **Impact:** Neither Accounts Payable nor the Corporate Controller can state the authorization limits actually applied to approximately a quarter of invoice volume, and the standard operating procedure cannot be relied upon as evidence of the control for audit purposes.
> - **Severity:** High

> **PAIN POINT — PP-004:** Non-PO invoices are coded manually to general ledger account, department and class from the invoice image alone, with no purchase order to derive the coding from.
> - **Impact:** Coding accuracy depends on a single preparer's judgment; no source describes a review of coding before or after approval. (TBD — no source quantifies the resulting misclassification or rework.)
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Export the non-PO Bill approval routing configuration from NetSuite, reconcile it against the standard operating procedure ladder, adopt a single ladder approved by the Chief Financial Officer, and reissue the standard operating procedure section against the configuration as built.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Configure and test the automatic escalation of unactioned approvals, and stand up a NetSuite aging view of pending non-PO approvals reviewed by the Accounts Payable Manager on a defined cadence.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-003:** Separate vendor master maintenance from non-PO invoice entry — consistent with the Corporate Controller's stated intent to make vendor master ownership a defined role — or, where headcount does not permit separation, implement a detective review of non-PO invoices raised against vendor records created or amended within a defined preceding period.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-004:** Introduce default coding derived from the supplier record for recurring non-PO categories such as utilities, insurance and legal, so that repeat invoices are coded consistently rather than keyed from the image each time.
> - **Addresses:** PP-004

```consult-meta
systems: [netsuite]
roles:   [ap-clerk, ap-manager, corporate-controller, cfo, cost-center-owner, functional-vp, it-manager, supplier]
```
