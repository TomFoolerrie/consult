## Goods Receipt

<!-- scope note: covers variants — Dock receipt against PO (Plants 1 and 2); Plant 3 consumption-based auto-receipt (TBD); Services / non-inventory receipt confirmation by department (TBD). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Scope

This procedure covers the recording of receipt against an open purchase order:
physical acceptance of a delivery at the plant receiving dock, identification of
the purchase order it belongs to, and entry of the item receipt in NetSuite that
evidences the quantity received. It covers all three current-state variants — dock
receipt at Plant 1 and Plant 2, the consumption-based automatic receipt operated
at Plant 3, and the confirmation of a services or non-inventory receipt by the
buying department — although only the dock variant was described in sufficient
detail to document. Issuance and amendment of the purchase order itself are
excluded and are documented in [[po-issuance-and-change-orders]], as is the
matching of the supplier invoice to the receipt, documented in
[[po-invoice-entry-and-three-way-match]]. Returning received material to the
supplier is excluded and is documented in [[return-to-vendor]]. Cycle counting and
inventory accuracy, freight and collect-shipment billing, and the received-not-invoiced
accrual are outside this procedure. (SRC-001, SRC-004, SRC-005)

### At a Glance

| Field | Value |
|---|---|
| Trigger | A carrier delivery arrives at the plant receiving dock against an open purchase order; for the Plant 3 and services variants, see the branch steps in Procedure |
| Frequency | Continuous, each delivery; same-day entry is the stated target |
| Preparer | Receiver, under the Receiving Supervisor, at Plant 1 and Plant 2; the buying department for a services purchase order (TBD — confirm with process owner) |
| Reviewer | None — no review or approval of an entered item receipt was described by any source |
| Systems | NetSuite (Receive Orders, item receipt); paper bill of lading and supplier packing slip at the dock |
| Key inputs | Open purchase order in NetSuite; carrier bill of lading; supplier packing slip |
| Key outputs | NetSuite item receipt against the purchase order lines; inventory labelled and put away by location; filed paper packing slip |

### Before You Start

- **Open purchase order in NetSuite** — [[po-issuance-and-change-orders]];
  synchronized from Coupa and open for the quantity being delivered.
- **Carrier bill of lading** — handed over by the driver on arrival; must be
  counted against and signed before the carrier leaves.
- **Supplier packing slip** — accompanies the shipment; carries the purchase order
  number where the supplier has quoted it.
- **Delivery** — physically unloaded at the dock door and available for piece
  count and damage inspection.

### Procedure

#### Step 1: Take delivery and count the shipment against the bill of lading

The carrier arrives at a dock door and the driver hands over the bill of lading.
Pieces are counted against the bill of lading and the shipment is visually
inspected for damage before the driver is released. (SRC-004)

- **Evidence Required:** the counted and signed bill of lading.

#### Step 2: Annotate the bill of lading for a short or damaged delivery

- **Condition:** the piece count is short of the bill of lading, or material is
  visibly damaged

The discrepancy is noted on the bill of lading, the driver signs the annotation, a
copy is retained at the dock and scanned subsequently. (SRC-004)

> **VALIDATION REQUIRED — GAP-01:** The destination and retention of the scanned annotated bill of lading are unknown.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor

#### Step 3: Identify the purchase order the delivery belongs to

The purchase order number is normally taken from the supplier packing slip. Where
the packing slip does not carry it — which occurs frequently on smaller
maintenance, repair and operations deliveries — the open purchase order is
searched for in NetSuite by supplier and by item, matching on the expected
quantity. (SRC-004)

- **Navigation Path:** Transactions > Purchases > Receive Orders.
- **Expected Result:** an open purchase order line is identified for the delivered
  material, or the delivery cannot be tied to a purchase order and follows the next
  step.

#### Step 4: Segregate a delivery that cannot be tied to a purchase order

- **Condition:** no open purchase order can be found for the delivered material

