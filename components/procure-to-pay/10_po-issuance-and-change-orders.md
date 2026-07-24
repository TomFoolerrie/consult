## PO Issuance and Change Orders

<!-- scope note: covers variants — Standard PO issuance (cXML / PDF transmission); Change order (re-route on value increase); Blanket PO with annual not-to-exceed. Document the shared flow once; branch at the step(s) where the variants diverge. -->

### A. Process Overview

This procedure covers how a fully approved requisition becomes a purchase order in
Coupa, how that purchase order is transmitted to the supplier and carried into
NetSuite, and how an issued purchase order is subsequently amended by change order.
It runs on demand as requisitions reach fully approved status, and it covers three
variants that share one flow: a standard purchase order transmitted by cXML or PDF, a
change order that creates a new version of an existing purchase order, and a blanket
purchase order carrying an annual not-to-exceed value that is released against by
receipt. Coupa cuts and transmits the purchase order; the Procurement Lead and the
Buyer own the purchase order once issued, and the Requester or Buyer initiates change
orders. The procedure begins where [[requisition-and-approval]] ends, at the fully
approved requisition, and does not restate the requisition approval ladder documented
there. Its output is the commitment that [[goods-receipt]] receives against and that
[[po-invoice-entry-and-three-way-match]] matches to; purchases made without a
purchase order in place are covered by [[confirming-po]]. (SRC-002, SRC-005)

### B. Quick Reference

- **Trigger:** A requisition reaches fully approved status in Coupa; or a Requester or Buyer needs to amend an issued purchase order.
- **Frequency:** On demand.
- **Preparer:** Coupa cuts the purchase order from the approved requisition; the Requester or Buyer prepares a change order.
- **Reviewer:** For a change order that increases value, the approvers determined by the Coupa approval chain (see [[requisition-and-approval]]).
- **Primary systems / tools:** Coupa (purchase order creation, cXML and PDF transmission, change order versioning, blanket purchase orders and the not-to-exceed burn-down report); NetSuite (purchase order record for matching).
- **Key outputs:** An issued purchase order numbered `NIG-` plus a sequential number, transmitted to the supplier and synced to NetSuite; change order versions of that purchase order; blanket purchase orders carrying an annual not-to-exceed value.

### C. Pre-Requisites

- The requisition is at fully approved status in Coupa (see [[requisition-and-approval]]).
- The supplier is transactable in both Coupa and NetSuite (see [[new-vendor-onboarding]]).
- For transmission by cXML, the supplier is one of the approximately sixty suppliers enabled for cXML in Coupa; otherwise the supplier has an email address on file to receive the purchase order PDF.
- For a change order, an issued purchase order exists in Coupa to be amended.

### D. Inputs

- **Fully approved requisition:** Coupa — released from [[requisition-and-approval]], carrying the lines, supplier, values and accounting to be placed on the purchase order.
- **Supplier transmission profile:** Coupa — whether the supplier is cXML-enabled or receives a PDF by email.
- **Change request:** Requester or Buyer — the amendment to be made to an issued purchase order (quantity, value, or other line detail).
- **Annual not-to-exceed value:** Buyer — for a blanket purchase order covering recurring spend.

### E. Step-by-Step Procedure

#### Step 1: Confirm the purchase order variant

The Buyer confirms which variant applies. A standard purchase order is cut for a
one-time or discrete purchase. A blanket purchase order is used for recurring spend —
janitorial services, the gas supplier, and the tooling consignment arrangement are the
arrangements cited — and carries an annual not-to-exceed value that is released against
by receipt rather than by a new purchase order for each drawdown. A change order
applies where a purchase order has already been issued and requires amendment, and is
covered from Step 6.

- **System / Tool:** Coupa

> **VALIDATION REQUIRED — GAP-01:** The criteria by which a purchase is placed on a blanket purchase order rather than a standard purchase order, and who makes that determination. Sources name the arrangements currently on blanket purchase orders but describe no selection rule.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 2: Cut the purchase order in Coupa

Once the requisition is fully approved, Coupa creates the purchase order from it. The
purchase order is numbered in the `NIG-` format followed by a sequential number.

For a blanket purchase order, the annual not-to-exceed value is set on the purchase
order. Subsequent drawdowns are released against that value by receipt, and the
blanket purchase order blocks further release once the not-to-exceed value is reached.

- **System / Tool:** Coupa
- **Fields / Parameters:** Purchase order number (`NIG-` plus sequential); supplier; lines and values carried from the approved requisition; annual not-to-exceed value (blanket purchase orders only).
- **Expected Result:** An issued purchase order exists in Coupa against the approved requisition.

