## Positive Pay Exception Handling

### Process Overview

This procedure covers the review and disposition of positive pay exception items — checks presented to the bank that do not match the positive pay issue file transmitted from NetSuite at check print under [[weekly-payment-run]]. The Accounts Payable Manager reviews each exception in Chase Connect the business morning after a check run and decides pay or return before the bank's disposition deadline; any item with no decision by the deadline is returned by default, a configuration the Company set deliberately (SRC-001, SRC-003). The procedure runs whenever the bank flags an exception, in practice tied to the weekly Thursday check run. Transmission of the issue file itself is part of [[weekly-payment-run]] and is not repeated here.

### Quick Reference

- **Trigger:** Positive pay exception item(s) presented in Chase Connect following a check issue date (SRC-001, SRC-003)
- **Frequency:** As exceptions arise; exception items post the next business morning after the check run — in practice by 10 AM Friday following the Thursday run (SRC-001, SRC-003)
- **Preparer:** Accounts Payable Manager — reviews and dispositions (SRC-001, SRC-003; §7.6 of the prior SOP, SRC-006)
- **Reviewer:** None identified — disposition is a single-person decision; no secondary review or backup was described (SRC-001, SRC-003)
- **Primary systems / tools:** Chase Connect (exception presentation and disposition); NetSuite (check issue records)
- **Key outputs:** Pay / return decision on each exception item recorded in Chase Connect; default return of any undecided item

### Pre-Requisites

- Checks have been printed and the positive pay issue file transmitted to Chase from NetSuite at check print, on each date checks are issued, under [[weekly-payment-run]] (SRC-001, SRC-003; §7.6 of the prior SOP, SRC-006).
- The Accounts Payable Manager holds Chase Connect access to the positive pay exception queue (SRC-001).

### Inputs

- **Positive pay exception items in Chase Connect:** presented checks the bank could not match to the issue file — source: the depository institution (SRC-001, SRC-003).
- **Positive pay issue file / check issue records in NetSuite:** the record of what the Company actually issued, transmitted at check print by [[weekly-payment-run]] (SRC-003).

### Step-by-Step Procedure

#### Step 1: Receive and review exception items

Exception items are reviewed in Chase Connect. Exceptions post the next business morning after checks are issued; following the weekly Thursday check run they are available by 10 AM Friday (SRC-001, SRC-003).

> **SCREENSHOT PLACEHOLDER — SC-01:** The Chase Connect positive pay exception queue showing a pending exception item with its pay/return options and the disposition deadline — validates where exceptions present and how the decision is recorded.

#### Step 2: Investigate each exception item

Each item is worked directly from the Chase Connect exception queue the same morning it presents, determining whether the presented check is a legitimate Company check by reference to the check issue records in NetSuite (SRC-001, SRC-003; process owner confirmation via the gap workbook).

- **Evidence Required:** Chase Connect decision log entry (the sole record of the disposition — see PP-003 in H)

#### Step 3: Disposition pay or return by the bank deadline

A pay or return decision is recorded on each item in Chase Connect not later than the deadline established by the depository institution — 1 PM on the day the exceptions post, in practice 1 PM Friday for the weekly cycle (SRC-001, SRC-005; §7.6 of the prior SOP, SRC-006) (CTRL-001).

- **Fields / Parameters:** Pay or return decision per exception item

#### Step 4: Default handling of undecided items

- **Condition:** an exception item has no decision recorded by the bank's disposition deadline

Any exception item with no decision recorded by the deadline is returned by the bank. This default was set deliberately (SRC-003) (CTRL-002). It has operated once, when the deadline was missed (SRC-001). What follow-up occurs after a default return — for example, reissue of a legitimate check returned in error — was not described by any source [[GAP-02 — POST-RETURN FOLLOW-UP AND BACKUP]].

> **VALIDATION REQUIRED — GAP-02:** What happens after an item is returned by default, and who dispositions exceptions when the Accounts Payable Manager is unavailable. The Accounts Payable Manager is the only person identified as reviewing exceptions, the decision window is roughly three hours (10 AM to 1 PM), the deadline has been missed once, and no source described a backup dispositioner or a correction/reissue path after a default return (SRC-001, SRC-003, SRC-005).
> - **Nature:** unknown
> - **Owner to confirm:** Accounts Payable Manager

