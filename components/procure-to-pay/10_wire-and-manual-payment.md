## Wire and Manual Payment

<!-- scope note: covers variants — Wire transfer (signed request form, dual portal authorization); Manual / emergency check (Controller written authorization). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### A. Process Overview

This procedure covers outbound payments made outside the scheduled weekly disbursement cycle: wire transfers and manual (emergency) checks. Both variants share a common shape — a written, signed authorization is obtained before any payment instruction is created, preparation and authorization are performed by different people, and the executed payment is evidenced back to the authorizing document. Wire transfers are used principally for overseas tooling suppliers and run at roughly eight to ten per month; the manual / emergency check variant is described only in the 2023 Accounts Payable standard operating procedure and its current use is unconfirmed (SRC-001, SRC-005, SRC-006). The procedure begins when a requester determines that a payable cannot wait for, or is not suited to, the scheduled run in [[weekly-payment-run]], and ends when the payment is released at the bank and the supporting authorization is filed. It excludes the routine ACH and check disbursement cycle, positive pay exception disposition (see [[positive-pay-exception-handling]]), and any change to supplier remittance banking, which is performed under [[vendor-banking-change]] before a payment instruction is created.

### B. Quick Reference

- **Trigger:** A payment obligation that cannot be settled through the scheduled weekly disbursement cycle (e.g. an overseas supplier requiring wire settlement, or an exceptional circumstance warranting a manual check).
- **Frequency:** Wire transfers, approximately eight to ten per month, on demand. Manual / emergency checks — TBD — confirm with process owner.
- **Preparer:** Treasury Analyst (wire transfer). Manual / emergency check preparer — TBD — confirm with process owner.
- **Reviewer:** Corporate Controller or Chief Financial Officer (wire authorization in the bank portal); Corporate Controller (written authorization for a manual check).
- **Primary systems / tools:** Chase Connect; Finance Shared Drive (Wire Transfer Request Form); NetSuite.
- **Key outputs:** Executed wire transfer or manual check; signed Wire Transfer Request Form or written Controller authorization; payment recorded in NetSuite.

### C. Pre-Requisites

- The payable is recorded and, where a purchase order applies, has cleared the three-way match under [[po-invoice-entry-and-three-way-match]].
- The supplier record exists in NetSuite with current remittance detail; any change to remit-to banking has already been verified and approved under [[vendor-banking-change]].
- For a wire transfer, the current Wire Transfer Request Form is obtained from the Finance Shared Drive at `Finance/Treasury/Forms`.
- Preparation and authorization are performed by different individuals, each holding their own Chase Connect user ID and token.
- For a manual check, check stock is drawn from the locked drawer in the Accounts Payable room and the signature plate is held in the safe; the combination is held by the Accounts Payable Manager and the Corporate Controller.

### D. Inputs

- **Supplier invoice or payment demand:** the underlying payable — source: Supplier, via the AP Inbox and [[invoice-intake-and-capture]].
- **Wire Transfer Request Form (PDF):** blank form — source: Finance Shared Drive, `Finance/Treasury/Forms`; completed and signed by the Requester and the Functional Vice President.
- **Supplier remittance detail:** beneficiary bank information — source: NetSuite vendor master.
- **Written Corporate Controller authorization (manual check variant):** source: Corporate Controller — form and medium TBD — confirm with process owner.

### E. Step-by-Step Procedure

#### Step 1: Establish that an off-cycle payment is warranted

The Requester identifies a payable that cannot be settled through the scheduled weekly disbursement cycle and determines the payment method. Wire transfer is used for suppliers settled by wire, predominantly overseas tooling suppliers. A manual check is used only in exceptional circumstances.

- **Expected Result:** A decision on payment method, with the underlying payable identified.

> **VALIDATION REQUIRED — GAP-01:** The criteria by which a payment is routed off-cycle to a wire or manual check rather than held for the weekly run are not documented. Confirm the decision criteria and who makes the call.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 2: Obtain written authorization before any payment instruction is created

Both variants require a completed written authorization in hand before anything is keyed at the bank or printed.

**For a wire transfer:** the Requester completes the Wire Transfer Request Form and obtains signatures from the Requester and their Functional Vice President. The completed form is the initiation authority — no wire is initiated without it.

**For a manual / emergency check:** the written authorization of the Corporate Controller is obtained. This requirement is carried from the 2023 Accounts Payable standard operating procedure (SRC-006).

- **System / Tool:** Finance Shared Drive (wire transfer variant).
- **Navigation Path:** `Finance/Treasury/Forms` (wire transfer variant).
- **Evidence Required:** Signed Wire Transfer Request Form, or the Corporate Controller's written authorization for a manual check.

> **VALIDATION REQUIRED — GAP-02:** The manual / emergency check variant is documented in the 2023 standard operating procedure (section 7.5) but no interviewee described it being performed. Confirm whether manual checks are issued at all under current practice and, if so, the frequency, the preparer, the form the Corporate Controller's written authorization takes, and where that authorization is retained. Every step of this variant beyond the written-authorization requirement is currently unsupported.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 3: Prepare the payment instruction

**For a wire transfer:** the Treasury Analyst keys the wire in Chase Connect from the signed request form, entering the beneficiary and amount. Same-day value requires entry ahead of the 2:00 PM Eastern cutoff.

**For a manual / emergency check:** the check is prepared against the Corporate Controller's written authorization, printed on the MICR printer in the Accounts Payable room from stock held in the locked drawer, with the signature plate retrieved from the safe. The detailed preparation sequence for this variant is TBD — confirm with process owner.

> **VALIDATION REQUIRED — GAP-04:** The preparation sequence for a manual / emergency check — who prints it, from which NetSuite transaction, and how the signature plate is drawn and returned — was not described by any interviewee.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

