# M78 — The last hundred yards: the ask loop's render path, run 3's one real bug

**Status: PROPOSED** (adversarial review applied 2026-08-24 — corrections
marked "per review" throughout; the review's findings R1–R5/H1–H7 are all
folded in).
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
   (`definitions.py:1293`); the FILL lives in `aggregate.py`'s derived
   loop (`PY_BUILDERS`, `aggregate.py:706–715`), which the improvised
   path never ran. The rendered docx carries all three content sections
   as "Pending generation." — and readiness reported CLEAN. The precise
   mechanism, per review: `_PLACEHOLDER_RE` (`render.py:708–709`)
   matches `TBD | Pending user input | Pending synthesis` — the
   `Pending generation` stub is in NO alternative; and `_readiness_scan`
   runs only under `--mode final` (`render.py:1122`) and is report-only
   without `--strict` (`render.py:1359`). Three gaps stacked; the fix
   has an exact home.

3. **The definition wears the capture document's clothes.** `render_plan`
   (`render_glue.py:280`) and the folder glue apply the v1 furniture —
   cover titled from the MANIFEST ("Procure To Pay — Process Capture"),
   TOC, Document Control, Introduction. Per review, this furniture is
   HARD-CODED glue, not data-driven: `do_cover` gates cover + Document
   Control + profile-card lift together (`render.py:1009–1015`), and the
   Introduction heading is a side effect of `emit_divider`'s
   front-matter branch (`render.py:1027–1034`). The information-request
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

`render.py --deliverable <name> <area>` (mutually exclusive with
`--slugs`; function-local imports in `main()`, per review N4 —
`render.py` imports neither `definitions` nor `render_glue` at module
scope and must not start). One command, one concrete pipeline (per
review R1 — the ticket's earlier "run the registered PY_BUILDERS"
was REFUTED: only the four `plan_views` builders take a minimal ctx;
every other registered builder KeyErrors without the big ctx
`aggregate.py` assembles at `aggregate.py:1039–1057`):

1. **Fill** = `definitions.materialize_views` → **`aggregate` over the
   area** — aggregate's derived loop (`aggregate.py:1060–1083`) is
   manifest-driven and already serves the definition's python views
   through the `PY_BUILDERS.get(kind)` fallback branch. A hand-built
   builder ctx is OUT OF BOUNDS; if the builder wants a lighter run,
   the sanctioned move is extracting aggregate's ctx assembly into a
   named function both callers share, never re-deriving it. Per review
   N6: `plan_python_kinds` resolves the OBJECTIVE definition, so the
   named `--deliverable`'s views ride the fallback branch — the builder
   either wires the `unbuildable_plan_views` refusal
   (`aggregate.py:896`) for the named definition too, or relies on
   step 2 to catch the skipped-view WARNING second-hand (builder's
   call; the gate below pins the outcome either way).
2. **Refuse on placeholders** — after fill, any view the definition
   binds still carrying the pending/`_Pending generation._` stub
   refuses the render by view name, exit nonzero, nothing written.
   SCOPE, per review H7: this refusal lives in the `--deliverable`
   path (and final mode), NOT unconditionally at the plan-render seam —
   `render_plan`'s `require_views=False` working renders of
   un-aggregated areas (`render_glue.py:302–304`) are a supported v1
   shape and must keep rendering. The readiness half of the fix:
   `Pending generation` joins `_PLACEHOLDER_RE` (`render.py:708`), so
   even the in-process path's final-mode readiness can never again
   report clean over these stubs.
3. **Compile + render** — `compile_plan` → `render_plan`, as today.

### Part B — the definition owns its shell

A definition-shaped render is titled by the DELIVERABLE, not the capture
manifest: cover title from the definition — an explicit `title:` key
added to the definition vocabulary (`_ALLOWED_TOP_KEYS`,
`definitions.py:96`, enforced at `:252` — per review R4 this is a
loader vocabulary ADDITION with its own test, not an incidental key;
name-derived default when absent). The v1 furniture (Document Control,
Introduction, TOC) is gated by the definition's `skin.requires` — per
review N7 that list is already validated vocabulary
(`definitions.py:957–963` against `RENDERERS["docx"]["capabilities"]`)
and already carries `document-control` and `toc` tokens, so no new
vocabulary is needed there. The REAL work, stated honestly (review N7):
`render_folder`'s furniture is hard-coded glue — `do_cover` currently
controls cover + Document Control + profile-card together, and the
Introduction is `emit_divider`'s front-matter side effect — so Part B
unpicks that gating for the `--deliverable` path (definition renders
consult `skin.requires`; the plain area render keeps the glue exactly
as-is). v1 byte-identity, per review H6: `materialize_views`
permanently adds the definition's view components to `manifest.json`,
so a v1 area that has run `--deliverable` renders those sections in its
AREA document too — pre-existing preservation behaviour, accepted and
stated; the golden byte-identity comparison runs over a fixture the
new verb never touched.

