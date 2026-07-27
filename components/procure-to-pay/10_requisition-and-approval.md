## Requisition Creation and Approval

<!-- scope note: covers variants — Catalog / punchout requisition; Non-catalog free-text requisition; Services requisition (SOW required). Document the shared flow once; branch at the step(s) where the variants diverge. -->

### Scope

This procedure covers the creation of a purchase requisition in Coupa and its
routing through the approval chain, for all three requisition paths in use:
catalog and punchout items, non-catalog free-text requests, and services requests
requiring a statement of work. It ends when the requisition is fully approved and
available for conversion to a purchase order. Establishment of the supplier is
excluded and is documented in [[new-vendor-onboarding]]; creation, transmission
and amendment of the resulting purchase order are excluded and are documented in
[[po-issuance-and-change-orders]]. Releases against an existing blanket
agreement are documented in [[blanket-po-management]], and purchases committed
before any requisition was raised are documented in [[confirming-po]].
(SRC-002, SRC-005)

### At a Glance

| Field | Value |
|---|---|
| Trigger | A requester needs goods or services and raises a requisition in Coupa |
| Frequency | Ad hoc, continuous |
| Preparer | Requester (Buyer or Procurement Lead assists on non-catalog and services requests) |
| Reviewer | Cost Center Owner on every requisition; Functional Vice President and Chief Financial Officer added by value threshold |
| Systems | Coupa (requisition entry and approval chains); supplier punchout sites for catalog shopping |
| Key inputs | Active supplier record; catalog or punchout content; statement of work for a services request; approved AFE number for capital expenditure |
| Key outputs | Fully approved Coupa requisition, available for conversion to a purchase order |

### Before You Start

- **Active supplier record** — [[new-vendor-onboarding]]; the supplier must exist
  in Coupa and in NetSuite before a requisition can be raised against it.
- **Coupa catalog or punchout content** — hosted catalogs and punchout
  connections for industrial MRO and IT categories; available to the requester at
  entry.
- **Statement of work** — supplied by the requesting department for a services
  request; must be available to attach at requisition entry.
- **Approved AFE (authorization for expenditure) number** — obtained outside
  Coupa for capital expenditure; must be in hand before the requisition will
  route.

### Procedure

#### Step 1: Create the requisition in Coupa

The requester creates a requisition in Coupa and selects the path appropriate to
what is being bought: a catalog or punchout item, a non-catalog free-text
request, or a services request. The three paths share a single approval chain and
differ only in how the requisition lines are built.

> **SCREENSHOT PLACEHOLDER — SC-01:** The Coupa requisition entry screen, showing the three available request paths.

#### Step 2: Build catalog or punchout lines

- **Condition:** the item is available on a hosted catalog or through a punchout
  connection

The requester shops the hosted catalog or punches out to the supplier site,
builds a cart and returns it to Coupa, where the cart becomes the requisition
lines.

- **System / Tool:** the supplier's punchout site, entered from and returned to
  Coupa.

#### Step 3: Build a non-catalog free-text line

- **Condition:** the item is not available on a catalog or punchout connection

The requester enters a free-text description of the goods or services required
and selects the supplier.

#### Step 4: Build a services request

- **Condition:** the requisition is for services

A separate services request form is used, which requires a statement of work to
be attached to the requisition.

> **VALIDATION REQUIRED — GAP-01:** The review and approval of the statement of work attached to a services requisition is undocumented.
> - **Note:** No source describes who reviews the statement of work or against what criteria — confirm before assuming a review exists over and above the standard approval chain.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 5: Record the AFE number for capital expenditure

- **Condition:** the requisition is for capital expenditure

An approved AFE (authorization for expenditure) number is entered in the
designated custom field. The requisition will not route for approval until the
field is populated.

- **Fields / Parameters:** AFE number (custom field).
- **Expected Result:** the requisition becomes eligible to route; without the AFE
  number it does not enter the approval chain at all.

#### Step 6: Submit the requisition for approval

The completed requisition is submitted and routes through the Coupa approval
chain. The Cost Center Owner approves every requisition regardless of value.

> **SCREENSHOT PLACEHOLDER — SC-02:** The Coupa approval chain view on a submitted requisition, showing the approvers assigned by value.

#### Step 7: Obtain the additional approvals required by value

- **Condition:** the requisition value exceeds the first approval threshold

Approvers are added to the chain by the value of the requisition: below
approximately $2,000 the Cost Center Owner approves alone; from approximately
$2,000 to the upper threshold the Functional Vice President is added; above the
upper threshold the Chief Financial Officer is added. The upper threshold is
`TBD — confirm with process owner`.

