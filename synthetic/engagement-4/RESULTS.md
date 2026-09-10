# RESULTS — synthetic #4 (Brightline Logistics, expense reimbursement): PASS

The first run with a MODEL in the consultant seat. Two sittings; the
human (played by the build session) relayed, answered the two gates, and
ran the scripted client between sittings. Everything below was read off
the folder afterwards — nothing asserted by hand.

## Exam — 6/6 (standings from `consult answer`, never assigned)
| # | question | expected | got |
|---|---|---|---|
| Q1 | receipt threshold | evidenced (policy) | evidenced [SRC-001] |
| Q2 | does the VP actually approve over $1,000 | contested → evidenced after the round | contested after sitting 1 (question naming SRC-001 + SRC-003); evidenced after Priya's reply (SRC-005) settled ASK-001 |
| Q3 | duplicate reimbursements | evidenced (export) | evidenced [SRC-002] — R-1041/42, R-1050/51 |
| Q4 | paid without receipt over $25 | evidenced (export) | evidenced [SRC-002] — 7 of 24 named |
| Q5 | receipt exceptions granted? | absent | absent → expense-submission#Q-4 (open; the non-answer folded as a deferral, question kept) |
| Q6 | corporate card in practice | absent | absent → corporate-card#Q-1/#Q-2; policy §7 evidenced as the WRITTEN rule only |

## Rubric — every box, and the one that could not be
- Every seed routed with intent, scanned, retired: scans are narrative /
  system-export / correspondence — all three kinds exercised.
- Taxonomy: 7 nodes with scope lines (see "prompt lessons" — three are
  source-shaped and the consultant flagged that itself).
- Canonical: `te-canonical-2025q2-v1.parquet` + sidecar card + lineage
  note; 24 in / 24 out, sum-checked, nothing filled, the duplicate pairs
  CARRIED not collapsed ("whether they are duplicates is the
  consultant's question, not the wrangler's" — the never-adjudicate law,
  applied by the model unprompted). Registered as SRC-004, provenance
  synthesis, grounds SRC-002; capture cites it at row level.
- Every capture statement cited (0 uncited across 7 fragments); the
  policy/VP conflict recorded as a question naming both sources.
- One full ask round: 6 proposed → human accepted 5, held 1 → sent →
  client delivered → `ask respond` → fold-in → ASK-001 settled by
  derivation; 5 awaiting; ASK-007 proposed, accepted, sent with the
  rendered request.
- Spend: 5 lines, estimate + actual, no over-budget spend; 383,000 of
  400,000 remaining.
- Render: `information-request.docx` + card; the send gate recorded for
  the document; re-rendered after the accept (see lessons).
- `check` clean at every checkpoint (4 checkpoints, git clean).
- Session record: 13 gate lines, 5 spends, 1 budget, 4 checkpoints.
- The consultant asked the human for NOTHING that was not a spend or a
  send. Zero off-gate questions.
- FIND-001 (VP second approval never enforced by the system) proposed
  with every ground evidenced; the model WITHHELD acceptance pending an
  A11 verification dispatch it could not make; the human verified against
  the export and accepted.
- NOT met: "at least one worker dispatch" — see substrate finding 1.

## Substrate findings
1. **A nested agent has no Agent tool.** Run as a background sub-agent
   of the build session, the consultant could not dispatch workers. It
   did the skill work itself under each skill's rules (which CLAUDE.md
   permits), labelled every spend "<skill> on consultant (direct)", and
   wrote the situation into the pad as precedent P1 with "re-check each
   sitting". Under the RUNBOOK's real substrate (`claude` opened in the
   folder, the consultant as the MAIN agent) the Agent tool exists and
   `.claude/agents/worker-*` are dispatchable — the dispatch leg still
   needs that run.
2. **harness/client.ts**: a YAML flow sequence split "over $1,000" on
   its comma (fixed: terms coerced to strings; the script quotes them),
   and the first-match-per-ask rule delivered only the VP reply — the
   receipts non-answer was relayed by hand, which is exactly what a human
   would do with a second email. Documented, not changed.

## Prompt lessons (folded into agents/consultant.md)
- **Nodes are process, never sources.** Three of seven nodes were
  source-shaped (te-policy, q2-export, expensify). The model noticed
  ("partitions by source rather than objective — tolerated") but the
  prompt should have said it outright.
- **Render after the accept.** The information request was rendered
  before ASK-007 was accepted, so its Requests section was empty; the
  model noticed and re-rendered. One sentence in the prompt saves the
  round trip.
- **Retrieval is substring**: `consult answer "receipt threshold"`
  returned nothing (the statement says "$25 or more"); "$25" found it.
  The consultant phrases the probe, so this is a known limit, not a
  defect — noted for a later ruling on whether answer() should also
  match scope lines.

## What the model did well, unprompted
Cited every statement; never adjudicated (policy vs VP, duplicate pairs);
held the honest absence through a non-answer; recorded a self-caught
error (a Thursday first called a Friday) in the pad and re-landed the
scan; wrote precedent that a later sitting can inherit; withheld a
finding it could not verify; asked the human only at the gates, with a
recommendation and the cost each time.
