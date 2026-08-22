# M65 — The confirm gate consumes the survey: staged taxonomy nodes must survive `--confirm`

**Status: RECORDED** (2026-08-22).
Origin: the first live run of the v2 pipeline over the Nordhaven
synthetic engagement (`examples/nordhaven-industrial`, run from branch
`example/nordhaven-p2p`). The taxonomist's survey notes were destroyed
at the confirm gate and the run proceeded green — data loss with
exit 0, in the release that shipped M63 "fail-loud edges".

## Why

The taxonomist stages its node fragments — the survey's actual scope
notes, written from the engagement's evidence — under
`_reference/.proposed/_taxonomy/*.md` (`scaffold.py:322`,
`PROPOSED_TAXONOMY`). The confirm gate then runs two verbs, and the
order the skill's prose presents is the order that loses the work:

1. **`--confirm` deletes the staging dir wholesale.** `do_scaffold`
   ends with `shutil.rmtree(proposed, ignore_errors=True)`
   (`scaffold.py:1443`) — the step-6 "consume the proposal set"
   discipline that stops the advisor's guard 1 from wedging. The
   comment reasons about registry files, `procedures.yaml` and
   `notes.yaml` — everything promoted or baked into the manifest by
   this pass — but `.proposed/_taxonomy/` is INSIDE the tree it
   removes, and nothing in `do_scaffold` promotes or even looks at it.

2. **The skill's prose order is the losing order.** The `confirm` row
   of `skills/consult-orchestrate/SKILL.md:300` mandates no sequence,
   but it presents `scaffold.py --confirm` first and mentions
   `--promote-taxonomy` later in the same cell ("run it at this gate
   on the same explicit go-ahead") — and the two verbs are mutually
   exclusive CLI flags (`scaffold.py:1594–1600`), so they cannot run
   in one invocation. An orchestrator following the row
   top-to-bottom deletes the nodes before the promote verb ever
   runs. A prose-sequence trap rather than a documented order — the
   distinction does not save the nodes.

3. **The no-op is graceful, so the loss is silent.**
   `promote_taxonomy` on an empty (or absent) staging dir returns
   `{"promoted": []}` by design (`scaffold.py:458–459`) — correct for
   "the human's go is safe to repeat", lethal here: the verb that
   should have moved the survey prints "no staged taxonomy nodes …
   nothing to promote" and exits 0. (That line and the success line
   are already distinct — `scaffold.py:1618–1626` — so the log says
   which happened; nothing says it is WRONG.) The only content left
   in the area is the desktop-procedure skeletons `--confirm` just
   wrote, so the fill wave drafts over a survey that no longer
   exists.

No test covers the `--confirm` × staged-`_taxonomy` interaction — the
M37/M41/M44 suites exercise `promote_taxonomy` only in isolation.

## The shape

### Part A — `--confirm` owns the promotion

The confirm gate is ONE human go, so it becomes one verb: `do_scaffold`
promotes staged `_taxonomy/` nodes itself by calling the existing
`promote_taxonomy`. Placement and error handling, precisely:

- **The COLLISION CHECK runs early** (with the malformed-profile
  check at `scaffold.py:1357` — before anything is promoted), so a
  live-node collision refuses BY NAME with `.proposed/` and the live
  folder untouched. **The MOVE runs late** — in step 6, immediately
  before the rmtree, AFTER the last raise site (manifest validation,
  `scaffold.py:1385–1390`): promoting at the top would leave nodes
  half-moved when a later validation fails, and a re-run would then
  collide against nodes the failed run itself moved.
- **The refusal must actually print as a refusal.** `main()` wraps
  only the seed/promote verbs in `try/except ScaffoldError`
  (`scaffold.py:1608–1638`); the `--confirm` call sits OUTSIDE it
  (`scaffold.py:1645`), so a `ScaffoldError` raised inside confirm
  today escapes as a raw traceback. The handler extends to cover the
  confirm path.
