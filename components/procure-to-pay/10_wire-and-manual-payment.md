## Wire Transfer and Manual Payment

<!-- scope note: covers variants — Wire transfer; Manual / emergency check. Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Scope

This procedure covers disbursements made outside the scheduled weekly cycle: wire
transfers, used principally for overseas suppliers, and manual or emergency
checks issued in exceptional circumstances. It covers the authorization of the
payment, its initiation and approval at the bank, and the evidence retained. It
explicitly excludes the scheduled ACH and check disbursement cycle
([[weekly-payment-run]]), the disposition of positive pay exception items
([[positive-pay-exception-handling]]), and any change to a supplier's remit-to
banking details ([[vendor-banking-change]]). Payroll disbursements, intercompany
settlements and employee expense reimbursements are outside the procedure
entirely (SRC-006). The payables being settled are established upstream in
[[po-invoice-entry-and-three-way-match]] and
[[non-po-invoice-entry-and-approval]].

### At a Glance

| Field | Value |
|---|---|
| Trigger | A payment that cannot wait for the scheduled weekly cycle — the qualifying circumstances are not documented (see GAP-01) |
| Frequency | Wires: approximately 8–10 per month. Manual / emergency checks: TBD — confirm with process owner (SRC-001, SRC-005) |
| Preparer | Treasury Analyst (wire entry); Accounts Payable Manager (manual check printing) |
| Reviewer | Corporate Controller; Chief Financial Officer (either may act as a portal approver) |
| Systems | Chase Connect (primary); NetSuite; Finance Shared Drive |
| Key inputs | Signed Wire Transfer Request Form; written Corporate Controller authorization (manual check); approved unpaid payable; verified remit-to banking details |
| Key outputs | Executed wire transfer; manual check; positive pay issue file for a manually issued check |

### Before You Start

- **Approved, unpaid payable** — [[po-invoice-entry-and-three-way-match]] or
  [[non-po-invoice-entry-and-approval]]; fully approved and not included in an
  open payment proposal.
- **Wire Transfer Request Form** — a PDF held on the Finance Shared Drive under
  Finance/Treasury/Forms; completed and signed by the requester and the
  requester's Functional Vice President before initiation (SRC-001, SRC-006).
- **Written Corporate Controller authorization** — required for a manual or
  emergency check; obtained before the check is printed (SRC-006).
- **Verified remit-to banking details** — [[vendor-master-data-maintenance]],
  with any change verified through [[vendor-banking-change]]; current on the
  vendor record.
- **Check stock and signature plate** — check stock in the locked drawer in the
  Accounts Payable area and the signature plate in the safe; drawn only for an
  authorized manual check (SRC-001).

### Procedure

#### Step 1: Establish that the payment must be made outside the weekly cycle

The payable is confirmed as approved and unpaid, and the decision is taken to
settle it outside the scheduled cycle rather than in the next
[[weekly-payment-run]]. The disbursement method — wire or manual check — is
determined at this point and governs the branch taken below.

> **VALIDATION REQUIRED — GAP-01:** The circumstances that qualify a payment for off-cycle disbursement are not documented.
> - **Note:** No qualifying criteria or approval gate for going off-cycle were described — confirm before relying on this step.
> - **Detail:** The prior SOP requires only that manual checks be issued "in exceptional circumstances" (§7.5 of the prior SOP) and sets no criteria for wires; no interviewee described how a payment is selected for off-cycle treatment or who makes that call (SRC-001, SRC-003, SRC-005, SRC-006).
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 2: Complete and sign the Wire Transfer Request Form

- **Condition:** the payment is being made by wire transfer

The Wire Transfer Request Form is retrieved, completed and signed by the
requester and the requester's Functional Vice President. The signed form is the
authorization on which the wire is initiated; a wire is not initiated without it
(SRC-001, SRC-006).

- **System / Tool:** Finance Shared Drive (Finance/Treasury/Forms)
- **Evidence Required:** the completed form bearing both signatures, retained as
  a PDF on the Finance Shared Drive

> **SCREENSHOT PLACEHOLDER — SC-01:** The Wire Transfer Request Form as held on the Finance Shared Drive, showing the requester and Functional Vice President signature blocks.

#### Step 3: Obtain written Corporate Controller authorization

- **Condition:** the payment is being made by manual or emergency check

Written authorization is obtained from the Corporate Controller before any
manual check is prepared (SRC-006).

- **Evidence Required:** the written authorization

> **VALIDATION REQUIRED — GAP-02:** The operation of the manual / emergency check process is unverified.
> - **Note:** This branch is documented from the prior SOP only — confirm the current practice, including form, frequency and retention, before relying on it.
> - **Detail:** §7.5 of the prior SOP requires Corporate Controller written authorization and secured custody of the signature plate. No interviewee described a manual or emergency check actually being issued, the frequency was not established, and the form the written authorization takes and where it is retained were not described (SRC-005). The prior SOP is version 3.0 with an effective date of 1 March 2023 and predates the current NetSuite configuration, and the Corporate Controller advised that documented practice and actual practice have drifted (SRC-003).
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 4: Key the wire into the banking portal

- **Condition:** the payment is being made by wire transfer

The Treasury Analyst keys the wire into Chase Connect from the signed request
form (SRC-001).

- **Fields / Parameters:** beneficiary and remit-to banking details as held on
  the vendor record; payment amount and currency per the signed request form

#### Step 5: Submit the wire ahead of the same-day cutoff

- **Condition:** same-day value is required

The wire is entered and fully approved in Chase Connect before the same-day
cutoff of 2:00 PM Eastern; wires completed after the cutoff carry a later value
date (SRC-001).

