## Blanket Purchase Order Setup and Not-to-Exceed Monitoring

### Scope

This procedure covers the use of blanket purchase orders for recurring spend at
Nordhaven Industrial Group — the establishment of a blanket purchase order
carrying an annual not-to-exceed value, the consumption of that value by releases
against it, and the monitoring of the remaining balance. It excludes the issuance
and amendment of individual purchase orders, which are documented in
[[po-issuance-and-change-orders]], and the creation and approval of the
underlying requisition, documented in [[requisition-and-approval]]. Receipt
against a purchase order is excluded and documented in [[goods-receipt]], and
matching of the supplier invoice is documented in
[[po-invoice-entry-and-three-way-match]]. The sources describe the mechanism and
its principal failure mode but not the establishment steps in detail, and the
gaps below record what remains unconfirmed. (SRC-002, SRC-005)

### At a Glance

| Field | Value |
|---|---|
| Trigger | A recurring spend category is contracted for a period — the sources name janitorial services, the gas supplier and tooling consignment |
| Frequency | TBD — confirm with process owner; no cadence for either establishment or monitoring is evidenced (see GAP-02) |
| Preparer | Buyer |
| Reviewer | TBD — confirm with process owner (see GAP-01) |
| Systems | Coupa (blanket purchase order and the not-to-exceed burn-down report) |
| Key inputs | Contracted recurring spend arrangement; annual not-to-exceed value |
| Key outputs | Blanket purchase order carrying an annual not-to-exceed value; releases consuming that value |

### Before You Start

- **Contracted recurring spend arrangement** — the recurring category (janitorial,
  gas supply, tooling consignment) must be agreed with the supplier before a
  blanket purchase order is raised against it.
- **Active supplier record** — [[new-vendor-onboarding]]; the supplier must exist
  in Coupa and in NetSuite before any purchase order can be cut.
- **Annual not-to-exceed value** — the ceiling the blanket purchase order carries
  for the year; no source describes how it is derived or who sets it.

### Procedure

#### Step 1: Establish a blanket purchase order with an annual not-to-exceed value

A blanket purchase order is raised in Coupa for a recurring spend category and
carries an annual not-to-exceed value. The categories described in the sources are
janitorial services, the gas supplier and tooling consignment. (SRC-002)

- **Fields / Parameters:** annual not-to-exceed value.

> **VALIDATION REQUIRED — GAP-01:** The establishment of a blanket purchase order — who sets the annual not-to-exceed value, what approval it attracts, and the term over which it runs — is not described by any source.
> - **Note:** Do not assume the blanket purchase order follows the standard requisition approval ladder; confirm the setup and approval path before documenting it to a preparer.
> - **Detail:** The Buyer described blanket purchase orders in outline only — used for recurring spend, carrying an annual not-to-exceed value and released against by receipt — and no source described how the ceiling is set, who approves it, whether it is requisition-driven, or when in the year it is established or renewed (SRC-002). The working notes record the blanket purchase order not-to-exceed area as insufficiently supported to document, and list a re-interview of the Buyer as an outstanding action (SRC-005). Resolution sits with the Procurement Lead.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

> **SCREENSHOT PLACEHOLDER — SC-01:** The Coupa blanket purchase order record, showing the annual not-to-exceed value and the released-against balance.

#### Step 2: Release against the blanket purchase order by receipt

Spend is drawn down against the blanket purchase order by receipt; each release
consumes part of the annual not-to-exceed value. (SRC-002)

- **Expected Result:** the not-to-exceed value remaining on the blanket purchase
  order is reduced by the value released.

#### Step 3: Run the not-to-exceed burn-down report

The remaining balance against the annual not-to-exceed value is visible from a
report in Coupa. No source describes the report being run on a schedule, and no
owner for it was named. See [[GAP-02 — NTE BURN-DOWN OWNER AND CADENCE]].
(SRC-002, SRC-005)

> **VALIDATION REQUIRED — GAP-02:** The not-to-exceed burn-down report has no named owner and no established cadence.
> - **Note:** The burn-down report is not a scheduled control today — do not rely on it to surface an approaching ceiling until an owner and a cadence are confirmed.
> - **Detail:** The Buyer stated that a Coupa report for the not-to-exceed burn-down exists but that he did not believe anyone runs it on a schedule (SRC-002). The working notes record the same position and add that there is no owner and no cadence, listing the item as insufficiently supported to document and naming a re-interview of the Buyer as the outstanding action (SRC-005). The report's name, its parameters and its navigation path within Coupa were not described by any source. Resolution sits with the Procurement Lead, who owns procurement reporting.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

#### Step 4: Respond to an exhausted not-to-exceed value

- **Condition:** the annual not-to-exceed value has been fully consumed

Once the not-to-exceed value is reached, further releases against the blanket
purchase order are blocked, and the block is discovered by the affected plants
rather than in advance. The Buyer described reaching the ceiling in month nine of
the year, everything blocking, and receiving four escalation calls in a single
afternoon. (SRC-002)

> **VALIDATION REQUIRED — GAP-03:** The remediation path after a not-to-exceed value is exhausted is not described.
> - **Note:** No source states whether the ceiling is raised by change order, by a new blanket purchase order, or by another route, nor what approval that attracts — confirm before documenting a resolution step.
> - **Nature:** unknown
> - **Owner to confirm:** Procurement Lead

### Outputs & Evidence

- **Blanket purchase order** — held in Coupa, carrying the annual not-to-exceed
  value and the balance consumed by releases.
- **Not-to-exceed burn-down report** — available in Coupa; produced on demand
  rather than on a schedule.
- **Evidence retained:** the blanket purchase order record and its consumed
  balance are held in Coupa; no source described any other retained evidence.
- **Not retained:** no evidence of the burn-down report having been run, reviewed
  or acted upon is retained, because the report is not run on a schedule and has
  no owner; no measurement of how often a not-to-exceed ceiling is reached, or of
  the disruption caused, is retained.

### Key Controls

> **CONTROL — CTRL-001:** Releases against a blanket purchase order are blocked once the annual not-to-exceed value is consumed, preventing spend beyond the contracted ceiling.
> - **Type:** Preventive
> - **Frequency:** each release
> - **Owner:** TBD — confirm with process owner (see GAP-02)

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The not-to-exceed burn-down is not monitored, so an approaching ceiling is discovered only when releases block.
> - **Note:** A Coupa burn-down report exists but is not run on a schedule and has no owner; the ceiling is reached mid-year and surfaces as blocked releases and escalation calls from the plants.
> - **Detail:** The Buyer described hitting the not-to-exceed value in month nine, everything blocking, and taking four angry calls in one afternoon, and stated that although a Coupa report for the burn-down exists he did not think anyone runs it on a schedule (SRC-002). The working notes confirm that there is no owner and no cadence for the report (SRC-005). The consequence is that a preventive ceiling working exactly as designed is experienced as an unplanned outage in recurring supply.
> - **Impact:** Recurring supply for categories such as janitorial services, gas and tooling consignment stops without warning, and the remediation is handled reactively under escalation.
> - **Severity:** High

> **IMPROVEMENT OPPORTUNITY — IO-001:** Assign a named owner to the Coupa not-to-exceed burn-down report and run it on a defined cadence, with a threshold at which the Buyer acts on a blanket purchase order approaching its ceiling — an action the Procurement Lead himself identified as needed.
> - **Addresses:** PP-001

```consult-meta
systems: [coupa]
roles:   [buyer, procurement-lead]
```
