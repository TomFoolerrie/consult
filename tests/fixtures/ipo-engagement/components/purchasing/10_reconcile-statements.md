## Reconcile Vendor Statements

### Scope

Monthly reconciliation of supplier statements against the paid and open
items in NetSuite for the larger vendors, ending in a worksheet of
differences the AP Manager chases with the supplier. Owner: AP Manager.
Systems: NetSuite, Excel, finance shared drive. Runs monthly, and in
practice only for the top vendors. Consumes the payment register from
[[schedule-payment]]. Nothing downstream in this area consumes its product.

### Inputs

- Payment register for the run — from [[schedule-payment]] (NetSuite)
- Supplier statement of account — from the supplier, by email
- Open bill listing by vendor — from NetSuite

### Transformation

The AP Manager works one vendor at a time: the supplier's statement lines
are ticked against paid items on the payment registers and against the open
bill listing, and whatever will not tie is written up as a difference and
raised with the supplier directly. Coverage is by judgment of vendor size,
not by a defined population.

1. Select the vendors to reconcile for the month by spend.
2. Request or retrieve the supplier statement of account.
3. Tick statement lines against the payment registers and the open bill
   listing in NetSuite.
4. Write the unmatched lines up on the reconciliation worksheet with a
   reason (invoice never received, payment in transit, credit not applied).
5. Raise the differences with the supplier and sign the worksheet off.

### Outputs

- Vendor statement reconciliation worksheet, signed — filed on the finance
  shared drive (no downstream process in this area consumes it; it is
  retained as evidence only)

### Controls

> **CONTROL — CTRL-06:** The AP Manager signs off each completed
> reconciliation worksheet before filing it (SRC-001).

### Issues

> **VALIDATION REQUIRED — GAP-04:** Whether the reconciliation worksheets
> are in fact filed on the finance shared drive, and for which vendors. The
> AP Manager states they are (SRC-001); the Corporate Controller has never
> audited that the reconciliation happens beyond the top vendors and had not
> looked at the drive (SRC-003).

> **PAIN POINT — PP-04:** "Nobody downstream uses it — it's for me, and for
> you people when you ask." — AP Manager on the reconciliation worksheet
> (SRC-001).

```consult-meta
systems:
  - netsuite
  - excel
  - finance-shared-drive
roles:
  - ap-manager
  - corporate-controller
  - supplier
```
