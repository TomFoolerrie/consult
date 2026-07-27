## Weekly Payment Run (ACH and Check)

<!-- scope note: covers variants — ACH / NACHA batch; Check run and positive pay issue file. Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Scope

This procedure covers the recurring weekly disbursement cycle: selection of
approved payables into a payment proposal, review and approval of that proposal,
and execution of the resulting payments through both settlement channels — the
NACHA/ACH batch transmitted to and released at the bank, and the printed check
run with its accompanying positive pay issue file. It begins with bills already
approved and eligible for payment by
[[po-invoice-entry-and-three-way-match]] and
[[non-po-invoice-entry-and-approval]], and ends when the ACH file has been
released and the checks have been printed and their issue file transmitted.
Wire transfers and manual or emergency check issuance are excluded and follow
[[wire-and-manual-payment]]. Disposition of positive pay exception items
returned by the bank after the issue file is transmitted is excluded and follows
[[positive-pay-exception-handling]]; bank reconciliation of the resulting
disbursements is outside this procedure. (SRC-001, SRC-003, SRC-006)

### At a Glance

| Field | Value |
|---|---|
| Trigger | The weekly disbursement cycle; bills approved and coming due within the selection window |
| Frequency | Weekly, one disbursement cycle — the day-by-day calendar is unconfirmed (GAP-01) |
| Preparer | Accounts Payable Manager |
| Reviewer | Corporate Controller (approves the proposal in NetSuite; releases the ACH file at the bank, or Treasury Analyst in the Controller's absence) |
| Systems | NetSuite (Pay Bills, payment proposal, check print, positive pay issue file); Chase Connect for ACH upload and release |
| Key inputs | Approved bills eligible for payment; due dates and discount terms; supplier remit-to and payment method on the supplier master record |
| Key outputs | Approved payment proposal; NACHA/ACH file released at the bank; printed checks; positive pay issue file transmitted to the bank |

A normal weekly run is described as approximately 400 to 600 lines and $2.0m to
$2.5m, with roughly 30 checks; these are recollected operating figures rather
than a system report (SRC-001, SRC-005).

### Before You Start

- **Approved PO-backed bills** — [[po-invoice-entry-and-three-way-match]];
  matched and released from any "Match Exception - Hold" status, so they are
  eligible for selection.
- **Approved non-PO bills** — [[non-po-invoice-entry-and-approval]]; fully
  approved through the NetSuite approval routing, with general ledger coding
  complete.
- **Supplier master record** — [[vendor-master-data-maintenance]]; active, with
  the payment method and remit-to banking details current, since any banking
  change must have completed [[vendor-banking-change]] before the run selects
  the supplier.
- **Check stock and signature plate** — held in the accounts payable area; stock
  in a locked drawer and the signature plate in the safe, accessible for the
  check branch of the run.

### Procedure

#### Step 1: Build the payment proposal

The payment proposal is built in NetSuite from the population of approved,
unpaid bills. Selection is filtered on due date through the following Friday and
extended to include any bill carrying a supplier discount about to expire.

- **Navigation Path:** Transactions > Payables > Pay Bills
- **Fields / Parameters:** due date through the following Friday; bills with an
  expiring early-payment discount

> **VALIDATION REQUIRED — GAP-01:** The day-by-day payment run calendar is unconfirmed — three sources give three different schedules.
> - **Note:** Do not operate to a fixed weekday schedule until the calendar is confirmed; treat the cycle as weekly and confirm the build, review and release days with the process owner.
> - **Detail:** The Accounts Payable Manager describes building the proposal on Wednesday afternoon and generating and uploading the ACH file Thursday morning (SRC-001). The Corporate Controller describes proposal Tuesday, review Wednesday, funding and release Thursday, settlement Friday (SRC-003). §7.1 of the prior SOP states that the proposal is prepared on Monday and released on Wednesday (SRC-006). The Controller noted that if the Manager's account is correct, the proposal is reviewed and released on the same morning, which the Controller characterised as a finding in its own right, and asked that the actual calendar be checked with the team (SRC-003, SRC-005).
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite Pay Bills proposal screen showing the selection filters and the resulting proposed payment lines.

#### Step 2: Review the proposed payment lines and remove items not to be paid

The proposal is exported to Excel and reviewed line by line, and anything
identified as incorrect is pulled from the run before it is submitted for
approval.

- **Expected Result:** a proposed payment list that the preparer is prepared to
  put forward for approval

> **VALIDATION REQUIRED — GAP-02:** The retention location of the payment proposal Excel export and of the evidence of its approval is unestablished.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 3: Submit the proposal for review and approval

The proposal is submitted to the Corporate Controller, who reviews it and
approves the run. The preparer cannot release a proposal they have built; the
run does not proceed to file generation without this approval (see CTRL-001).

- **Expected Result:** an approved payment run, cleared for file generation and
  check print

#### Step 4: Generate the ACH file and upload it to the bank

- **Condition:** for the ACH portion of the approved run

The ACH payment file is generated in NACHA format from the approved run and
uploaded to the bank portal.

- **System / Tool:** Chase Connect (upload of the generated NACHA file)
- **Evidence Required:** upload confirmation in the bank portal for the batch

> **SCREENSHOT PLACEHOLDER — SC-02:** The Chase Connect upload confirmation for the weekly ACH batch, showing batch total and item count.

#### Step 5: Release the ACH batch at the bank

- **Condition:** for the ACH portion of the approved run

Release of the uploaded batch is performed by the Corporate Controller, or by
the Treasury Analyst when the Controller is unavailable. The uploading and
releasing individuals hold separate bank portal user IDs and separate tokens,
and the preparer holds no release entitlement (see CTRL-002).

- **System / Tool:** Chase Connect

> **VALIDATION REQUIRED — GAP-03:** Whether a second approver is required on every ACH batch or only above a dollar threshold is unconfirmed.
> - **Note:** Two accounts of the same control are in circulation; confirm the configured entitlement before describing the batch as dual-authorised without exception.
> - **Detail:** The Accounts Payable Manager states that a second approver is required on every batch with no dollar floor, dual authorisation having been applied to all batches following a 2022 phishing incident (SRC-001). The Corporate Controller states that the configured entitlement requires a second approver only above $100,000 and that a single release is permitted below that, adding that practice is stricter than entitlement because the weekly run always exceeds the threshold, and asking that the control be documented as configured with the stricter practice noted (SRC-003). §7.3 of the prior SOP requires only that the individual transmitting the file not be the individual releasing it, and sets no second-approver threshold (SRC-006). The working notes call for the bank entitlement report to be obtained to settle the point (SRC-005).
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

#### Step 6: Print the check run

- **Condition:** for the check portion of the approved run

Checks in the approved run are printed on the MICR printer in the accounts
payable area. Blank check stock is held in a locked drawer and the signature
plate is held in the safe, to which the Accounts Payable Manager and the
Corporate Controller hold the combination (see CTRL-003).

- **System / Tool:** MICR check printer in the accounts payable area

#### Step 7: Transmit the positive pay issue file

- **Condition:** for the check portion of the approved run

The positive pay issue file is transmitted from NetSuite to the bank on the same
day the checks are printed, covering the checks issued in that run. Exception
items returned by the bank against this file are dispositioned under
[[positive-pay-exception-handling]].

- **Expected Result:** the bank holds the issued-check register for the run, and
  any item presented that does not match it is returned as a positive pay
  exception

### Outputs & Evidence

- **Approved payment proposal** — the proposal reviewed and approved by the
  Corporate Controller before file generation; the prior SOP requires that
  evidence of approval be retained, but the location of the Excel export and of
  the approval evidence was not established (GAP-02) (SRC-005, SRC-006).
- **NACHA/ACH file and bank release record** — the uploaded batch and its
  release, recorded under separate bank portal user IDs in Chase Connect.
- **Printed checks and the positive pay issue file** — the physical checks
  issued in the run and the issue file transmitted to the bank the same day.
- **Payment register in NetSuite** — the record of payments applied against the
  bills selected in the run; it is subsequently reviewed post-hoc and is matched
  in the monthly bank reconciliation.
- **Not retained:** no documentation was described of the lines removed from the
  proposal during review, or of the reason for their removal.

### Key Controls

> **CONTROL — CTRL-001:** The Corporate Controller reviews and approves the payment proposal before any payment file is generated; the Accounts Payable Manager, who builds the proposal, cannot release it.
> - **Type:** Preventive
> - **Frequency:** Each run
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-002:** The individual uploading the ACH file to the bank portal is not the individual releasing it; upload and release are held under separate user IDs and tokens, and the Accounts Payable Manager holds no release entitlement.
> - **Type:** Preventive
> - **Frequency:** Each ACH batch
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-003:** Blank check stock is held in a locked drawer and the check signature plate in the safe, with the combination held only by the Accounts Payable Manager and the Corporate Controller.
> - **Type:** Preventive
> - **Frequency:** Continuous
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-004:** A positive pay issue file is transmitted to the bank on each date checks are issued, so that items not on the issued-check register are returned.
> - **Type:** Preventive
> - **Frequency:** Each check run
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-005:** Payment preparation, vendor master maintenance and payment release are held by different individuals, so that no one who can create or amend a supplier record can release a payment.
> - **Type:** Preventive
> - **Frequency:** Continuous
> - **Owner:** Corporate Controller

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The Corporate Controller both approves the payment run in NetSuite and releases the funds at the bank, so the two authorisation points in the cycle rest with one individual.
> - **Note:** The segregation across the run is three-way in name only at the approval and release steps; the auditors have challenged it twice.
> - **Detail:** The Controller describes the separation as "roughly" three-way — vendor master with the Accounts Payable Clerk, proposal build with the Accounts Payable Manager, approval and release with the Controller — and acknowledges that approving the run in the ERP and releasing it at the bank sits with the same person. External audit has pushed back on this twice. The compensating position offered is that the Controller approves a proposal they did not build and that the payment register is reviewed after the fact, which the Controller characterised as a compensating story and "not a great one" (SRC-003, SRC-005).
> - **Impact:** A single individual can carry an approved payment through to settlement; the mitigating review is detective and after the fact.
> - **Severity:** High

> **PAIN POINT — PP-002:** The documented disbursement procedure has drifted from practice — the prior SOP describes a Monday/Wednesday cycle that no one performing the run recognises, and no two accounts of the current calendar agree.
> - **Impact:** There is no authoritative statement of when the proposal is built, reviewed and released, which leaves the timing of the approval control unverifiable; if the proposal is reviewed and released the same morning, the review is compressed to the point the Controller identified it as a finding.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Approximately 30 checks a week are still printed, requiring physical check stock, a signature plate, a MICR printer and a positive pay exception loop for a small share of disbursement value.
> - **Impact:** Physical-instrument handling and its custody controls are sustained for a residual volume, and each run carries a same-week exception disposition deadline.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Separate approval of the run in NetSuite from release of the funds at the bank, so that no individual performs both, and retire the post-hoc register review as the primary mitigation.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Fix and publish the payment run calendar, with the proposal build, Controller review and bank release on separate days, and align the SOP to it.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Convert remaining check-paid suppliers to ACH, reducing residual check volume and the physical custody and positive pay handling that supports it.
> - **Addresses:** PP-003

```consult-meta
systems: [netsuite, chase-connect]
roles:   [ap-manager, corporate-controller, treasury-analyst, ap-clerk]
```