### Part C — the export has a home the checkpoint sees

Definition renders default to `<central_root>/_exports/` (created on
first render; `-o` still overrides), and `_checkpoint_pathspecs`
(`orchestrate.py:2007`) gains the `_exports` entry beside
`_registers`/`_records` — same one-list-three-calls, drop-if-absent
discipline (`orchestrate.py:2036–2039`). Run 3's docx sat untracked at
the engagement root outside every pathspec (audit §7-F) — an explicit
`-o`; the plain area render's default home is unchanged
(`<area>/<name>_process-doc.docx`, `render.py:1259–1261`).
"Exports are ephemeral" was the alternative ruling and it loses: the
document sent to a client is engagement state. Per review N3:
`test_flags_m76.py:448` asserts central-extra membership — extend it
with `_exports` if it pins an exact list; `:455` (v1 = exactly `["."]`)
is untouched.

### Part D — the ask register keeps up with the send

`render.py --deliverable` with `--mark-sent` runs `asks.send`
(`asks.py:319`) over the bound asks — FILTERED, per review H4, to
`status == "accepted"` only: `renderable()` returns accepted + sent
(`asks.py:397`) and `_FROM[SENT] = (ACCEPTED,)` (`asks.py:106`), so an
unfiltered sweep crashes on round two of a loop M75 explicitly designed
to run multiple rounds. Already-`sent` asks are skipped silently — they
are already the recorded state. Partial-failure rule stated: the filter
makes per-ask refusal unreachable in normal operation, and the builder
pins that a mid-list `AsksError` (register edited underfoot) stops with
the successfully-sent ids named — `_transition` persists per call, so
the register is never left inconsistent, only partially advanced, and
re-running is idempotent. One flag, default OFF — rendering a working
copy is not sending it; the skill's row tells the orchestrator to ask
the human "did/will this go to the client?" and run it on their yes
(the same answer-is-authorization pattern as Part E). Closes audit
§7-D.

### Part E — the gate answer writes the hold (M17 amendment, ruled 2026-08-24)

New verbs on `orchestrate.py`: `hold --area <area> <action>` and
`release-hold --area <area> <action>`.

**Mechanics, per review R3/H2/H3:**

- **Line surgery, not YAML round-trip.** `client_config` is
  `yaml.safe_load`-only (`client_config.py:154`) and no round-trip YAML
  dependency exists; the file is hand-authored and may carry comments.
  The verb edits the `hold:` block's LINES only and leaves every other
  byte of the file untouched — "byte-faithful" is achievable no other
  way. After the edit it re-runs `client_config.holds()` and refuses
  (restoring the original bytes) if the result is not exactly the
  intended hold set — surgery that cannot verify itself does not land.
- **Edit the OWNING file and layer.** `hold:` lives in the merged
  `_client/` namespace, only conventionally in `consult.yaml`
  (`client_config.py:37`), and a duplicate top-level key across two
  files in one layer raises (`client_config.py:186–189`) — so blindly
  creating `consult.yaml` with a second `hold:` can WEDGE every
  `decide()` call in the area. The verb locates the file that supplies
  the key (the machinery `cfg.layers` already computes,
  `client_config.py:991`) and edits that; it creates
  `<area>/_client/consult.yaml` only when NO layer supplies the key.
- **Layer shadowing is ruled, not stumbled into.** Area shadows
  engagement WHOLE (`test_sticky_holds.py:109` — no per-item merge).
  When the hold being released lives in the ENGAGEMENT layer and the
  area layer has no `hold:` key, `release-hold --area` refuses and
  names the engagement file — writing an area-level `hold: []` would
  silently release every engagement-wide hold, and holding/releasing at
  engagement scope is an edit to the engagement's file, done there.
  Same rule for `hold` when an engagement list exists: add to the list
  that is actually in effect, or refuse naming it.
- Action names validate through the existing `parse_holds` vocabulary
  (`HOLDABLE_ACTIONS`, `orchestrate.py:753`; unknown or GATE names
  refuse exactly as a typo'd hand edit does); a no-op (holding a held
  action, releasing an unheld one) refuses loudly.

**Doctrine.** It narrows, it does not fall: **no writer outside an
explicit human gate answer.** The confirm gate's "ask first" answer
runs `hold fill`; the human's later "I have what I need — draft" runs
`release-hold fill`; `accept-draft` is the standing precedent for a
verb the orchestrator runs only as the recorded outcome of a human
answer. The file stays human-editable and a hand edit still wins — the
verb is a convenience over the same file, not a new owner. No
`decide()` guard and no agent contract invokes the verbs (grep-shaped
test, the analyst human-trigger pattern);
`HOLDABLE_ACTIONS ∩ GATE_ACTIONS` stays empty (the assertion at
`test_sticky_holds.py:270` inside `:260`'s classification test —
citation corrected per review N1).

