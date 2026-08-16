# M45 — The Taxonomist: one agent for survey, curation and taxonomy

**Status: BUILT** (`2.2.0-alpha.2`, gate 10/10, suite 1158) — from the
2026-08-16 architecture review, decision D3 (ruled LOOKS RIGHT). Second of
the review's five tickets (M44–M48). See Amendment A1 for build friction.

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

## Amendment A1 — build friction (recorded at close-out, 2026-08-16)

1. **Part B was wrong about `engagement.py`.** Neither agent was named
   there — the central-mode brief routing lives in `scripts/orchestrate.py`
   (`_CENTRAL_TAXONOMY_BRIEFS`), which is what got repointed. The
   `test_engagement_module_repointed` gate passed vacuously. And the
   brief-assembly merge Part B described ("one taxonomist brief") **was
   not done** — survey and curation still assemble briefs on two code
   paths (`brief.py --objective` + coverage map; `engagement.py brief`),
   both stated in the contract. **Follow-up (recorded):** one assembled
   taxonomist brief, if the two-dispatch pattern proves annoying in use.
2. **The write-rights rule the ruling under-specified, split as built:** a
   FRESH node set on a survey pass still stages under
   `.proposed/_taxonomy/` (the human confirm gate and `--promote-taxonomy`
   keep their reason to exist); only an already-live node's refinement is
   written in place. Deleting a live node is never the agent's, even under
   one-writer.
3. **Model tier:** the surveyor was opus-pinned, the librarian
   sonnet-pinned; the merged agent keeps **opus** (the survey judgment is
   the enforced one), which makes pure curation passes pricier than
   before. M48's roster audit should revisit (a tier hint per dispatch
   kind, like the revise path's).
4. **Line count −6%, not "meaningfully fewer":** the ~120 genuinely
   duplicated lines are said once, offset by the two sections the ruling
   requires (the write boundary, the explicit confirm gate). The real
   efficiency win is one dispatch and one context, not a shorter prompt.
5. Two v1 agents' STATUS banners named the old pair and were edited
   (banner sentences only, bodies byte-identical) — forced by the gate's
   no-stray-reference sweep; the v1 dispatch paths are untouched.

## Acceptance gate

`tests/test_taxonomist_m45.py` — written before the build: the new contract
exists and carries the load-bearing anchors of BOTH absorbed contracts (the
one-writer statement over `_taxonomy/`, the notes-bus boundary, the confirm
gate, the objective intake, the grooming vocabulary); the old agent files
are gone; the orchestrate skill names the taxonomist; engagement.py's brief
carries the merged sections; the M37/M41–M43 gates stay green after their
mechanical repointing.
