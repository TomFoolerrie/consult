## Putaway and Bin Confirmation

### Scope

This procedure covers the movement of received material from the receiving
area to its warehouse storage bin and the confirmation of that move in
NetSuite. It begins after the goods receipt has been posted; the dock check
of the delivery against the purchase order (PO) and the posting of the goods
receipt in Coupa are performed under the Procure to Pay process and are
explicitly excluded here. Corrections to item-vendor records, including unit
of measure setup, are likewise owned by the Procure to Pay process. Book-to-floor
variances that originate at this handoff are detected downstream by
[[cycle-count-execution]].

### At a Glance

| Field | Value |
|---|---|
| Trigger | A goods receipt is posted for an inbound delivery |
| Frequency | Each posted goods receipt |
| Preparer | Material Handler |
| Reviewer | None identified in the current state |
| Systems | NetSuite |
| Key inputs | Posted goods receipt; palletized material staged at receiving |
| Key outputs | Confirmed bin transfer in NetSuite; material stored in its bin |

### Before You Start

- **Posted goods receipt** — supplied by the Procure to Pay receiving process
  (posted in Coupa); must be posted before putaway begins (SRC-001).
- **Staged material** — the received pallets, dock-checked and visually
  inspected for damage under the Procure to Pay receiving process, staged and
  ready to move
  (SRC-001).

### Procedure

#### Step 1: Identify material ready for putaway

Once the goods receipt posts, the received pallets are ready for putaway
(SRC-001).

#### Step 2: Move the pallets to the system-suggested bin

The pallets are moved to the storage bin that the system suggests (SRC-001).

> **VALIDATION REQUIRED — GAP-01:** How the suggested bin is generated and
> communicated to the Material Handler (device, printed ticket, or on-screen
> task) is unconfirmed, as is the handling of a full or blocked suggested bin.
> - **Nature:** unknown
> - **Owner to confirm:** Warehouse Manager

#### Step 3: Scan the bin and confirm the move in NetSuite

At the destination bin, the bin is scanned and the move is confirmed in
NetSuite, updating the on-hand location record (SRC-001).

- **Evidence Required:** Confirmed bin transfer record in NetSuite.

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite bin confirmation screen
> for a completed putaway, showing the item, quantity, and confirmed bin.

#### Step 4: Flag a suspected unit of measure discrepancy to the Procurement Lead

- **Condition:** the on-hand quantity created by the receipt is inconsistent
  with the physical material (e.g., eaches received against a case-based
  item-vendor record)

Suspected unit of measure errors on the item-vendor record are flagged to the
Procurement Lead; correcting the vendor record is performed under the Procure
to Pay process (SRC-001).

> **VALIDATION REQUIRED — GAP-02:** How the flag to the Procurement Lead is
> raised and tracked (email, ticket, or verbal) is unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Warehouse Manager

### Outputs & Evidence

- **Confirmed bin transfer in NetSuite** — the on-hand record reflects the
  storage bin; this record is what subsequent counts under
  [[cycle-count-execution]] are performed against.
- **Evidence retained:** the bin confirmation transaction in NetSuite (SRC-001).
- **Not retained:** no independent record of putaway accuracy is produced;
  errors introduced at receipt or putaway surface only when a later cycle
  count detects them (SRC-001).

### Key Controls

> **CONTROL — CTRL-001:** Bin scan confirmation — the destination bin is
> scanned and the move is confirmed in NetSuite before the putaway is
> complete, verifying the material was placed in the system-directed location.
> - **Type:** Preventive
> - **Frequency:** Each putaway
> - **Owner:** Material Handler

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Receiving errors propagate undetected into inventory.
> - **Note:** A short count or a receipt posted against the wrong PO line makes
>   the inventory wrong from the first day, and there is no check at putaway
>   that would catch it.
> - **Detail:** The Warehouse Manager describes the receipt-posted-to-putaway-
>   confirmed handoff as where most book-to-floor variances are born: if the
>   receiver short-counts or posts against the wrong PO line, the on-hand
>   record is wrong from day one and the error is only detected weeks later
>   when the cycle count reaches that location (SRC-001).
> - **Impact:** Book-to-floor variances persist for weeks until a cycle count
>   detects them (SRC-001).
> - **Severity:** High

> **PAIN POINT — PP-002:** Unit of measure errors on item-vendor records
> distort on-hand quantities.
> - **Impact:** A wrong unit of measure causes receiving to post eaches as
>   cases, leaving on-hand off by a factor of twelve; the warehouse team can
>   only flag the record to the Procurement Lead and absorb the fallout until
>   it is corrected (SRC-001).
> - **Severity:** Medium

```consult-meta
systems: [netsuite, coupa]
roles:   [material-handler, warehouse-manager, procurement-lead]
```