The material is moved to the fenced holding area at the dock known as the cage,
where it is held unreceived until somebody claims it. No item receipt is entered
and the material does not enter inventory. (SRC-004)

- **Expected Result:** the delivery is held outside the system; nothing posts, and
  no supplier invoice for it can match.

#### Step 5: Enter the item receipt in NetSuite

The purchase order is opened on the Receive Orders screen, the quantity received
is keyed per line, the packing slip number is entered in the memo field and the
transaction is saved, creating the item receipt. Same-day entry is the stated
target. (SRC-004)

- **Navigation Path:** Transactions > Purchases > Receive Orders.
- **Fields / Parameters:** quantity received per purchase order line; packing slip
  number in the memo field.
- **Expected Result:** an item receipt exists against the purchase order lines and
  the received quantity is available to the three-way match in
  [[po-invoice-entry-and-three-way-match]].

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite Receive Orders screen for an open purchase order, showing quantity received keyed per line and the packing slip number in the memo field.

#### Step 6: Label and put away inventory material

- **Condition:** the received material is inventory rather than non-inventory or
  direct-charge

A label is printed and the material is put away by location. (SRC-004)

#### Step 7: Leave the purchase order open on a partial shipment

- **Condition:** the quantity delivered is less than the quantity ordered

Only the quantity that physically arrived is received. The purchase order remains
open for the balance and no change order is required. (SRC-004)

#### Step 8: Refer a blocked over-receipt to the Buyer

- **Condition:** the quantity delivered exceeds the purchase order quantity by more
  than the configured receiving tolerance

NetSuite permits receipt of an over-shipment up to a configured tolerance. Above
that tolerance the receipt is blocked and cannot be entered; the Buyer is asked to
raise a change order increasing the purchase order quantity, per
[[po-issuance-and-change-orders]], after which the increased quantity can be
received. See [[GAP-02 — OVER-RECEIPT TOLERANCE]]. (SRC-004, SRC-005)

> **VALIDATION REQUIRED — GAP-02:** The over-receipt tolerance that blocks entry is unconfirmed.
> - **Note:** The tolerance is unconfirmed — do not operate to a figure; obtain the configured NetSuite value before applying it.
> - **Detail:** The Receiving Supervisor recalled a percentage tolerance of approximately 10% and believed there is also a dollar cap of perhaps $500, while stating that he did not know the figures exactly and deferring to the Buyer or to whoever configured the tolerance (SRC-004). The working notes record the over-receipt tolerance as insufficiently supported to document, note that it does not appear in the prior SOP excerpt, and flag that the Receiving Supervisor may be conflating it with the disputed three-way match tolerance (SRC-005). The NetSuite configuration has not been pulled. The same gap is open against [[po-issuance-and-change-orders]], which carries the change order side of the branch.
> - **Nature:** unknown
> - **Owner to confirm:** Buyer

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite message blocking a receipt that exceeds the configured over-receipt tolerance, showing the tolerance applied.

#### Step 9: File the packing slip

The paper packing slip is filed in the receiving office cabinet by month. Packing
slips are not scanned or imaged anywhere. (SRC-004, SRC-005)

- **Evidence Required:** the filed paper packing slip, which is the only evidence
  of what physically arrived.

#### Step 10: Research a receipt queried by a downstream match exception

- **Condition:** a bill has failed the three-way match on quantity and the query
  reaches the dock

The Senior Accounts Payable Specialist raises the discrepancy with the Receiving
Supervisor by email, and the relevant filed packing slips are retrieved and
compared against the entered receipt to establish whether the difference is a
keying error at receipt or a supplier shipping difference. Correction of the bill
is documented in [[po-invoice-entry-and-three-way-match]]. (SRC-004)

#### Step 11: Post the receipt automatically from consumption at Plant 3

- **Condition:** Plant 3 only

Plant 3 operates a Kanban arrangement with its two principal steel suppliers under
which the receipt posts automatically from consumption rather than from a dock
transaction. TBD — confirm with process owner. See
[[GAP-03 — PLANT 3 CONSUMPTION-BASED RECEIPT]]. (SRC-004, SRC-005)

