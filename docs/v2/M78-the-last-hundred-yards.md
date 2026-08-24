# M78 — The last hundred yards: the ask loop's render path, run 3's one real bug

**Status: PROPOSED.**
Origin: the third Nordhaven run (session audit 2026-08-24, the first live
exercise of the 2.5.0 ask loop). The register side of the loop worked on
first contact — the taxonomist staged 14 curated asks, confirm promoted
them, the human accepted all 14, flags and tenure filed through the verbs
with zero orchestrator transcription. Everything that failed sat in the
last hundred yards between the register and the page the client reads —
plus two frictions the same session surfaced (the hand-typed hold, and a
wiped engagement reading as a finished one).

## Why

1. **There is no command that renders a deliverable definition.** The
   skill's confirm row instructs "render `information-request`" as the
   ask-first loop's core move and names no command, because none exists:
   `render.py`'s CLI renders only the area document (no deliverable
   selector — audit §7-E). The run-3 orchestrator improvised the plan
   path in-process (`definitions.materialize_views` →
   `compile_plan` → `render_glue.render_plan`).

2. **The improvised path shipped placeholders and called it clean.**
   `materialize_views` writes the `_Pending generation._` stubs
   (`definitions.py:1293`); the FILL lives in `aggregate.py`'s
   `PY_BUILDERS` (`aggregate.py:706–715` — `build_client_asks` et al.),
   which the improvised path never ran. The rendered
   `procure-to-pay_information-request.docx` carries all three content
   sections as "Pending generation." — and the readiness scorecard
   reported CLEAN over it. A client-facing document that is 100%
   placeholder passing readiness is a fail-loud violation independent of
   how the render was driven.

3. **The definition wears the capture document's clothes.** `render_plan`
   (`render_glue.py:280`) applies the v1 furniture — cover titled from
   the MANIFEST ("Procure To Pay — Process Capture"), TOC, Document
   Control, Introduction — to every plan. The information-request
   definition has no say over its own title or shell; the user's read of
   the output was, verbatim, "it was desktop procedure shaped."

4. **Choosing ask-first means typing YAML.** M75's gate hands the human
   the two `hold:` lines to type into `_client/consult.yaml` themselves
   (the M17 zero-programmatic-writers rule). Run 3 showed where that
   lands: the human granted the orchestrator ad-hoc permission to type
   it (audit D4) — a doctrine that pushes people into improvised
   exceptions is worse than a designed path. The standing ruling from
   the design sessions applies: humans drop artifacts and answer gates;
   they don't type YAML.

5. **A wiped engagement reads as a finished one.** Deleting
   `_sources/sources.yaml` removes the central-mode marker
   (`sources.central_root`, `sources.py:112` — the file's existence IS
   the mode), so the advisor returned `done — no manifest and no sources
   to scope` (`orchestrate.py:1364`) over a damaged engagement (audit
   §7-A). The wipe itself was deliberate and needs no support — the
   ruled fix for re-scoping is a new folder, and NO ledger reset verb is
   built (the run's hand-edit stays a documented deviation, not a
   workflow). But "done" is the most trusted word the advisor can say,
   and it must not be reachable by damage.

Loose ends the same audit filed that this ticket deliberately does NOT
take: the resumed-agent stale-blocker relay (§7-B — orchestrator
diligence, skill prose at most), and any ledger repair verb (§7-C —
refused above).

## The shape

### Part A — one honest verb renders a deliverable

`render.py --deliverable <name> <area>` (builder confirms the host —
`render.py` is where every render CLI already lives; the flag is
mutually exclusive with `--slugs`). One command does the whole path, in
order:

1. **Fill** — materialize the definition's view slots and run the
   registered `PY_BUILDERS` for every python-written view the definition
   binds (the same builders `aggregate.py` dispatches; reuse, never
   re-derive — `plan_views.build_client_asks` and its siblings are the
   one implementation).
2. **Refuse on placeholders** — after fill, any bound view still
   carrying the pending/`_Pending generation._` stub refuses the render
   by view name, exit nonzero, nothing written. This check ALSO lands in
   the plan-render seam itself so the in-process path cannot ship
   placeholders either: readiness over a plan render must count a
   placeholder view as a failure, never clean (the run-3 defect,
   pinned regardless of entry point).
3. **Compile + render** — `compile_plan` → `render_plan`, as today.

### Part B — the definition owns its shell

A definition-shaped render is titled by the DELIVERABLE, not the capture
manifest: cover title from the definition (name-derived default, an
optional `title:` key in the definition YAML if the builder finds one is
needed), and the v1 capture furniture (Document Control table,
Introduction section) present only where the definition's skin asks for
it — the existing `skin.requires` list is the natural home (builder
confirms the vocabulary; `cover-page` already lives there). The v1 area
document render is byte-identical: it never passes `--deliverable` and
its plan path is untouched except for the placeholder refusal, which it
cannot trip (v1 readiness already fails pending agent views — builder
verifies and pins rather than assumes).

