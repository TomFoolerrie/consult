## Return to Vendor

### Scope

Return to Vendor covers the return of damaged or incorrect goods to the supplier after they have been received at a plant dock, and the follow-through to the vendor credit that should result. The goods being returned were recorded through [[goods-receipt]]; the expected vendor credit memo ultimately offsets the supplier's account in Accounts Payable, where invoice activity is processed under [[po-invoice-entry-and-three-way-match]]. Ordinary shortage and damage notations taken at the dock before acceptance are part of [[goods-receipt]], not this procedure.

### At a Glance

| Field | Value |
|---|---|
| Trigger | Goods identified as damaged or incorrect after receipt at the dock (SRC-004) |
| Frequency | As needed, per occurrence; no volume was stated (SRC-004) |
| Preparer | Receiving Supervisor (return initiation and NetSuite entry); Buyer (return authorization with the supplier) (SRC-004) |
| Reviewer | TBD — confirm with process owner; no review step was described (SRC-004, SRC-005) |
| Systems | NetSuite (Return Authorization); email for the return request to the Buyer |
| Key inputs | Damaged or incorrect goods; original NetSuite item receipt; supplier-issued RMA number |
| Key outputs | NetSuite Return Authorization; return shipment on the supplier's freight account; expected vendor credit memo |

### Before You Start

- **Damaged or incorrect goods** — identified at or after receipt as goods that must go back to the supplier (SRC-004).
- **Original item receipt** — [[goods-receipt]]; posted in NetSuite, since the Return Authorization is entered against that receipt (SRC-004).
- **RMA number** — issued by the supplier and obtained by the Buyer before the return is processed (SRC-004).

### Procedure

#### Step 1: Identify the goods to be returned and notify the Buyer

When goods are found to be damaged or incorrect, the Buyer is emailed to request a return (SRC-004). Damage or shortage visible at unloading is annotated on the bill of lading under [[goods-receipt]]; this procedure applies to goods that have been received and must now go back.

#### Step 2: Obtain the RMA number from the supplier

The Buyer contacts the supplier and obtains an RMA number authorizing the return (SRC-004). No documented criteria for when a supplier may refuse a return, and no timing expectation for the RMA, were described.

#### Step 3: Enter the Return Authorization in NetSuite

The Receiving Supervisor's team enters a Return Authorization in NetSuite against the original item receipt (SRC-004). The specific navigation path and required fields were not demonstrated during the walkthrough — TBD — confirm with process owner [[GAP-01 — RETURN AUTHORIZATION ENTRY]].

- **Navigation Path:** TBD — confirm with process owner
- **Expected Result:** A Return Authorization exists in NetSuite, tied to the original receipt, relieving the returned quantity.

> **VALIDATION REQUIRED — GAP-01:** The NetSuite navigation path, required fields (including where the supplier's RMA number is recorded), and the inventory/GL effect of the Return Authorization entry. The Receiving Supervisor described the step in one sentence during the walkthrough and it was not demonstrated on screen (SRC-004).
> - **Nature:** unknown
> - **Owner to confirm:** Receiving Supervisor

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite Return Authorization screen for a completed return, showing the link to the original item receipt and the RMA reference — validates the entry path and required fields once confirmed.

#### Step 4: Ship the goods back on the supplier's account

The returned goods are shipped back to the supplier on the supplier's freight account, referencing the RMA number (SRC-004). What shipping documentation is retained for the return was not described — TBD — confirm with process owner.

#### Step 5: Obtain and apply the vendor credit memo

A credit memo from the supplier is expected to follow the return. The Receiving Supervisor does not track whether the credit arrives and believes Accounts Payable chases it, but no one in Accounts Payable described monitoring open returns or applying vendor credits, and the consultant working notes record the credit application step as undescribed by any interviewee (SRC-004, SRC-005). The owner, method and evidence of this step are TBD — confirm with process owner [[GAP-02 — VENDOR CREDIT FOLLOW-UP]].

> **VALIDATION REQUIRED — GAP-02:** Who monitors open Return Authorizations for the corresponding vendor credit memo, how the credit is applied against the supplier's account in NetSuite, and what happens when a credit never arrives. The Receiving Supervisor believes Accounts Payable chases credits but does not track them himself (SRC-004); the consultant working notes flag that no interviewee described the credit application step at all (SRC-005).
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

### Outputs & Evidence

- **NetSuite Return Authorization:** the system record of the return, tied to the original item receipt (SRC-004).
- **Return shipment:** goods returned to the supplier with freight on the supplier's account (SRC-004).
- **Vendor credit memo:** expected from the supplier following the return; its receipt and application are unconfirmed (see the validation raised at Step 5) (SRC-004, SRC-005).
- **Evidence retained:** the Return Authorization record in NetSuite; other retained evidence (RMA correspondence, return shipping documents) is TBD — confirm with process owner (SRC-004).

### Key Controls

> **CONTROL — CTRL-001:** A return is processed only against a supplier-issued RMA number obtained by the Buyer before the goods are shipped back (SRC-004).
> - **Type:** Preventive
> - **Frequency:** Each return
> - **Owner:** Buyer

> **CONTROL — CTRL-002:** The return is recorded as a NetSuite Return Authorization against the original item receipt, so the returned quantity is reflected in the system rather than handled off the books (SRC-004).
> - **Type:** Preventive
> - **Frequency:** Each return
> - **Owner:** Receiving Supervisor

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** There is no tracking of whether vendor credit memos actually arrive after a return. The Receiving Supervisor does not follow up ("Whether the credit ever shows up is not something I track"), assumes Accounts Payable does, and no one interviewed described owning the step (SRC-004, SRC-005).
> - **Impact:** Credits owed by suppliers for returned goods may never be received or applied, overstating amounts paid to those suppliers; the exposure is unquantified (SRC-005).
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Assign a named owner in Accounts Payable for open-return follow-up and institute a periodic review of open NetSuite Return Authorizations against vendor credit memos received, so every return closes with a credit or a documented resolution.
> - **Addresses:** PP-001

```consult-meta
systems: [netsuite]
roles:   [receiving-supervisor, buyer, supplier, ap-manager]
```
