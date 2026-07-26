## Weekly Payment Run

<!-- scope note: covers variants — ACH payment run (NACHA file upload and release); Check run (MICR print and positive pay issue file). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### A. Process Overview

This procedure covers the Company's weekly disbursement cycle: the Accounts Payable Manager builds a payment proposal in NetSuite from bills released through [[po-invoice-entry-and-three-way-match]] and approved through [[non-po-invoice-entry-and-approval]], the Corporate Controller reviews and approves the proposal, and payment is executed in two variants — an ACH batch (NACHA file) uploaded to and released in Chase Connect, and a check run printed on the MICR printer with a positive pay issue file transmitted to the bank. Dual authorization on outbound funds is one of the three procure-to-pay controls in scope for the external audit (SRC-003). Wire transfers and manually issued checks are excluded — see [[wire-and-manual-payment]] — as is the disposition of positive pay exceptions, handled in [[positive-pay-exception-handling]].

### B. Quick Reference

- **Trigger:** The weekly disbursement cycle — the Company executes one payment run per week (§7.1 of the prior SOP, SRC-006; SRC-001)
- **Frequency:** Weekly; the day-by-day calendar is contested across the sources — see GAP-01 in E
- **Preparer:** Accounts Payable Manager (SRC-001; §7.2 of the prior SOP, SRC-006)
- **Reviewer:** Corporate Controller — reviews and approves the proposal prior to file generation (SRC-001, SRC-003)
- **Primary systems / tools:** NetSuite (Pay Bills, check print, positive pay issue file); Chase Connect (ACH upload and release); Excel for the proposal review
- **Key outputs:** Released ACH (NACHA) batch; printed checks; positive pay issue file; approved payment proposal

### C. Pre-Requisites

- Bills eligible for payment exist in NetSuite: PO bills matched and released through [[po-invoice-entry-and-three-way-match]], and non-PO bills carrying all required approvals from [[non-po-invoice-entry-and-approval]] (SRC-001).
- The Accounts Payable Manager holds NetSuite access to the Pay Bills function but holds no vendor edit rights and no bank release entitlement (SRC-003).
- Release entitlement in Chase Connect is held by the Corporate Controller and, as backup, the Treasury Analyst — under separate user IDs with separate tokens from the uploading user (SRC-001).
- For the check variant: blank check stock is available in the locked drawer in the AP room and the signature plate is in the safe, whose combination is held only by the Accounts Payable Manager and the Corporate Controller (SRC-001).

### D. Inputs

- **Open payables in NetSuite:** released PO bills and fully approved non-PO bills, selected by due date (SRC-001).
- **Early-payment discount data:** bills whose discount is about to expire are pulled into the proposal alongside those coming due (SRC-001).
- **Payment proposal export (Excel):** the working file the Accounts Payable Manager scrubs and the Corporate Controller reviews (SRC-001).

### E. Step-by-Step Procedure

#### Step 1: Build the payment proposal

The Accounts Payable Manager builds the payment proposal in NetSuite, filtering on bills with a due date through the following Friday plus anything with an early-payment discount about to expire. A normal week's proposal runs four to six hundred lines and roughly $2,000,000 to $2,500,000 (SRC-001, SRC-005).

The day on which each stage of the run occurs is contested across the sources [[GAP-01 — PAYMENT RUN CALENDAR]]: the Accounts Payable Manager builds the proposal Wednesday afternoon with file generation Thursday morning (SRC-001); the Corporate Controller describes proposal Tuesday, review Wednesday, funding and release Thursday, settlement Friday (SRC-003); and the prior SOP prescribes preparation Monday and release Wednesday (§7.1 of the prior SOP, SRC-006).

- **System / Tool:** NetSuite
- **Navigation Path:** Transactions > Payables > Pay Bills
- **Fields / Parameters:** Due date filter through the following Friday; bills with expiring early-payment discounts
- **Expected Result:** A proposed payment list of all bills due for the cycle