### Part C — the export has a home the checkpoint sees

Definition renders land in `<central_root>/_exports/` (created on first
render), and `_checkpoint_pathspecs` (`orchestrate.py:2007`) gains the
`_exports` entry beside `_registers`/`_records` — same
one-list-three-calls, drop-if-absent discipline. Run 3's docx sat
untracked at the engagement root outside every pathspec (audit §7-F);
"exports are ephemeral" was the alternative ruling and it loses: the
document sent to a client is engagement state. `-o/--output` still
overrides. v1 renders keep today's output location exactly.

### Part D — the ask register keeps up with the send

`render.py --deliverable` with `--mark-sent` runs `asks.send`
(`asks.py:319–330`) over every accepted ask the render bound — one flag,
default OFF, because rendering a working copy is not sending it. The
skill's row tells the orchestrator to ask the human "did/will this go to
the client?" and run the flag (or the `asks.py send` commands) on their
yes — the same answer-is-authorization pattern as Part E. Closes audit
§7-D without inventing a lifecycle event the human didn't confirm.

### Part E — the gate answer writes the hold (M17 amendment, ruled 2026-08-24)

New verbs on `orchestrate.py`: `hold --area <area> <action>` and
`release-hold --area <area> <action>`. They edit ONLY the `hold:` list
in `<area>/_client/consult.yaml` (round-tripping every other key
byte-faithfully; creating the file with just the hold when absent),
validate the action name through the existing
`client_config.parse_holds` vocabulary (`HOLDABLE_ACTIONS`,
`orchestrate.py:753` — an unknown or GATE_ACTIONS name refuses exactly
as a typo'd hand edit does), and refuse a no-op (holding a held action,
releasing an unheld one) loudly.

The doctrine narrows, it does not fall: **no writer outside an explicit
human gate answer.** The confirm gate's "ask first" answer runs `hold
fill`; the human's later "I have what I need — draft" runs
`release-hold fill`; `accept-draft` is the standing precedent for a verb
the orchestrator runs only as the recorded outcome of a human answer.
Pinned three ways: no `decide()` guard and no agent contract invokes the
verb (grep-shaped test, the analyst human-trigger pattern);
`HOLDABLE_ACTIONS ∩ GATE_ACTIONS` stays empty
(`test_sticky_holds.py:261` unchanged); the file stays human-editable
and a hand edit still wins — the verb is a convenience over the same
file, not a new owner. The skill's confirm row replaces "hand over the
exact instruction / there is no verb and you must not invent one" with
the verb, run only on the explicit answer.

### Part F — damage is not done

The advisor's `done — no manifest and no sources to scope` gains a
contradiction check before it speaks: walking up from the area, a
`_sources/` DIRECTORY (or a `components/` sibling layout) without the
`sources.yaml` marker is a central-shaped tree whose marker is missing —
return a loud non-gate state (`details` naming the path and the two
readings: marker deleted vs never-central) instead of `done`. Cheap,
read-only, and inert for true v1 areas (no `_sources/` dir above them
inside the repo — builder verifies against the v1 fixtures, where a
repo-root `_sources/` would false-positive, and scopes the walk
accordingly, e.g. stopping at the git root and requiring the
`components/` sibling). No ledger repair verb; the state's
`human_action` says exactly what run 3's recovery did: restore the
marker from git, or start a fresh engagement folder.

## The gate

- Verb round-trip: a run-3-shaped fixture (register with accepted asks,
  confirmed manifest, no drafting) → `--deliverable information-request`
  produces a docx whose three views carry real content (the asks
  section names the ask ids), titled as the deliverable, landed in
  `_exports/`.
- Placeholder refusal: the same fixture with a builder forced to stub →
  refusal names the view, exit nonzero, no file written; readiness over
  a placeholder plan render is never clean (pinned at the seam, not
  just the CLI).
- Shell: the definition render carries no Document Control/Introduction
  unless its skin requires them; the v1 area document render is
  byte-identical to today's (golden comparison).
- Checkpoint: a central-mode stage with a populated `_exports/` commits
  it (M68/M76 test pattern); v1 checkpoint pathspecs unchanged.
- `--mark-sent`: bound accepted asks flip to `sent` (still renderable);
  without the flag the register is untouched.
- Hold verbs: hold/release round-trip preserves unrelated consult.yaml
  keys byte-for-byte; unknown action, GATE action, and no-op all refuse
  loudly; grep-shaped test that no guard/agent path names the verbs;
  `test_sticky_holds.py` doctrine pins unchanged.
- Marker check: a central fixture with `sources.yaml` deleted → the loud
  state, not `done`; every v1 fixture's advisor output byte-identical.
- Skill: the confirm row carries the hold verb (on explicit answer
  only) and the render row carries the one-command deliverable path;
  the "no verb exists" sentence is gone.
- Full suite + compat gate untouched.
