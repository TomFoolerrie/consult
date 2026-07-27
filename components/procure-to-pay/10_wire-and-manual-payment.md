## Wire and Manual Payment

<!-- scope note: covers variants — Wire transfer; Manual / emergency check. Document the shared flow once; branch at the step(s) where the variants diverge. -->

### A. Process Overview

This procedure covers the two disbursement paths that run outside the weekly ACH and check cycle documented in [[weekly-payment-run]]: wire transfers and manual (emergency) checks. Wires — approximately eight to ten per month, chiefly to overseas tooling suppliers and one German bearing supplier — are initiated by the Treasury Analyst in Chase Connect on the strength of a signed Wire Transfer Request Form and are subject to dual authorization in the portal regardless of value (SRC-001, SRC-003). Manual checks are permitted only in exceptional circumstances with the written authorization of the Corporate Controller, per §7.5 of the prior AP SOP (SRC-006); no interviewee described one being issued, and the current-state practice is raised for validation in this procedure. Upstream, the procedure disburses against supplier obligations, paying to remittance details maintained through [[vendor-banking-change]]; downstream, any check issued feeds the positive pay cycle in [[positive-pay-exception-handling]], and all disbursements clear through the monthly bank reconciliation performed by the Assistant Controller (SRC-003). It excludes the routine weekly disbursement cycle and employee expense reimbursements, which pay through the payroll ACH file from a separate bank account (SRC-003).

### B. Quick Reference

- **Trigger:** Wire — receipt of a completed Wire Transfer Request Form signed by the requester and the requester's Functional Vice President (SRC-001; §7.4 of the prior AP SOP, SRC-006). Manual check — an exceptional circumstance authorized in writing by the Corporate Controller (§7.5 of the prior AP SOP, SRC-006).
- **Frequency:** Wires — approximately eight to ten per month (SRC-001, SRC-005). Manual checks — TBD; no occurrence was described during fieldwork (SRC-005).
- **Preparer:** Treasury Analyst (wire entry in Chase Connect) (SRC-001, SRC-005). Manual check — TBD; no preparer was identified (SRC-005; see GAP-03).
- **Reviewer:** Corporate Controller or Chief Financial Officer (wire approval in Chase Connect) (SRC-001); Corporate Controller (written authorization of manual checks) (SRC-006).
- **Primary systems / tools:** Chase Connect; Finance Shared Drive; NetSuite (positive pay issue file at check print).
- **Key outputs:** Executed wire transfer; issued manual check; positive pay issue file on each check issuance date; retained signed Wire Transfer Request Form.

### C. Pre-Requisites

- A supplier payment is to be made outside the weekly disbursement cycle in [[weekly-payment-run]] — in practice, wires are the standing payment method for overseas suppliers (SRC-001).
- The supplier exists on the NetSuite vendor master with remittance details maintained through [[vendor-banking-change]] (SRC-003).
- The Wire Transfer Request Form template is available on the Finance Shared Drive under Finance/Treasury/Forms (SRC-001, SRC-005).
- The Treasury Analyst holds wire-initiation entitlement in Chase Connect, and the Corporate Controller and Chief Financial Officer hold portal approval entitlements (SRC-001).
- For a manual check: the written authorization of the Corporate Controller has been obtained, and access to the blank check stock (locked drawer in the AP room) and the check signature plate (safe) is available (SRC-001; §7.5 of the prior AP SOP, SRC-006).

### D. Inputs

- **Completed, signed Wire Transfer Request Form:** PDF template held on the Finance Shared Drive under Finance/Treasury/Forms; signed by the requester and the requester's Functional Vice President (SRC-001; §7.4 of the prior AP SOP, SRC-006).
- **Beneficiary banking details for the wire:** the details keyed into Chase Connect; whether these are taken from the Wire Transfer Request Form or from the NetSuite vendor master record was not established (GAP-01).
- **Written Corporate Controller authorization (manual check):** required before any manual check is issued — source: Corporate Controller (§7.5 of the prior AP SOP, SRC-006).
- **Blank check stock and signature plate (manual check):** stock held in a locked drawer in the AP room; signature plate held in the safe (SRC-001, SRC-005).

### E. Step-by-Step Procedure

#### Step 1: Obtain documented authorization for the off-cycle disbursement

Both variants require documented authorization before any funds move.

For a **wire transfer**, the requester obtains the Wire Transfer Request Form — a PDF held on the Finance Shared Drive under Finance/Treasury/Forms — completes it, signs it, and obtains the countersignature of their Functional Vice President (SRC-001, SRC-005). A wire may be initiated only upon receipt of the completed and signed form (§7.4 of the prior AP SOP, SRC-006). The signed form is provided to the Treasury Analyst for initiation.

