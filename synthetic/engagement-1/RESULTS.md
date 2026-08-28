# Synthetic engagement #1 — Meridian Manufacturing AP (2026-08-28)

**Verdict: PASS.** Two sittings, one full ask round, exam 6/6 on expected
standings, zero check errors at every checkpoint, all gates and spends in
the session record, zero hand-edits to any verb-owned store.

## The exam (questions.md)
| Q | expected | got |
|---|---|---|
| 1 ≥$10k approver | evidenced | evidenced [SRC-001, SRC-003] |
| 2 Dana's line, before round | contested | contested (Q-1, SRC-001 vs SRC-002) |
| 2 Dana's line, after round | evidenced | evidenced [SRC-004] — settled by fold-in, question removed |
| 3 3-way match | both readings evidenced | required [SRC-001] · violated [SRC-003], both held |
| 4 expedite path | absent, surviving the non-answer | absent → ap-payment#Q-3; ASK-002 closed with the client's own words; question stays open |
| 5 duplicates | evidenced observation, question open | evidenced [SRC-003]; ASK-003 sent, client silent — visible as awaiting-response debt |

## What the run proved
- **Settlement derived, never declared:** ASK-001 settled purely by the
  capture edit citing SRC-004; unsettled() emptied with check clean.
- **The non-answer stayed honest:** a response that answers nothing left
  the standing ABSENT; closing the ask preserved the open question.
- **The synthesis chain live:** approval-model registered with grounds
  [SRC-001, SRC-004]; the statement citing it reads evidenced THROUGH the
  chain to the primary artifacts.
- **Consumption computed:** SRC-002's outstanding debt from sitting 1
  closed itself when sitting 2's fold-in cited it; retirement followed at
  checkpoint with no declaration anywhere.
- **Recovery works:** a crashed sitting was rolled back to the previous
  checkpoint with git alone.
- **Render refuses honestly** at the docx seam by name; the plan compiled
  and all views built (information-request-v1.md in _synthesis/).

## Engine defects found by this run (all fixed, suite 52/52)
1. compilePlan handed binding NAMES to the view registry instead of
   builder kinds — the definitions↔render join was untested. Fixed;
   pinned with a new test.
2. Empty store directories do not survive git recovery — writers now
   mkdir on demand.
3. route() assumed every file lives in _sources/new/ — synthesis sources
   live in _synthesis/ and must never be moved; the ledger now records
   the real root-relative path.

## Design gap found (fixed)
4. state() had no visibility for sent-but-unanswered asks (the silent
   client). askDebts now carries awaitingResponse.

## For the cross-run analysis (D8)
Tokens: budget 200k, spent 20.8k across two sittings (estimates 23k —
overestimated ~10%). The consultant's context never held a source
document after intake; all answers came from capture. Next runs should
vary texture: a contradiction-heavy seed (#2) and a sparse seed where
most answers are honest absences (#3).
