## PO Invoice Entry and Three-Way Match

### A. Process Overview

This procedure covers the entry of a supplier invoice bearing a purchase order reference
against that purchase order in NetSuite, the three-way match of purchase order, goods
receipt and invoice, and the resolution of the match exceptions the comparison raises. It
runs continuously through the business day against the population of pending Bills, and is
performed by the Senior Accounts Payable Specialist under the Accounts Payable Manager,
with the Buyer and the Receiving Supervisor engaged on exceptions. It begins with the
pending NetSuite Bill produced by [[invoice-intake-and-capture]], matches it to the
purchase order issued in [[po-issuance-and-change-orders]] and the item receipt posted in
[[goods-receipt]], and ends with a matched bill eligible for selection in
[[weekly-payment-run]]. Invoices carrying no purchase order reference are entered and
approved in [[non-po-invoice-entry-and-approval]] and are outside its scope, as are
supplier credits arising from returns, which are handled in [[return-to-vendor]].
(SRC-001, SRC-003, SRC-004, SRC-005, SRC-006)

### B. Quick Reference

- **Trigger:** A Bill bearing a purchase order reference appears in the pending population in NetSuite following capture.
- **Frequency:** Continuous / daily as pending Bills accumulate.
- **Preparer:** Senior Accounts Payable Specialist.
- **Reviewer:** No separate human review of a matched purchase order bill is performed. A bill whose variances fall within the matching tolerance releases automatically on the strength of the approved purchase order; a bill outside tolerance is held and worked as an exception. Oversight sits with the Accounts Payable Manager, and approval of the resulting disbursement sits with the Corporate Controller in [[weekly-payment-run]].
- **Primary systems / tools:** NetSuite (saved search "AP - Bills Pending Review", Enter Bills, item receipt, purchase order record); Coupa (purchase order and change order source).
- **Key outputs:** A matched and released NetSuite Bill eligible for payment selection; bills held at "Match Exception - Hold" with the exception under resolution.

### C. Pre-Requisites

- A Bill exists in NetSuite in a pending state with the invoice image attached, produced by [[invoice-intake-and-capture]].
- The invoice carries a valid purchase order reference, captured at intake or keyed in the validation queue.
- An approved purchase order exists in NetSuite for the referenced number, synced from Coupa (see [[po-issuance-and-change-orders]]).
- An item receipt has been posted against the purchase order lines being billed (see [[goods-receipt]]).
- The Senior Accounts Payable Specialist holds NetSuite access to the Enter Bills function and to the "AP - Bills Pending Review" saved search.

### D. Inputs

- **Pending NetSuite Bill:** [[invoice-intake-and-capture]] — carries the captured supplier, invoice number, invoice date and total, and the original invoice image as an attachment.
- **Approved purchase order:** NetSuite, synced from Coupa — supplies the ordered quantity, the unit price and the account coding on each line.
- **NetSuite item receipt:** [[goods-receipt]] — supplies the quantity received per line and the packing slip number in the memo field; the bill lines are drawn from the receipt.
- **Supplier invoice image:** Supplier — the document against which the quantity, price and total are read.
- **Paper packing slip:** Receiving office — retrieved by the Receiving Supervisor when a quantity exception is investigated.

### E. Step-by-Step Procedure

#### Step 1: Select the pending purchase order invoice from the review queue

The Senior Accounts Payable Specialist works the pending Bill population from a NetSuite
saved search held on the dashboard, and selects the bills carrying a purchase order
reference. Bills without a purchase order reference are routed to
[[non-po-invoice-entry-and-approval]].

- **System / Tool:** NetSuite
- **Navigation Path:** Saved search "AP - Bills Pending Review" (dashboard portlet); Transactions > Payables > Enter Bills where the bill is opened directly rather than from the search.
- **Expected Result:** A pending purchase order bill is open for entry.

#### Step 2: Enter the bill by reference to the purchase order

The bill is entered by reference to the purchase order rather than by keying payable lines
by hand. On entry of the purchase order reference, NetSuite populates the bill lines from
the item receipt posted against that purchase order. The prior standard operating procedure
prohibits the manual creation of payable lines where a purchase order exists (SRC-006 §5.1).

- **System / Tool:** NetSuite
- **Navigation Path:** Transactions > Payables > Enter Bills
- **Fields / Parameters:** Purchase order reference; supplier; supplier invoice number; invoice date; invoice total.
- **Expected Result:** The bill lines populate from the item receipt, carrying quantity received, purchase order unit price and the account coding from the purchase order.

> **SCREENSHOT PLACEHOLDER — SC-01:** A NetSuite bill opened from the "AP - Bills Pending Review" saved search with the purchase order reference entered and the lines populated from the item receipt — validates the navigation path, the saved search as the working queue, and the population of lines from the receipt rather than by manual entry.

