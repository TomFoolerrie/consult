## New Vendor Onboarding

### Scope

This procedure covers the establishment of a new supplier at Nordhaven Industrial
Group, from the requester's New Supplier Request through sourcing diligence,
supplier self-registration, approval, and activation of the corresponding vendor
record for payment purposes. It covers first-time suppliers only. Changes to an
existing supplier's remittance banking details are excluded and are documented in
[[vendor-banking-change]]; ongoing edits, periodic review and deactivation of
existing records are excluded and are documented in
[[vendor-master-data-maintenance]]. A supplier must exist and be active before a
requisition can be raised against it, so this procedure is upstream of
[[requisition-and-approval]] and [[po-issuance-and-change-orders]]. (SRC-002,
SRC-003, SRC-005)

### At a Glance

| Field | Value |
|---|---|
| Trigger | A requester needs goods or services from a supplier not already established |
| Frequency | Ad hoc, on request |
| Preparer | Procurement Lead (or Buyer, depending on plant) |
| Reviewer | Procurement Lead approves in Coupa; Corporate Controller as second approver above the expected-annual-spend threshold |
| Systems | Coupa (system of record for the supplier record); NetSuite (vendor master for payment purposes) |
| Key inputs | New Supplier Request form; W-9; supplier-entered registration data (banking, insurance certificates, diversity classification) |
| Key outputs | Approved Coupa supplier record with diligence evidence attached; active NetSuite vendor record with payment terms and default GL account |

### Before You Start

- **New Supplier Request form (Coupa)** — submitted by the requester; complete,
  with supplier legal name, DBA, remit-to address, contact, the related-party
  response, and the W-9 attached.
- **Existing supplier list (Coupa)** — available for the duplicate check; used as
  the comparison population before a new record is created.
- **IRS TIN matching service and the Treasury OFAC SDN list** — externally
  accessible; both are consulted manually and the results captured as evidence.

### Procedure

#### Step 1: Submit the New Supplier Request

A requester who needs goods or services from a supplier that does not yet exist
submits the New Supplier Request form in Coupa. The form is a Company-built Coupa
form.

- **Fields / Parameters:** supplier legal name; DBA; remit-to address; supplier
  contact; W-9 attachment; mandatory related-party question.

> **SCREENSHOT PLACEHOLDER — SC-01:** The Coupa New Supplier Request form, showing the required fields including the related-party question.

> **VALIDATION REQUIRED — GAP-01:** The disposition of the mandatory related-party response is undocumented.
> - **Note:** No source describes what happens when a requester answers the related-party question affirmatively — do not assume a review exists; confirm before relying on it.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 2: Route the request to procurement

The submitted request routes to the Procurement Lead or to the Buyer for the
plant concerned. Ownership of the request follows the plant, not the requester.

#### Step 3: Perform supplier diligence

Diligence is performed on the requested supplier before any invitation is issued:
the W-9 name is verified against the TIN through the IRS TIN matching service;
the supplier is screened against the Treasury OFAC SDN list by manual lookup on
the Treasury site; and the existing supplier list is checked for an existing or
near-duplicate record.

- **System / Tool:** IRS TIN matching service and the U.S. Treasury OFAC SDN
  search, both accessed outside Coupa.
- **Evidence Required:** the OFAC screening result is captured as a screenshot
  and attached, together with the TIN match result, to the Coupa supplier record.

#### Step 4: Invite the supplier to self-register

Once diligence is satisfied, Coupa issues a Supplier Information Management (SIM)
invitation to the supplier. The supplier enters its own banking details, W-9,
insurance certificates and diversity classification directly in the SIM portal;
this information is not keyed by Company personnel from an emailed document.

- **Expected Result:** a completed supplier registration is returned into Coupa
  with supplier-entered banking and compliance documentation attached.

#### Step 5: Approve the supplier in Coupa

The Procurement Lead approves the supplier record in Coupa.

#### Step 6: Obtain second approval for high expected spend

- **Condition:** the supplier is expected to exceed the annual spend threshold
  (`TBD — confirm with process owner`; recalled as approximately $250,000)

The Corporate Controller approves the supplier in addition to the Procurement
Lead.

> **VALIDATION REQUIRED — GAP-02:** The expected-annual-spend threshold that triggers Corporate Controller approval is unconfirmed.
> - **Note:** The threshold is unconfirmed — do not operate to a figure; obtain the configured value before applying it.
> - **Detail:** The Procurement Lead recalled the threshold as "two-fifty, two hundred fifty thousand" a year but expressed uncertainty (SRC-002). No other source states the figure and the Coupa approval-chain configuration has not been pulled. Resolution sits with the Procurement Lead, who owns the Coupa approval chains.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 7: Sync the approved supplier to NetSuite

The approved Coupa supplier record is transmitted to NetSuite by the nightly
supplier sync, which creates the corresponding vendor record in the payment
system of record.

- **System / Tool:** the Coupa-to-NetSuite nightly integration.
- **Expected Result:** a NetSuite vendor record exists the following day, in an
  inactive state pending activation.

#### Step 8: Activate the vendor record in NetSuite

The Accounts Payable Clerk activates the synced vendor record, sets the payment
terms and the default GL account. Standard terms are net 45; net 60 is sought on
new suppliers.

- **Fields / Parameters:** payment terms; default GL account.
- **Evidence Required:** the activated NetSuite vendor record.

> **SCREENSHOT PLACEHOLDER — SC-02:** The NetSuite vendor record at activation, showing payment terms and default GL account.

#### Step 9: Correct an incomplete synced record

