## New Vendor Onboarding

### Scope

New Vendor Onboarding establishes a new supplier in both Coupa and NetSuite so
that the supplier can be requisitioned against and ultimately paid (SRC-002).
It covers the intake request, onboarding diligence, supplier self-registration,
Coupa approval, the overnight sync, and NetSuite activation, ending with an
active vendor record that enables [[requisition-and-approval]]. Subsequent
changes to the supplier's remit-to banking details are excluded and handled
under [[vendor-banking-change]]; ongoing hygiene of the supplier record
population is covered under [[vendor-master-data-maintenance]].

### At a Glance

| Field | Value |
|---|---|
| Trigger | A Requester needs goods or services from a supplier that does not exist as an active record in Coupa and NetSuite (SRC-002) |
| Frequency | Ad hoc, on demand |
| Preparer | Requester (request submission); Procurement Lead or Buyer (diligence and supplier invitation); Supplier (SIM self-registration); Accounts Payable Clerk (NetSuite activation) (SRC-002, SRC-005) |
| Reviewer | Procurement Lead (Coupa supplier approval); Corporate Controller (co-approval above an expected-annual-spend threshold — value unconfirmed, validation raised at the approval step in Procedure) |
| Systems | Coupa (including the SIM portal) — system of record for the supplier record from a sourcing standpoint; NetSuite — system of record for the vendor master for payment purposes (SRC-002) |
| Key inputs | New Supplier Request form with W-9 attached; supplier self-registration data entered through the SIM portal |
| Key outputs | Approved, active supplier record in Coupa with diligence evidence attached; active NetSuite vendor master record with payment terms and default GL coding |

### Before You Start

- **New Supplier Request form (Coupa)** — completed by the Requester, who requires Coupa access to submit it (SRC-002).
- **Supplier W-9** — provided by the prospective Supplier; completed and attached to the New Supplier Request form by the Requester (SRC-002).
- **Supplier contact details** — provided by the Supplier; sufficient for Coupa to issue the SIM self-registration invitation (SRC-002).
- **IRS TIN match result** — obtained by the Procurement Lead or Buyer during diligence (SRC-002).
- **OFAC SDN lookup result** — manual search of the U.S. Treasury Specially Designated Nationals list by the Procurement Lead or Buyer (SRC-002, SRC-005).
- **Existing supplier list** — the current Coupa supplier population; used for the duplicate check (SRC-002).
- **Supplier self-registration data (SIM portal)** — banking details, W-9, insurance certificates, and diversity classification, entered by the Supplier (SRC-002, SRC-005).

### Procedure

#### Step 1: Submit the New Supplier Request form

The Requester — for example a plant maintenance planner, an engineer, or a
marketing staff member — completes the New Supplier Request form in Coupa. The
form is an internally built Coupa form and captures the supplier's legal name,
DBA, remit-to address, an attached W-9, a supplier contact, and a mandatory
question on whether the supplier is a related party (SRC-002).

- **Fields / Parameters:** Supplier legal name; DBA; remit-to address; W-9 attachment; supplier contact; related-party disclosure (mandatory).

> **SCREENSHOT PLACEHOLDER — SC-01:** The Coupa New Supplier Request form, showing the required fields including the mandatory related-party question.

#### Step 2: Perform onboarding diligence

The request routes to the Procurement Lead or the Buyer, depending on the
plant. The reviewer performs three diligence checks before the supplier is
invited to register (SRC-002):

1. **TIN match** — verify through the IRS TIN match that the name on the supplier's W-9 matches its taxpayer identification number.
2. **OFAC SDN screening** — run the supplier against the OFAC Specially Designated Nationals list via a manual lookup on the U.S. Treasury website; screenshot the result and attach it to the Coupa supplier record.
3. **Duplicate check** — check the prospective supplier against the existing supplier list. Note that the current supplier population is heavily polluted (roughly 11,000 records with only about 4,000 active in the last 24 months, including vendors present multiple times under different spellings), which limits the reliability of this check (SRC-002, SRC-005).

- **System / Tool:** IRS TIN match; U.S. Treasury OFAC SDN search (manual, outside Coupa).
- **Evidence Required:** OFAC search-result screenshot and TIN match result attached to the Coupa supplier record (SRC-005).

> **VALIDATION REQUIRED — GAP-01:** What happens when the mandatory related-party question is answered "yes" — no source describes how a related-party disclosure is reviewed, escalated, or approved.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-02:** A Coupa supplier record showing the attached OFAC SDN search-result screenshot and TIN match evidence.

#### Step 3: Invite the supplier to self-register through the SIM portal

Once diligence is complete, Coupa sends the supplier a Supplier Information
Management (SIM) invitation. The Supplier self-registers, entering its own
banking details, W-9, insurance certificates, and diversity classification
(SRC-002). Because the banking details come directly from the supplier through
the portal, they are not keyed by Company staff from an emailed document —
a deliberate control feature of the design (SRC-002). Any later change to the
supplier's remit-to banking details is handled under [[vendor-banking-change]],
not through re-registration.

- **Fields / Parameters:** Banking details; W-9; insurance certificates; diversity classification (supplier-entered).

#### Step 4: Approve the supplier in Coupa

The Procurement Lead approves the new supplier in Coupa. Where the Company
expects annual spend with the supplier to exceed $250,000, the Corporate
Controller must also approve (SRC-002). The threshold value is unconfirmed
[[GAP-02 — co-approval threshold]].

- **Expected Result:** Supplier approved in Coupa and queued for the nightly sync to NetSuite.

