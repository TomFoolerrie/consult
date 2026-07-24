## RACI Matrix

<!-- derived: raci; writer: agent -->

_R = Responsible (does the work) · A = Accountable (answerable for the outcome) · C = Consulted · I = Informed. An asterisk (*) marks an assumed assignment not confirmed in the source._

| Activity | Requester | Cost Center Owner | Functional Vice President | Chief Financial Officer | Procurement Lead | Buyer | Plant Manager | Receiving Supervisor | Accounts Payable Clerk | Senior Accounts Payable Specialist | Accounts Payable Manager | Assistant Controller | Corporate Controller | Treasury Analyst | IT Manager | Supplier |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| [[new-vendor-onboarding]] | R |  |  |  | R, A | R |  |  | R |  | I |  | C |  |  | C |
| [[vendor-banking-change]] |  |  |  |  | C |  |  |  | R* | R* | A* |  | C |  |  | C |
| [[vendor-master-data-maintenance]] |  |  |  |  |  |  |  |  | R |  | R | C | A |  | C |  |
| [[requisition-and-approval]] | R | A | C | C | I |  |  |  |  |  |  |  |  |  |  | I |
| [[po-issuance-and-change-orders]] | R | C |  |  | A* | R |  |  |  |  |  |  |  |  |  | I |
| [[confirming-po]] | C |  |  |  | R, A* | R | C |  |  |  | I |  |  |  |  | I |
| [[goods-receipt]] | R |  |  |  | I | C |  | R, A* |  | I | I |  |  |  |  | I |
| [[return-to-vendor]] |  |  |  |  |  | R |  | R, A* |  |  | I |  |  |  |  | C |
| [[invoice-intake-and-capture]] |  |  |  |  |  |  |  |  | R | R | A |  |  |  |  | I |
| [[po-invoice-entry-and-three-way-match]] |  |  |  |  |  | C |  | C |  | R | A* |  | I |  |  | C |
| [[non-po-invoice-entry-and-approval]] |  | A | C | C |  |  |  |  | R |  | I |  | C |  |  |  |
| [[vendor-statement-reconciliation]] |  |  |  |  | I |  |  |  |  | R | A* |  | I |  |  | C |
| [[weekly-payment-run]] |  |  |  |  |  |  |  |  |  |  | R | I | A | R |  | I |
| [[wire-and-manual-payment]] | R |  | C | C |  |  |  |  |  |  | I |  | A | R |  | I |
| [[positive-pay-exception-handling]] |  |  |  |  |  |  |  |  |  |  | R, A* | I | C |  |  | I |

\* Eight activities carry an assumed accountability because no reviewer or approver is named in the source. For [[confirming-po]], [[goods-receipt]], [[return-to-vendor]], [[vendor-statement-reconciliation]] and [[positive-pay-exception-handling]], no second review of the completed work was described, so accountability is assumed to sit with the role that performs the work — the Procurement Lead, the Receiving Supervisor, the Senior Accounts Payable Specialist and the Accounts Payable Manager respectively — pending confirmation with the process owner. For [[po-invoice-entry-and-three-way-match]], a bill within matching tolerance releases without human review, so accountability is assumed to sit with the Accounts Payable Manager, who oversees the exception population. For [[po-issuance-and-change-orders]], the purchase order is cut by the system from the approved requisition and only value-increasing change orders re-enter an approval chain, so accountability for issuance is assumed to sit with the Procurement Lead. For [[vendor-banking-change]], both the role that performs the callback and keys the change and the role that gives the second approval are disputed across sources; the Accounts Payable Clerk and the Senior Accounts Payable Specialist are shown as assumed performers and accountability is assumed to sit with the Accounts Payable Manager, all three pending confirmation with the process owner.