- **Condition:** the nightly sync lands the record with blank payment terms or
  otherwise incomplete data

The missing values are keyed manually onto the NetSuite vendor record before the
supplier is used.

> **VALIDATION REQUIRED — GAP-03:** No monitoring, alerting or ownership is established for the nightly Coupa-to-NetSuite supplier sync.
> - **Note:** Sync failures are found by hand — confirm whether any detective mechanism exists before assuming a failed record will be noticed.
> - **Detail:** The sync is described as failing intermittently, with records landing without payment terms and being corrected manually (SRC-002). No interviewee could name an owner for the interface or describe any monitoring or alert on it (SRC-005). Resolution sits with the IT Manager as NetSuite administrator, jointly with the Procurement Lead.
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager

### Outputs & Evidence

- **Approved Coupa supplier record** — the system of record for the supplier from
  a sourcing standpoint; carries the supplier-entered W-9, banking, insurance
  certificates and diversity classification.
- **Diligence evidence** — the OFAC SDN screening screenshot and the TIN match
  result, retained as attachments on the Coupa supplier record.
- **Active NetSuite vendor record** — with payment terms and default GL account
  set; consumed by [[requisition-and-approval]],
  [[po-invoice-entry-and-three-way-match]] and the payment processes.
- **Not retained:** no record of the duplicate check against the existing
  supplier list is described as being retained, and no evidence of the
  disposition of the related-party response was identified (see GAP-01).

### Key Controls

> **CONTROL — CTRL-001:** The W-9 legal name is verified against the TIN through the IRS TIN matching service, and the supplier is screened against the Treasury OFAC SDN list before an onboarding invitation is issued; both results are attached to the Coupa supplier record.
> - **Type:** Preventive
> - **Frequency:** each new supplier request
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-002:** The requested supplier is checked against the existing supplier list for an existing or near-duplicate record before a new record is created.
> - **Type:** Preventive
> - **Frequency:** each new supplier request
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-003:** The new supplier is approved in Coupa by the Procurement Lead, with a second approval by the Corporate Controller where expected annual spend exceeds the threshold, before the record can be used.
> - **Type:** Preventive
> - **Frequency:** each new supplier
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-004:** Supplier banking and compliance documentation is entered by the supplier itself in the Coupa SIM portal rather than keyed by Company personnel from an emailed document.
> - **Type:** Preventive
> - **Frequency:** each new supplier
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-005:** Creation and modification of the NetSuite vendor record is restricted to the Vendor Maintenance role, which holds no payment preparation, payment approval or banking portal entitlement.
> - **Type:** Preventive
> - **Frequency:** continuous (entitlement-based)
> - **Owner:** Corporate Controller

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The supplier master is heavily duplicated, which undermines the duplicate check this procedure depends on.
> - **Note:** Roughly 11,000 supplier records exist against approximately 4,000 active in the last two years, with the same vendor present multiple times under different spellings.
> - **Detail:** The Procurement Lead described the duplicate population as an "enormous problem" that has been on his list for some time, with no de-duplication project, no cadence and no named owner (SRC-002, SRC-005). The prior SOP requires a semi-annual review of the supplier master file for inactive, duplicate and incomplete records, reported to the Corporate Controller (§9.5 of the prior SOP, SRC-006); no interviewee produced evidence that this review takes place. The Corporate Controller separately identified unowned vendor master data as one of three things she would change (SRC-003).
> - **Impact:** The duplicate check at diligence is performed against an unreliable population, so new duplicates continue to be created; duplicate records also raise the risk of duplicate payment and distort spend analysis.
> - **Severity:** High

> **PAIN POINT — PP-002:** The nightly Coupa-to-NetSuite supplier sync fails intermittently and has no monitoring or owner.
> - **Note:** Failed or partial syncs are discovered manually and corrected by hand, and no owner for the interface could be named.
> - **Detail:** Records land in NetSuite with blank payment terms and are corrected manually by the Accounts Payable Clerk (SRC-002). Each sync failure is described as consuming roughly an hour of three people's time, and no interviewee could identify monitoring, alerting or an owner for the interface (SRC-005). See GAP-03.
> - **Impact:** New suppliers can sit unusable or incorrectly configured until someone notices; recurring unplanned effort across procurement, AP and IT.
> - **Severity:** Medium

> **PAIN POINT — PP-003:** Vendor master maintenance and non-PO invoice entry are performed by the same role.
> - **Note:** The Accounts Payable Clerk who activates and maintains vendor records also enters non-PO invoices, weakening the separation the vendor-master control relies on.
> - **Detail:** Segregation as designed separates vendor maintenance from payment preparation, approval and bank release (§9.3 of the prior SOP, SRC-006; SRC-003). The working notes flag that the same individual holding the Vendor Maintenance role also performs non-PO invoice entry, which places creation of the payee and creation of the payable in one pair of hands (SRC-005).
> - **Impact:** A payee and a payable to that payee can be originated by the same role, reducing the assurance provided by CTRL-005.
> - **Severity:** High

> **IMPROVEMENT OPPORTUNITY — IO-001:** Run a supplier de-duplication and deactivation project across the existing master, and assign a named owner accountable for the ongoing supplier master file review the prior SOP already requires.
> - **Addresses:** PP-001, PP-003

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish monitoring and alerting on the nightly Coupa-to-NetSuite supplier sync with a named owner, so failed or incomplete records are detected rather than found in use.
> - **Addresses:** PP-002

```consult-meta
systems: [coupa, netsuite]
roles:   [requester, procurement-lead, buyer, corporate-controller, ap-clerk, it-manager]
```