**The wall this ticket knowingly amends, per review H1/N2** (named here
so the builder edits tests as SPEC changes, not as obstacles):

- `tests/test_ask_loop_m75.py:657`
  `test_nothing_programmatic_writes_client_yaml` — greps all of
  `scripts/` for `_client`-writing lines and asserts empty. NARROW to
  "no writer outside the hold verbs' named implementation" (an
  allowlist of the verb's function, kept grep-shaped so evasion by
  line-splitting still fails).
- `tests/test_ask_loop_m75.py:637` (the gate hands over the exact
  `hold:` edit text) and `:843` (the skill relays that instruction) —
  both re-pin to the VERB: the gate's `human_action` now names
  `orchestrate.py hold --area <area> fill` run on the explicit answer.
- `skills/consult-orchestrate/SKILL.md` — FOUR sites say "no verb
  exists", not one: `:334` (confirm row), `:183` (holds are
  human-owned, no clear-once verb), `:351` (the `held_by` row), `:550`
  (gates with no verb by design). All four are rewritten to the
  narrowed doctrine; `test_sticky_holds.py:192`'s docstring is updated
  to match (its assertions survive).

### Part F — damage is not done

Per review R2, "loud non-gate state" is IMPOSSIBLE under the standing
pins (`test_decide_states.py:232` — every non-productive state is a
gate or done/error; `test_sticky_holds.py:266–270` — every action name
classified, the two sets disjoint). So the marker-missing case routes
to the EXISTING gate that already carries the right reporting contract:
**`unresolvable`** (`GATE_ACTIONS`, `orchestrate.py:766`) — `details.state`
"central marker missing", `details.why_no_stage` (no stage can restore
a deleted registry file), `details.human_action` naming exactly what
run 3's recovery did: restore `_sources/sources.yaml` from git, or
start a fresh engagement folder. No new action name, no
classification change.

Detection, per review H5, is a CONJUNCTION: walking up from the area
(stopping at the git root), fire only when some ancestor `X` has
`X/_sources/` (a directory) **AND** `X/components/` (a directory)
**AND** no `X/_sources/sources.yaml`. The earlier "or a `components/`
sibling layout" disjunction is struck — it re-opens the exact hole:
`tests/fixtures/p2p-complete/components/procure-to-pay/_sources/` is a
real v1 area with its own markerless `_sources/`, and only the
components-sibling requirement at the SAME ancestor filters it. That
fixture is the named negative pin. Read-only, checked only where the
advisor would otherwise say `done`; every v1 fixture's advisor output
byte-identical.

## The gate

- Verb round-trip: a run-3-shaped fixture (register with accepted asks,
  confirmed manifest, no drafting) → `--deliverable information-request`
  produces a docx whose three views carry real content (the asks
  section names the ask ids), titled by the definition's `title:`,
  landed in `_exports/`.
- Fill is the real pipeline: the fixture proves the aggregate-driven
  fill (a hand-ctx implementation fails the matrix/needs-bearing
  definition fixture by construction); a definition binding a kind with
  no registered builder refuses by name (or the placeholder refusal
  catches it — one of the two, pinned).
- Placeholder refusal: a builder forced to stub → refusal names the
  view, exit nonzero, no file written. `Pending generation` matches
  `_PLACEHOLDER_RE`. A v1 `require_views=False` working render of an
  un-aggregated area still renders (the H7 pin).
- Shell: the definition render carries Document Control/Introduction/
  TOC only per its `skin.requires`; `title:` is loader-validated
  vocabulary (unknown top key still refuses); the v1 area-document
  golden comparison runs over a fixture `--deliverable` never touched.
- Checkpoint: a central-mode stage with a populated `_exports/` commits
  it (M68/M76 test pattern); v1 checkpoint pathspecs stay exactly
  `["."]`.
- `--mark-sent`: accepted asks flip to `sent`; already-sent asks are
  skipped silently (second-round fixture — the loop runs twice and
  does not crash); without the flag the register is untouched.
- Hold verbs: hold/release surgery leaves every non-`hold:` byte of the
  file identical; post-edit self-verification via `client_config.holds`;
  unknown action, GATE action, no-op, and wrong-layer release all
  refuse loudly by name; the duplicate-key wedge is unreachable (fixture
  with `hold:` in a non-consult file); grep-shaped test that no
  guard/agent path names the verbs; the three re-pinned M75 tests and
  four SKILL.md sites updated as specced in Part E.
- Marker check: a central fixture with `sources.yaml` deleted →
  `unresolvable` with the marker-missing state, not `done`;
  `p2p-complete`'s v1 area pinned as the named negative; every v1
  fixture's advisor output byte-identical.
- Skill: the confirm row carries the hold verb (on explicit answer
  only) and the render row carries the one-command deliverable path.
- Full suite + compat gate untouched.