> **VALIDATION REQUIRED — GAP-02:** The expected-annual-spend threshold above which the Corporate Controller must co-approve a new supplier — stated tentatively as $250,000 by the Procurement Lead ("I think it's two-fifty"), and the Coupa approval chain configuration was not verified against the system during fieldwork (SRC-002, SRC-005).
> - **Nature:** unsupported-assumption
> - **Owner to confirm:** Procurement Lead

#### Step 5: Supplier record syncs to NetSuite overnight

The approved supplier record is pushed from Coupa to NetSuite by the nightly
supplier sync (SRC-002). The sync is intermittently unreliable: records
sometimes land with a blank payment term, which the Accounts Payable Clerk
corrects by hand. No monitoring, alerting, or named owner for the sync could be
identified during fieldwork (SRC-005) [[GAP-03 — sync ownership]].

- **Expected Result:** The new supplier record present in NetSuite the following business day.

> **VALIDATION REQUIRED — GAP-03:** Whether any monitoring or alerting exists for the nightly Coupa-to-NetSuite supplier sync, and who owns the interface — no owner could be named by any interviewee (SRC-005).
> - **Nature:** unknown
> - **Owner to confirm:** IT Manager

#### Step 6: Activate the vendor record in NetSuite

The Accounts Payable Clerk activates the synced vendor record in NetSuite,
sets the payment terms, and assigns the default GL coding (SRC-002). Standard
payment terms are net 45; the Company pushes for net 60 on new suppliers
(SRC-002). Activation is performed under the Vendor Maintenance role, which
carries no payment permissions — the segregation-of-duties control described
in F.

- **System / Tool:** NetSuite
- **Fields / Parameters:** Vendor status (active); payment terms (standard net 45; net 60 targeted for new suppliers); default GL coding.

> **SCREENSHOT PLACEHOLDER — SC-03:** An activated NetSuite vendor record showing vendor status, payment terms, and default GL coding as set by the Accounts Payable Clerk.

### Outputs & Evidence

- **Approved supplier record in Coupa**, with OFAC screenshot and TIN match evidence attached, and supplier-entered W-9, insurance certificates, and banking details held in the SIM portal (SRC-002, SRC-005).
- **Active NetSuite vendor master record** with payment terms and default GL coding — consumed downstream by [[requisition-and-approval]] and by AP for invoice matching and payment (SRC-002).
- **Evidence retained:** OFAC SDN search-result screenshot and TIN match result on the Coupa supplier record; supplier self-registration data (W-9, insurance certificates, banking) in Coupa SIM (SRC-005).

### Key Controls

> **CONTROL — CTRL-001:** Onboarding diligence — before a new supplier is invited to register, the Procurement Lead or Buyer verifies the W-9 name against the taxpayer identification number via the IRS TIN match, screens the supplier against the OFAC SDN list, and checks for duplicates against the existing supplier list; the OFAC screenshot and TIN match evidence are attached to the Coupa supplier record (SRC-002, SRC-005).
> - **Type:** Preventive
> - **Frequency:** Each new supplier request
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-002:** Supplier-entered banking — the supplier's remit-to banking details are entered directly by the Supplier through the Coupa SIM portal rather than keyed by Company staff from emailed documents, reducing the opportunity for interception or keying fraud at setup (SRC-002).
> - **Type:** Preventive
> - **Frequency:** Each supplier onboarding
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-003:** New supplier approval — every new supplier is approved in Coupa by the Procurement Lead; where expected annual spend exceeds $250,000 the Corporate Controller must co-approve (threshold unconfirmed — validation raised at the approval step in E) (SRC-002).
> - **Type:** Preventive
> - **Frequency:** Each new supplier
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-004:** Segregation of duties on vendor setup — additions and modifications to the supplier master record are performed only by personnel holding the Vendor Maintenance role, which excludes payment preparation, payment approval, and banking portal entitlements (§9.3 of the prior SOP, SRC-006). The Corporate Controller confirmed the Accounts Payable Clerk who activates vendor records holds no payment permissions in NetSuite (SRC-003). Ongoing governance of vendor-record edit access is covered under [[vendor-master-data-maintenance]].
> - **Type:** Preventive
> - **Frequency:** Continuous (role-based)
> - **Owner:** Corporate Controller

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The supplier master population is heavily duplicated and inactive — roughly 11,000 supplier records of which only about 4,000 have been active in the last 24 months, with some vendors present four times under different spellings; there is no de-duplication project and no owner (SRC-002, SRC-005).
> - **Impact:** The duplicate check performed during onboarding diligence is unreliable, new duplicate records continue to be created, and spend history is fragmented across records; the Corporate Controller flagged the unowned vendor master as a material exposure (SRC-002, SRC-003).
> - **Severity:** High

> **PAIN POINT — PP-002:** The nightly Coupa-to-NetSuite supplier sync fails intermittently — records land in NetSuite with a blank payment term and are corrected by hand by the Accounts Payable Clerk; there is no monitoring, no alerting, and no named owner, and each failure consumes roughly an hour each for three people (SRC-002, SRC-005).
> - **Impact:** Manual rework in AP, delayed vendor activation, and risk that a mis-synced record carries wrong payment terms into the payment cycle (SRC-002, SRC-005).
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Launch a supplier master de-duplication and cleanup project with a named owner, addressing the ~11,000-record population as a dedicated effort rather than a background task (SRC-002, SRC-003).
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish monitoring and alerting for the nightly Coupa-to-NetSuite supplier sync and assign a named owner for the interface, so failures (including blank payment terms) are detected and resolved systematically instead of by ad hoc manual correction (SRC-005).
> - **Addresses:** PP-002

```consult-meta
systems: [coupa, netsuite]
roles:   [requester, procurement-lead, buyer, supplier, corporate-controller, ap-clerk, it-manager]
```
