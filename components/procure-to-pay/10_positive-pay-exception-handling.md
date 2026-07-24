## Positive Pay Exception Handling

### A. Process Overview

This procedure covers the disposition of positive pay exception items — checks presented
against the Company's operating account at Chase Connect that do not match the issued
check population the bank holds on file. The bank returns the mismatched items to the
Company for a pay or return decision, which the Accounts Payable Manager makes in Chase
Connect against a hard bank cutoff of 1:00 PM Friday; where no decision is recorded by the
cutoff the bank returns the item by default, a setting adopted deliberately by the
Corporate Controller. It is bank-initiated: it begins when the exception population appears
in the portal, and runs only in the weeks in which checks were issued. It consumes the
check issue file transmitted at check print under [[weekly-payment-run]] — that
transmission is performed in that procedure and is not repeated here — and the resulting
paid or returned items flow to the monthly bank reconciliation performed by the Assistant
Controller's team. Wires, ACH batches and the ACH debit block filter on the operating
account are outside this procedure. (SRC-001, SRC-003, SRC-005, SRC-006)

### B. Quick Reference

- **Trigger:** Exception items posted by the bank to Chase Connect following a check run — the bank has presented items that do not match the issue file.
- **Frequency:** Each week in which checks were issued; exceptions are available in the portal by 10:00 AM Friday and must be dispositioned by 1:00 PM Friday.
- **Preparer:** Accounts Payable Manager (reviews and dispositions each exception item).
- **Reviewer:** TBD — confirm with process owner. No source described a second review of the pay/return decisions (see the gap at Step 3).
- **Primary systems / tools:** Chase Connect (exception review and pay/return disposition); NetSuite (check register, used to identify the issued item behind an exception).
- **Key outputs:** A recorded pay or return decision on each exception item; returned items passing to the bank reconciliation population.

### C. Pre-Requisites

- A check run has been printed and the corresponding positive pay issue file transmitted to Chase Connect at print under [[weekly-payment-run]].
- The Accounts Payable Manager holds a Chase Connect user ID entitled to view and disposition positive pay exception items.
- The NetSuite check register for the run is available, so that a presented item can be traced to the check as issued.

### D. Inputs

- **Positive pay exception file:** Chase Connect — the items the bank could not match to the issue file, made available in the portal by 10:00 AM Friday (SRC-001, SRC-003).
- **Positive pay issue file as transmitted:** The issued-check population established at check print in [[weekly-payment-run]]; the baseline against which the bank matched.
- **NetSuite check register:** NetSuite — the record of checks issued in the run, used to identify the item behind an exception.
- **Reason code / mismatch detail per item:** TBD — confirm with process owner. No source described what the bank reports as the reason an item failed to match (serial number, amount, payee).

### E. Step-by-Step Procedure

#### Step 1: Retrieve the exception population from the bank

The Accounts Payable Manager retrieves the positive pay exception items in Chase Connect on
the morning following the check run. Exceptions are available in the portal by 10:00 AM
Friday. The exception window is therefore fixed against the day on which checks are printed,
and the payment run calendar is itself disputed across sources — see
[[GAP-01 — EXCEPTION WINDOW AGAINST RUN CALENDAR]].

- **System / Tool:** Chase Connect
- **Expected Result:** The list of items presented against the operating account that did not match the transmitted issue file is on screen and available for disposition.

> **VALIDATION REQUIRED — GAP-01:** Whether the 10:00 AM Friday availability and 1:00 PM Friday cutoff hold on every cycle. The Accounts Payable Manager describes the check run printing Thursday, with exceptions returned by 10:00 AM Friday and a 1:00 PM Friday decision deadline (SRC-001). The Corporate Controller describes exceptions returning "the next business morning" without naming a day, against a payment calendar the Controller states runs a day earlier than the Accounts Payable Manager's (SRC-003); the standard operating procedure fixes only "the deadline established by the depository institution" (SRC-006). The underlying payment run calendar is unresolved in [[weekly-payment-run]]. Confirm the bank's published exception availability and cutoff times, and the day of the week the cycle actually falls on.
> - **Nature:** conflict
> - **Owner to confirm:** Accounts Payable Manager

> **SCREENSHOT PLACEHOLDER — SC-01:** The Chase Connect positive pay exception screen showing the exception list and the displayed decision deadline, validating the population presented and the cutoff time.

