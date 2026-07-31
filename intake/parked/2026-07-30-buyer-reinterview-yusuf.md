# Buyer Re-Interview — Yusuf (Plants 2 & 3)

**Date:** 2026-07-30 · **Present:** Yusuf (Buyer), Gideon (IT Manager,
first 20 minutes for the NetSuite configuration pull), consultant.
**Purpose:** the outstanding re-interview named in the working notes —
over-receipt tolerance, blanket PO mechanics, and the Plant 3 Kanban
arrangement.

## 1. Over-receipt tolerance — configuration pulled

Gideon pulled the NetSuite receiving tolerance configuration on the call.

> Yusuf: "There it is. Five percent, and a five-hundred-dollar cap,
> whichever is SMALLER. So Hal's ten percent was wrong — or, being fair
> to Hal, ten percent might have been the old value. Five and five hundred
> is what's live."

The tolerance applies at receipt entry: a receipt exceeding PO quantity by
more than 5% of line value or $500, whichever is smaller, blocks entry.
Below the tolerance the receipt posts and the difference rides through to
the three-way match. Yusuf and Gideon both confirmed the same parameter
governs the change-order fork: above tolerance, the buyer must issue a
change order before the dock can complete the receipt.

## 2. Blanket purchase orders — the full mechanics

> Yusuf: "Every January, Dev and I sit down with the prior-year spend by
> supplier and set the not-to-exceed for each blanket. Dev signs off on
> the list, and each blanket goes through the normal requisition chain at
> its FULL annual value — so almost all of them hit Emmett's desk, since
> they're over twenty-five. That's deliberate. The whole point is the
> approval happens once, up front, at the ceiling."

- Term: calendar year, renewed each January; no mid-year blankets unless
  a new recurring supplier is onboarded.
- Releases against the blanket are receipt-driven and attract no further
  approval below the ceiling.
- The burn-down report is a saved Coupa report named **"Blanket PO
  Utilization"** (Yusuf showed it on screen). It is real and it works;
  nobody runs it on a schedule. Yusuf agreed on the call to run it
  **monthly, on the first business day**, and forward it to Dev.
- Exhaustion: a release that would breach the not-to-exceed is blocked by
  Coupa. The fix is a change order raising the ceiling, which re-routes
  through the requisition chain at the new full value. "It happened twice
  last year. Both times it was a scramble because nobody had looked at
  the burn-down since spring — hence me agreeing to the monthly run."

## 3. Plant 3 — the Kanban / consumption-based receipt

> Yusuf: "OK, Plant 3. Two steel suppliers, bin-managed. There is no dock
> receipt transaction at all. The material sits in supplier-owned bins on
> our floor; when production backflushes consumption in NetSuite, the
> backflush itself CREATES the goods receipt against the blanket PO —
> quantity equals what production consumed that day. Ownership transfers
> at consumption, not at delivery."

- The receipt posts automatically overnight from the backflush batch; no
  human touches it. Gideon: the batch job is `NS-BACKFLUSH-GR`, and it
  has the same no-owner-no-alerting problem as the Coupa sync — "if it
  fails, receipts just don't post and nobody is paged."
- Because ownership transfers at consumption, the supplier-owned bin
  stock at Plant 3 is EXCLUDED from cycle counts and from the month-end
  inventory reconciliation — "counting it would double-count material we
  don't own yet. The warehouse team knows this, but I don't think it's
  written down anywhere on their side."
- Invoicing: the two steel suppliers invoice monthly against the posted
  consumption receipts; those invoices three-way-match normally.

Consultant note: the exclusion rule and the auto-posted receipt clearly
touch the inventory team's counting and reconciliation procedures as well
as receiving — flagged for both workstreams.

## 4. Still open after this interview

- Whether the 5%/$500 tolerance should differ for Plant 3's auto-receipts
  (currently the tolerance is global). Yusuf had no view; Dev owns it.
- Who is paged when `NS-BACKFLUSH-GR` fails — same integration-ownership
  question as the Coupa sync, now with two instances.
