# Field notes — P2P, Nordhaven

wk of 5/18, misc. Not cleaned up. Mine only.

---

**Systems (confirmed)**
- Coupa = req/PO/supplier onboarding. SIM portal for supplier self-reg.
- NetSuite = GL, vendor master (payment side), item receipt, bill, pay bills, bank rec
- Concur = T&E only. Client insists NOT P2P — files under Travel & Expense. Reimb via payroll ACH, sep acct. Note for taxonomy: out of L1.
- Ephesoft = OCR/capture. "the OCR thing"
- Chase Connect = "the portal". ACH upload, wire init, pos pay exceptions, ACH debit block/filter
- shared mbx ap-invoices@ (Outlook). "AP Inbox"
- nightly Coupa→NS supplier sync. Breaks sometimes → blank pmt terms, Tobias fixes manually. No monitoring/alert on the sync?? nobody could name an owner

**Volumes (rough, unvalidated)**
- ~4,800 invoices/mo?? Marisol said "about that" — DID NOT CONFIRM. get from NS
- ~25% non-PO
- 30 checks/wk, 8-10 wires/mo
- wkly ACH run $2-2.5M, 400-600 lines
- 11k supplier records, ~4k active 24mo
- ~15-20 confirming POs/mo, concentrated Plant 2
- req→PO median 6.5 days per Dev. Source = Dev's own spreadsheet, not a system report. treat as soft
- 40 vendor status calls/wk to AP → self-service opportunity

**People**
- Marisol Vance AP Mgr — owns pmt run build, pos pay dispo, sig plate combo
- Priya Raghunathan Sr AP Spec — PO inv entry, match exceptions, stmt recs
- Tobias Lindqvist AP Clerk / vendor master — non-PO entry too. SoD question: vendor master AND non-PO invoice entry in one pair of hands. FLAG.
- Bo Whitfield AP Clerk PT — inbox triage, scanning, Concur audit queue
- Dev Anand Rao Proc Lead
- Yusuf Adeyemi Buyer P2/P3
- Corinne Baptiste Controller
- Delphine Arceneaux Asst Controller — bank rec, manual accrual
- Renata Kowalczyk Treasury Analyst — wire entry, corp card
- Hal Ostrowski Recv Supv P2
- Emmett Suzuki CFO
- Gideon Pruitt IT / NS admin. Has vendor edit via admin role. Also legacy impl partner login still live — Corinne aware, unremediated

