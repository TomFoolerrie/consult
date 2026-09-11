# The skill contract (A27) — how anything sits on top of the engine

Status: SPEC, ruled 2026-09-11. Build tests-first. Branch `v2-skills`.

The engine enforces four things and decides nothing: auditability (every
statement walks back to an artifact, computed never labelled), progressive
disclosure (index → card → content, never cached), the client loop (asks
minted against question records, gated, settled by derivation), and the
bookkeeping nobody should hand-roll (ids, session record, checkpoints,
budget, the two gates). Everything else — which source to read, which
skill to run, what a fact means, what to ask next — is judgment, and lives
in the consultant's prompt and in skills.

A skill sits ON TOP of the engine when it reads through it, writes through
it, and returns through it. A skill that keeps its own knowledge ledger,
its own gates, or its own next-action loop inside the engagement folder
sits BESIDE the engine and is a second brain. The contract makes the first
declarable and the second impossible.

## Three ports — a skill may use these and nothing else

### 1. READ — verified, locatable, any store
`consult index` · `consult card <ref>` · `consult answer` ·
`consult source verify|excerpt|table|record` (PR #12's engine half).
Everything a skill learns comes back with a locator it can cite:
`SRC-002:L4-L9` (text lines) · `SRC-002:R7` (CSV data record) ·
`slug#Q-1` (a question record). A changed source refuses by name.

### 2. WRITE — exactly two landings
- **Work products** → `publishSynthesis(root, file, intent, inputs)`:
  immutable, every input declared with its expected hash, refuses
  collisions, requires a card beside the artifact. A skill's OWN working
  state (notes, intermediate ledgers, run logs) lives under
  `_synthesis/<skill>/<run>/` as work products with cards — visible,
  indexed, never mistaken for knowledge.
- **Capture fragments** → only under a declared grant (`writes:
  capture-fragment`), the way `procedure-draft` writes its one fragment.
Nothing else. A skill never writes a register, a pad, `_sources/`, or
another skill's directory.

### 3. RETURN — the one door for what a skill produces
`consult return <file>` lands an engine-shaped return (YAML):
```yaml
skill: consult-assessment
run: payment-review-2026-09-11
findings:            # → finding proposals (grounds validated by answers.cite)
  - claim: "Two exported rows share INV-001; whether paid twice is unresolved"
    grounds: [SRC-002:R1, SRC-002:R2, SRC-004]
    theme: payment-review
asks:                # → NOT minted; handed to the consultant (asks are its judgment)
  - text: "Please send one completed duplicate-review record"
    questions: [payment-review#Q-1]
statements:          # → handed to the consultant for fold-in; never written by return
  - slug: payment-review
    text: "The controller reports pre-payment duplicate checks"
    cites: [SRC-001:L2-L3]
artifacts:           # → must already be published; return records them on the run
  - SRC-004
flags:               # → out-of-lane observations, verbatim to the pad
  - "register completeness not confirmed"
```
`return` VALIDATES (every ground, address, slug, and artifact resolves;
locators are well-formed; artifacts are registered synthesis), MINTS the
finding proposals, RECORDS the return in the session record, and PRINTS
what it handed to the consultant (asks, statements, flags). It refuses
malformed by name and mints nothing on refusal. Symmetry: `route` is the
one door for what comes in from the world; `return` is the one door for
what skills produce.

## The manifest — a skill declares its ports
`kernel/skills/<name>.yaml` (level 1, prompt-only) or
`<dir>/skill.yaml` (level 2, has code) — same schema:
```yaml
contract: v1
name: data-wrangle
mission: "…"
recommendedClass: sonnet
reads: [sources, capture]          # subset of: sources, capture, registers, synthesis
writes: [synthesis]                # subset of: synthesis, capture-fragment  (or [])
returns: [artifacts, flags]        # subset of: findings, asks, statements, artifacts, flags
runtime: prompt                    # or { command: "python3 scripts/run.py", cwd: "." }
contextContract: [...]
returnContract: [...]
rules: [...]
origin: shipped | engagement
```
`brief.skill` refuses an unknown `contract`, an undeclared port value,
or a return kind the skill did not declare. A brief prints the declared
ports so the worker knows its walls. The eight shipped skills get
manifests.

## Conformance — proof, not hope
- `consult skill check <name>`: the STATIC half — manifest valid, ports
  declared, runtime entry exists, no `[HUMAN]`/`gate` vocabulary in a
  level-2 skill's own runner (grep, named).
- `harness/conformance.ts <name>`: the DYNAMIC half — run the skill
  against the fixture engagement and prove: it read only through the
  read port (no direct reads outside `_synthesis/<skill>/` — checked by
  file access audit where the runtime allows, else by diff), it wrote
  only under its own synthesis directory and every artifact has a card,
  every source hash is intact afterwards, its return validates through
  `consult return`, no register or pad changed, and it stopped for no
  one (exit 0 with a return, or a named refusal).
A skill that passes cannot become a second brain, whoever wrote it.

## Deliberately absent
No skill orchestrator in the engine. When to run a skill, in what order,
and what to do with its return is the consultant's judgment. A skill may
keep an internal loop for its own workers; it commands nothing outside
itself and never stops for a human. The two gates stay the only stops.

## Build order (tests first, each its own commit)
1. `src/returns.ts` + `consult return` + tests (validation, minting,
   refusal-mints-nothing, session line, printed handoff).
2. Manifest schema in `brief.ts` (contract/reads/writes/returns/runtime),
   shipped skills migrated, refusals by name, brief prints ports.
3. `consult skill check` (static) + tests.
4. `harness/conformance.ts` + fixture + a test that runs a shipped
   prompt-only skill (as a scripted stub) through it.
5. Docs: consultant.md (return port in the economy; "a skill returns,
   you land"), worker.md, DESIGN.md (verb + module rows), CHARTER A27.
Then, separately (`v2-assessment`, with the human): migrate
`packages/consult-assessment` onto the ports; re-run synthetic #5
through `return`.
