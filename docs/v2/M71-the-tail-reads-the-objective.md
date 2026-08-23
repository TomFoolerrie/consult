# M71 — The tail reads the objective: post-draft prose still speaks v1

**Status: TICKETED.**
Origin: the second Nordhaven build run (audit 2026-08-23) reaching the
`draft_ready` gate. The gate's machinery is v2-clean — the manifest has
no agent-derived views, so `synthesize` structurally cannot fire, and
guard 10's render target is the objective's deliverable
(`findings-report`) via M66 WP2 — but every sentence AROUND that
machinery still describes the v1 desktop-procedure tail. The user's
read of the gate transcript was, verbatim, "it still feels very v1
shaped" — and the words were, even though the behavior was not.

## Why

1. **The accept answer promises a step that cannot happen.** The
   `draft_ready` gate's `accept` note reads "lets the ladder through to
   synthesize" (`orchestrate.py:1425–1426`), unconditionally. For a
   process-step area the manifest carries zero agent-derived components,
   `st.agent_derived_kinds` is empty, `stale_kinds` is always empty, and
   guard 9 can never return `synthesize`. The advisor's own
   `would_spend` already computes the truth (`render`, not
   `synthesize`) two lines below, in the same `result(...)` call
   (`orchestrate.py:1428–1429`) — the note just doesn't read it.

2. **The skill's tail narrative is the v1 tail.** The orchestrate
   skill's framing prose presents dependencies+RACI as the standing
   post-accept spend (SKILL.md:7–8, 93–99, 129) and the `draft_ready`
   row explains `would_spend` as "`synthesize` = 2 agents, or `render` =
   a human review round" (SKILL.md:311). All of it reads as the default
   shape of every engagement; for an objective-shaped one it describes
   a path that does not exist.

3. **Nothing names the actual next verb.** For a `findings-report`
   engagement the ladder past `accept` is: `render` → the deliverable
   binds `findings: accepted` → the register is empty → an honest
   "not yet" naming findings. The verb that fills the register — the
   analyst — is human-called BY DESIGN (SKILL.md:740–748: no action
   handler fires it, and that rule stands; this ticket does not touch
   it). But no gate, answer, or note ever tells the human "your
   deliverable's path runs through calling the analyst" — the machine
   drives toward a render that will politely refuse, and the human
   learns the shape of their own engagement by hitting the refusal.

The line: the LADDER became objective-shaped in M66; the CONVERSATION
the ladder has with the human did not.

## The shape

### Part A — the gate reads the deliverable it is gating for

The `draft_ready` gate's prose becomes a function of
`area_definition(folder)` (the seam guard 10 already uses):

- The `accept` note names the actual next action — "lets the ladder
  through to `<would_spend>`" — instead of hard-coding `synthesize`.
  `would_spend` is already computed; the note reads it.
- When `would_spend` is `render`, the gate carries the render TARGET
  (`definition: <name>`) so the human is told which document accepting
  leads to.
- When that definition is findings-bound and the register would report
  "not yet" (the serviceability reads named, per review:
  `definitions.serviceability_records(defn, area)` at
  `definitions.py:715`, the flat `definitions.serviceability` at
  `:768`, and the findings gap producer `_findings_gaps` at `:677` —
  reuse these, do not re-derive), the gate says so in one sentence: the
  deliverable renders from ACCEPTED findings, none exist yet, and the
  analyst is the human-called verb that proposes them. A statement of
  the path, never a dispatch: the analyst's human-trigger rule
  (M39/M49) is untouched.

### Part B — the render action refuses forward, not backward

Guard 10 today returns `render` for a deliverable whose serviceability
is "not yet" — instructing a spend that will refuse. The action carries
the serviceability report (same read as Part A): the orchestrator
relays "render would report: not yet — <gaps>" and the human decides,
instead of paying a render to learn it. `render` stays the action name
and v1 areas (always serviceable at this point) see byte-identical
output.

### Part C — the skill stops narrating v1 as the default

The skill's tail prose (the framing lines and the `draft_ready` and
`synthesize` rows) is rewritten to state the real rule: the post-accept
spend is whatever the manifest and the objective's deliverable make it
— `synthesize` exists only where the document profile declares
agent-derived views; an objective-shaped engagement's tail is
render-the-deliverable, and a findings deliverable's path runs through
the human-called analyst. The synthesize HANDLER text stays (v1 areas
still use it); only the "this is what always happens next" framing
goes.

## The gate

- Process-step fixture at draft-ready: the gate's `accept` note names
  `render` (not `synthesize`) and carries the definition name; with an
  empty findings register the gate's prose names the analyst as the
  human-called path. v1 fixture: the same gate's note names
  `synthesize` when kinds are stale — the prose now tracks
  `would_spend` in both directions.
- Guard-10 fixture, findings deliverable, empty register: the `render`
  action carries the "not yet" serviceability report; a v1 area's
  `render` action is byte-identical to today's.
- No new dispatch: nothing in the diff fires `consult-analyst` from
  any handler (asserted by the existing human-trigger doctrine tests
  if present, else by grep-shaped test).
- Test seams, per review: `test_stage_gates.py:172` pins the answers
  list and `:183` the accept COMMAND (both unchanged — Part A edits
  the note only; NO answer-list additions); `:160/:214` pin
  `would_spend` both ways (read, not changed);
  `test_serviceability_m51.py:94–105` pins records/flat PARITY
  across all three deliverables — Part A must call the named
  functions, never re-derive, or parity breaks. Sequencing (per set
  review, mandatory): M75 builds first — its asks serviceability
  producer must exist before Part A's read is written.
- Full suite + compat gate untouched.
