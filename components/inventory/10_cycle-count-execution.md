## Cycle Count Execution (ABC Schedule)

### Scope

This procedure covers the execution of routine cycle counts on the ABC schedule: generating blind count sheets, performing the physical counts in pairs, keying the results into NetSuite, auto-posting variances within tolerance, and recounting variances outside tolerance. It ends when a recount-confirmed variance is placed on the adjustment log; the Friday review and Monday posting of that log are covered in [[count-adjustment-review-and-posting]]. Adjustments arising outside the count — damage, spoilage, and scrap — are excluded and covered in [[material-disposition-adjustment]]. Bin accuracy at receipt, which drives many of the variances this procedure detects, is established in [[putaway-and-bin-confirmation]].

### At a Glance

| Field | Value |
|---|---|
| Trigger | Counting window opens per the ABC schedule; count sheets are generated on the first Monday of the window (SRC-001) |
| Frequency | A-items monthly, B-items quarterly, C-items annually (SRC-001) |
| Preparer | Inventory Control Analyst (sheet generation, keying, worksheet approval); Cycle Counters (physical counts) |
| Reviewer | Plant Controller (for out-of-tolerance variances, via the adjustment log — see [[count-adjustment-review-and-posting]]) |
| Systems | NetSuite |
| Key inputs | NetSuite cycle count worksheet; counter pair assignments |
| Key outputs | Posted within-tolerance count adjustments; adjustment log entries for confirmed out-of-tolerance variances |

### Before You Start

- **NetSuite cycle count worksheet** — item and location population for the current counting window, per the ABC schedule (SRC-001, SRC-002).
- **Tolerance table** — the saved search maintained by the Inventory Control Analyst holding the auto-post tolerances (2% by value for A-items, 5% for B and C items); current as of the count (SRC-001, SRC-002).
- **Counter pair assignments** — pairs assigned such that no counter counts a location they picked from that same week (SRC-001).

### Procedure

#### Step 1: Generate blind count sheets from NetSuite

On the first Monday of the counting window, the Inventory Control Analyst generates and prints the count sheets from the NetSuite cycle count worksheet. The sheets are blind: they show location and item but not the system (book) quantity (SRC-001, SRC-002).

- **System / Tool:** NetSuite cycle count worksheet, printed to paper sheets
- **Evidence Required:** Printed blind count sheets for the window

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite cycle count worksheet at sheet generation, validating that book quantities are suppressed on the printed sheets.

#### Step 2: Confirm counter independence and swap assignments where needed

- **Condition:** a counter is assigned a location they picked from that same week

Counters are not permitted to count locations they picked from during the same week. Where an assignment breaks this rule, the Inventory Control Analyst swaps the assignment to a different pair (SRC-001).

#### Step 3: Perform the physical count in pairs

The Cycle Counters work in pairs, one counting and one recording, and record the counted quantities on the blind sheets. Completed sheets are returned to the Inventory Control Analyst the same day (SRC-001).

#### Step 4: Key counted quantities into the NetSuite count worksheet

The counted quantities are keyed into the NetSuite count worksheet, which displays the variances against book quantity (SRC-001).

- **Expected Result:** The worksheet shows a variance (or zero variance) against book for every counted line

#### Step 5: Approve the worksheet to post within-tolerance variances

The Inventory Control Analyst approves the count worksheet; variances within tolerance — 2% by value for A-items, 5% for B and C items — post automatically to inventory on approval (SRC-001). The tolerances are applied from a saved search maintained by the Inventory Control Analyst rather than from system configuration (SRC-002).

#### Step 6: Stage a recount for out-of-tolerance variances

- **Condition:** a variance exceeds the tolerance for the item's class

Out-of-tolerance variances are not adjusted on the day of the count. They are recounted the next business day by a different counting pair. The recount sheets are staged separately from the day's normal sheets and marked RECOUNT in red to prevent mixing (SRC-001, SRC-002).

- **Evidence Required:** Recount sheets marked RECOUNT, counted by a pair different from the original

#### Step 7: Place confirmed variances on the adjustment log

- **Condition:** the recount confirms the out-of-tolerance variance

The confirmed variance is entered on the adjustment log for the Plant Controller. Review, approval, and posting of the log — including third counts for rejected lines — proceed under [[count-adjustment-review-and-posting]] (SRC-001).

> **VALIDATION REQUIRED — GAP-01:** Retention of the completed and recount count sheets (where they are filed and for how long) is unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Inventory Control Analyst

### Outputs & Evidence

- **Posted within-tolerance adjustments** — inventory adjustments posted automatically in NetSuite on worksheet approval (SRC-001).
- **Adjustment log entries** — confirmed out-of-tolerance variances, handed to [[count-adjustment-review-and-posting]] for Friday review (SRC-001).
- **Completed count sheets and recount sheets** — returned to the Inventory Control Analyst the same day; recount sheets marked RECOUNT (SRC-001, SRC-002).

### Key Controls

> **CONTROL — CTRL-001:** Count sheets are printed blind — location and item only, no book quantity — so counters cannot anchor to the system figure (SRC-001, SRC-002).
> - **Type:** Preventive
> - **Frequency:** Each counting window
> - **Owner:** Inventory Control Analyst

> **CONTROL — CTRL-002:** Counters work in pairs (one counting, one recording) and may not count locations they picked from that same week; conflicting assignments are swapped (SRC-001).
> - **Type:** Preventive
> - **Frequency:** Each counting window
> - **Owner:** Inventory Control Analyst

> **CONTROL — CTRL-003:** Only variances within tolerance (2% by value for A-items, 5% for B and C items) post automatically; larger variances are held for recount (SRC-001).
> - **Type:** Preventive
> - **Frequency:** Each count worksheet approval
> - **Owner:** Inventory Control Analyst

> **CONTROL — CTRL-004:** Out-of-tolerance variances are recounted the next business day by a different counting pair before any adjustment is made; no adjustment posts the same day as the count (SRC-001).
> - **Type:** Detective
> - **Frequency:** Each out-of-tolerance variance
> - **Owner:** Inventory Control Analyst

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The cycle-count tolerance table lives in a saved search maintained personally by the Inventory Control Analyst rather than in approved system configuration (SRC-002).
> - **Impact:** A mis-edit to the saved search would silently change the tolerances that drive auto-posting, and nobody would know (SRC-002).
> - **Severity:** High

> **PAIN POINT — PP-002:** Count-driven variances frequently originate upstream at the receiving-to-putaway handoff — short counts, receipts posted against the wrong purchase order (PO) line, or wrong units of measure on the item-vendor record — and the cycle count detects them only weeks later (SRC-001).
> - **Impact:** Inventory records are wrong from day one of the receipt until the next scheduled count of the affected location; unit-of-measure errors can misstate on-hand by a large factor (SRC-001).
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Move the cycle-count tolerances from the user-maintained saved search into approved, change-controlled NetSuite configuration, as the Inventory Control Analyst has requested (SRC-002).
> - **Addresses:** PP-001

```consult-meta
systems: [netsuite]
roles:   [inventory-control-analyst, cycle-counter, plant-controller]
```
