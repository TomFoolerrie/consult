## Confirming (After-the-Fact) PO

### A. Process Overview

This procedure covers the creation of a purchase order after goods have already
been delivered or services already performed without an approved purchase order
in place — referred to internally as a confirming PO. It runs on an exception
basis, most commonly when an urgent plant condition leads a requester to engage
a supplier directly and the supplier subsequently submits an invoice that
Accounts Payable cannot match. Procurement performs the work in Coupa, after
which the purchase order syncs to NetSuite so the invoice can be processed.
It is the exception path around [[requisition-and-approval]] and
[[po-issuance-and-change-orders]], and it unblocks
[[po-invoice-entry-and-three-way-match]] downstream. It excludes routine
change orders to an existing purchase order, which are covered in
[[po-issuance-and-change-orders]].

No documented process exists for this activity at the time of this engagement;
the steps below reflect the practice described in interview (SRC-002) and are
correspondingly light on system detail. The volume is material — roughly fifteen
to twenty per month, concentrated at Plant 2 (SRC-002, SRC-005) — so the gaps
recorded in Section E should be closed before this procedure is relied upon.

### B. Quick Reference

- **Trigger:** A supplier invoice arrives with no referenced purchase order for
  goods or services already delivered, and Accounts Payable returns it to
  Procurement.
- **Frequency:** Ad hoc; approximately 15–20 occurrences per month, concentrated
  at Plant 2 (SRC-002, SRC-005 — an unvalidated estimate, not a system-reported
  figure).
- **Preparer:** Procurement Lead or Buyer (TBD — confirm with process owner; see
  GAP-02).
- **Reviewer:** TBD — confirm with process owner (see GAP-03).
- **Primary systems / tools:** Coupa; NetSuite.
- **Key outputs:** An issued confirming purchase order in Coupa, synced to
  NetSuite; the written justification supporting it.

### C. Pre-Requisites

- The supplier exists and is active in both Coupa and NetSuite; if not,
  [[new-vendor-onboarding]] must complete first.
- The goods or services have already been delivered or performed, and the
  supplier has submitted an invoice.
- Accounts Payable has been unable to match the invoice to an existing purchase
  order and has returned it to Procurement.

### D. Inputs

- **Supplier invoice:** Received by Accounts Payable and routed back to
  Procurement.
- **Written justification for the unplanned purchase:** Per the practice
  described, this is expected to come from the Plant Manager; in current practice
  an email from any requesting party is accepted (SRC-002).
- **Purchase detail (supplier, description, quantity, price, cost center /
  account coding):** Provided by the Requester or taken from the invoice face.
  TBD — confirm with process owner which is the governing source.

### E. Step-by-Step Procedure

#### Step 1: Receive the returned invoice from Accounts Payable

Accounts Payable identifies that an invoice references no purchase order for
goods or services already received, and returns it to Procurement for creation
of a confirming purchase order.

- **Expected Result:** Procurement holds an invoice identified as requiring a
  confirming purchase order.

> **VALIDATION REQUIRED — GAP-01:** How an invoice requiring a confirming purchase order is identified and routed back to Procurement — the specific Accounts Payable role that performs the return, the mechanism used (system status, email, queue), and whether the invoice is held or rejected in NetSuite while the purchase order is created.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Obtain the written justification

Procurement obtains a written justification for the unplanned purchase from the
requesting party. The stated expectation is a written justification from the
Plant Manager; the practice described is that an email from any requesting party
is accepted (SRC-002). See [[GAP-04 — JUSTIFICATION STANDARD]] below on which
standard is authoritative.

- **Evidence Required:** The justification email or memo. TBD — confirm with
  process owner where it is retained (see GAP-05).

> **VALIDATION REQUIRED — GAP-04:** JUSTIFICATION STANDARD — whether the written justification must come from the Plant Manager, as stated as the requirement, or from any requester, as described in practice; and whether any approval of the justification is required before the purchase order is created.
> - **Nature:** conflict
> - **Owner to confirm:** Procurement Lead