### Key Controls

> **CONTROL — CTRL-001:** Positive pay exception review: the bank flags any presented check that does not match the issue file, and the Accounts Payable Manager dispositions each flagged item (pay or return) in Chase Connect before the deadline established by the depository institution (SRC-001, SRC-003; §7.6 of the prior SOP, SRC-006).
> - **Type:** Detective
> - **Frequency:** Each exception cycle (in practice weekly, following the Thursday check run)
> - **Owner:** Accounts Payable Manager

> **CONTROL — CTRL-002:** Default-return configuration: an exception item receiving no decision by the deadline is returned, not paid — a deliberate fail-safe so that an unattended fraudulent item cannot clear (SRC-001, SRC-003).
> - **Type:** Preventive
> - **Frequency:** Continuous (bank configuration)
> - **Owner:** Corporate Controller

> **CONTROL — CTRL-003:** ACH debit block with filter list on the operating account: only two originators — the payroll processor and the health plan — are authorized to debit the account; all other presented debits are rejected automatically (SRC-003, SRC-005). This standing bank-side companion control generates no exception queue; unauthorized debits simply bounce.
> - **Type:** Preventive
> - **Frequency:** Continuous (bank configuration)
> - **Owner:** Corporate Controller

### Outputs

- **Dispositioned exception items:** pay or return decision recorded in Chase Connect for each flagged check (SRC-001).
- **Returned items:** checks returned by decision or by the default-return configuration (SRC-001, SRC-003).
- **Evidence retained:** The pay/return decision is recorded only in Chase Connect's decision log; no NetSuite record or email trail of the disposition is kept (process owner confirmation via the gap workbook).

### Known Issues & Improvement Opportunities

> **PAIN POINT — PP-001:** Exception disposition is a single-person dependency with a hard, short window: only the Accounts Payable Manager reviews exceptions, decisions are due within roughly three hours of the items posting (10 AM to 1 PM Friday), no backup dispositioner was identified, and the deadline has been missed once — triggering a default return (SRC-001, SRC-003, SRC-005).
> - **Impact:** A missed window returns every undecided item, including legitimate Company checks — the fail-safe protects against fraud but converts an absence or a busy Friday morning into returned vendor payments.
> - **Severity:** Medium

> **PAIN POINT — PP-002:** The Company still issues roughly thirty checks per week — described by the Accounts Payable Manager as "we still cut checks, sadly" — sustaining the positive pay exception workload and the check-fraud exposure it guards against (SRC-001, SRC-005).
> - **Impact:** Ongoing weekly exception-handling effort and residual check-fraud risk that would shrink or disappear if check volume migrated to electronic payment.
> - **Severity:** Low

> **PAIN POINT — PP-003:** Evidence of each exception disposition exists only in Chase Connect's decision log — no NetSuite record or email trail is retained, a thinness the process owner acknowledged (process owner confirmation via the gap workbook).
> - **Impact:** The Company's audit trail for pay/return decisions depends entirely on a bank-side system; there is no Company-retained record supporting or explaining a disposition.
> - **Severity:** Low

> **IMPROVEMENT OPPORTUNITY — IO-001:** Designate and entitle a backup dispositioner in Chase Connect (with a documented reissue path for items returned by default), so the pay/return decision does not depend on one individual's availability inside a three-hour window.
> - **Addresses:** PP-001

> **IMPROVEMENT OPPORTUNITY — IO-002:** Migrate remaining check-paid suppliers to ACH to reduce weekly check volume and, with it, the positive pay exception workload and check-fraud exposure.
> - **Addresses:** PP-001, PP-002

> **IMPROVEMENT OPPORTUNITY — IO-003:** Retain Company-side evidence of each exception disposition — e.g. a periodic export of the Chase Connect decision log, or a brief note on the NetSuite payment record for any returned item — so the disposition trail does not live solely in the bank's system.
> - **Addresses:** PP-003

```consult-meta
systems: [chase-connect, netsuite]
roles:   [ap-manager, corporate-controller, supplier]
```
