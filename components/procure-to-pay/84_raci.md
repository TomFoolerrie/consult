## RACI Matrix

<!-- derived: raci; writer: agent -->

_R = Responsible (does the work) · A = Accountable (answerable for the outcome) · C = Consulted · I = Informed. An asterisk (*) marks an assumed assignment not confirmed in the source._

| Activity | Chief Financial Officer | Corporate Controller | Accounts Payable Manager | Senior Accounts Payable Specialist | Accounts Payable Clerk | Treasury Analyst | Procurement Lead | Buyer | Receiving Supervisor | Receiver | IT Manager | Cost Center Owner | Functional Vice President | Requester | Plant Manager |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `[[requisition-and-approval]]` | C | C |  |  |  |  | C | C |  |  |  | A | C | R |  |
| `[[po-issuance-and-change-orders]]` | C |  |  |  |  |  | A* | R | C |  | C | C | C | R |  |
| `[[blanket-po-management]]` |  |  |  |  |  |  | C | R, A* |  |  |  |  |  |  |  |
| `[[confirming-po]]` |  |  |  |  |  |  | R, A* | R |  |  |  |  |  | C | C |
| `[[new-vendor-onboarding]]` |  | C |  |  | R |  | R, A | R |  |  | C |  |  | C |  |
| `[[vendor-master-data-maintenance]]` |  | A* | R |  | R |  | C |  |  |  |  |  |  |  |  |
| `[[vendor-banking-change]]` |  | A* |  |  | R* |  | R* |  |  |  |  |  |  |  |  |
| `[[goods-receipt]]` |  |  |  | C |  |  | C | C | A* | R |  |  |  |  |  |
| `[[return-to-vendor]]` |  |  | C |  |  |  |  | R | R, A* |  |  |  |  |  |  |
| `[[invoice-intake-and-capture]]` |  |  | A* | R | R |  |  |  |  |  | C |  |  |  |  |
| `[[po-invoice-entry-and-three-way-match]]` |  | C | C | R, A* |  |  | C | C | C |  |  |  |  |  |  |
| `[[non-po-invoice-entry-and-approval]]` | C | C | C | C | R |  | C |  |  |  | C | A | C |  |  |
| `[[vendor-statement-reconciliation]]` |  | C | C | R, A* |  |  |  |  |  |  |  |  |  |  |  |
| `[[weekly-payment-run]]` |  | A | R |  |  | R |  |  |  |  |  |  |  |  |  |
| `[[wire-and-manual-payment]]` | C | A | R |  |  | R |  |  |  |  |  |  | C | C |  |
| `[[positive-pay-exception-handling]]` |  | C | R, A* |  |  |  |  |  |  |  |  |  |  |  |  |

\* Accountability is assumed rather than confirmed on eleven activities. No reviewer or approver is named in the source for [[blanket-po-management]], [[confirming-po]], [[po-invoice-entry-and-three-way-match]], [[vendor-statement-reconciliation]], [[return-to-vendor]] or [[goods-receipt]]; accountability is therefore placed with the role that performs the work — or, for [[goods-receipt]], with the supervisor of the role that performs it — pending confirmation with the process owner. For [[positive-pay-exception-handling]] the disposition is made and finalised by the preparer alone, so accountability is shown as sitting with that same role. For [[invoice-intake-and-capture]] the named reviewer performs a second tranche of the same keying rather than a review, so accountability is assumed to sit with the Accounts Payable Manager. For [[po-issuance-and-change-orders]] approvers act only on a value-increasing change order and no role is answerable for issuance itself, so accountability is assumed to sit with the Procurement Lead as owner of the purchasing system. For [[vendor-master-data-maintenance]] no reviewer is described for day-to-day record maintenance and the Corporate Controller receives the results of the periodic master file review, so accountability is assumed to sit there. For [[vendor-banking-change]] both the performer and the second approver are disputed between sources: the Responsible marks on the Accounts Payable Clerk and the Procurement Lead are both assumed, and accountability is assumed to sit with the Corporate Controller as owner of the banking change policy. All eleven require confirmation with the process owner before the matrix is relied upon.