> **VALIDATION REQUIRED — GAP-01:** The payment-run calendar. The Accounts Payable Manager: proposal Wednesday afternoon, ACH file generated and uploaded Thursday morning (SRC-001). The Corporate Controller: proposal Tuesday, review Wednesday, funding and release Thursday, settlement Friday (SRC-003). The prior SOP: proposal prepared Monday, released Wednesday (§7.1 of the prior SOP, SRC-006). The Corporate Controller noted that if the Accounts Payable Manager's calendar is what operates, the Controller is reviewing the proposal the same morning it is released — "which if true is a finding" — and asked that the actual calendar be checked with the AP team (SRC-003, SRC-005). Confirm the operating calendar day by day.
> - **Nature:** conflict
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Scrub the proposal

The Accounts Payable Manager exports the proposal to Excel, reviews it, and pulls anything that looks wrong before it goes to review (SRC-001).

- **System / Tool:** NetSuite export; Excel
- **Expected Result:** A scrubbed proposal ready for the Corporate Controller's review
- **Evidence Required:** The proposal export — its retention location is unconfirmed [[GAP-02 — PROPOSAL APPROVAL EVIDENCE LOCATION]]

> **VALIDATION REQUIRED — GAP-02:** Where the payment proposal export and the evidence of the Corporate Controller's approval are retained. The prior SOP requires that evidence of approval be retained (§7.2 of the prior SOP, SRC-006) and the Corporate Controller confirmed it is retained, but no source stated where, and the question was not asked during fieldwork (SRC-005). Confirm the retention location and form of the approval evidence.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-01:** The payment proposal in NetSuite Pay Bills with the due-date filter applied, alongside the Excel export — validates the selection criteria and the review artifact.

#### Step 3: Corporate Controller review and approval

The Corporate Controller reviews and approves the run before any file is generated. The Accounts Payable Manager cannot release their own proposal (SRC-001; §7.2 of the prior SOP, SRC-006) (CTRL-001).

- **Expected Result:** An approved payment run, cleared for file generation

#### Step 4: ACH variant — generate, upload and release the NACHA file

The Accounts Payable Manager generates the ACH file — a NACHA file — from NetSuite and uploads it to Chase Connect. The uploader does not release: the Accounts Payable Manager holds no release entitlement, and the file is released by the Corporate Controller or, in the Controller's absence, the Treasury Analyst, under separate Chase Connect user IDs with separate tokens (SRC-001; §7.3 of the prior SOP, SRC-006) (CTRL-002).

Whether a second approver is required on every batch or only above a dollar floor is contested [[GAP-03 — ACH SECOND-APPROVER FLOOR]].

- **System / Tool:** NetSuite (file generation); Chase Connect (upload and release)
- **Fields / Parameters:** NACHA-format ACH file for the approved batch
- **Expected Result:** ACH batch uploaded by the Accounts Payable Manager and released by a separately entitled user

> **VALIDATION REQUIRED — GAP-03:** The ACH second-approver requirement. The Accounts Payable Manager states a second approver is required on every batch, without exception, a configuration in place since a 2022 phishing incident (SRC-001). The Corporate Controller states the entitlement as configured requires a second approver only above $100,000, with single release permitted below that — noting that practice is stricter only because the weekly batch always exceeds the floor, and asking that the control be documented as configured (SRC-003). The open question is whether "dual on every batch" is system-enforced or merely conventional. Obtain the Chase Connect entitlement report to establish the configured floor (SRC-005).
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-02:** The Chase Connect batch release screen showing the uploaded ACH batch pending release by a second user — validates the upload/release segregation and the approval configuration on the batch.

#### Step 5: Check variant — print checks and transmit the positive pay issue file

For payments made by check — roughly thirty per week — checks are printed on the MICR printer in the AP room on the same day as the ACH release. Blank check stock is held in a locked drawer; the signature plate is kept in the safe, whose combination is held only by the Accounts Payable Manager and the Corporate Controller (SRC-001) (CTRL-003). The positive pay issue file transmits to Chase from NetSuite at check print, the same day (SRC-001, SRC-003) (CTRL-004). Exception items returned by the bank are dispositioned under [[positive-pay-exception-handling]].

Manual checks outside this run are issued only in exceptional circumstances with the written authorization of the Corporate Controller (§7.5 of the prior SOP, SRC-006) and are covered in [[wire-and-manual-payment]].

- **System / Tool:** NetSuite (check print, positive pay issue file); MICR printer
- **Expected Result:** Checks printed and the positive pay issue file transmitted to the bank the same day
- **Evidence Required:** Positive pay issue file transmission

### F. Key Controls

