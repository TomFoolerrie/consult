## Invoice Intake and Capture

### Scope

This procedure covers the receipt and digital capture of supplier invoices — from arrival by email or as paper mail, through automated header-data extraction, to the creation of a bill in a pending state in the accounting system. Suppliers are directed to the AP Inbox by the purchase order terms and conditions issued in [[po-issuance-and-change-orders]]. Captured bills flow downstream for entry and matching in [[po-invoice-entry-and-three-way-match]] and for coding and approval in [[non-po-invoice-entry-and-approval]]; this procedure ends once the pending bill exists in NetSuite. Payroll disbursements, intercompany settlements, and employee expense reimbursements (handled in Concur under a separate Travel & Expense function) are excluded (§1.2 of the prior SOP, SRC-006).

### At a Glance

| Field | Value |
|---|---|
| Trigger | Receipt of a supplier invoice — by email to the AP Inbox (ap-invoices@) or by paper mail to the Company's post office box (SRC-001) |
| Frequency | Daily (mailbox triaged each business day; paper mail scanned as received) |
| Preparer | Accounts Payable Clerk (mailbox triage, scanning, first-pass validation); Senior Accounts Payable Specialist (manual validation keying) |
| Reviewer | None at intake — captured bills are reviewed downstream during invoice entry |
| Systems | AP Inbox (ap-invoices@); Ephesoft; NetSuite |
| Key inputs | Supplier invoices, received by email or in paper form |
| Key outputs | NetSuite bill in a pending state with the invoice image attached, visible on the "AP - Bills Pending Review" saved search |

### Before You Start

- **Supplier invoices received by email** — sent by the Supplier to the AP Inbox (ap-invoices@); roughly ninety percent or more of invoice volume arrives this way (SRC-001).
- **Supplier invoices received in paper form** — sent by the Supplier to the Company's post office box; approximately forty to fifty pieces per week (SRC-001).
- **Purchase order terms and conditions** — issued in [[po-issuance-and-change-orders]]; must direct suppliers to submit invoices to the AP Inbox (§4.1 of the prior SOP, SRC-006).
- **AP Inbox and Ephesoft validation queue access** — held by the Accounts Payable Clerk and Senior Accounts Payable Specialist (SRC-001).
- **Scanning capability** — available to digitize paper invoices (SRC-001).
- **Ephesoft-to-NetSuite integration** — operating, so captured documents post as pending bills (SRC-001).

### Procedure

#### Step 1: Triage the AP Inbox

The AP Inbox (ap-invoices@) is triaged daily, separating supplier invoices from other correspondence. Roughly ninety percent or more of supplier invoices arrive through this mailbox, to which suppliers are directed by the purchase order terms and conditions (SRC-001; §4.1 of the prior SOP, SRC-006). Total volume is approximately 4,800 invoices per month, of which roughly a quarter are non-PO [[GAP-01 — MONTHLY INVOICE VOLUME]]. Invoice documents identified in triage are passed into Ephesoft for capture.

> **VALIDATION REQUIRED — GAP-01:** The monthly invoice volume (approximately 4,800, about one quarter non-PO) was stated by the Accounts Payable Manager but never validated against NetSuite (SRC-005). Confirm the actual volume from a NetSuite transaction count.
> - **Nature:** unsupported-assumption
> - **Owner to confirm:** Accounts Payable Manager

#### Step 2: Date-stamp and scan paper invoices

- **Condition:** the invoice is received in paper form at the Company's post office box

Invoices received in physical form — approximately forty to fifty pieces per week — are scanned into Ephesoft (SRC-001). The prior SOP requires each physical invoice to be date-stamped upon receipt and scanned not later than one business day following receipt (§4.2 of the prior SOP, SRC-006).

- **Evidence Required:** Date stamp on the original paper invoice (prior SOP requirement)

> **VALIDATION REQUIRED — GAP-02:** Fieldwork confirmed that the Accounts Payable Clerk scans incoming paper invoices, but did not verify that the date-stamp and one-business-day scanning standard in §4.2 of the prior SOP is followed in current practice. Confirm current-state practice against that standard.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 3: Automated header extraction in Ephesoft

All invoice images, whether received electronically or scanned, are processed through Ephesoft, which extracts the header data: supplier name, supplier invoice number, invoice date, invoice total, currency, and the purchase order reference where one appears on the face of the invoice (SRC-001; §4.3 of the prior SOP, SRC-006). Purchase order extraction is dependable when the supplier places the PO reference in a standard position and unreliable when it is embedded in body text (SRC-001). Documents scoring below the configured extraction confidence threshold [[GAP-03 — EXTRACTION CONFIDENCE THRESHOLD]] are routed to the manual validation queue rather than auto-posting (CTRL-001).

