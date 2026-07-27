## Weekly Payment Run

<!-- scope note: covers variants — ACH payment run (NACHA file upload and release); Check run (MICR print and positive pay issue file). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Process Overview

This procedure covers the Company's weekly disbursement cycle: the Accounts Payable Manager builds a payment proposal in NetSuite from bills released through [[po-invoice-entry-and-three-way-match]] and approved through [[non-po-invoice-entry-and-approval]], the Corporate Controller reviews and approves the proposal, and payment is executed in two variants — an ACH batch (NACHA file) uploaded to and released in Chase Connect, and a check run printed on the MICR printer with a positive pay issue file transmitted to the bank. Dual authorization on outbound funds is one of the three procure-to-pay controls in scope for the external audit (SRC-003). Wire transfers and manually issued checks are excluded — see [[wire-and-manual-payment]] — as is the disposition of positive pay exceptions, handled in [[positive-pay-exception-handling]].

### Quick Reference

- **Trigger:** The weekly disbursement cycle — the Company executes one payment run per week (§7.1 of the prior SOP, SRC-006; SRC-001)
- **Frequency:** Weekly — proposal built Wednesday afternoon, reviewed and released Thursday (SRC-001; calendar confirmed with the AP team during gap review)
- **Preparer:** Accounts Payable Manager (SRC-001; §7.2 of the prior SOP, SRC-006)
- **Reviewer:** Corporate Controller — reviews and approves the proposal prior to file generation (SRC-001, SRC-003)
- **Primary systems / tools:** NetSuite (Pay Bills, check print, positive pay issue file); Chase Connect (ACH upload and release); Excel for the proposal review
- **Key outputs:** Released ACH (NACHA) batch; printed checks; positive pay issue file; approved payment proposal

### Pre-Requisites

- Bills eligible for payment exist in NetSuite: PO bills matched and released through [[po-invoice-entry-and-three-way-match]], and non-PO bills carrying all required approvals from [[non-po-invoice-entry-and-approval]] (SRC-001).
- The Accounts Payable Manager holds NetSuite access to the Pay Bills function but holds no vendor edit rights and no bank release entitlement (SRC-003).
- Release entitlement in Chase Connect is held by the Corporate Controller and, as backup, the Treasury Analyst — under separate user IDs with separate tokens from the uploading user (SRC-001).
- For the check variant: blank check stock is available in the locked drawer in the AP room and the signature plate is in the safe, whose combination is held only by the Accounts Payable Manager and the Corporate Controller (SRC-001).

### Inputs

- **Open payables in NetSuite:** released PO bills and fully approved non-PO bills, selected by due date (SRC-001).
- **Early-payment discount data:** bills whose discount is about to expire are pulled into the proposal alongside those coming due (SRC-001).
- **Payment proposal export (Excel):** the working file the Accounts Payable Manager scrubs and the Corporate Controller reviews (SRC-001).

### Step-by-Step Procedure

#### Step 1: Build the payment proposal

The payment proposal is built in NetSuite on Wednesday afternoon, filtering on bills with a due date through the following Friday plus anything with an early-payment discount about to expire. A normal week's proposal runs four to six hundred lines and roughly $2,000,000 to $2,500,000 (SRC-001, SRC-005). The remainder of the run executes Thursday: the Corporate Controller's review Thursday morning, the ACH upload and release Thursday ahead of the bank's 2:00 pm cutoff, and check printing Thursday afternoon (SRC-001; calendar confirmed with the AP team during gap review).

- **Navigation Path:** Transactions > Payables > Pay Bills
- **Fields / Parameters:** Due date filter through the following Friday; bills with expiring early-payment discounts

#### Step 2: Scrub the proposal

The proposal is exported to Excel and scrubbed, and anything that looks wrong is pulled before it goes to review (SRC-001).

- **System / Tool:** Excel (proposal export)
- **Evidence Required:** The proposal export — its retention location is unconfirmed [[GAP-02 — PROPOSAL APPROVAL EVIDENCE LOCATION]]

> **VALIDATION REQUIRED — GAP-02:** Where the payment proposal export and the evidence of the Corporate Controller's approval are retained.
> - **Note:** Approval evidence is retained, but its location and form are unconfirmed — confirm the retention location before relying on it.
> - **Detail:** The prior SOP requires that evidence of approval be retained (§7.2 of the prior SOP, SRC-006) and the Corporate Controller confirmed it is retained, but no source stated where, and the question was not asked during fieldwork (SRC-005). Confirm the retention location and form of the approval evidence.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-01:** The payment proposal in NetSuite Pay Bills with the due-date filter applied, alongside the Excel export — validates the selection criteria and the review artifact.

#### Step 3: Corporate Controller review and approval

The Corporate Controller reviews and approves the run Thursday morning, before any file is generated. The Accounts Payable Manager cannot release their own proposal (SRC-001; §7.2 of the prior SOP, SRC-006) (CTRL-001).

#### Step 4: ACH variant — generate, upload and release the NACHA file

- **Condition:** ACH variant — payments disbursed electronically