#### Step 3: Create the confirming purchase order in Coupa

Procurement creates the purchase order in Coupa against the supplier and the
already-delivered goods or services, coded to the requesting cost center.

- **System / Tool:** Coupa
- **Expected Result:** A purchase order is issued and carries a NIG- prefixed
  purchase order number.

> **VALIDATION REQUIRED — GAP-02:** Whether the confirming purchase order is created by the Procurement Lead or by the Buyer responsible for the plant, and whether a requisition is entered first or the purchase order is created directly.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **VALIDATION REQUIRED — GAP-06:** Whether a confirming purchase order is distinguishable from a standard purchase order in Coupa — by document type, custom field, or other flag — and, if not, how the population would be identified for review or reporting.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-01:** The Coupa purchase order entry screen for a confirming purchase order, showing the header fields, supplier, coding, and any field used to flag the document as after-the-fact.

#### Step 4: Route the confirming purchase order for approval

The confirming purchase order is routed for approval before issuance.

> **VALIDATION REQUIRED — GAP-03:** The approval chain applied to a confirming purchase order — whether the standard Coupa requisition approval thresholds documented in [[requisition-and-approval]] apply unchanged, whether an additional or different approver is required because the commitment is already incurred, and who reviews the completed purchase order.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 5: Release the purchase order to NetSuite for invoice processing

Once approved and issued in Coupa, the purchase order syncs to NetSuite so that
Accounts Payable has a document to match the held invoice against, and the
invoice re-enters [[po-invoice-entry-and-three-way-match]].

- **System / Tool:** Coupa; NetSuite
- **Expected Result:** The purchase order is available in NetSuite and the
  supplier invoice can be entered and matched.

> **VALIDATION REQUIRED — GAP-05:** How the goods receipt is recorded for a confirming purchase order, given that the material or service was received before the purchase order existed — who enters the receipt, in which system, and whether the three-way match is completed or bypassed. Also confirm where the justification and the confirming purchase order documentation are retained.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

### F. Key Controls

> **CONTROL — CTRL-001:** A written justification is required to support a purchase order created after the goods or services have been received.
> - **Type:** Detective
> - **Frequency:** Each occurrence
> - **Owner:** TBD — confirm with process owner (see GAP-04)

### G. Outputs

- **Confirming purchase order:** Issued in Coupa with a NIG- prefixed number and
  synced to NetSuite; consumed by [[po-invoice-entry-and-three-way-match]].
- **Written justification:** Retained. TBD — confirm with process owner where
  (see GAP-05).
- **Evidence retained:** TBD — confirm with process owner. No retention
  requirement for this activity was described in the sources.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Purchases are being committed outside the requisition and purchase order process at a rate of roughly fifteen to twenty per month, concentrated at Plant 2, and the purchase order is created only after the supplier has already performed and invoiced.
> - **Impact:** Spend occurs with no competitive or negotiated pricing leverage, since price is agreed after the work is done; the purchase order becomes a formality rather than a commitment control (SRC-002).
> - **Severity:** High

> **PAIN POINT — PP-002:** The requirement for a written justification from the Plant Manager is not enforced as designed; in practice an email from any requesting party is accepted.
> - **Impact:** The only control over after-the-fact commitments operates below its intended standard, and the approval of the unplanned spend is not evidenced by an accountable owner (SRC-002).
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Confirming purchase order volume is not tracked as a metric; the only record is a spreadsheet maintained personally by the Procurement Lead.
> - **Impact:** There is no reliable measure of process leakage, no trend visibility, and no basis for targeting remediation at the plants or requesters driving the volume (SRC-002, SRC-005).
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Establish a reported confirming purchase order metric — flag the document type in Coupa and report volume and value monthly by plant, cost center and requester.
> - **Addresses:** PP-001, PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Document and enforce a single justification standard for confirming purchase orders, naming the required approver and the retention location for the justification.
> - **Addresses:** PP-002

```consult-meta
systems: [coupa, netsuite]
roles:   [procurement-lead, buyer, requester, plant-manager, ap-manager, supplier]
```