> **VALIDATION REQUIRED — GAP-03:** The Plant 3 consumption-based automatic receipt is undocumented.
> - **Note:** No step detail for this variant is supported — do not execute or review Plant 3 receipts against this procedure until the variant has been walked through.
> - **Detail:** The Receiving Supervisor described Plant 3 as operating a Kanban arrangement with two steel suppliers in which the receipt auto-posts off consumption, stated that he did not understand it well enough to explain it, and deferred to the Buyer covering Plant 2 and Plant 3 (SRC-004). The working notes carry the same item as thin and insufficient to document, record that the Buyer has not been re-interviewed on it, and note that it may prove to be a distinct activity rather than a variant of this one (SRC-005). No trigger, system path, control or evidence for the variant has been described by anyone.
> - **Nature:** unknown
> - **Owner to confirm:** Buyer

#### Step 12: Confirm receipt of a service or non-inventory purchase against the purchase order

- **Condition:** the purchase order is for a service or other non-inventory item
  with no physical delivery

Where there is no delivery to a dock, a person in the buying department is
understood to enter a receipt in NetSuite against the service purchase order to
confirm that the service was performed. TBD — confirm with process owner. See
[[GAP-04 — SERVICES RECEIPT CONFIRMATION]]. (SRC-004, SRC-005)

> **VALIDATION REQUIRED — GAP-04:** The services and non-inventory receipt confirmation has no described process and no owner.
> - **Note:** No step detail, timing, or accountable role for this variant is supported — treat services receipting as undefined rather than as the dock flow performed by a department.
> - **Detail:** The Receiving Supervisor stated that services receipting is not performed at his dock, that somebody in the department has to enter a receipt against the service purchase order to record that the work happened, that he knows this to be the process but never sees it, and that he doubts it works well (SRC-004). The working notes record that nobody owns services purchase order receipting, that no process was described by any interviewee, and that a services purchase order still needs to be walked end to end (SRC-005). No source names the role that performs it, the timing, or any evidence produced.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

### Outputs & Evidence

- **NetSuite item receipt** — recorded against the purchase order lines; supplies
  the received quantity leg of the three-way match in
  [[po-invoice-entry-and-three-way-match]] and the receipt against which a return
  is raised in [[return-to-vendor]].
- **Inventory put away** — labelled and stored by location for inventory material.
- **Evidence retained:** the item receipt and its packing slip number in NetSuite;
  the signed bill of lading, including any shortage or damage annotation; paper
  packing slips filed in the receiving office cabinet by month, then moved to the
  outside storage container. The retention period was recalled as approximately two
  years but is unconfirmed (TBD — confirm with process owner).
- **Not retained:** packing slips are paper only and are never scanned or attached
  to any system record, so no image of receiving evidence exists; no record is kept
  of material held in the cage, of how long it has been held, or of its
  disposition; the lag between physical delivery and receipt entry is not measured
  or recorded anywhere.

### Key Controls

> **CONTROL — CTRL-001:** Pieces are counted and the shipment is inspected for damage against the carrier bill of lading before the driver is released, and any shortage or damage is annotated on the bill of lading and signed by the driver.
> - **Type:** Preventive
> - **Frequency:** each delivery
> - **Owner:** Receiving Supervisor

> **CONTROL — CTRL-002:** An item receipt is entered only against an identified open purchase order; material that cannot be tied to a purchase order is segregated in the cage and is not received into inventory.
> - **Type:** Preventive
> - **Frequency:** each delivery
> - **Owner:** Receiving Supervisor

