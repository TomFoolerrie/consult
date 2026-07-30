# Interview — Warehouse Manager (Plant 2), 2026-07-20

Attendees: Warehouse Manager (Plant 2); consultant.
Subject: inventory control at Nordhaven Industrial Group — cycle counting,
stock adjustments, and how inventory records tie to receiving.

## Cycle counting

We count on an ABC schedule. A-items are counted monthly, B-items quarterly,
C-items annually. The count sheets are generated out of NetSuite on the first
Monday of the counting window by the Inventory Control Analyst — she prints
them blind, meaning the sheet shows location and item but not the system
quantity. Counters work in pairs, one counting, one recording. They are not
allowed to count locations they picked from that same week; the analyst
swaps assignments when that happens.

Completed sheets come back to the analyst the same day. She keys the counted
quantities into the NetSuite count worksheet and the system shows variances
against book. Anything within tolerance — it's 2% by value for A-items, 5%
for B and C — posts automatically when she approves the worksheet. Variances
outside tolerance are recounted the next morning by a different pair before
anything is adjusted. If the recount confirms the variance, it goes on the
adjustment log for the Plant Controller.

We never post an adjustment the same day as the count. The Plant Controller
reviews the adjustment log every Friday and approves or challenges each line.
He signs the log — literally signs the printout — and the analyst posts the
approved adjustments in NetSuite on Monday. Rejected lines go back for a
third count. I know audit asked for the sign-off to move into the system as
an approval step; that hasn't happened.

## Stock adjustments outside the count

Damage, spoilage and scrap go on a Material Disposition Form. Whoever finds
the damage fills the form, their supervisor signs it, and the form goes to
the Inventory Control Analyst to post. Anything over $5,000 book value also
needs the Plant Controller before posting. The form is paper. Photos are
supposed to be attached for damage claims but usually are not.

## Where receiving meets inventory

Receiving is procurement's process, not mine — the receiver dock-checks the
delivery against the purchase order, counts the cartons, and posts the goods
receipt in Coupa, and the shipment is visually inspected for damage before
anything is putaway. Once the receipt posts, my team does putaway: the
material handler moves the pallets to the bin the system suggests, scans the
bin, and confirms the move in NetSuite. If the receiver short-counts or the
receipt posts against the wrong PO line, the inventory is wrong from day one
and the cycle count catches it weeks later. That handoff — receipt posted,
putaway confirmed — is where most of our book-to-floor variances are born.

The vendor master matters to us too: if procurement sets a wrong unit of
measure on the item-vendor record, receiving posts eaches as cases and my
on-hand is off by a factor of twelve. We flag those to the Procurement Lead;
fixing the vendor record is their process, we just live with the fallout.