> **VALIDATION REQUIRED — GAP-02:** Whether Coupa cuts the purchase order automatically on final requisition approval or whether a Buyer action is required to release it, and whether the Buyer can amend the purchase order before it transmits. Sources state only that Coupa cuts the purchase order and transmits it once the requisition is fully approved.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-01:** The issued purchase order in Coupa, showing the `NIG-` number format, the linked requisition, and — for a blanket purchase order — the annual not-to-exceed field.

#### Step 3: Transmit the purchase order to the supplier

Coupa transmits the issued purchase order to the supplier. Suppliers enabled for
cXML — approximately sixty of the supplier base — receive the purchase order by cXML.
All other suppliers receive the purchase order as a PDF by email.

- **System / Tool:** Coupa
- **Expected Result:** The supplier holds the issued purchase order.

> **VALIDATION REQUIRED — GAP-03:** How failed transmissions are identified and handled — whether Coupa reports a cXML transmission failure or an undelivered PDF email, who monitors for them, and how the purchase order is re-sent. No exception path was described in the sources.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 4: Sync the purchase order to NetSuite

The issued purchase order syncs from Coupa into NetSuite, so that a NetSuite purchase
order record exists for goods receipt and for the three-way match performed in
[[po-invoice-entry-and-three-way-match]].

- **System / Tool:** Coupa, NetSuite
- **Expected Result:** The purchase order is present in NetSuite and available to receive and match against.

> **VALIDATION REQUIRED — GAP-04:** The timing and mechanism of the Coupa-to-NetSuite purchase order sync (whether it runs on the same nightly schedule as the supplier sync or separately), whether any monitoring or failure alerting exists on it, and who owns remediation when it fails. Sources record that Coupa-to-NetSuite sync failures occur and consume around three hours of effort each time, but no owner for the sync could be named.
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager, with the Procurement Lead

#### Step 5: Monitor blanket purchase order burn-down

*Blanket purchase orders only.* Receipts drawn against a blanket purchase order consume
the annual not-to-exceed value. Coupa provides a burn-down report showing consumption
against the not-to-exceed value, but the report is not run on a schedule and no owner
has been identified for it; consumption is therefore not actively monitored, and the
first indication that the not-to-exceed value has been reached is the blocking of
further releases — see [[GAP-05 — BLANKET NTE BURN-DOWN OWNERSHIP]].

- **System / Tool:** Coupa
- **Expected Result:** TBD — confirm with process owner. No monitoring cadence or review outcome is currently defined.

> **VALIDATION REQUIRED — GAP-05:** The owner and the cadence for the Coupa blanket purchase order not-to-exceed burn-down report, and the action to be taken when consumption approaches the not-to-exceed value (for example raising a replacement or uplifted blanket purchase order). The report exists, but sources state that nobody runs it on a schedule and that no owner exists. This must be assigned rather than assumed.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-02:** The Coupa blanket purchase order not-to-exceed burn-down report, to validate that the report exists, what it shows, and the parameters required to run it.

#### Step 6: Raise a change order against an issued purchase order

*Change orders only.* The Requester or Buyer edits the issued purchase order in Coupa.
Coupa creates a new version of the purchase order — the first amendment produces
version 2 — recording the change against the original purchase order number.

- **System / Tool:** Coupa
- **Fields / Parameters:** The amended purchase order lines, quantities or values.
- **Expected Result:** A new version of the purchase order exists in Coupa.
- **Evidence Required:** The Coupa purchase order version history.

> **VALIDATION REQUIRED — GAP-06:** Whether any justification, comment or supporting documentation is required on a change order, and whether the Buyer reviews change orders raised directly by a Requester. Sources state only that the Requester or Buyer edits the purchase order.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 7: Re-route the change order for approval where the value increases

*Change orders only.* Where the change increases the purchase order value, Coupa
re-routes the purchase order for approval. Where the change decreases the value, it does
not re-route. The re-routing is understood to be driven by the amended purchase order
value against the standing Coupa approval chain — the same ladder applied at
requisition in [[requisition-and-approval]] — so that an amended value crossing a
higher breakpoint brings in the approver at that breakpoint. This was contested during
the interview; see [[GAP-07 — CHANGE ORDER RE-ROUTING RULE]].

- **System / Tool:** Coupa
- **Fields / Parameters:** Amended purchase order total value.
- **Expected Result:** An increased-value change order is pending with the approvers determined by the amended value; a decreased-value change order proceeds without further approval.
- **Evidence Required:** The Coupa approval record on the purchase order version.

> **VALIDATION REQUIRED — GAP-07:** The exact change order re-routing rule configured in Coupa. Sources conflict: the Procurement Lead stated that an increase of less than ten percent returns only to the Cost Center Owner rather than the full chain, while the Buyer stated there is no percentage grace and the change order re-routes to whichever approver the amended value reaches. The Procurement Lead accepted the Buyer's account during the interview, but the Buyer qualified it as roughly eighty percent certain and confirmed he had never read the configuration. The Coupa approval chain export should be pulled and the change order rule confirmed against it.
> - **Nature:** conflict
> - **Owner to confirm:** Procurement Lead, with the Buyer

