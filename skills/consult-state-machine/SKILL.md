---
name: consult-state-machine
description: Single skill surface over the engagement state — the Layer 1 node tracker (state.json via state_machine.py) plus the Layer 2 item register (register.json via improvement_log.py). Granular, token-efficient discovery and mutation; orchestrator-driven deterministic Python, not a sub-agent.
---

# Skill: Engagement State Machine — Node Tracker + Item Register

## Purpose

This is the **single skill surface over the engagement state-management layer**. It wraps two coupled artifacts that live per engagement under `engagements/{id}/`:

- **Layer 1 — node tracker** `state.json`, owned by `scripts/state_machine.py`. One node per L2 taxonomy sub-function, keyed `{l1_id}.{l2_id}`. Holds per-node coverage, evidence, the 5 diagnostic lenses, SOP status, and links/counts into the register.
- **Layer 2 — item register** `register.json`, owned by `skills/consult-improvement-log/scripts/improvement_log.py`. A flat list of improvements, gaps, and screenshot placeholders, each linked to its node via `l1_cycle` / `l2_process`.

These commands are **orchestrator-driven deterministic Python** — the orchestrator calls them directly. State mutation is **NOT** a spawned sub-agent task. (Bulk reading is fanned out to sub-agents elsewhere in the pipeline; those agents return artifacts, and the orchestrator writes them in via the commands below.)

**Scripts:**
- `scripts/state_machine.py` — node tracker (this skill).
- `skills/consult-improvement-log/scripts/improvement_log.py` — item register (see also the `consult-improvement-log` skill for the full xlsx/CSV round-trip).

---

## MANDATORY: Always Use the Scripts

**The JSON state files are script-only. Never hand-edit `state.json` or `register.json`** — not with Python, not with an editor, not "just this once."

- All writes to `state.json` go through `state_machine.py`.
- All writes to `register.json` go through `improvement_log.py` (or `state_machine.py add-item`, which routes through it).
- These scripts own timestamping, coverage derivation, count roll-up, backup-before-overwrite, `record_count` sync, and schema/vocab validation that raw edits silently skip.

The only permitted direct operation on the JSON files is **reading** — and even then, prefer the granular discovery commands (`get-node`, `query`) over loading the file.

What **is** directly editable:
- **Node MDs** (`nodes/{l1}/{l2}.md`) are **LLM-owned narrative** — edit them directly.
- The **register is the human-reviewable surface**: round-trip via Excel — `build-xlsx` → human edits the workbook → `update-json` → `sync`. `state.json` is internal machinery; humans never touch it directly.

If you find yourself opening a JSON state file to mutate it: **stop, and use a command below instead.**

---

## Token-Efficiency Principle

**Never load a whole state or register file into context.** Use:

- **Granular discovery** — `get-node` for one node, `query` to get just the matching node keys. Do not `cat state.json`.
- **Granular mutation** — one field per call (`set-lens` sets one lens; `add-evidence` appends one entry). Make several small calls rather than reading + rewriting the file.

---

## Two-Layer Model & Keys

- **Node key scheme:** `{l1_id}.{l2_id}` — e.g. `record-to-report.close`, `procure-to-pay.payment`. Both ids are the kebab-case slugs from the taxonomy.
- **Taxonomy is READ-ONLY reference:** `reference/taxonomy.yaml` (7 L1 domains · 37 L2 sub-functions · 212 L3 activities) is the naming authority. Never edit it from this skill. `add-item` and `validate` refuse / report node keys not present in it.
- **One node per L2 invariant:** `init` seeds exactly one node and one MD file for every L2 — even empty ones (`coverage: none`; an empty node is itself a finding). `validate` enforces that the node set exactly matches the taxonomy L2 set.

---

## When to Use / When Not to Use

**Use this skill when you need to:**
- Seed a new engagement (`init`).
- Record a finding/gap/screenshot against a node (`add-item`).
- Set diagnostic lenses or attach evidence to a node (`set-lens`, `add-evidence`).
- Inspect or steer state (`get-node`, `query`, `show`, `validate`, `set-coverage`, `set-sop`).
- Drive the human review cycle on the register (`build-xlsx` → `update-json` → `sync`).

**Do NOT use it for:**
- Writing narrative — that goes in the node MDs, edited directly.
- The synthesis/classification judgment itself — lenses and evidence are *produced* by the classify/consolidate stages; this skill only persists their output.
- Hand-editing JSON for any reason.

---

## Command Reference — `state_machine.py`

All commands take `--engagement {id}`. Run from the repo root.

