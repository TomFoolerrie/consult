---
node: record-to-report.consolidation
l1: record-to-report
l1_name: Record to Report
l2: consolidation
l2_name: Consolidation
coverage: partial
lenses:
  current_state: present
  process: null
  automation: mixed
  capability: null
  operating_model: central
---

# Record to Report — Consolidation

## What we learned

The consolidation function operates as a mature, centralized discipline at corporate. Entity-level trial balances are loaded into a central consolidation system after recons are signed off, and intercompany (IC) eliminations are executed by that system automatically against matched IC accounts. This is a notably advanced automation posture for the elimination step.

The meaningful gap is in topside entries: these remain fully manual at the corporate level, sitting alongside an otherwise machine-driven elimination process. There is no documented policy or system configuration governing the handoff between the reconciliation sign-off and consolidation intake — the sequencing lives in institutional knowledge rather than enforced workflow controls. Regional entities are pure data providers; all consolidation judgment and review resides centrally.

Coverage is partial: the walkthrough touched data collection, IC eliminations, topside entries, and operating model, but did not reach equity accounting, variance analysis, or analytic-driven review.

## Evidence digest

**Centralized data collection and elimination automation** — The Senior Accountant confirmed that once trial balances are final, each entity submits reconciliations into the consolidation system for central loading before eliminations run. IC eliminations are described as "fairly mature, machine-driven." (`ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L22-23`, `#L26-28`)

**Manual topside entries** — In the same walkthrough, the Senior Accountant noted that topside entries are "still booked manually by corporate," creating an automation maturity gap within an otherwise automated step. (`ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L26-28`)

**Operating model — fully centralized** — Confirmed explicitly: "Consolidation is fully centralized at corporate. Regions feed data in, but the actual consolidation and corporate review happen in one central team." (`ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L33-35`)

**Handoff from recons to consolidation — undocumented** — The Controller noted that once recons are signed off, the consolidated trial balance is handed to the consolidation team for eliminations and topside entries, but acknowledged this sequencing "isn't written into any policy or system config — it lives in people's heads." (`ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L35-36`)

## Diagnosis (5 lenses)

**Current state: `present`**
The consolidation process exists and is operational. Entity data is collected centrally, IC eliminations run automatically, and topside entries are completed by a corporate team before consolidated financials are produced. The step is present and functional within the close cycle.

**Process: `null`**
Insufficient evidence to assess process formality, documented procedures, or exception-handling workflows. The handoff from recon sign-off to consolidation intake was described as undocumented, but no broader view of the end-to-end consolidation procedure (including equity accounting or variance analysis) was obtained.

**Automation: `mixed`**
IC eliminations are fully automated within the consolidation tool based on matched intercompany accounts — a mature posture. Topside entries remain entirely manual at the corporate level. The two sub-steps within the same L2 node sit at opposite ends of the automation spectrum, yielding a mixed overall assessment.

**Capability: `null`**
No evidence was gathered regarding team size, staffing tenure, training, or skill depth within the consolidation function. This lens cannot be assessed from current evidence.

**Operating model: `central`**
Explicitly confirmed. All consolidation activity — data aggregation, elimination runs, topside bookings, and corporate review — is performed by a single central team. Regional entities are data providers only, with no consolidation authority.

## Open items

- **[gap — pending register ID]** Manual topside entries represent an automation gap within an otherwise machine-driven consolidation step. Assess whether topside entry types and volumes are candidates for systemization within the consolidation tool. (`ingested/2026-06-21_recon-walkthrough.transcript.dd5170b5c7b8.md#L26-28`) — *evidence_tier: verbal*

- **[open question]** The handoff from reconciliation sign-off to consolidation intake is undocumented and relies on institutional knowledge. Whether this is a process gap warranting formal controls should be assessed in a subsequent conversation covering process documentation. (`ingested/2026-06-21_close-walkthrough.transcript.47023e6a8544.md#L35-36`)

- **[coverage gap]** Equity accounting, variance analysis, and analytic-driven review were not discussed. A targeted walkthrough of these L3 activities is needed before the consolidation node can move from `partial` to `full` coverage.