> **VALIDATION REQUIRED — GAP-02:** The requisition value threshold at which Chief Financial Officer approval is required is in conflict between sources.
> - **Note:** The threshold is unconfirmed — do not operate to a figure; obtain the configured Coupa approval chain before applying it.
> - **Detail:** The Procurement Lead stated the threshold is $25,000 and confirmed it when asked again (SRC-002). The Corporate Controller implied $50,000 in a separate conversation, and the Accounts Payable Manager did not know the figure (SRC-005). The Coupa approval chain export has not been obtained, so no source of record has been consulted. Resolution sits with the Procurement Lead, who owns the Coupa approval chains, jointly with the Corporate Controller.
> - **Nature:** conflict
> - **Owner to confirm:** Procurement Lead

> **VALIDATION REQUIRED — GAP-03:** Whether the requisition approval ladder is intended to differ from the non-PO invoice approval ladder is unresolved.
> - **Note:** The two ladders use different breakpoints and approver sets — confirm which difference is deliberate before either is described as policy.
> - **Detail:** The Procurement Lead stated the difference is deliberate, on the basis that the AP ladder governs non-PO invoices and is a different chain, and acknowledged the divergence as a fair criticism (SRC-002). The Corporate Controller did not appear to be aware that the two ladders differ (SRC-005). The non-PO invoice ladder is documented in [[non-po-invoice-entry-and-approval]]. Resolution sits with the Corporate Controller.
> - **Nature:** conflict
> - **Owner to confirm:** Corporate Controller

#### Step 8: Release the approved requisition to purchase order creation

Once every approver in the chain has approved, the requisition is fully approved
in Coupa and is converted to a purchase order, which is handled in
[[po-issuance-and-change-orders]].

- **Expected Result:** a fully approved requisition exists in Coupa, with the
  approval chain recorded against it.

### Outputs & Evidence

- **Fully approved Coupa requisition** — the input to
  [[po-issuance-and-change-orders]]; carries the requisition lines, the selected
  supplier and, where applicable, the attached statement of work and the AFE
  number.
- **Evidence retained:** the approval chain and approver actions are retained on
  the requisition record in Coupa; the statement of work is retained as an
  attachment on a services requisition.
- **Not retained:** no cycle-time or approval-ageing measurement is retained from
  a system report; requisition-to-PO elapsed time has been measured only from a
  manually maintained spreadsheet (SRC-005).

### Key Controls

> **CONTROL — CTRL-001:** Every requisition is approved by the Cost Center Owner before it can be converted to a purchase order, irrespective of value.
> - **Type:** Preventive
> - **Frequency:** each requisition
> - **Owner:** Cost Center Owner

> **CONTROL — CTRL-002:** Requisitions above the value thresholds configured in the Coupa approval chain require additional approval by the Functional Vice President and, above the upper threshold, the Chief Financial Officer.
> - **Type:** Preventive
> - **Frequency:** each requisition above the first threshold
> - **Owner:** Procurement Lead

> **CONTROL — CTRL-003:** A capital-expenditure requisition will not route for approval unless an approved AFE number is populated in the designated custom field.
> - **Type:** Preventive
> - **Frequency:** each capital-expenditure requisition
> - **Owner:** Procurement Lead

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Requisition-to-PO cycle time is dominated by approvals waiting in queues.
> - **Note:** Median requisition-to-PO elapsed time was measured at approximately 6.5 days, of which about 5 days is approvals sitting unactioned.
> - **Detail:** The figure comes from the Procurement Lead's own measurement and was volunteered as the second of his four pain points (SRC-002). The working notes record that the measurement derives from a manually maintained spreadsheet rather than a system report and should be treated as soft (SRC-005).
> - **Impact:** Delivery of goods and services is delayed by approval latency rather than by sourcing or supplier lead time, and the delay is not measured from any system of record.
> - **Severity:** High

> **PAIN POINT — PP-002:** Punchout and hosted catalog pricing is stale relative to negotiated contracts.
> - **Note:** Requesters buying through the catalog path can transact at off-contract prices without any indication that the price shown is not the negotiated one.
> - **Detail:** The Buyer stated that roughly half of punchout pricing does not reflect the negotiated contract, so requesters buy off-contract without knowing (SRC-002). No catalog refresh cadence or owner was described by any source.
> - **Impact:** Negotiated pricing is not realised on catalog spend, and the leakage is invisible to the requester at the point of purchase.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Introduce automatic approval of low-value catalog requisitions — for example below $1,000 — where the line transacts at a contracted price, removing an estimated one third of requisition volume from the approval chain.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Establish a scheduled refresh and a named owner for hosted catalog and punchout pricing, so that catalog prices reconcile to the negotiated contract.
> - **Addresses:** PP-002

```consult-meta
systems: [coupa]
roles:   [requester, cost-center-owner, functional-vp, cfo, procurement-lead, buyer, corporate-controller]
```
