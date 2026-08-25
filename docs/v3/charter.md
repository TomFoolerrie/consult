# The v3 Charter — distill, then build fresh

**Status: DRAFT — awaiting rulings on D1–D8**
**Origin:** the human's call after run 3 ("I feel like what we built is not really v2... reform this repo, or distill what we want and build fresh"), 2026-08-25. Evidence base: the run-derived tickets M65–M78, CHANGELOG 2.4.0–2.5.1, docs/retrospective-v0.md, and the three live Nordhaven runs (2026-08-22/-23/-24).

---

## 1. Why a fresh build, in one paragraph

v2 was never built as v2. It was built as 45 tickets on top of v1's chassis under a standing law that v1 output stays byte-identical, so every v2 idea was expressed as an accretion beside a v1 organ it could not remove: a second type beside `activity`, a second ledger path beside per-area sources, a second taxonomy agent beside the first, alias tables to keep dead letters alive. The three live runs then demonstrated, with unusual clarity, where the failures live. **Across all three runs the agents' error count is approximately zero; every defect lived in the harness** (M77) — and specifically in the *seams between the layers*: the confirm gate that destroyed the survey it was promoting (M65), the advisor that scoped against an empty ledger (M68), the render path that shipped placeholders under a CLEAN readiness report in a document wearing the wrong deliverable's furniture (M78), the wiped engagement that read as `done` (M78). The architecture's core ideas are proven. The body they wear is v1's, and the seams are where every run has bled.

The usual argument against a rewrite — that the code silently embeds rulings a rewrite loses — is unusually weak here, because this repo is obsessive about externalizing its rulings: they live in the tickets, the kernel YAML, the agent contracts, and 1,886 tests. The code is the cheap part. The expensive part is already written down, and this document is its distillation.

## 2. The single most damning fact

The objective of every Nordhaven run declared `deliverables: [findings-report]`. **In three runs, a findings report has never been rendered.** Run 1 died before drafting finished cleanly; run 2 stopped at the draft-ready gate with a tail that "still feels very v1 shaped" (M71); run 3 held the fill wave by design and rendered only the information request — with placeholders. Meanwhile the system carries five deliverable definitions, a review-kit loop, two synthesis agents, a consolidator, an analyst, a matrix, an agenda, and a research pass — and the runs establish that most of that surface has *never executed live* (§4). v2 optimized for breadth of capability; the engagement needed depth on one path. v3 inverts that.

## 3. What the runs proved — the KEEP list

These survive into v3 essentially as they are. Each earned its place with live evidence.

