## Goods Receipt

<!-- scope note: covers variants — Dock receipt (Plants 1 and 2); Service / non-inventory receipt confirmation by department; Plant 3 consumption-based auto-receipt (Kanban). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### A. Process Overview

This procedure covers how the receipt of goods and services against an issued purchase
order is recorded in NetSuite, creating the item receipt that evidences delivery and
supports payment. It runs on delivery — continuously through the working day at the
inbound docks, and on demand where a service or non-inventory purchase is confirmed by
the buying department. Receiving personnel under the Receiving Supervisor perform dock
receipts at Plants 1 and 2; the department that raised the requirement performs service
and non-inventory receipt confirmation; Plant 3 operates a consumption-based automatic
receipt arrangement with two steel suppliers. The procedure begins with the purchase
order issued in [[po-issuance-and-change-orders]] and available in NetSuite, and its
item receipt is the receipt leg consumed by
[[po-invoice-entry-and-three-way-match]]; goods rejected or returned after receipt are
handled in [[return-to-vendor]]. Freight billing and the physical inventory cycle count
programme are outside its scope. (SRC-001, SRC-004, SRC-005)

### B. Quick Reference

- **Trigger:** A carrier delivers goods against a purchase order at an inbound dock; or a purchased service or non-inventory item is delivered and requires confirmation by the buying department; or, at Plant 3, material is consumed under the Kanban arrangement.
- **Frequency:** Continuous through the working day at the docks; on demand for service and non-inventory receipt.
- **Preparer:** Receiving personnel at the dock, under the Receiving Supervisor (Plants 1 and 2); the Requester or department for service and non-inventory receipt (owner unconfirmed — see Step 7).
- **Reviewer:** TBD — confirm with process owner. No review or approval of a posted item receipt was described in the sources; discrepancies are surfaced downstream at invoice match.
- **Primary systems / tools:** NetSuite (Receive Orders, item receipt, Return Authorization); supplier bill of lading and packing slip (paper).
- **Key outputs:** A posted NetSuite item receipt against the purchase order; a printed put-away label for inventory items; the signed and annotated bill of lading and packing slip retained in paper.

### C. Pre-Requisites

- An issued purchase order exists in NetSuite for the delivered goods or services, synced from Coupa (see [[po-issuance-and-change-orders]]).
- The purchase order is open, with an undelivered balance on the lines being received.
- Receiving personnel hold NetSuite access to the Receive Orders function.

### D. Inputs

- **Bill of lading:** Carrier — presented by the driver at the dock and used for the piece count and damage annotation.
- **Packing slip:** Supplier — accompanies the shipment; carries the purchase order reference where the supplier has printed one, and its number is keyed to the receipt.
- **Open purchase order:** NetSuite — the commitment received against, carrying the ordered quantity and price per line.
- **Physical delivery:** Supplier or carrier — the goods themselves, or the delivered service in the case of a service purchase order.

### E. Step-by-Step Procedure

#### Step 1: Receive the delivery at the dock and count against the bill of lading

*Dock receipt (Plants 1 and 2).* The carrier arrives at an assigned dock door and the
driver presents the bill of lading. Receiving personnel count the pieces delivered
against the bill of lading and inspect the shipment for visible damage.

- **Evidence Required:** The bill of lading presented by the driver.

#### Step 2: Annotate and sign for short or damaged shipments

*Dock receipt (Plants 1 and 2).* Where the piece count is short or the goods are
visibly damaged, receiving personnel note the discrepancy on the bill of lading, the
driver signs the annotation, and receiving retains a copy. The retained copy is scanned
subsequently.

- **Expected Result:** The exception is recorded on the bill of lading and acknowledged by the carrier at the point of delivery.
- **Evidence Required:** The annotated, driver-signed bill of lading copy retained by receiving.

> **VALIDATION REQUIRED — GAP-01:** Where the annotated bill of lading copy is scanned to and retained, and whether a damage or shortage noted at the dock is notified to the Buyer or to Accounts Payable at that point or only surfaces at invoice match. The Receiving Supervisor described the annotation and the subsequent scan but named no destination system and no notification.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor

#### Step 3: Identify the purchase order the delivery relates to

*Dock receipt (Plants 1 and 2).* Receiving personnel identify the purchase order the
delivery is to be received against. The purchase order reference is normally printed on
the packing slip. Where it is not — which occurs frequently on smaller maintenance,
repair and operations deliveries — receiving personnel search NetSuite by supplier and
by item for an open purchase order with a matching quantity.

- **System / Tool:** NetSuite
- **Navigation Path:** Transactions > Purchases > Receive Orders
- **Fields / Parameters:** Supplier; item; open purchase order quantity.
- **Expected Result:** An open purchase order line is identified for the delivered goods.

#### Step 4: Hold unidentifiable deliveries pending ownership

