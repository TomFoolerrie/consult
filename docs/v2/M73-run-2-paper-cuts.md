# M73 — Run-2 paper cuts: stale contracts and undisclosed sweeps

**Status: BUILT** (`2.5.0-alpha.2`, gate 19/19 — see Amendment A1).
Origin: the second Nordhaven build run (audit 2026-08-23, findings 6.1,
7.3, 7.4). Three small items, none data loss, each a place where the
run succeeded only because the orchestrator was careful — grouped
because all three are one build day and none deserves its own ticket.

## Why

1. **The taxonomist's contract still teaches the two-verb confirm**
   (audit 7.4). M65 made `--confirm` own taxonomy promotion
   (`promote_taxonomy(area)` called inside `confirm()`,
   `scaffold.py:1598`) and rewrote the SKILL's confirm row — but
   `agents/consult-taxonomist.md` still teaches the old promoter in
   four places: two-verb pairings at lines 88–90 and 947, and
   `--promote-taxonomy` alone as the promoter at 342 and 796. The
   run's taxonomist dutifully relayed the sequence in its return; the
   orchestrator happened to know better. Failure modes, stated
   precisely (per review): both flags on ONE command line hit the
   mutual-exclusion refusal (`scaffold.py:1758–1768`); run as the two
   SEPARATE invocations the prose teaches, `--promote-taxonomy` after
   `--confirm` hits the graceful no-op ("nothing to promote", exit 0)
   — not harmful post-M65, but the agent contract asserting a false
   mechanism is the defect either way.

2. **The first checkpoint sweeps pre-session state under the wrong
   label** (audit 7.3). M68's widened pathspec is correct — engagement
   `_sources/` and `components/_client/` ride with every central-mode
   checkpoint — but it means the FIRST checkpoint of a session commits
   whatever was already dirty in those trees before the session began.
   In the run, an 11-line comment header deleted from
   `objective.yaml` pre-session was committed as
   "consult(procure-to-pay): route" — a misattributed change in the
   engagement's audit trail. Behavior by design; disclosure absent.

3. **The advisor's missing-folder error can't tell a typo from a
   fresh area** (audit 6.1). Guard 0 returns `error` ("check the
   --area name") for any absent folder (`orchestrate.py:891–896`;
   message string at 893–894).
   The run's area was a legitimately-never-scaffolded placeholder;
   the orchestrator broke the write-nothing rule with a silent
   `mkdir` because the error's only offered explanation was wrong.
   Right outcome, undisclosed deviation — invited by an error that
   knows less than it could.

## The shape

### Part A — the taxonomist contract catches up to M65

The four two-verb sites in `consult-taxonomist.md` are rewritten to
the M65 truth: the confirm gate is ONE verb (`--confirm` promotes
staged nodes itself); `--promote-taxonomy` is the hand-flow footnote.
The agent's return-instructions section stops telling the
orchestrator to run anything beyond relaying the gate.

### Part B — the checkpoint discloses what it is about to sweep

Before the FIRST checkpoint of a session (equivalently: the skill's
checkpoint duty gains a step), the orchestrator runs `git status`
over the checkpoint pathspecs and names any pre-existing dirty paths
it is about to commit — in its message to the user, before
committing. Skill-level duty, not engine change, UNLESS the build
finds a cheap engine seam (e.g. `checkpoint` printing the
about-to-be-committed paths it did not itself stage) — builder's
choice, recorded in the amendment. The pathspec itself does not
change; M68's design stands.

### Part C — the missing-folder error states both readings

Guard 0's error message distinguishes what the advisor can already
see: if the committed tree carries content under the named folder
("folder absent but committed content exists"), the message stays
typo-shaped; if it carries none, the message says so and names the
safe move ("no committed content under this path — if this is a new
area, create the folder and re-run"). Still an `error`, still exits
nonzero, still the human's call — the advisor just stops offering
only the wrong explanation. Same-diff duty (per review): the skill's
`error` row (`SKILL.md:328`) recites the current typo-only
explanation and is updated with the message, or skill and engine
contradict. Test pin (per set review): BOTH branches keep the
substring "does not exist" in `reason` — `test_advisor_honesty.py:
322–330` and `test_decide_states.py:88` assert it; the non-git
degrade path keeps today's message and its bare-tmp_path fixture;
the git-aware branch gets its own fixture.

### Part D — the register-blanks warning reaches the gate (fourth cut)

Run-2 finding 7.2, previously accepted as out of scope: the five
`reports_to` blanks are check 23 (`check_required_register_fields`,
`reconcile.py:1552–1580`), WARNING-only, surfacing only in reconcile
output after drafting shipped. One-line fix riding M76's mechanism:
the draft-ready gate's details carry the check-23 warning count
beside M76's open-flag count — same additive-details shape, no new
check, no severity change. Whichever of M73/M76 builds second wires
it.

## The gate

- Grep-shaped test: no `--confirm` + `--promote-taxonomy` sequence
  instruction remains in `consult-taxonomist.md`.
- Part C fixture: absent folder with committed content → typo-shaped
  error; absent folder with no committed content → fresh-area-shaped
  error; both exit nonzero. Non-git tree degrades to today's message.
- Part B asserted where testable (engine seam if chosen; else the
  skill row's duty text asserted by presence).
- Full suite + compat gate untouched.

## Amendment A1 — build rulings (2026-08-23)

* Part B landed as an ENGINE seam after all: `checkpoint --dry-run`
  (~12 lines, strictly read-only preview returning pathspecs + dirty
  porcelain lines). Rationale: the pathspecs are engine knowledge
  post-M68 — the orchestrator cannot run the right `git status`
  without duplicating `_checkpoint_pathspecs`. The skill duty says
  "run the dry-run, name what is pre-existing, then commit."
* Part C: `_committed_content()` probes read-only (`rev-parse` on the
  nearest existing ancestor + one `ls-tree`); unborn-HEAD repos are
  INCONCLUSIVE, not fresh-area — "no committed content" in a repo
  with no commits at all would be true and misleading. Inconclusive
  degrades to today's typo message. `details.committed_content`
  added (omitted when inconclusive).
* Part D: `_register_warnings()` is a standalone helper feeding an
  additive `extra` dict — M76's flag count slots beside it with no
  restructuring. Note for M76: most gate fixtures now carry
  `register_warnings: 1` (the shared `simple()` fixture has a
  description-less system); nothing asserts details by equality.
* Ticket precision: the four taxonomist sites were 87/90, 342, 796,
  947; only two were true two-verb pairings — both classes fixed.
