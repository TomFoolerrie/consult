## Appendix C — Screenshot / Evidence Index

<!-- derived: screenshot-index; writer: python -->

_Screenshot placeholders aggregated from the `SCREENSHOT PLACEHOLDER` callouts. IDs are numbered sequentially through the document; rows are grouped by sub-process._

#### Vendor Management

| SC ID | Caption | Status |
|---|---|---|
| SC-01 ([[#new-vendor-onboarding]]) | The Coupa New Supplier Request form, showing the required fields including the mandatory related-party question. | Pending user input |
| SC-02 ([[#new-vendor-onboarding]]) | A Coupa supplier record showing the attached OFAC SDN search-result screenshot and TIN match evidence. | Pending user input |
| SC-03 ([[#new-vendor-onboarding]]) | An activated NetSuite vendor record showing vendor status, payment terms, and default GL coding as set by the Accounts Payable Clerk. | Pending user input |
| SC-04 ([[#vendor-banking-change]]) | The NetSuite vendor record showing the callback note and attachment; must validate that the verification (date, time, person spoken to, details confirmed) is documented on the record itself. | Pending user input |
| SC-05 ([[#vendor-banking-change]]) | The NetSuite vendor record after approval, showing the active remit-to banking details; must validate that the active details match those confirmed on the callback. | Pending user input |
| SC-06 ([[#vendor-master-data-maintenance]]) | A NetSuite vendor record corrected after a sync failure, showing the populated payment terms field; must validate that manually corrected records carry complete payment terms. | Pending user input |
| SC-07 ([[#vendor-master-data-maintenance]]) | The NetSuite role configuration for the Vendor Maintenance role; must validate that the role carries no payment preparation, payment approval, or banking portal permissions. | Pending user input |

#### Procurement

| SC ID | Caption | Status |
|---|---|---|
| SC-08 ([[#requisition-and-approval]]) | The Coupa requisition entry screen showing the three request paths (hosted catalog / punchout, non-catalog free text, services request form); validates that all three intake paths exist as described. | Pending user input |
| SC-09 ([[#requisition-and-approval]]) | A capital requisition in Coupa showing the AFE custom field populated; validates that the field exists and blocks routing when empty. | Pending user input |
| SC-10 ([[#requisition-and-approval]]) | The approval chain panel on a submitted high-value requisition in Coupa; validates the live approver sequence by threshold and supports resolution of GAP-12. | Pending user input |
| SC-11 ([[#po-issuance-and-change-orders]]) | An issued purchase order in Coupa showing the NIG- sequential number and issued status; validates automatic generation from an approved requisition and the numbering format. | Pending user input |
| SC-12 ([[#po-issuance-and-change-orders]]) | The version history of a revised purchase order in Coupa showing the original and revised versions and the associated approval routing; validates that revisions are versioned rather than overwritten. | Pending user input |
| SC-13 ([[#po-issuance-and-change-orders]]) | The Coupa blanket purchase order burn-down report for an active blanket; validates that the report exists and shows cumulative releases against the annual NTE. | Pending user input |
| SC-14 ([[#confirming-po]]) | A recent confirming PO record in Coupa, showing the PO creation date relative to the supplier's invoice or service date and how the justification is documented on the record (if at all). | Pending user input |
| SC-15 ([[#confirming-po]]) | The Procurement Lead's confirming PO spreadsheet, showing the fields tracked and recent monthly volume, to substantiate the 15–20 per month estimate. | Pending user input |

#### Receiving

| SC ID | Caption | Status |
|---|---|---|
| SC-16 ([[#goods-receipt]]) | The Receive Orders screen for a purchase order receipt, showing per-line quantity received and the packing slip number keyed in the Memo field, immediately before save — validates the navigation path and the required entry fields. | Pending user input |
| SC-17 ([[#goods-receipt]]) | The NetSuite block message produced when an attempted receipt exceeds the over-receipt tolerance — validates that the block operates and evidences the live tolerance values (supports closure of the tolerance gap above). | Pending user input |
| SC-18 ([[#return-to-vendor]]) | The NetSuite Return Authorization screen for a completed return, showing the link to the original item receipt and the RMA reference — validates the entry path and required fields once confirmed. | Pending user input |

#### Invoice Processing

| SC ID | Caption | Status |
|---|---|---|
| SC-19 ([[#invoice-intake-and-capture]]) | The Ephesoft manual validation queue showing documents pending keying — validates that below-threshold documents route to the queue for human entry. | Pending user input |
| SC-20 ([[#invoice-intake-and-capture]]) | A captured bill in NetSuite in a pending state with the invoice image attached — validates the Ephesoft-to-NetSuite hand-off and the image attachment. | Pending user input |
| SC-21 ([[#po-invoice-entry-and-three-way-match]]) | A PO bill in NetSuite with lines populated from the purchase order reference, prior to save — validates that lines derive from the receipt rather than manual entry. | Pending user input |
| SC-22 ([[#po-invoice-entry-and-three-way-match]]) | A bill in "Match Exception - Hold" status in NetSuite — validates the exception status name and that failed matches hold rather than release. | Pending user input |
| SC-23 ([[#non-po-invoice-entry-and-approval]]) | The NetSuite Enter Bills screen showing a non-PO bill with manual GL account, department, and Class coding — validates the manual coding fields and the absence of a PO reference. | Pending user input |
| SC-24 ([[#non-po-invoice-entry-and-approval]]) | A non-PO bill in NetSuite showing the completed approval history — validates that approvals are recorded in the system rather than by email. | Pending user input |
| SC-25 ([[#vendor-statement-reconciliation]]) | A completed reconciliation worksheet for one top vendor from a recent quarter — validates that the reconciliation is performed and captures the worksheet's actual format and content. | Pending user input |
| SC-26 ([[#vendor-statement-reconciliation]]) | The designated reconciliation folder on the Finance Shared Drive showing retained worksheets by period — documents the three months of the last twelve for which completed worksheets exist (§9.2 of the prior SOP, SRC-006). | Pending user input |

#### Payments

| SC ID | Caption | Status |
|---|---|---|
| SC-27 ([[#weekly-payment-run]]) | The payment proposal in NetSuite Pay Bills with the due-date filter applied, alongside the Excel export — validates the selection criteria and the review artifact. | Pending user input |
| SC-28 ([[#weekly-payment-run]]) | The Chase Connect batch release screen showing the uploaded ACH batch pending release by a second user — validates the upload/release segregation and the approval configuration on the batch. | Pending user input |
| SC-29 ([[#wire-and-manual-payment]]) | The blank Wire Transfer Request Form template at its Finance/Treasury/Forms location on the Finance Shared Drive, showing the requester and Functional Vice President signature blocks. | Pending user input |
| SC-30 ([[#wire-and-manual-payment]]) | The Chase Connect wire initiation screen as completed by the Treasury Analyst, validating the entry fields and the pending-approval state after submission. | Pending user input |
| SC-31 ([[#wire-and-manual-payment]]) | The Chase Connect approval screen for a pending wire, validating the required approval action and the enforced dual-authorization workflow. | Pending user input |
| SC-32 ([[#positive-pay-exception-handling]]) | The Chase Connect positive pay exception queue showing a pending exception item with its pay/return options and the disposition deadline — validates where exceptions present and how the decision is recorded. | Pending user input |
