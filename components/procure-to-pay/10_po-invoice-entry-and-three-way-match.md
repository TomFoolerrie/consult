## PO Invoice Entry and Three-Way Match

### Process Overview

This procedure covers the entry and release of supplier invoices that reference a purchase order: from the pending bill created in NetSuite by [[invoice-intake-and-capture]], through the three-way match of the approved purchase order, the recorded item receipt from [[goods-receipt]], and the supplier invoice, to a bill eligible for payment in [[weekly-payment-run]]. It runs daily and is performed principally by the Senior Accounts Payable Specialist, who also works the match-exception queue. The three-way match is one of the three procure-to-pay controls in scope for the external audit (SRC-003). Invoices without a purchase order reference are excluded — they are coded and approved under [[non-po-invoice-entry-and-approval]].

### Quick Reference

- **Trigger:** A captured bill bearing a purchase order reference appears in a pending state on the "AP - Bills Pending Review" saved search (SRC-001)
- **Frequency:** Daily, as pending bills arrive; a clean match takes roughly ninety seconds per bill (SRC-001)
- **Preparer:** Senior Accounts Payable Specialist
- **Reviewer:** No separate per-bill reviewer was identified; the match itself is system-enforced, and downstream payment release is separately controlled in [[weekly-payment-run]]
- **Primary systems / tools:** NetSuite
- **Key outputs:** Matched bill released for payment; bills in "Match Exception - Hold" status pending resolution

### Pre-Requisites

- A pending bill with a purchase order reference exists in NetSuite, created through [[invoice-intake-and-capture]] with the invoice image attached (SRC-001).
- An approved purchase order exists in NetSuite for the invoice, issued through [[po-issuance-and-change-orders]] (SRC-001).
- An item receipt has been recorded against the purchase order in [[goods-receipt]] — all three documents must be present before the payable is eligible for release (§5.2 of the prior SOP, SRC-006).
- The Senior Accounts Payable Specialist holds NetSuite access to the Enter Bills function and the "AP - Bills Pending Review" saved search (SRC-001).

### Inputs

- **Pending bill (NetSuite):** created by [[invoice-intake-and-capture]], with the supplier invoice image attached (SRC-001).
- **Approved purchase order (NetSuite):** from [[po-issuance-and-change-orders]] (SRC-001).
- **Item receipt (NetSuite):** the receiving leg, recorded in [[goods-receipt]] (SRC-001, SRC-004).
- **Receiving documentation:** filed packing slips held by receiving, pulled when a quantity discrepancy must be researched (SRC-004).

### Step-by-Step Procedure

#### Step 1: Select the pending PO bill

Work proceeds from the "AP - Bills Pending Review" saved search on the NetSuite dashboard, opening each pending bill from the search results; the Enter Bills screen can also be reached directly when entering a bill cold (SRC-001).

- **Navigation Path:** Transactions > Payables > Enter Bills (or directly from the "AP - Bills Pending Review" saved search)

#### Step 2: Populate the bill lines from the purchase order

Enter the bill by reference to the purchase order: the PO reference populates the bill lines from the recorded receipt (SRC-001). Payable lines are not created manually where a purchase order exists (§5.1 of the prior SOP, SRC-006) (CTRL-002). NetSuite enforces duplicate invoice prevention at entry through a unique constraint on the combination of supplier identifier and supplier invoice number, rejecting an attempted duplicate (§5.6 of the prior SOP, SRC-006) (CTRL-003). No owner of that configuration was identified [[GAP-02 — DUPLICATE-CHECK CONFIG OWNER]].

- **Fields / Parameters:** Purchase order reference; bill lines populated from the item receipt

> **VALIDATION REQUIRED — GAP-02:** No owner of the duplicate-invoice constraint configuration in NetSuite was identified during fieldwork; the sources describe the control as system-enforced without naming who maintains or monitors it (SRC-005, SRC-006). Confirm the configuration owner.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-01:** A PO bill in NetSuite with lines populated from the purchase order reference, prior to save — validates that lines derive from the receipt rather than manual entry.

#### Step 3: Verify the three match legs

Verify three things on each bill: quantity billed against quantity received, unit price against the purchase order price, and the general ledger account each item maps to (SRC-001). Where all three legs line up within tolerance, the bill releases — a clean bill is completed in roughly ninety seconds (SRC-001).

- **Fields / Parameters:** Quantity billed vs. quantity received; unit price vs. PO price; GL account mapping
- **Expected Result:** Bill released for payment, or flagged to "Match Exception - Hold"

#### Step 4: Apply the matching tolerance

A variance between the invoice and the purchase order within the configured tolerance auto-releases without further approval; a variance above it places the bill on hold and refers it to the responsible Buyer for resolution (SRC-001; §5.3 of the prior SOP, SRC-006). The live tolerance value is contested across the sources and has never been confirmed against the NetSuite configuration [[GAP-01 — MATCH TOLERANCE VALUE]].

> **VALIDATION REQUIRED — GAP-01:** The three-way match tolerance configured in NetSuite.
> - **Note:** The tolerance value is contested and unconfirmed — do not operate to a stated figure; pull the NetSuite match tolerance configuration.
> - **Detail:** The prior SOP states five percent of the line extended value or one hundred dollars, whichever is less (§5.3 of the prior SOP, SRC-006); the Accounts Payable Manager stated three percent or two hundred fifty dollars, whichever is lower (SRC-001); the Corporate Controller stated five percent or five hundred dollars, whichever is less, at the line level, raised at the 2024 NetSuite upgrade, and asked that the configuration be pulled rather than relying on recollection (SRC-003). No one interviewed has looked at the configuration (SRC-005). Pull the NetSuite match tolerance configuration.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