- **Fields / Parameters:** Supplier name; supplier invoice number; invoice date; invoice total; currency; purchase order reference
- **Expected Result:** Documents at or above the confidence threshold pass to NetSuite; documents below it appear in the validation queue

> **VALIDATION REQUIRED — GAP-03:** The extraction confidence threshold that routes documents to the manual validation queue is contested.
> - **Note:** The live threshold is unconfirmed — do not operate to a figure; see GAP-03.
> - **Detail:** The prior SOP states ninety percent (§4.4 of the prior SOP, SRC-006), while the Accounts Payable Manager recalled approximately seventy-five percent and asked not to be quoted on it (SRC-001). The Ephesoft configuration has never been pulled to confirm the live value (SRC-005). Obtain the configured threshold from Ephesoft.
> - **Nature:** conflict
> - **Owner to confirm:** IT Manager

#### Step 4: Key below-threshold documents in the validation queue

- **Condition:** the document scored below the extraction confidence threshold and routed to the manual validation queue

The Accounts Payable Clerk performs a first pass of the manual validation queue each morning; the Senior Accounts Payable Specialist works the remainder (SRC-001). Header data for each queued document is keyed by hand, after which the document proceeds to NetSuite in the same manner as auto-extracted documents.

> **SCREENSHOT PLACEHOLDER — SC-01:** The Ephesoft manual validation queue showing documents pending keying — validates that below-threshold documents route to the queue for human entry.

#### Step 5: Captured invoices post to NetSuite as pending bills

Ephesoft pushes each captured invoice into NetSuite as a bill in a pending state, with the original invoice image attached to the bill record (SRC-001; SRC-005). Pending bills appear on the "AP - Bills Pending Review" saved search, from which they are picked up for entry and matching in [[po-invoice-entry-and-three-way-match]] or for coding and approval in [[non-po-invoice-entry-and-approval]].

> **SCREENSHOT PLACEHOLDER — SC-02:** A captured bill in NetSuite in a pending state with the invoice image attached — validates the Ephesoft-to-NetSuite hand-off and the image attachment.

### Outputs & Evidence

- **Pending bill in NetSuite:** one bill in a pending state per captured invoice, consumed downstream through the "AP - Bills Pending Review" saved search by [[po-invoice-entry-and-three-way-match]] and [[non-po-invoice-entry-and-approval]].
- **Evidence retained:** the original invoice image, attached to the resulting NetSuite bill and retained for not less than seven years (§4.5 of the prior SOP, SRC-006; attachment practice confirmed in fieldwork, SRC-005).

### Key Controls

> **CONTROL — CTRL-001:** Documents whose Ephesoft extraction confidence score falls below the configured threshold are routed to the manual validation queue and keyed by hand rather than auto-posting, preventing low-confidence OCR data from entering NetSuite unreviewed. The live threshold value is unconfirmed — a validation gap is raised at Step 3 in E.
> - **Type:** Preventive
> - **Frequency:** Each document (continuous)
> - **Owner:** Senior Accounts Payable Specialist

> **CONTROL — CTRL-002:** Physical invoices received at the Company's post office box are date-stamped upon receipt and scanned to Ephesoft not later than one business day following receipt, ensuring paper invoices enter the same capture and retention path as electronic ones (§4.2 of the prior SOP, SRC-006). Current-state adherence is unverified — a validation gap is raised at Step 2 in E.
> - **Type:** Preventive
> - **Frequency:** Each paper receipt (daily mail cycle)
> - **Owner:** Accounts Payable Clerk

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Ephesoft purchase order extraction is unreliable when the supplier does not place the PO reference in a standard position on the invoice — for example, inside a paragraph of body text — and below-threshold documents fall to the manual validation queue for hand keying (SRC-001).
> - **Impact:** Recurring manual keying workload for the Accounts Payable Clerk and Senior Accounts Payable Specialist, and missed PO references that push otherwise matchable invoices toward manual handling downstream.
> - **Severity:** Medium

> **PAIN POINT — PP-002:** Suppliers have no self-service visibility into invoice or payment status and call the AP team instead — approximately forty status calls per week, largely handled by the part-time Accounts Payable Clerk (SRC-001; SRC-005).
> - **Impact:** Staff time absorbed answering roughly forty inbound calls per week, diverting the part-time Accounts Payable Clerk from mailbox triage and scanning.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Implement an AP automation layer with stronger OCR extraction and a supplier self-service portal for invoice and payment status, as proposed by the Accounts Payable Manager (SRC-001).
> - **Addresses:** PP-001, PP-002

```consult-meta
systems: [ap-inbox, ephesoft, netsuite, concur]
roles:   [ap-clerk, senior-ap-specialist, ap-manager, it-manager, supplier]
```
