## Invoice Intake and Capture

<!-- scope note: covers variants — Emailed invoice to AP Inbox; Paper invoice scanned from PO box. Document the shared flow once; branch at the step(s) where the variants diverge. -->

### A. Process Overview

This procedure covers the receipt of supplier invoices through the two intake channels in use — the AP Inbox shared mailbox and the corporate post office box — and their capture into NetSuite as pending Bill records via the Ephesoft document capture application. It runs continuously each business day as invoices arrive, and is performed by the Accounts Payable Clerk (intake triage and scanning) and the Senior Accounts Payable Specialist (validation-queue keying), under the Accounts Payable Manager. It begins when a supplier transmits an invoice and ends when a Bill exists in NetSuite in a pending state with the invoice image attached; it excludes coding, matching and approval, which are performed in [[po-invoice-entry-and-three-way-match]] and [[non-po-invoice-entry-and-approval]]. Suppliers are directed to the AP Inbox by the terms recorded on the purchase order issued in [[po-issuance-and-change-orders]] (SRC-001, SRC-005).

### B. Quick Reference

- **Trigger:** A supplier invoice arrives in the AP Inbox or as paper at the corporate post office box.
- **Frequency:** Continuous / daily as invoices arrive.
- **Preparer:** Accounts Payable Clerk (intake triage, scanning, first-pass validation); Senior Accounts Payable Specialist (validation-queue keying).
- **Reviewer:** Accounts Payable Manager.
- **Primary systems / tools:** AP Inbox; Ephesoft; NetSuite.
- **Key outputs:** NetSuite Bill in a pending state with the original invoice image attached; Ephesoft validation-queue disposition.

### C. Pre-Requisites

- The supplier is an active record in the NetSuite vendor master (maintained in [[vendor-master-data-maintenance]]).
- Purchase order terms and conditions direct the supplier to submit invoices to the AP Inbox (SRC-006 §4.1).
- The Accounts Payable Clerk holds access to the AP Inbox shared mailbox and to the scanning equipment used for post office box mail.
- Ephesoft is configured with the extraction template and confidence threshold in force, and the Ephesoft-to-NetSuite push is operating.

### D. Inputs

- **Supplier invoice (electronic):** PDF or image received from the supplier at the AP Inbox — approximately ninety percent of invoice volume (SRC-001).
- **Supplier invoice (paper):** Hard-copy invoice received at the Belmont Ridge post office box — approximately forty to fifty pieces per week (SRC-001).
- **Purchase order reference:** Printed on the face of the invoice by the supplier where the purchase was made against a purchase order; used by Ephesoft for extraction.
- **NetSuite vendor master record:** Used to resolve the extracted supplier name to a vendor record.

### E. Step-by-Step Procedure

#### Step 1: Receive and triage electronic invoices in the AP Inbox

The Accounts Payable Clerk monitors the AP Inbox shared mailbox, to which suppliers are directed to send invoices under the purchase order terms. Approximately ninety percent of total invoice volume arrives through this channel.

- **System / Tool:** AP Inbox (shared Outlook mailbox `ap-invoices@`).
- **Expected Result:** Each inbound invoice attachment is identified and made available for release into Ephesoft.

> **VALIDATION REQUIRED — GAP-04:** Monthly invoice volume across both intake channels. The working notes record approximately 4,800 invoices per month as an unconfirmed figure that the Accounts Payable Manager did not validate; the number should be pulled from NetSuite before it is relied upon.
> - **Nature:** unsupported-assumption
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Receive and scan paper invoices (paper variant)

For the paper channel, the Accounts Payable Clerk collects mail from the Belmont Ridge post office box and scans the invoices so they enter the same capture flow as electronic invoices. The prior standard operating procedure requires that physical invoices be date-stamped on receipt and scanned within one business day; current practice as described in the interview does not confirm either the date-stamp or the one-business-day standard. See [[GAP-02 — PAPER INTAKE SLA]].

- **System / Tool:** Scanning equipment in the Accounts Payable area; Ephesoft.
- **Expected Result:** A scanned image of each paper invoice, released into Ephesoft on the same footing as an emailed invoice.

> **VALIDATION REQUIRED — GAP-02:** Whether paper invoices are date-stamped on receipt and scanned within one business day. SRC-006 §4.2 requires both; the Accounts Payable Manager described scanning without stating a date-stamp step or a turnaround standard, and SRC-006 is a 2023 document that predates the current NetSuite configuration.
> - **Nature:** conflict
> - **Owner to confirm:** Accounts Payable Manager

#### Step 3: Release documents into Ephesoft for header capture

All invoice images, whether emailed or scanned, are released into Ephesoft, which extracts the invoice header data and attempts to read the purchase order reference from the face of the invoice. Extraction of the purchase order number is reliable only where the supplier prints the reference in a standard position; a reference embedded in body paragraph text is not captured.

- **System / Tool:** Ephesoft.
- **Fields / Parameters:** Supplier name; supplier invoice number; invoice date; invoice total; purchase order reference. The prior standard operating procedure also requires currency — see [[GAP-03 — CAPTURED FIELD SET]].
- **Expected Result:** A captured document with header values and a per-document extraction confidence score.

