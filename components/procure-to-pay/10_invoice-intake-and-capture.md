## Invoice Intake, Imaging and OCR Capture

<!-- scope note: covers variants — Electronic (AP Inbox) intake; Paper intake and scanning. Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Scope

This procedure covers the receipt of third-party supplier invoices through both
intake channels — electronic delivery to the AP Inbox and physical delivery to the
Company post office box — together with date-stamping, scanning, OCR capture of
header data, manual keying of low-confidence documents, and the creation of a
pending Bill in NetSuite. It ends at the point a pending Bill exists in NetSuite
with the invoice image attached; entry, coding, matching and approval of that Bill
are covered by [[po-invoice-entry-and-three-way-match]] and
[[non-po-invoice-entry-and-approval]]. Employee expense reimbursements, payroll
disbursements and intercompany settlements are excluded, as are corporate card
statements. Supplier records used to identify the invoicing party are established
by [[new-vendor-onboarding]] and maintained by [[vendor-master-data-maintenance]].
(SRC-001, SRC-006)

### At a Glance

| Field | Value |
|---|---|
| Trigger | Arrival of a supplier invoice at the AP Inbox or the Company post office box |
| Frequency | Continuous; paper is scanned within one business day of receipt, and the AP Inbox is triaged each morning |
| Preparer | Accounts Payable Clerk (inbox triage, scanning, first-pass validation keying) |
| Reviewer | Senior Accounts Payable Specialist (validation queue keying) |
| Systems | Ephesoft (capture, default system for this procedure); AP Inbox; NetSuite |
| Key inputs | Supplier invoice, received by email or in physical form |
| Key outputs | Captured invoice image and header data; pending Bill in NetSuite with image attached |

Volume is understood to be roughly 4,800 invoices per month, of which approximately
90% or more arrive electronically and 40–50 pieces per week arrive as paper; the
monthly figure is an unvalidated recollection rather than a system report (SRC-005).

### Before You Start

- **Supplier invoice (electronic)** — delivered by the supplier to the AP Inbox as
  directed by the purchase order terms and conditions; legible image or attachment.
- **Supplier invoice (paper)** — delivered to the Company post office box at
  Belmont Ridge; date-stamped on receipt and not yet scanned.
- **Supplier master record** — [[vendor-master-data-maintenance]]; active, so that
  the captured supplier name resolves to a payable vendor.
- **Purchase order reference** — [[po-issuance-and-change-orders]]; present on the
  face of the invoice where the purchase is PO-backed, so that capture can extract it.

### Procedure

#### Step 1: Triage the AP Inbox

The shared AP Inbox is triaged each morning and incoming invoice attachments are
released into Ephesoft for capture. Supplier remittance instructions and purchase
order terms and conditions direct suppliers to this mailbox, and the large majority
of invoice volume arrives this way. (SRC-001, SRC-006)

- **System / Tool:** AP Inbox (shared Outlook mailbox `ap-invoices@`)

> **SCREENSHOT PLACEHOLDER — SC-01:** The AP Inbox triage view, showing how received invoice mail is separated from vendor correspondence and status enquiries.

#### Step 2: Date-stamp and scan paper invoices

- **Condition:** the invoice was received in physical form at the Company post office box

Physical invoices are date-stamped on receipt and scanned into Ephesoft not later
than one business day following receipt, after which they follow the same capture
flow as electronically received invoices. (SRC-001, SRC-006)

- **System / Tool:** paper / desktop scanner (departure from the electronic flow)
- **Evidence Required:** the receipt date stamp on the scanned image

> **VALIDATION REQUIRED — GAP-01:** The retention and disposal treatment of the original paper invoice after scanning is not established.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 3: Extract invoice header data

Every invoice image, whether emailed or scanned, is processed through Ephesoft for
extraction of header data. Extraction is generally reliable where the purchase order
reference appears in a conventional position on the invoice face, and unreliable
where the supplier embeds it in body text. (SRC-001, SRC-006)

- **Fields / Parameters:** supplier name; supplier invoice number; invoice date;
  invoice total; currency; purchase order reference

#### Step 4: Key the document in the manual validation queue

- **Condition:** the extraction confidence score falls below the configured threshold

Documents below the confidence threshold are routed to the manual validation queue
and the header fields are keyed by hand. First-pass keying is performed each morning
by the Accounts Payable Clerk; the balance is worked by the Senior Accounts Payable
Specialist. (SRC-001, SRC-006)

- **Expected Result:** the document carries complete, human-verified header data and
  re-enters the capture flow

