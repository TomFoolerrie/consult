# M67 — Interpreter honesty: the engine checks its Python and says so

**Status: RECORDED** (2026-08-22).
Origin: the Nordhaven build-run audit (2026-08-22), finding F1
(severity high, remediated by hand mid-run).

## Why

The plugin's scripts require Python ≥ 3.10, and nothing checks — and
nothing documents the floor either (no `pyproject.toml`, nothing in
the README). The floor is not a syntax boundary: no 3.10-only syntax
exists in `scripts/`. It is a RUNTIME one — `callouts.py` lacks
`from __future__ import annotations` and evaluates `str | None` at
def time (`callouts.py:42, 139`), so under 3.9 the `TypeError` fires
at MODULE IMPORT, through every script that transitively imports it
(`client_config`, `engagement`, `render`, `consolidate`, and so
`brief`). On the run machine the default `python3` was 3.9.6 and the
available 3.12 lacked PyYAML — and the failure mode was not a refusal
but a LIE:

1. **The first taxonomist ran degraded.** With PyYAML absent the
   dispatch ran without the coverage map, the needs view, and a true
   objective block. (Credit where due: the coverage and needs
   sections DO fail loud on exceptions — `brief.py:282–307, 324–338`
   print "UNREADABLE … report it, do not reconstruct". The defect is
   the SILENT-EMPTY paths, which produce no exception at all.)

2. **The brief mis-attributed its own failure — twice.** The primary
   site is `client_config._read_yaml`: `if yaml is None: return {}`
   (`client_config.py:126–127`), so `load(area)` carries no
   `objective` key, `objective()` returns the empty `Objective`, and
   `report_line` emits "none (no engagement objective configured)"
   (`client_config.py:818`) — a client-config fact that was FALSE,
   when the true fact was "I cannot read YAML on this interpreter."
   Same shape one block down: `needs.needs(area)` returns `[]` on the
   empty objective, so the brief prints "none — no objective-selected
   target reports a blocking need" (`brief.py:339–341`) — an
   affirmative clean-state claim, structurally worse. (The same
   `yaml is None → empty` guard pattern recurs, e.g.
   `brief.py:116–117` for the v1 sources list.) Absence-by-choice and
   absence-by-breakage render identically.

3. **The fix now lives in prompts.** Post-remediation every dispatch
   prompt carries a "use python3.12" instruction — tribal knowledge
   repeated per dispatch, exactly the workaround-in-prompts shape M68
   flags for the path bug.

## The shape

### Part A — a version gate that can actually fire

Each entry-point script refuses on `sys.version_info < (3, 10)` with
one shared message naming the running interpreter, the floor, and the
fix ("re-run as `python3.12 …`"). Two constraints the failure mode
imposes, or the guard ships dead:

- **The check runs BEFORE the first first-party import.** Under 3.9
  the `TypeError` fires while importing `callouts` transitively — a
  guard inside `main()` after `import client_config` at module top
  (`brief.py:52`) never executes. The gate is the first statements of
  each entry file, ahead of every first-party import.
- **The shared helper is itself 3.9-importable** — stdlib only, no
  `X | Y` annotations, no 3.10-dependent constructs.

### Part B — a missing dependency is a refusal, not an empty result

The silent-empty guards stop degrading in every path where the
dependency is REQUIRED for the answer — primary site
`client_config._read_yaml` (`client_config.py:126–127`), plus the
same pattern's other instances: the brief refuses loudly ("PyYAML is
not importable under <interpreter> — install it or re-run under …")
instead of printing false blocks. Both false sentences are
enumerated targets: "no engagement objective configured" AND "no
objective-selected target reports a blocking need" may only ever
mean their configured facts. A guard may stay soft only where the
missing piece is genuinely optional to the output, and then the
output SAYS the piece was skipped and why. The exception paths that
already fail loud (coverage, needs UNREADABLE lines) stay as they
are.

### Part C — the floor gets written down, the workaround retires

The dispatch-prompt "use python3.12" guidance is removed once A/B
land; the engine's own refusal now carries the fix. The ≥ 3.10 floor
is DOCUMENTED for the first time (today it is stated nowhere), in one
place the release checklist owns. (Sequencing note: M68 Part A edits
the same skill prose for the path workaround — land these two skill
edits in order, whichever ticket builds second rebases on the
first.)

## The gate

- Any entry-point script run under a < 3.10 interpreter exits
  non-zero with the shared message BEFORE any first-party import
  (one representative test, monkeypatched version tuple; plus an
  import-order assertion on the entry files).
- `brief.py` with PyYAML absent refuses naming the interpreter — and
  never prints "no engagement objective configured" OR "no
  objective-selected target reports a blocking need".
- A configured objective and an absent objective file still print
  their two distinct lines under a healthy interpreter.
- Full suite + compat gate untouched.