Following the Thursday-morning approval, the ACH file — a NACHA file — is generated from NetSuite and uploaded to Chase Connect; the batch is released ahead of the bank's 2:00 pm cutoff. The uploader does not release: the Accounts Payable Manager holds no release entitlement, and the file is released by the Corporate Controller or, in the Controller's absence, the Treasury Analyst, under separate Chase Connect user IDs with separate tokens (SRC-001; §7.3 of the prior SOP, SRC-006) (CTRL-002).

Whether a second approver is required on every batch or only above a dollar floor is contested [[GAP-03 — ACH SECOND-APPROVER FLOOR]].

- **System / Tool:** Chase Connect (upload and release)
- **Fields / Parameters:** NACHA-format ACH file for the approved batch

> **VALIDATION REQUIRED — GAP-03:** The ACH second-approver requirement.
> - **Note:** Whether a second approver is system-enforced on every batch or only above a $100,000 floor is contested — do not document a floor until the Chase Connect entitlement report is obtained.
> - **Detail:** The Accounts Payable Manager states a second approver is required on every batch, without exception, a configuration in place since a 2022 phishing incident (SRC-001). The Corporate Controller states the entitlement as configured requires a second approver only above $100,000, with single release permitted below that — noting that practice is stricter only because the weekly batch always exceeds the floor, and asking that the control be documented as configured (SRC-003). The open question is whether "dual on every batch" is system-enforced or merely conventional. Obtain the Chase Connect entitlement report to establish the configured floor (SRC-005).
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

> **SCREENSHOT PLACEHOLDER — SC-02:** The Chase Connect batch release screen showing the uploaded ACH batch pending release by a second user — validates the upload/release segregation and the approval configuration on the batch.

#### Step 5: Check variant — print checks and transmit the positive pay issue file

- **Condition:** Check variant — payments disbursed by check

For payments made by check — roughly thirty per week — checks are printed on the MICR printer in the AP room on Thursday afternoon, the same day as the ACH release. Blank check stock is held in a locked drawer; the signature plate is kept in the safe, whose combination is held only by the Accounts Payable Manager and the Corporate Controller (SRC-001) (CTRL-003). The positive pay issue file transmits to Chase from NetSuite at check print, the same day (SRC-001, SRC-003) (CTRL-004). Exception items returned by the bank are dispositioned under [[positive-pay-exception-handling]].

Manual checks outside this run are issued only in exceptional circumstances with the written authorization of the Corporate Controller (§7.5 of the prior SOP, SRC-006) and are covered in [[wire-and-manual-payment]].

- **System / Tool:** MICR printer (check print)
- **Evidence Required:** Positive pay issue file transmission

### Key Controls

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

### Outputs

- **Released ACH (NACHA) batch in Chase Connect:** the week's electronic disbursements (SRC-001).
- **Printed checks:** roughly thirty per week, mailed to suppliers (SRC-001).
- **Positive pay issue file:** transmitted to Chase at check print, consumed by [[positive-pay-exception-handling]] (SRC-001, SRC-003).
- **Payment register in NetSuite:** matched against the daily Chase bank feed in the monthly bank reconciliation performed by the Assistant Controller's team (SRC-003).
- **Evidence retained:** the approved payment proposal — evidence of approval is retained per the prior SOP (§7.2 of the prior SOP, SRC-006), but its location is unconfirmed (see GAP-02 at Step 2 in E).

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The Corporate Controller both approves the payment run in NetSuite and releases it at Chase Connect. External auditors have pushed back on this combination twice; the compensating argument — approval against a proposal the Controller did not build, plus a post-hoc review of the payment register — was characterized by the Controller as "a compensating story. It's not a great one" (SRC-003, SRC-005).
> - **Impact:** A single individual sits on both the ERP approval and the bank release leg of an audit-scoped dual-authorization control, weakening the three-way segregation across proposal, approval and release.
> - **Severity:** High

> **PAIN POINT — PP-002:** The prior SOP's payment-run calendar (proposal Monday, release Wednesday — §7.1 of the prior SOP, SRC-006) predates the 2024 NetSuite upgrade and is obsolete; the documented procedure does not reflect the Wednesday/Thursday cycle actually operated (SRC-001; calendar confirmed with the AP team during gap review).
> - **Impact:** The governing documentation does not reflect practice, leaving the operating calendar dependent on institutional knowledge.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** The ACH dual-release control is understood differently by its own operators: the Accounts Payable Manager believes a second approver is required on every batch, while the Corporate Controller states the configured entitlement floor is $100,000, and no one has pulled the Chase Connect entitlement report (SRC-001, SRC-003, SRC-005).
> - **Impact:** A batch under $100,000 may be releasable by a single individual without anyone recognizing that the "dual on everything" understanding is convention rather than configuration; audit evidence for the control depends on the entitlement, not the practice.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Separate the ERP approval and bank release legs — for example by making the Treasury Analyst the routine releasing user in Chase Connect rather than the backup — so no single individual both approves the run and releases the funds (SRC-003).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Confirm the Chase Connect entitlement configuration (second-approver floor), then update the SOP so the documented cycle — now confirmed as the Wednesday/Thursday calendar — the configured control and practice agree (SRC-003, SRC-005).
> - **Addresses:** PP-002, PP-003

```consult-meta
systems: [netsuite, chase-connect, excel]
roles:   [ap-manager, corporate-controller, treasury-analyst, assistant-controller, supplier]
```
