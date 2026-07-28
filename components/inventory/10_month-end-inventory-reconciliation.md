## Month-End Inventory Sub-Ledger to GL Reconciliation

### Scope

This procedure covers the month-end reconciliation of the inventory sub-ledger to the general ledger (GL): comparing the NetSuite inventory valuation report to the GL inventory account balances by location, documenting reconciling items in the reconciliation workbook, and the Plant Controller's review of the completed workbook. It begins after period-end count adjustments have been posted under [[count-adjustment-review-and-posting]] and ends when the reviewed workbook is retained on the shared drive. The execution of physical counts is covered in [[cycle-count-execution]], and adjustments for damage, spoilage, and scrap are covered in [[material-disposition-adjustment]]. Remediation of the Coupa-to-NetSuite interface is handled by Procurement under the Procure to Pay process and is excluded here.

### At a Glance

| Field | Value |
|---|---|
| Trigger | Month-end close calendar — reconciliation prepared on workday 2 (SRC-002) |
| Frequency | Monthly (SRC-002) |
| Preparer | Inventory Control Analyst |
| Reviewer | Plant Controller — review complete by workday 4 (SRC-002) |
| Systems | NetSuite (reconciliation workbook maintained on the shared drive) |
| Key inputs | NetSuite inventory valuation report by location; GL inventory account balances |
| Key outputs | Completed reconciliation workbook with documented reconciling items, reviewed by the Plant Controller |

### Before You Start

- **NetSuite inventory valuation report** — run as of period end, by location (SRC-002).
- **GL inventory account balances** — the period-end balances of the GL inventory accounts, by location (SRC-002).
- **Posted count adjustments** — [[count-adjustment-review-and-posting]]; the period's approved count adjustments posted in NetSuite (adjustments approved after the last Friday review may post into the next period — see that procedure's known issues).
- **Reconciliation workbook** — the prior workbook on the shared drive under Accounting/Month End Close/2026/150 - Property and Equipment (SRC-002).

### Procedure

#### Step 1: Run the NetSuite inventory valuation report as of period end

On workday 2, the Inventory Control Analyst runs the NetSuite inventory valuation report by location as of the period end (SRC-002).

#### Step 2: Compare the valuation report to the GL inventory accounts by location

The inventory valuation report is compared against the GL inventory account balances, location by location, and differences are identified (SRC-002).

- **Expected Result:** Every location's sub-ledger balance either ties to the GL or carries an identified difference to be documented

#### Step 3: Document each reconciling item in the reconciliation workbook

Each reconciling item is documented in the reconciliation workbook. Timing differences from in-transit receipts are the usual reconciling item: a goods receipt posted in Coupa on the last day of the period can reach NetSuite a day later through the sync (SRC-002).

- **System / Tool:** Reconciliation workbook on the shared drive
- **Evidence Required:** A documented explanation in the workbook for each reconciling item

> **VALIDATION REQUIRED — GAP-01:** How reconciling items other than in-transit timing differences are investigated and resolved — and whether there is a threshold or aging rule requiring escalation or adjustment — is unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Inventory Control Analyst

#### Step 4: Save the completed workbook to the shared drive

The completed workbook is saved on the shared drive under Accounting/Month End Close/2026/150 - Property and Equipment (SRC-002).

> **VALIDATION REQUIRED — GAP-03:** How long completed reconciliation workbooks are retained is unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Inventory Control Analyst

> **SCREENSHOT PLACEHOLDER — SC-01:** The completed reconciliation workbook for a closed period, validating the location-by-location tie-out and the documented reconciling items.

#### Step 5: Plant Controller reviews the reconciliation

The Plant Controller reviews the completed workbook, including the documented reconciling items, by workday 4 (SRC-002).

> **VALIDATION REQUIRED — GAP-02:** How the Plant Controller's review is evidenced (sign-off, dated note in the workbook, or otherwise) is unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Plant Controller

### Outputs & Evidence

- **Completed reconciliation workbook** — the location-by-location tie-out with a documented explanation for each reconciling item, retained on the shared drive under Accounting/Month End Close/2026/150 - Property and Equipment (SRC-002).
- **Evidence retained:** the workbook, including the documented explanation for each reconciling item, on the shared drive (SRC-002).

### Key Controls

> **CONTROL — CTRL-001:** The inventory sub-ledger is reconciled to the GL inventory accounts by location each month on workday 2, with every reconciling item documented in the workbook (SRC-002).
> - **Type:** Detective
> - **Frequency:** Monthly (workday 2)
> - **Owner:** Inventory Control Analyst

> **CONTROL — CTRL-002:** The Plant Controller reviews the completed reconciliation, including the documented reconciling items, by workday 4 (SRC-002).
> - **Type:** Detective
> - **Frequency:** Monthly (workday 4)
> - **Owner:** Plant Controller

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The Coupa-to-NetSuite sync is unreliable in some months; when it fails, the in-transit list is wrong and the analyst reconciles the timing differences to a moving target (SRC-002).
> - **Impact:** In-transit reconciling items are distorted, and the reconciliation takes longer and is less reliable in affected months (SRC-002).
> - **Severity:** Medium

> **PAIN POINT — PP-002:** The reconciliation workbook is stored in a shared-drive folder named "150 - Property and Equipment," a misnamed location that predates the current analyst (SRC-002).
> - **Impact:** The workbook is filed under an unrelated account name, making it harder for reviewers and auditors to locate (SRC-002).
> - **Severity:** Low

> **IMPROVEMENT OPPORTUNITY — IO-001:** Raise the Coupa-to-NetSuite interface reliability with the Procurement Lead, who owns the interface, so the in-transit data is stable before the workday 2 reconciliation (SRC-002).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Move the reconciliation workbook to a correctly named inventory folder in the month-end close directory (SRC-002).
> - **Addresses:** PP-002

```consult-meta
systems: [netsuite, coupa]
roles:   [inventory-control-analyst, plant-controller, procurement-lead]
```