#### Step 2: Review each exception item

The Accounts Payable Manager reviews each exception item against the check as issued,
referring to the NetSuite check register to identify the underlying check. No source
described the criteria applied in reaching a pay or return decision, or what is done when
an item cannot be identified within the window — see
[[GAP-02 — EXCEPTION REVIEW CRITERIA]].

- **System / Tool:** Chase Connect; NetSuite
- **Fields / Parameters:** TBD — confirm with process owner. The attributes compared between the presented item and the issued check were not described.
- **Expected Result:** Each exception item is identified as a validly issued check or as an item that should not be paid.

> **VALIDATION REQUIRED — GAP-02:** The criteria the Accounts Payable Manager applies in deciding to pay or return an exception item, including what is done when the presented item cannot be tied to a check in the NetSuite check register before the cutoff, and whether any item is escalated to the Corporate Controller before disposition. No source described the decision basis (SRC-001, SRC-003, SRC-005); the standard operating procedure requires only that items be dispositioned by the deadline (SRC-006).
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 3: Record the pay or return decision before the 1:00 PM cutoff

The Accounts Payable Manager records a pay or return decision on each exception item in
Chase Connect. The decision must be recorded by 1:00 PM Friday, the deadline established by
the bank (CTRL-001 in F). No source described a review or approval of the decisions
recorded, or evidence retained of the disposition — see
[[GAP-03 — DISPOSITION REVIEW AND EVIDENCE]].

- **System / Tool:** Chase Connect
- **Expected Result:** Every item in the exception population carries a recorded decision before the cutoff; items marked pay are honoured by the bank and items marked return are dishonoured.
- **Evidence Required:** TBD — confirm with process owner. No source identified a retained record of the exception population or the decisions taken on it.

> **VALIDATION REQUIRED — GAP-03:** Whether the pay/return decisions are reviewed by anyone other than the Accounts Payable Manager who records them, and what evidence of the exception population and its disposition is retained and where. No source described a reviewer or a retention location (SRC-001, SRC-003, SRC-005); the standard operating procedure assigns disposition to the Accounts Payable Manager and is silent on review and evidence (SRC-006).
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 4: Where the cutoff is missed — default return

Where no decision is recorded against an exception item by the 1:00 PM Friday cutoff, the
bank's default disposition applies and the item is returned unpaid (CTRL-002 in F). The
default was set to return deliberately by the Corporate Controller. The Accounts Payable
Manager reports the cutoff having been missed on one occasion. No source described what is
done after a default return occurs — whether the affected supplier is notified, whether the
check is voided and reissued in NetSuite, or whether the miss is reported — see
[[GAP-04 — DEFAULT RETURN REMEDIATION]].

- **System / Tool:** Chase Connect; NetSuite
- **Expected Result:** The item is returned unpaid by the bank; the payment to the supplier does not settle.

> **VALIDATION REQUIRED — GAP-04:** What is performed after an item is returned by default because the cutoff was missed — supplier notification, void and reissue of the check in NetSuite, and whether the occurrence is reported to the Corporate Controller. The Accounts Payable Manager confirmed the default is return and that the deadline has been missed once (SRC-001); the Corporate Controller confirmed the default setting but described no remediation path (SRC-003). No source described the downstream handling.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 5: Coverage when the Accounts Payable Manager is unavailable

Disposition is performed by the Accounts Payable Manager. No source identified a named
backup with the Chase Connect entitlement to disposition exception items when the Accounts
Payable Manager is absent on a Friday, nor any handover practice for planned absence — see
[[GAP-05 — BACKUP DECISION-MAKER]]. Against a same-morning bank cutoff and a default of
return, the absence of a confirmed alternate is a control exposure rather than a
documentation gap alone (PP-002 in H).

- **System / Tool:** Chase Connect
- **Expected Result:** TBD — confirm with process owner.

> **VALIDATION REQUIRED — GAP-05:** Who dispositions positive pay exceptions when the Accounts Payable Manager is unavailable, and whether that individual holds the Chase Connect entitlement to do so. Every source assigns disposition to the Accounts Payable Manager alone (SRC-001, SRC-003, SRC-005); the standard operating procedure names only the Accounts Payable Manager (SRC-006). No source named an alternate. Confirm against the Chase Connect entitlement matrix, which is also being obtained for the ACH release question in [[weekly-payment-run]].
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 6: Hand off to bank reconciliation

