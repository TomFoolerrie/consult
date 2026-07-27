## Return to Vendor

### Scope

This procedure covers the return of received material to the supplier where the
material is damaged or is not what was ordered: obtaining a return authorization
from the supplier, recording a Return Authorization in NetSuite against the
original item receipt, and shipping the material back. Physical acceptance,
inspection and entry of the original receipt are excluded and are documented in
[[goods-receipt]]; amendment of the purchase order is excluded and is documented
in [[po-issuance-and-change-orders]]. The vendor credit expected to follow the
return, and its application against the supplier account, was not described by any
source and is recorded as a gap rather than documented — the matching and
disposition of supplier bills is documented in
[[po-invoice-entry-and-three-way-match]]. Material held at the dock that could
never be tied to a purchase order is not a return and is dealt with in
[[goods-receipt]]. (SRC-004, SRC-005)

### At a Glance

| Field | Value |
|---|---|
| Trigger | Received material is found to be damaged or incorrect |
| Frequency | As required; no frequency or volume was established (TBD — confirm with process owner) |
| Preparer | Receiving Supervisor, with the Buyer obtaining the return authorization from the supplier |
| Reviewer | None — no review or approval of a return was described by any source |
| Systems | NetSuite (Return Authorization against the item receipt); email to the Buyer |
| Key inputs | Posted NetSuite item receipt; the damaged or incorrect material; supplier return authorization (RMA) number |
| Key outputs | NetSuite Return Authorization; material shipped back on the supplier's carrier account; an expected supplier credit memo |

### Before You Start

- **NetSuite item receipt** — [[goods-receipt]]; posted against the purchase order
  lines covering the material being returned.
- **Damaged or incorrect material** — held at the plant and identified to the
  receipt it was posted under.
- **Supplier return authorization (RMA) number** — obtained from the supplier by
  the Buyer; required before the return is recorded and shipped.

### Procedure

#### Step 1: Identify received material as damaged or incorrect

Material that has been received is found to be damaged or not what was ordered,
and is identified to the item receipt it was posted under. (SRC-004)

#### Step 2: Request a return authorization from the supplier

The Receiving Supervisor emails the Buyer, who obtains a return authorization
(RMA) number from the supplier. (SRC-004)

- **System / Tool:** email to the Buyer; the RMA number originates with the
  supplier and outside any client system.
- **Expected Result:** a supplier RMA number is available to record against the
  return.

> **VALIDATION REQUIRED — GAP-01:** The timing, content and evidence of the return authorization request are unconfirmed.
> - **Note:** No standard request form, required information or turnaround expectation is supported — confirm before treating the email as a controlled step.
> - **Detail:** The only account of this step is the Receiving Supervisor's statement that he emails the Buyer and the Buyer gets an RMA number from the supplier (SRC-004). No source describes what the request must contain, how quickly the supplier is expected to respond, whether the email is retained, or what happens where the supplier declines or does not respond.
> - **Nature:** unknown
> - **Owner to confirm:** Buyer

#### Step 3: Record the Return Authorization in NetSuite against the receipt

A Return Authorization is entered in NetSuite against the original item receipt
for the material being returned. (SRC-004)

- **Fields / Parameters:** the item receipt the return is raised against.

> **VALIDATION REQUIRED — GAP-02:** The NetSuite navigation path, required fields and approval routing for a Return Authorization are unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite Return Authorization created against an item receipt, showing the lines returned and the reference to the supplier RMA number.

#### Step 4: Ship the material back to the supplier

The material is shipped back to the supplier on the supplier's carrier account.
(SRC-004)

#### Step 5: Obtain and apply the supplier credit memo

A supplier credit memo is expected to follow the return. Neither the receipt of
the credit nor its application against the supplier account is documented: the
Receiving Supervisor does not track whether the credit arrives and understands
that Accounts Payable pursues it, and no source described the credit application
step. TBD — confirm with process owner. See [[GAP-03 — CREDIT MEMO APPLICATION]].
(SRC-004, SRC-005)

> **VALIDATION REQUIRED — GAP-03:** The receipt, recording and application of the vendor credit memo following a return has no described process and no confirmed owner.
> - **Note:** No step detail, timing, system path, or accountable role is supported — treat credit recovery on returns as undefined rather than assuming it follows ordinary bill processing.
> - **Detail:** The Receiving Supervisor stated that after the return there is supposed to be a credit memo, that whether the credit ever shows up is not something he tracks, and that he thinks Accounts Payable chases it (SRC-004). The working notes carry the same item as thin and insufficient to document, recording that the Return Authorization is raised in NetSuite by the Receiving Supervisor and that no one described the credit application step (SRC-005). No source names how the credit is received, how it is entered, how it is matched to the Return Authorization or the original bill, who is accountable, or whether open returns awaiting credit are monitored.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

### Outputs & Evidence

- **NetSuite Return Authorization** — recorded against the original item receipt,
  reversing the received quantity for the lines returned.
- **Material returned to the supplier** — shipped on the supplier's carrier
  account.
- **Evidence retained:** the Return Authorization in NetSuite and its link to the
  item receipt raised in [[goods-receipt]].
- **Not retained:** no source describes retention of the supplier RMA number, of
  the email requesting it, or of return shipping documentation; no log of returns
  awaiting a supplier credit is maintained, so an unreceived credit is not
  visible anywhere.

### Key Controls

> **CONTROL — CTRL-001:** Material is not returned to a supplier until a return authorization (RMA) number has been obtained from that supplier by the Buyer.
> - **Type:** Preventive
> - **Frequency:** each return
> - **Owner:** Buyer

> **CONTROL — CTRL-002:** The Return Authorization is recorded in NetSuite against the original item receipt, so that the returned quantity is reversed against the purchase order lines it was received on.
> - **Type:** Preventive
> - **Frequency:** each return
> - **Owner:** Receiving Supervisor

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** No one tracks whether the supplier credit expected after a return is ever received.
> - **Note:** The return is recorded and the material is shipped back, but the credit is assumed to be pursued by Accounts Payable and no source could describe the step or name an owner.
> - **Detail:** The Receiving Supervisor stated that a credit memo is supposed to follow the return, that whether the credit ever shows up is not something he tracks, and that he believes Accounts Payable chases it (SRC-004). The working notes record the return-to-credit handoff as insufficiently supported to document, noting that the Return Authorization is raised in NetSuite and that no one described the credit application step (SRC-005). No monitoring, ageing report or reconciliation of open returns against credits received was described by anyone.
> - **Impact:** Credits due on returned material may never be received or applied, and the exposure is not quantified because open returns awaiting credit are not visible in any report.
> - **Severity:** High

> **IMPROVEMENT OPPORTUNITY — IO-001:** Establish and assign ownership of the credit recovery step, supported by a report of Return Authorizations with no matching supplier credit, so that returns awaiting credit are aged and pursued rather than assumed.
> - **Addresses:** PP-001

```consult-meta
systems: [netsuite]
roles:   [receiving-supervisor, buyer, ap-manager]
```
