## Vendor Statement Reconciliation

### A. Process Overview

Vendor statement reconciliation compares a supplier's statement of account to the
Company's accounts payable subledger in NetSuite, identifying invoices the supplier
shows as open that the Company has not recorded, items the Company shows as open that
the supplier has already applied, and misapplied payments or credits. It is performed
by the Senior Accounts Payable Specialist and is positioned as a close-calendar
activity. The procedure sits downstream of invoice recording — [[po-invoice-entry-and-three-way-match]]
and [[non-po-invoice-entry-and-approval]] — and of [[weekly-payment-run]], and it acts as a
detective backstop over both. Procurement does not participate; the activity is owned
entirely by Accounts Payable (SRC-002). The scope, cadence and even the operation of this
procedure are disputed across sources — see [[GAP-01 — RECONCILIATION CADENCE AND SCOPE]]
— so the flow below documents the activity as described rather than as verified in
operation. (SRC-001, SRC-002, SRC-003, SRC-005, SRC-006)

### B. Quick Reference

- **Trigger:** Arrival of the close-calendar reconciliation task for the applicable
  period. The governing period is disputed — see [[GAP-01 — RECONCILIATION CADENCE AND SCOPE]].
- **Frequency:** TBD — confirm with process owner. The prior SOP specifies monthly;
  Accounts Payable and the Corporate Controller describe a quarterly practice; the
  Procurement Lead doubts it occurs (SRC-001, SRC-003, SRC-006, SRC-002).
- **Preparer:** Senior Accounts Payable Specialist
- **Reviewer:** TBD — confirm with process owner. No source describes a review or
  sign-off over the completed reconciliation.
- **Primary systems / tools:** NetSuite (accounts payable subledger); Finance Shared
  Drive (worksheet retention, per SOP)
- **Key outputs:** Completed reconciliation worksheet per in-scope supplier; list of
  reconciling items

### C. Pre-Requisites

- The period being reconciled is closed to further invoice entry, or the cut-off date
  used for the comparison is fixed and stated on the worksheet.
- The population of in-scope suppliers for the period is established. The basis for
  that population is disputed — see [[GAP-02 — IN-SCOPE VENDOR POPULATION]].
- Invoice recording for the period is substantially complete, so that timing
  differences are distinguishable from unrecorded liabilities.
- The preparer has read access to the NetSuite accounts payable subledger and to the
  designated Finance Shared Drive folder.

### D. Inputs

- **Supplier statement of account:** Issued by the Supplier. How statements are
  obtained is not described in any source — see [[GAP-03 — STATEMENT SOURCING]].
- **In-scope supplier list:** Provided to the Senior Accounts Payable Specialist by the
  Accounts Payable Manager. The list in use was issued in approximately 2024 and is not
  known to have been refreshed (SRC-001).
- **Accounts payable subledger detail:** NetSuite, for the supplier and period being
  reconciled.
- **Payment history for the period:** NetSuite, to identify payments in transit or
  applied by the supplier in a different period.
- **Prior-period reconciliation worksheet:** Finance Shared Drive, where one exists, to
  carry forward unresolved reconciling items.

### E. Step-by-Step Procedure

#### Step 1: Establish the in-scope supplier population for the period

The Senior Accounts Payable Specialist works from the supplier list supplied by the
Accounts Payable Manager. The Accounts Payable Manager and the Senior Accounts Payable
Specialist describe the list as the top fifty suppliers by spend; the prior SOP instead
requires all suppliers with annual spend above fifty thousand dollars. The list held by
the preparer dates from approximately 2024 and has not been refreshed against current
spend (SRC-001, SRC-005, SRC-006).

- **Evidence Required:** The supplier list used for the period, with its effective date.

