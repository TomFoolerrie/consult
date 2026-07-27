## Key Dependencies

<!-- derived: dependencies; writer: agent -->

Upstream and downstream relationships below are drawn from the scope statement of
each procedure. Procedures are referenced by link; anything outside this document
set is named in plain text.

| Procedure | Upstream (depends on) | Downstream (feeds) |
|---|---|---|
| `[[new-vendor-onboarding]]` | Requester's New Supplier Request; supplier self-registration in the supplier portal; sourcing diligence | `[[requisition-and-approval]]`, `[[po-issuance-and-change-orders]]`, `[[vendor-banking-change]]`, `[[vendor-master-data-maintenance]]`, `[[invoice-intake-and-capture]]`, `[[non-po-invoice-entry-and-approval]]` |
| `[[vendor-banking-change]]` | `[[new-vendor-onboarding]]`; supplier-initiated change request; contact already held on file for callback verification | `[[weekly-payment-run]]`, `[[wire-and-manual-payment]]` |
| `[[vendor-master-data-maintenance]]` | `[[new-vendor-onboarding]]`; nightly Coupa-to-NetSuite supplier sync | `[[po-invoice-entry-and-three-way-match]]`, `[[non-po-invoice-entry-and-approval]]`, `[[weekly-payment-run]]`, `[[invoice-intake-and-capture]]` |
| `[[requisition-and-approval]]` | `[[new-vendor-onboarding]]`; catalog/punchout content; statement of work for services requests | `[[po-issuance-and-change-orders]]`, `[[blanket-po-management]]` |
| `[[po-issuance-and-change-orders]]` | `[[requisition-and-approval]]`, `[[new-vendor-onboarding]]`; Coupa-to-NetSuite purchase order synchronisation | `[[goods-receipt]]`, `[[po-invoice-entry-and-three-way-match]]`, `[[blanket-po-management]]`, `[[return-to-vendor]]` |
| `[[confirming-po]]` | `[[po-invoice-entry-and-three-way-match]]` (unmatched supplier invoice returned to procurement); `[[goods-receipt]]` (delivered material that could not be tied to a purchase order) | `[[goods-receipt]]`, `[[po-invoice-entry-and-three-way-match]]` |
| `[[blanket-po-management]]` | `[[requisition-and-approval]]`, `[[po-issuance-and-change-orders]]` | `[[goods-receipt]]`, `[[po-invoice-entry-and-three-way-match]]` |
| `[[goods-receipt]]` | `[[po-issuance-and-change-orders]]`; supplier delivery to the plant receiving dock; consumption signal for the automatic-receipt plant | `[[po-invoice-entry-and-three-way-match]]`, `[[return-to-vendor]]` |
| `[[return-to-vendor]]` | `[[goods-receipt]]`, `[[po-issuance-and-change-orders]]`; supplier-issued return authorization | `[[po-invoice-entry-and-three-way-match]]` (supplier credit memo, per the open gap recorded there) |
| `[[invoice-intake-and-capture]]` | Supplier invoices via the AP Inbox and the Company post office box; OCR capture service; `[[new-vendor-onboarding]]`, `[[vendor-master-data-maintenance]]` | `[[po-invoice-entry-and-three-way-match]]`, `[[non-po-invoice-entry-and-approval]]`, `[[vendor-statement-reconciliation]]` |
| `[[po-invoice-entry-and-three-way-match]]` | `[[invoice-intake-and-capture]]`, `[[goods-receipt]]`, `[[po-issuance-and-change-orders]]`, `[[blanket-po-management]]`, `[[vendor-master-data-maintenance]]`, `[[return-to-vendor]]` | `[[weekly-payment-run]]`, `[[wire-and-manual-payment]]`, `[[confirming-po]]`, `[[vendor-statement-reconciliation]]` |
| `[[non-po-invoice-entry-and-approval]]` | `[[invoice-intake-and-capture]]`, `[[new-vendor-onboarding]]`, `[[vendor-master-data-maintenance]]` | `[[weekly-payment-run]]`, `[[wire-and-manual-payment]]` |
| `[[vendor-statement-reconciliation]]` | Supplier-issued statements of account; `[[invoice-intake-and-capture]]`, `[[po-invoice-entry-and-three-way-match]]`, `[[weekly-payment-run]]`, `[[wire-and-manual-payment]]`, `[[vendor-master-data-maintenance]]` | — |
| `[[weekly-payment-run]]` | `[[po-invoice-entry-and-three-way-match]]`, `[[non-po-invoice-entry-and-approval]]`, `[[vendor-banking-change]]`, `[[vendor-master-data-maintenance]]`; bank release of the ACH batch | `[[positive-pay-exception-handling]]`; monthly bank reconciliation (outside procure-to-pay) |
| `[[wire-and-manual-payment]]` | `[[po-invoice-entry-and-three-way-match]]`, `[[non-po-invoice-entry-and-approval]]`, `[[vendor-banking-change]]`; bank initiation and approval | `[[positive-pay-exception-handling]]`; monthly bank reconciliation (outside procure-to-pay) |
| `[[positive-pay-exception-handling]]` | `[[weekly-payment-run]]` (positive pay issue file / issued-check register); bank portal presentation of exception items and the bank's disposition deadline | Monthly bank reconciliation (outside procure-to-pay) |