#### Step 3: Compare the three legs of the match

The Senior Accounts Payable Specialist compares three points on each bill: the quantity
billed against the quantity received on the item receipt; the unit price billed against the
unit price on the purchase order; and the general ledger account to which the item is
mapping. Where all three agree, the bill is completed; a clean purchase order invoice takes
in the order of ninety seconds. All three documents — purchase order, goods receipt and
supplier invoice — must be present before the payable is eligible for release (SRC-006 §5.2).

- **System / Tool:** NetSuite
- **Fields / Parameters:** Quantity billed against quantity received; unit price billed against purchase order unit price; general ledger account per line.
- **Expected Result:** Agreement on all three points, or an identified variance on one or more of them.

#### Step 4: Apply the matching tolerance

Where a variance exists between the invoice and the purchase order, NetSuite applies a
configured matching tolerance expressed as a percentage and a dollar amount, the lesser of
the two governing. A variance within tolerance releases without further approval; a variance
exceeding tolerance places the bill on hold for referral. The tolerance value currently
configured could not be established from the sources and is the most contested parameter in
this procedure — see [[GAP-01 — THREE-WAY MATCH TOLERANCE]]. This procedure should not be
operated against any tolerance figure until the configuration has been read from NetSuite.

- **System / Tool:** NetSuite
- **Expected Result:** A within-tolerance variance releases automatically; a variance above tolerance moves the bill to "Match Exception - Hold".

> **VALIDATION REQUIRED — GAP-01:** The three-way match tolerance configured in NetSuite — the percentage, the dollar amount, whether the lesser of the two governs, and whether the test is applied at the line level or to the invoice total. Four accounts were obtained and no two agree: SRC-006 §5.3 states five percent of the line extended value or one hundred dollars, whichever is the lesser; the Accounts Payable Manager stated three percent or two hundred fifty dollars, whichever is lower, and the Senior Accounts Payable Specialist questioned the dollar figure in the same conversation, believing it had been increased; the Corporate Controller stated five percent or five hundred dollars, whichever is less, at the line level, described three percent and two hundred fifty dollars as the pre-upgrade values raised at the 2024 NetSuite upgrade to reduce exception volume, but expressly qualified her answer as "fairly confident" and asked that the configuration be pulled rather than her recollection relied upon; and the Receiving Supervisor recalled a five hundred dollar figure in connection with the separate over-receipt tolerance, which he conflated with this control. **Resolution path:** export the match tolerance configuration from NetSuite — the percentage and amount fields, the level at which the test is applied, and the change history showing whether the values were amended at the 2024 upgrade — and reconcile the exported values to the standard operating procedure before it is reissued. The distinct over-receipt tolerance applied at the dock belongs to [[goods-receipt]] and should be exported at the same time so the two are visibly separated. No value should be selected from the recollections above.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller, with the IT Manager

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite match tolerance configuration showing the percentage and dollar fields, the level at which the tolerance is applied and, where available, the change history — the evidence that resolves GAP-01.

#### Step 5: Place an out-of-tolerance bill on hold and identify the broken leg

Where the variance exceeds tolerance, NetSuite flags the bill and sets its status to
"Match Exception - Hold", which blocks release until the exception is resolved. The Senior
Accounts Payable Specialist establishes which of the three legs is broken. The predominant
cause is a missing receipt — the goods are physically at the dock but the item receipt has
not been entered, so there is no receipt line to bill against; this accounts for
approximately sixty percent of exceptions. The second most frequent cause is price: the
supplier has raised its price against a purchase order that was not amended by change order.

- **System / Tool:** NetSuite
- **Expected Result:** The bill is held at "Match Exception - Hold" and the variance is attributed to the receipt, the price or the coding.
- **Evidence Required:** The held bill in NetSuite showing the variance against the purchase order and the item receipt.

> **VALIDATION REQUIRED — GAP-04:** Whether the "Match Exception - Hold" population is monitored — whether an aged report or saved search exists, who reviews it, on what cadence, and whether any escalation applies to a bill held beyond a defined period. The Senior Accounts Payable Specialist described exceptions being worked as encountered and price exceptions sitting after referral to the Buyer; no source described a report, an ageing threshold or an escalation path.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

> **SCREENSHOT PLACEHOLDER — SC-03:** A NetSuite bill at status "Match Exception - Hold" showing the variance between billed and received quantity or between billed and purchase order price — validates the hold status, the block on release, and the information available to the preparer at the point of investigation.

#### Step 6: Resolve a quantity exception with receiving

