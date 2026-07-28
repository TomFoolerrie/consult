## Count Variance Adjustment Log Review and Posting

### Scope

This procedure covers the weekly review, approval, and posting of count-driven inventory adjustments: the Plant Controller's Friday review of the adjustment log, the paper sign-off, the Monday posting of approved lines in NetSuite, and the return of rejected lines for a third count. It begins when a recount-confirmed out-of-tolerance variance is placed on the adjustment log by [[cycle-count-execution]] and ends when approved adjustments are posted. Adjustments arising outside the count — damage, spoilage, and scrap — are excluded and covered in [[material-disposition-adjustment]]. The month-end tie-out of the resulting inventory balances is covered in [[month-end-inventory-reconciliation]].

### At a Glance

| Field | Value |
|---|---|
| Trigger | Recount-confirmed out-of-tolerance variances accumulate on the adjustment log during the week (SRC-001) |
| Frequency | Weekly — review on Friday, posting on Monday (SRC-001) |
| Preparer | Inventory Control Analyst |
| Reviewer | Plant Controller |
| Systems | NetSuite (adjustment log maintained and signed on paper) |
| Key inputs | Adjustment log of recount-confirmed variances |
| Key outputs | Signed adjustment log; posted inventory adjustments in NetSuite; rejected lines returned for a third count |

### Before You Start

- **Adjustment log** — [[cycle-count-execution]]; a printed log of recount-confirmed out-of-tolerance variances for the week, complete through the week's counts (SRC-001).

### Procedure

#### Step 1: Present the adjustment log for the Friday review

The Inventory Control Analyst presents the week's adjustment log — the recount-confirmed out-of-tolerance variances — to the Plant Controller for the Friday review (SRC-001, SRC-002).

- **System / Tool:** Paper adjustment log (printout)

#### Step 2: Review and disposition each line on the log

The Plant Controller reviews the adjustment log every Friday and approves or challenges each line (SRC-001).

- **Expected Result:** Every line on the log is either approved for posting or rejected for a further count

#### Step 3: Sign the adjustment log

The Plant Controller signs the printed log as evidence of the review and approval (SRC-001).

- **Evidence Required:** Signed adjustment log printout

> **VALIDATION REQUIRED — GAP-01:** Where the signed adjustment logs are filed and how long they are retained is unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Inventory Control Analyst

#### Step 4: Return rejected lines for a third count

- **Condition:** the Plant Controller rejects a line

Rejected lines go back for a third count before they can be adjusted (SRC-001).

> **VALIDATION REQUIRED — GAP-02:** How the third count is executed — who performs it, and whether the recount staging and independent-pair rules of [[cycle-count-execution]] apply — is unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Inventory Control Analyst

#### Step 5: Post approved adjustments in NetSuite on Monday

The Inventory Control Analyst posts the approved adjustments in NetSuite on Monday. Approved-but-unposted adjustments are held over the weekend between sign-off and posting (SRC-001, SRC-002).

- **Expected Result:** Every approved line on the signed log is reflected as a posted inventory adjustment in NetSuite

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite inventory adjustment entry for an approved log line, validating that the posted quantity and item match the signed adjustment log.

### Outputs & Evidence

- **Posted inventory adjustments** — approved count variances posted in NetSuite on Monday, correcting book quantities to the confirmed counts (SRC-001).
- **Signed adjustment log** — the Plant Controller's signed printout evidencing the Friday review (SRC-001).
- **Rejected lines** — returned for a third count; only lines that clear a further count come back to a later log (SRC-001).

### Key Controls

> **CONTROL — CTRL-001:** The Plant Controller reviews the adjustment log line by line each Friday and approves or challenges each entry; only approved lines are posted (SRC-001).
> - **Type:** Preventive
> - **Frequency:** Weekly (Friday)
> - **Owner:** Plant Controller

> **CONTROL — CTRL-002:** The Plant Controller physically signs the adjustment log printout as evidence of approval before any adjustment is posted (SRC-001).
> - **Type:** Preventive
> - **Frequency:** Weekly (Friday)
> - **Owner:** Plant Controller

> **CONTROL — CTRL-003:** No count adjustment is posted the same day as the count; posting occurs only after recount confirmation, Friday review, and sign-off (SRC-001).
> - **Type:** Preventive
> - **Frequency:** Each adjustment
> - **Owner:** Plant Controller

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The adjustment approval is a paper signature on a printout rather than an approval step in NetSuite, despite an audit request to move the sign-off into the system (SRC-001, SRC-002).
> - **Impact:** Approval evidence exists only on paper; the audit request remains unaddressed (SRC-001).
> - **Severity:** High

> **PAIN POINT — PP-002:** Approved adjustments are signed off on Friday but not posted until Monday, so approved-but-unposted adjustments sit in the Inventory Control Analyst's tray over the weekend (SRC-002).
> - **Impact:** Book quantities remain misstated for known, approved variances over the weekend gap between approval and posting (SRC-002).
> - **Severity:** Medium

> **PAIN POINT — PP-003:** At month-end, if the last Friday review falls before the final count day, adjustments from that last count post into the following period; the Corporate Controller has asked for period-end adjustments to be accrued, and this has never been done (SRC-002).
> - **Impact:** Known count variances at period-end are recorded in the wrong period, misstating the closing inventory balance (SRC-002).
> - **Severity:** High

> **IMPROVEMENT OPPORTUNITY — IO-001:** Replace the paper sign-off with an in-system approval step in NetSuite, as requested by audit (SRC-001).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Accrue period-end count adjustments that cannot be reviewed and posted before the period closes, as requested by the Corporate Controller (SRC-002).
> - **Addresses:** PP-003

```consult-meta
systems: [netsuite]
roles:   [inventory-control-analyst, plant-controller, corporate-controller]
```