| Keep | Why the evidence says so |
|---|---|
| **The kernel language** — types, deliverable definitions, bindings, skins, four-stage fail-loud loading | The one part of v2 that IS v2. Zero run defects. The vocabulary discipline (a binding may only name what its type declares) caught real drift repeatedly in build. |
| **`process-step` capture + "capture is the brain; every document is a render over it"** | The human's own ruling (M66) and the load-bearing frame of runs 2–3. |
| **Folder state is the only state; the advisor is a pure read; the guard-table loop with human gates** | Run 2 was "a clean run" precisely when the guards finally matched reality. Defects were in individual guards, never in the shape. |
| **One writer per file; agents write only through verbs** | Run 3: "flags and tenure filed through the verbs with zero orchestrator transcription... worked on first contact" (M78). |
| **The agent contracts** — taxonomist, drafter, and their write boundaries, minting bars, brief-first discipline | The agents were the *reliable* layer, three runs running. Port near-verbatim. |
| **The ask loop** — asks register, curated-lead information request, sent/answered/settled lifecycle, route-back | Born from run 2's most painful waste ("the synthesis the engagement most needs to send a client was paid for and thrown away", M75), worked on first contact in run 3. This is v3's front door. |
| **The engagement ledger** (central, SRC minting, touches ⊆ manifest, consumption credit) | The balanced ledger is what made run 2 clean. Only the *central* half survives (see D1). |
| **The coverage map as a pure function** + the lens-conflict rule | The v0 retrospective names the lens-conflict rule "the single most valuable thing to port back," and v2 proved the pure-function form. |
| **Flags, tenure, and the standing tenancy** (M76/M77) | "A token spent on judgment must land somewhere the machine reads — a transcript is not a home." Exercised once, cleanly. |
| **Cost gates that COST, never SCOPE** (M74) and briefs-over-guards (M77) | A quarter of run 2's 1.83M tokens went to confirming absences the taxonomist had already established. Never again. |
| **Humans drop artifacts and answer gates; they never type YAML** (M78) and **`done` must not be reachable by damage** (M78) | Both written in run 3's blood. |
| **Checkpoint discipline** — git as the recovery substrate | The run-3 wipe was recovered *from git*. But checkpoints must cover the whole engagement from day one (run 1's F5 open window). |

## 4. What dies — the KILL list

Nothing here is speculative; each row is either v1's ghost or surface no live run has ever touched.

| Kill | Standing | Disposition |
|---|---|---|
| **v1 compatibility, wholesale** — `activity` type, letter/slug aliases, per-area `_sources`, `centralize`, the `_v1_*` ledger reads, the byte-identical compat gate, `consult-taxonomy` (the v1 agent) | The chassis the cancer grew on | Does not exist in v3. The v2 repo remains the oracle for anyone who ever needs v1 behavior. |
| **`desktop-procedure` as a first-class deliverable** | "Honestly unserviceable over process-step capture until reworked" (M66); never rendered post-demotion | Not in v3.0. If a client ever wants one, it is written then, as a *renderer over the brain* — the human's own words. |
| **`synthesize` + `consult-dependencies` + `consult-raci` + `scope_delta`** | Structurally unreachable on process-step capture (M71); never fired in v2 | Dead. Dependencies are already in the IPO edges; if a dependencies/RACI *view* is ever wanted, it is a python render over capture, not an agent. |
| **The review-kit loop as shipped** — kits, xlsx round-trip, screens/gaps ingest, tracked-changes apply, review_extract/apply | ~3,300 lines; never exercised by any v2 run | Not ported up front. Rebuilt (or ported from the oracle) the day a run actually reaches client review — see D4. |
| **`process-controls-matrix`, `interview-agenda`, the research pass (M47), `registers.py`, consolidator** | Tests only; no run reference | Not in v3.0. Each returns only when a run demands it, as a ticket with a run finding as its Origin. |
| **`migrate_sections.py`, `split_doc.py`, dead re-exports, the M-number archaeology in comments** | One-time/legacy/dead | Gone. v3 comments carry rulings, not history; the history stays in the oracle. |
| **Hand-rolled CLI inconsistency** | argparse here, arg-count checks there | v3 has one entry point (`consult <verb> ...`), one parser, one floor check, one console-compat shim. |

## 5. What v3.0 actually is — the spine

One mode (central). One capture type. One loop. Two deliverables. Built to survive run 4.

```
stage sources → route (intake) → taxonomy survey → confirm gate
      → ask loop (curate → accept → render INFORMATION REQUEST → send → answers route back → settle)
      → fill (drafters, cost-gated by evidence)
      → aggregate → reconcile → draft-ready gate
      → analysis (human-called) → findings accept gate
      → render FINDINGS REPORT
```

- **Two deliverables ship in v3.0:** `information-request` (the front door, proven in run 3) and `findings-report` (the declared objective, never yet delivered — v3.0's definition of done is *rendering one from a live run*). Everything else is a future ticket.
- **The analyst path is core** (see D6): it is the synthesis/decision layer the v0 retrospective names as v2's still-unrecovered loss, and it is the only road to the findings report. It stays human-called — "human-called, never dispatched" is already doctrine (M71).
- **The engine is one package** with the spine modules only: kernel/definitions, ledger, asks, findings, flags+tenure, coverage, aggregate+views, reconcile, render, orchestrate (advisor + verbs + checkpoint), brief. First-order estimate: v3.0 is roughly a third of v2's 28,600 lines.
- **Every write is a verb; every gate answer is a verb** — including `hold`/`release-hold` from day one, not as a 2.5.1 afterthought.
- **The advisor's `done` requires positive evidence of completion, not absence of work** — the run-3 lesson, structural this time.
- **Session records are contract, not heroics**: the `_records/` session file M76 specified is written by the loop, not by orchestrator virtue. The three v2 audits existing only in transcripts is a named evidence gap; v3 closes it structurally.
- **Tests:** the doctrine and behavior tests port (rewritten against the new tree); the v1-parity and compat tests do not. Suite green with zero skips remains law.

## 6. The build method — run-first, permanently

The bug history has one cause: 2.0–2.3 were written before any live run existed, and every run since has torn holes in exactly the never-run parts. The rewrite is only worth doing if it also flips the cadence:

1. **v3.0 is the spine above and nothing else.** It is done when run 4 (Nordhaven, same seed, same objective) executes end-to-end and a findings report renders.
2. **Nothing is built ahead of a run's need.** A feature enters v3 only as a ticket whose Origin is a run finding or a human call — the M65–M78 pattern, which worked, made the default instead of the correction.
3. **The v2 repo is the oracle.** It stays frozen at 2.5.1. When v3 must decide a behavior question, v2's behavior is the spec until the human rules otherwise; when a deferred subsystem (review loop, matrix) is finally needed, it is ported *from* the oracle against its tests, not reinvented.
4. **The doctrines carry over as law:** grow the tenancy, not the harness · no new persistent store without retiring one · confidence gates cost, never scope · judgment lands in files the machine reads · humans answer gates, never type YAML · `done` unreachable by damage.

## 7. The decisions that are yours — D1–D8

Each with my recommendation. Rulings get recorded here as Amendment A1.

- **D1 — One mode.** v3 is central-mode only; per-area sources do not exist. *Recommend: yes.* Every live engagement has been central; the dual path is a top-three source of seams.
- **D2 — One capture type.** `process-step` (+ `taxonomy-node`) is the only capture; `activity` dies with no compat gate. *Recommend: yes.* Your own ruling (M66) already made capture the brain.
- **D3 — The flagship.** v3.0 ships exactly two deliverables: information-request and findings-report; matrix/agenda/desktop-procedure return only on run demand. *Recommend: yes.* Three runs, one declared objective, zero findings reports — depth beats breadth.
- **D4 — The review loop.** Not ported up front; rebuilt from the oracle when a run first reaches client review. *Recommend: defer.* It is the largest never-exercised surface (~3,300 lines). Counter-argument you should weigh: run 4 could plausibly reach review, and porting mid-run is pressure. If you expect run 4 to send documents out for markup, say so and it moves into v3.0.
- **D5 — Synthesis agents.** consult-dependencies and consult-raci die; any future dependencies/RACI view is a python render over IPO edges. *Recommend: kill.* They are structurally unreachable today and their information is already captured.
- **D6 — The analyst is core.** analysis.py's four candidate feeds + consult-analyst + the findings register ship in v3.0, human-called. *Recommend: yes.* It is the only road to the flagship and the v0 retrospective's named unrecovered loss. The cheaper alternative — findings proposed ad hoc without the candidate-feed license — recreates the "likely"-shaped judgment leaks the license exists to prevent.
- **D7 — Where v3 lives.** A new repository; `consult` freezes at 2.5.1 as the oracle. *Recommend: new repo.* A clean tree is the point; an in-repo `v3/` directory would tempt every import to reach across the boundary. (Alternative: an orphan branch — same isolation, one less repo to manage. Weak preference for the new repo; either works.)
- **D8 — Definition of done for v3.0.** Run 4 on the Nordhaven seed, end-to-end, findings report rendered, session record written by the loop, zero hand-edits to engagement state. *Recommend: yes.* This makes the rewrite falsifiable — v3.0 is not "the code is nicer," it is "the thing the objective asked for in August finally exists."

---

*Amendment A1 (rulings) — pending.*
