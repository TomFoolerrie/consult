## Vendor Master Data Maintenance and Periodic Review

<!-- scope note: covers variants — Record maintenance (terms, GL defaults, sync repair); Semi-annual master file review (inactive/duplicate/incomplete). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Scope

This procedure covers ongoing maintenance of the existing supplier and vendor
master population at Nordhaven Industrial Group: changes to an established
record's payment terms and default general ledger coding, correction of records
delivered incomplete by the nightly Coupa-to-NetSuite supplier sync, and the
periodic review of the master file for inactive, duplicate and incomplete
records. Establishment of a first-time supplier is excluded and is documented in
[[new-vendor-onboarding]]; changes to a supplier's remittance banking details are
excluded and are documented in [[vendor-banking-change]]. The maintained vendor
record is relied on downstream by [[po-invoice-entry-and-three-way-match]],
[[non-po-invoice-entry-and-approval]] and [[weekly-payment-run]]. Ownership of
this process is not settled in the current state (see GAP-01). (SRC-002, SRC-003,
SRC-005, SRC-006)

### At a Glance

| Field | Value |
|---|---|
| Trigger | A change is required to an established vendor record (terms, default GL coding, incomplete data from the nightly sync); separately, the periodic master file review falls due |
| Frequency | Ad hoc for record maintenance; semi-annual for the master file review (`TBD — confirm with process owner`; semi-annual per the prior SOP, operation unevidenced — see GAP-02) |
| Preparer | Accounts Payable Clerk (holder of the NetSuite Vendor Maintenance role) for record maintenance; Accounts Payable Manager for the master file review per the prior SOP |
| Reviewer | `TBD — confirm with process owner` for record maintenance (no reviewer described); Corporate Controller receives the results of the master file review |
| Systems | NetSuite (vendor master for payment purposes); Coupa (system of record for the supplier record, source of the nightly sync) |
| Key inputs | Change request or observed defect on an existing record; the NetSuite vendor master population; the Coupa supplier list |
| Key outputs | Updated NetSuite vendor record; results of the master file review reported to the Corporate Controller |

### Before You Start

- **NetSuite vendor record** — [[new-vendor-onboarding]]; already created and
  activated, and the record to which the change applies is identified.
- **Coupa supplier record** — [[new-vendor-onboarding]]; the sourcing-side system
  of record, referenced where the NetSuite record is incomplete relative to it.
- **NetSuite Vendor Maintenance role** — held by the person making the change;
  the role carries no payment preparation, payment approval or banking portal
  entitlement (§9.3 of the prior SOP).
- **Supplier master population** — the full NetSuite and Coupa record set,
  available for extract, for the periodic review variant.

### Procedure

#### Step 1: Identify the record and the change required

The vendor record requiring maintenance is identified, together with the change
required — payment terms, default general ledger account, or data missing from
the record. Requests reach the Accounts Payable Clerk who holds the Vendor
Maintenance role; no formal request form or intake channel for maintenance
changes was described by any source.

> **VALIDATION REQUIRED — GAP-01:** Ownership and intake of vendor master maintenance are unresolved.
> - **Note:** No single owner or intake channel is established — confirm who owns the vendor master and how change requests are raised before relying on this step.
> - **Detail:** Vendor maintenance in NetSuite is performed by the Accounts Payable Clerk, who also performs non-PO invoice entry and other duties (SRC-001, SRC-003, SRC-005). The Corporate Controller identified as one of three priorities that "somebody own the vendor master as a real job, not as a thing [the clerk] does between other things," citing roughly 11,000 records with no owner (SRC-003). The prior SOP assigns only the semi-annual master file review, to the Accounts Payable Manager, and is otherwise silent on who owns ongoing maintenance (§9.5 of the prior SOP, SRC-006). No source described a request form, ticket queue or log for maintenance changes.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 2: Route a banking change out of this procedure

- **Condition:** the requested change is to the supplier's remittance banking details

Changes to remittance banking are not made under this procedure; they are subject
to a telephone callback verification to a number held on the vendor record and a
second approval, and are handled under [[vendor-banking-change]].

#### Step 3: Apply the change to the NetSuite vendor record

