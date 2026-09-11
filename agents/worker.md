# the worker classes — model shells that load a skill

**The distinction, ruled 2026-08-26: AGENTS pin model (and skills);
what we called templates ARE SKILLS — skills with agency.** A worker class is a thin shell that
pins exactly one thing — its model — and loads the skill it is handed.
All behavior, boundary, and license come from the skill. Three classes:

| class | model | for |
|---|---|---|
| `worker-haiku`  | cheap    | bounded reads, mechanical edits, small drafts |
| `worker-sonnet` | mid      | first drafts, structured analysis of modest feeds |
| `worker-opus`   | strong   | assessment under license, hard synthesis, review-with-edits passes |

The consultant picks CLASS and SKILL independently per dispatch — two
dials, not one: the same `procedure-draft` skill may run on haiku for a
mechanical update and on opus for a hard first draft; the same class may
run any skill. Cost estimates price the pair.

## Mission (all classes)
Execute exactly one skilled unit of work against the material the brief
resolves, and return exactly what the skill's return contract names.
Nothing outside the skill's write boundary, ever.

## What you need
One skill + parameters, composed into a brief by `brief.compose`.
Reading the brief is always the first action.

## Context provided (by the brief, never hunted for)
The resolved facts for this unit: files/sources in scope, register slices,
the consultant's standing precedent and open observations (from its
state pad), the objective's framing, the skill's rules
verbatim.

## What you return
The skill's return contract — a file written (if the skill grants
one) or structured grounded material — plus out-of-lane OBSERVATIONS
returned to the consultant, who logs them in its state pad (A9).
Never judgment the skill didn't license.

## Your walls (A27)
A skill sits ON TOP of the engine, and the manifest in your brief names the
ports you may use. Nothing else is available to you, whatever you can reach:

- **Read through the read port, with locators.** `consult index`,
  `consult card <ref>`, `consult answer`, and
  `consult source verify|excerpt|table|record`. Everything you learn comes
  back verified and citable: `SRC-002:L4-L9` for text lines, `SRC-002:R7`
  for a CSV data record, `slug#Q-1` for a question record. A source whose
  bytes changed refuses by name; you never quote around a refusal.
- **Write only under `_synthesis/<skill>/<run>/`, and only with cards.**
  Your own working state — notes, intermediate tables, run logs — is a work
  product like any other: carded, indexed, never a private store. Land every
  file through `publishSynthesis`, declaring every input with its hash; it is
  immutable, and a rerun mints a new artifact rather than editing the old one.
  Capture is off-limits unless your manifest declares
  `writes: capture-fragment` — then exactly the fragment the brief names.
- **Return through a return file.** One door: you write the engine-shaped
  YAML return OUTSIDE the stores and the consultant lands it with
  `consult return <file>` — findings become proposals, asks and statements are
  HANDED to the consultant (never minted, never written by you), artifacts are
  recorded, flags go verbatim to the pad.
- **Never a register, never a pad, never a stop.** You do not write
  `_registers/`, `STATE.md`, or `OBJECTIVE.md`, and you never pause for a
  human: the two gates are the consultant's and they are the only stops. You
  finish with a return, or with a refusal that names what stopped you.

`consult skill check <name>` proves this statically; `harness/conformance.ts`
runs the skill against a fixture engagement and proves it dynamically, naming
every path written outside these walls.

## Skills — skills with agency
A skill declares its MANIFEST — contract v1 (A27): `contract: v1`, name,
mission, `reads` (subset of sources, capture, registers, synthesis),
`writes` (subset of synthesis, capture-fragment — or `[]`), `returns`
(subset of findings, asks, statements, artifacts, flags), `runtime`
(`prompt`, or `{ command, cwd }` for a level-2 skill with code), plus the
context contract, the return contract, the rules, an `origin`
(shipped | engagement) and a RECOMMENDED class (advisory; the consultant
may override with reason, recorded). Level 1 is one YAML file; level 2 is
a directory with the manifest at its root. Two layers, same shadowing rule
as deliverable definitions:

- **shipped** — `kernel/skills/`: procedure-draft, source-read,
  assessment, data-analysis, data-wrangle (one or many data sources →
  ONE canonical dataset in _synthesis/ with its lineage — the
  engagement's single source of truth for data; cleaning one file is
  the one-input case, A21), intake-scan
  (haiku: scout one source at route time into a durable report the
  consultant lands as _sources/scans/SRC-nnn.yaml — describes the
  document, never the engagement, by default; advisory, never grounds;
  the consultant extends it by authoring a local variant, A17/A20),
  interview-guide (open question records → an agenda for the human's
  next client conversation, A24), narrative-draft (a synthesis document
  from cited capture, every sentence carrying its citation, A24). Eight
  shipped. A capture
  template is not new machinery — a capture shape IS a skill
  (procedure-draft variant), authored per engagement.
- **engagement-authored** — `<root>/_skills/`: the consultant may CREATE
  a skill ad-hoc, from scratch or as a variant of an existing one.
  Every ad-hoc skill is SAVED (never used from a prompt), logged in the
  session record, and reusable — later sittings inherit it.
  A local name shadows a shipped one.

## How you read (A22)
Your brief carries an INDEX (one line per item in the engagement) and
the CARDS of the items in scope; content is named by path. Read the
index, read the cards, and open a file only when its card says it is
the one you need. Anything you produce carries its own card: a
`scope:` line on a fragment, frontmatter on markdown, a sidecar
`<stem>.card.yaml` beside anything that cannot carry text. Same schema
as the scan. No card, no deliverable.

## The worker's tool surface for data (A21)
The ENVIRONMENT must provide Python 3.11 with python-docx (render) and
duckdb + pyarrow (data-wrangle / data-analysis over Parquet); the
classes ASSUME it is there. Nothing checks at dispatch time — a missing
library surfaces as the worker failing, not as a refusal. Canonical datasets
are Parquet; analysis is SQL over Parquet; a spreadsheet is something a
worker READS at wrangle time and never something it queries. This is
harness wiring, not engine — the same wiring the docx render worker
needs, so it lands with synthetic #4.

## How dispatch runs on the substrate (no hot-loading)
Built as `harness/` (A24): `install.ts` puts the seat and the three
class definitions into an engagement folder; see harness/README.md.

The three classes are three tiny STATIC agent definitions (model + tool
surface pinned; system prompt: "read the brief, do exactly what it says,
return what its return contract names"). The skill is NOT delivered
through the harness — agent-frontmatter `skills:` is deliberately unused
(it welds skill to agent, the v1 shape). The composed brief IS the skill
delivery: plain prompt text, resolved by `brief.compose` and handed at
dispatch. This is why an ad-hoc skill saved mid-sitting works instantly
(harness skills are discovered only at session start), why local-shadows-
shipped is our resolution logic, and why the library is portable beyond
Claude Code. Per-dispatch model choice is first-class in the Agent call;
tools can't be granted per-dispatch and don't need to be — the class's
tool surface is fixed, and the skill's write boundary narrows it as an
INSTRUCTION the composed brief carries. Nothing verifies that boundary
mechanically: `check.run` checks the record's grammar, citations,
consumption, mentions, ask coverage, registers, and cards — it does not
know which agent wrote which file. What audits the boundary is the
CHECKPOINT DIFF: the consultant reads what actually changed before it
commits, and a file outside the skill's `writes:` shows up there. The
discipline is the brief plus that read, not a mechanism.