For a quantity variance, the Senior Accounts Payable Specialist contacts the Receiving
Supervisor at the relevant facility and the two review the paper packing slips filed in the
receiving office for the period in question, to establish whether the difference arose from
a keying error at receipt or from the supplier's shipment. Approximately half of the
discrepancies investigated trace to a keying error on the receiving side. The receipt is
corrected or the discrepancy referred to the Buyer accordingly, and the bill is re-matched
once the receipt reflects what was delivered. Where the goods were delivered but no receipt
was entered at all, the bill remains held until [[goods-receipt]] posts the item receipt.

- **Expected Result:** The item receipt reflects the quantity actually delivered and the bill re-matches, or the variance is established as a supplier error and referred to the Buyer.
- **Evidence Required:** TBD — confirm with process owner. See [[GAP-03 — WRITTEN RECEIVING CONFIRMATION]].

> **VALIDATION REQUIRED — GAP-03:** Whether written confirmation of quantities received is obtained and retained when a quantity variance is resolved with receiving. SRC-006 §5.4 requires that where receiving documentation is unavailable the Receiving Supervisor be contacted and confirmation obtained in writing; both the Accounts Payable Manager and the Receiving Supervisor described the resolution as a telephone call or an email followed by a review of the paper packing slips, and neither described a written confirmation being captured or attached to the bill. Confirm whether the requirement is operating and, if so, where the confirmation is retained.
> - **Nature:** conflict
> - **Owner to confirm:** Accounts Payable Manager, with the Receiving Supervisor

#### Step 7: Resolve a price exception with the Buyer

For a price variance, the Senior Accounts Payable Specialist refers the exception by email
to the Buyer responsible for the purchase order; the prior standard operating procedure
likewise requires referral to the responsible Buyer (SRC-006 §5.3). The Buyer establishes
whether the invoiced price is correct and, where it is, raises a change order against the
purchase order in [[po-issuance-and-change-orders]]. The bill is re-matched against the
amended purchase order once the change order is issued. Referrals are made without a
response deadline, and bills routinely remain held while the referral is outstanding.

- **System / Tool:** NetSuite; Coupa (change order raised by the Buyer).
- **Expected Result:** The purchase order price is corrected by change order and the bill re-matches, or the invoiced price is rejected and the supplier is asked to correct the invoice.

#### Step 8: Complete the matched bill

Once all three legs agree, or the residual variance falls within tolerance, the bill is
completed in NetSuite and joins the population of open payables eligible for selection in
[[weekly-payment-run]]. NetSuite enforces a unique constraint on the combination of supplier
identifier and supplier invoice number, rejecting an attempt to enter the same invoice twice
(SRC-006 §5.6, SRC-005).

- **System / Tool:** NetSuite
- **Expected Result:** A completed bill carrying the supplier, invoice number, due date and account coding, open for payment selection.
- **Evidence Required:** The completed NetSuite Bill with the invoice image attached and the purchase order and item receipt linked to it.

> **VALIDATION REQUIRED — GAP-02:** How a bill held at "Match Exception - Hold" is released once the underlying exception is resolved — whether the bill re-matches automatically when the receipt or purchase order is corrected or the hold must be cleared by a person, whether an unresolved variance can be overridden, and if so which role holds that permission and what evidence the override leaves. The hold status and its blocking effect were described, but no source described the release mechanism or any override.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager, with the IT Manager

> **VALIDATION REQUIRED — GAP-05:** The owner of the duplicate invoice constraint and confirmation that it remains configured following the 2024 NetSuite upgrade. The constraint on supplier identifier plus supplier invoice number is stated in SRC-006 §5.6 and carried in the consultant's draft control inventory, but no source described it being tested and none named a role accountable for it.
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager

### F. Key Controls

> **CONTROL — CTRL-001:** Three-way match — the approved purchase order, the recorded goods receipt and the supplier invoice must all be present and in agreement before the payable is eligible for release. A bill failing the comparison is set to "Match Exception - Hold", which blocks release until the exception is resolved.
> - **Type:** Preventive
> - **Frequency:** Each purchase order invoice entered
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-002:** Matching tolerance — a variance between the invoice and the purchase order within the configured percentage and dollar tolerance releases without further approval; a variance exceeding the tolerance is held and referred to the responsible Buyer. The configured value is unconfirmed and disputed across every source that addressed it (see Step 4).
> - **Type:** Preventive
> - **Frequency:** Each purchase order invoice carrying a variance
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-003:** Purchase order basis for entry — a payable bearing a purchase order reference is entered by reference to that purchase order, with lines populated from the item receipt; payable lines are not created manually where a purchase order exists.
> - **Type:** Preventive
> - **Frequency:** Each purchase order invoice entered
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-004:** Duplicate invoice prevention — NetSuite enforces a unique constraint on the combination of supplier identifier and supplier invoice number and rejects an attempt to enter a duplicate.
> - **Type:** Preventive
> - **Frequency:** Each bill entered
> - **Owner:** TBD — confirm with process owner (see [[GAP-05 — DUPLICATE CONSTRAINT OWNER]])