*Dock receipt (Plants 1 and 2).* Where no purchase order can be identified, the goods
are moved to the fenced holding area at the plant — referred to locally as "the cage" —
and remain there until a requester claims them. Deliveries arriving without a purchase
order are attributed to purchases placed directly with a supplier without a
requisition; these are addressed as confirming purchase orders in [[confirming-po]].

- **Expected Result:** The delivery is segregated and no receipt is posted.

> **VALIDATION REQUIRED — GAP-02:** The process, if any, for clearing the holding area — who reviews the goods held there, on what cadence, how a requester is identified and notified, and how the goods are ultimately received, returned or written off. The Receiving Supervisor described the holding area and its accumulation but described no clearing routine; approximately thirty pallets were held at the time of the walkthrough, some since autumn 2025.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor, with the Procurement Lead

#### Step 5: Enter the receipt in NetSuite

*Dock receipt (Plants 1 and 2).* Receiving personnel open the identified purchase order
in the Receive Orders screen, key the quantity received on each line, enter the packing
slip number in the memo field, and save. Saving creates the item receipt against the
purchase order.

Where only part of the ordered quantity has been delivered, the quantity actually
received is keyed and the purchase order remains open for the balance.

- **System / Tool:** NetSuite
- **Navigation Path:** Transactions > Purchases > Receive Orders
- **Fields / Parameters:** Quantity received per line; packing slip number (memo field).
- **Expected Result:** An item receipt is posted against the purchase order, and the purchase order balance is reduced by the quantity received.
- **Evidence Required:** The posted NetSuite item receipt carrying the packing slip number.

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite Receive Orders screen with a purchase order open for receipt, showing the quantity-received field per line and the memo field carrying the packing slip number, to validate the navigation path and the fields keyed.

#### Step 6: Handle an over-shipment against the receiving tolerance

*Dock receipt (Plants 1 and 2).* Where the supplier has delivered more than the ordered
quantity, NetSuite permits the receipt up to a configured over-receipt tolerance. Above
that tolerance the receipt is blocked, and receiving personnel refer the over-shipment
to the Buyer, who raises a change order against the purchase order (see
[[po-issuance-and-change-orders]]) before the excess can be received.

- **System / Tool:** NetSuite
- **Expected Result:** An over-shipment within tolerance posts as received; an over-shipment above tolerance is blocked pending a change order.

> **VALIDATION REQUIRED — GAP-03:** The over-receipt tolerance configured in NetSuite — both the percentage and the dollar cap, and how the two interact. The Receiving Supervisor believed the tolerance to be approximately ten percent with a dollar cap of around five hundred dollars but explicitly could not confirm either figure, and the tolerance is not documented elsewhere. The configuration should be pulled from NetSuite rather than confirmed by recollection. Note also that the over-receipt tolerance is a distinct control from the invoice matching tolerance applied in [[po-invoice-entry-and-three-way-match]]; the two were conflated during the walkthrough, and confirming both values should establish which is which for the people operating them.
> - **Nature:** unknown
> - **Owner to confirm:** Buyer, with the IT Manager

#### Step 7: Confirm receipt of a service or non-inventory purchase

*Service and non-inventory receipt.* Where the purchase is for a service or another
non-inventory item — a contractor engagement or an engineering study are the examples
cited — there is no physical delivery to a dock. The department that raised the
requirement is understood to enter a receipt in NetSuite against the service purchase
order to confirm that the service was performed. Beyond that, the procedure is not
established: no owner has been identified and no participant was able to describe how
the confirmation is performed or monitored.

- **System / Tool:** NetSuite
- **Expected Result:** TBD — confirm with process owner. See [[GAP-04 — SERVICE PO RECEIPT PROCESS]].

> **VALIDATION REQUIRED — GAP-04:** The entire service and non-inventory receipt process. Required: the role that owns and performs the receipt confirmation, the NetSuite navigation path and fields used, what evidence supports the confirmation that a service was performed, the trigger and expected timing relative to the supplier invoice, and whether any monitoring exists for service purchase orders left unreceipted. The Receiving Supervisor confirmed that services are not received at the dock and that a departmental receipt is the intended mechanism, but stated he never sees it and does not know whether it works; no other source described it. A service purchase order should be walked end to end before this step is documented.
> - **Nature:** unknown
> - **Owner to confirm:** TBD — no owner identified; to be assigned by the Procurement Lead with the Accounts Payable Manager.

#### Step 8: Consumption-based automatic receipt at Plant 3

*Plant 3 (Kanban).* Plant 3 operates a Kanban arrangement with two steel suppliers under
which the receipt posts automatically on consumption of the material rather than on
physical delivery at a dock. The mechanism was identified but not walked through, and
is not documented here.

