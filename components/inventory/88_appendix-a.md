## Appendix — Pain Points & Improvement Opportunities

<!-- derived: appendix-a; writer: python -->

_Pain points and improvement opportunities observed in the current-state walkthroughs, with the impact and severity recorded for each. Each pain point is shown alongside the improvement opportunities that address it. IDs are numbered sequentially through the document; items are grouped by sub-process._


#### Inventory Counting

| Pain Point | Impact | Severity | Improvement Opportunity |
|---|---|---|---|
| PP-01 ([[#cycle-count-execution]]) — The cycle-count tolerance table lives in a saved search maintained personally by the Inventory Control Analyst rather than in approved system configuration (SRC-002). | A mis-edit to the saved search would silently change the tolerances that drive auto-posting, and nobody would know (SRC-002). | High | **IO-01** — Move the cycle-count tolerances from the user-maintained saved search into approved, change-controlled NetSuite configuration, as the Inventory Control Analyst has requested (SRC-002). |
| PP-02 ([[#cycle-count-execution]]) — Count-driven variances frequently originate upstream at the receiving-to-putaway handoff — short counts, receipts posted against the wrong purchase order (PO) line, or wrong units of measure on the item-vendor record — and the cycle count detects them only weeks later (SRC-001). | Inventory records are wrong from day one of the receipt until the next scheduled count of the affected location; unit-of-measure errors can misstate on-hand by a large factor (SRC-001). | Medium | — |

#### Inventory Adjustments

| Pain Point | Impact | Severity | Improvement Opportunity |
|---|---|---|---|
| PP-03 ([[#count-adjustment-review-and-posting]]) — The adjustment approval is a paper signature on a printout rather than an approval step in NetSuite, despite an audit request to move the sign-off into the system (SRC-001, SRC-002). | Approval evidence exists only on paper; the audit request remains unaddressed (SRC-001). | High | **IO-02** — Replace the paper sign-off with an in-system approval step in NetSuite, as requested by audit (SRC-001). |
| PP-04 ([[#count-adjustment-review-and-posting]]) — Approved adjustments are signed off on Friday but not posted until Monday, so approved-but-unposted adjustments sit in the Inventory Control Analyst's tray over the weekend (SRC-002). | Book quantities remain misstated for known, approved variances over the weekend gap between approval and posting (SRC-002). | Medium | — |
| PP-05 ([[#count-adjustment-review-and-posting]]) — At month-end, if the last Friday review falls before the final count day, adjustments from that last count post into the following period; the Corporate Controller has asked for period-end adjustments to be accrued, and this has never been done (SRC-002). | Known count variances at period-end are recorded in the wrong period, misstating the closing inventory balance (SRC-002). | High | **IO-03** — Accrue period-end count adjustments that cannot be reviewed and posted before the period closes, as requested by the Corporate Controller (SRC-002). |
| PP-06 ([[#material-disposition-adjustment]]) — Photographs are supposed to be attached to damage-claim forms but usually are not (SRC-001). | Damage claims lack supporting visual evidence at the time the adjustment is posted. | Medium | **IO-04** — Replace the paper Material Disposition Form with an electronic form or workflow that enforces supervisor and Plant Controller approvals and requires photograph attachment for damage claims before the adjustment can be posted. *(also addresses PP-07)* |
| PP-07 ([[#material-disposition-adjustment]]) — The Material Disposition Form is entirely paper-based, from preparation through sign-off to delivery for posting (SRC-001). | Approvals and routing occur outside the system, leaving no system audit trail before the posting itself and making forms and their evidence easy to lose. | Medium | **IO-04** — Replace the paper Material Disposition Form with an electronic form or workflow that enforces supervisor and Plant Controller approvals and requires photograph attachment for damage claims before the adjustment can be posted. *(also addresses PP-06)* |

#### Warehouse Operations

| Pain Point | Impact | Severity | Improvement Opportunity |
|---|---|---|---|
| PP-08 ([[#putaway-and-bin-confirmation]]) — Receiving errors propagate undetected into inventory. The Warehouse Manager describes the receipt-posted-to-putaway- confirmed handoff as where most book-to-floor variances are born: if the receiver short-counts or posts against the wrong PO line, the on-hand record is wrong from day one and the error is only detected weeks later when the cycle count reaches that location (SRC-001). | Book-to-floor variances persist for weeks until a cycle count detects them (SRC-001). | High | — |
| PP-09 ([[#putaway-and-bin-confirmation]]) — Unit of measure errors on item-vendor records distort on-hand quantities. | A wrong unit of measure causes receiving to post eaches as cases, leaving on-hand off by a factor of twelve; the warehouse team can only flag the record to the Procurement Lead and absorb the fallout until it is corrected (SRC-001). | Medium | — |

#### Inventory Accounting

| Pain Point | Impact | Severity | Improvement Opportunity |
|---|---|---|---|
| PP-10 ([[#month-end-inventory-reconciliation]]) — The Coupa-to-NetSuite sync is unreliable in some months; when it fails, the in-transit list is wrong and the analyst reconciles the timing differences to a moving target (SRC-002). | In-transit reconciling items are distorted, and the reconciliation takes longer and is less reliable in affected months (SRC-002). | Medium | **IO-05** — Raise the Coupa-to-NetSuite interface reliability with the Procurement Lead, who owns the interface, so the in-transit data is stable before the workday 2 reconciliation (SRC-002). |
| PP-11 ([[#month-end-inventory-reconciliation]]) — The reconciliation workbook is stored in a shared-drive folder named "150 - Property and Equipment," a misnamed location that predates the current analyst (SRC-002). | The workbook is filed under an unrelated account name, making it harder for reviewers and auditors to locate (SRC-002). | Low | **IO-06** — Move the reconciliation workbook to a correctly named inventory folder in the month-end close directory (SRC-002). |
