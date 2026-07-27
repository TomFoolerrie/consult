## Non-PO Invoice Entry and Approval

### Process Overview

This procedure covers the entry, coding, and approval of supplier invoices that carry no purchase order reference — utilities, legal, insurance, freight bills that do not tie to a PO, and purchases under the PO threshold — roughly a quarter of invoice volume (SRC-001). Because there is no purchase order approval behind these invoices, each bill is coded manually to the general ledger and routed through NetSuite approval workflow before it becomes eligible for payment. The Accounts Payable Clerk performs the entry and coding as captured bills arrive from [[invoice-intake-and-capture]]; approvers act on the routed bills in their NetSuite queues. Approved bills flow into the weekly disbursement cycle in [[weekly-payment-run]]. Invoices bearing a valid purchase order reference are excluded — those are handled in [[po-invoice-entry-and-three-way-match]] — as are payroll disbursements, intercompany settlements, and employee expense reimbursements (§1.2 of the prior SOP, SRC-006).

### Quick Reference

- **Trigger:** A captured bill without a purchase order reference appears in NetSuite in a pending state (SRC-001)
- **Frequency:** Continuous — worked as bills arrive; roughly a quarter of total invoice volume is non-PO (SRC-001; SRC-005)
- **Preparer:** Accounts Payable Clerk (entry and coding) (SRC-001)
- **Reviewer:** Dollar-tiered approval chain beginning with the Cost Center Owner; higher tiers are contested between the sources — see GAP-01 in E
- **Primary systems / tools:** NetSuite
- **Key outputs:** Fully approved non-PO bill in NetSuite, eligible for the weekly payment run

### Pre-Requisites

- The invoice has been captured and exists in NetSuite as a bill in a pending state with the invoice image attached, per [[invoice-intake-and-capture]] (SRC-001).
- The supplier exists in the NetSuite vendor master; vendor record creation and maintenance are handled in [[vendor-master-data-maintenance]] (SRC-003).
- The invoice genuinely carries no purchase order reference — where a purchase order exists, payable lines are not created manually and the bill is processed through [[po-invoice-entry-and-three-way-match]] instead (§5.1 of the prior SOP, SRC-006).
- The Accounts Payable Clerk has access to the NetSuite Enter Bills function and to the Company chart of accounts for coding (SRC-001; §5.5 of the prior SOP, SRC-006).

### Inputs

- **Pending non-PO bill in NetSuite:** produced by [[invoice-intake-and-capture]], visible on the "AP - Bills Pending Review" saved search, with the invoice image attached (SRC-001).
- **Company chart of accounts:** the coding reference for general ledger account assignment (§5.5 of the prior SOP, SRC-006).
- **Freight bills:** sent by carriers directly to Accounts Payable rather than through receiving (SRC-004); handling within the non-PO stream is unconfirmed — see GAP-03 in E.

### Step-by-Step Procedure

#### Step 1: Identify the bill as non-PO

Captured bills are worked from the pending queue in NetSuite and those without a purchase order reference are identified. Typical non-PO invoices are utilities, legal, insurance, freight bills that do not tie to a PO, and anything under the PO threshold (SRC-001). Where a valid purchase order reference exists, the bill is not processed here — payable lines are never created manually against an existing PO (§5.1 of the prior SOP, SRC-006).

Freight bills arrive at Accounts Payable directly from carriers and do not pass through the receiving dock (SRC-004). Their routing is unconfirmed [[GAP-03 — FREIGHT AND COLLECT SHIPMENT HANDLING]].

> **VALIDATION REQUIRED — GAP-03:** No source described how freight bills are processed once they reach Accounts Payable — whether they are entered through the non-PO stream by default, who codes them, and who authorizes payment of collect shipments (described only as "a whole conversation about who authorized collect") (SRC-004; SRC-005). Confirm the freight bill and collect-shipment handling path.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Code the bill manually