**Open conflicts — need resolution**
1. 3-way match tolerance. SOP v3 = 5% / $100 lesser. Marisol = 3% / $250. Corinne = 5% / $500 "fairly confident". Hal thinks $500 for over-receipt (diff control, he may be conflating). → PULL THE NS CONFIG. nobody has actually looked.
2. Non-PO invoice approval ladder. Marisol: <5k CC owner / 5-25k +Controller / >25k CFO. SOP: 2.5k / 10k / 50k w/ VP layer. Different in both breakpoints AND approver set. Which is live in NS workflow?
3. PO req threshold to CFO. Dev = $25k. Corinne implied 50k in passing (didn't press, my fault). Marisol didn't know. Also: is req ladder same as non-PO invoice ladder? Dev says no, deliberately. Corinne didn't seem to know they differ.
4. ACH 2nd approver. Marisol: every batch, no floor, post-2022 phishing incident. Corinne: entitlement threshold at $100k, practice is stricter b/c batches always exceed. → get Chase entitlement report.
5. Pmt run calendar. Marisol: propose Wed / release Thu. Corinne: propose Tue / review Wed / release Thu. SOP: propose Mon / release Wed. Three different answers. Corinne flagged that if Marisol's right, Corinne reviews + releases same morning = finding.
6. Vendor banking change callback owner. Corinne says procurement. Dev says AP (Tobias). SOP 9.4 says AP Specialist. Corinne appeared surprised — policy may never have been operationalized. Also unclear who the 2nd approver on the change actually is; Corinne speculated it's her.
7. Stmt recon cadence. SOP = monthly, all vendors >$50k spend. Corinne = quarterly top vendors, accepted. Priya = works off a list from ~2024, never refreshed, thinks it's top 50. Dev = "I'd be surprised if it's real."
8. Ephesoft confidence threshold. SOP = 90%. Marisol = "seventy-five? don't quote me." → check Ephesoft config

**Thin / TBD — insufficient to document**
- Services PO receipting. Hal: "not my dock," dept does it in NS, "don't know how well it works." NOBODY owns this. No process described by anyone. TBD.
- Plant 3 Kanban / consumption-based auto-receipt w/ 2 steel suppliers. Hal can't explain, deferred to Yusuf, Yusuf not re-interviewed. TBD — may be a distinct L3 or a variant.
- Over-receipt tolerance. Hal ~10% + a dollar cap, unsure. Not in SOP excerpt. TBD.
- RMA → vendor credit memo. Hal does the RA in NS, then "AP chases that, I think." No one described the credit application step. Gap.
- Blanket PO NTE burn-down. Coupa report exists, Yusuf says nobody runs it on a schedule. No owner, no cadence. TBD.
- Escheatment of stale checks — Delphine mentioned "annually," no detail, out of scope? probably R2R
- Manual/emergency check issuance. SOP 7.5 says Controller written auth. No one described it happening. Did not ask frequency. TBD.
- Intercompany — explicitly out of SOP scope, didn't probe. Assume out.
- Freight bills / collect shipments — Hal: "whole conversation about who authorized collect." No process. Non-PO bucket by default?

**Controls inventory (draft)**
- SoD vendor master vs pmt release — 3-way split Tobias / Marisol / Corinne. BUT Corinne both approves NS run and releases at Chase. Auditor pushback x2, compensating = post-hoc register review. Weak.
- 3-way match w/ tolerance (value TBD, see #1)
- Dual auth wires, no floor, + signed paper form (shared drive Finance/Treasury/Forms)
- ACH upload ≠ ACH release (Marisol uploads, Corinne/Renata release)
- Positive pay, issue file at print, default-return on no decision. Dispo deadline 1PM Fri.
- ACH debit block + filter, 2 authorized originators (payroll processor, health plan)
- Duplicate invoice constraint vendor+inv# in NS
- Bank rec monthly, 5-day close, >30d unreconciled to exception sched reviewed w/ Corinne
- RNI systematic accrual off NS saved search, posts close day 2
- Vendor banking callback (owner TBD, see #6)
- Supplier master file review semi-annual per SOP 9.5 — ASKED NOBODY. no evidence it happens.
- Approval escalation @3 biz days per SOP 6.4 — Priya says approvals sit 2 wks, "no escalation, it just sits there." So either not configured or not working. Contradiction w/ SOP.

**Pain points voiced**
- late receipts → ~60% of match exceptions (Priya). root cause of most downstream noise. Marisol + Corinne + Hal all independently named it #1.
- Hal wants handheld scanners, ~$60k, cut 2y ago
- dup vendors (Dev) — no dedup project, no owner
- stale punchout catalog pricing → off-contract buying (Yusuf)
- confirming PO leakage, no metric (Dev)
- Coupa↔NS sync failures, 3 people × 1hr each time
- non-PO approvals parked in queues
- "the cage" at P2 — ~30 unidentified pallets, some since fall '25. direct-to-vendor calls.
- 40 status calls/wk → vendor self-serve portal idea
- Dev's ask: auto-approve catalog reqs <$1k against contract price = ~1/3 of volume out of chain

**Evidence / retention**
- inv image attached to NS bill, 7 yrs per SOP
- OFAC screenshot + TIN match attached to Coupa supplier record
- W-9, insurance certs, banking: supplier-entered in Coupa SIM
- callback note + attachment on NS vendor record
- packing slips: PAPER ONLY, receiving file cabinet by month ~2yrs then storage container. never scanned. audit risk.
- wire request form PDF signed → shared drive
- pmt proposal export to Excel — where saved? didn't ask. Corinne said "evidence of approval retained," didn't say where.
- stmt recon worksheet → shared drive per SOP 9.2. existence unverified.

**Next**
- re-interview Yusuf (P3 Kanban, over-recv tol, blanket NTE)
- get NS: approval workflow config, match tolerance, saved searches
- get Chase entitlement matrix
- get Coupa approval chain export
- ask Gideon re: role matrix + legacy partner login
- somebody needs to walk a services PO end to end