> **SCREENSHOT PLACEHOLDER — SC-03:** The Coupa change order configuration and an approved change order's version history and approval chain, to validate the re-routing rule and the approvers applied at the amended value.

#### Step 8: Transmit and sync the amended purchase order

*Change orders only.* Once the change order is approved, the amended purchase order
version is transmitted to the supplier and synced to NetSuite on the same basis as the
original issue in Steps 3 and 4, so that receipt and matching operate against the
current purchase order value.

- **System / Tool:** Coupa, NetSuite
- **Expected Result:** The supplier and NetSuite hold the current purchase order version.

> **VALIDATION REQUIRED — GAP-08:** Whether an approved change order re-transmits to the supplier automatically on the same cXML or PDF basis as the original purchase order, and how the amended value updates the NetSuite purchase order where receipts or bills already exist against the prior version. Not described in the sources.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

### F. Key Controls

> **CONTROL — CTRL-001:** Approved-requisition basis — a purchase order is cut in Coupa only from a fully approved requisition, so no commitment is transmitted to a supplier without the approvals applied in [[requisition-and-approval]].
> - **Type:** Preventive
> - **Frequency:** Each purchase order
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-002:** Change order re-approval — a change order that increases the purchase order value is re-routed by Coupa for approval before the amended purchase order takes effect; a decrease does not re-route. The precise re-routing rule is in dispute; see Step 7.
> - **Type:** Preventive
> - **Frequency:** Each value-increasing change order
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-003:** Blanket purchase order not-to-exceed cap — releases against a blanket purchase order are limited to the annual not-to-exceed value recorded on the purchase order, and further release is blocked once that value is consumed.
> - **Type:** Preventive
> - **Frequency:** Continuous, on each release against a blanket purchase order
> - **Owner:** TBD — confirm with process owner; no owner has been identified for blanket purchase order not-to-exceed monitoring (see Step 5).

> **CONTROL — CTRL-004:** Purchase order versioning — Coupa records each amendment as a new purchase order version against the original purchase order number, retaining the change history and the approvals applied to each version.
> - **Type:** Detective
> - **Frequency:** Each change order
> - **Owner:** Procurement Lead

### G. Outputs

- **Issued purchase order:** Numbered `NIG-` plus a sequential number, transmitted to the supplier by cXML or PDF email and available in NetSuite for [[goods-receipt]] and [[po-invoice-entry-and-three-way-match]].
- **Blanket purchase order:** Carrying an annual not-to-exceed value, released against by receipt.
- **Change order versions:** Amended purchase order versions in Coupa against the original purchase order number.
- **Evidence retained:** The Coupa purchase order record with its version history and, for value-increasing change orders, the approval chain record on the amended version.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Blanket purchase order not-to-exceed consumption is not monitored. A Coupa burn-down report exists but is not run on a schedule and has no owner, so the first signal that the annual not-to-exceed value has been reached is the blocking of further releases.
> - **Impact:** Blanket purchase orders are reported to reach their not-to-exceed value around month nine, at which point releases block without warning and the Buyer fields escalations from the affected departments while a replacement commitment is arranged.
> - **Severity:** High

> **PAIN POINT — PP-002:** The change order re-routing rule is not understood by the people who operate it. The Procurement Lead and the Buyer gave different accounts of whether a percentage grace applies to value increases, and neither had reviewed the Coupa configuration.
> - **Impact:** Whether a change order receives the approval its amended value warrants cannot be stated with confidence, and an increase could pass at a lower approval level than intended.
> - **Severity:** High

> **PAIN POINT — PP-003:** The Coupa-to-NetSuite integration fails intermittently and has no identified owner or monitoring. When a record does not sync, the failure is found through its downstream effects rather than through an alert.
> - **Impact:** Each failure is reported to consume roughly three people for an hour, and a purchase order absent from NetSuite cannot be received or matched, delaying downstream processing.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Assign an owner and a recurring cadence to the Coupa blanket purchase order not-to-exceed burn-down report, with a defined consumption threshold at which the Buyer initiates a replacement or uplifted blanket purchase order before releases block.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Pull the Coupa approval chain export, confirm the configured change order re-routing rule, and document it so that Procurement operates to the live configuration rather than to recollection.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Assign ownership of the Coupa-to-NetSuite integration and implement failure alerting with a defined remediation path, so sync failures are detected at the point of failure rather than downstream.
> - **Addresses:** PP-003

```consult-meta
systems: [coupa, netsuite]
roles:   [procurement-lead, buyer, requester, cost-center-owner, supplier, it-manager]
```
