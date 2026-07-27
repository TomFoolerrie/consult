## Positive Pay Exception Handling

### Scope

This procedure covers the disposition of positive pay exception items returned by
the bank against checks issued by the company: their receipt in the bank portal,
the pay-or-return decision, and the effect of the disposition deadline passing
without a decision. It begins at the point the bank presents an exception item —
the creation and transmission of the positive pay issue file that produces the
issued-check register is excluded and is performed under [[weekly-payment-run]].
Manual and emergency check issuance is likewise excluded and follows
[[wire-and-manual-payment]], and clearing or non-clearing of the resulting items
is picked up in the monthly bank reconciliation, which is outside this
procedure. (SRC-001, SRC-003, SRC-006)

### At a Glance

| Field | Value |
|---|---|
| Trigger | The bank presents one or more positive pay exception items against the issued-check register for a check run |
| Frequency | Per check run, where the bank returns exceptions; exceptions are presented the business morning after checks are issued |
| Preparer | Accounts Payable Manager |
| Reviewer | None — the disposition is made and finalised by the preparer alone (see PP-001) |
| Systems | Chase Connect (positive pay exception queue and disposition) |
| Key inputs | Exception items presented by the bank; the issued-check register established by the transmitted issue file |
| Key outputs | A pay or return disposition recorded in the bank portal for each exception item |

### Before You Start

- **Positive pay issue file for the check run** — [[weekly-payment-run]];
  transmitted to the bank on the date the checks were printed, so that the bank
  holds the issued-check register against which items are compared.
- **Bank portal access with positive pay entitlement** — the Accounts Payable
  Manager's Chase Connect user ID, entitled to view and disposition the exception
  queue.

### Procedure

#### Step 1: Review the exception items presented by the bank

Positive pay exception items are returned by the bank in the bank portal the
business morning following the check issue date; they are described as available
for review by 10:00 AM. Each item presented is one that the bank could not match
to the issued-check register for the run.

- **Expected Result:** the population of items requiring a pay-or-return decision
  for that cycle is known, and the disposition deadline for the cycle applies

> **VALIDATION REQUIRED — GAP-01:** The basis on which each exception item is researched and decided is not documented.
> - **Note:** No source describes what the exception item is compared against, or what evidence supports a pay decision — do not infer a research step; confirm the actual review performed before relying on this as a control.
> - **Detail:** The Accounts Payable Manager describes reviewing the items in the portal and deciding pay or return (SRC-001), and the Corporate Controller confirms that the Manager reviews and dispositions (SRC-003). Neither describes what causes an item to be exceptioned in the first place (amount mismatch, payee mismatch, serial number not on file), what record is consulted to resolve it, or what threshold or judgment separates a pay from a return. §7.6 of the prior SOP requires only that exception items be dispositioned by the Accounts Payable Manager not later than the bank's deadline, and is silent on the basis of the decision (SRC-006).
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

> **SCREENSHOT PLACEHOLDER — SC-01:** The Chase Connect positive pay exception queue showing pending exception items and the available pay / return disposition options.

#### Step 2: Disposition each exception item as pay or return before the bank deadline

Each exception item is dispositioned in the bank portal as pay or return. The
decision is made by the Accounts Payable Manager, and the disposition must be
recorded before the deadline set by the bank; the deadline is described as 1:00
PM on the day the exceptions are presented (see CTRL-001).

- **Evidence Required:** the disposition recorded against each item in the bank
  portal

