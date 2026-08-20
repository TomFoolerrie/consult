# Interview — Accounts Payable Manager

**Client:** Nordhaven Industrial Group
**Date:** 2026-05-12
**Location:** Corporate office, Belmont Ridge (Conference Rm 2B) + Teams
**Participants:** Marisol Vance (AP Manager), Priya Raghunathan (Senior AP Specialist, joined ~00:38)
**Interviewer:** Engagement team

---

**Interviewer:** Thanks for making the time. Let's start wide — walk me through what your team owns, end to end.

**Marisol Vance:** Sure. So AP is me plus three. Priya's my senior — she does the bulk of PO invoice entry and she's the one who fights with the match exceptions. Tobias Lindqvist does vendor master and, um, also the smaller non-PO stuff, credit card statements, that kind of thing. And then Bo Whitfield is part-time, twenty-five hours, mostly filing and the AP Inbox triage. We touch everything from the invoice hitting the mailbox to the payment leaving the bank. Not the requisition side — that's Dev's world.

**Interviewer:** Dev being —

**Marisol Vance:** Dev Anand Rao, procurement lead. Dev and Yusuf Adeyemi, they're the buyers. Yusuf covers Plant 2 and Plant 3, Dev's got corporate and Plant 1 plus all the indirect. You'll want to talk to Dev, they know the Coupa side way better than I do.

**Interviewer:** We're seeing them tomorrow. Okay — so invoice arrives. What actually happens?

**Marisol Vance:** [00:04:12] Right. Ninety-something percent come into ap-invoices@ — it's a shared Outlook mailbox, we just call it the AP Inbox. Vendors are supposed to send there, it's on the PO terms. Some still mail paper to the Belmont Ridge PO box, maybe forty, fifty pieces a week, and Bo scans those in. Everything — scanned or emailed — gets dropped into Ephesoft. That's our OCR thing. It reads the header data, vendor, invoice number, invoice date, total, and it tries to grab the PO number off the face of the invoice.

**Interviewer:** Tries?

**Marisol Vance:** Tries. [laughs] It's, I'd say, decent. It's better than it was two years ago. If the vendor puts the PO in a normal place it gets it. If they put it in the body of a paragraph, forget it. Ephesoft kicks anything below — I think it's a seventy-five percent confidence score? Don't quote me. Below that it goes to a validation queue and a human keys it.

**Interviewer:** Who's the human?

**Marisol Vance:** Priya, mostly. Bo does first pass in the morning. Then Ephesoft pushes into NetSuite as a Bill in a pending state. Priya, you want to jump in on entry?

**Priya Raghunathan:** [00:09:40] Yeah. So they land in NetSuite and I work from a saved search — it's called "AP - Bills Pending Review," it's on my dashboard. For a PO invoice I open it, Transactions > Payables > Enter Bills if I'm going in cold, but normally I'm just clicking through from the search. The PO reference populates the lines from the receipt. I check three things: quantity billed against quantity received, unit price against the PO price, and the GL account the item's mapping to. If those all line up it's done in like ninety seconds.

**Interviewer:** And when they don't line up?

**Priya Raghunathan:** That's the exception queue. NetSuite flags it and it goes to a status of, um, "Match Exception - Hold." Then I have to figure out which of the three legs is broken. Usually it's receiving — the goods are physically at the dock but nobody's entered the receipt yet, so I'm billing against nothing. That's probably sixty percent of my exceptions.

**Marisol Vance:** Which is a plant issue, not an AP issue, and I've said that in about six meetings.

**Priya Raghunathan:** [laughs] Second is price. Vendor raised their price, the PO's stale, nobody did a change order. Then I email the buyer and it sits.

**Interviewer:** What's the tolerance on the match?

**Marisol Vance:** Three percent or two hundred fifty dollars, whichever's lower. Under that it auto-releases.

**Priya Raghunathan:** Is it two-fifty? I thought it went up.

**Marisol Vance:** I don't think it went up. Corinne would know — Corinne Baptiste, the Controller. There was a conversation about raising it when we did the NetSuite 2024 upgrade but I don't believe it landed. You should check with Corinne.

**Interviewer:** Noted. Non-PO invoices?

