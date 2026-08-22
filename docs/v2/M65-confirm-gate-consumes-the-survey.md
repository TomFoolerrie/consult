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
order the skill documents is the order that loses the work:

1. **`--confirm` deletes the staging dir wholesale.** `do_scaffold`
   ends with `shutil.rmtree(proposed, ignore_errors=True)`
   (`scaffold.py:1443`) — the step-6 "consume the proposal set"
   discipline that stops the advisor's guard 1 from wedging. The
   comment reasons about registry files, `procedures.yaml` and
   `notes.yaml` — everything promoted or baked into the manifest by
   this pass — but `.proposed/_taxonomy/` is INSIDE the tree it
   removes, and nothing in `do_scaffold` promotes or even looks at it.

2. **The skill runs `--confirm` first.** The `confirm` row of
   `skills/consult-orchestrate/SKILL.md` instructs the orchestrator to
   run `scaffold.py --confirm` on the human's go, and only THEN
   mentions that staged taxonomy-node files "are promoted by
   `--promote-taxonomy` — run it at this gate on the same explicit
   go-ahead". An obedient orchestrator following the row top-to-bottom
   deletes the nodes before the promote verb ever runs.

3. **The no-op is graceful, so the loss is silent.**
   `promote_taxonomy` on an empty (or absent) staging dir returns
   `{"promoted": []}` by design (`scaffold.py:458–459`) — correct for
   "the human's go is safe to repeat", lethal here: the verb that
   should have moved the survey prints "nothing to promote" and exits
   0. No error, no warning, no artifact. The only content left in the
   area is the desktop-procedure skeletons `--confirm` just wrote, so
   the fill wave drafts over a survey that no longer exists.

No test covers the `--confirm` × staged-`_taxonomy` interaction — the
M37/M41/M44 suites exercise `promote_taxonomy` only in isolation.

## The shape

### Part A — `--confirm` owns the promotion

The confirm gate is ONE human go, so it becomes one verb: `do_scaffold`
promotes staged `_taxonomy/` nodes itself, BEFORE anything else is
promoted and before the rmtree — by calling the existing
`promote_taxonomy` (same collision discipline: a live-node collision
refuses BY NAME and stops the whole confirm with `.proposed/`
untouched, the same before-anything-moves rule the malformed-profile
check at `scaffold.py:1357` already enforces). The staged nodes are
gone from `.proposed/` because they were MOVED to `_taxonomy/`, so
step 6's rmtree consumes only what was actually consumed.

### Part B — the standalone verb stays, and stays honest

`--promote-taxonomy` remains for hand-run flows (a human editing the
staged set between the taxonomist and the gate). Its empty-set return
stays graceful — that contract is correct — but the CLI's report line
distinguishes "nothing staged" from "promoted N", so a log of the run
always says which happened.

### Part C — the skill row stops leading into the trap

The `confirm` row of `consult-orchestrate/SKILL.md` is rewritten: one
command (`--confirm`) does the whole gate — registry promotion, tag
replay, node promotion, skeletons, manifest — and the separate
`--promote-taxonomy` sentence becomes the hand-flow footnote it should
have been. No ordering for an orchestrator to get wrong.

## The gate

- End-to-end regression: taxonomist-staged node fragments with real
  content → `--confirm` → the same bytes live at
  `{area}/_taxonomy/<slug>.md`; `.proposed/` is gone; nothing printed
  "nothing to promote".
- Collision regression: one staged node colliding with a live node →
  the whole confirm refuses by name; `.proposed/` (nodes, registry
  proposals, `notes.yaml`) is byte-for-byte untouched.
- The standalone verb: `--promote-taxonomy` on an empty staging dir
  reports "nothing staged" distinctly from a successful promote.
- Full suite + compat gate untouched.
