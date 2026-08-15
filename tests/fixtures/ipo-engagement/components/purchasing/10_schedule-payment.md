## Schedule Payment

### Scope

The weekly disbursement run: selection of approved bills, Controller
approval of the proposal, and transmission and release of the ACH file.
Owner: AP Manager for the proposal, Treasury Analyst for the file, Corporate
Controller for approval. Systems: NetSuite, Excel, Chase Connect. Runs
Thursday (proposal) and Friday (release). Consumes releases from
[[match-po]] and [[approve-exceptions]]; its payment register feeds
[[reconcile-statements]]. Wires and manual checks are out of scope.

### Inputs

- Matched bill approved for payment — from [[match-po]] (NetSuite)
- Released bill approved for payment — from [[approve-exceptions]] (NetSuite)
- Cash position sheet — from the Treasury Analyst (finance shared drive)

### Transformation

The AP Manager builds the NetSuite payment proposal against due dates and
exports it to Excel for the Controller, who reviews high-value and new-payee
lines and approves by reply. Treasury then builds the NACHA file from the
NetSuite run and uploads it in Chase Connect; the Controller releases it
under a separate login. Where cash is tight the Treasury Analyst has the
proposal trimmed before approval rather than after.

1. Generate the NetSuite payment proposal for the week's due bills.
2. Export the proposal to Excel and send it to the Corporate Controller.
3. Trim the proposal against the cash position sheet if treasury calls for
   it, and re-export.
4. Obtain the Controller's approval by reply, then build the NACHA file from
   the NetSuite run.
5. Upload the file in Chase Connect (Treasury Analyst) and release it
   (Corporate Controller).

### Outputs

- NACHA payment file, released — transmitted to the bank through Chase
  Connect
- Payment register for the run — to [[reconcile-statements]] (NetSuite)

### Controls

> **CONTROL — CTRL-04:** The Corporate Controller reviews and approves the
> weekly payment proposal before any file is built; lines above twenty-five
> thousand and all new payees are reviewed individually (SRC-001, SRC-003).

> **CONTROL — CTRL-05:** Upload and release in Chase Connect are held under
> separate user IDs with separate tokens — the Treasury Analyst uploads, the
> Corporate Controller releases (SRC-003).

### Issues

> **VALIDATION REQUIRED — GAP-03:** Retention location of the
> Controller-approved payment proposal export. The Controller could locate it
> only in her mailbox and treasury works from the NetSuite run rather than
> from the approved copy, so the evidence of approval has no established
> filing location (SRC-003).

```consult-meta
systems:
  - netsuite
  - excel
  - chase-connect
  - finance-shared-drive
roles:
  - ap-manager
  - corporate-controller
  - treasury-analyst
```
