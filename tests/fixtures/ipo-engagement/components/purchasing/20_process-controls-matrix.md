## Process & Controls Matrix

<!-- derived: process-controls-matrix; writer: python -->

_One row per process step, grouped by the taxonomy node that covers it. Owner and systems come from each step's recorded bindings; inputs and outputs are the step's own process edges; the last column counts what is still open on that step._

### Invoice Handling

| Process Step | Owner (roles) | Systems | Inputs | Outputs | Control | Open Validation Required / Pain Point |
|---|---|---|---|---|---|---|
| Receive Invoice ([[#receive-invoice]]) | Accounts Payable Clerk | AP Inbox (ap-invoices@), Ephesoft, NetSuite | Supplier invoice image (PDF or scan) — from the supplier, arriving in the AP Inbox; Purchase order reference printed on the invoice face — from the Buyer, via the invoice document itself | Captured invoice header record (pending bill) — to [[match-po]] (NetSuite); Capture exception queue item — to [[approve-exceptions]] where the PO reference could not be read from the invoice face; Invoice image, indexed — retained in Ephesoft as the source document | CTRL-01 | 1 Validation Required (GAP-01); 1 Pain Point (PP-01) |
| Match Invoice to PO ([[#match-po]]) | Accounts Payable Manager | NetSuite | Captured invoice header record (pending bill) — from [[receive-invoice]] (NetSuite); Open purchase order line — from the Buyer (NetSuite PO record); Goods receipt confirmation — from the Receiving Supervisor (NetSuite item receipt) | Matched bill approved for payment — to [[schedule-payment]] (NetSuite); Variance hold item — to [[approve-exceptions]] (NetSuite hold queue) | CTRL-02, CTRL-03 | 1 Validation Required (GAP-02); 1 Pain Point (PP-02) |
| Approve Exceptions ([[#approve-exceptions]]) | Accounts Payable Manager | NetSuite, Ephesoft | Variance hold item — from [[match-po]] (NetSuite hold queue); Capture exception queue item — from [[receive-invoice]] (Ephesoft validation queue); Goods receipt confirmation — from the Receiving Supervisor (NetSuite item receipt) | Released bill approved for payment — to [[schedule-payment]] (NetSuite); Disposition reason code entry — retained on the bill in NetSuite (seven-year retention per the SOP); Returned invoice — sent back to the supplier by email | — | 1 Pain Point (PP-03) |

### Schedule Payment

| Process Step | Owner (roles) | Systems | Inputs | Outputs | Control | Open Validation Required / Pain Point |
|---|---|---|---|---|---|---|
| Schedule Payment ([[#schedule-payment]]) | Accounts Payable Manager | NetSuite, Microsoft Excel, Chase Connect, Finance Shared Drive | Matched bill approved for payment — from [[match-po]] (NetSuite); Released bill approved for payment — from [[approve-exceptions]] (NetSuite); Cash position sheet — from the Treasury Analyst (finance shared drive) | NACHA payment file, released — transmitted to the bank through Chase Connect; Payment register for the run — to [[reconcile-statements]] (NetSuite) | CTRL-04, CTRL-05 | 1 Validation Required (GAP-03) |

### Reconcile Vendor Statements

| Process Step | Owner (roles) | Systems | Inputs | Outputs | Control | Open Validation Required / Pain Point |
|---|---|---|---|---|---|---|
| Reconcile Vendor Statements ([[#reconcile-statements]]) | Accounts Payable Manager | NetSuite, Microsoft Excel, Finance Shared Drive | Payment register for the run — from [[schedule-payment]] (NetSuite); Supplier statement of account — from the supplier, by email; Open bill listing by vendor — from NetSuite | Vendor statement reconciliation worksheet, signed — filed on the finance shared drive (no downstream process in this area consumes it; it is retained as evidence only) | CTRL-06 | 1 Validation Required (GAP-04); 1 Pain Point (PP-04) |