| Command | Kind | Key flags | Purpose |
|---|---|---|---|
| `init` | seed | `--engagement` (req), `--client`, `--region` (default `NA`), `--force` | Seed `state.json` + `register.json` + node MD stubs + deliverable dirs from the taxonomy. |
| `sync` | derive | `--engagement` | Roll **active** register rows into node item links/counts; recompute coverage; report orphan rows. |
| `show` | read | `--engagement` | Coverage summary + per-node line for any non-empty node. |
| `validate` | read | `--engagement` | Node set vs taxonomy + JSON Schema check. |
| `get-node` | discovery | `--node` (req), `--json` | Print one node (compact lines, or full dict with `--json`). |
| `query` | discovery | `--coverage`, `--lens-missing`, `--has-gaps`, `--has-improvements`, `--l1`, `--count` | List node keys matching ANDed filters. |
| `set-lens` | mutate | `--node`, `--lens`, `--value` (all req) | Set or clear one of the 5 lenses; recomputes coverage. |
| `add-evidence` | mutate | `--node`, `--source` (req), `--loc`, `--note` | Append an evidence entry; recomputes coverage. |
| `set-coverage` | mutate | `--node`, `--value` (req) | Set/clear a manual coverage override (or recompute via `auto`). |
| `set-sop` | mutate | `--node` (req), `--status`, `--path`, `--bump-rev` | Update a node's SOP status / path / rev (needs ≥1 of the three). |
| `add-item` | mutate | `--type`, `--l1`, `--l2` (req), `--id`, `--field KEY=VALUE` (repeatable) | Add a register row (via `improvement_log.py`) and auto-`sync`. |

### Enum values

- **`set-lens --value`** (per `--lens`; plus `null` / `none` / `clear` to clear, valid for any lens):
  - `current_state`: `present` · `absent`
  - `process`: `pain_high` · `pain_med` · `pain_low` · `strength`
  - `automation`: `machine` · `mixed` · `human`
  - `capability`: `new` · `existing`
  - `operating_model`: `central` · `mixed` · `local`
- **`set-coverage --value`**: `none` · `partial` · `covered` · `auto` (`auto` clears the override).
- **`set-sop --status`**: `not_started` · `drafting` · `draft` · `in_review` · `revised` · `final`.
- **`add-item --type`**: `improvement` · `gap` · `screenshot`. IDs auto-generate per type unless `--id` is given:
  - `improvement` → `IMP-0001`, `IMP-0002`, …
  - `gap` → `GAP-0001`, …
  - `screenshot` → `SC-0001`, …

### Examples (copy-paste; `__skilltest__` standing in for your engagement id)

```bash
# init — seed everything from the taxonomy
python3 scripts/state_machine.py init --engagement __skilltest__ --client "Acme" --region NA
# -> Initialized engagement '__skilltest__' with 37 L2 nodes at .../engagements/__skilltest__

# show — coverage summary
python3 scripts/state_machine.py show --engagement __skilltest__
# -> Engagement: __skilltest__ | client: Acme | region: NA
# -> Nodes: 37 | coverage none=37 partial=0 covered=0

# validate — node set vs taxonomy + schema
python3 scripts/state_machine.py validate --engagement __skilltest__
# -> OK: state nodes exactly match the taxonomy L2 set.
# -> Schema: OK (validates against engagement_state.schema.json).

# get-node — one node, compact
python3 scripts/state_machine.py get-node --engagement __skilltest__ --node record-to-report.close
# get-node — full dict
python3 scripts/state_machine.py get-node --engagement __skilltest__ --node record-to-report.close --json

# query — list / count node keys matching ANDed filters
python3 scripts/state_machine.py query --engagement __skilltest__ --coverage none --count
python3 scripts/state_machine.py query --engagement __skilltest__ --has-gaps
python3 scripts/state_machine.py query --engagement __skilltest__ --lens-missing process --l1 record-to-report --count

# set-lens — set one lens (recomputes coverage); clear with --value clear
python3 scripts/state_machine.py set-lens --engagement __skilltest__ --node record-to-report.close --lens current_state --value present
python3 scripts/state_machine.py set-lens --engagement __skilltest__ --node record-to-report.close --lens process --value pain_high
python3 scripts/state_machine.py set-lens --engagement __skilltest__ --node record-to-report.close --lens automation --value human
python3 scripts/state_machine.py set-lens --engagement __skilltest__ --node record-to-report.close --lens capability --value existing
python3 scripts/state_machine.py set-lens --engagement __skilltest__ --node record-to-report.close --lens operating_model --value central

# add-evidence — append one entry (--loc/--note optional)
python3 scripts/state_machine.py add-evidence --engagement __skilltest__ --node record-to-report.close \
  --source "ingested/kickoff.md" --loc "L42-58" --note "Close calendar described"

# set-coverage — manual override, then back to auto
python3 scripts/state_machine.py set-coverage --engagement __skilltest__ --node record-to-report.close --value partial
python3 scripts/state_machine.py set-coverage --engagement __skilltest__ --node record-to-report.close --value auto

# set-sop — status / path / rev (needs at least one)
python3 scripts/state_machine.py set-sop --engagement __skilltest__ --node record-to-report.close --status drafting
python3 scripts/state_machine.py set-sop --engagement __skilltest__ --node record-to-report.close --path "deliverables/sop/close.md" --bump-rev

# add-item — add a register row and auto-sync counts (IDs auto-generate)
python3 scripts/state_machine.py add-item --engagement __skilltest__ --type improvement --l1 record-to-report --l2 close \
  --field tag=automation --field observation_pain_point="Manual journal uploads"
python3 scripts/state_machine.py add-item --engagement __skilltest__ --type gap --l1 record-to-report --l2 close --field tag=owner_unknown
python3 scripts/state_machine.py add-item --engagement __skilltest__ --type screenshot --l1 record-to-report --l2 close

# sync — re-roll register rows into node counts and recompute coverage
python3 scripts/state_machine.py sync --engagement __skilltest__
# -> Synced 3 register rows into 37 nodes; 3 active items linked.
```

