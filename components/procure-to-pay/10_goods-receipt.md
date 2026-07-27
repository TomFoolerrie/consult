## Goods Receipt

### A. Process Overview

Goods Receipt records the physical arrival of purchased goods at the plant receiving docks and creates the NetSuite item receipt that forms the receiving leg of the three-way match. It runs continuously — each inbound carrier delivery — and is performed by Receivers under the Receiving Supervisor at each facility. Receipts are recorded against open purchase orders issued through [[po-issuance-and-change-orders]]; the resulting item receipt is what allows a supplier invoice to release through [[po-invoice-entry-and-three-way-match]], and open receipts with no bill feed the systematic month-end received-not-invoiced accrual (a Record to Report activity outside this process). Returns of damaged or incorrect goods are handled under [[return-to-vendor]], and deliveries that cannot be tied to a purchase order are resolved through [[confirming-po]]. Receipting of services (which involve no dock delivery) and Plant 3's consumption-based auto-receipt arrangement are treated as variants within the steps below, both pending validation.

### B. Quick Reference

- **Trigger:** An inbound carrier delivery at a plant receiving dock (SRC-004).
- **Frequency:** Daily; each delivery, across two receiving shifts (SRC-004).
- **Preparer:** Receiver.
- **Reviewer:** No formal per-receipt review was identified; the Receiving Supervisor provides supervisory oversight and handles discrepancy resolution (SRC-004).
- **Primary systems / tools:** NetSuite (Receive Orders).
- **Key outputs:** NetSuite item receipt; annotated bill of lading for shortage/damage exceptions; filed packing slip.

### C. Pre-Requisites

- An approved, open purchase order exists in NetSuite for the goods being delivered — issued via [[po-issuance-and-change-orders]]; purchase orders originate in Coupa and reach NetSuite on the nightly sync (SRC-005).
- Receiving staff hold NetSuite access to the Receive Orders function (SRC-004).
- The delivery is accompanied by a bill of lading and, in most cases, a packing slip bearing the purchase order number (SRC-004).

### D. Inputs

- **Bill of lading:** presented by the carrier's driver at delivery (SRC-004).
- **Packing slip:** supplied with the shipment; the primary means of identifying the purchase order (SRC-004).
- **Open purchase order:** held in NetSuite, from [[po-issuance-and-change-orders]].
- **Quantity-discrepancy inquiries:** raised by Accounts Payable from the match-exception queue in [[po-invoice-entry-and-three-way-match]] (SRC-001).

### E. Step-by-Step Procedure

The steps below reflect the documented walkthrough of the Plant 2 receiving dock (SRC-004). Plant 1 follows the same flow; Plant 3 differences are covered in Step 7.

#### Step 1: Unload and verify the delivery against the bill of lading

Pieces are counted against the bill of lading and inspects the shipment for visible damage before acceptance. Shortages or damage are noted on the bill of lading and the carrier's driver signs the notation; receiving keeps a copy, which is scanned afterwards (SRC-004).

- **Evidence Required:** Annotated bill of lading copy, signed by the driver, for any shortage or damage exception.

#### Step 2: Identify the purchase order

Locate the purchase order number, normally shown on the packing slip. If the packing slip does not carry it, search NetSuite for an open purchase order by supplier and by item, matching the delivered quantity (SRC-004).

- **Navigation Path:** Transactions > Purchases > Receive Orders

If no open purchase order can be found, the goods are not received into the system. They are moved to the cage — the fenced holding area at the back corner of the Plant 2 dock — until the ordering party is identified; such deliveries typically trace to goods ordered directly from a vendor without a requisition, and resolution runs through an after-the-fact purchase order under [[confirming-po]] (SRC-004, SRC-005).

#### Step 3: Record the item receipt in NetSuite

On the Receive Orders screen, pull up the purchase order, key the quantity received on each line, enter the packing slip number in the Memo field, and save; saving creates the item receipt. For goods going to inventory, print a label and put the items away by location. The stated target is to enter receipts on the day of delivery (SRC-004).

- **Navigation Path:** Transactions > Purchases > Receive Orders
- **Fields / Parameters:** Quantity received per line; packing slip number in the Memo field.
- **Expected Result:** An item receipt is posted against the purchase order and the received quantities update the open purchase order balance.
- **Evidence Required:** Item receipt record in NetSuite; packing slip filed per Step 5.

> **SCREENSHOT PLACEHOLDER — SC-01:** The Receive Orders screen for a purchase order receipt, showing per-line quantity received and the packing slip number keyed in the Memo field, immediately before save — validates the navigation path and the required entry fields.

#### Step 4: Handle partial shipments and over-shipments

- **Condition:** the delivered quantity differs from the ordered quantity