For a **manual / emergency check**, issuance is permitted only in exceptional circumstances and only with the written authorization of the Corporate Controller (§7.5 of the prior AP SOP, SRC-006). Proceed to Step 4.

- **System / Tool:** Finance Shared Drive (form template).
- **Evidence Required:** Wire Transfer Request Form bearing both signatures; written Corporate Controller authorization for a manual check.

> **SCREENSHOT PLACEHOLDER — SC-01:** The blank Wire Transfer Request Form template at its Finance/Treasury/Forms location on the Finance Shared Drive, showing the requester and Functional Vice President signature blocks.

#### Step 2: Key the wire in Chase Connect (wire variant)

- **Condition:** wire transfer variant

The wire is keyed in Chase Connect from the signed Wire Transfer Request Form (SRC-001). The cutoff for same-day execution is 2:00 PM Eastern (SRC-001). The source of the beneficiary banking details keyed into the portal was not described — [[GAP-01 — WIRE BENEFICIARY DETAILS]].

- **Evidence Required:** The completed, signed Wire Transfer Request Form supporting the entry.

> **VALIDATION REQUIRED — GAP-01:** Where the beneficiary banking details keyed into Chase Connect come from — the Wire Transfer Request Form itself or the supplier's NetSuite vendor master record (maintained through [[vendor-banking-change]]). No source describes this, and the answer determines whether the banking-change callback control protects wire disbursements.
> - **Nature:** unknown
> - **Owner to confirm:** Treasury Analyst

> **SCREENSHOT PLACEHOLDER — SC-02:** The Chase Connect wire initiation screen as completed by the Treasury Analyst, validating the entry fields and the pending-approval state after submission.

#### Step 3: Approve the wire in Chase Connect (wire variant)

- **Condition:** wire transfer variant

The wire is subject to dual authorization within Chase Connect without regard to value — there is no dollar floor and no exception (SRC-003; §7.4 of the prior AP SOP, SRC-006). The Accounts Payable Manager describes the Corporate Controller or the Chief Financial Officer approving the keyed wire in the portal (SRC-001). The exact approval configuration is contested — [[GAP-02 — WIRE APPROVER CONFIGURATION]].

- **Expected Result:** The wire is released for execution; same-day value where keyed and approved before the 2:00 PM Eastern cutoff (SRC-001).

> **VALIDATION REQUIRED — GAP-02:** The wire approval configuration in Chase Connect.
> - **Note:** Whether dual authorization means the initiator plus one approver or two approvers on top of the initiator is contested — do not represent the approval flow as confirmed; see GAP-02.
> - **Detail:** The Accounts Payable Manager describes the Treasury Analyst keying the wire and the Corporate Controller or Chief Financial Officer approving it — dual authorization read as initiator plus one approver (SRC-001). The Corporate Controller describes "two approvers" in Chase Connect on every wire (SRC-003), which may mean two approvers in addition to the initiator. §7.4 of the prior AP SOP requires dual authorization without defining the approver count (SRC-006). Obtain the Chase Connect entitlement report to confirm the configured approval flow (SRC-005).
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-03:** The Chase Connect approval screen for a pending wire, validating the required approval action and the enforced dual-authorization workflow.

#### Step 4: Prepare and sign the manual check (manual check variant)

- **Condition:** manual / emergency check variant

Manual checks are issued only in exceptional circumstances with the Corporate Controller's written authorization, per the trigger in Step 1 (§7.5 of the prior AP SOP, SRC-006). Blank check stock is held in a locked drawer in the AP room, and the check signature plate is kept in the safe, whose combination is held only by the Accounts Payable Manager and the Corporate Controller (SRC-001, SRC-005). Who prepares and prints a manual check, how it is signed and dispatched, and how the written authorization is evidenced were not described by any interviewee — no manual check issuance was recounted during fieldwork — [[GAP-03 — MANUAL CHECK PRACTICE]].

- **Evidence Required:** Written Corporate Controller authorization supporting the check.

> **VALIDATION REQUIRED — GAP-03:** The current-state manual / emergency check process. §7.5 of the prior AP SOP requires exceptional circumstances and written Corporate Controller authorization (SRC-006), but no interviewee described a manual check being issued; the preparer, the printing and signing mechanics, the frequency, and where the written authorization is retained are all unconfirmed (SRC-005). Confirm whether the path is still used and, if so, walk one end to end.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 5: Transmit the positive pay issue file (manual check variant)

- **Condition:** manual / emergency check variant — a manual check has been issued

A positive pay issue file must transmit to the depository institution on each date on which checks are issued — including a manual check issued outside the weekly run (§7.6 of the prior AP SOP, SRC-006). The issue file transmits to Chase Connect from NetSuite at check print (SRC-003). Exception items returned by the bank are dispositioned under [[positive-pay-exception-handling]].