> **CONTROL — CTRL-003:** NetSuite blocks entry of a receipt exceeding the purchase order quantity by more than the configured tolerance, requiring a change order before the quantity can be received.
> - **Type:** Preventive
> - **Frequency:** each receipt exceeding the tolerance
> - **Owner:** Buyer

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Receipts are entered late, so goods are physically on site while the purchase order shows nothing received.
> - **Note:** Late receipt entry is the single largest driver of downstream invoice match exceptions and was named independently as the top pain point by the Accounts Payable Manager, the Senior Accounts Payable Specialist and the Receiving Supervisor.
> - **Detail:** Same-day entry is the target and is generally achieved by first shift on a normal day, but second shift performs the physical put-away and leaves the keying for the following morning, so a delivery arriving one afternoon may not appear in NetSuite two days later; the Receiving Supervisor attributes this to staffing — two receivers on first shift and one on second — and states he has no additional person (SRC-004). The Senior Accounts Payable Specialist attributes approximately 60% of her match exceptions to receipts not yet entered, and the Accounts Payable Manager states that same-day receipting would halve exception volume (SRC-001, SRC-005). The Receiving Supervisor further notes that a portion of the inventory cycle-count variance, against accuracy of roughly 96–97%, traces back to receipts entered late or entered wrong (SRC-004).
> - **Impact:** Bills are matched against nothing and route to Match Exception - Hold, consuming Accounts Payable capacity, delaying supplier payment and contributing to inventory record inaccuracy.
> - **Severity:** High

> **PAIN POINT — PP-002:** Deliveries that cannot be tied to a purchase order accumulate indefinitely in the cage with no disposition process.
> - **Note:** Roughly thirty pallets are held in the cage at Plant 2, some since autumn 2025, and no process exists to identify, receive or return them.
> - **Detail:** The Receiving Supervisor describes the cage as holding anything that cannot be tied to a purchase order until somebody claims it, estimates approximately thirty pallets, and states that some has been there since the previous autumn (SRC-004). He attributes the material to buyers or departments contacting a supplier directly without raising a requisition, and the working notes record the cage among the pain points voiced, with the same root cause (SRC-005). No source describes any review, ageing report, escalation or write-off of cage material.
> - **Impact:** Material that has been paid for or will be invoiced sits unreceived and off the books, inventory is understated, and the underlying off-process buying goes undetected.
> - **Severity:** High

> **PAIN POINT — PP-003:** Packing slips exist only on paper and are never imaged, so the primary evidence of what was physically received is not retrievable outside the receiving office.
> - **Note:** Packing slips are filed by month in a cabinet at the dock and then moved to an outside storage container; a proposal to scan them into the document capture application was never implemented.
> - **Detail:** The Receiving Supervisor states that packing slips are paper only, filed by month in the receiving file cabinet for approximately two years before moving to the storage container out back, and that although scanning them into the imaging system had been discussed it never happened (SRC-004). The working notes carry the same item under evidence and retention and flag it explicitly as an audit risk (SRC-005). Retrieval of a packing slip to resolve an invoice match exception therefore requires a physical search at the plant.
> - **Impact:** Receipt evidence cannot be produced remotely or attached to the transaction, match exception research is slow, and there is no protection against loss or destruction of the only copy.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Deploy handheld barcode scanners at the dock that read the supplier barcode from the packing slip and post the item receipt at the door, removing the deferred keying step that drives late receipts.
> - **Note:** The Receiving Supervisor names this as the single change he would make; it was evaluated approximately two years ago at around $60,000 and was cut.
> - **Addresses:** PP-001, PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Prevent direct supplier ordering outside the requisition process, so that material cannot arrive without a purchase order to receive it against, and establish an ageing review and disposition rule for material already held in the cage.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Scan packing slips into the document capture application already used for supplier invoices and attach the image to the NetSuite item receipt, making receiving evidence retrievable with the transaction.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-004:** Measure and report the elapsed time between physical delivery and item receipt entry by plant and shift, so that the receipting lag driving downstream match exceptions is visible rather than inferred from Accounts Payable exception volume.
> - **Addresses:** PP-001

```consult-meta
systems: [netsuite, coupa, ephesoft]
roles:   [receiving-supervisor, receiver, buyer, senior-ap-specialist, ap-manager, procurement-lead, requester]
```