### G. Outputs

- **Matched NetSuite Bill:** Completed and open for payment, carrying the supplier, invoice number, due date and purchase order account coding; consumed by [[weekly-payment-run]].
- **Bills held at "Match Exception - Hold":** Blocked from release pending resolution; quantity exceptions drive contact with the Receiving Supervisor and price exceptions drive change order referrals to the Buyer in [[po-issuance-and-change-orders]].
- **Open item receipts with no bill:** Purchase order receipts not yet invoiced remain in the population from which the received-not-invoiced accrual is derived at month end.
- **Evidence retained:** The completed NetSuite Bill with the invoice image attached and the purchase order and item receipt linked to it. No record of an exception investigation or its conclusion is retained against the bill (see Step 6).

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Invoices arrive for goods that are physically on site but for which no item receipt has been entered, so there is no receipt leg to match against. This accounts for approximately sixty percent of the match exceptions worked by the Senior Accounts Payable Specialist.
> - **Impact:** Bills sit at "Match Exception - Hold" for reasons outside the control of Accounts Payable, the specialist chases receipts rather than processing invoices, and the Accounts Payable Manager estimates that same-day receipt entry would halve exception volume and return roughly a week per month to the specialist. The root cause sits at the dock and is addressed in [[goods-receipt]].
> - **Severity:** High

> **PAIN POINT — PP-002:** Price exceptions arise where a supplier has raised its price against a purchase order that was never amended by change order. The exception is referred to the Buyer by email with no response deadline, and the bill remains held while the referral is outstanding.
> - **Impact:** Bills are held for an indeterminate period on a variance that Accounts Payable cannot resolve alone, exposing the Company to late payment and to lost early-payment discounts.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** No participant could state the matching tolerance in force, and the four accounts obtained — the 2023 standard operating procedure, the Accounts Payable Manager, the Senior Accounts Payable Specialist and the Corporate Controller — differ on both the percentage and the dollar amount. The Corporate Controller, who owns the parameter, qualified her own answer and asked that the configuration be pulled instead. The Receiving Supervisor conflated this tolerance with the separate over-receipt tolerance applied at the dock.
> - **Impact:** The threshold governing automatic release of a variance without approval is unknown to the people operating and supervising the control, the documented standard operating procedure cannot be relied upon, and the control cannot be evidenced to an auditor in its configured form. The two distinct tolerances are not reliably told apart across the functions that encounter them.
> - **Severity:** High

> **PAIN POINT — PP-004:** Resolving a quantity exception depends on retrieving paper packing slips from the receiving office and on a telephone or email exchange between the Senior Accounts Payable Specialist and the Receiving Supervisor. Neither the exchange nor its conclusion is captured against the bill.
> - **Impact:** Investigation is slow and dependent on the availability of two people and of paper, and a completed bill carries no record of why a variance was accepted or how it was resolved.
> - **Severity:** Medium

> **PAIN POINT — PP-005:** The held-bill population is worked as encountered rather than managed. No aged report, review cadence or escalation for bills held beyond a threshold was described by any source.
> - **Impact:** A bill can remain on hold indefinitely with no one accountable for clearing it, and the size and ageing of the held population are not visible to management.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Export the match tolerance configuration from NetSuite, publish the confirmed percentage, dollar amount and level of application, reissue the standard operating procedure against the exported values, and place the parameter under change control so that a future adjustment is documented. Publish the distinct over-receipt tolerance alongside it so the two controls are visibly separate to Accounts Payable, receiving and the buyers.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish an aged report of bills at "Match Exception - Hold" segmented by exception reason, review it on a defined cadence with the Accounts Payable Manager, and set a response service level with escalation for referrals to the Buyer and to receiving.
> - **Addresses:** PP-002, PP-005

> **IMPROVEMENT OPPORTUNITY — IO-003:** Reconcile bills held for a missing receipt against open deliveries daily, so that the receipt is chased when the invoice arrives rather than when the bill is next worked, pending the receipt-entry remediation in [[goods-receipt]].
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-004:** Capture exception resolution on the bill itself — attaching the receiving confirmation, the supporting packing slip evidence or the change order reference to the NetSuite Bill — so that the reason a variance was accepted is auditable from the transaction record rather than reconstructed from email and paper.
> - **Addresses:** PP-004

```consult-meta
systems: [netsuite, coupa]
roles:   [senior-ap-specialist, ap-manager, buyer, receiving-supervisor, corporate-controller, it-manager, supplier]
```
