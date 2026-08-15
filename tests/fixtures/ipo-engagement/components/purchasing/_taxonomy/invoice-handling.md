## Invoice Handling

### Scope

Everything that happens to a supplier invoice between arrival and a bill
that is fit to pay: receipt and capture, the three-way match against the
purchase order and the goods receipt, and disposition of whatever the match
holds. Covers the steps receive-invoice, match-po and approve-exceptions.

The boundary upstream is the purchase order — vendor selection, requisition
and PO issuance belong to the buying side and not to this node. The boundary
downstream is the approved-for-payment state: selection of what actually
pays in a given week is disbursement, under schedule-payment. Non-PO invoices
and employee expense reimbursement are outside this area entirely.

> **VALIDATION REQUIRED — GAP-05:** Whether capture exceptions belong to
> this node at all. The AP Manager treats the Ephesoft validation queue as
> part of invoice handling and dispositions its items alongside variance
> holds, because they surface as the same Friday workload (SRC-001). The SOP
> and the Corporate Controller place capture exceptions with document
> management under intake administration, explicitly excluded from invoice
> processing exceptions (SRC-002, SRC-003). Both framings are recorded; the
> client has never settled it, so the boundary of this node is unresolved.

```consult-meta
systems:
  - ap-inbox
  - ephesoft
  - netsuite
roles:
  - ap-manager
  - ap-clerk
  - senior-ap-specialist
```