---

## Command Reference — Register (`improvement_log.py`)

The register is the human-reviewable surface. These four commands are the ones this skill leans on; see the `consult-improvement-log` skill for the full controlled-vocab and field reference.

| Command | Purpose |
|---|---|
| `build-xlsx` | Build the Excel review workbook from `register.json` (`--active-only` to drop archived rows). |
| `update-json` | Merge a CSV (Excel export) back into `register.json`; auto-backup when out path == in path. |
| `remove` | Archive (`--archive`) or hard-delete register rows by `--ids`. |
| `validate` | Report per-record vocab issues + counts by type (read-only); `--schema` adds a JSON Schema check. |

```bash
REG=engagements/__skilltest__/register.json

# build-xlsx — produce the human review workbook
python3 skills/consult-improvement-log/scripts/improvement_log.py build-xlsx \
  --json "$REG" --xlsx engagements/__skilltest__/register_review.xlsx

# update-json — merge the human-edited CSV back in (writing to the same path auto-backs-up first)
python3 skills/consult-improvement-log/scripts/improvement_log.py update-json \
  --json "$REG" --csv register_review.csv --out-json "$REG" --modified-by "human-review"

# remove --archive — retire a row but keep history (sync then drops it from counts)
python3 skills/consult-improvement-log/scripts/improvement_log.py remove \
  --json "$REG" --ids SC-0001 --out-json "$REG" --archive --modified-by "human-review"

# validate — read-only vocab + schema check
python3 skills/consult-improvement-log/scripts/improvement_log.py validate \
  --json "$REG" --schema schemas/item_register.schema.json
```

> After any register edit (`update-json` / `remove`), run `state_machine.py sync` to re-roll counts and recompute coverage. `add-item` already syncs for you.

---

## Typical Workflows

**(a) Start an engagement**
```bash
python3 scripts/state_machine.py init --engagement {id} --client "{client}" --region NA
```

**(b) Record a finding** (auto-syncs node counts)
```bash
python3 scripts/state_machine.py add-item --engagement {id} --type improvement --l1 record-to-report --l2 close --field tag=automation
```

**(c) Diagnose a node** (set lenses ×N, attach evidence)
```bash
python3 scripts/state_machine.py set-lens --engagement {id} --node record-to-report.close --lens current_state --value present
python3 scripts/state_machine.py set-lens --engagement {id} --node record-to-report.close --lens process --value pain_high
# ...automation / capability / operating_model...
python3 scripts/state_machine.py add-evidence --engagement {id} --node record-to-report.close --source "ingested/kickoff.md" --loc "L42-58"
```

**(d) Human review cycle**
```bash
python3 skills/consult-improvement-log/scripts/improvement_log.py build-xlsx --json engagements/{id}/register.json --xlsx engagements/{id}/register_review.xlsx
# human edits register_review.xlsx, exports to register_review.csv (File → Save As → CSV UTF-8)
python3 skills/consult-improvement-log/scripts/improvement_log.py update-json --json engagements/{id}/register.json --csv register_review.csv --out-json engagements/{id}/register.json --modified-by "human-review"
python3 scripts/state_machine.py sync --engagement {id}
```

**(e) Status check / QC**
```bash
python3 scripts/state_machine.py show --engagement {id}
python3 scripts/state_machine.py query --engagement {id} --coverage none --count
python3 scripts/state_machine.py validate --engagement {id}
```

---

## Coverage Derivation Rules & Override

`sync` (and every mutation command) recomputes a node's `coverage` from its contents (spec §3):

- **`none`** — no evidence **and** no linked active items.
- **`covered`** — has evidence **and** all 5 lenses are set.
- **`partial`** — anything in between (items but no evidence, evidence but incomplete lenses, etc.).

Only **active** register rows count toward `partial`/`covered`; rows in archived/inactive/deleted-pending statuses are excluded by `sync`.

**Override:** `set-coverage --value {none|partial|covered}` writes `coverage_override`, which **takes precedence and is preserved across `sync`**. `set-coverage --value auto` clears the override and returns to derived coverage.

---

## Hand-off Boundaries

- **Lenses & evidence** are *filled by the classify/consolidate stages* (Stage 2/3). This skill only persists their output via `set-lens` / `add-evidence`.
- **Node MDs** (`nodes/{l1}/{l2}.md`) are **LLM-owned narrative**, edited directly — not through these scripts. The scripts seed the stubs at `init` and never overwrite them after (except `init --force`).
- **Structural gaps** come from the planned `scripts/gap_report.py` (stable IDs `GAP-STRUCT-{l1}-{l2}-{kind}`), which writes `type: gap` rows into the register. Substantive gaps are added by `consult-gap-analyzer`. This skill's `add-item --type gap` is for ad-hoc gap rows.