Paid and returned items settle against the operating account and form part of the
population matched to the NetSuite payment register in the monthly bank reconciliation
performed by the Assistant Controller's team.

- **System / Tool:** NetSuite; Chase Connect
- **Expected Result:** Disposition of the week's exception population is complete and the resulting items pass to bank reconciliation.

### F. Key Controls

> **CONTROL — CTRL-001:** Each positive pay exception item returned by the bank is reviewed and dispositioned pay or return by the Accounts Payable Manager in Chase Connect before the bank's 1:00 PM Friday decision cutoff, so that an item presented against the operating account which does not match the issued check population is not honoured without a decision.
> - **Type:** Detective
> - **Frequency:** Each week in which checks were issued
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-002:** The bank's default disposition on an exception item for which no decision is recorded by the cutoff is set to return, so that a mismatched item is dishonoured rather than paid where the decision window lapses. The setting was established deliberately by the Corporate Controller.
> - **Type:** Preventive
> - **Frequency:** Continuous (bank configuration)
> - **Owner:** Corporate Controller

### G. Outputs

- **Recorded pay/return decision per exception item:** Held in Chase Connect; determines whether the presented item is honoured against the operating account.
- **Returned items:** Items dishonoured by decision or by the default-return setting; the underlying disbursement does not settle.
- **Bank reconciliation population:** Paid and returned items feed the monthly reconciliation of the operating account to the NetSuite payment register performed by the Assistant Controller's team.
- **Evidence retained:** TBD — confirm with process owner. No source identified a retained record of the exception population or of the decisions taken (see the disposition evidence gap at Step 3).

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The pay/return decision on positive pay exceptions rests with a single individual, the Accounts Payable Manager, with no described second review and no identified retained evidence of the decisions taken.
> - **Impact:** A decision to honour an item that did not match the issued check population — the precise condition positive pay exists to detect — is neither independently reviewed nor demonstrably evidenced to an auditor.
> - **Severity:** High

> **PAIN POINT — PP-002:** No backup has been identified to disposition exceptions when the Accounts Payable Manager is unavailable, against a three-hour decision window and a same-day bank cutoff.
> - **Impact:** A Friday absence causes the entire week's exception population to be returned by default, dishonouring validly issued checks to suppliers with no one positioned to intervene.
> - **Severity:** High

> **PAIN POINT — PP-003:** The decision window is short — exceptions are available at 10:00 AM and the cutoff falls at 1:00 PM the same day — and the cutoff has been missed at least once.
> - **Impact:** A missed cutoff returns validly issued checks to suppliers unpaid. (TBD — no source described the supplier or reissue consequences of the one occurrence.)
> - **Severity:** Medium

> **PAIN POINT — PP-004:** The criteria applied in reaching a pay or return decision are undocumented, as is the handling of an item that cannot be traced to the NetSuite check register within the window.
> - **Impact:** The effectiveness of the control depends on undocumented individual judgment and cannot be tested or transferred to a successor or a backup.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Establish and entitle a named alternate — for example the Treasury Analyst, who already holds Chase Connect entitlements for the disbursement cycle — to disposition positive pay exceptions when the Accounts Payable Manager is unavailable, and confirm the entitlement in the Chase Connect matrix rather than by practice.
> - **Addresses:** PP-002, PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Document the pay/return decision criteria, including the treatment of an unidentifiable item and the point at which an exception is escalated to the Corporate Controller, so the control is testable and can be executed by a backup.
> - **Addresses:** PP-004, PP-001

> **IMPROVEMENT OPPORTUNITY — IO-003:** Retain the exception population and its recorded dispositions each cycle — an export of the Chase Connect exception screen held with the run's check register — and have the Corporate Controller review any item dispositioned as pay, so that honouring a mismatched item carries independent authorization and durable evidence.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-004:** Set a standing internal deadline ahead of the bank cutoff with a calendar reminder on the disposition owner and the alternate, and report any default return to the Corporate Controller, so a lapsed window is detected rather than discovered from a supplier call.
> - **Addresses:** PP-003

```consult-meta
systems: [chase-connect, netsuite]
roles:   [ap-manager, corporate-controller, assistant-controller, treasury-analyst, supplier]
```