> **VALIDATION REQUIRED — GAP-02:** The exception presentation and disposition times are tied to a weekday calendar that is itself unconfirmed.
> - **Note:** Treat the deadline as "the bank-established deadline on the morning after check issue" rather than a fixed weekday and time until the check run calendar and the bank's stated cutoff are confirmed.
> - **Detail:** The Accounts Payable Manager describes exceptions returning by 10:00 AM Friday with a disposition deadline of 1:00 PM Friday, on the basis that the check run is printed Thursday (SRC-001). The Corporate Controller describes only that exceptions come back the next business morning (SRC-003). The day-by-day payment run calendar is itself in conflict across three accounts and is unresolved under [[weekly-payment-run]], so the Friday times cannot be relied on as fixed. §7.6 of the prior SOP fixes no clock time and defers to the deadline established by the depository institution (SRC-006). The working notes record the disposition deadline as 1:00 PM Friday without independent confirmation from the bank (SRC-005).
> - **Nature:** conflict
> - **Owner to confirm:** Accounts Payable Manager

#### Step 3: Allow the default return to apply where no decision is recorded

- **Condition:** the disposition deadline passes with one or more items
  undecided

Where no disposition is recorded by the bank's deadline, the item defaults to
return and the check is not paid. This default was set deliberately by the
Corporate Controller as the safer failure position (see CTRL-002). The
Accounts Payable Manager reports one occasion on which the deadline was missed
and the default applied.

- **Expected Result:** the undecided item is returned unpaid by the bank without
  further action by the company

> **VALIDATION REQUIRED — GAP-03:** No alternate dispositioner is identified for periods when the Accounts Payable Manager is unavailable.
> - **Note:** Only the Accounts Payable Manager is described as dispositioning exceptions; confirm who covers the deadline in that role's absence, or accept that the default return applies.
> - **Nature:** unknown
> - **Owner to confirm:** Corporate Controller

### Outputs & Evidence

- **Pay or return disposition per exception item** — recorded in Chase Connect
  against each item, and reflected in whether the check clears the operating
  account.
- **Evidence retained:** the disposition recorded in the bank portal is the only
  record of the decision described by any source; its retention period in the
  portal was not established.
- **Not retained:** no record of the research supporting a pay or return decision
  is described as being retained, in the bank portal, in NetSuite or elsewhere;
  nor is any log of items that defaulted to return on an expired deadline.

### Key Controls

> **CONTROL — CTRL-001:** Positive pay exception items are reviewed and dispositioned as pay or return by the Accounts Payable Manager before the deadline established by the bank.
> - **Type:** Detective
> - **Frequency:** Each cycle in which the bank presents exception items
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-002:** The bank's no-decision default is configured as return, so that an exception item left undecided at the deadline is not paid.
> - **Type:** Preventive
> - **Frequency:** Continuous
> - **Owner:** Corporate Controller

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** The exception disposition is performed end to end by a single individual, with no second review and no recorded rationale.
> - **Note:** One person decides whether a check the bank could not match is paid, and nothing in the process evidences why.
> - **Detail:** The Accounts Payable Manager receives the exceptions, decides pay or return, and records the disposition, with no reviewer described at any point (SRC-001, SRC-003). The same role builds the payment proposal and holds the check signature plate combination (SRC-005), so the individual who originated the check population also decides the fate of items the bank flagged against it. No documentation of the basis for a disposition is retained, which leaves the control unverifiable after the fact even where it operated correctly.
> - **Impact:** A fraudulent or altered check paid on a single unreviewed decision would not be detected by this process, and no evidence exists for an auditor to test the decisions taken.
> - **Severity:** High

> **PAIN POINT — PP-002:** The disposition window is short, falls to one role, and has already been missed at least once.
> - **Impact:** Items default to return when the deadline passes, so a legitimate check can be returned unpaid to a supplier without a decision having been taken; the reported instance confirms the exposure is real rather than theoretical.
> - **Severity:** Medium

> **IMPROVEMENT OPPORTUNITY — IO-001:** Require a second reviewer on any exception dispositioned as pay, and retain a short record of the basis for each disposition against the check run.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Name and entitle a backup dispositioner in the bank portal, and monitor items that default to return so a missed deadline is visible rather than silent.
> - **Addresses:** PP-002

```consult-meta
systems: [chase-connect, netsuite]
roles:   [ap-manager, corporate-controller]
```