For a partial shipment, receive the quantity actually delivered; the purchase order remains open for the balance (SRC-004). For an over-shipment, NetSuite accepts a receipt above the ordered quantity only up to a configured over-receipt tolerance; above the tolerance the system blocks the receipt, and the Buyer is contacted to process a change order under [[po-issuance-and-change-orders]] before the excess can be received (SRC-004). The tolerance in force is unconfirmed [[GAP-01 — OVER-RECEIPT TOLERANCE]].

> **VALIDATION REQUIRED — GAP-01:** The over-receipt tolerance configured in NetSuite.
> - **Note:** The over-receipt tolerance is unconfirmed — do not operate to a specific percentage or dollar cap; see GAP-01.
> - **Detail:** The Receiving Supervisor recalls approximately ten percent over the ordered quantity plus a dollar cap of possibly five hundred dollars, but is not certain (SRC-004); the consultant working notes flag that the five-hundred-dollar figure may be conflated with the (itself contested) three-way match tolerance, and the prior SOP excerpt does not address over-receipt at all (SRC-005, SRC-006). Pull the NetSuite configuration to confirm both the percentage and any dollar cap.
> - **Nature:** unknown
> - **Owner to confirm:** Buyer

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite block message produced when an attempted receipt exceeds the over-receipt tolerance — validates that the block operates and evidences the live tolerance values (supports closure of the tolerance gap above).

#### Step 5: File receiving documentation and support discrepancy resolution

File the packing slip in the receiving office file cabinet, by month. Packing slips are paper only — they are not scanned — and are retained for approximately two years before moving to the storage container behind the dock (SRC-004). The retention period is as recalled by the Receiving Supervisor and is unconfirmed [[GAP-02 — PACKING SLIP RETENTION]].

When the Senior Accounts Payable Specialist raises a quantity match exception from [[po-invoice-entry-and-three-way-match]] — for example, the bill shows a different quantity than was received — receiving pulls the filed packing slips and re-verifies the quantities; in practice the cause splits roughly evenly between receiving keying errors and supplier errors (SRC-001, SRC-004). Where the error is on the receiving side, the receipt entry is corrected; where receiving documentation is unavailable, the Receiving Supervisor confirms the quantities received in writing, per §5.4 of the prior SOP (CTRL-004) (SRC-006).

> **VALIDATION REQUIRED — GAP-02:** The packing slip retention period and end-of-life arrangement. The Receiving Supervisor recalls approximately two years in the receiving file cabinet followed by transfer to the storage container, but was not certain (SRC-004). Confirm the retention period and whether a records-retention policy governs receiving documentation.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor

#### Step 6: Record receipts for services and non-inventory purchases

- **Condition:** the purchase is a service or non-inventory item (no dock delivery)

Service and non-inventory purchases involve no dock delivery. The Requester's department is expected to record a receipt against the service purchase order in NetSuite to confirm the work or item was delivered (SRC-004). No owner of this receipting could be identified, and no interviewee could describe it operating in practice (SRC-005) — the working process is TBD — confirm with process owner [[GAP-03 — SERVICES RECEIPTING]].

> **VALIDATION REQUIRED — GAP-03:** How receipts against service and non-inventory purchase orders are actually recorded, by whom, and how reliably. The Receiving Supervisor states that departments enter these in NetSuite but does not observe the practice (SRC-004); the consultant working notes record that no one interviewed owns or could describe the process (SRC-005). Walk a services purchase order end to end and identify an owner.
> - **Nature:** unknown
> - **Owner to confirm:** TBD

#### Step 7: Plant variations — consumption-based receipts at Plant 3

- **Condition:** Plant 3 only (Kanban items from the two steel suppliers)

Plant 1 follows the same dock process as Plant 2 (SRC-004). Plant 3 operates a Kanban arrangement with two steel suppliers under which the item receipt posts automatically from consumption rather than at the dock; interviewees could not describe the arrangement in detail and it remains undocumented [[GAP-04 — PLANT 3 AUTO-RECEIPT]] (SRC-004, SRC-005).

> **VALIDATION REQUIRED — GAP-04:** The Plant 3 consumption-based (Kanban) auto-receipt arrangement with the two steel suppliers — how the receipt posts, what triggers it, and what controls apply. The Receiving Supervisor deferred the question and the consultant working notes leave it open; it may be a variant of this procedure or a distinct activity (SRC-004, SRC-005).
> - **Nature:** unknown
> - **Owner to confirm:** Buyer

### F. Key Controls

> **CONTROL — CTRL-001:** Piece counts are verified against the bill of lading and the shipment is inspected for damage before acceptance; shortages and damage are annotated on the bill of lading and acknowledged by the carrier driver's signature (SRC-004).
> - **Type:** Preventive
> - **Frequency:** Each delivery
> - **Owner:** Receiver

