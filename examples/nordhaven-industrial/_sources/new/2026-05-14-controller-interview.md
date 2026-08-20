# Interview — Corporate Controller

**Client:** Nordhaven Industrial Group
**Date:** 2026-05-14
**Location:** Corporate office, Belmont Ridge
**Participants:** Corinne Baptiste (Corporate Controller), Delphine Arceneaux (Assistant Controller) joined ~00:44, Renata Kowalczyk (Treasury Analyst) joined ~00:52
**Interviewer:** Engagement team

---

**Interviewer:** We've spoken to AP and to procurement. I want your view of the control environment and where you think the risk sits.

**Corinne Baptiste:** Sure. Let me frame it. We're not public, but we've got a bank covenant package and a private equity sponsor, so we get an audit and we get a fairly nosy quarterly review. The auditors have three P2P controls in scope: segregation of duties on the vendor master versus payment release, the three-way match, and dual authorization on outbound funds.

**Interviewer:** Take those in order.

**Corinne Baptiste:** [00:03:30] Vendor master. The rule is that nobody who can create or edit a vendor record can release a payment. In NetSuite, Tobias Lindqvist has the vendor maintenance role. Tobias has no payment permissions at all — can't approve a bill, can't touch the Pay Bills screen. Marisol Vance can build a payment run but has no vendor edit rights and no bank release entitlement. I approve the run in NetSuite and I release at Chase. So it's three-way separated, roughly.

**Interviewer:** Roughly?

**Corinne Baptiste:** Roughly because I both approve the run in the ERP and release at the bank, which an auditor has pushed back on twice. My answer is that I'm approving against a proposal I didn't build, and there's a review of the register after. It's a compensating story. It's not a great one.

**Interviewer:** Who else has vendor edit in NetSuite?

**Corinne Baptiste:** Tobias, Delphine has it for emergency, and the NetSuite administrator role — that's our IT person, Gideon Pruitt, plus the implementation partner still has a login I keep meaning to kill. That's on my list.

**Interviewer:** Banking changes specifically.

**Corinne Baptiste:** [00:09:50] Any change to a vendor's remit-to bank account requires a callback to a phone number already on file — not a number in the email requesting the change. The person doing the callback documents it: date, time, who they spoke to, what was confirmed, and that goes as a note plus an attachment on the vendor record in NetSuite. Then a second person approves the change before it goes active.

**Interviewer:** Who does the callback?

**Corinne Baptiste:** Procurement. Dev's team owns the supplier relationship, they've got the real contacts.

**Interviewer:** Dev told us yesterday they thought AP did it — Tobias.

**Corinne Baptiste:** [pause] Huh. Then I don't know that the policy I wrote ever got operationalized. That's — okay, flag that one, I'll go look. It's possible Tobias is doing it and calling me the second approver.

**Interviewer:** Three-way match.

**Corinne Baptiste:** PO, receipt, invoice, all three or the bill doesn't release. Tolerance is where people get fuzzy. It is five percent or five hundred dollars, whichever is less, at the line level.

**Interviewer:** Marisol said three percent, two-fifty.

**Corinne Baptiste:** That was the old number. We raised it — this would have been the 2024 upgrade — because the exception volume was drowning the team. I'm fairly confident it's five and five hundred now. Fairly. Someone should pull the config in NetSuite rather than take my word.

**Interviewer:** Noted. Dual authorization on funds.

**Corinne Baptiste:** [00:19:12] Wires: two approvers in Chase Connect, always, no exception, no dollar floor. Plus a signed wire request form. ACH: the file is uploaded by AP and released by me or Renata. On the batch there's a second approver required above one hundred thousand dollars. Under that a single release is permitted by entitlement.

**Interviewer:** Marisol described it as dual on every batch.

**Corinne Baptiste:** Marisol may be describing practice rather than entitlement. In practice we almost never have a batch under a hundred thousand — the weekly run is two-plus million — so functionally it's always dual. But the control as configured has a threshold. I'd want you to write it the way it's configured, and note that the practice is stricter.

**Interviewer:** Payment run timing?

**Corinne Baptiste:** Proposal Tuesday, my review Wednesday, funding and release Thursday. Settlement Friday.

**Interviewer:** Marisol said proposal Wednesday, release Thursday.

**Corinne Baptiste:** Then Marisol's a day later than I think and I'm reviewing it the same morning I release it, which if true is a finding. Please check the actual calendar with them.

**Interviewer:** Positive pay?

**Corinne Baptiste:** [00:26:40] Issue file transmits to Chase from NetSuite at check print. Exceptions come back next business morning. Marisol reviews and dispositions. Default on no-decision is return, which we set deliberately. We also have ACH debit block on the operating account with a filter list — only two vendors are authorized to debit us, the payroll processor and the health plan. Everything else bounces.

**Interviewer:** Bank reconciliation?

**Corinne Baptiste:** Delphine's team, monthly, in NetSuite, with a five-day close deadline. Delphine, you want to speak to that?

**Delphine Arceneaux:** [00:44:30] Yeah. Chase feeds transactions into NetSuite daily and we match against the payment register. Unreconciled items over thirty days go on an exception schedule that I review with Corinne. Most of what's aged is stale checks — we escheat annually, which is its own headache.

**Interviewer:** Vendor statement reconciliation — cadence?

**Corinne Baptiste:** The SOP says monthly for all significant vendors. I know it's not happening monthly. My understanding is AP does it quarterly for the top vendors, which I have accepted because I don't have the headcount to insist otherwise. If you ask Dev, Dev will tell you it doesn't happen at all, and Dev might be right for some quarters.

**Interviewer:** Accruals at month end?

**Corinne Baptiste:** [00:33:15] Two pieces. Received-not-invoiced comes off a NetSuite saved search of open receipts with no bill — that's a systematic accrual, journal posts on day two of close. Then there's a manual accrual for known-not-received, which is Delphine chasing department heads by email for a list of "what did you commit to that hasn't hit." That second one is the weak spot. It's a spreadsheet, it lives on the shared drive, and the population is whoever answers the email.

**Interviewer:** T&E — where does that sit?

**Corinne Baptiste:** Concur, and I want to be clear, we do not consider that part of procure-to-pay. It's an employee reimbursement process, it's owned by the same AP team operationally but we file it under Travel & Expense in our own process map, and it reimburses through payroll's ACH file, not through the AP payment run. Different bank account, even.

**Interviewer:** Who approves expense reports?

**Corinne Baptiste:** Direct manager, then Concur audit rules flag anything over seventy-five dollars without a receipt, any meal over a hundred a head, and all airfare. Flagged reports get a manual review by — Renata, is that you or is that Bo?

**Renata Kowalczyk:** [00:52:05] Bo Whitfield does the Concur audit queue. I only get involved on the corporate card side, disputes and the monthly card reconciliation.

**Interviewer:** Corinne, if you could change one thing?

**Corinne Baptiste:** [00:57:40] Get receipts entered at the dock in real time. Everything downstream of that is symptom. Second, I want the vendor banking change control actually operating the way it's written, with evidence I can hand an auditor without three emails first. Third — and this is the unglamorous one — I want somebody to own the vendor master as a real job, not as a thing Tobias does between other things. Eleven thousand records, no owner, is how you end up on the front page.

**Interviewer:** Anything you'd expect us to find that you haven't said?

**Corinne Baptiste:** I'd expect you to find that the documented SOP and what people actually do have drifted a long way apart. The AP SOP is version three, it's from 2023, it predates the NetSuite upgrade. Read it, but don't believe it.
