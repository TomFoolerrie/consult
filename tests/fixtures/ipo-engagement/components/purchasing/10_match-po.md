## Match Invoice to PO

### Scope

Three-way match of PO-backed invoices against the purchase order line and
the goods receipt, ending in either a bill approved for payment or a
variance hold. Owner: AP Manager. System: NetSuite. Runs continuously as
captured invoices land. Takes its work from [[receive-invoice]], passes
clean bills to [[schedule-payment]] and variances to
[[approve-exceptions]]. Non-PO invoices are out of scope for this area.

### Inputs

- Captured invoice header record (pending bill) — from [[receive-invoice]]
  (NetSuite)
- Open purchase order line — from the Buyer (NetSuite PO record)
- Goods receipt confirmation — from the Receiving Supervisor (NetSuite item
  receipt)

### Transformation

The AP Manager works the unmatched-bill view. NetSuite compares invoiced
quantity and extended price to the PO line and the item receipt; anything
inside tolerance releases without human touch, and anything outside it
stops and is handed to exception disposition. The match is re-run rather
than overridden when receiving is simply behind.

1. Open the NetSuite unmatched-bill view and filter to PO-backed bills.
2. Compare invoiced quantity and extended price to the PO line and to the
   goods receipt confirmation for the same PO line.
3. Let bills inside tolerance release; confirm the bill state changed to
   approved for payment.
4. Place bills outside tolerance on hold and record the variance type
   (quantity, price, or no receipt posted).

### Outputs

- Matched bill approved for payment — to [[schedule-payment]] (NetSuite)
- Variance hold item — to [[approve-exceptions]] (NetSuite hold queue)

### Controls

> **CONTROL — CTRL-02:** Three-way match enforced by NetSuite: a PO-backed
> bill cannot reach approved-for-payment state without a matching PO line
> and a posted item receipt (SRC-001, SRC-002).

> **CONTROL — CTRL-03:** Variances outside the configured tolerance release
> nothing automatically — the bill stops in the hold queue (SRC-002).

### Issues

> **VALIDATION REQUIRED — GAP-02:** The live three-way match tolerance. The
> SOP caps it at two percent of extended line value (SRC-002); the AP
> Manager described tolerance behaviour without naming a figure and had not
> pulled the configuration (SRC-001).

> **PAIN POINT — PP-02:** "Half the holds are not real variances. They're
> receipts the dock posted late. It eats my Fridays." — AP Manager
> (SRC-001). The process itself is understood; the cost is receipt timing,
> not missing documentation.

```consult-meta
systems:
  - netsuite
roles:
  - ap-manager
  - buyer
  - receiving-supervisor
```
