## Return to Vendor

### A. Process Overview

This procedure covers how goods already received from a supplier are authorised for
return, shipped back, and recorded in NetSuite as a Return Authorization against the
original item receipt. It runs on exception, when goods are found to be damaged or
incorrect. The Receiving Supervisor initiates the return at the plant and the Buyer
obtains the return authorisation from the supplier. The procedure begins from a posted
item receipt created in [[goods-receipt]], and it is intended to result in a supplier
credit that reduces the payable; how that credit is recorded and applied against the
supplier invoice is not established and is not documented here (see Step 6). Disposal
of deliveries that could not be tied to a purchase order in the first place is not a
return and is handled in [[goods-receipt]]. (SRC-004, SRC-005)

### B. Quick Reference

- **Trigger:** Goods received against a purchase order are found to be damaged or incorrect.
- **Frequency:** On exception. TBD — confirm with process owner; no volume or rate was described in the sources.
- **Preparer:** Receiving Supervisor (initiation and physical return); Buyer (return authorisation from the supplier).
- **Reviewer:** TBD — confirm with process owner. No review or approval of a return was described in the sources.
- **Primary systems / tools:** NetSuite (Return Authorization against the item receipt); email between receiving and the Buyer.
- **Key outputs:** A NetSuite Return Authorization; the supplier RMA number; the goods shipped back to the supplier; an expected supplier credit memo.

### C. Pre-Requisites

- The goods were received against a purchase order and an item receipt is posted in NetSuite (see [[goods-receipt]]).
- The damage or error has been identified on the goods physically held at the plant.
- A Buyer is assigned to the purchase order and can contact the supplier.

### D. Inputs

- **Posted item receipt:** NetSuite — the receipt the return is raised against.
- **Rejected goods:** Held at the plant — the damaged or incorrect items being returned.
- **Supplier RMA number:** Supplier, obtained by the Buyer — the supplier's authorisation reference for the return.

### E. Step-by-Step Procedure

#### Step 1: Identify goods to be returned

Receiving personnel identify goods that are damaged or that do not correspond to what
was ordered, and set them aside from the put-away stream.

- **Expected Result:** The affected goods are segregated pending return authorisation.

> **VALIDATION REQUIRED — GAP-01:** How and when goods requiring return are identified and by whom, including whether returns are limited to damage and wrong-item found at the dock or also cover items rejected later by the requesting department or by quality inspection, and whether any condition or value threshold determines that goods are returned rather than accepted or scrapped. The Receiving Supervisor described returns only as "if it's damaged or wrong," with no criteria, threshold or approval named.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor

#### Step 2: Notify the Buyer

The Receiving Supervisor emails the Buyer responsible for the purchase order to advise
that goods are to be returned.

- **Expected Result:** The Buyer is aware of the return and can approach the supplier.
- **Evidence Required:** TBD — confirm with process owner. The notification is described as an email; no template, distribution list or retention location was named. See [[GAP-02 — RETURN NOTIFICATION CONTENT AND RETENTION]].

> **VALIDATION REQUIRED — GAP-02:** What the return notification to the Buyer must contain (purchase order, item receipt, item, quantity, reason code, photographs), whether it follows any standard form, and where it is retained as evidence of the return request. The Receiving Supervisor described only "I email the buyer."
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor, with the Buyer

#### Step 3: Obtain the return material authorisation from the supplier

The Buyer contacts the supplier and obtains a return material authorisation (RMA)
number for the goods being returned.

- **Expected Result:** The supplier has authorised the return and issued an RMA number.
- **Evidence Required:** The supplier's RMA number.

> **VALIDATION REQUIRED — GAP-03:** Where the supplier RMA number is recorded and retained — whether it is entered on the NetSuite Return Authorization, held in the Buyer's email only, or recorded elsewhere — and what happens when a supplier declines to authorise a return or does not respond. Neither the recording location nor any exception path was described.
> - **Nature:** unknown
> - **Owner to confirm:** Buyer

#### Step 4: Enter the Return Authorization in NetSuite

A Return Authorization is entered in NetSuite against the original item receipt for the
items and quantities being returned.

- **System / Tool:** NetSuite
- **Navigation Path:** TBD — confirm with process owner.
- **Fields / Parameters:** TBD — confirm with process owner.
- **Expected Result:** A Return Authorization exists in NetSuite referencing the item receipt the goods were received on.
- **Evidence Required:** The NetSuite Return Authorization record.

> **VALIDATION REQUIRED — GAP-04:** The role that enters the Return Authorization, the NetSuite navigation path and the fields keyed, whether any approval is required before it is saved, and how the Return Authorization affects the on-hand inventory balance and the purchase order. The Receiving Supervisor stated "we do a Return Authorization in NetSuite against the receipt" without identifying the individual role, the path, the fields or the accounting effect.
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor, with the IT Manager

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite Return Authorization created against an item receipt, showing the linkage to the originating receipt and purchase order, the returned quantity per line, and the field carrying the supplier RMA number, to validate the navigation path and the fields keyed.

