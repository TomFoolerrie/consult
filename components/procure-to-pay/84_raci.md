## RACI Matrix

<!-- derived: raci; writer: agent -->

_R = Responsible (does the work) · A = Accountable (answerable for the outcome) · C = Consulted (two-way input) · I = Informed (told after). An asterisk (*) marks an assumed assignment not confirmed in the source._

| Activity | Requester | Cost Center Owner | Functional Vice President | Chief Financial Officer | Buyer | Procurement Lead | Plant Manager | Receiver | Receiving Supervisor | Accounts Payable Clerk | Senior Accounts Payable Specialist | Accounts Payable Manager | Corporate Controller | Assistant Controller | Treasury Analyst | IT Manager | Supplier | Carrier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [[requisition-and-approval]] | R | A | C | C |  | C |  |  |  |  |  |  |  |  |  |  |  |  |
| [[po-issuance-and-change-orders]] | R |  C |  |  | R, A* | C |  |  | C |  |  |  |  |  |  |  | I |  |
| [[confirming-po]] | C |  |  |  | R | R, A* | C |  | C |  |  | I |  |  |  |  |  |  |
| [[new-vendor-onboarding]] | R |  |  |  | R | R, A |  |  |  | R |  |  | C |  |  |  | R |  |
| [[vendor-banking-change]] |  |  |  |  |  | C |  |  |  | R |  | I | A* |  |  |  | C |  |
| [[vendor-master-data-maintenance]] |  |  |  |  |  |  |  |  |  | R |  | R, A* | I |  |  |  |  |  |
| [[goods-receipt]] | R |  |  |  | C |  |  | R | A* |  | C |  |  |  |  |  | C | C |
| [[return-to-vendor]] |  |  |  |  | R |  |  |  | R, A* |  |  | I |  |  |  |  | C |  |
| [[invoice-intake-and-capture]] |  |  |  |  |  |  |  |  |  | R | R | A* |  |  |  | C | I |  |
| [[po-invoice-entry-and-three-way-match]] |  |  |  |  | C |  |  |  | C |  | R, A* |  |  |  |  |  | C |  |
| [[non-po-invoice-entry-and-approval]] |  | A | C | C |  |  |  |  |  | R |  |  | C |  |  |  |  |  |
| [[vendor-statement-reconciliation]] |  |  |  |  |  |  |  |  |  |  | R, A* | C | C |  |  |  | C |  |
| [[weekly-payment-run]] |  |  |  |  |  |  |  |  |  |  |  | R | A |  | C |  |  |  |
| [[wire-and-manual-payment]] | R |  | C | C |  |  |  |  |  |  |  | C | A |  I | R |  |  |  |
| [[positive-pay-exception-handling]] |  |  |  |  |  |  |  |  |  |  |  | R, A* | C |  |  |  |  |  |

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

For [[wire-and-manual-payment]], the manual-check preparer is unidentified in the sources; the Corporate Controller is accountable via the required written authorization for manual checks and the wire approval role. For [[non-po-invoice-entry-and-approval]] and [[requisition-and-approval]], the Cost Center Owner is accountable as the first and universal approver; higher-tier approvers whose thresholds are contested between the sources are shown as consulted.
