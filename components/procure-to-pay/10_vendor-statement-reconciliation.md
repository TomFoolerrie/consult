## Vendor Statement Reconciliation

### Scope

This procedure covers the comparison of supplier-issued statements of account to the corresponding vendor account balance and open items in NetSuite, the identification and documentation of reconciling items, and the retention of the completed reconciliation. It covers only vendors within the selected reconciliation population; vendors outside that population are not reconciled. It excludes the resolution of the underlying transactions themselves — missing or unposted invoices are worked through [[invoice-intake-and-capture]] and [[po-invoice-entry-and-three-way-match]], unapplied or disputed payments through [[weekly-payment-run]] and [[wire-and-manual-payment]], and vendor record corrections through [[vendor-master-data-maintenance]]. It also excludes the monthly bank reconciliation and the received-not-invoiced accrual, which are performed outside procure-to-pay. Procurement does not participate in this procedure (SRC-002).

### At a Glance

| Field | Value |
|---|---|
| Trigger | Quarter-end close per the AP Manager and the Corporate Controller; month-end per the prior SOP — see GAP-01 |
| Frequency | Disputed — quarterly, monthly or not performed; see GAP-01 |
| Preparer | Senior Accounts Payable Specialist |
| Reviewer | TBD — confirm with process owner (see GAP-04) |
| Systems | NetSuite; Finance Shared Drive |
| Key inputs | Supplier statement of account; NetSuite vendor account activity and open payables; the reconciliation vendor list |
| Key outputs | Completed statement reconciliation worksheet; documented reconciling items |

### Before You Start

- **Reconciliation vendor list** — held by the Senior Accounts Payable Specialist; the working list was issued by the Accounts Payable Manager in approximately 2024 and is understood to represent the top fifty vendors by spend (SRC-001). Currency of the list is unconfirmed (see GAP-02).
- **Supplier statement of account** — issued by the vendor; must cover the period being reconciled. How statements are requested or received is not described in any source (see GAP-03).
- **NetSuite vendor account** — [[po-invoice-entry-and-three-way-match]], [[non-po-invoice-entry-and-approval]] and [[weekly-payment-run]] post the bills, credits and payments that make up the balance; the period being reconciled must be fully posted.
- **Statement reconciliation worksheet location** — Finance Shared Drive, in the folder designated for reconciliations per §9.2 of the prior SOP (SRC-006); the folder and any worksheet template were not verified in the field (SRC-005).

### Procedure

#### Step 1: Determine the vendor population for the period

The vendors to be reconciled are drawn from the reconciliation list held by the Senior Accounts Payable Specialist. In practice the list is the one issued by the Accounts Payable Manager in approximately 2024 and understood to be the top fifty vendors by spend; the prior SOP instead defines the population as all suppliers with annual spend in excess of $50,000 (SRC-001, SRC-006).

> **VALIDATION REQUIRED — GAP-01:** Whether this procedure is performed, and on what cadence and population, is described three different ways.
> - **Note:** Do not operate to a stated cadence until it is confirmed — the frequency and population rows in At a Glance are unresolved.
> - **Detail:** §9.1 of the prior SOP requires monthly reconciliation of all suppliers with annual spend over $50,000 (SRC-006). The Accounts Payable Manager describes reconciliation of top vendors quarterly, scheduled on the close calendar for the quarter-end month (SRC-001). The Corporate Controller states the SOP cadence is not being met, understands the practice to be quarterly for top vendors, and has accepted that for headcount reasons — while allowing that it may not have happened in some quarters (SRC-003). The Procurement Lead has never been shown a reconciled statement and doubts the process is real (SRC-002). No completed reconciliation was produced during fieldwork (SRC-005). Resolution sits with the Corporate Controller, who owns the policy.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **VALIDATION REQUIRED — GAP-02:** The basis, owner and refresh cadence of the reconciliation vendor list are unconfirmed.
> - **Note:** The working list has not been refreshed since approximately 2024; confirm who owns it and how it is regenerated before relying on it as the population.
> - **Detail:** The Senior Accounts Payable Specialist works from a list received from the Accounts Payable Manager in approximately 2024 and is not aware of it having been refreshed, and is not certain the list is in fact the top fifty by spend (SRC-001). No source describes a spend report, saved search or other derivation behind the list, nor a review that would bring it back into line with the $50,000 spend threshold in §9.1 of the prior SOP (SRC-006).
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Obtain the supplier statement of account

A statement of account is obtained for each vendor in the population, covering the period being reconciled. No source describes how statements are requested, received or logged.

> **VALIDATION REQUIRED — GAP-03:** The method of obtaining supplier statements is not established.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 3: Compare the statement to the NetSuite vendor account