#### Step 6: Approve the wire in the banking portal

- **Condition:** the payment is being made by wire transfer

The wire is approved in Chase Connect by two approvers, drawn from the Corporate
Controller and the Chief Financial Officer. Dual authorization applies to every
wire with no dollar floor, and it is required in addition to the signed paper
form (SRC-001, SRC-003, SRC-006). The individual keying the wire is not an
approver.

- **Expected Result:** the wire is released to the beneficiary bank; a wire not
  carrying two portal approvals does not release

> **SCREENSHOT PLACEHOLDER — SC-02:** The Chase Connect wire approval view for a released wire, showing both approvals recorded against the transaction.

#### Step 7: Print the manual check

- **Condition:** the payment is being made by manual or emergency check

The check is printed on the MICR printer in the Accounts Payable area. Check
stock is drawn from the locked drawer and the signature plate is retrieved from
the safe; the safe combination is held only by the Accounts Payable Manager and
the Corporate Controller (SRC-001).

- **System / Tool:** MICR printer, Accounts Payable area

#### Step 8: Transmit the positive pay issue file

- **Condition:** the payment is being made by manual or emergency check

The issue file transmits to the bank from NetSuite on check print, on the same
date the check is issued (SRC-001, SRC-003, SRC-006). Any exception item arising
against the check is dispositioned under
[[positive-pay-exception-handling]].

- **System / Tool:** NetSuite

#### Step 9: Record and file the disbursement

The executed payment is recorded and the supporting authorization filed — the
signed request form on the Finance Shared Drive for a wire, the written
authorization for a manual check.

> **VALIDATION REQUIRED — GAP-03:** How an off-cycle disbursement is recorded against the payable in NetSuite is not established.
> - **Note:** The entry that clears the payable and the point at which it is made were not described — confirm before documenting this step as executable.
> - **Detail:** Wires are keyed directly in Chase Connect and manual checks are printed outside the scheduled cycle, so neither is created by the NetSuite payment proposal used for the weekly run. No interviewee described the corresponding NetSuite entry, its preparer, or its timing relative to bank release, and the handoff to the monthly bank reconciliation was described only in terms of the payment register (SRC-001, SRC-003, SRC-005).
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

### Outputs & Evidence

- **Executed wire transfer** — released in Chase Connect to the beneficiary bank.
- **Manual or emergency check** — issued to the payee.
- **Positive pay issue file** — transmitted to the bank on the date of check
  issue; feeds [[positive-pay-exception-handling]].
- **Evidence retained:** the signed Wire Transfer Request Form as a PDF on the
  Finance Shared Drive under Finance/Treasury/Forms; the dual approval recorded
  against the wire in Chase Connect.
- **Not retained / not established:** the retention period for the signed wire
  request form is not established, and no linkage between the filed form and the
  corresponding transaction record was described (see GAP-03). The form and
  content of the written Corporate Controller authorization for a manual check,
  and where it is filed, were not described by any interviewee (see GAP-02).

### Key Controls

> **CONTROL — CTRL-001:** A wire transfer is initiated only on a completed Wire Transfer Request Form signed by the requester and the requester's Functional Vice President.
> - **Type:** Preventive
> - **Frequency:** each wire
> - **Owner:** Treasury Analyst

> **CONTROL — CTRL-002:** Every wire transfer requires two approvers in Chase Connect, with no dollar floor and no exception.
> - **Type:** Preventive
> - **Frequency:** each wire
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-003:** The individual keying a wire in Chase Connect is not an individual approving it; entry and approval sit with separate portal users and tokens.
> - **Type:** Preventive
> - **Frequency:** each wire
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-004:** A manual or emergency check is issued only with the written authorization of the Corporate Controller.
> - **Type:** Preventive
> - **Frequency:** each occurrence
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-005:** Check stock is held in a locked drawer and the signature plate in the safe, with the combination held only by the Accounts Payable Manager and the Corporate Controller.
> - **Type:** Preventive
> - **Frequency:** continuous
> - **Owner:** Accounts Payable Manager

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The manual / emergency check branch exists in the prior SOP but could not be evidenced as operating.
> - **Note:** No one described a manual check being issued, and neither its frequency nor its authorization evidence could be established.
> - **Detail:** §7.5 of the prior SOP requires written Corporate Controller authorization, but no interviewee described the process operating, the frequency was never established, and the working notes record it as insufficient to document (SRC-005). A control that cannot be shown to operate, over a disbursement channel that bypasses the scheduled cycle and its proposal review, cannot be evidenced to the auditors who hold dual authorization on outbound funds in scope (SRC-003).
> - **Impact:** Off-cycle check disbursements cannot be evidenced as authorized.
> - **Severity:** Medium

> **PAIN POINT — PP-002:** Wire authorization evidence is a manually signed PDF held on the Finance Shared Drive, separate from both the banking portal and the accounting record.
> - **Impact:** Assembling the authorization trail for a wire requires retrieving evidence from a location outside the systems that hold the transaction.
> - **Severity:** Low

> **IMPROVEMENT OPPORTUNITY — IO-001:** Confirm whether manual / emergency checks are still issued; document the current authorization, evidence and retention practice, or formally retire the channel if it is no longer used.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Capture the wire request and its approvals in a system-based workflow so the authorization is held with the transaction record rather than as a separate signed PDF.
> - **Addresses:** PP-002

```consult-meta
systems: [chase-connect, netsuite, finance-shared-drive]
roles:   [treasury-analyst, corporate-controller, cfo, ap-manager, requester, functional-vp]
```
