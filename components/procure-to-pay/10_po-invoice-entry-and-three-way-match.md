## PO Invoice Entry and Three-Way Match

### Scope

This procedure covers the entry of a supplier invoice that bears a valid purchase
order reference, the three-way match of that invoice against the approved purchase
order and the recorded goods receipt, the application of the matching tolerance,
and the research and clearance of match exceptions up to the point the bill is
matched and eligible for payment. Intake, imaging and capture of the invoice are
excluded and are documented in [[invoice-intake-and-capture]]; the purchase order
and any change order to it are documented in [[po-issuance-and-change-orders]] and
the receipt itself in [[goods-receipt]]. Invoices bearing no purchase order
reference are excluded and follow [[non-po-invoice-entry-and-approval]], and
selection of the matched bill for payment is excluded and follows
[[weekly-payment-run]]. Supplier credit memos arising from returned material are
outside this procedure and adjoin it through [[return-to-vendor]]. (SRC-001,
SRC-006)

### At a Glance

| Field | Value |
|---|---|
| Trigger | A pending Bill carrying a purchase order reference appears in the "AP - Bills Pending Review" saved search |
| Frequency | Continuous, each PO-backed invoice; approximately three quarters of invoice volume is PO-backed |
| Preparer | Senior Accounts Payable Specialist |
| Reviewer | None at bill level — the purchase order approval and the system match are relied upon; the downstream review is the payment run approval in [[weekly-payment-run]] |
| Systems | NetSuite (Enter Bills, three-way match) |
| Key inputs | Pending Bill with attached invoice image; approved purchase order; NetSuite item receipt |
| Key outputs | Matched NetSuite bill eligible for payment, or a bill in "Match Exception - Hold" |

### Before You Start

- **Pending Bill in NetSuite** — [[invoice-intake-and-capture]]; created from the
  captured invoice with header data extracted or keyed and the invoice image
  attached.
- **Approved purchase order** — [[po-issuance-and-change-orders]]; open in NetSuite
  and reflecting the currently agreed unit price for the lines being billed.
- **NetSuite item receipt** — [[goods-receipt]]; posted against the purchase order
  lines being billed, supplying the quantity received leg of the match.
- **Supplier master record** — [[vendor-master-data-maintenance]]; active, so the
  bill can be entered and the duplicate-invoice constraint applies.

### Procedure

#### Step 1: Select the pending PO bill for entry

Pending Bills are worked from the "AP - Bills Pending Review" saved search held on
the Senior Accounts Payable Specialist's NetSuite dashboard; the bill is opened
from the search result. A bill entered cold is reached through the Enter Bills
screen. (SRC-001)

- **Navigation Path:** Transactions > Payables > Enter Bills

> **SCREENSHOT PLACEHOLDER — SC-01:** The "AP - Bills Pending Review" saved search, showing how pending PO-backed bills are presented for entry.

#### Step 2: Populate the bill lines from the purchase order reference

The purchase order reference on the bill populates the bill lines from the receipt,
rather than lines being created by hand. Payable lines are not created manually
where a purchase order exists. (SRC-001, SRC-006)

- **Expected Result:** the bill carries lines derived from the purchase order and
  the posted receipt, ready to be compared against the invoice face.

#### Step 3: Compare the three legs of the match

Three things are checked on the populated bill: quantity billed against quantity
received, unit price on the invoice against the purchase order price, and the
general ledger account to which the item is mapping. All three of the purchase
order, the receipt and the invoice must be present before the payable is eligible
for release. A bill on which the three legs agree is completed in about ninety
seconds. (SRC-001, SRC-006)

- **Fields / Parameters:** quantity billed vs. quantity received per line; invoice
  unit price vs. purchase order unit price; general ledger account mapping

#### Step 4: Apply the matching tolerance

A line variance within the configured matching tolerance is accepted without
further approval and the bill releases automatically; a variance beyond it is held.
The tolerance is applied by NetSuite at line level. The configured figure is
unconfirmed — see [[GAP-01 — THREE-WAY MATCH TOLERANCE]]. (SRC-001, SRC-003,
SRC-006)