The change is applied directly to the vendor record in NetSuite by the holder of
the Vendor Maintenance role. Standard payment terms are net 45.

- **Fields / Parameters:** payment terms; default GL account.
- **Evidence Required:** the updated NetSuite vendor record.

> **SCREENSHOT PLACEHOLDER — SC-01:** The NetSuite vendor record in edit mode, showing the payment terms and default GL account fields.

> **VALIDATION REQUIRED — GAP-02:** No review or approval of a routine vendor master change is described.
> - **Note:** No second-person review of a non-banking master data change was identified — do not assume one operates.
> - **Detail:** Sources describe the segregation between vendor maintenance and payment execution (§9.3 of the prior SOP, SRC-006; SRC-003) and a second approval specific to banking changes (SRC-003), but no source describes any review, approval or system-generated change log for a change to payment terms or default GL coding. Whether the NetSuite audit trail is used as a detective control is unconfirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

#### Step 4: Repair a record delivered incomplete by the nightly sync

- **Condition:** the nightly Coupa-to-NetSuite supplier sync has landed a record with blank payment terms or otherwise incomplete data

The missing values are keyed manually onto the NetSuite vendor record. Failures
are discovered when the record is found to be defective rather than by any
monitoring on the interface; no owner for the interface could be named.

- **System / Tool:** Coupa, consulted as the sourcing-side system of record where
  the correct values must be re-derived.

#### Step 5: Extract and review the supplier master file

- **Condition:** the periodic master file review falls due (semi-annually per the
  prior SOP)

The supplier master file is reviewed for inactive, duplicate and incomplete
records. This variant is performed by the Accounts Payable Manager rather than by
the Accounts Payable Clerk who performs day-to-day maintenance. The population is
substantial: approximately 11,000 supplier records exist, of which approximately
4,000 have been active in the last two years.

> **VALIDATION REQUIRED — GAP-03:** There is no evidence that the semi-annual supplier master file review is performed.
> - **Note:** The review is a documented requirement with no observed operation — treat its performance as unconfirmed rather than assumed.
> - **Detail:** The prior SOP requires a semi-annual review of the supplier master file for inactive, duplicate and incomplete records, performed by the Accounts Payable Manager with results reported to the Corporate Controller (§9.5 of the prior SOP, SRC-006). No interviewee described performing, receiving or reviewing such an exercise, and the working notes record the requirement as untested with no evidence it happens (SRC-005). The Procurement Lead separately described the duplicate population as a long-standing problem with no de-duplication project and no owner (SRC-002). The prior SOP is itself version 3.0 from 2023 and predates the NetSuite upgrade.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 6: Disposition the records identified

- **Condition:** the periodic master file review has identified inactive,
  duplicate or incomplete records

Records identified are dispositioned — deactivated, merged or completed. The
mechanics, sequencing and approval of disposition in NetSuite and in Coupa are
`TBD — confirm with process owner`.

> **VALIDATION REQUIRED — GAP-04:** The disposition mechanics for inactive and duplicate records are undocumented.
> - **Note:** No source describes how a record is deactivated or how duplicates are merged across NetSuite and Coupa — do not document or execute a method until it is confirmed.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

#### Step 7: Report the review results to the Corporate Controller

- **Condition:** the periodic master file review has been performed

The results of the review are reported to the Corporate Controller. The form,
retention and content of that report are `TBD — confirm with process owner`.

> **SCREENSHOT PLACEHOLDER — SC-02:** The output of the supplier master file review as reported to the Corporate Controller, evidencing the population reviewed and the records dispositioned.

### Outputs & Evidence

- **Updated NetSuite vendor record** — the maintained payment-side master record,
  consumed by [[po-invoice-entry-and-three-way-match]],
  [[non-po-invoice-entry-and-approval]] and [[weekly-payment-run]].
- **Supplier master file review results** — reported to the Corporate Controller
  per the prior SOP; no instance of such a report was identified.
- **Not retained:** no request, log or approval record for a routine change to
  payment terms or default GL coding was identified as being retained (see
  GAP-02); no record of a sync-repair correction is retained, so the frequency of
  sync failures is not measurable; and no evidence of the periodic master file
  review was produced (see GAP-03).

