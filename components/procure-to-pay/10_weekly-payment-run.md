## Weekly Payment Run

<!-- scope note: covers variants — ACH (NACHA file upload and release); Check run (MICR print and positive pay issue file). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### A. Process Overview

This procedure covers the weekly disbursement cycle: building the payment proposal in
NetSuite from bills that have become due, obtaining Corporate Controller approval of the
proposal, and executing the resulting payments through the two settlement methods used in
the run — an ACH batch transmitted to Chase Connect as a NACHA file and released by a
second individual, and a check run printed on the MICR printer in the Accounts Payable
room with a positive pay issue file transmitted to the bank at print. It runs once per
week and is prepared by the Accounts Payable Manager, with approval and bank release by
the Corporate Controller or, in the Controller's absence, release by the Treasury Analyst.
It consumes bills made eligible for payment in [[po-invoice-entry-and-three-way-match]]
and [[non-po-invoice-entry-and-approval]], and hands off to
[[positive-pay-exception-handling]] for the disposition of returned check exceptions.
Wires and manual or emergency checks are issued outside this cycle and are covered in
[[wire-and-manual-payment]]; employee reimbursements settle through the payroll ACH file
on a separate bank account and are outside Procure to Pay entirely.
(SRC-001, SRC-003, SRC-005, SRC-006)

### B. Quick Reference