> **VALIDATION REQUIRED — GAP-01:** The cadence and scope of this procedure are in
> conflict across sources and the conflict extends to whether the procedure operates at
> all. The prior SOP (section 9.1) requires monthly reconciliation of all suppliers with
> annual spend above fifty thousand dollars. The Accounts Payable Manager describes a
> quarterly reconciliation of top suppliers, performed in the quarter-end month per the
> close calendar. The Corporate Controller states the monthly requirement is not being
> met, that the quarterly practice has been accepted for headcount reasons, and that the
> Procurement Lead's position — that it may not happen in some quarters — may be correct.
> The Procurement Lead has never been shown a reconciled statement. Confirm the cadence
> actually in operation, the periods for which reconciliations were in fact completed,
> and whether the SOP requirement is to be retained or formally amended.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **VALIDATION REQUIRED — GAP-02:** The basis for the in-scope supplier population is
> unresolved — top fifty by spend (per Accounts Payable) versus annual spend above fifty
> thousand dollars (per the prior SOP) — and the list in use has not been refreshed since
> approximately 2024. Confirm the governing selection criterion, the owner of the list,
> and the required refresh frequency.
> - **Nature:** conflict
> - **Owner to confirm:** Accounts Payable Manager

> **SCREENSHOT PLACEHOLDER — SC-01:** The in-scope supplier list as currently held by
> the Senior Accounts Payable Specialist, showing its effective date, to evidence the
> population basis and the currency of the list.

#### Step 2: Obtain the supplier statement of account

The Senior Accounts Payable Specialist obtains the statement of account for each
in-scope supplier for the period. No source describes whether statements are requested
from suppliers, received unsolicited, or retrieved from supplier portals, nor where
they are held pending reconciliation.

- **System / Tool:** TBD — confirm with process owner.
- **Evidence Required:** The supplier statement used, retained with the reconciliation.

> **VALIDATION REQUIRED — GAP-03:** The mechanism by which supplier statements are
> obtained is not described in any source. Confirm whether statements are requested by
> Accounts Payable or sent by the Supplier, the channel used, the expected turnaround,
> and the action taken where a supplier does not provide a statement.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 3: Extract the accounts payable subledger detail

The Senior Accounts Payable Specialist extracts open and period activity for the
supplier from the NetSuite accounts payable subledger for comparison against the
statement. The specific report or saved search used, and the navigation path to it, are
not described in any source.

- **System / Tool:** NetSuite
- **Navigation Path:** TBD — confirm with process owner.
- **Fields / Parameters:** TBD — confirm with process owner.

> **VALIDATION REQUIRED — GAP-04:** The NetSuite report or saved search used to extract
> supplier subledger detail, its parameters (period, status, subsidiary), and the
> navigation path to it are undocumented. Confirm the extract used and whether it is
> standardized across preparers.
> - **Nature:** unknown
> - **Owner to confirm:** Senior Accounts Payable Specialist

#### Step 4: Compare the statement to the subledger and identify reconciling items

The Senior Accounts Payable Specialist compares the statement to the subledger extract
and documents the differences on a reconciliation worksheet. Typical categories —
invoices on the statement not recorded in NetSuite, invoices recorded but not reflected
on the statement, payments in transit, and unapplied credits — are not enumerated in any
source, nor is the worksheet format prescribed beyond the SOP's requirement that a
completed worksheet exist.

- **Expected Result:** A worksheet showing the statement balance, the NetSuite subledger
  balance, and the reconciling items bridging the two.
- **Evidence Required:** Completed reconciliation worksheet per supplier.

> **SCREENSHOT PLACEHOLDER — SC-02:** A completed vendor statement reconciliation
> worksheet for a recent period, to evidence the worksheet format, the reconciling-item
> categories used, and whether a preparer and reviewer are identified on the face of it.

#### Step 5: Resolve and clear reconciling items

The prior SOP requires that reconciling items be documented and cleared within thirty
days. No source describes how items are actually pursued, who is contacted at the
supplier, how unrecorded invoices are routed back into [[invoice-intake-and-capture]] for
entry, or how aged unresolved items are escalated. Where the reconciliation identifies a
defect in the supplier record itself, the correction is made through
[[vendor-master-data-maintenance]].

> **VALIDATION REQUIRED — GAP-05:** The resolution path for reconciling items is
> undocumented, and there is no evidence that the SOP's thirty-day clearing requirement
> is monitored. Confirm how items are pursued with the Supplier, how unrecorded invoices
> are routed for entry, who tracks ageing, and what escalation applies to items open
> beyond thirty days.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 6: Retain the completed reconciliation

