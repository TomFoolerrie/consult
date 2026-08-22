# M67 — Interpreter honesty: the engine checks its Python and says so

**Status: RECORDED** (2026-08-22).
Origin: the Nordhaven build-run audit (2026-08-22), finding F1
(severity high, remediated by hand mid-run).

## Why

The plugin's scripts require Python ≥ 3.10, and nothing checks. On the
run machine the default `python3` was 3.9.6 (syntax error on our
sources) and the available 3.12 lacked PyYAML — and the failure mode
was not a refusal but a LIE:

1. **The first taxonomist ran degraded and half-blind.** `brief.py`
   could not import its dependencies, so the dispatch ran WITHOUT the
   coverage map, the needs view, and the objective block — the three
   inputs the brief exists to supply. The agent disclosed the
   degradation (good), but the engine never did.

2. **The brief mis-attributed its own failure.** With `yaml is None`
   the loaders return empty (`brief.py:116–117` and the same guard
   pattern throughout), so the brief printed "no engagement objective
   configured" — reporting a client-config fact that was false, when
   the true fact was "I cannot read YAML on this interpreter."
   Absence-by-choice and absence-by-breakage rendered identically.

3. **The fix now lives in prompts.** Post-remediation every dispatch
   prompt carries a "use python3.12" instruction — tribal knowledge
   repeated per dispatch, exactly the workaround-in-prompts shape M68
   flags for the path bug.

## The shape

### Part A — a version gate at every entry point

Each CLI script refuses on `sys.version_info < (3, 10)` with one
shared message naming the running interpreter, the floor, and the fix
("re-run as `python3.12 …`" / point at the plugin's documented
requirement). One helper, imported everywhere `main()` lives — not
thirty hand-rolled checks.

### Part B — a missing dependency is a refusal, not an empty result

The `yaml is None` / import-guard fallbacks stop degrading silently
in every path where the dependency is REQUIRED for the answer: the
brief refuses loudly ("PyYAML is not importable under <interpreter> —
install it or re-run under …") instead of printing empty blocks. A
guard may stay soft only where the missing piece is genuinely
optional to the output, and then the output SAYS the piece was
skipped and why. "No engagement objective configured" may only ever
mean the objective file: absence-by-choice and absence-by-breakage
get different sentences.

### Part C — the skill stops shipping the workaround

The dispatch-prompt "use python3.12" guidance is removed once A/B
land; the engine's own refusal now carries the fix. The plugin's
install/requirements documentation states the ≥ 3.10 floor in one
place.

## The gate

- Any entry-point script run under a < 3.10 interpreter exits
  non-zero with the shared message (one representative test,
  monkeypatched version tuple).
- `brief.py` with PyYAML absent refuses naming the interpreter — and
  never prints "no engagement objective configured".
- A configured objective and an absent objective file still print
  their two distinct lines under a healthy interpreter.
- Full suite + compat gate untouched.
