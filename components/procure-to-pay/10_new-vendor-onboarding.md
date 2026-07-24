## New Vendor Onboarding

### A. Process Overview

This procedure establishes a new supplier as a transactable vendor in both Coupa,
the system of record for the supplier record from a sourcing standpoint, and
NetSuite, the system of record for the vendor master for payment purposes. It is
performed on demand, whenever a Requester needs to buy from a supplier the Company
has not previously used, and it is a hard pre-condition for purchasing: a
requisition cannot be raised against a supplier that does not yet exist in both
systems. The Requester initiates the request, the Procurement Lead or the
responsible Buyer performs supplier diligence and approves the record, the Supplier
self-registers its own remittance and compliance data through the Coupa Supplier
Information Management (SIM) portal, and the Accounts Payable Clerk activates the
synced record in NetSuite. Completion feeds [[requisition-and-approval]] and
downstream payment. Subsequent changes to an established supplier are out of scope
here and are covered by [[vendor-banking-change]] and
[[vendor-master-data-maintenance]]. (SRC-002, SRC-003, SRC-005)

### B. Quick Reference

- **Trigger:** A Requester needs goods or services from a supplier that does not exist in Coupa and NetSuite.
- **Frequency:** On demand.
- **Preparer:** Requester (request submission); Procurement Lead or Buyer (diligence); Accounts Payable Clerk (NetSuite activation).
- **Reviewer:** Procurement Lead approves in Coupa; Corporate Controller additionally approves where expected annual spend exceeds the approval threshold (see F).
- **Primary systems / tools:** Coupa (New Supplier Request form and SIM portal), NetSuite, IRS TIN Matching, OFAC SDN List.
- **Key outputs:** Approved Coupa supplier record with diligence evidence attached; active NetSuite vendor record with payment terms and default GL account set.

### C. Pre-Requisites

- The Requester has confirmed that the supplier does not already exist in Coupa.
- A completed W-9 has been obtained from the supplier and is available to attach to the request.
- A supplier contact able to complete the SIM self-registration has been identified.
- The Requester is able to answer the mandatory related-party question on the request form.

### D. Inputs

- **New Supplier Request form (Coupa):** Requester. Captures supplier legal name, DBA, remit-to address, contact, and the related-party response.
- **Supplier W-9:** Supplier, attached by the Requester to the request form.
- **Existing supplier list (Coupa):** Coupa, used for the duplicate check.
- **IRS TIN matching result:** IRS TIN Matching, obtained by the Procurement Lead or Buyer.
- **OFAC SDN screening result:** OFAC SDN List, obtained as a manual lookup on the Treasury website.
- **Supplier-entered registration data:** Supplier, submitted through the Coupa SIM portal — banking, W-9, insurance certificates, and diversity classification.

### E. Step-by-Step Procedure

#### Step 1: Submit the New Supplier Request

The Requester completes the New Supplier Request form in Coupa, a Company-built
form, providing the supplier legal name, DBA, remit-to address, and supplier
contact, attaching the W-9, and answering the mandatory related-party question.

- **System / Tool:** Coupa
- **Fields / Parameters:** Supplier legal name; DBA; remit-to address; supplier contact; W-9 attachment; related-party question (mandatory).
- **Expected Result:** The request is submitted and routed to Procurement for diligence.

> **SCREENSHOT PLACEHOLDER — SC-01:** The completed Coupa New Supplier Request form, showing the mandatory fields and the related-party question, to validate what the Requester is required to provide before diligence begins.

#### Step 2: Route the request to Procurement

The submitted request is directed to the Procurement Lead or to the responsible
Buyer, assigned by plant. The receiving party takes ownership of the diligence
steps that follow.

- **System / Tool:** Coupa
- **Expected Result:** A named Procurement owner holds the request.

> **VALIDATION REQUIRED — GAP-01:** The plant-to-owner assignment that determines whether a given request routes to the Procurement Lead or to the responsible Buyer, and whether that assignment is configured in Coupa or applied manually.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 3: Check for duplicate supplier records

The Procurement Lead or Buyer checks the requested supplier against the existing
supplier list to confirm that no record already exists for the same entity. The
supplier master currently holds approximately 11,000 records, of which roughly
4,000 have transacted in the last twenty-four months, and the same supplier is known
to appear multiple times under different spellings — see
[[GAP-02 — DUPLICATE CHECK CRITERIA]].

