## Approve Invoice

### Scope

Approval and release of PO-backed vendor invoices after capture, from the
match queue to released-for-payment status. Owner: AP Manager. System:
Coupa. Runs daily; adjoins [[invoice-intake]] upstream and
[[payment-run]] downstream.

### Inputs

- Captured invoice — from [[invoice-intake]] (Coupa match queue)
- Open purchase order — from purchasing (Coupa)
- Goods receipt confirmation — from receiving (NetSuite sync)

### Transformation

The AP Manager performs the three-way match (invoice vs. PO vs. receipt)
and releases or holds each invoice. Quantity and price variances inside
tolerance release automatically; anything outside routes to a manual hold.

1. Open the Coupa match queue and filter to unreleased invoices.
2. Compare invoiced quantity and price to the PO line and the receipt.
3. Release matched invoices; route exceptions to hold with a reason code.

### Outputs

- Released invoice — to the weekly payment run ([[payment-run]])
- Match log with hold reason codes — retained in Coupa (audit evidence)

### Controls

> **CONTROL — CTRL-01:** Three-way match enforced in Coupa before release;
> tolerance thresholds configured centrally (SRC-002).

### Issues

> **VALIDATION REQUIRED — GAP-01:** The exact quantity tolerance percentage
> in effect. The AP Manager quoted 5% but was not certain (SRC-002).

> **PAIN POINT — PP-01:** "The manual holds eat my Fridays — half of them
> are receipts posted late, not real mismatches." — AP Manager (SRC-002).

```consult-meta
systems:
  - coupa
  - netsuite
roles:
  - ap-manager
```
