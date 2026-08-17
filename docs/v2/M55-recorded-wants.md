# M55 — Recorded wants: the ledger speaks, the appendix becomes optional

**Status: SPECCED** (backlog line, unscheduled — build on the human's go).
A paired-small-items ticket: two user-facing wants carried in the charter
backlog since the 2.1.0 close ("a human-readable ledger verb,
appendix-controls optionality").

## The items

### Part A — the human-readable ledger verb

The SRC ledger is YAML a human can read but nobody should have to. A
read-only verb — working name `ledger.py show [<root-or-area>]` — prints
the engagement's source picture: each SRC id with its title/path, tags,
`provenance:` (M47), and its consumption records (which areas read it
into what), plus the unconsumed tail (the M50 owed-a-read feed's raw
material). Deterministic order, read-only, brief.py idiom. Filters at
build discretion (`--unconsumed`, `--area <name>`), each just a subset of
the one rendering.

### Part B — appendix-controls optionality

The desktop procedure's controls appendix renders unconditionally; the
charter records the want to make it optional. The switch is a DEFINITION
concern, not an engine one (the M35/M38 rule): the section entry in
`desktop-procedure.yaml` gains whatever the definition language already
affords for presence (or the language gains a minimal declared
`optional:`/`when:` key if it affords nothing — the build stops for a
spec amendment if that key's design grows beyond a presence flag).
Default stays ON — v1 output is law: with no engagement opting out, every
golden and the compatibility gate are byte-identical. An engagement opts
out in user space (the `_client/deliverables/` shadow copy — the M38
mechanism), never by editing the shipped definition.

## Test impact

New gate: `tests/test_wants_m55.py` (committed with this spec; two skip
gates, one per part). Licensed edits: none — Part A is a new read-only
verb; Part B's default-ON posture is pinned by the untouched compatibility
gate and goldens. **Zero v1 tests change.** If Part B cannot land without
touching the gate, the ticket stops and the spec is amended.

## Acceptance gate

`tests/test_wants_m55.py`: `ledger.py show` renders every fixture SRC
with consumption records and flags the unconsumed tail, byte-equal across
two runs; an opted-out shadow definition renders without the appendix and
with zero shape-audit entries; the shipped definition untouched and the
compatibility gate green.