**Marisol Vance:** [00:17:55] Those are the messy ones. Utilities, legal, insurance, the freight bills that don't tie to a PO, anything under our PO threshold. Roughly a quarter of volume. Those Tobias enters — same Enter Bills screen but no PO reference, so he has to code them manually, GL account and department and, we use Class for plant. Then it has to route for approval because there's no PO approval behind it.

**Interviewer:** Route how?

**Marisol Vance:** NetSuite approval routing. Cost center owner approves anything, then it steps up by dollar. Under five thousand it's just the cost center owner. Five to twenty-five, it adds Corinne. Above twenty-five thousand it goes to Emmett — Emmett Suzuki, CFO. Above a hundred it's Emmett plus the board's kind of, no, sorry, above a hundred thousand is Emmett and it gets flagged in the monthly cap-ex review but there's no separate approval.

**Interviewer:** Does that same ladder apply to POs?

**Marisol Vance:** I'd have to check. I think procurement has their own thresholds in Coupa and they're not the same numbers, which has always bugged me. Ask Dev.

**Interviewer:** Let's go to payments.

**Marisol Vance:** [00:24:03] Weekly run. I build the payment proposal in NetSuite Wednesday afternoon — Transactions > Payables > Pay Bills. I filter on due date through the following Friday, plus anything with a discount about to expire. That gives me a proposed list, usually four to six hundred lines, call it two, two and a half million on a normal week.

**Interviewer:** And then?

**Marisol Vance:** I export it to Excel, I look at it, I pull anything that looks wrong. Then Corinne reviews and approves the run. That's a real control — I cannot release my own proposal. Thursday morning I generate the ACH file, it's a NACHA file, and I upload it to Chase Connect. Chase calls it the payments portal, everybody here just says "the portal."

**Interviewer:** Who releases it at the bank?

**Marisol Vance:** I upload, someone else releases. I don't have release entitlement — that's the segregation. Corinne releases, or Renata Kowalczyk in treasury if Corinne's out. Two different Chase Connect user IDs, two different tokens.

**Interviewer:** Is a second approver required on every ACH batch or only above a threshold?

**Marisol Vance:** Every batch. Every single one. That's been true since the — there was an incident in 2022, before my time, someone got phished. Ever since then it's dual on everything.

**Interviewer:** And wires?

**Marisol Vance:** Wires are worse, in a good way. Wire request form — it's a PDF, it lives on the shared drive under Finance/Treasury/Forms — signed by the requester and their VP, then Renata keys it in Chase Connect and Corinne or Emmett approves in the portal. Dual approval in the tool on top of the paper. Cutoff for same-day is 2:00 PM Eastern. We do maybe eight, ten wires a month, mostly overseas tooling vendors and the one German bearing supplier.

**Interviewer:** Positive pay?

**Marisol Vance:** [00:33:20] We still cut checks, sadly. Maybe thirty a week. Check run is Thursday same as ACH, printed on the MICR printer in the AP room, locked drawer for the stock, signature plate is in the safe and only me and Corinne have the combination. Issue file goes to Chase same day, positive pay. Exceptions come back to me in the portal by 10 AM Friday and I have to decide pay or return by 1 PM. If I miss it, default is return. Which has happened. Once.

**Interviewer:** Vendor statements?

**Marisol Vance:** We reconcile statements for our top vendors quarterly. Priya does it. It's on the close calendar for the quarter-end month.

**Priya Raghunathan:** Top fifty by spend. Well — the list is supposed to be top fifty, honestly I work off a list Marisol gave me in, I want to say, 2024? I don't know that it's been refreshed.

**Interviewer:** Biggest pain point, if you could fix one thing?

**Marisol Vance:** Receiving. Full stop. If receipts got entered same day my exception volume drops by half and Priya gets a week of her life back every month. Second thing would be — I'd love an AP automation layer with better OCR and vendor portal self-service so vendors could check their own status instead of calling Bo. We get maybe forty status calls a week.

**Priya Raghunathan:** And the non-PO approvals sitting in people's NetSuite queues for two weeks.

**Marisol Vance:** That too. There's no escalation. It just sits there until someone yells.

**Interviewer:** Great. That's a good stopping point.
