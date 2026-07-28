# Interview — Inventory Control Analyst, 2026-07-21

Attendees: Inventory Control Analyst; consultant.
Subject: count execution detail, reservations about the adjustment process,
and the month-end inventory reconciliation.

## Count execution detail

I generate the count sheets from the NetSuite cycle count worksheet — blind,
no book quantities shown. The tolerance table lives in a saved search I
maintain myself; it is not configuration, so if I fat-finger the saved
search the tolerances change and nobody would know. I have asked for the
tolerances to be moved into an approved configuration.

Recounts: a variance outside tolerance is recounted next business day by a
different counting pair. I stage the recount sheets separately and mark them
RECOUNT in red so they don't get mixed into the day's normal sheets.

## Adjustments

The Friday adjustment log review with the Plant Controller works, but the
sign-off is on paper and the posting happens Monday, so there is a weekend
where approved-but-unposted adjustments sit in my tray. Month-end is the
problem: if the last Friday falls before the final count day, adjustments
from that last count post into the next period. The Corporate Controller
told me she wants period-end adjustments accrued; we have never done it.

## Month-end inventory reconciliation

On workday 2 I reconcile the inventory sub-ledger to the general ledger.
NetSuite inventory valuation report against the GL inventory accounts,
by location. Timing differences from in-transit receipts are the usual
reconciling item — a goods receipt posted in Coupa on the last day can hit
NetSuite a day later through the sync. I document each reconciling item in
the workbook and the Plant Controller reviews it by workday 4. The workbook
is on the shared drive under Accounting/Month End Close/2026//150 - Property
and Equipment — I know, wrong folder name, it predates me.

The Coupa-to-NetSuite sync being flaky makes the timing rows worse in some
months. Procurement owns that interface issue; when it fails, my in-transit
list is wrong and I reconcile to a moving target.