The open items and balance on the supplier statement are compared to the vendor account in NetSuite for the same period, and differences are identified. The specific NetSuite report or saved search used, and the fields compared, were not described by any interviewee.

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite vendor account view used for the comparison, showing open bills, credits and applied payments for a single vendor and period — validates the comparison basis described in this step.

#### Step 4: Document the reconciling items and clear them

Differences between the statement and the NetSuite vendor account are recorded as reconciling items on the reconciliation worksheet. Under §9.1 of the prior SOP, reconciling items are to be documented and cleared within thirty days (SRC-006). Whether that clearance window is tracked in practice, and how an aged reconciling item is escalated, was not established in the field (SRC-005).

Items requiring transaction-level correction are worked through the procedure that owns them — a missing supplier invoice through [[invoice-intake-and-capture]], a mismatched or unposted bill through [[po-invoice-entry-and-three-way-match]] or [[non-po-invoice-entry-and-approval]], and an unapplied or returned payment through [[weekly-payment-run]] or [[wire-and-manual-payment]].

#### Step 5: Retain the completed reconciliation worksheet

The completed worksheet is retained on the Finance Shared Drive in the folder designated for reconciliations, per §9.2 of the prior SOP (SRC-006). Whether completed worksheets exist for recent periods was not verified, and no reconciliation was produced during fieldwork (SRC-005).

> **VALIDATION REQUIRED — GAP-04:** Whether a completed statement reconciliation is reviewed or approved, and by whom, is unconfirmed.
> - **Note:** No reviewer is identified for this procedure; confirm whether a review occurs before treating the reconciliation as evidenced.
> - **Detail:** §9.2 of the prior SOP requires only that the reconciliation be evidenced by a completed worksheet retained on the shared drive; it names no reviewer or approver (SRC-006). No interviewee described a review, sign-off or reporting of results, and the Corporate Controller describes accepting a reduced cadence rather than reviewing output (SRC-001, SRC-003).
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

### Outputs & Evidence

- **Completed statement reconciliation worksheet** — retained on the Finance Shared Drive in the folder designated for reconciliations per §9.2 of the prior SOP (SRC-006).
- **Documented reconciling items** — recorded on the worksheet, to be cleared within thirty days per §9.1 of the prior SOP (SRC-006).
- **Evidence retained:** TBD — confirm with process owner. The retention period for completed worksheets is not stated in any source, and the existence of worksheets for recent periods was not verified (SRC-005).
- **Not retained:** No log of statements requested or received is described, so there is no record of which vendors in the population were attempted and which produced no statement. No record of review or sign-off is retained (see GAP-04), and no report of reconciliation results is made to the Corporate Controller.

### Key Controls

> **CONTROL — CTRL-001:** Supplier statements of account are reconciled to the NetSuite vendor account balance and open items, and differences are identified and documented.
> - **Type:** Detective
> - **Frequency:** TBD — quarterly per the Accounts Payable Manager and the Corporate Controller, monthly per the prior SOP, and possibly not performed in some periods (see GAP-01)
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-002:** Reconciling items identified on a statement reconciliation are documented and cleared within thirty days.
> - **Type:** Corrective
> - **Frequency:** TBD — per reconciliation performed (see GAP-01)
> - **Owner:** TBD — confirm with process owner

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The procedure is not performed at the cadence or over the population the prior SOP requires, and no party could confirm it was performed in any given recent period.
> - **Impact:** The detective control over the completeness of recorded payables operates inconsistently or not at all; unrecorded invoices, duplicate charges and misapplied credits can persist undetected between periods. The Corporate Controller attributes the reduced cadence to available headcount and has accepted it without a documented policy change.
> - **Severity:** High

> **PAIN POINT — PP-002:** The vendor population is taken from a static list issued in approximately 2024 that has not been refreshed and is not confirmed to match any defined selection basis.
> - **Impact:** Vendors that have since become significant by spend are outside the reconciliation population, and vendors that have declined consume effort; the population no longer ties to the $50,000 spend threshold in the prior SOP.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** No completed reconciliation worksheet was produced or located during fieldwork, and no review or reporting of results occurs.
> - **Impact:** The procedure cannot be evidenced to an auditor even for periods in which it was performed, and errors surfaced by a reconciliation have no escalation path.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Set a single documented cadence and population for statement reconciliation that the department can sustain, formally amend the SOP to match it, and place the resulting task on the close calendar with a named owner.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Regenerate the reconciliation vendor list from a NetSuite vendor spend report on a defined refresh cycle rather than maintaining a static list.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Adopt a standard reconciliation worksheet stored in a defined shared-drive location, with preparer and reviewer sign-off and an aged reconciling-item schedule reported to the Corporate Controller.
> - **Addresses:** PP-003, PP-001

```consult-meta
systems: [netsuite, finance-shared-drive]
roles:   [senior-ap-specialist, ap-manager, corporate-controller, procurement-lead]
```