> **VALIDATION REQUIRED — GAP-01:** The three-way match tolerance is unconfirmed and is described differently by every source.
> - **Note:** Do not operate or review to a stated tolerance figure; the configured NetSuite value must be pulled before any number is documented or applied.
> - **Detail:** §5.3 of the prior SOP states five percent (5%) of the line extended value or one hundred dollars ($100.00), whichever is the lesser (SRC-006). The Accounts Payable Manager states three percent or two hundred and fifty dollars, whichever is lower, while the Senior Accounts Payable Specialist questioned in the same session whether the dollar figure had since been raised (SRC-001). The Corporate Controller states the figure was raised at the 2024 NetSuite upgrade to five percent or five hundred dollars, whichever is less, at line level, describes herself as only "fairly confident", and asks that the configuration be pulled rather than her recollection relied upon (SRC-003). The working notes record all three positions as an unresolved conflict and note that nobody has actually looked at the NetSuite configuration (SRC-005). A separate over-receipt tolerance blocks receipt entry upstream and is also unconfirmed; it is logged against [[goods-receipt]] and [[po-issuance-and-change-orders]] and should not be conflated with the matching tolerance. Resolution requires the NetSuite match tolerance configuration and sits with the Corporate Controller, who owns the tolerance policy.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

#### Step 5: Place an out-of-tolerance bill on hold and identify the broken leg

- **Condition:** the variance exceeds the matching tolerance

NetSuite flags the bill and applies the status "Match Exception - Hold", which
blocks release until the exception is resolved. The bill is then researched to
establish which of the three legs — purchase order, receipt or invoice — is
broken. (SRC-001)

- **Expected Result:** the bill is blocked from payment and is attributed to a
  quantity, price or coding cause.

> **SCREENSHOT PLACEHOLDER — SC-02:** A NetSuite bill in "Match Exception - Hold", showing the variance between billed, received and ordered quantity and price at line level.

#### Step 6: Resolve a quantity exception

- **Condition:** the broken leg is quantity — the receipt is missing or the
  quantity received differs from the quantity billed

The most common cause is that the goods are physically at the dock but the item
receipt has not yet been entered, so the bill is matching against nothing; this
accounts for approximately sixty percent of exceptions and clears when the receipt
posts under [[goods-receipt]]. Where a receipt exists but the quantities differ,
the discrepancy is raised by email with the Receiving Supervisor at the relevant
plant, who retrieves the filed paper packing slips and compares them against the
entered receipt; the difference proves to be a keying error at receipt or a
supplier shipping difference in roughly equal measure. Quantity variances are to be
resolved by reference to the receiving documentation, and where that documentation
is unavailable the confirmation of quantities received is to be obtained in
writing. See [[GAP-02 — WRITTEN CONFIRMATION OF RECEIVED QUANTITY]]. (SRC-001,
SRC-004, SRC-006)

- **Evidence Required:** the corrected or newly posted item receipt in NetSuite

> **VALIDATION REQUIRED — GAP-02:** Whether the written confirmation of received quantity required where receiving documentation is unavailable is obtained and retained is unconfirmed.
> - **Nature:** unsupported-assumption
> - **Owner to confirm:** Senior Accounts Payable Specialist

#### Step 7: Resolve a price exception

- **Condition:** the broken leg is price — the invoice unit price exceeds the
  purchase order price

The typical cause is that the supplier has raised its price against a stale
purchase order for which no change order was raised. The exception is referred to
the responsible Buyer by email, and clearance depends on a change order being
raised under [[po-issuance-and-change-orders]] to bring the purchase order price
into line. The bill remains on hold in the interim. See [[GAP-03 — PRICE EXCEPTION
RESOLUTION]]. (SRC-001, SRC-006)

> **VALIDATION REQUIRED — GAP-03:** No timeframe, escalation path or accountable owner for clearing a referred price exception is defined.
> - **Note:** Referred price exceptions have no service level — track them outside NetSuite until an owner and a clearance timeframe are established.
> - **Detail:** The Senior Accounts Payable Specialist describes emailing the buyer and the exception then sitting, with no further action described by any source (SRC-001). §5.3 of the prior SOP requires only that out-of-tolerance variances be referred to the responsible Buyer for resolution, and specifies no timeframe, escalation or reporting (SRC-006). No source describes an ageing report over bills in "Match Exception - Hold" or any review of how long they have been held.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 8: Complete the matched bill

Once the three legs agree, or the variance falls within the matching tolerance, the
bill is completed and saved in NetSuite with the invoice image attached to the
transaction record. On save, NetSuite rejects any bill that duplicates an existing
combination of supplier and supplier invoice number. The completed bill becomes
available for selection in [[weekly-payment-run]] according to its due date.
(SRC-001, SRC-005, SRC-006)

- **Expected Result:** the bill is matched, released from hold, and eligible for
  payment on its due date.

### Outputs & Evidence

- **Matched NetSuite bill** — carries the purchase order and item receipt
  references, the coded lines and the attached invoice image; consumed by
  [[weekly-payment-run]].
- **Bill in "Match Exception - Hold"** — the unresolved population, blocked from
  payment until the broken leg is cleared.