The bill is entered through the same Enter Bills screen used for PO invoices, but with no purchase order reference to populate the lines, coding is manual: general ledger account, department, and Class, which the Company uses to designate plant (SRC-001). Coding follows the Company chart of accounts (§5.5 of the prior SOP, SRC-006). NetSuite enforces a unique constraint on the combination of supplier identifier and supplier invoice number, so an attempted duplicate entry is rejected by the system (CTRL-002; §5.6 of the prior SOP, SRC-006).

- **Navigation Path:** Transactions > Payables > Enter Bills
- **Fields / Parameters:** General ledger account; Department; Class (plant)

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite Enter Bills screen showing a non-PO bill with manual GL account, department, and Class coding — validates the manual coding fields and the absence of a PO reference.

#### Step 3: Route the bill for approval

Because no purchase order approval stands behind the invoice, the coded bill routes through NetSuite approval workflow (SRC-001). The Cost Center Owner approves every non-PO invoice, and additional approvers are added as the dollar value steps up. The composition of the ladder is contested between the sources [[GAP-01 — NON-PO APPROVAL LADDER]]:

- Per the Accounts Payable Manager: under $5,000 the Cost Center Owner alone; $5,000 to $25,000 adds the Corporate Controller; above $25,000 adds the Chief Financial Officer; above $100,000 the invoice is additionally flagged in the monthly capital-expenditure review, with no separate approval (SRC-001).
- Per the prior SOP: up to $2,500 the Cost Center Owner; $2,500.01 to $10,000 adds the Functional Vice President; $10,000.01 to $50,000 adds the Corporate Controller; above $50,000 adds the Chief Financial Officer (§6.1 of the prior SOP, SRC-006).

The two accounts differ in both the breakpoints and the approver set — the prior SOP includes a Functional Vice President layer that the Accounts Payable Manager did not mention — and no one interviewed had pulled the live NetSuite workflow configuration (SRC-005).

Approvals are recorded within NetSuite; approval by email is not acceptable evidence of approval (§6.2 of the prior SOP, SRC-006). An approver may not approve an invoice for which that approver is the requester or the beneficiary (§6.3 of the prior SOP, SRC-006).

- **Expected Result:** The bill enters the approval queue of each required approver in sequence

> **VALIDATION REQUIRED — GAP-01:** The live non-PO approval ladder is contested.
> - **Note:** The ladder is contested between the sources — do not treat either set of breakpoints as authoritative; see GAP-01.
> - **Detail:** The Accounts Payable Manager described tiers of $5,000 / $25,000 / $100,000 with no Functional Vice President layer (SRC-001); the prior SOP prescribes $2,500 / $10,000 / $50,000 including a Functional Vice President layer (§6.1 of the prior SOP, SRC-006). The breakpoints and the approver set both differ, and the configured NetSuite approval workflow has not been examined (SRC-005). Pull the NetSuite workflow configuration to establish the operating ladder.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

#### Step 4: Monitor pending approvals and follow up

Bills awaiting approval are monitored. The prior SOP requires approvals not actioned within three business days to escalate automatically to the approver's supervisor (§6.4 of the prior SOP, SRC-006), but in practice non-PO approvals are described as sitting in approvers' NetSuite queues for up to two weeks with no escalation — "it just sits there until someone yells" (SRC-001) [[GAP-02 — APPROVAL ESCALATION]]. Follow-up is manual and reactive.

> **VALIDATION REQUIRED — GAP-02:** The prior SOP's three-business-day automatic escalation (§6.4 of the prior SOP, SRC-006) contradicts fieldwork accounts that approvals sit for up to two weeks with no escalation (SRC-001; SRC-005). Determine whether the escalation is not configured in NetSuite or configured but not operating, and confirm the intended escalation path.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

#### Step 5: Release the approved bill to the payment cycle

Once all required approvals are recorded, the bill is fully approved in NetSuite and becomes eligible for selection in the weekly disbursement cycle in [[weekly-payment-run]] (SRC-001).