> **VALIDATION REQUIRED — GAP-02:** The Ephesoft extraction confidence threshold is unconfirmed — see [[GAP-02 — OCR CONFIDENCE THRESHOLD]].
> - **Note:** Do not operate to a stated confidence percentage; the configured value must be read from Ephesoft before it is documented.
> - **Detail:** §4.4 of the prior SOP requires routing to manual validation below ninety percent (90%). The Accounts Payable Manager recalls the threshold as "seventy-five percent, don't quote me" and expressly declined to confirm it. The Ephesoft configuration has not been pulled, and no interviewee could point to it. Resolution requires the Ephesoft configuration extract. (SRC-001, SRC-005, SRC-006)
> - **Nature:** conflict
> - **Owner to confirm:** IT Manager

> **SCREENSHOT PLACEHOLDER — SC-02:** The Ephesoft manual validation queue, showing the extracted-versus-keyed header fields and the confidence indicator.

#### Step 5: Create the pending Bill in NetSuite

Captured invoices are pushed from Ephesoft into NetSuite, where each creates a Bill
in a pending state with the invoice image attached to the transaction record. Pending
Bills are worked from the "AP - Bills Pending Review" saved search by the entry
procedures. (SRC-001, SRC-006)

- **System / Tool:** NetSuite (departure from Ephesoft)
- **Expected Result:** a pending Bill exists in NetSuite carrying the captured header
  data and the invoice image, available to
  [[po-invoice-entry-and-three-way-match]] or
  [[non-po-invoice-entry-and-approval]]

### Outputs & Evidence

- **Captured invoice image** — attached to the resulting NetSuite Bill and retained
  for not less than seven years (SRC-005, SRC-006).
- **Pending Bill in NetSuite** — carries extracted or keyed header data; consumed
  downstream by the PO and non-PO entry procedures.
- **Not retained:** no record is kept of documents rejected or re-routed at triage,
  and no log of validation-queue corrections is retained, so the accuracy of OCR
  extraction cannot be measured from the current-state evidence (SRC-001, SRC-005).

### Key Controls

> **CONTROL — CTRL-001:** Physical invoices are date-stamped on receipt and scanned into the capture application within one business day, establishing the receipt date and bringing paper into the same capture flow as electronic invoices.
> - **Type:** Preventive
> - **Frequency:** Each paper receipt
> - **Owner:** Accounts Payable Clerk

> **CONTROL — CTRL-002:** Documents whose extraction confidence falls below the configured threshold are routed to a manual validation queue and keyed by hand rather than passed through unverified.
> - **Type:** Detective
> - **Frequency:** Each document captured
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-003:** The original invoice image is retained as an attachment to the resulting payable transaction record for not less than seven years.
> - **Type:** Preventive
> - **Frequency:** Each invoice captured
> - **Owner:** Accounts Payable Manager

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Purchase order reference extraction is unreliable where the supplier prints the PO number inside body text rather than in a conventional position on the invoice face.
> - **Impact:** Affected invoices drop to the manual validation queue for hand-keying, consuming Accounts Payable Clerk and Senior Accounts Payable Specialist time daily. (SRC-001)
> - **Severity:** Medium

> **PAIN POINT — PP-002:** Suppliers have no means of checking invoice or payment status themselves, and telephone the Accounts Payable team instead.
> - **Impact:** Approximately forty status calls per week are absorbed by the Accounts Payable Clerk who also owns inbox triage and scanning. (SRC-001, SRC-005)
> - **Severity:** Medium

> **PAIN POINT — PP-003:** A material share of invoice volume still arrives as paper at the post office box despite the purchase order terms directing suppliers to the AP Inbox.
> - **Impact:** Forty to fifty pieces per week require manual handling, date-stamping and scanning before capture can begin, adding at least one business day to intake. (SRC-001, SRC-006)
> - **Severity:** Low

> **IMPROVEMENT OPPORTUNITY — IO-001:** Introduce an accounts payable automation layer with improved OCR extraction, so that purchase order references are recognized reliably regardless of placement on the invoice face.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Provide supplier self-service visibility of invoice and payment status through a vendor portal, removing routine status enquiries from the Accounts Payable team.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Enforce the electronic delivery requirement already stated in the purchase order terms through supplier outreach, reducing residual paper intake.
> - **Addresses:** PP-003

```consult-meta
systems: [ephesoft, ap-inbox, netsuite]
roles:   [ap-clerk, senior-ap-specialist, ap-manager, it-manager]
```
