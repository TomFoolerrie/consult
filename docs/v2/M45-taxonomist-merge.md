# M45 — The Taxonomist: one agent for survey, curation and taxonomy

**Status: SPEC** — from the 2026-08-16 architecture review, decision D3
(ruled LOOKS RIGHT). Second of the review's five tickets (M44–M48).

## Why (the ruling)

The review's efficiency lens: "each time you call a specialized agent, it
costs token efficiency — they have their own prompt and you have to have a
process for them to know what to do. Sometimes it is best for the taxonomy
agent to just edit the brain." The human put **full consolidation on the
table**. The surveyor (M37), the librarian (M37) and v1's taxonomy agent
total ~1,541 lines of contract across three prompts, dispatched separately,
each re-establishing the same context (the objective, the coverage map, the
taxonomy state) before doing anything.

## The shape

**One agent: `consult-taxonomist`.** It absorbs, whole:

- the surveyor's upfront job — propose the taxonomy, assess sufficiency per
  node, feed the confirm gate (M37, M41's objective-aimed skeleton and
  seed/promote path);
- the librarian's ongoing job — placement, scoping reassessment, callout
  grooming via the hygiene feeder (M37, M43), proposals through the notes
  bus;
- v1's taxonomy agent's residue, folded or retired after an audit of what
  still dispatches it.

**Write rights (the ruled change):** the taxonomist writes
`<area>/_taxonomy/` and `<area>/_reference/.proposed/` **directly** — they
become *its files* under the one-writer rule, exactly as a drafter owns its
fragment. No more propose-a-node-through-a-side-channel for its own
domain. Everything OUTSIDE its files is unchanged: grooming another
writer's fragment stays a **proposal through the notes bus**, never an
edit.

**The human confirm gate is untouched.** Taxonomy confirmation remains the
human's call (charter guardrail); seed → refine → **promote at the gate**
(M41) is still the promotion path. What the merge removes is agent count
and prompt duplication, not a single gate.

## Parts

- **Part A — the contract.** `agents/consult-taxonomist.md`, assembled from
  the two contracts' normative content with duplication removed once:
  objective intake (M41), coverage/sufficiency verbs, the ask agenda as a
  render over the needs view (M44), placement, grooming (the hygiene
  feeder's three kinds), the notes-bus boundary for non-owned files, hard
  rules consolidated. The old files are deleted, not stubbed.
- **Part B — the dispatch surface.** `skills/consult-orchestrate/SKILL.md`
  rows and `scripts/engagement.py` brief assembly updated: `placement_brief`
  and the surveyor dispatch inputs merge into one taxonomist brief (the
  objective block, the coverage map, the hygiene section, the placement
  queue — assembled once). Any `consult-surveyor` / `consult-librarian`
  reference in skills, scripts and docs repointed or retired.
- **Part C — the tests.** M37/M41/M42/M43 prose tests grep the old
  filenames; those greps are v2 tests and MAY be updated to the new
  file (the zero-v1-edits rule is about v1's suite; the v2 prose gates
  follow their subject). The update is mechanical: same anchors, new path.

## Open questions for the spec review (resolve before build)

1. Does `consult-intake` stay separate? (Out of D3's scope — it stays.)
2. The analyst stays separate by design (assessment license, M39) — the
   merge never touches it.

## Test impact (the licensed edits — verified by grep, 2026-08-16)

New gate: `tests/test_taxonomist_m45.py` (committed with this spec, skips
until `agents/consult-taxonomist.md` exists).

Existing tests this ticket repoints — all v2 gates, all MECHANICAL (same
anchors, new path), edited in the same commit as the merge:

- `tests/test_doctrine_m42.py` — the `SURVEYOR`/`LIBRARIAN` path constants
  and `TestPopulationOwnership` (both anchors must hold on the taxonomist).
- `tests/test_hygiene_m43.py:274` — the librarian feeder grep.
- `tests/test_dispatch_hints_m37.py:78,87` — `details.brief` asserted as
  the two old agent paths; both become `agents/consult-taxonomist.md`
  (engagement.py's hint changes with them).
- `tests/test_objective_m41.py:285` — the surveyor prose admission.
- `tests/test_needs_m44.py` — the `SURVEYOR`/`LIBRARIAN` constants and the
  two prose anchors in `TestDoctrineProse`.

**Zero v1 tests change** — verified: no v1 test greps either agent file
(`test_m6_reassessment.py` mentions `consult-taxonomy` in a docstring
only, and that agent's v1 dispatch path stays untouched behind the
compatibility gate).

## Acceptance gate

`tests/test_taxonomist_m45.py` — written before the build: the new contract
exists and carries the load-bearing anchors of BOTH absorbed contracts (the
one-writer statement over `_taxonomy/`, the notes-bus boundary, the confirm
gate, the objective intake, the grooming vocabulary); the old agent files
are gone; the orchestrate skill names the taxonomist; engagement.py's brief
carries the merged sections; the M37/M41–M43 gates stay green after their
mechanical repointing.