### Key Controls

> **CONTROL — CTRL-001:** Additions and modifications to the supplier master record are performed only by personnel holding the NetSuite Vendor Maintenance role, which carries no payment preparation, payment approval or banking portal entitlement.
> - **Type:** Preventive
> - **Frequency:** continuous (entitlement-based)
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-002:** A review of the supplier master file for inactive, duplicate and incomplete records is performed periodically and the results reported to the Corporate Controller.
> - **Type:** Detective
> - **Frequency:** semi-annual per the prior SOP; operation unevidenced (see GAP-03)
> - **Owner:** Accounts Payable Manager

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The vendor master has no named owner.
> - **Note:** Maintenance of approximately 11,000 supplier records is performed by the Accounts Payable Clerk alongside non-PO invoice entry and other duties, with no owner accountable for the population as a whole.
> - **Detail:** The Corporate Controller named unowned vendor master data as one of three things she would change, describing it as "a thing [the clerk] does between other things" and observing that "eleven thousand records, no owner, is how you end up on the front page" (SRC-003). The working notes record the same clerk holding both vendor master maintenance and non-PO invoice entry as a segregation-of-duties flag (SRC-005). No intake channel, work queue or service level for maintenance requests was described by any source. See GAP-01.
> - **Impact:** Master data quality degrades unchecked; defects are corrected reactively when a record is found unusable rather than through any owned process.
> - **Severity:** High

> **PAIN POINT — PP-002:** The supplier master file review required by the prior SOP does not demonstrably operate.
> - **Note:** A semi-annual review for inactive, duplicate and incomplete records is required and reported to the Corporate Controller, but no source could evidence that it has been performed.
> - **Detail:** The requirement is stated at §9.5 of the prior SOP (SRC-006); the working notes record it as untested with no evidence of performance (SRC-005). In its absence the duplicate population persists — approximately 11,000 records against approximately 4,000 active in the last two years, with the same vendor present multiple times under different spellings (SRC-002). See GAP-03.
> - **Impact:** Inactive, duplicate and incomplete records accumulate, raising the risk of duplicate payment and payment to a stale remit-to, and distorting spend analysis; a documented control is not operating.
> - **Severity:** High

> **PAIN POINT — PP-003:** Vendor edit capability in NetSuite is broader than the Vendor Maintenance role, including a legacy third-party login.
> - **Note:** Vendor edit is also held through the NetSuite administrator role and by an implementation partner login that remains active, weakening the entitlement-based control.
> - **Detail:** Vendor edit rights in NetSuite are held by the Accounts Payable Clerk, by the Assistant Controller for emergency use, by the NetSuite administrator role held by the IT Manager, and by the implementation partner, whose login remains live; the Corporate Controller is aware of the partner login and described removing it as outstanding (SRC-003, SRC-005). No periodic access review of the vendor maintenance entitlement was described.
> - **Impact:** The population able to create or alter a payee is larger than the control described to the auditors, and includes an external party outside the Company's segregation model.
> - **Severity:** High

> **PAIN POINT — PP-004:** Records arriving from the nightly Coupa-to-NetSuite sync require manual repair.
> - **Note:** Records land with blank payment terms and are corrected by hand, with no monitoring or named owner for the interface.
> - **Impact:** Maintenance effort is consumed correcting defects originated upstream, and a defective record can remain in use until noticed.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Assign a named owner for the vendor master with a defined intake channel for maintenance requests, and re-establish the periodic master file review on a scheduled basis with retained evidence of performance and of the results reported to the Corporate Controller.
> - **Addresses:** PP-001, PP-002

> **IMPROVEMENT OPPORTUNITY — IO-002:** Run a one-time supplier de-duplication and deactivation exercise across the existing master to bring the population to the active record set, with a documented disposition method for duplicates and inactive records.
> - **Addresses:** PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Perform a periodic access review of vendor edit entitlement in NetSuite and remove the legacy implementation partner login.
> - **Addresses:** PP-003

```consult-meta
systems: [netsuite, coupa]
roles:   [ap-clerk, ap-manager, corporate-controller, assistant-controller, it-manager, procurement-lead]
```