> **VALIDATION REQUIRED — GAP-03:** Whether currency is among the fields Ephesoft currently extracts. SRC-006 §4.3 lists currency in the required minimum field set; the fields described in interview do not include it.
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager

#### Step 4: Work the Ephesoft validation queue

Documents whose extraction confidence score falls below the configured threshold are routed to the Ephesoft manual validation queue, where a person keys or corrects the header values. The Accounts Payable Clerk works a first pass through the queue each morning; the Senior Accounts Payable Specialist handles the balance. The threshold value in force is disputed across sources — see [[GAP-01 — CAPTURE CONFIDENCE THRESHOLD]].

- **System / Tool:** Ephesoft manual validation queue.
- **Expected Result:** Every low-confidence document has validated header values before it is pushed to NetSuite.
- **Evidence Required:** The validated document record in Ephesoft.

> **VALIDATION REQUIRED — GAP-01:** The extraction confidence threshold configured in Ephesoft. SRC-006 §4.4 states ninety percent; the Accounts Payable Manager recalled approximately seventy-five percent and expressly declined to be held to it. The configured value should be read from the Ephesoft configuration rather than resolved by preference.
> - **Nature:** conflict
> - **Owner to confirm:** IT Manager

> **SCREENSHOT PLACEHOLDER — SC-01:** The Ephesoft manual validation queue with at least one low-confidence document open, showing the extracted header fields and the confidence score — validates the queue routing and the fields subject to manual keying.

#### Step 5: Push the captured invoice to NetSuite as a pending Bill

Ephesoft pushes the captured invoice into NetSuite, where it is created as a Bill in a pending state with the original invoice image attached to the transaction record. The pending population is the starting point for [[po-invoice-entry-and-three-way-match]] and [[non-po-invoice-entry-and-approval]]; no coding, matching or approval occurs within this procedure.

- **System / Tool:** Ephesoft; NetSuite.
- **Expected Result:** A NetSuite Bill in a pending state, carrying the captured header values and the invoice image.
- **Evidence Required:** The invoice image retained as an attachment to the NetSuite Bill.

> **VALIDATION REQUIRED — GAP-05:** The role accountable for the seven-year retention of the invoice image, and whether any check confirms the image is in fact attached to the Bill. The seven-year period is stated in SRC-006 §4.5, a 2023 document; no source names an owner or a verification step.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

> **SCREENSHOT PLACEHOLDER — SC-02:** A NetSuite Bill in the pending state showing the captured header values and the attached invoice image — validates the handoff into invoice entry and the image retention point.

### F. Key Controls

> **CONTROL — CTRL-001:** Ephesoft routes any document whose extraction confidence score falls below the configured threshold to the manual validation queue, where header values are keyed or corrected by a person before the document is pushed to NetSuite.
> - **Type:** Preventive
> - **Frequency:** Each invoice captured
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-002:** The original invoice image is retained as an attachment to the resulting NetSuite payable transaction record for not less than seven years.
> - **Type:** Preventive
> - **Frequency:** Each invoice captured
> - **Owner:** TBD — confirm with process owner (see [[GAP-05 — IMAGE RETENTION OWNER]])

### G. Outputs

- **NetSuite Bill in a pending state:** Carries the captured header values and the attached invoice image; consumed by [[po-invoice-entry-and-three-way-match]] and [[non-po-invoice-entry-and-approval]].
- **Ephesoft validation-queue disposition:** Record of documents keyed or corrected manually.
- **Evidence retained:** The original invoice image, attached to the NetSuite Bill and retained for not less than seven years (SRC-006 §4.5, SRC-005).

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Ephesoft extracts the purchase order reference reliably only when the supplier prints it in a standard position on the invoice face; a reference appearing in body paragraph text is not captured.
> - **Impact:** The document drops into the manual validation queue and the purchase order reference is keyed by hand, adding effort at intake and delaying the downstream match.
> - **Severity:** Medium

> **PAIN POINT — PP-002:** Approximately forty to fifty paper invoices per week still arrive at the corporate post office box and must be collected and scanned by hand before they can enter capture.
> - **Impact:** Manual handling by the part-time Accounts Payable Clerk ahead of capture; the added elapsed time to capture was not quantified in the sources. (TBD)
> - **Severity:** Low

> **PAIN POINT — PP-003:** Suppliers place roughly forty status calls per week to Accounts Payable because they have no way to see whether their invoice has been received or scheduled for payment.
> - **Impact:** Recurring interruption of the Accounts Payable Clerk performing intake triage, and no self-service channel for suppliers.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Implement an accounts payable automation layer with stronger optical character recognition to raise straight-through capture rates, in particular for purchase order references not printed in a standard position.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Provide supplier self-service visibility into invoice receipt and payment status so suppliers can check status without calling Accounts Payable.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-003:** Run a supplier enablement effort against the remaining paper-submitting suppliers to move the residual post office box volume onto the AP Inbox channel already required by purchase order terms.
> - **Addresses:** PP-002

```consult-meta
systems: [ap-inbox, ephesoft, netsuite]
roles:   [ap-clerk, senior-ap-specialist, ap-manager, it-manager, supplier]
```