- **`--confirm` reports the promotion** — a "promoted taxonomy
  nodes: <slugs>" (or "no staged nodes") line joins confirm's own
  print block (`scaffold.py:1445` ff.), so the gate's log always
  states what happened to the survey. Today confirm says nothing
  about nodes at all — the same unauditability that let the loss
  hide.

The staged nodes are gone from `.proposed/` because they were MOVED
to `_taxonomy/`, so the rmtree consumes only what was actually
consumed. (`components/_client/.proposed/` — `promote_client`'s
staging area, `scaffold.py:485` ff. — is a SIBLING tree outside the
area's `.proposed/` and is untouched by all of this; stated so a
reader need not re-derive it.)

### Part B — the standalone verb stays as it is

`--promote-taxonomy` remains for hand-run flows (a human editing the
staged set between the taxonomist and the gate). Its empty-set
return stays graceful — repeat-safety is the correct contract — and
its report lines ALREADY distinguish "nothing to promote" from
"promoted: <slugs>" (`scaffold.py:1618–1626`); this part is a test
pinning that behavior, not a change. Doctrine note, so nobody
"fixes" this later: the graceful no-op is fail-loud-compatible
because Part A makes the CONSUMING verb the reporter — the silent
case that mattered (nodes destroyed upstream) can no longer occur.

### Part C — the skill row stops leading into the trap

The `confirm` row of `consult-orchestrate/SKILL.md` is rewritten: one
command (`--confirm`) does the whole gate — registry promotion, tag
replay, node promotion, skeletons, manifest — and the separate
`--promote-taxonomy` sentence becomes the hand-flow footnote it should
have been. No ordering for an orchestrator to get wrong.

## The gate

- End-to-end regression: taxonomist-staged node fragments with real
  content → `--confirm` → the same bytes live at
  `{area}/_taxonomy/<slug>.md`; `.proposed/` is gone; confirm's OWN
  report names the promoted slugs.
- Collision regression: one staged node colliding with a live node →
  the whole confirm refuses by name (clean `error:` line, no
  traceback); `.proposed/` (nodes, registry proposals, `notes.yaml`)
  AND the live folder are byte-for-byte untouched.
- Late-failure regression: a confirm that fails manifest validation
  leaves the staged nodes still in `.proposed/_taxonomy/` (nothing
  half-moved).
- The standalone verb: `--promote-taxonomy`'s two distinct report
  lines pinned by test (behavior exists today, uncovered).
- Full suite + compat gate untouched.

## Amendment A1 — corroborated by the run audit (2026-08-22)

The post-hoc audit of the Nordhaven build run (finding F3) confirms
the loss fired live and at scale: 23 staged node files — reported by
two independent taxonomist dispatches, the second describing specific
GAP edits across 16 of them by name — were gone when
`--promote-taxonomy` ran immediately after `--confirm` ("nothing to
promote"), and the area has no live `_taxonomy/` today. The audit
could not settle cause from surviving evidence because `.proposed/`
was never committed (the first checkpoint came after confirm); the
code reading in this ticket settles it — the rmtree is unconditional
and the skill's prose order is the losing one.

Two audit recommendations are adopted into the shape:

* **Part D — the post-taxonomy checkpoint is enforced, not widened.**
  Correction on review: no scope change is needed — `.proposed/` is
  area-resident, already inside the checkpoint pathspec
  (`orchestrate.py:1488`, `add -A -- .`; `AREA_GITIGNORE` does not
  exclude it), and the skill already mandates a checkpoint after
  every mutating action including the taxonomy dispatch
  (SKILL.md:233–241). The Nordhaven loss of evidence was
  orchestrator NON-COMPLIANCE with that existing rule. The fix is a
  guard, not a pathspec: the build decides where it bites (e.g. the
  advisor flags an uncommitted `.proposed/` at the confirm gate, or
  the skill row makes the pre-gate checkpoint an explicit numbered
  step). No dependency on M68.
* The engagement's lost node set is real damage to a live area, not
  just a defect record: the build carries a note that the Nordhaven
  area needs a taxonomist re-dispatch to regenerate its nodes once
  this ticket lands (or the human accepts prose-only sufficiency
  tracking for that area).