> **SCREENSHOT PLACEHOLDER — SC-02:** A non-PO bill in NetSuite showing the completed approval history — validates that approvals are recorded in the system rather than by email.

### Key Controls

> **CONTROL — CTRL-001:** Every non-PO invoice is approved through the dollar-tiered NetSuite approval workflow before it becomes eligible for payment, beginning with the Cost Center Owner and adding senior approvers as value increases. The live tier breakpoints and approver set are contested — see GAP-01 at Step 3 in E.
> - **Type:** Preventive
> - **Frequency:** Each non-PO invoice
> - **Owner:** Cost Center Owner (first tier); higher tiers per the configured ladder (TBD — see GAP-01)

> **CONTROL — CTRL-002:** NetSuite rejects duplicate invoice entry through a unique constraint on the combination of supplier identifier and supplier invoice number (§5.6 of the prior SOP, SRC-006).
> - **Type:** Preventive
> - **Frequency:** Each bill entry (system-enforced)
> - **Owner:** System-enforced in NetSuite (administered by the IT Manager)

> **CONTROL — CTRL-003:** Approvals are recorded within NetSuite; approval by electronic mail is not acceptable evidence and is not relied upon (§6.2 of the prior SOP, SRC-006).
> - **Type:** Preventive
> - **Frequency:** Each approval
> - **Owner:** Cost Center Owner and subsequent approvers

> **CONTROL — CTRL-004:** An approver may not approve an invoice for which that approver is the requester or the beneficiary (§6.3 of the prior SOP, SRC-006).
> - **Type:** Preventive
> - **Frequency:** Each approval
> - **Owner:** TBD — confirm with process owner whether this is system-enforced in the NetSuite workflow or a policy expectation (covered by GAP-01, the workflow configuration pull)

### Outputs

- **Approved non-PO bill in NetSuite:** fully coded and carrying all required approvals, consumed downstream by [[weekly-payment-run]] (SRC-001).
- **Evidence retained:** the approval history recorded on the bill in NetSuite (§6.2 of the prior SOP, SRC-006), and the original invoice image attached to the bill record, retained for not less than seven years (§4.5 of the prior SOP, SRC-006).

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Non-PO approvals sit in approvers' NetSuite queues for up to two weeks with no escalation — the prior SOP's automatic three-business-day escalation is either not configured or not operating (SRC-001; SRC-005).
> - **Impact:** Delayed payables, manual chasing by the AP team, and invoices that stall "until someone yells" (SRC-001).
> - **Severity:** High

> **PAIN POINT — PP-002:** The Accounts Payable Clerk who enters and codes non-PO invoices also holds the NetSuite Vendor Maintenance role, combining vendor master edit access and non-PO invoice entry in one pair of hands (SRC-003; SRC-005).
> - **Impact:** A segregation-of-duties exposure: the same individual could create or alter a vendor record and enter an invoice against it. Payment approval and release sit with other roles, which limits but does not eliminate the risk (SRC-003).
> - **Severity:** Medium

> **PAIN POINT — PP-003:** The documented approval ladder and the ladder described by the operating team differ in both breakpoints and approver set, and no one has verified the configured NetSuite workflow (SRC-001; SRC-005; §6.1 of the prior SOP, SRC-006).
> - **Impact:** Approval authority may be operating below (or differently from) documented policy without anyone knowing which standard governs; audit evidence of approval authority is unreliable until the configuration is pulled.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Configure (or repair) automatic approval escalation in the NetSuite workflow so that approvals not actioned within the policy window escalate to the approver's supervisor, as the prior SOP already requires (§6.4 of the prior SOP, SRC-006).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Pull the live NetSuite approval workflow configuration, reconcile it with policy, and republish a single authoritative approval ladder for non-PO invoices (SRC-005).
> - **Addresses:** PP-003

```consult-meta
systems: [netsuite]
roles:   [ap-clerk, cost-center-owner, functional-vp, corporate-controller, cfo, ap-manager, it-manager, supplier]
```