- **System / Tool:** Chase Connect (wire transfer variant).
- **Fields / Parameters:** Beneficiary bank detail and payment amount per the signed Wire Transfer Request Form.
- **Expected Result:** Wire entered in Chase Connect and pending authorization.

> **SCREENSHOT PLACEHOLDER — SC-01:** Chase Connect wire entry screen showing the entered wire pending authorization — must validate that the preparer cannot self-authorize and that the beneficiary detail is captured from the request form.

#### Step 4: Authorize and release

**For a wire transfer:** the Corporate Controller or the Chief Financial Officer approves the wire in Chase Connect. Two approvers are required in the portal on every wire, with no dollar floor. Portal authorization sits on top of the signed paper form, so the wire carries both a documentary and a system authorization. Approvers hold separate Chase Connect user IDs and tokens from the preparer.

**For a manual / emergency check:** the check is signed under the signature-plate custody arrangement described in Step 3. Whether a second authorization is applied beyond the Corporate Controller's written authorization is TBD — confirm with process owner.

- **System / Tool:** Chase Connect (wire transfer variant).
- **Expected Result:** Wire released to the bank; same-day value achieved where released ahead of the 2:00 PM Eastern cutoff.
- **Evidence Required:** Chase Connect authorization record showing two distinct approvers.

> **SCREENSHOT PLACEHOLDER — SC-02:** Chase Connect approval history for a released wire — must validate two distinct approver user IDs and that neither is the preparer.

#### Step 5: Record and file

The payment is recorded against the payable in NetSuite and the signed Wire Transfer Request Form is retained on the Finance Shared Drive. A manual check issued outside the scheduled check run is reflected in the positive pay issue file transmitted at check print; issue-file and exception handling are performed under [[positive-pay-exception-handling]].

- **System / Tool:** NetSuite; Finance Shared Drive.
- **Evidence Required:** Signed Wire Transfer Request Form filed on the Finance Shared Drive.

> **VALIDATION REQUIRED — GAP-03:** The mechanism and timing by which an off-cycle wire or manual check is recorded against the payable in NetSuite were not described, nor was the retention location for the manual-check authorization. Confirm the recording step, its owner, and the retention path.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

### F. Key Controls

> **CONTROL — CTRL-001:** No wire transfer is initiated without a completed Wire Transfer Request Form signed by the Requester and the Functional Vice President.
> - **Type:** Preventive
> - **Frequency:** Each wire
> - **Owner:** Treasury Analyst

> **CONTROL — CTRL-002:** Every wire transfer requires two approvers in Chase Connect, with no dollar floor, and the approvers are separate from the individual who keyed the wire. This is stricter than the ACH batch control in [[weekly-payment-run]], which carries a dollar threshold.
> - **Type:** Preventive
> - **Frequency:** Each wire
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-003:** Manual checks are issued only in exceptional circumstances and only on the written authorization of the Corporate Controller.
> - **Type:** Preventive
> - **Frequency:** Each manual check
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-004:** Check stock is held in a locked drawer in the Accounts Payable room and the signature plate is held in the safe, with the combination restricted to the Accounts Payable Manager and the Corporate Controller.
> - **Type:** Preventive
> - **Frequency:** Continuous
> - **Owner:** Accounts Payable Manager

### G. Outputs

- **Executed wire transfer:** released to the supplier's beneficiary bank through Chase Connect.
- **Manual / emergency check:** issued to the supplier; reflected in the positive pay issue file at check print.
- **Signed Wire Transfer Request Form:** retained on the Finance Shared Drive.
- **Payment recorded in NetSuite** against the underlying payable.
- **Evidence retained:** Signed Wire Transfer Request Form (Finance Shared Drive); Chase Connect authorization record showing two approvers. Retention location for the Corporate Controller's written manual-check authorization is TBD — confirm with process owner.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The manual / emergency check variant exists in written policy but no member of the Accounts Payable, Treasury or Controllership groups described it being performed, and its frequency was not established. The Corporate Controller observed that the 2023 standard operating procedure and current practice have drifted substantially apart.
> - **Impact:** A disbursement channel with the highest inherent fraud risk in the cycle has no observable operating practice, no confirmed preparer and no confirmed evidence trail, so its effectiveness cannot be asserted to an auditor.
> - **Severity:** High

> **PAIN POINT — PP-002:** The wire authorization trail is split between a signed PDF form on the Finance Shared Drive and the approval record in Chase Connect, with no link between the two.
> - **Impact:** Demonstrating that a released wire matches the beneficiary and amount on its signed request form requires manual reassembly from two systems.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** The 2023 standard operating procedure remains the only written source for the manual check requirement and predates the NetSuite upgrade, and the Corporate Controller advised that it should be read but not relied upon.
> - **Impact:** Preparers have no current, authoritative written procedure for off-cycle disbursement.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Establish whether manual / emergency checks are still issued; if they are, define and document the full sequence — requester, authorization form, preparer, second authorization and retention — and if they are not, retire the provision from policy so the written control set matches operating practice.
> - **Addresses:** PP-001, PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Attach the signed Wire Transfer Request Form to the corresponding payment record in NetSuite, and record the Chase Connect wire reference on the form, so a single retrieval evidences authorization, instruction and release.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Refresh the disbursement sections of the Accounts Payable standard operating procedure to reflect current systems and practice, and put it on a periodic review cycle.
> - **Addresses:** PP-003

```consult-meta
systems: [chase-connect, netsuite, finance-shared-drive]
roles:   [treasury-analyst, corporate-controller, cfo, ap-manager, functional-vp, requester, supplier]
```