#### Step 5: Ship the goods back to the supplier

The goods are shipped back to the supplier on the supplier's carrier account.

- **Expected Result:** The rejected goods leave the plant against the supplier's RMA, at the supplier's freight cost.

> **VALIDATION REQUIRED — GAP-05:** The shipping documentation raised for a return and where it is retained, how the outbound shipment is evidenced against the Return Authorization, and how a return shipped on the supplier's account is handled where the supplier disputes freight cost or where the return arises from a cause other than supplier fault. The Receiving Supervisor described only that returns ship "on the vendor's account."
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor

#### Step 6: Record and apply the supplier credit

A credit memo from the supplier is expected following a return. How that credit is
obtained, recorded in NetSuite and applied against the supplier's open payable is not
established and is not documented here. See
[[GAP-06 — VENDOR CREDIT MEMO RECORDING AND APPLICATION]].

- **Expected Result:** TBD — confirm with process owner.
- **Evidence Required:** TBD — confirm with process owner.

> **VALIDATION REQUIRED — GAP-06:** The entire vendor credit leg of the return. Required: the role that requests and chases the credit memo from the supplier, how an outstanding expected credit is tracked and aged, how the credit memo is entered in NetSuite once received, how it is applied against the supplier's open payable or the original invoice, whether an offsetting entry is made where the invoice has already been paid, and what monitoring exists for returns where no credit is ever received. The Receiving Supervisor stated that a credit memo is "supposed to be" issued, that he does not track whether it arrives, and that he believes Accounts Payable chases it; no source described the credit application step, and the working notes record it as undocumented. A return should be walked end to end from Return Authorization to credit application before this step is documented.
> - **Nature:** unknown
> - **Owner to confirm:** TBD — no owner identified; to be assigned by the Accounts Payable Manager with the Receiving Supervisor.

### F. Key Controls

> **CONTROL — CTRL-001:** Supplier return authorisation before shipment — the Buyer obtains an RMA number from the supplier before the goods are shipped back, so that no rejected goods leave the plant without the supplier having authorised their return.
> - **Type:** Preventive
> - **Frequency:** Each return
> - **Owner:** Buyer

> **CONTROL — CTRL-002:** Return recorded against the originating receipt — the return is entered in NetSuite as a Return Authorization against the item receipt the goods were received on, linking the return to the original purchase order and receipt.
> - **Type:** Preventive
> - **Frequency:** Each return
> - **Owner:** TBD — confirm with process owner. The role entering the Return Authorization was not identified (see Step 4).

### G. Outputs

- **NetSuite Return Authorization:** Raised against the originating item receipt for the items and quantities returned.
- **Supplier RMA number:** Obtained by the Buyer from the supplier and authorising the return shipment.
- **Returned goods:** Shipped back to the supplier on the supplier's carrier account.
- **Expected supplier credit memo:** Anticipated following the return; its receipt, recording and application against the payable are not established (see Step 6).
- **Evidence retained:** TBD — confirm with process owner. No retention location was described for the return notification, the RMA number or the return shipping documentation.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The vendor credit resulting from a return is not tracked. A credit memo is expected after a return, but the Receiving Supervisor does not track whether it is received and believed, without confirmation, that Accounts Payable pursues it. No participant described how an expected credit is monitored, recorded or applied.
> - **Impact:** A return can be shipped back to the supplier with no assurance that the corresponding credit is ever received or applied, so the payable may remain overstated and the value of returned goods may be paid for. No source could state whether this occurs or how often.
> - **Severity:** High

> **PAIN POINT — PP-002:** The return process has no identified single owner. Initiation sits with receiving, supplier authorisation with the Buyer, and the credit leg is assumed to sit with Accounts Payable without confirmation, so the handoffs between the three are undefined.
> - **Impact:** A return that stalls between the plant, the Buyer and Accounts Payable has no owner to escalate it, and no participant could describe the process end to end.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** The return is conducted largely outside a system record. The request to the Buyer is an ad hoc email, the supplier RMA number has no confirmed recording location, and no retention location was identified for the return notification or the return shipping documentation.
> - **Impact:** Evidence that a return was authorised, shipped and credited cannot be assembled from the system record, and the population of returns cannot be established for testing.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Establish and document the vendor credit leg end to end — assign an owner for chasing the credit memo, record the expected credit at the point the Return Authorization is raised, and define how the credit is entered in NetSuite and applied against the supplier's open payable.
> - **Addresses:** PP-001, PP-002

> **IMPROVEMENT OPPORTUNITY — IO-002:** Introduce an aged report of Return Authorizations with no matching supplier credit received, reviewed on a defined cadence by a named owner, so that unreceived credits are visible rather than relying on individual follow-up.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-003:** Capture the return in the system record from the outset — a structured return request replacing the ad hoc email, the supplier RMA number recorded on the NetSuite Return Authorization, and the return shipping documentation attached to it.
> - **Addresses:** PP-003

```consult-meta
systems: [netsuite]
roles:   [receiving-supervisor, buyer, ap-manager, supplier, it-manager]
```
