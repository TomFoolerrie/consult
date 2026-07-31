# Known risks & unfunded work (standing doc — not a ticket)

> Source: the independent system review of 2026-07-30 (scratchpad
> `system-review.md`), triaged with the user. These are the items worth
> tracking that did NOT become ticket amendments — watch-items and blind
> spots. Each entry says what would promote it to a ticket. Prune on
> every review pass; a risk nobody revisits is worse than no list.

## Watch-items (direction known, needs evidence or a conversation)

### 1. engagement.py becoming a second orchestrator
It keeps gaining subcommands (~15 planned across M25/M27/M30) with no
advisor and no state model. The system works because it has ONE brain
(orchestrate.py) and dumb tools everywhere else. **Standing rule adopted
now:** engagement.py gets deterministic VERBS only — anything that
decides sequencing, gates, or "what next" belongs to the advisor.
**Promotes to a ticket when:** any engagement.py subcommand needs to know
about another subcommand's state, or the orchestrate skill starts
scripting multi-verb engagement.py sequences.

### 2. Adopted-source staleness (first thing to break at scale)
`adopt` takes a frozen copy of another area's prose; the copy never
learns the origin was corrected — silent, cited, client-visible drift.
Cheap detector exists in principle: the audit already reads
engagement-wide and adoption entries carry the origin `<area>/<slug>`
in their note — flag when the origin fragment's current content no
longer contains the adopted content's key claims (or simply: origin
fragment hash changed since adoption; adoption records the hash at copy
time). **Promotes to a ticket when:** the real engagement performs its
first adopt, or area count reaches ~4+ with adoptions in play.

### 3. M27 held for evidence
The detection toolkit invests ~6 query subcommands in matching machinery
M26 just demoted to a backstop, and its `answers` query re-admits the
rejected planner's anchoring risk (the ticket admits this). **Held until
the real-engagement migration run** shows what the placement/cross
passes actually needed that their briefs didn't carry. The run IS the
requirements document.

### 4. Multi-human / teammate story is absent
All six state sidecars (.draft_ready.json, .consolidate.json, etc.) are
git-ignored, so a teammate's clone forgets human acceptances; nothing
addresses two humans driving one area concurrently. Fine for a solo
consultant today — the plugin is explicitly solo-shaped. **Promotes to a
ticket when:** a second person touches an engagement. (Cheap first step
recorded: stop git-ignoring acceptance-class sidecars; they are folder
state and the doctrine says folder state is THE state.)

## Blind spots (no design yet — the review's genuinely new findings)

### 5. No gate on deliverable QUALITY
Every gate checks process quality (citations resolve, rules obeyed);
nothing checks whether the rendered document is GOOD — reads well,
flows, would impress the client. Candidate shape when taken up: a
read-the-rendered-doc review agent at the render gate (judgment, so
findings route as notes, never edits) — but design against the
gate-gaming rule.

### 6. The human bottleneck is the review round-trip, and nothing funds it
All five pending tickets improve the agent side; the slowest human-side
loop (docx out → reviewer marks up → extract → apply) gets no
investment. Revisit after the pending chain ships.

### 7. No plugin-version stamp on engagements
Mixed-version PROSE was the root cause of the user's real-engagement
pain; mixed-version ENGAGEMENTS will recur it — nothing records which
plugin version scaffolded/drafted an area. Cheap: stamp plugin version
into manifest at scaffold and into checkpoints; the audit warns on
mixed-version areas. Near-free — fold into whichever ticket next touches
scaffold.

### 8. Agent-behavior fixtures (model drift is invisible)
The test suite pins the deterministic layer thoroughly; nothing detects
an agent contract quietly degrading under a new model (e.g., the pinned
taxonomy Opus being swapped). Candidate: golden-run fixtures — a tiny
synthetic engagement whose expected agent OUTPUTS (proposal shape,
finding categories) are asserted loosely. Expensive to maintain; take
up only if a model change visibly regresses a live run first.

### 9. Client-data sprawl via copies
intake routing and adopt both multiply copies of client material across
area folders (by design — but retention/deletion at engagement end has
no story). One-line mitigation today: the engagement repo is private and
single; deletion = delete the repo. Revisit if engagements ever live
longer than their client-data retention terms.

## From the run-5 acceptance test (2026-07-31, v1.17.1 → fixes in v1.17.2)

### 10. Human decisions don't reach later subagents (run-5 finding 8)
A consolidator re-proposed a register entry the human had already
declined in the same session — dispatches don't inherit decisions unless
they live in a file the next subagent's brief actually reads. Cheap shape
when taken up: a `declined:` section in the register file itself (the
verb records a decline; `register list` shows it; briefs carry it) — the
same folder-state-is-the-state answer as everything else. **Promotes to a
ticket when:** a declined proposal is re-relayed to the human a second
time on a real engagement.

### 11. Audit fix-suggestion text is static boilerplate (run-5 finding 6)
Section-4's "run the placement pass" suggestion fires identically whether
1 or 40 gaps are plausibly cross-answerable. Minor noise; wording-level
fix whenever the audit is next touched.

Resolved from the same report in v1.17.2: the missing consult-placement
agent contract (finding 5 — file added), and the freeform-register error
message that implied a nonexistent migration path (finding 3 — message
now names the two real human paths). Finding 1 (nested orchestrator
wake-up) is addressed as skill guidance (dispatch synchronously when
running as a sub-agent); findings 2 (environment cuts), 4 and 9 (positive
signals), and 7 (alias top-ups working as intended) need no change.