> **CONTROL — CTRL-002:** Receipts are recorded only against an open purchase order; deliveries that cannot be tied to one are physically segregated in the cage rather than entered into NetSuite (SRC-004).
> - **Type:** Preventive
> - **Frequency:** Each delivery
> - **Owner:** Receiver

> **CONTROL — CTRL-003:** NetSuite blocks receipt of quantities above the configured over-receipt tolerance; the excess can be received only after the Buyer processes a change order (SRC-004). The tolerance values are unconfirmed — see the validation raised at the over-shipment step in E.
> - **Type:** Preventive
> - **Frequency:** Each receipt (system-enforced)
> - **Owner:** Buyer

> **CONTROL — CTRL-004:** Quantity variances raised in invoice matching are re-verified against retained receiving documentation; where the documentation is unavailable, the Receiving Supervisor confirms the quantities received in writing, per §5.4 of the prior SOP (SRC-004, SRC-006).
> - **Type:** Detective
> - **Frequency:** Per quantity match exception
> - **Owner:** Receiving Supervisor

### G. Outputs

- **Item receipt (NetSuite):** the receiving leg of the three-way match, consumed by [[po-invoice-entry-and-three-way-match]]; open receipts with no bill also drive the systematic month-end received-not-invoiced accrual taken from a NetSuite saved search (a Record to Report activity) (SRC-005, SRC-006).
- **Annotated bill of lading:** documents shortage and damage exceptions, signed by the carrier's driver; a copy is retained and scanned (SRC-004).
- **Labeled, put-away inventory:** inventory items are labeled at receipt and put away by location (SRC-004).
- **Evidence retained:** the NetSuite item receipt; annotated bill of lading copies; paper packing slips filed by month in the receiving office (retention as described in E) (SRC-004).

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Receipts are not consistently entered on the day of delivery. Second shift performs the physical put-away but leaves system keying for the next morning, and on heavy days a Tuesday-afternoon delivery may not be in NetSuite until Thursday; dock staffing is two Receivers on first shift and one on second (SRC-004).
> - **Impact:** Goods physically received but not yet entered account for roughly sixty percent of Accounts Payable's three-way match exceptions, driving rework for the Senior Accounts Payable Specialist and delaying invoice release; the Accounts Payable Manager, the Corporate Controller and the Receiving Supervisor each independently named late receipt entry the process's top issue, and a portion of inventory cycle-count variance traces to late or incorrect receipt entry (SRC-001, SRC-004, SRC-005).
> - **Severity:** High

> **PAIN POINT — PP-002:** Deliveries that cannot be tied to an open purchase order accumulate in the cage at the Plant 2 dock — roughly thirty pallets at the time of the walkthrough, some sitting since fall 2025 — typically goods ordered directly from a vendor without a requisition (SRC-004, SRC-005).
> - **Impact:** Goods on hand remain unreceived in the system with no recorded purchase order or liability until someone claims them; resolution depends on identifying the ordering party and raising an after-the-fact purchase order (SRC-004).
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Receiving documentation is paper only. Packing slips are never scanned; they are filed by month in the receiving office cabinet and later moved to a storage container. A proposal to scan them into Ephesoft was discussed but never implemented (SRC-004).
> - **Impact:** Quantity-discrepancy research requires manual retrieval of paper records, and the consultant working notes flag the paper-only retention as an audit risk (SRC-005).
> - **Severity:** Medium

> **PAIN POINT — PP-004:** Receipting of service and non-inventory purchase orders has no identified owner, and no interviewee could describe the practice operating (SRC-004, SRC-005).
> - **Impact:** A service invoice cannot complete the three-way match until a receipt is recorded — the prior SOP, §5.2 requires the purchase order, the goods receipt and the invoice to be present before release — so unrecorded service receipts stall invoices in [[po-invoice-entry-and-three-way-match]] (SRC-006).
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Deploy handheld barcode scanners at the receiving docks so receipts post in NetSuite at the point of unload; a proposal of approximately sixty thousand dollars was evaluated about two years ago and cut from the budget (SRC-004, SRC-005).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Scan packing slips into Ephesoft at receipt so receiving documentation is retained electronically and is searchable for discrepancy research and audit (SRC-004).
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-003:** Enforce buying channels so goods cannot be ordered by direct vendor contact without a requisition — the Receiving Supervisor's ask is to "make it impossible for people to call a vendor direct" — reducing unidentifiable deliveries into the cage (SRC-004).
> - **Addresses:** PP-002

```consult-meta
systems: [netsuite, coupa, ephesoft]
roles:   [receiver, receiving-supervisor, buyer, requester, supplier, senior-ap-specialist, ap-manager, corporate-controller, carrier]
```
