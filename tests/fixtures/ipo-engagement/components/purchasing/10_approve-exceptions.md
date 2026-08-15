## Approve Exceptions

### Scope

Disposition of held invoices — variance holds from the match and capture
exceptions from intake — to either release for payment or return to the
originator. Owner: AP Manager, working with the Senior AP Specialist.
System: NetSuite. Runs as the queue fills, in practice heaviest on Fridays.
Draws work from [[match-po]] and [[receive-invoice]]; releases feed
[[schedule-payment]]. Vendor-side dispute resolution is out of scope.

### Inputs

- Variance hold item — from [[match-po]] (NetSuite hold queue)
- Capture exception queue item — from [[receive-invoice]] (Ephesoft
  validation queue)
- Goods receipt confirmation — from the Receiving Supervisor (NetSuite item
  receipt)

### Transformation

The AP Manager and the Senior AP Specialist work the hold queue by judgment.
Each held bill is re-checked against the receipt, because most holds resolve
themselves once receiving posts; the remainder are priced against the PO with
the Buyer or returned to the supplier. The disposition is typed straight into
the bill with a reason code, and nothing in NetSuite asks a second person to
agree.

1. Sort the hold queue by variance type and age.
2. Re-check each quantity variance against the goods receipt confirmation to
   separate late receipts from real mismatches.
3. Re-run the match on bills whose receipt has since posted.
4. Take price variances to the Buyer for a PO change or a return decision.
5. Record the disposition and a reason code on the bill and release it, or
   return the invoice to the supplier.

### Outputs

- Released bill approved for payment — to [[schedule-payment]] (NetSuite)
- Disposition reason code entry — retained on the bill in NetSuite (seven-year
  retention per the SOP)
- Returned invoice — sent back to the supplier by email

### Controls

No system-enforced or supervisory control was identified over exception
disposition: the reason code is recorded by the same person who releases the
bill, and NetSuite requires no second approval (SRC-001). Recorded here as
the current state, not as a recommendation.

### Issues

> **PAIN POINT — PP-03:** "There's no approval step in NetSuite for a
> variance disposition — you just change it and move on. I log the reason
> code because I want the history, not because anything makes me." — AP
> Manager (SRC-001).

```consult-meta
systems:
  - netsuite
  - ephesoft
roles:
  - ap-manager
  - senior-ap-specialist
  - buyer
  - receiving-supervisor
  - supplier
```