- **System / Tool:** Coupa
- **Expected Result:** The request proceeds only where no existing record covers the supplier; where one does, the existing record is used instead.

> **VALIDATION REQUIRED — GAP-02:** The defined matching criteria and search method used for the duplicate check (for example legal name, TIN, or remit-to address), and whether any result is retained as evidence. Sources describe the check as performed but do not describe a defined method.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 4: Perform supplier diligence

The Procurement Lead or Buyer verifies that the legal name on the W-9 matches the
taxpayer identification number using IRS TIN Matching, and screens the supplier
against the OFAC SDN List. OFAC screening is performed as a manual lookup on the
Treasury website; the result is screenshotted and attached to the Coupa supplier
record together with the TIN matching result.

- **System / Tool:** IRS TIN Matching; OFAC SDN List; Coupa
- **Expected Result:** W-9 legal name and TIN agree, and no sanctions match is returned.
- **Evidence Required:** OFAC screening screenshot and TIN matching result attached to the Coupa supplier record.

> **VALIDATION REQUIRED — GAP-03:** The disposition path where diligence fails — a TIN mismatch, a potential OFAC match, or an affirmative related-party answer. No escalation or rejection handling was described in the sources.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-02:** The Coupa supplier record attachments pane showing the OFAC screening screenshot and TIN matching evidence, to validate that diligence evidence is retained on the record.

#### Step 5: Invite the supplier to self-register in SIM

Coupa issues a Supplier Information Management invitation to the supplier contact.
The Supplier self-registers, entering its own banking details, W-9, insurance
certificates, and diversity classification. Banking data is therefore entered by the
Supplier directly rather than keyed by the Company from an emailed document.

- **System / Tool:** Coupa (SIM portal)
- **Fields / Parameters:** Banking details; W-9; insurance certificates; diversity classification.
- **Expected Result:** A completed supplier registration is returned into the Coupa supplier record.
- **Evidence Required:** Supplier-entered W-9, insurance certificates, and banking held on the Coupa supplier record.

> **VALIDATION REQUIRED — GAP-04:** Whether the SIM registration is reviewed or validated by the Company before approval, and how an incomplete or stalled registration is followed up. Sources describe the self-registration but not any Company-side review of it.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 6: Approve the supplier in Coupa

The Procurement Lead approves the new supplier in Coupa. Where the supplier is
expected to exceed the annual spend threshold, the Corporate Controller approves in
addition — see [[GAP-05 — SECOND-APPROVER SPEND THRESHOLD]].

- **System / Tool:** Coupa
- **Expected Result:** The supplier record reaches approved status and becomes eligible for the overnight synchronization to NetSuite.
- **Evidence Required:** Coupa approval record on the supplier.

> **VALIDATION REQUIRED — GAP-05:** The expected-annual-spend threshold above which the Corporate Controller must also approve a new supplier. The source states approximately $250,000 per year but expresses it as a recollection rather than a confirmed configuration; the Coupa approval chain configuration should be pulled.
> - **Nature:** unsupported-assumption
> - **Owner to confirm:** Procurement Lead

#### Step 7: Synchronize to NetSuite and activate the vendor record

An overnight synchronization pushes the approved supplier from Coupa into NetSuite.
The Accounts Payable Clerk then activates the vendor record and sets the payment
terms and the default GL account. Standard payment terms are net 45; net 60 is
sought on new suppliers. Synchronized records occasionally arrive with a blank
payment term and are corrected manually at this step.

- **System / Tool:** NetSuite
- **Fields / Parameters:** Vendor status (active); payment terms (standard net 45); default GL account.
- **Expected Result:** An active NetSuite vendor record exists and the supplier is transactable for requisitioning and payment.

> **VALIDATION REQUIRED — GAP-06:** How the default GL account and the applicable payment terms are determined for a new supplier, and whether net 60 on new suppliers is a negotiating position or a standard to be applied. Sources describe the fields being set but not the basis for the values.
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

> **VALIDATION REQUIRED — GAP-07:** Whether any monitoring, alerting, or reconciliation confirms that the nightly Coupa-to-NetSuite supplier synchronization completed and that records landed complete. No owner for the synchronization could be named.
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager

> **SCREENSHOT PLACEHOLDER — SC-03:** The activated NetSuite vendor record showing status, payment terms, and default GL account, to validate the fields set at activation.