- **Expected Result:** TBD — confirm with process owner. See [[GAP-05 — PLANT 3 KANBAN AUTO-RECEIPT]].

> **VALIDATION REQUIRED — GAP-05:** The Plant 3 consumption-based automatic receipt arrangement in full. Required: which two steel suppliers it covers, what triggers the automatic receipt and in which system it posts, what purchase order or blanket commitment it releases against, who monitors that automatic receipts post correctly and how a failure is detected, and how the arrangement is reconciled to physical inventory. The Receiving Supervisor identified the arrangement but stated he does not understand it well enough to describe and referred it to the Buyer covering Plants 2 and 3, who has not been re-interviewed. This variant may prove to be a distinct activity rather than a variant of dock receipt.
> - **Nature:** unknown
> - **Owner to confirm:** Buyer

#### Step 9: Label and put away inventory items

*Dock receipt (Plants 1 and 2).* For goods going to inventory, receiving personnel print
a put-away label and the goods are put away by storage location.

- **System / Tool:** NetSuite
- **Expected Result:** The received goods are in their storage location and the on-hand balance reflects the receipt.

#### Step 10: File the packing slip

*Dock receipt (Plants 1 and 2).* The paper packing slip is filed in the receiving office
filing cabinet by month. Packing slips are held there for approximately two years and
are then moved to the external storage container. They are not scanned or imaged.

- **Evidence Required:** The paper packing slip, filed by month in the receiving office.

> **VALIDATION REQUIRED — GAP-06:** The formal retention period for receiving documentation — packing slips and bills of lading — and the total period held including the external storage container. The Receiving Supervisor gave approximately two years in the receiving office as a recollection and could not state a policy period or a destruction point.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor, with the Corporate Controller

#### Step 11: Support the resolution of downstream match exceptions

Where a quantity discrepancy is identified at invoice match, the Senior Accounts Payable
Specialist contacts the Receiving Supervisor and the two review the retained packing
slips for the period in question to establish whether the discrepancy arose from a
keying error at receipt or from the supplier's shipment. The receipt is corrected or the
discrepancy referred to the Buyer accordingly. Resolution of the exception itself sits
in [[po-invoice-entry-and-three-way-match]].

- **Evidence Required:** The filed paper packing slip for the delivery in question.

> **VALIDATION REQUIRED — GAP-07:** How a receipt found to be keyed incorrectly is corrected in NetSuite — whether the item receipt is edited, reversed and re-entered, or adjusted, and whether any approval is required to change a posted receipt. The Receiving Supervisor described identifying keying errors through this route but not how they are corrected.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor, with the Senior Accounts Payable Specialist

### F. Key Controls

> **CONTROL — CTRL-001:** Count and damage inspection against the bill of lading — pieces delivered are counted and inspected against the carrier's bill of lading before the delivery is accepted, and any shortage or damage is annotated on the bill of lading and signed by the driver at the point of delivery.
> - **Type:** Detective
> - **Frequency:** Each delivery
> - **Owner:** Receiving Supervisor

> **CONTROL — CTRL-002:** Purchase order basis for receipt — a receipt is posted only against an identified open purchase order in NetSuite; a delivery that cannot be tied to a purchase order is segregated in the plant holding area and no receipt is posted.
> - **Type:** Preventive
> - **Frequency:** Each delivery
> - **Owner:** Receiving Supervisor

> **CONTROL — CTRL-003:** Over-receipt tolerance — NetSuite blocks receipt of a quantity exceeding the ordered quantity beyond a configured tolerance, requiring a Buyer change order before the excess can be received. The tolerance value is unconfirmed (see Step 6).
> - **Type:** Preventive
> - **Frequency:** Each receipt exceeding the ordered quantity
> - **Owner:** Buyer

> **CONTROL — CTRL-004:** Service and non-inventory receipt confirmation — receipt against a service purchase order is intended to evidence that the service was performed before the supplier invoice is paid. No owner has been identified and no operating detail could be described; the control cannot be confirmed as operating (see Step 7).
> - **Type:** Preventive
> - **Frequency:** TBD — confirm with process owner
> - **Owner:** TBD — confirm with process owner

### G. Outputs