- **Evidence retained:** the invoice image attached to the bill, retained for not
  less than seven years; the purchase order and item receipt references recorded on
  the bill (SRC-005, SRC-006).
- **Not retained:** no record of the match exception investigation is retained on
  the transaction — the email exchanges with the Receiving Supervisor and the Buyer
  sit only in mailboxes; no log is kept of how long a bill was held in "Match
  Exception - Hold" or of the cause to which each exception was attributed, so
  exception volume and root cause cannot be measured from current-state evidence
  (SRC-001, SRC-005).

### Key Controls

> **CONTROL — CTRL-001:** A three-way match is performed between the approved purchase order, the recorded item receipt and the supplier invoice; all three must be present and agree within tolerance before the bill is eligible for release.
> - **Type:** Preventive
> - **Frequency:** Each PO-backed invoice
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-002:** NetSuite applies the status "Match Exception - Hold" to a bill whose variance exceeds the matching tolerance, blocking payment until the exception is resolved. The tolerance value itself is unconfirmed — see GAP-01.
> - **Type:** Preventive
> - **Frequency:** Each bill exceeding tolerance
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-003:** Bill lines are populated from the purchase order reference and are not created manually where a purchase order exists, so the billed lines cannot depart from the ordered and received lines.
> - **Type:** Preventive
> - **Frequency:** Each PO-backed invoice
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-004:** NetSuite enforces a unique constraint on the combination of supplier and supplier invoice number, rejecting duplicate entry.
> - **Type:** Preventive
> - **Frequency:** Each bill saved
> - **Owner:** IT Manager

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Match exceptions are dominated by receipts that have not yet been entered, so the bill is matched against nothing.
> - **Note:** Approximately sixty percent of match exceptions are caused by receipt entry lag rather than by any discrepancy in the invoice; the root cause sits at the dock and is documented in [[goods-receipt]].
> - **Detail:** The Senior Accounts Payable Specialist attributes roughly sixty percent of her exceptions to goods being physically at the dock with no receipt entered, and the Accounts Payable Manager states that same-day receipting would halve exception volume and return a week a month to the Senior Accounts Payable Specialist (SRC-001). The Corporate Controller names real-time receipt entry at the dock as the single change she would make and describes everything downstream of it as symptom (SRC-003). The working notes record the item as independently named the top pain point by the Accounts Payable Manager, the Senior Accounts Payable Specialist and the Receiving Supervisor (SRC-005).
> - **Impact:** Accounts Payable capacity is consumed re-working bills that carry no actual discrepancy, and supplier payment is delayed for reasons unrelated to the invoice.
> - **Severity:** High

> **PAIN POINT — PP-002:** A price exception referred to the Buyer has no clearance timeframe, no escalation and no visibility, and the bill sits on hold indefinitely.
> - **Impact:** Bills are held past their due date with no mechanism to surface the ageing population, and no source could describe how or when such an exception is closed. (SRC-001)
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Nobody is able to state the matching tolerance the process operates to.
> - **Note:** Three different tolerance figures were given by three sources and the NetSuite configuration has never been pulled, so the threshold governing an audited control is unknown to the people executing it — see GAP-01.
> - **Impact:** The control cannot be evidenced or tested as written, and staff cannot judge whether an out-of-tolerance bill should have released. (SRC-001, SRC-003, SRC-005, SRC-006)
> - **Severity:** High

> **PAIN POINT — PP-004:** Match exception research leaves no record on the transaction.
> - **Impact:** The cause of each exception, the time it was held and the resolution reached exist only in email, so the exception population cannot be analyzed, reported or evidenced to an auditor. (SRC-001, SRC-005)
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Pull, confirm and publish the configured NetSuite match tolerance, and re-approve it as a documented Controller-owned policy so that a single figure governs the control.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Introduce an ageing report over bills in "Match Exception - Hold", broken down by cause and by the party the exception is referred to, with an escalation rule for referrals not cleared within a defined period.
> - **Addresses:** PP-002, PP-004

> **IMPROVEMENT OPPORTUNITY — IO-003:** Record the exception cause and resolution against the bill in NetSuite rather than in email, so that exception volume and root cause are measurable and the investigation is evidenced with the transaction.
> - **Addresses:** PP-004

> **IMPROVEMENT OPPORTUNITY — IO-004:** Address receipt entry lag at source through the dock-side receipting improvements identified in [[goods-receipt]], which would remove the largest share of match exceptions rather than processing them faster.
> - **Addresses:** PP-001

```consult-meta
systems: [netsuite]
roles:   [senior-ap-specialist, ap-manager, corporate-controller, receiving-supervisor, buyer, procurement-lead, it-manager]
```
