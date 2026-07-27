## RACI Matrix

<!-- derived: raci; writer: agent -->

_Responsible = does the work · Accountable = answerable for the outcome (exactly one per activity) · Consulted = two-way input · Informed = told after. An asterisk (*) marks an assumed assignment not confirmed in the source._

| Activity | Responsible | Accountable | Consulted | Informed |
|---|---|---|---|---|
| [[requisition-and-approval]] | Requester | Cost Center Owner | Functional Vice President; Chief Financial Officer; Procurement Lead | — |
| [[po-issuance-and-change-orders]] | Requester; Buyer | Buyer* | Cost Center Owner; Procurement Lead; Receiving Supervisor | Supplier |
| [[confirming-po]] | Buyer; Procurement Lead | Procurement Lead* | Requester; Plant Manager; Receiving Supervisor | Accounts Payable Manager |
| [[new-vendor-onboarding]] | Requester; Buyer; Procurement Lead; Accounts Payable Clerk; Supplier | Procurement Lead | Corporate Controller | — |
| [[vendor-banking-change]] | Accounts Payable Clerk | Corporate Controller* | Procurement Lead; Supplier | Accounts Payable Manager |
| [[vendor-master-data-maintenance]] | Accounts Payable Clerk; Accounts Payable Manager | Accounts Payable Manager* | — | Corporate Controller |
| [[goods-receipt]] | Requester; Receiver | Receiving Supervisor* | Buyer; Senior Accounts Payable Specialist; Supplier; Carrier | — |
| [[return-to-vendor]] | Buyer; Receiving Supervisor | Receiving Supervisor* | Supplier | Accounts Payable Manager |
| [[invoice-intake-and-capture]] | Accounts Payable Clerk; Senior Accounts Payable Specialist | Accounts Payable Manager* | IT Manager | Supplier |
| [[po-invoice-entry-and-three-way-match]] | Senior Accounts Payable Specialist | Senior Accounts Payable Specialist* | Buyer; Receiving Supervisor; Supplier | — |
| [[non-po-invoice-entry-and-approval]] | Accounts Payable Clerk | Cost Center Owner | Functional Vice President; Chief Financial Officer; Corporate Controller | — |
| [[vendor-statement-reconciliation]] | Senior Accounts Payable Specialist | Senior Accounts Payable Specialist* | Accounts Payable Manager; Corporate Controller; Supplier | — |
| [[weekly-payment-run]] | Accounts Payable Manager | Corporate Controller | Treasury Analyst | Assistant Controller |
| [[wire-and-manual-payment]] | Requester; Treasury Analyst | Corporate Controller | Functional Vice President; Chief Financial Officer; Accounts Payable Manager | Assistant Controller |
| [[positive-pay-exception-handling]] | Accounts Payable Manager | Accounts Payable Manager* | Corporate Controller | — |

\* Assumed accountability, pending confirmation with the process owner:

- For [[po-issuance-and-change-orders]], issuance is system-automatic and no approver of change orders or blanket purchase orders is separately named; accountability is assumed to sit with the Buyer, who initiates and administers revisions, pending confirmation.
- For [[confirming-po]], approval routing of the confirming purchase order is unconfirmed; accountability is assumed to sit with the Procurement Lead, who obtains the justification and logs the confirming purchase orders.
- For [[vendor-banking-change]], the sources disagree three ways on who performs the callback verification (the Procurement Lead's team per policy, the Accounts Payable Clerk per current practice, or the Senior Accounts Payable Specialist per the prior SOP); the matrix follows the current-practice account, with the Accounts Payable Clerk responsible for both the callback and the record entry, and the dispute is flagged in that procedure. The required second-person approver is likewise unconfirmed; accountability is assigned to the Corporate Controller, who mandates the control and is speculated to be the approver in practice.
- For [[vendor-master-data-maintenance]], the Accounts Payable Manager owns the semi-annual master file review, but no independent review of individual non-banking record changes was described; per-change accountability is assumed to sit with the Accounts Payable Manager.
- For [[goods-receipt]], no formal per-receipt review exists; accountability is assumed to sit with the Receiving Supervisor, who provides supervisory oversight and resolves discrepancies.
- For [[return-to-vendor]], no review step was described; accountability is assumed to sit with the Receiving Supervisor, who initiates the return and whose team records it. Ownership of vendor credit-memo follow-up is unconfirmed; the Accounts Payable Manager is shown as informed pending confirmation.
- For [[invoice-intake-and-capture]], no reviewer exists at intake (captured bills are reviewed downstream); accountability is assumed to sit with the Accounts Payable Manager as the supervisor of the intake staff.
- For [[po-invoice-entry-and-three-way-match]], no separate per-bill reviewer was identified — the match is system-enforced and payment release is controlled downstream; accountability is assumed to sit with the Senior Accounts Payable Specialist, who performs the entry and works the exceptions.
- For [[vendor-statement-reconciliation]], no reviewer or sign-off was identified in any source; accountability is assumed to sit with the Senior Accounts Payable Specialist, who prepares the reconciliations.
- For [[positive-pay-exception-handling]], disposition is a single-person decision with no secondary review or backup described; accountability is assumed to sit with the Accounts Payable Manager, who makes the pay-or-return decision.

For [[wire-and-manual-payment]], the manual-check preparer is unidentified in the sources; the Corporate Controller is accountable via the required written authorization for manual checks and the wire approval role, with the Chief Financial Officer shown as consulted as the alternate wire approver. For [[non-po-invoice-entry-and-approval]] and [[requisition-and-approval]], the Cost Center Owner is accountable as the first and universal approver; higher-tier approvers whose thresholds are contested between the sources are shown as consulted.
