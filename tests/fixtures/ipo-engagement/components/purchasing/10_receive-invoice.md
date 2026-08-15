## Receive Invoice

### Scope

Receipt and capture of supplier invoices, from arrival in the AP Inbox (or
the scanner, for the residual paper) to a pending bill in NetSuite carrying
extracted header data. Owner: AP Clerk. Systems: AP Inbox, Ephesoft,
NetSuite. Runs daily, first thing. Hands off downstream to [[match-po]] for
PO-backed invoices and to [[approve-exceptions]] where capture itself fails.
Vendor selection and PO issuance sit upstream and outside this area.

### Inputs

- Supplier invoice image (PDF or scan) — from the supplier, arriving in the
  AP Inbox
- Purchase order reference printed on the invoice face — from the Buyer, via
  the invoice document itself

### Transformation

The AP Clerk triages the shared mailbox each morning, pushes every image
through Ephesoft, and lets the extraction land in NetSuite as a pending
bill. Anything the OCR scores below the confidence threshold, and anything
where the PO reference cannot be located on the invoice face, is keyed by
hand instead of trusted.

1. Work the AP Inbox front to back; scan any hard-copy invoices received
   that day so every invoice exists as an image.
2. Push the images through Ephesoft and let it extract supplier, invoice
   number, invoice date, total, currency and PO reference.
3. Review the Ephesoft validation queue: key by hand any header field the
   OCR could not read with confidence, then submit to NetSuite.
4. Confirm the pending bill exists in NetSuite and note the PO reference (or
   its absence) on the bill.

### Outputs

- Captured invoice header record (pending bill) — to [[match-po]] (NetSuite)
- Capture exception queue item — to [[approve-exceptions]] where the PO
  reference could not be read from the invoice face
- Invoice image, indexed — retained in Ephesoft as the source document

### Controls

> **CONTROL — CTRL-01:** NetSuite refuses a second bill carrying the same
> supplier identifier and supplier invoice number, preventing duplicate
> submission (SRC-001, SRC-002).

### Issues

> **VALIDATION REQUIRED — GAP-01:** The live Ephesoft extraction confidence
> threshold. The SOP specifies ninety percent (SRC-002); the AP Manager
> believed it to be approximately seventy-five percent and said the
> configuration has not been pulled since the implementation partner left
> (SRC-001). Pull the configuration.

> **PAIN POINT — PP-01:** "When it can't find the PO number on the face of
> the invoice it dumps the thing into a validation queue and somebody keys it
> by hand." — AP Manager (SRC-001).

```consult-meta
systems:
  - ap-inbox
  - ephesoft
  - netsuite
roles:
  - ap-clerk
  - ap-manager
  - supplier
  - buyer
```
