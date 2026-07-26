# Interview — Procurement Lead

**Client:** Nordhaven Industrial Group
**Date:** 2026-05-13
**Location:** Teams (Dev remote from Plant 3 that week)
**Participants:** Dev Anand Rao (Procurement Lead), Yusuf Adeyemi (Buyer, Plants 2 & 3) joined at ~00:31
**Interviewer:** Engagement team

---

**Interviewer:** Let's start with vendor onboarding, since that's upstream of everything.

**Dev Anand Rao:** Okay. So a requester — could be a plant maintenance planner, could be an engineer, could be somebody in marketing — needs something from a supplier we've never used. They can't just requisition it, the vendor has to exist in Coupa and in NetSuite first.

**Interviewer:** Two systems.

**Dev Anand Rao:** Two systems, yeah, and they're integrated but not, like, beautifully. Coupa is the system of record for the supplier record from a sourcing standpoint. NetSuite is the system of record for the vendor master for payment purposes. There's a nightly sync that pushes new suppliers from Coupa into NetSuite. It's, uh, it works. Mostly. Sometimes a record lands with a blank payment term and Tobias fixes it by hand.

**Interviewer:** Walk me through the request.

**Dev Anand Rao:** [00:05:50] The requester fills out a New Supplier Request form. It's a Coupa form, we built it — supplier legal name, DBA, remit-to address, W-9 attached, contact, and there's a mandatory question about whether they're a related party. That comes to me or Yusuf depending on the plant. We do the diligence: verify the W-9 name matches the TIN through the IRS TIN match, run them against the OFAC SDN list — that's a manual lookup on the Treasury site, we screenshot the result and attach it — and check for duplicates against the existing supplier list.

**Interviewer:** Duplicates being a problem?

**Dev Anand Rao:** Enormous problem. We've got, I want to say, eleven thousand supplier records and maybe four thousand are actually active in the last two years. There are vendors in there four times with different spellings. It's on my list. It's been on my list a while.

**Interviewer:** After diligence?

**Dev Anand Rao:** Then it goes to the supplier for onboarding. Coupa sends them a Supplier Information Management invite, they self-register — they enter their own banking, W-9, insurance certs, diversity classification. That's actually the one part of this I like, because the banking comes from the supplier directly, we're not keying it off an emailed PDF.

**Interviewer:** Who approves the new supplier?

**Dev Anand Rao:** I approve it in Coupa. If it's a supplier we expect to spend over — I think it's two-fifty a year, two hundred fifty thousand — then Corinne has to approve too. And then the record syncs to NetSuite overnight and Tobias activates it, sets the payment terms, default GL. Standard terms are net 45, we push for net 60 on new ones.

**Interviewer:** Banking changes on existing vendors?

**Dev Anand Rao:** [00:14:15] That's a big one. Vendor emails saying "we changed banks." Those go to AP, and AP does — hmm. Honestly I don't know the current state of that. I know there's a callback requirement. Whether AP owns it or we own it, that's murky. I think Tobias makes the call to a number on file. Not a number from the email — from the file. That's the whole point. But I've also heard Corinne say procurement should own banking changes because we own the supplier relationship, and I don't think that ever actually got implemented.

**Interviewer:** So today it's AP?

**Dev Anand Rao:** Today I believe it's Tobias, yeah. You should confirm.

**Interviewer:** Requisitions.

**Dev Anand Rao:** [00:19:02] Coupa. Requester goes in, there are three paths. Catalog items — we've got hosted catalogs and punchout for Grainger-equivalent MRO stuff, the industrial distributor, and for IT. Punchout is easy, they shop, they come back with a cart, it's a req. Second is a non-catalog request, free text, they type what they want and pick a supplier. Third is a services request, which uses a different form because it needs a statement of work attached.

**Interviewer:** Approval flow?

**Dev Anand Rao:** Coupa approval chains. Cost center manager always. Then dollar thresholds. Under two thousand, cost center manager only. Two to twenty-five thousand adds the functional VP. Over twenty-five thousand it goes to the CFO, Emmett. And anything cap-ex has to have an approved AFE — authorization for expenditure — number in a custom field before it'll route at all.

**Interviewer:** Over twenty-five is CFO?

**Dev Anand Rao:** Yeah, twenty-five.

**Interviewer:** Okay, I'd asked Marisol yesterday and got something a little different. We'll reconcile.

**Dev Anand Rao:** AP's ladder is for non-PO invoices, that's a different chain, they might not match. That's a fair criticism of us.

**Interviewer:** PO issuance?

**Dev Anand Rao:** Once fully approved Coupa cuts the PO and transmits it. Most suppliers get it by cXML if they're enabled — maybe sixty of them — the rest get a PDF by email. PO number format is NIG- and then a sequential. Then it syncs into NetSuite so AP has something to match against.

**Interviewer:** Change orders?

**Dev Anand Rao:** [00:27:40] Requester or buyer edits the PO in Coupa, it creates a version 2, and it re-routes for approval if the change increases the value. If it decreases, it doesn't re-route. If it increases by less than ten percent it — I want to say it only goes back to the cost center manager, not the whole chain. Yusuf, do you know that one?

**Yusuf Adeyemi:** [00:31:10] It re-routes to whoever the new dollar value hits. So if you were at twenty-four and you go to twenty-eight, congratulations, now you need Emmett. If you were at twenty-four and you go to twenty-six, same thing.

**Dev Anand Rao:** Okay, so I was wrong, there's no ten percent grace.

**Yusuf Adeyemi:** I'm like eighty percent sure. I've never actually read the config.

**Interviewer:** Blanket POs?

**Yusuf Adeyemi:** We use them for the recurring stuff — janitorial, the gas supplier, the tooling consignment. Annual not-to-exceed, released against by receipt. The problem is nobody watches the burn-down, so we hit the NTE in month nine and everything blocks and I get four angry calls in one afternoon. There's a Coupa report for it. I don't think anyone runs it on a schedule.

**Interviewer:** Emergency or after-the-fact POs?

**Dev Anand Rao:** [00:36:22] Happens. Plant's down, maintenance calls a vendor, vendor shows up, does the work, sends an invoice. No PO. Then AP kicks it back and we have to create a PO after the fact. We call it a confirming PO. It's supposed to require a written justification from the plant manager. In practice it requires an email from anyone. I'd guess we do fifteen, twenty a month, mostly Plant 2.

**Interviewer:** Does anyone track that as a metric?

**Dev Anand Rao:** No. I mean — no. I've got a spreadsheet. That's not tracking.

**Interviewer:** Statement reconciliation — does procurement touch that?

**Dev Anand Rao:** No, that's AP. And honestly I'm not sure it happens at all. I've never been shown a reconciled statement. I'd be surprised if it's a real monthly process.

**Interviewer:** Pain points?

**Dev Anand Rao:** [00:41:05] One, the duplicate vendor mess. Two, cycle time — median req to PO is, last I measured, six point five days, and about five of those are approvals sitting. Three, the confirming PO leakage, because it means we're spending money outside the process and I have no leverage on price. Four, honestly, Coupa-to-NetSuite. Every time something doesn't sync, three people spend an hour on it.

**Yusuf Adeyemi:** And the catalogs are stale. Half the punchout pricing doesn't reflect the negotiated contract, so people buy off-contract without knowing.

**Interviewer:** Improvement ideas?

**Dev Anand Rao:** Auto-approve low-dollar catalog reqs under, say, a thousand, against a contracted price. That would take maybe a third of the volume out of the approval chain. And a real supplier de-duplication project. And someone to own the NTE burn-down report.

**Interviewer:** Thanks — very helpful.
