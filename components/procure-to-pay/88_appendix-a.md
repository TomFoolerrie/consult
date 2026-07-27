## Appendix — Pain Points & Improvement Opportunities

<!-- derived: appendix-a; writer: python -->

_Pain points and improvement opportunities observed in the current-state walkthroughs, with the impact and severity recorded for each. Each pain point is shown alongside the improvement opportunities that address it. IDs are numbered sequentially through the document; items are grouped by sub-process._


#### Vendor Management

**PP-01 ([[#new-vendor-onboarding]]) — Severity: High**

The supplier master is heavily duplicated, which undermines the duplicate check this procedure depends on. The Procurement Lead described the duplicate population as an "enormous problem" that has been on his list for some time, with no de-duplication project, no cadence and no named owner (SRC-002, SRC-005). The prior SOP requires a semi-annual review of the supplier master file for inactive, duplicate and incomplete records, reported to the Corporate Controller (§9.5 of the prior SOP, SRC-006); no interviewee produced evidence that this review takes place. The Corporate Controller separately identified unowned vendor master data as one of three things she would change (SRC-003).

*Impact:* The duplicate check at diligence is performed against an unreliable population, so new duplicates continue to be created; duplicate records also raise the risk of duplicate payment and distort spend analysis.

**Improvement IO-01:** Run a supplier de-duplication and deactivation project across the existing master, and assign a named owner accountable for the ongoing supplier master file review the prior SOP already requires. *(also addresses PP-03)*

**PP-02 ([[#new-vendor-onboarding]]) — Severity: Medium**

The nightly Coupa-to-NetSuite supplier sync fails intermittently and has no monitoring or owner. Records land in NetSuite with blank payment terms and are corrected manually by the Accounts Payable Clerk (SRC-002). Each sync failure is described as consuming roughly an hour of three people's time, and no interviewee could identify monitoring, alerting or an owner for the interface (SRC-005). See GAP-03.

*Impact:* New suppliers can sit unusable or incorrectly configured until someone notices; recurring unplanned effort across procurement, AP and IT.

**Improvement IO-02:** Establish monitoring and alerting on the nightly Coupa-to-NetSuite supplier sync with a named owner, so failed or incomplete records are detected rather than found in use.

**PP-03 ([[#new-vendor-onboarding]]) — Severity: High**

Vendor master maintenance and non-PO invoice entry are performed by the same role. Segregation as designed separates vendor maintenance from payment preparation, approval and bank release (§9.3 of the prior SOP, SRC-006; SRC-003). The working notes flag that the same individual holding the Vendor Maintenance role also performs non-PO invoice entry, which places creation of the payee and creation of the payable in one pair of hands (SRC-005).

*Impact:* A payee and a payable to that payee can be originated by the same role, reducing the assurance provided by CTRL-005.

**Improvement IO-01:** Run a supplier de-duplication and deactivation project across the existing master, and assign a named owner accountable for the ongoing supplier master file review the prior SOP already requires. *(also addresses PP-01)*

**PP-04 ([[#vendor-banking-change]]) — Severity: High**

The banking change control is not demonstrably operating as written, and no source could confirm who performs it. The Corporate Controller assigns the callback to procurement, the Procurement Lead believes the Accounts Payable Clerk performs it, and the prior SOP assigns it to an Accounts Payable Specialist (SRC-003, SRC-002, §9.4 of the prior SOP, SRC-006). Told of the conflict, the Corporate Controller responded that she did not know the policy she wrote had ever been operationalized (SRC-003). The working notes carry the same item as an open conflict with the second approver also unresolved (SRC-005). See GAP-05 and GAP-06.

*Impact:* A remit-to banking change — the highest-value target for payment fraud in the process — rests on a control with no confirmed performer, no confirmed second approver, and therefore no assurance that the callback occurs before funds are redirected.

**Improvement IO-03:** Assign a single named owner for the callback verification and a named second approver, and confirm both against the NetSuite and Coupa entitlements actually in force.

**PP-05 ([[#vendor-banking-change]]) — Severity: Medium**

Evidence of the banking change control cannot be produced on demand. She stated that she wants the vendor banking change control operating the way it is written, "with evidence I can hand an auditor without three emails first" (SRC-003). The callback evidence is a free-form note plus attachment on the vendor record, with no standard form and no described completeness check (SRC-003, SRC-005).

*Impact:* Audit and quarterly review effort is expended reconstructing whether the control operated; an omitted note cannot be distinguished from an omitted callback.

**Improvement IO-04:** Standardize the callback evidence as a structured record on the vendor record — date, time, person spoken to, confirmation, performer, approver — so that the control can be evidenced without reconstruction.

**PP-06 ([[#vendor-banking-change]]) — Severity: High**

Banking change requests are accepted as inbound email rather than through an authenticated supplier channel. The Procurement Lead contrasted the two directly, describing supplier self-entry of banking in the SIM portal as the part of onboarding he likes precisely because "we're not keying it off an emailed PDF," while describing banking changes as arriving as a "vendor emails saying 'we changed banks'" (SRC-002). No source states whether the SIM portal supports a banking change on an existing supplier. See GAP-04.

*Impact:* The Company keys bank account details from an unauthenticated inbound message, leaving the telephone callback as the sole barrier to a fraudulent redirection.

**Improvement IO-05:** Route banking changes on existing suppliers through the Coupa Supplier Information Management portal, so the new account is entered by the authenticated supplier rather than keyed from an email.

**PP-07 ([[#vendor-master-data-maintenance]]) — Severity: High**

The vendor master has no named owner. The Corporate Controller named unowned vendor master data as one of three things she would change, describing it as "a thing [the clerk] does between other things" and observing that "eleven thousand records, no owner, is how you end up on the front page" (SRC-003). The working notes record the same clerk holding both vendor master maintenance and non-PO invoice entry as a segregation-of-duties flag (SRC-005). No intake channel, work queue or service level for maintenance requests was described by any source. See GAP-08.

*Impact:* Master data quality degrades unchecked; defects are corrected reactively when a record is found unusable rather than through any owned process.

**Improvement IO-06:** Assign a named owner for the vendor master with a defined intake channel for maintenance requests, and re-establish the periodic master file review on a scheduled basis with retained evidence of performance and of the results reported to the Corporate Controller. *(also addresses PP-08)*

**PP-08 ([[#vendor-master-data-maintenance]]) — Severity: High**

The supplier master file review required by the prior SOP does not demonstrably operate. The requirement is stated at §9.5 of the prior SOP (SRC-006); the working notes record it as untested with no evidence of performance (SRC-005). In its absence the duplicate population persists — approximately 11,000 records against approximately 4,000 active in the last two years, with the same vendor present multiple times under different spellings (SRC-002). See GAP-10.

*Impact:* Inactive, duplicate and incomplete records accumulate, raising the risk of duplicate payment and payment to a stale remit-to, and distorting spend analysis; a documented control is not operating.

**Improvement IO-06:** Assign a named owner for the vendor master with a defined intake channel for maintenance requests, and re-establish the periodic master file review on a scheduled basis with retained evidence of performance and of the results reported to the Corporate Controller. *(also addresses PP-07)*

**Improvement IO-07:** Run a one-time supplier de-duplication and deactivation exercise across the existing master to bring the population to the active record set, with a documented disposition method for duplicates and inactive records.

**PP-09 ([[#vendor-master-data-maintenance]]) — Severity: High**

Vendor edit capability in NetSuite is broader than the Vendor Maintenance role, including a legacy third-party login. Vendor edit rights in NetSuite are held by the Accounts Payable Clerk, by the Assistant Controller for emergency use, by the NetSuite administrator role held by the IT Manager, and by the implementation partner, whose login remains live; the Corporate Controller is aware of the partner login and described removing it as outstanding (SRC-003, SRC-005). No periodic access review of the vendor maintenance entitlement was described.

*Impact:* The population able to create or alter a payee is larger than the control described to the auditors, and includes an external party outside the Company's segregation model.

**Improvement IO-08:** Perform a periodic access review of vendor edit entitlement in NetSuite and remove the legacy implementation partner login.

**PP-10 ([[#vendor-master-data-maintenance]]) — Severity: Medium**

Records arriving from the nightly Coupa-to-NetSuite sync require manual repair.

*Impact:* Maintenance effort is consumed correcting defects originated upstream, and a defective record can remain in use until noticed.

_No improvement opportunity recorded for this pain point._

#### Procurement

**PP-11 ([[#requisition-and-approval]]) — Severity: High**

Requisition-to-PO cycle time is dominated by approvals waiting in queues. The figure comes from the Procurement Lead's own measurement and was volunteered as the second of his four pain points (SRC-002). The working notes record that the measurement derives from a manually maintained spreadsheet rather than a system report and should be treated as soft (SRC-005).

*Impact:* Delivery of goods and services is delayed by approval latency rather than by sourcing or supplier lead time, and the delay is not measured from any system of record.

**Improvement IO-09:** Introduce automatic approval of low-value catalog requisitions — for example below $1,000 — where the line transacts at a contracted price, removing an estimated one third of requisition volume from the approval chain.

**PP-12 ([[#requisition-and-approval]]) — Severity: Medium**

Punchout and hosted catalog pricing is stale relative to negotiated contracts. The Buyer stated that roughly half of punchout pricing does not reflect the negotiated contract, so requesters buy off-contract without knowing (SRC-002). No catalog refresh cadence or owner was described by any source.

*Impact:* Negotiated pricing is not realised on catalog spend, and the leakage is invisible to the requester at the point of purchase.

**Improvement IO-10:** Establish a scheduled refresh and a named owner for hosted catalog and punchout pricing, so that catalog prices reconcile to the negotiated contract.

**PP-13 ([[#po-issuance-and-change-orders]]) — Severity: High**

Failures of the Coupa-to-NetSuite integration are detected by their downstream symptoms rather than by monitoring, and have no owner. The Procurement Lead named Coupa-to-NetSuite synchronization as one of his four pain points, stating that every time something does not sync, three people spend an hour on it (SRC-002). The working notes record that the nightly synchronization breaks intermittently, that records land incomplete and are corrected by hand, and that nobody could name an owner or any monitoring or alerting over it (SRC-005).

*Impact:* A purchase order that does not reach NetSuite blocks receipt and invoice matching until somebody notices downstream, and the remediation effort is unplanned and undirected.

**Improvement IO-11:** Assign a named owner to the Coupa-to-NetSuite integration and implement failure alerting, so that a purchase order or supplier record that does not synchronize is detected at the integration rather than by the receiving dock or Accounts Payable.

**PP-14 ([[#po-issuance-and-change-orders]]) — Severity: Medium**

The change order re-approval rule is not documented and the Coupa configuration governing it has never been read. The Procurement Lead stated there was a grace band below approximately 10% that returns the revision only to the Cost Center Manager, then accepted the Buyer's contrary account that routing follows the new dollar value; the Buyer put his own confidence at approximately 80% and stated he had never read the configuration (SRC-002). The Coupa approval chain export remains outstanding (SRC-005). The conflict is logged as GAP-18.

*Impact:* Buyers cannot predict what a revision will require, and no party can assert that value-increasing amendments are approved at the correct level.

**Improvement IO-12:** Extract the Coupa approval chain configuration and document the change order re-approval rule, including the receiving tolerance that forces a change order, so that both are stated from the system of record rather than from recollection.

**PP-15 ([[#confirming-po]]) — Severity: High**

Commitments are made outside the procurement process at a rate of roughly 15–20 per month, concentrated at Plant 2, and the volume is not tracked as a metric. The Procurement Lead describes the pattern as a plant going down, maintenance calling a vendor direct, the vendor performing the work and invoicing with no purchase order in place (SRC-002). Volume is estimated at 15–20 per month, concentrated at Plant 2 (SRC-002, SRC-005). Asked whether the volume is tracked as a metric, the Procurement Lead confirmed it is not, noting only a personal spreadsheet. The consequence named is loss of price leverage, because the commitment is made before procurement is involved.

*Impact:* Spend is committed outside the process with no negotiated price and no competitive leverage; the scale of the leakage is not measured.

**Improvement IO-13:** Track confirming purchase orders as a reported metric — volume, value, plant and requesting department — from Coupa rather than a personal spreadsheet, and review the trend with plant leadership.

**PP-16 ([[#confirming-po]]) — Severity: Medium**

The stated requirement for a Plant Manager written justification is not enforced; an email from any requester is accepted.

*Impact:* The only preventive control over after-the-fact commitments operates as a formality, providing no accountability at the plant for bypassing the process.

**Improvement IO-14:** Enforce the justification requirement by routing every confirming purchase order for Plant Manager approval in Coupa, so the justification is captured on the transaction rather than in email.

**PP-17 ([[#confirming-po]]) — Severity: High**

Delivered goods that cannot be tied to a purchase order accumulate in the segregated receiving area at Plant 2 and are not cleared. The Receiving Supervisor describes a fenced area in the back corner of the receiving floor holding anything that cannot be tied to a purchase order until somebody claims it, estimating roughly 30 pallets at the time of the walkthrough with some material held since the previous autumn (SRC-004, SRC-005). The Receiving Supervisor attributes the contents to people calling a vendor direct without a requisition. No clearing routine, ageing review or owner for the held material was described by any source.

*Impact:* Material that has been delivered and will be invoiced is neither received nor available for use; the associated liability is unrecorded until the confirming purchase order is raised.

**Improvement IO-15:** Establish an owner and a periodic ageing review for material held in the segregated receiving area, so held items are claimed, converted to a confirming purchase order or returned rather than accumulating.

**PP-18 ([[#blanket-po-management]]) — Severity: High**

The not-to-exceed burn-down is not monitored, so an approaching ceiling is discovered only when releases block. The Buyer described hitting the not-to-exceed value in month nine, everything blocking, and taking four angry calls in one afternoon, and stated that although a Coupa report for the burn-down exists he did not think anyone runs it on a schedule (SRC-002). The working notes confirm that there is no owner and no cadence for the report (SRC-005). The consequence is that a preventive ceiling working exactly as designed is experienced as an unplanned outage in recurring supply.

*Impact:* Recurring supply for categories such as janitorial services, gas and tooling consignment stops without warning, and the remediation is handled reactively under escalation.

**Improvement IO-16:** Assign a named owner to the Coupa not-to-exceed burn-down report and run it on a defined cadence, with a threshold at which the Buyer acts on a blanket purchase order approaching its ceiling — an action the Procurement Lead himself identified as needed.

#### Receiving

**PP-19 ([[#goods-receipt]]) — Severity: High**

Receipts are entered late, so goods are physically on site while the purchase order shows nothing received. Same-day entry is the target and is generally achieved by first shift on a normal day, but second shift performs the physical put-away and leaves the keying for the following morning, so a delivery arriving one afternoon may not appear in NetSuite two days later; the Receiving Supervisor attributes this to staffing — two receivers on first shift and one on second — and states he has no additional person (SRC-004). The Senior Accounts Payable Specialist attributes approximately 60% of her match exceptions to receipts not yet entered, and the Accounts Payable Manager states that same-day receipting would halve exception volume (SRC-001, SRC-005). The Receiving Supervisor further notes that a portion of the inventory cycle-count variance, against accuracy of roughly 96–97%, traces back to receipts entered late or entered wrong (SRC-004).

*Impact:* Bills are matched against nothing and route to Match Exception - Hold, consuming Accounts Payable capacity, delaying supplier payment and contributing to inventory record inaccuracy.

**Improvement IO-17:** Deploy handheld barcode scanners at the dock that read the supplier barcode from the packing slip and post the item receipt at the door, removing the deferred keying step that drives late receipts. *(also addresses PP-21)*

**Improvement IO-20:** Measure and report the elapsed time between physical delivery and item receipt entry by plant and shift, so that the receipting lag driving downstream match exceptions is visible rather than inferred from Accounts Payable exception volume.

**PP-20 ([[#goods-receipt]]) — Severity: High**

Deliveries that cannot be tied to a purchase order accumulate indefinitely in the cage with no disposition process. The Receiving Supervisor describes the cage as holding anything that cannot be tied to a purchase order until somebody claims it, estimates approximately thirty pallets, and states that some has been there since the previous autumn (SRC-004). He attributes the material to buyers or departments contacting a supplier directly without raising a requisition, and the working notes record the cage among the pain points voiced, with the same root cause (SRC-005). No source describes any review, ageing report, escalation or write-off of cage material.

*Impact:* Material that has been paid for or will be invoiced sits unreceived and off the books, inventory is understated, and the underlying off-process buying goes undetected.

**Improvement IO-18:** Prevent direct supplier ordering outside the requisition process, so that material cannot arrive without a purchase order to receive it against, and establish an ageing review and disposition rule for material already held in the cage.

**PP-21 ([[#goods-receipt]]) — Severity: Medium**

Packing slips exist only on paper and are never imaged, so the primary evidence of what was physically received is not retrievable outside the receiving office. The Receiving Supervisor states that packing slips are paper only, filed by month in the receiving file cabinet for approximately two years before moving to the storage container out back, and that although scanning them into the imaging system had been discussed it never happened (SRC-004). The working notes carry the same item under evidence and retention and flag it explicitly as an audit risk (SRC-005). Retrieval of a packing slip to resolve an invoice match exception therefore requires a physical search at the plant.

*Impact:* Receipt evidence cannot be produced remotely or attached to the transaction, match exception research is slow, and there is no protection against loss or destruction of the only copy.

**Improvement IO-17:** Deploy handheld barcode scanners at the dock that read the supplier barcode from the packing slip and post the item receipt at the door, removing the deferred keying step that drives late receipts. *(also addresses PP-19)*

**Improvement IO-19:** Scan packing slips into the document capture application already used for supplier invoices and attach the image to the NetSuite item receipt, making receiving evidence retrievable with the transaction.

**PP-22 ([[#return-to-vendor]]) — Severity: High**

No one tracks whether the supplier credit expected after a return is ever received. The Receiving Supervisor stated that a credit memo is supposed to follow the return, that whether the credit ever shows up is not something he tracks, and that he believes Accounts Payable chases it (SRC-004). The working notes record the return-to-credit handoff as insufficiently supported to document, noting that the Return Authorization is raised in NetSuite and that no one described the credit application step (SRC-005). No monitoring, ageing report or reconciliation of open returns against credits received was described by anyone.

*Impact:* Credits due on returned material may never be received or applied, and the exposure is not quantified because open returns awaiting credit are not visible in any report.

**Improvement IO-21:** Establish and assign ownership of the credit recovery step, supported by a report of Return Authorizations with no matching supplier credit, so that returns awaiting credit are aged and pursued rather than assumed.

#### Invoice Processing

**PP-23 ([[#invoice-intake-and-capture]]) — Severity: Medium**

Purchase order reference extraction is unreliable where the supplier prints the PO number inside body text rather than in a conventional position on the invoice face.

*Impact:* Affected invoices drop to the manual validation queue for hand-keying, consuming Accounts Payable Clerk and Senior Accounts Payable Specialist time daily. (SRC-001)

**Improvement IO-22:** Introduce an accounts payable automation layer with improved OCR extraction, so that purchase order references are recognized reliably regardless of placement on the invoice face.

**PP-24 ([[#invoice-intake-and-capture]]) — Severity: Medium**

Suppliers have no means of checking invoice or payment status themselves, and telephone the Accounts Payable team instead.

*Impact:* Approximately forty status calls per week are absorbed by the Accounts Payable Clerk who also owns inbox triage and scanning. (SRC-001, SRC-005)

**Improvement IO-23:** Provide supplier self-service visibility of invoice and payment status through a vendor portal, removing routine status enquiries from the Accounts Payable team.

**PP-25 ([[#invoice-intake-and-capture]]) — Severity: Low**

A material share of invoice volume still arrives as paper at the post office box despite the purchase order terms directing suppliers to the AP Inbox.

*Impact:* Forty to fifty pieces per week require manual handling, date-stamping and scanning before capture can begin, adding at least one business day to intake. (SRC-001, SRC-006)

**Improvement IO-24:** Enforce the electronic delivery requirement already stated in the purchase order terms through supplier outreach, reducing residual paper intake.

**PP-26 ([[#po-invoice-entry-and-three-way-match]]) — Severity: High**

Match exceptions are dominated by receipts that have not yet been entered, so the bill is matched against nothing. The Senior Accounts Payable Specialist attributes roughly sixty percent of her exceptions to goods being physically at the dock with no receipt entered, and the Accounts Payable Manager states that same-day receipting would halve exception volume and return a week a month to the Senior Accounts Payable Specialist (SRC-001). The Corporate Controller names real-time receipt entry at the dock as the single change she would make and describes everything downstream of it as symptom (SRC-003). The working notes record the item as independently named the top pain point by the Accounts Payable Manager, the Senior Accounts Payable Specialist and the Receiving Supervisor (SRC-005).

*Impact:* Accounts Payable capacity is consumed re-working bills that carry no actual discrepancy, and supplier payment is delayed for reasons unrelated to the invoice.

**Improvement IO-28:** Address receipt entry lag at source through the dock-side receipting improvements identified in [[goods-receipt]], which would remove the largest share of match exceptions rather than processing them faster.

**PP-27 ([[#po-invoice-entry-and-three-way-match]]) — Severity: Medium**

A price exception referred to the Buyer has no clearance timeframe, no escalation and no visibility, and the bill sits on hold indefinitely.

*Impact:* Bills are held past their due date with no mechanism to surface the ageing population, and no source could describe how or when such an exception is closed. (SRC-001)

**Improvement IO-26:** Introduce an ageing report over bills in "Match Exception - Hold", broken down by cause and by the party the exception is referred to, with an escalation rule for referrals not cleared within a defined period. *(also addresses PP-29)*

**PP-28 ([[#po-invoice-entry-and-three-way-match]]) — Severity: High**

Nobody is able to state the matching tolerance the process operates to.

*Impact:* The control cannot be evidenced or tested as written, and staff cannot judge whether an out-of-tolerance bill should have released. (SRC-001, SRC-003, SRC-005, SRC-006)

**Improvement IO-25:** Pull, confirm and publish the configured NetSuite match tolerance, and re-approve it as a documented Controller-owned policy so that a single figure governs the control.

**PP-29 ([[#po-invoice-entry-and-three-way-match]]) — Severity: Medium**

Match exception research leaves no record on the transaction.

*Impact:* The cause of each exception, the time it was held and the resolution reached exist only in email, so the exception population cannot be analyzed, reported or evidenced to an auditor. (SRC-001, SRC-005)

**Improvement IO-26:** Introduce an ageing report over bills in "Match Exception - Hold", broken down by cause and by the party the exception is referred to, with an escalation rule for referrals not cleared within a defined period. *(also addresses PP-27)*

**Improvement IO-27:** Record the exception cause and resolution against the bill in NetSuite rather than in email, so that exception volume and root cause are measurable and the investigation is evidenced with the transaction.

**PP-30 ([[#non-po-invoice-entry-and-approval]]) — Severity: High**

Non-PO approvals remain unactioned in approver queues for extended periods with no automated escalation operating.

*Impact:* Bills are described as sitting for up to two weeks until someone chases them, delaying the payable and consuming Accounts Payable time in manual follow-up. (SRC-001, SRC-005)

**Improvement IO-29:** Configure and activate automated reminder and escalation of unactioned approvals in the NetSuite approval workflow, as the prior SOP already contemplates, so that stalled non-PO bills surface without manual chasing.

**PP-31 ([[#non-po-invoice-entry-and-approval]]) — Severity: High**

Non-PO invoice entry and supplier master maintenance are performed by the same Accounts Payable Clerk.

*Impact:* The individual able to create and edit supplier records also enters unmatched payables against those records, concentrating in one pair of hands two activities the control environment elsewhere separates. (SRC-005)

**Improvement IO-30:** Separate non-PO invoice entry from supplier master maintenance by reassigning one of the two activities, restoring the segregation applied elsewhere in the payables process.

**PP-32 ([[#non-po-invoice-entry-and-approval]]) — Severity: Medium**

Every non-PO invoice is coded by hand to account, department and class because there is no purchase order from which coding can be derived.

*Impact:* Roughly a quarter of total invoice volume carries manual coding effort at entry and the associated miscoding exposure. (SRC-001, SRC-005)

**Improvement IO-31:** Bring recurring non-PO spend such as utilities, insurance and legal billing onto standing purchase orders through [[blanket-po-management]], so that coding and approval derive from the purchase order rather than being applied by hand at each invoice.

**PP-33 ([[#non-po-invoice-entry-and-approval]]) — Severity: Medium**

Freight billing arising from collect shipments has no defined authorization or entry route and falls into the non-PO population by default.

*Impact:* TBD — the sources record that no process was described and that authorization of collect shipments is itself disputed at the receiving dock. (SRC-005)

**Improvement IO-32:** Establish a defined authorization and entry route for freight billing on collect shipments, so that such invoices are not absorbed into the non-PO population without an owner.

**PP-34 ([[#vendor-statement-reconciliation]]) — Severity: High**

The procedure is not performed at the cadence or over the population the prior SOP requires, and no party could confirm it was performed in any given recent period.

*Impact:* The detective control over the completeness of recorded payables operates inconsistently or not at all; unrecorded invoices, duplicate charges and misapplied credits can persist undetected between periods. The Corporate Controller attributes the reduced cadence to available headcount and has accepted it without a documented policy change.

**Improvement IO-33:** Set a single documented cadence and population for statement reconciliation that the department can sustain, formally amend the SOP to match it, and place the resulting task on the close calendar with a named owner.

**Improvement IO-35:** Adopt a standard reconciliation worksheet stored in a defined shared-drive location, with preparer and reviewer sign-off and an aged reconciling-item schedule reported to the Corporate Controller. *(also addresses PP-36)*

**PP-35 ([[#vendor-statement-reconciliation]]) — Severity: Medium**

The vendor population is taken from a static list issued in approximately 2024 that has not been refreshed and is not confirmed to match any defined selection basis.

*Impact:* Vendors that have since become significant by spend are outside the reconciliation population, and vendors that have declined consume effort; the population no longer ties to the $50,000 spend threshold in the prior SOP.

**Improvement IO-34:** Regenerate the reconciliation vendor list from a NetSuite vendor spend report on a defined refresh cycle rather than maintaining a static list.

**PP-36 ([[#vendor-statement-reconciliation]]) — Severity: Medium**

No completed reconciliation worksheet was produced or located during fieldwork, and no review or reporting of results occurs.

*Impact:* The procedure cannot be evidenced to an auditor even for periods in which it was performed, and errors surfaced by a reconciliation have no escalation path.

**Improvement IO-35:** Adopt a standard reconciliation worksheet stored in a defined shared-drive location, with preparer and reviewer sign-off and an aged reconciling-item schedule reported to the Corporate Controller. *(also addresses PP-34)*

#### Payments

**PP-37 ([[#weekly-payment-run]]) — Severity: High**

The Corporate Controller both approves the payment run in NetSuite and releases the funds at the bank, so the two authorization points in the cycle rest with one individual. The Controller describes the separation as "roughly" three-way — vendor master with the Accounts Payable Clerk, proposal build with the Accounts Payable Manager, approval and release with the Controller — and acknowledges that approving the run in the ERP and releasing it at the bank sits with the same person. External audit has pushed back on this twice. The compensating position offered is that the Controller approves a proposal they did not build and that the payment register is reviewed after the fact, which the Controller characterised as a compensating story and "not a great one" (SRC-003, SRC-005).

*Impact:* A single individual can carry an approved payment through to settlement; the mitigating review is detective and after the fact.

**Improvement IO-36:** Separate approval of the run in NetSuite from release of the funds at the bank, so that no individual performs both, and retire the post-hoc register review as the primary mitigation.

**PP-38 ([[#weekly-payment-run]]) — Severity: Medium**

The documented disbursement procedure has drifted from practice — the prior SOP describes a Monday/Wednesday cycle that no one performing the run recognizes, and no two accounts of the current calendar agree.

*Impact:* There is no authoritative statement of when the proposal is built, reviewed and released, which leaves the timing of the approval control unverifiable; if the proposal is reviewed and released the same morning, the review is compressed to the point the Controller identified it as a finding.

**Improvement IO-37:** Fix and publish the payment run calendar, with the proposal build, Controller review and bank release on separate days, and align the SOP to it.

**PP-39 ([[#weekly-payment-run]]) — Severity: Medium**

Approximately 30 checks a week are still printed, requiring physical check stock, a signature plate, a MICR printer and a positive pay exception loop for a small share of disbursement value.

*Impact:* Physical-instrument handling and its custody controls are sustained for a residual volume, and each run carries a same-week exception disposition deadline.

**Improvement IO-38:** Convert remaining check-paid suppliers to ACH, reducing residual check volume and the physical custody and positive pay handling that supports it.

**PP-40 ([[#wire-and-manual-payment]]) — Severity: Medium**

The manual / emergency check branch exists in the prior SOP but could not be evidenced as operating. §7.5 of the prior SOP requires written Corporate Controller authorization, but no interviewee described the process operating, the frequency was never established, and the working notes record it as insufficient to document (SRC-005). A control that cannot be shown to operate, over a disbursement channel that bypasses the scheduled cycle and its proposal review, cannot be evidenced to the auditors who hold dual authorization on outbound funds in scope (SRC-003).

*Impact:* Off-cycle check disbursements cannot be evidenced as authorized.

**Improvement IO-39:** Confirm whether manual / emergency checks are still issued; document the current authorization, evidence and retention practice, or formally retire the channel if it is no longer used.

**PP-41 ([[#wire-and-manual-payment]]) — Severity: Low**

Wire authorization evidence is a manually signed PDF held on the Finance Shared Drive, separate from both the banking portal and the accounting record.

*Impact:* Assembling the authorization trail for a wire requires retrieving evidence from a location outside the systems that hold the transaction.

**Improvement IO-40:** Capture the wire request and its approvals in a system-based workflow so the authorization is held with the transaction record rather than as a separate signed PDF.

**PP-42 ([[#positive-pay-exception-handling]]) — Severity: High**

The exception disposition is performed end to end by a single individual, with no second review and no recorded rationale. The Accounts Payable Manager receives the exceptions, decides pay or return, and records the disposition, with no reviewer described at any point (SRC-001, SRC-003). The same role builds the payment proposal and holds the check signature plate combination (SRC-005), so the individual who originated the check population also decides the fate of items the bank flagged against it. No documentation of the basis for a disposition is retained, which leaves the control unverifiable after the fact even where it operated correctly.

*Impact:* A fraudulent or altered check paid on a single unreviewed decision would not be detected by this process, and no evidence exists for an auditor to test the decisions taken.

**Improvement IO-41:** Require a second reviewer on any exception dispositioned as pay, and retain a short record of the basis for each disposition against the check run.

**PP-43 ([[#positive-pay-exception-handling]]) — Severity: Medium**

The disposition window is short, falls to one role, and has already been missed at least once.

*Impact:* Items default to return when the deadline passes, so a legitimate check can be returned unpaid to a supplier without a decision having been taken; the reported instance confirms the exposure is real rather than theoretical.

**Improvement IO-42:** Name and entitle a backup dispositioner in the bank portal, and monitor items that default to return so a missed deadline is visible rather than silent.