The prior SOP requires that reconciliations be evidenced by a completed worksheet
retained on the Finance Shared Drive in a folder designated for that purpose. The
existence of that folder and of completed worksheets within it has not been verified,
and no source describes a review or approval of the completed reconciliation.

- **System / Tool:** Finance Shared Drive
- **Navigation Path:** TBD — confirm with process owner.
- **Evidence Required:** Completed worksheet with supporting statement, retained in the
  designated folder.

> **VALIDATION REQUIRED — GAP-06:** The retention location for completed reconciliation
> worksheets is stated in the prior SOP but its existence and contents are unverified,
> and no reviewer or approver of the completed reconciliation is identified in any
> source. Confirm the folder path, inspect the worksheets retained for recent periods,
> and confirm whether a review or sign-off is required and by whom.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

### F. Key Controls

> **CONTROL — CTRL-001:** The supplier's statement of account is reconciled to the
> NetSuite accounts payable subledger, and differences are documented as reconciling
> items on a reconciliation worksheet — a detective check over unrecorded liabilities,
> duplicate or misapplied invoices, and misapplied payments.
> - **Type:** Detective
> - **Frequency:** TBD — see [[GAP-01 — RECONCILIATION CADENCE AND SCOPE]]
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-002:** Reconciling items identified are documented and cleared within
> thirty days, per the prior SOP. No source confirms that clearing is tracked or
> enforced in current practice.
> - **Type:** Corrective
> - **Frequency:** TBD — see [[GAP-05 — RECONCILING ITEM RESOLUTION]]
> - **Owner:** TBD — confirm with process owner

### G. Outputs

- **Completed reconciliation worksheet:** One per in-scope supplier per period, bridging
  the statement balance to the NetSuite subledger balance.
- **Reconciling item listing:** Differences requiring follow-up with the Supplier or
  correction in NetSuite; unrecorded invoices are routed for entry.
- **Downstream recipients:** TBD — confirm with process owner. No source describes the
  completed reconciliation being reported to the Accounts Payable Manager or the
  Corporate Controller.
- **Evidence retained:** Completed worksheet on the Finance Shared Drive in the folder
  designated by the prior SOP; retention verified only as a policy statement, not in
  practice.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The cadence and existence of the procedure are unresolved.
> The prior SOP requires monthly reconciliation; Accounts Payable and the Corporate
> Controller describe a quarterly practice; the Procurement Lead has never been shown a
> reconciled statement and doubts the process is real, a view the Corporate Controller
> concedes may be correct for some quarters.
> - **Impact:** The Company's principal detective control over unrecorded liabilities,
>   duplicate invoices and misapplied payments cannot be relied upon, and current practice
>   does not meet its own written policy.
> - **Severity:** High

> **PAIN POINT — PP-002:** The in-scope supplier population is worked from a list issued
> in approximately 2024 that has not been refreshed, and its selection basis (top fifty
> by spend) differs from the SOP criterion (annual spend above fifty thousand dollars).
> - **Impact:** Suppliers whose spend has grown since 2024 are outside the reconciliation
>   population, and coverage cannot be demonstrated against any stated criterion.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Completed reconciliations are required by policy to be
> retained on the Finance Shared Drive, but no completed worksheet has been produced or
> located, and no review or sign-off over the reconciliation is described by any source.
> - **Impact:** The control leaves no verifiable evidence trail, so neither completion
>   nor quality can be substantiated to internal or external review.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Establish a single approved cadence and scope for
> vendor statement reconciliation, resourced to what Accounts Payable can sustain, and
> amend the SOP so that the written policy and the operating practice agree. Track
> completion per period on the close calendar.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Derive the in-scope supplier population from a
> NetSuite spend report at the start of each cycle against a stated threshold, rather
> than a static list, and assign ownership of the refresh.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Adopt a standard reconciliation worksheet with
> named preparer, reviewer and date, retained in a defined Finance Shared Drive folder,
> and add a periodic review of reconciling items aged beyond thirty days.
> - **Addresses:** PP-003

```consult-meta
systems: [netsuite, finance-shared-drive]
roles:   [senior-ap-specialist, ap-manager, corporate-controller, procurement-lead, supplier]
```