### F. Key Controls

> **CONTROL — CTRL-001:** New supplier diligence — the W-9 legal name is verified against the taxpayer identification number through IRS TIN Matching and the supplier is screened against the OFAC SDN List before the supplier record is approved, with the screening result retained on the Coupa supplier record.
> - **Type:** Preventive
> - **Frequency:** Each new supplier request
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-002:** Duplicate prevention — the requested supplier is checked against the existing supplier list before a new record is created.
> - **Type:** Preventive
> - **Frequency:** Each new supplier request
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-003:** Supplier approval — a new supplier is approved in Coupa by the Procurement Lead before it can synchronize to NetSuite, with a second approval by the Corporate Controller where expected annual spend exceeds the threshold identified in Step 6.
> - **Type:** Preventive
> - **Frequency:** Each new supplier request
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-004:** Supplier-entered banking — remittance banking is entered by the Supplier directly in the Coupa Supplier Information Management portal rather than keyed by Company personnel from a supplier document.
> - **Type:** Preventive
> - **Frequency:** Each new supplier registration
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-005:** Segregation of duties over the vendor master — the Accounts Payable Clerk who maintains and activates vendor records in NetSuite holds no payment entitlements, and can neither approve a bill nor operate the payment run.
> - **Type:** Preventive
> - **Frequency:** Continuous (entitlement-based)
> - **Owner:** Corporate Controller

### G. Outputs

- **Approved Coupa supplier record:** Carries the New Supplier Request data, the supplier's self-registered banking, W-9, insurance certificates, and diversity classification, and the diligence evidence.
- **Active NetSuite vendor record:** Payment terms and default GL account set; the vendor becomes available for requisitioning in [[requisition-and-approval]] and for payment downstream.
- **Evidence retained:** OFAC screening screenshot and IRS TIN matching result attached to the Coupa supplier record; W-9, insurance certificates, and banking held as supplier-entered attachments in Coupa.

### H. Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The supplier master is heavily duplicated. Approximately 11,000 supplier records exist against roughly 4,000 that have transacted in the last twenty-four months, and individual suppliers appear multiple times under different spellings.
> - **Impact:** Spend is fragmented across duplicate records, weakening spend visibility and negotiating leverage, and the duplicate check performed at onboarding runs against an unreliable population. No de-duplication project or owner exists.
> - **Severity:** High

> **PAIN POINT — PP-002:** The vendor master has no dedicated owner. Maintenance is performed by the Accounts Payable Clerk alongside other duties rather than as a defined role.
> - **Impact:** Data quality and access hygiene over an 11,000-record master are not actively managed; the Corporate Controller identified this as a top concern.
> - **Severity:** High

> **PAIN POINT — PP-003:** The nightly Coupa-to-NetSuite supplier synchronization fails intermittently, and records sometimes land in NetSuite with a blank payment term requiring manual correction.
> - **Impact:** Each failure is reported to consume roughly one hour each for three people, and incomplete records delay the point at which a new supplier becomes transactable.
> - **Severity:** Medium

> **PAIN POINT — PP-004:** OFAC sanctions screening is a one-time manual lookup performed on the Treasury website at onboarding, evidenced by a screenshot.
> - **Impact:** Screening depends on consistent manual execution and is not monitored on an ongoing basis once the supplier is onboarded.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Run a supplier master de-duplication and deactivation project to consolidate duplicate records and retire suppliers with no recent activity, and define the match criteria to be applied at onboarding.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish vendor master data ownership as a defined role with accountability for record quality, activation standards, and periodic review.
> - **Addresses:** PP-001, PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Assign an owner and implement monitoring or alerting on the Coupa-to-NetSuite supplier synchronization, with a completeness check on newly synchronized records so blank payment terms are detected rather than discovered.
> - **Addresses:** PP-003

> **IMPROVEMENT OPPORTUNITY — IO-004:** Replace the manual OFAC lookup with an automated screen embedded in the onboarding workflow, with ongoing rescreening of the active supplier population.
> - **Addresses:** PP-004

```consult-meta
systems: [coupa, netsuite, irs-tin-match, ofac-sdn-list]
roles:   [requester, procurement-lead, buyer, corporate-controller, ap-clerk, ap-manager, it-manager, supplier]
```