- **System / Tool:** NetSuite (issue file transmission at check print).
- **Expected Result:** The manual check appears in the positive pay issue file for its issuance date.

#### Step 6: Record the disbursement and retain evidence

The signed Wire Transfer Request Form is retained on the Finance Shared Drive (SRC-005). How the wire or manual check is recorded in NetSuite — application against the supplier's open bill, and by whom — was not described by any source — [[GAP-04 — LEDGER RECORDING]]. Retention of the Corporate Controller's written authorization for a manual check was likewise not established (GAP-03). Downstream, the disbursement clears through the daily bank feed from Chase Connect into NetSuite and the monthly bank reconciliation performed by the Assistant Controller (SRC-003).

- **Evidence Required:** Signed Wire Transfer Request Form filed on the Finance Shared Drive.

> **VALIDATION REQUIRED — GAP-04:** How a wire or manual check is recorded in NetSuite against the supplier's open bill — the transaction type used, who enters it, and when. No interviewee described the ledger-recording side of an off-cycle disbursement; only the bank-side execution was covered (SRC-001, SRC-003).
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

### F. Key Controls

> **CONTROL — CTRL-001:** A wire is initiated only upon receipt of a completed Wire Transfer Request Form signed by the requester and the requester's Functional Vice President (SRC-001; §7.4 of the prior AP SOP, SRC-006).
> - **Type:** Preventive
> - **Frequency:** Each wire
> - **Owner:** Treasury Analyst

> **CONTROL — CTRL-002:** Dual authorization of every wire within Chase Connect, without regard to value — the initiating Treasury Analyst cannot alone release funds; portal approval by the Corporate Controller or Chief Financial Officer is required on top of the signed paper form (SRC-001, SRC-003; §7.4 of the prior AP SOP, SRC-006). The exact configured approver count is unconfirmed (GAP-02).
> - **Type:** Preventive
> - **Frequency:** Each wire
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-003:** Manual checks are issued only in exceptional circumstances and only with the written authorization of the Corporate Controller (§7.5 of the prior AP SOP, SRC-006). Whether this control currently operates could not be evidenced (GAP-03).
> - **Type:** Preventive
> - **Frequency:** Each manual check
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-004:** Physical safeguarding of check-issuance instruments — blank check stock in a locked drawer in the AP room, and the check signature plate in the safe with the combination held only by the Accounts Payable Manager and the Corporate Controller (SRC-001, SRC-005).
> - **Type:** Preventive
> - **Frequency:** Continuous
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-005:** A positive pay issue file transmits to the depository institution on each date on which checks are issued, so that any manual check is covered by the bank-side match; unmatched presentments return as exceptions handled under [[positive-pay-exception-handling]] (SRC-003; §7.6 of the prior AP SOP, SRC-006).
> - **Type:** Preventive
> - **Frequency:** Each check issuance date
> - **Owner:** Accounts Payable Manager

### G. Outputs

- **Executed wire transfer:** to the supplier's bank; same-day value where keyed and approved before the 2:00 PM Eastern cutoff (SRC-001).
- **Issued manual check:** to the supplier, in exceptional circumstances only (§7.5 of the prior AP SOP, SRC-006).
- **Positive pay issue file:** transmitted from NetSuite to the depository institution on each check issuance date — downstream to [[positive-pay-exception-handling]] (SRC-003, SRC-006).
- **Evidence retained:** the signed Wire Transfer Request Form, filed on the Finance Shared Drive (SRC-005); the Corporate Controller's written authorization for any manual check — retention location TBD — confirm with process owner (GAP-03).
- **Downstream:** disbursements flow into the daily Chase Connect bank feed to NetSuite and clear through the monthly bank reconciliation performed by the Assistant Controller (SRC-003).

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The manual / emergency check path exists in policy — exceptional circumstances, written Corporate Controller authorization (§7.5 of the prior AP SOP, SRC-006) — but no interviewee could describe it operating: no preparer, mechanics, frequency, or authorization evidence could be identified during fieldwork (SRC-005).
> - **Impact:** An off-cycle disbursement path of unknown frequency cannot currently be evidenced as controlled; if a manual check were issued today, the authorization control could not be demonstrated to an auditor from the record.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Formalize the manual / emergency check path or retire it. Confirm whether manual checks are still used; if retained, document the preparer, printing and signing mechanics, and a standard form and retention point for the Corporate Controller's written authorization — if not, route exceptional payments through the wire path, which already carries portal-enforced dual authorization (SRC-001, SRC-003).
> - **Addresses:** PP-001

```consult-meta
systems: [chase-connect, finance-shared-drive, netsuite]
roles:   [treasury-analyst, corporate-controller, cfo, ap-manager, functional-vp, requester, assistant-controller, supplier]
```
