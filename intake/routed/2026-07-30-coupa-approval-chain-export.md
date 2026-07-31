# Coupa Approval Chain Export — Configuration of Record

**Pulled:** 2026-07-30, by Gideon (IT Manager), at the request of Corinne
Baptiste (Corporate Controller). Export of the live approval chain
configuration from the Coupa production tenant, annotated by Dev
(Procurement Lead) on a screen-share the same afternoon.

This is the system-of-record answer to the threshold questions that have
been circling. Values below are read directly from the configuration, not
recalled.

## 1. Requisition approval chain (chain: `REQ-STANDARD`)

| Step | Condition (requisition total) | Approver |
|---|---|---|
| 1 | all | Cost Center Manager |
| 2 | ≥ $5,000 | Procurement Lead |
| 3 | ≥ $25,000 | Chief Financial Officer |

Dev's comment on the call: "So it is twenty-five. Corinne's fifty number
was the old chain from before the Coupa migration — the export settles it."

There is **no percentage grace band anywhere in the chain configuration.**
A change order re-routes to whatever approvers the NEW total value
attracts, exactly as Yusuf described: a PO moving from $24,000 to $26,000
picks up the CFO step. The configuration has no rule that limits
re-approval to the incremental amount.

## 2. New supplier approval (chain: `SUPPLIER-ONBOARD`)

| Step | Condition (expected annual spend, entered on the supplier request) | Approver |
|---|---|---|
| 1 | all | Procurement Lead |
| 2 | ≥ $250,000 | Corporate Controller |

The $250,000 Corporate Controller threshold Dev recalled as "two-fifty" is
confirmed in configuration.

## 3. Confirming purchase orders

There is **no separate chain and no field flag** for a confirming PO in
the configuration. A PO created after the fact routes through
`REQ-STANDARD` at its full value like any other requisition. Dev: "So the
system genuinely cannot tell a confirming PO apart. If we want them
reportable, someone has to add a checkout field — today the only marker is
whatever the buyer types in the justification box."

## 4. Non-PO invoice approval (chain: `AP-NONPO`)

Confirmed as a **separate chain with different steps** from
`REQ-STANDARD`: Cost Center Manager at all values, Accounts Payable
Manager ≥ $2,500, Corporate Controller ≥ $10,000, Chief Financial Officer
≥ $50,000. The divergence between the requisition ladder and the non-PO
invoice ladder is therefore real and configured, not a misremembering.
Corinne, on being shown both chains side by side: "I want these two on one
page somewhere the whole engagement can see, because we clearly cannot
keep four numbers straight in our heads."

## 5. Not in this export

The export covers Coupa approval chains only. The NetSuite receiving
tolerances (the over-receipt question) are NetSuite configuration and are
being pulled separately by Gideon with Yusuf — see the Buyer re-interview.
