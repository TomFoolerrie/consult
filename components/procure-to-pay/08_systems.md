## Systems & Data Inputs

<!-- derived: systems; writer: python -->

_Canonical systems (from `_reference/systems.yaml`) with the procedures that use each, from `consult-meta` bindings._

| System / Tool | Role in Process | Related Procedures |
|---|---|---|
| AP Inbox | Shared Outlook mailbox that receives the large majority of supplier invoices; stated on PO terms as the required delivery address. | [[#invoice-intake-and-capture]] |
| Chase Connect | Bank portal used for NACHA/ACH file upload and release, wire initiation and approval, positive pay exception disposition, and ACH debit block with an authorized-originator filter list. | [[#weekly-payment-run]], [[#wire-and-manual-payment]], [[#positive-pay-exception-handling]] |
| Coupa | System of record for supplier onboarding from a sourcing standpoint, requisitions, purchase orders and change orders. Includes a supplier self-registration (SIM) portal in which suppliers enter their own banking, W-9, insurance certificates and diversity classification. | [[#new-vendor-onboarding]], [[#vendor-banking-change]], [[#vendor-master-data-maintenance]], [[#requisition-and-approval]], [[#po-issuance-and-change-orders]], [[#confirming-po]], [[#blanket-po-management]], [[#goods-receipt]] |
| Ephesoft | OCR/document capture applied to all emailed and scanned invoice images; extracts supplier name, invoice number, invoice date, total, currency and PO reference, then pushes a pending Bill into NetSuite. Documents below the confidence threshold route to a manual validation queue. | [[#goods-receipt]], [[#invoice-intake-and-capture]] |
| Finance Shared Drive | Holds the wire transfer request form PDF, the manual known-not-received accrual spreadsheet, and (per SOP) statement reconciliation worksheets. | [[#vendor-statement-reconciliation]], [[#wire-and-manual-payment]] |
| NetSuite | General ledger, vendor master for payment purposes, item receipts, bill entry, three-way match, approval routing, Pay Bills / payment proposal, positive pay issue file and bank reconciliation. Duplicate invoice prevention via a unique constraint on supplier plus supplier invoice number. | [[#new-vendor-onboarding]], [[#vendor-banking-change]], [[#vendor-master-data-maintenance]], [[#po-issuance-and-change-orders]], [[#confirming-po]], [[#goods-receipt]], [[#return-to-vendor]], [[#invoice-intake-and-capture]], [[#po-invoice-entry-and-three-way-match]], [[#non-po-invoice-entry-and-approval]], [[#vendor-statement-reconciliation]], [[#weekly-payment-run]], [[#wire-and-manual-payment]], [[#positive-pay-exception-handling]] |
