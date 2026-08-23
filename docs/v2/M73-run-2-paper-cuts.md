# M73 — Run-2 paper cuts: stale contracts and undisclosed sweeps

**Status: TICKETED.**
Origin: the second Nordhaven build run (audit 2026-08-23, findings 6.1,
7.3, 7.4). Three small items, none data loss, each a place where the
run succeeded only because the orchestrator was careful — grouped
because all three are one build day and none deserves its own ticket.

## Why

1. **The taxonomist's contract still teaches the two-verb confirm**
   (audit 7.4). M65 made `--confirm` own taxonomy promotion and
   rewrote the SKILL's confirm row — but `agents/consult-taxonomist.md`
   still instructs `--confirm` THEN `--promote-taxonomy` in four
   places (lines 90, 342, 796, 947). The run's taxonomist dutifully
   relayed that sequence in its return; the orchestrator happened to
   know better. The flags are mutually exclusive
   (`scaffold.py:1594–1600`), so a less careful orchestrator gets a
   confusing refusal — the exact prose-sequence trap M65 closed in
   the skill, still open in the agent.

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
   --area name") for any absent folder (`orchestrate.py:890–896`).
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
only the wrong explanation.

## The gate

- Grep-shaped test: no `--confirm` + `--promote-taxonomy` sequence
  instruction remains in `consult-taxonomist.md`.
- Part C fixture: absent folder with committed content → typo-shaped
  error; absent folder with no committed content → fresh-area-shaped
  error; both exit nonzero. Non-git tree degrades to today's message.
- Part B asserted where testable (engine seam if chosen; else the
  skill row's duty text asserted by presence).
- Full suite + compat gate untouched.