#### Step 5: Work the match-exception queue

- **Condition:** the bill fails the match and is flagged to "Match Exception - Hold"

A bill that fails the match is flagged by NetSuite to a status of "Match Exception - Hold" (SRC-001). The broken leg of the three is determined:

- **Missing or short receipt** — roughly sixty percent of exceptions: the goods are physically at the dock but the item receipt has not yet been entered (SRC-001). The Receiving Supervisor at the relevant facility is contacted; the receipt is entered or corrected under [[goods-receipt]], and the bill re-matches.
- **Price variance:** the supplier has raised its price and the purchase order is stale with no change order processed. The responsible Buyer is emailed and resolves it through a change order under [[po-issuance-and-change-orders]]; the bill remains on hold until the purchase order is corrected (SRC-001).
- **Quantity discrepancy:** where the bill quantity disagrees with the recorded receipt, the exception is resolved by reference to the receiving documentation — receiving pulls the filed packing slips and re-verifies; where the documentation is unavailable, the Receiving Supervisor confirms the quantities received in writing (§5.4 of the prior SOP, SRC-006; SRC-004). In practice the cause splits roughly evenly between receiving keying errors and supplier errors (SRC-004).

- **System / Tool:** Email (to the responsible Buyer or the Receiving Supervisor)
- **Evidence Required:** Written confirmation of quantities from the Receiving Supervisor where receiving documentation is unavailable (prior SOP requirement)

> **SCREENSHOT PLACEHOLDER — SC-02:** A bill in "Match Exception - Hold" status in NetSuite — validates the exception status name and that failed matches hold rather than release.

### Key Controls

> **CONTROL — CTRL-001:** Three-way match: the approved purchase order, the recorded goods receipt and the supplier invoice must all be present, and agree within tolerance, before the payable is eligible for release; failed matches hold in "Match Exception - Hold" status (SRC-001; §5.2–§5.3 of the prior SOP, SRC-006). One of the three procure-to-pay controls in scope for the external audit (SRC-003). The tolerance value is contested — a validation gap is raised at Step 4 in E.
> - **Type:** Preventive
> - **Frequency:** Each PO bill (system-enforced)
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-002:** Where a purchase order exists, the bill is entered by reference to that purchase order and payable lines are not created manually, ensuring invoices cannot bypass the match (§5.1 of the prior SOP, SRC-006).
> - **Type:** Preventive
> - **Frequency:** Each PO bill
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-003:** NetSuite rejects entry of a duplicate invoice through a unique constraint on the combination of supplier identifier and supplier invoice number (§5.6 of the prior SOP, SRC-006; SRC-005).
> - **Type:** Preventive
> - **Frequency:** Each bill entry (system-enforced)
> - **Owner:** TBD — confirm with process owner (a validation gap is raised at Step 2 in E)

### Outputs

- **Released bill (NetSuite):** a matched bill eligible for payment, picked up by the payment proposal in [[weekly-payment-run]] (SRC-001).
- **Bills in "Match Exception - Hold":** the exception queue worked by the Senior Accounts Payable Specialist until each broken leg is resolved (SRC-001).
- **Exception referrals:** price variances referred to the responsible Buyer; receipt and quantity issues referred to the Receiving Supervisor (SRC-001, SRC-004).
- **Evidence retained:** the supplier invoice image attached to the NetSuite bill, retained for not less than seven years (§4.5 of the prior SOP, SRC-006); written quantity confirmations from the Receiving Supervisor where obtained (§5.4 of the prior SOP, SRC-006).

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Late receipt entry drives the exception queue: goods physically received but not yet keyed in NetSuite account for roughly sixty percent of match exceptions, so the Senior Accounts Payable Specialist is billing against nothing (SRC-001). The Accounts Payable Manager, the Corporate Controller and the Receiving Supervisor each independently named it the top issue (SRC-001, SRC-003, SRC-004, SRC-005).
> - **Impact:** The Accounts Payable Manager estimates exception volume would drop by half with same-day receipt entry, recovering roughly a week of the Senior Accounts Payable Specialist's time each month; invoice release is delayed in the meantime (SRC-001).
> - **Severity:** High

> **PAIN POINT — PP-002:** Price-variance exceptions stall with the Buyer: when a supplier's price has risen against a stale purchase order with no change order, the Senior Accounts Payable Specialist emails the Buyer "and it sits," with no escalation identified (SRC-001).
> - **Impact:** Bills remain in "Match Exception - Hold" for extended periods awaiting a change order, delaying supplier payment.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** The live match tolerance is not reliably known inside the organization — the SOP, the Accounts Payable Manager and the Corporate Controller each gave a different value, and no one has pulled the NetSuite configuration (SRC-001, SRC-003, SRC-005, SRC-006).
> - **Impact:** An audit-scoped control (SRC-003) is operating at a threshold its owners cannot state, and the documented SOP does not reflect the configured system.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Achieve same-day receipt posting at the receiving docks (for example through the handheld-scanner deployment proposed at the docks) so the receiving leg exists before the invoice arrives (SRC-001, SRC-004).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Pull the NetSuite match tolerance configuration, confirm the intended value with the Corporate Controller, and update the SOP so document, system and practice agree (SRC-003, SRC-005).
> - **Addresses:** PP-003

```consult-meta
systems: [netsuite]
roles:   [senior-ap-specialist, ap-manager, corporate-controller, buyer, receiving-supervisor, supplier]
```
