## Schedule Payment

### Scope

The weekly disbursement of approved bills: proposal, Controller approval,
NACHA file build, and bank upload and release. A single L3 — the node slug is
the step slug, because nothing else groups under it.

The boundary upstream is the approved-for-payment bill, produced under
invoice-handling. Wires, manual checks and positive-pay exception handling
are payment mechanisms the client operates but were not in this engagement's
scope, so they are absent rather than empty here.

```consult-meta
systems:
  - netsuite
  - excel
  - chase-connect
roles:
  - ap-manager
  - corporate-controller
  - treasury-analyst
```