- **NetSuite item receipt:** Posted against the purchase order, carrying the quantity received per line and the packing slip number in the memo field; consumed as the receipt leg of the match in [[po-invoice-entry-and-three-way-match]] and as the basis for the received-not-invoiced accrual.
- **Put-away label:** Printed for inventory items and used to place the goods by storage location.
- **Reduced purchase order balance:** The purchase order remains open for any undelivered balance following a partial receipt.
- **Evidence retained:** The paper packing slip, filed by month in the receiving office for approximately two years and then moved to external storage; the bill of lading, annotated and driver-signed where a shortage or damage was identified. Receiving documentation is not scanned or imaged.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Receipts are entered late. Same-day entry is the target and is generally met on first shift, but second shift performs the physical put-away and leaves the keying for the following morning, and heavy or short-staffed days extend this further; a delivery arriving on a Tuesday afternoon may not be in NetSuite until Thursday. The dock runs two receivers on first shift and one on second.
> - **Impact:** Invoices arrive for goods that are physically on site but not yet received in NetSuite, so the bill has no receipt to match against. Late receipts account for roughly sixty percent of the Senior Accounts Payable Specialist's match exceptions, and the Accounts Payable Manager, the Corporate Controller and the Receiving Supervisor independently identified this as the single largest source of downstream rework in the payables cycle. It is also a contributor to inventory count variance, which runs at roughly ninety-six to ninety-seven percent accuracy.
> - **Severity:** High

> **PAIN POINT — PP-002:** Deliveries arrive that cannot be tied to a purchase order and accumulate in the plant holding area. Approximately thirty pallets were held at Plant 2 at the time of the walkthrough, some since autumn 2025, and the accumulation is attributed to purchases placed directly with suppliers without a requisition.
> - **Impact:** Goods on site are neither received nor available to the requester, capital is tied up in unrecorded inventory, and the associated supplier invoices arrive with no purchase order and no receipt behind them. No routine exists to clear the area.
> - **Severity:** High

> **PAIN POINT — PP-003:** Receipt entry is fully manual and keyed from paper. Purchase order identification frequently requires a search of NetSuite by supplier and item where the packing slip carries no purchase order reference, and quantities are keyed by hand, producing keying errors that surface only downstream at invoice match.
> - **Impact:** Receipt entry is slow, contributing directly to the late-entry problem, and roughly half of the quantity discrepancies investigated at invoice match trace to a receiving keying error rather than to the supplier.
> - **Severity:** High

> **PAIN POINT — PP-004:** Packing slips exist only on paper. They are filed by month in the receiving office and moved to an external storage container, are never scanned or imaged, and are the sole evidence of what was physically delivered.
> - **Impact:** Investigating a match exception requires physically retrieving paper from the receiving office or the storage container, and receiving evidence is exposed to loss or damage with no second copy.
> - **Severity:** Medium

> **PAIN POINT — PP-005:** The receiving-side thresholds are not known to the people who operate them. The Receiving Supervisor could not state the over-receipt tolerance and conflated it with the invoice matching tolerance.
> - **Impact:** Whether an over-shipment is accepted or blocked cannot be predicted or explained at the dock, and the distinction between the two tolerances is not understood by the role that encounters them.
> - **Severity:** Medium

> **PAIN POINT — PP-006:** Service and non-inventory receipt has no identified owner and no described process, and the Plant 3 consumption-based automatic receipt arrangement could not be explained by any participant available.
> - **Impact:** Two of the three receipt variants cannot be evidenced as operating. Service purchase orders may be invoiced and paid without any confirmation that the service was performed, and the automatic posting at Plant 3 is unmonitored so far as could be established.
> - **Severity:** High

> **IMPROVEMENT OPPORTUNITY — IO-001:** Deploy handheld barcode scanners at the docks to read the supplier barcode from the packing slip and post the receipt at the point of delivery. The Receiving Supervisor identified this as his first priority; the initiative was evaluated approximately two years ago at around sixty thousand dollars and was not funded. Point-of-delivery posting would remove both the keying delay and the manual quantity entry.
> - **Addresses:** PP-001, PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish a receipt-entry service level with daily monitoring of unposted deliveries, and review second-shift coverage so that keying is not deferred to the following morning.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-003:** Institute a scheduled review of the plant holding area with a named owner, a defined ageing threshold and a disposition path — claim and receive, return to supplier, or write off — and pair it with the controls over direct-to-supplier ordering addressed in [[confirming-po]] so that the inflow is reduced as well as the backlog cleared.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-004:** Image receiving documentation — packing slips and annotated bills of lading — at the point of receipt and attach it to the NetSuite item receipt, so that match exception investigation works from the system record rather than from paper retrieval.
> - **Addresses:** PP-004

> **IMPROVEMENT OPPORTUNITY — IO-005:** Pull the NetSuite over-receipt tolerance configuration, document it alongside the invoice matching tolerance so the two are visibly distinct, and communicate both to receiving and to the buyers.
> - **Addresses:** PP-005

> **IMPROVEMENT OPPORTUNITY — IO-006:** Walk a service purchase order and the Plant 3 Kanban arrangement end to end, assign an owner to each, and document them before either is relied upon as a control.
> - **Addresses:** PP-006

```consult-meta
systems: [netsuite, coupa]
roles:   [receiving-supervisor, buyer, senior-ap-specialist, ap-manager, procurement-lead, requester, corporate-controller, it-manager, supplier]
```