> **CONTROL — CTRL-001:** The Corporate Controller reviews and approves the payment proposal before file generation; the Accounts Payable Manager, who builds the proposal, cannot release it (SRC-001, SRC-003; §7.2 of the prior SOP, SRC-006). Part of the dual-authorization control set in scope for the external audit (SRC-003).
> - **Type:** Preventive
> - **Frequency:** Each weekly run
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-002:** ACH upload and release are segregated: the individual transmitting the file is not the individual releasing it. The Accounts Payable Manager uploads with no release entitlement; the Corporate Controller (or the Treasury Analyst as backup) releases, under separate Chase Connect user IDs with separate tokens (SRC-001; §7.3 of the prior SOP, SRC-006). The second-approver floor on the batch is contested — see GAP-03 at Step 4 in E.
> - **Type:** Preventive
> - **Frequency:** Each ACH batch
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-003:** Physical safeguarding of check instruments: blank check stock in a locked drawer in the AP room; the signature plate in the safe, combination held only by the Accounts Payable Manager and the Corporate Controller (SRC-001; §7.5 of the prior SOP, SRC-006).
> - **Type:** Preventive
> - **Frequency:** Continuous
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-004:** A positive pay issue file transmits to the depository institution from NetSuite at check print, on each date checks are issued, enabling the bank to flag presented items that do not match (SRC-001, SRC-003; §7.6 of the prior SOP, SRC-006). Exception disposition is performed under [[positive-pay-exception-handling]].
> - **Type:** Detective
> - **Frequency:** Each check run
> - **Owner:** Accounts Payable Manager

### G. Outputs

- **Released ACH (NACHA) batch in Chase Connect:** the week's electronic disbursements (SRC-001).
- **Printed checks:** roughly thirty per week, mailed to suppliers (SRC-001).
- **Positive pay issue file:** transmitted to Chase at check print, consumed by [[positive-pay-exception-handling]] (SRC-001, SRC-003).
- **Payment register in NetSuite:** matched against the daily Chase bank feed in the monthly bank reconciliation performed by the Assistant Controller's team (SRC-003).
- **Evidence retained:** the approved payment proposal — evidence of approval is retained per the prior SOP (§7.2 of the prior SOP, SRC-006), but its location is unconfirmed (see GAP-02 at Step 2 in E).

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The Corporate Controller both approves the payment run in NetSuite and releases it at Chase Connect. External auditors have pushed back on this combination twice; the compensating argument — approval against a proposal the Controller did not build, plus a post-hoc review of the payment register — was characterized by the Controller as "a compensating story. It's not a great one" (SRC-003, SRC-005).
> - **Impact:** A single individual sits on both the ERP approval and the bank release leg of an audit-scoped dual-authorization control, weakening the three-way segregation across proposal, approval and release.
> - **Severity:** High

> **PAIN POINT — PP-002:** The operating payment-run calendar is not reliably known: the prior SOP, the Accounts Payable Manager and the Corporate Controller each gave a different weekly schedule, and if the AP Manager's version operates, the Controller's review and the release compress into the same morning — which the Controller flagged as a potential finding (SRC-001, SRC-003, SRC-005, SRC-006).
> - **Impact:** The review control may have less separation from release than designed, and the documented SOP does not reflect practice.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** The ACH dual-release control is understood differently by its own operators: the Accounts Payable Manager believes a second approver is required on every batch, while the Corporate Controller states the configured entitlement floor is $100,000, and no one has pulled the Chase Connect entitlement report (SRC-001, SRC-003, SRC-005).
> - **Impact:** A batch under $100,000 may be releasable by a single individual without anyone recognizing that the "dual on everything" understanding is convention rather than configuration; audit evidence for the control depends on the entitlement, not the practice.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Separate the ERP approval and bank release legs — for example by making the Treasury Analyst the routine releasing user in Chase Connect rather than the backup — so no single individual both approves the run and releases the funds (SRC-003).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Confirm the operating payment-run calendar and the Chase Connect entitlement configuration (second-approver floor), then update the SOP so the documented cycle, the configured control and practice agree (SRC-003, SRC-005).
> - **Addresses:** PP-002, PP-003

```consult-meta
systems: [netsuite, chase-connect, excel]
roles:   [ap-manager, corporate-controller, treasury-analyst, assistant-controller, supplier]
```
