## Key Dependencies

<!-- derived: dependencies; writer: agent -->

Each procedure's upstream and downstream connections, as stated in its process
overview. A dash indicates the overview states no connection in that direction.

| Procedure | Upstream (depends on) | Downstream (feeds) |
|---|---|---|
| `[[new-vendor-onboarding]]` | Supplier self-registration of remittance and compliance data through the Coupa Supplier Information Management portal | `[[requisition-and-approval]]`, `[[vendor-banking-change]]`, `[[vendor-master-data-maintenance]]` |
| `[[vendor-banking-change]]` | `[[new-vendor-onboarding]]`, supplier-initiated request to change the remit-to bank account | `[[wire-and-manual-payment]]` |
| `[[vendor-master-data-maintenance]]` | `[[new-vendor-onboarding]]`, nightly Coupa-to-NetSuite vendor synchronization | Periodic supplier master file review results reported to the Corporate Controller |
| `[[requisition-and-approval]]` | `[[new-vendor-onboarding]]` (supplier must be transactable in both systems) | `[[po-issuance-and-change-orders]]` |
| `[[po-issuance-and-change-orders]]` | `[[requisition-and-approval]]` (fully approved requisition) | `[[goods-receipt]]`, `[[po-invoice-entry-and-three-way-match]]`, `[[invoice-intake-and-capture]]` (purchase order terms direct suppliers to the AP Inbox) |
| `[[confirming-po]]` | `[[requisition-and-approval]]` and `[[po-issuance-and-change-orders]]` (exception path around both), supplier engaged directly without an approved purchase order and subsequently invoicing | `[[po-invoice-entry-and-three-way-match]]` |
| `[[goods-receipt]]` | `[[po-issuance-and-change-orders]]` (issued purchase order available in NetSuite), supplier delivery at the inbound docks, Plant 3 consumption-based automatic receipt arrangement with two steel suppliers | `[[po-invoice-entry-and-three-way-match]]`, `[[return-to-vendor]]` |
| `[[return-to-vendor]]` | `[[goods-receipt]]` (posted item receipt), supplier-issued return authorisation | Supplier credit intended to reduce the payable; how it is recorded and applied is not established |
| `[[invoice-intake-and-capture]]` | Supplier invoice transmission through the AP Inbox shared mailbox and the corporate post office box, Ephesoft document capture, `[[po-issuance-and-change-orders]]` | `[[po-invoice-entry-and-three-way-match]]`, `[[non-po-invoice-entry-and-approval]]` |
| `[[po-invoice-entry-and-three-way-match]]` | `[[invoice-intake-and-capture]]`, `[[po-issuance-and-change-orders]]`, `[[goods-receipt]]`, `[[confirming-po]]` | `[[weekly-payment-run]]`, `[[vendor-statement-reconciliation]]` |
| `[[non-po-invoice-entry-and-approval]]` | `[[invoice-intake-and-capture]]` (pending Bill with no purchase order reference), approval by the Cost Center Owner and, above defined breakpoints, more senior approvers outside Accounts Payable | `[[weekly-payment-run]]`, `[[vendor-statement-reconciliation]]` |
| `[[vendor-statement-reconciliation]]` | `[[po-invoice-entry-and-three-way-match]]`, `[[non-po-invoice-entry-and-approval]]`, `[[weekly-payment-run]]`, supplier statement of account, close calendar | — |
| `[[weekly-payment-run]]` | `[[po-invoice-entry-and-three-way-match]]`, `[[non-po-invoice-entry-and-approval]]`, Corporate Controller approval of the payment proposal | `[[positive-pay-exception-handling]]`, `[[vendor-statement-reconciliation]]`, Chase Connect ACH and check settlement |
| `[[wire-and-manual-payment]]` | `[[weekly-payment-run]]` (payable that cannot wait for the scheduled cycle), `[[vendor-banking-change]]` (any remittance banking change must precede the payment instruction), written signed authorization | Bank release and filing of the supporting authorization |
| `[[positive-pay-exception-handling]]` | `[[weekly-payment-run]]` (check issue file transmitted at check print), Chase Connect exception population against the Friday bank cutoff | Monthly bank reconciliation performed by the Assistant Controller's team |
