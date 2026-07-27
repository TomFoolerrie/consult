## Confirming (After-the-Fact) PO

### A. Process Overview

This procedure regularizes purchases made outside the standard requisition process: a supplier has already delivered goods or performed work — typically on an emergency plant call-out — without a requisition or purchase order, and Procurement raises a purchase order after the fact (a "confirming PO") so the invoice can be matched and paid. It runs ad hoc, triggered when Accounts Payable receives a supplier invoice that references no purchase order and returns it to Procurement. The Buyer or Procurement Lead prepares the confirming PO in Coupa, nominally on the strength of a written justification from the Plant Manager. Upstream, the procedure is fed by off-process purchases that bypass [[requisition-and-approval]]; downstream, the confirming PO syncs to NetSuite so the returned invoice can be processed through [[po-invoice-entry-and-three-way-match]]. Standard purchase order issuance and change orders are excluded — see [[po-issuance-and-change-orders]].

### B. Quick Reference

- **Trigger:** A supplier invoice arrives for goods or services already supplied without a purchase order, and Accounts Payable returns it to Procurement.
- **Frequency:** Ad hoc; approximately 15–20 per month, concentrated at Plant 2 (Procurement Lead estimate, SRC-002, corroborated in SRC-005; not validated against system data).
- **Preparer:** Buyer or Procurement Lead.
- **Reviewer:** TBD — confirm with process owner (justification is nominally provided by the Plant Manager; approval routing is unconfirmed).
- **Primary systems / tools:** Coupa (PO creation); NetSuite (receives the PO by sync for invoice matching).
- **Key outputs:** Confirming purchase order; justification documentation; entry in the Procurement Lead's informal log.

### C. Pre-Requisites

- Goods have been delivered or services performed by a supplier without a requisition or purchase order in place.
- The supplier invoice (or other evidence of the purchase) has been returned to Procurement by Accounts Payable.
- The supplier exists in Coupa and NetSuite; a supplier not yet set up must first complete [[new-vendor-onboarding]].

### D. Inputs

- **Supplier invoice with no purchase order reference** — returned by Accounts Payable.
- **Written justification for the purchase** — nominally from the Plant Manager; in current practice an email from the requesting party (Procurement Lead, SRC-002).
- **Details of the goods or services supplied** — from the Requester who engaged the supplier and from the supplier's invoice.

### E. Step-by-Step Procedure

#### Step 1: Identify the off-process purchase and return the invoice to Procurement

In the typical case, a plant is down, a Requester (for example, plant maintenance) calls a supplier directly, the supplier performs the work or delivers the goods, and an invoice arrives with no purchase order behind it (SRC-002). Accounts Payable identifies that no purchase order exists and returns the invoice to Procurement for a confirming PO to be created.

A related symptom surfaces at the receiving dock: a delivery that cannot be tied to an open purchase order — usually the product of the same direct-to-supplier calls — is held in the cage at Plant 2 until someone claims it, rather than arriving through this invoice-driven path (SRC-004).

> **VALIDATION REQUIRED — GAP-01:** Which Accounts Payable role identifies the missing purchase order and returns the invoice to Procurement, and how the returned invoice is held or tracked while the confirming PO is created.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

> **VALIDATION REQUIRED — GAP-02:** Whether deliveries held in the cage are regularized through a confirming PO once claimed, and who initiates that resolution.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor

#### Step 2: Obtain justification for the purchase

Written justification for the off-process purchase is obtained. The stated requirement is a written justification from the Plant Manager; in current practice an emailed justification from any requesting party is accepted (SRC-002; the enforcement drift is documented at PP-002 in H).

- **Evidence Required:** Written justification (in practice, an email); retention location TBD — confirm with process owner.

> **VALIDATION REQUIRED — GAP-03:** Where the Plant Manager justification requirement is formally documented, and where the justification obtained for each confirming PO is retained (for example, whether it is attached to the Coupa PO record).
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 3: Create the confirming PO in Coupa

A purchase order is created in Coupa after the fact, covering the goods or services already supplied. Whether the confirming PO routes through the standard approval chain applied to requisitions (see [[requisition-and-approval]]) or is issued outside it is TBD — confirm with process owner [[GAP-04 — APPROVAL ROUTING]].

> **VALIDATION REQUIRED — GAP-04:** Whether a confirming PO routes through the standard Coupa approval chain used for requisitions, follows a separate path, or is issued without system approval.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-01:** A recent confirming PO record in Coupa, showing the PO creation date relative to the supplier's invoice or service date and how the justification is documented on the record (if at all).