- **Trigger:** The weekly disbursement cycle date. The proposal is built by due date, capturing bills due through the following Friday plus any bill carrying a discount about to expire.
- **Frequency:** Weekly, one disbursement cycle. The days of the week on which the proposal, the approval and the release fall are disputed across sources — see the calendar gap raised at Step 1.
- **Preparer:** Accounts Payable Manager (proposal build, ACH file generation and upload, check print, issue file transmission).
- **Reviewer:** Corporate Controller (approves the proposal in NetSuite and releases the ACH file at the bank; the Treasury Analyst releases in the Controller's absence).
- **Primary systems / tools:** NetSuite (Pay Bills, payment register); Chase Connect (NACHA file upload and release, positive pay issue file receipt); MICR check printer in the Accounts Payable room; Microsoft Excel (proposal export and review).
- **Key outputs:** Approved payment proposal; released NACHA ACH batch; printed check run; positive pay issue file transmitted to Chase Connect; NetSuite payment register.

### C. Pre-Requisites

- Bills are recorded and eligible for payment in NetSuite — purchase order bills matched and released per [[po-invoice-entry-and-three-way-match]], non-PO bills fully approved per [[non-po-invoice-entry-and-approval]].
- The supplier record in NetSuite carries the payment method and, for ACH, current remit-to banking details verified per [[vendor-banking-change]].
- The Accounts Payable Manager holds NetSuite access to the Pay Bills function and a Chase Connect user ID with file upload but **no** release entitlement.
- The releasing individual (Corporate Controller or Treasury Analyst) holds a separate Chase Connect user ID and token carrying release entitlement.
- Check stock is available in the locked drawer in the Accounts Payable room and the signature plate is available in the safe; the combination is held only by the Accounts Payable Manager and the Corporate Controller.

### D. Inputs

- **Bills due for payment:** NetSuite — the population of approved, released bills with a due date within the selection window.
- **Discount-eligible bills:** NetSuite — bills whose early-payment discount expires before the next cycle, added to the selection irrespective of due date.
- **Supplier payment method and remit-to details:** NetSuite vendor master, maintained per [[vendor-master-data-maintenance]] — determines whether a given payment settles by ACH or by check.
- **Available funding position:** TBD — confirm with process owner. No source described a funding or cash-position check performed before release.

### E. Step-by-Step Procedure

#### Step 1: Build the payment proposal

The Accounts Payable Manager builds the weekly payment proposal in NetSuite, filtering the
open payable population on due date through the following Friday and adding any bill whose
early-payment discount is about to expire. A normal week produces approximately four to
six hundred proposed lines totalling $2.0–2.5 million.

- **System / Tool:** NetSuite
- **Navigation Path:** Transactions > Payables > Pay Bills
- **Fields / Parameters:** Due date through the following Friday; discount-expiring bills added to the selection.
- **Expected Result:** A proposed payment list covering the cycle.

The day of the week on which this step falls, and its spacing from approval and release,
are unresolved — see [[GAP-02 — PAYMENT RUN CALENDAR]].

> **VALIDATION REQUIRED — GAP-02:** The days of the week on which the proposal is built, approved and released. Three sources give three answers: the standard operating procedure specifies proposal Monday and release Wednesday (SRC-006); the Accounts Payable Manager describes proposal Wednesday afternoon and release Thursday morning (SRC-001); the Corporate Controller describes proposal Tuesday, review Wednesday, release Thursday, settling Friday (SRC-003). The Corporate Controller observed that if the Accounts Payable Manager's calendar is the one in operation, the Controller reviews the proposal and releases the file on the same morning, compressing the review to the point that it may not be an independent check — the discrepancy is itself a potential control finding, not only a documentation defect (SRC-005). Confirm the calendar actually operated and whether approval and release fall on the same day.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite Pay Bills selection screen showing the due-date filter and discount criteria, validating how the proposal population is defined.

#### Step 2: Review and scrub the proposed list

The Accounts Payable Manager exports the proposal to Excel, reviews it, and removes any
line that should not pay in this cycle. No source described the criteria applied on that
review, nor a record of the lines removed — see [[GAP-03 — PROPOSAL SCRUB CRITERIA]].

- **System / Tool:** NetSuite; Microsoft Excel
- **Expected Result:** A scrubbed proposal ready for approval.
- **Evidence Required:** The Excel export of the proposal as presented for approval.

> **VALIDATION REQUIRED — GAP-03:** The criteria the Accounts Payable Manager applies when removing lines from the proposed list, and whether removals and their reasons are recorded anywhere.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 3: Obtain Corporate Controller approval of the proposal

The scrubbed proposal is submitted to the Corporate Controller, who reviews and approves
the run before any payment file is generated. The Accounts Payable Manager cannot release
a self-built proposal; this separation is the primary preventive control over the run
(CTRL-001 in F). The standard operating procedure requires that evidence of the approval
be retained, but no source could state where that evidence is held — see
[[GAP-01 — PROPOSAL APPROVAL EVIDENCE]].

- **System / Tool:** NetSuite
- **Expected Result:** The proposal is approved and the run is authorized for file generation and check print.
- **Evidence Required:** Evidence of the Corporate Controller's approval — TBD — confirm with process owner.

> **VALIDATION REQUIRED — GAP-01:** Where evidence of the Corporate Controller's approval of the payment proposal is actually stored. The standard operating procedure requires evidence of approval to be retained (SRC-006) and the Corporate Controller confirmed evidence is retained but did not state where; no source could identify a location for the approved Excel export or a corresponding approval record in NetSuite (SRC-003, SRC-005). Confirm the form the approval takes and the retention location.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 4: Generate and execute the payment files — branch by payment method

The approved run is executed through two settlement methods in the same cycle. Steps 4a
and 4b below apply respectively; the preceding steps are performed once for the whole run.

##### Step 4a: ACH — generate, upload and release the NACHA file

The Accounts Payable Manager generates the ACH file from the approved run in NetSuite in
NACHA format and uploads it to Chase Connect. The Accounts Payable Manager holds no
release entitlement. Release is performed at the bank by the Corporate Controller, or by
the Treasury Analyst when the Controller is unavailable, under a separate Chase Connect
user ID and token (CTRL-002 and CTRL-003 in F). Whether the second approver is required by
bank entitlement on every batch or only above a dollar threshold is unresolved — see
[[GAP-04 — ACH SECOND-APPROVER RULE]].

- **System / Tool:** NetSuite (file generation); Chase Connect (upload and release)
- **Fields / Parameters:** NACHA-format ACH file for the approved run.
- **Expected Result:** The batch is released at the bank and settles on the bank's normal ACH cycle.
- **Evidence Required:** Chase Connect record of the upload and of the release, showing the two distinct user IDs.

> **VALIDATION REQUIRED — GAP-04:** Whether a second approver on an ACH batch is enforced by bank entitlement on every batch or only above a dollar threshold. The Accounts Payable Manager states dual release is required on every batch with no dollar floor, a practice adopted following a 2022 phishing incident (SRC-001). The Corporate Controller states the Chase Connect entitlement threshold is $100,000 and that a single release is permitted below it, so that the observed dual release reflects practice — and the fact that the weekly batch always exceeds the threshold — rather than configuration, and asked that the control be written as configured with the stricter practice noted (SRC-003). The open question is therefore not what happens on a normal weekly run but whether the control is system-enforced or conventional, which determines whether a smaller batch could release on a single approval. Obtain the Chase Connect entitlement matrix (SRC-005).
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-02:** The Chase Connect entitlement or approval-rule screen for the ACH service, validating whether the second-approver requirement carries a dollar floor.

##### Step 4b: Check run — print checks and transmit the positive pay issue file

Checks in the approved run — approximately thirty per week — are printed on the MICR
printer in the Accounts Payable room. Blank check stock is drawn from the locked drawer
and the signature plate from the safe. NetSuite transmits the positive pay issue file to
Chase Connect on the date the checks are issued (CTRL-004 in F).

- **System / Tool:** NetSuite; MICR check printer in the Accounts Payable room; Chase Connect
- **Expected Result:** Checks are printed and signed, and the corresponding issue file is transmitted to the bank the same day.
- **Evidence Required:** Confirmation that the issue file transmitted; the NetSuite check register for the run.

Custody of the stock and the plate is described in CTRL-005, but no source described a log
or a reconciliation of either to the checks printed — see
[[GAP-05 — CHECK STOCK AND PLATE CUSTODY]].

> **VALIDATION REQUIRED — GAP-05:** How check stock is logged in and out of the locked drawer, how the signature plate is signed out of the safe, and whether either is reconciled to the checks printed in the run.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

> **SCREENSHOT PLACEHOLDER — SC-03:** The NetSuite positive pay issue file setup and transmission confirmation, validating that the file is generated and sent at check print.

#### Step 5: Hand off downstream

Positive pay exceptions returned by the bank following the check run are dispositioned
under [[positive-pay-exception-handling]]. The resulting NetSuite payment register is the
input to the monthly bank reconciliation performed by the Assistant Controller's team.

- **System / Tool:** NetSuite; Chase Connect
- **Expected Result:** The run is complete, the register reflects the disbursements, and exception disposition passes to the downstream procedure.

### F. Key Controls

> **CONTROL — CTRL-001:** The Corporate Controller reviews and approves the payment proposal in NetSuite before any payment file is generated or check is printed; the Accounts Payable Manager who built the proposal cannot approve or release it.
> - **Type:** Preventive
> - **Frequency:** Each run
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-002:** The individual who uploads the ACH file to Chase Connect is not the individual who releases it. The Accounts Payable Manager holds upload entitlement only; release is performed by the Corporate Controller or the Treasury Analyst under a separate user ID and token.
> - **Type:** Preventive
> - **Frequency:** Each run
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-003:** A second approver is required on an ACH batch. As described at the bank this requirement carries a $100,000 threshold, below which a single release is permitted by entitlement; in practice every batch is released under dual approval, and the weekly run of $2.0–2.5 million always exceeds the threshold. Whether the requirement is system-enforced on all batches or is a convention stricter than the entitlement is unresolved (see the ACH second-approver gap at Step 4a).
> - **Type:** Preventive
> - **Frequency:** Each ACH batch
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-004:** A positive pay issue file is transmitted from NetSuite to Chase Connect on each date on which checks are issued, so that items presented against the account are matched to the issued population.
> - **Type:** Preventive
> - **Frequency:** Each check run
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-005:** Blank check stock is held in a locked drawer in the Accounts Payable room and the check signature plate is held in a safe whose combination is known only to the Accounts Payable Manager and the Corporate Controller.
> - **Type:** Preventive
> - **Frequency:** Continuous
> - **Owner:** Accounts Payable Manager

### G. Outputs

- **Approved payment proposal:** The scrubbed proposal as approved by the Corporate Controller, exported to Excel.
- **Released ACH batch:** NACHA file uploaded to and released in Chase Connect; settles on the bank's ACH cycle.
- **Printed check run:** Approximately thirty checks per week, MICR-printed and signature-plate signed.
- **Positive pay issue file:** Transmitted to Chase Connect at check print; establishes the exception population dispositioned in [[positive-pay-exception-handling]].
- **NetSuite payment register:** Input to the monthly bank reconciliation performed by the Assistant Controller's team; also the basis of the post-hoc register review offered as the compensating measure for the Corporate Controller both approving the run and releasing at the bank.
- **Evidence retained:** Chase Connect upload and release records; the NetSuite payment register and check register. Retention of the approved payment proposal itself is unconfirmed (see the approval-evidence gap at Step 3).

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The Corporate Controller both approves the payment run in NetSuite and releases the ACH file at Chase Connect, concentrating authorization of the disbursement and its execution in one individual. External audit has challenged this twice.
> - **Impact:** Separation of duties over outbound funds relies on the Accounts Payable Manager's inability to release rather than on independent authorization of the release itself; the compensating measure offered is a review of the payment register after the fact, which the Corporate Controller characterized as a weak story.
> - **Severity:** High

> **PAIN POINT — PP-002:** Three sources give three different payment run calendars, and no source could state which one is operated. If the Accounts Payable Manager's calendar is the live one, the Corporate Controller reviews the proposal and releases the file on the same morning.
> - **Impact:** The approval step may be compressed to the point that it is not an effective independent review of the proposal, and the standard operating procedure cannot be relied on to describe the cycle actually run.
> - **Severity:** High

> **PAIN POINT — PP-003:** The dollar floor on the ACH second-approver requirement is understood differently by the Accounts Payable Manager and the Corporate Controller, and no party has examined the bank entitlement configuration.
> - **Impact:** Whether the dual-release control is system-enforced or conventional is unknown, so it cannot be asserted that a smaller off-cycle or corrective batch would be prevented from releasing on a single approval.
> - **Severity:** High

> **PAIN POINT — PP-004:** No source could identify where evidence of the Corporate Controller's approval of the payment proposal is retained, although the standard operating procedure requires such evidence.
> - **Impact:** The principal preventive control over the run may not be evidenced in a form that can be produced to an auditor without reconstruction from email.
> - **Severity:** High

> **PAIN POINT — PP-005:** The criteria by which the Accounts Payable Manager removes lines from the proposed payment list are undocumented, and removals are not recorded.
> - **Impact:** A payable can be excluded from a run without a recorded reason, and the proposal the Corporate Controller approves cannot be reconciled to the population the system originally selected. (TBD — no source quantifies how often lines are removed.)
> - **Severity:** Medium

> **PAIN POINT — PP-006:** The Company continues to issue roughly thirty checks per week, requiring MICR print, physical stock and signature plate custody, and a positive pay exception cycle, alongside the ACH run.
> - **Impact:** A parallel disbursement channel carries its own custody and exception-handling burden for a small share of payment volume; the Accounts Payable Manager described continuing to cut checks as an unwelcome carry-over.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Introduce an independent release at the bank — for example, releasing the ACH file under the Treasury Analyst's or the Chief Financial Officer's entitlement whenever the Corporate Controller has approved the proposal in NetSuite — so that approval of the run and execution of the payment sit with different individuals by design rather than by availability.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish and publish a single payment run calendar, confirmed against what is actually performed, with the proposal build, the Corporate Controller's approval and the bank release on separate days, and reissue the standard operating procedure disbursement section against it.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Obtain the Chase Connect entitlement matrix, confirm the configured approval rules for the ACH service, and — where the intent is dual release on every batch — remove the dollar floor from the entitlement so that the control is enforced by the bank rather than by practice.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-004:** Define a single retained artefact of proposal approval — the approved export stored in a designated location, or an approval record captured on the run in NetSuite — and hold it with the payment register so the control is evidenced from one place.
> - **Addresses:** PP-004

> **IMPROVEMENT OPPORTUNITY — IO-005:** Document the criteria for excluding a line from the proposal and record removals against the approved run, so that the difference between the system-selected population and the approved population is explained on its face.
> - **Addresses:** PP-005

> **IMPROVEMENT OPPORTUNITY — IO-006:** Assess migration of the remaining check population to ACH — through a supplier payment-method campaign using the banking details already held in the vendor master — to retire the MICR print, stock and plate custody burden and reduce the positive pay exception population.
> - **Addresses:** PP-006

```consult-meta
systems: [netsuite, chase-connect]
roles:   [ap-manager, corporate-controller, treasury-analyst, assistant-controller, cfo, supplier]
```
