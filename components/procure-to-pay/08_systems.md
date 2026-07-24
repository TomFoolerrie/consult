## Systems & Data Inputs

<!-- derived: systems; writer: python -->

_Canonical systems (from `_reference/systems.yaml`) with the procedures that use each, from `consult-meta` bindings._

| System / Tool | Role in Process | Related Procedures |
|---|---|---|
| AP Inbox | Shared Outlook mailbox to which suppliers are directed to send invoices per PO terms; receives roughly ninety percent of invoice volume. | [[#vendor-banking-change]], [[#invoice-intake-and-capture]] |
| Chase Connect | Bank portal used for ACH (NACHA) file upload and release, wire initiation and approval, positive pay exception review and disposition, and the ACH debit block filter list. | [[#weekly-payment-run]], [[#wire-and-manual-payment]], [[#positive-pay-exception-handling]] |
| Concur | Travel and expense system used for employee expense reports and the corporate card program. The client explicitly files this outside Procure to Pay under Travel & Expense; reimbursement runs through the payroll ACH file on a separate bank account. | — |
| Coupa | System of record for the supplier record from a sourcing standpoint; handles requisitions, PO issuance and change orders, supplier onboarding, and supplier self-registration via the Supplier Information Management portal. | [[#new-vendor-onboarding]], [[#vendor-banking-change]], [[#vendor-master-data-maintenance]], [[#requisition-and-approval]], [[#po-issuance-and-change-orders]], [[#confirming-po]], [[#goods-receipt]], [[#po-invoice-entry-and-three-way-match]] |
| Ephesoft | Document capture / OCR application that extracts invoice header data (vendor, invoice number, invoice date, total, PO reference) and routes low-confidence documents to a manual validation queue. | [[#invoice-intake-and-capture]] |
| Finance Shared Drive | Network file share holding the Wire Transfer Request Form PDF, the manual known-not-received accrual spreadsheet, and (per SOP) vendor statement reconciliation worksheets. | [[#vendor-statement-reconciliation]], [[#wire-and-manual-payment]] |
| IRS TIN Matching | Used during supplier diligence to verify that the W-9 legal name matches the taxpayer identification number. | [[#new-vendor-onboarding]] |
| NetSuite | System of record for the general ledger, the vendor master for payment purposes, item receipts, bills, the Pay Bills payment run, non-PO invoice approval routing, and bank reconciliation. | [[#new-vendor-onboarding]], [[#vendor-banking-change]], [[#vendor-master-data-maintenance]], [[#requisition-and-approval]], [[#po-issuance-and-change-orders]], [[#confirming-po]], [[#goods-receipt]], [[#return-to-vendor]], [[#invoice-intake-and-capture]], [[#po-invoice-entry-and-three-way-match]], [[#non-po-invoice-entry-and-approval]], [[#vendor-statement-reconciliation]], [[#weekly-payment-run]], [[#wire-and-manual-payment]], [[#positive-pay-exception-handling]] |
| OFAC SDN List | Sanctions screening performed as a manual lookup on the Treasury website during supplier diligence; the result is screenshotted and attached to the Coupa supplier record. | [[#new-vendor-onboarding]] |