#### Step 4: Confirm the PO is available in NetSuite

The purchase order syncs from Coupa into NetSuite, giving Accounts Payable a purchase order to match the returned invoice against. The invoice cannot be processed until the sync has completed.

- **System / Tool:** Coupa → NetSuite sync

#### Step 5: Complete receipt and invoice matching

Once the confirming PO is available in NetSuite, the returned invoice is processed against it through [[po-invoice-entry-and-three-way-match]]. How the remaining match legs are completed for a purchase that has already been delivered — in particular whether an item receipt or service receipt is recorded against the confirming PO after the fact, and how the returned invoice re-enters entry and matching — is TBD — confirm with process owner [[GAP-05 — MATCH COMPLETION]].

> **VALIDATION REQUIRED — GAP-05:** How the three-way match is completed for a confirming PO: whether a goods or service receipt is recorded against it after the fact (and by whom), and how the previously returned invoice re-enters entry and matching.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 6: Log the confirming PO

The Procurement Lead records the confirming PO in an informal spreadsheet. No formal metric or management reporting on confirming PO volume exists (see PP-003 in H).

- **System / Tool:** Spreadsheet maintained by the Procurement Lead (location TBD — confirm with process owner).

> **SCREENSHOT PLACEHOLDER — SC-02:** The Procurement Lead's confirming PO spreadsheet, showing the fields tracked and recent monthly volume, to substantiate the 15–20 per month estimate.

### F. Key Controls

> **CONTROL — CTRL-001:** A written justification from the Plant Manager is required before a confirming PO is raised for an off-process purchase.
> - **Type:** Preventive
> - **Frequency:** Each confirming PO
> - **Owner:** Procurement Lead

CTRL-001 does not operate as designed in practice; see PP-002 in H.

> **CONTROL — CTRL-002:** Invoices that reference no purchase order are not processed for payment; Accounts Payable returns them to Procurement until a valid purchase order exists.
> - **Type:** Detective
> - **Frequency:** Each occurrence
> - **Owner:** TBD — confirm with process owner

### G. Outputs

- **Confirming purchase order** — created in Coupa and synced to NetSuite; consumed by Accounts Payable to match and pay the previously returned invoice via [[po-invoice-entry-and-three-way-match]].
- **Justification documentation** — the written justification obtained for the purchase (in practice, an email).
- **Informal log entry** — a row in the Procurement Lead's confirming PO spreadsheet.
- **Evidence retained:** TBD — where the justification and its linkage to the PO record are filed was not established during fieldwork; confirm with process owner.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Confirming POs represent spend committed outside the procurement process — approximately 15–20 per month, concentrated at Plant 2 — with the supplier engaged before any purchase order exists.
> - **Impact:** Procurement has no leverage on price, and the purchase is committed before any approval or sourcing control can operate (SRC-002, SRC-005).
> - **Severity:** High

> **PAIN POINT — PP-002:** The written Plant Manager justification nominally required for a confirming PO is not enforced; in practice an email from any requesting party is accepted.
> - **Impact:** The intended authorization control over off-process purchases provides little assurance as operated.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Confirming PO volume is not tracked as a management metric; the only record is an informal spreadsheet maintained by the Procurement Lead.
> - **Impact:** The scale and root causes of off-process purchasing cannot be quantified or systematically addressed.
> - **Severity:** Low

> **PAIN POINT — PP-004:** Deliveries that cannot be tied to an open purchase order — generally the product of the same direct-to-supplier calls that drive confirming POs — accumulate in the cage at Plant 2; roughly thirty pallets were on hand at the time of fieldwork, some present since fall 2025 (SRC-004, SRC-005).
> - **Impact:** Goods sit unclaimed for months with no receipt recorded and no clear resolution path.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Establish formal tracking and management reporting of confirming PO volume (by plant, supplier, and value), replacing the informal spreadsheet, to create visibility into off-process spend.
> - **Addresses:** PP-001, PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Enforce the written Plant Manager justification as a mandatory element of the confirming PO record before the PO is issued.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Close the direct-to-supplier channel that generates confirming POs and cage accumulation — per the Receiving Supervisor, "make it impossible for people to call a vendor direct" (SRC-004) — so that emergency call-outs enter the purchasing process rather than bypass it.
> - **Addresses:** PP-001, PP-004

```consult-meta
systems: [coupa, netsuite]
roles:   [procurement-lead, buyer, plant-manager, requester, ap-manager, receiving-supervisor, supplier]
```
