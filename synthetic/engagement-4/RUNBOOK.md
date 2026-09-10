# RUNBOOK — synthetic #4, the live-model run

Prerequisites: Node ≥ 22.6, Python 3.11 with python-docx (and, for the
Parquet leg, `pip install duckdb pyarrow`), the `claude` CLI. From the repo:

```
export PATH="$PWD/bin:$PATH"                  # consult on PATH
npm test                                     # green before you start
ROOT=/tmp/brightline                         # a fresh engagement root
node --experimental-strip-types harness/install.ts $ROOT --objective synthetic/engagement-4/objective.md
cp synthetic/engagement-4/seed/* $ROOT/_sources/new/
cd $ROOT && consult budget set 400000        # the sitting budget, in tokens
claude                                       # you are now talking to the consultant
```

**Sitting 1 (in the chat):** "Three things arrived from Priya — the policy,
the Q2 export, and a forwarded thread. Take them in." Then let it work: it
should read STATE, system, objective, run state and index, route the three
files with intent, dispatch intake-scan per source and land the scans,
shape a taxonomy, fold in with citations, wrangle the export, propose asks.
Answer its gate questions (spend over budget; anything client-facing) and
nothing else. It ends with check + checkpoint.

**Between sittings (in a second terminal):**
```
node --experimental-strip-types harness/client.ts $ROOT synthetic/engagement-4/script.yaml
```
The driver delivers the scripted responses for every SENT ask into
`_sources/new/` and prints what to relay.

**Sitting 2:** relay exactly what the driver printed ("Priya replied on
ASK-001 and ASK-002 — files are in new/"). Let it respond, fold in, and
render the information request. Give the send gate its yes. Checkpoint.

**Exam:** `consult answer "<each question in questions.md>"` and compare
standings. Then walk rubric.md against the folder. Write RESULTS.md next to
this file: what the model did well, where it needed the prompt to say more,
every place a verb refused it and whether the refusal was right, and the
spend lines from the session record.
