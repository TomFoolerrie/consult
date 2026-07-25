# M17 — Stage gates (draft-ready boundary + sticky holds)

> **Status: DESIGNED.** The gate has no dependencies and can ship alone. Sticky
> holds depend on M13 (`_client/` resolution).

## Goal

Two controls over *when* the ladder commits resources:

1. **The draft-ready gate** — a stop between `reconcile` and `synthesize`, on by
   default, at the last free point after drafting.
2. **Sticky holds** — per-engagement or per-area config that turns any automatic
   action into a gate, so a policy like "never auto-render on this engagement"
   survives across runs.

## Why

`decide()` is a strict priority ladder returning exactly one next action, and
between `fill` and `review` it never stops. The first gate a human meets after
drafting is `review` (guard 11) — by which point `synthesize` has dispatched two
judgment agents and the document has rendered.

That is the wrong place for the decision people actually make. The real question
is: **am I happy with the verbs and the nouns before I pay for anything else?**
Procedures and the registry are the two databases; everything downstream is a
projection of them. Judging them is cheap, and judging them *late* is what makes
a pass expensive.

### The cost topology

| Guard | Action | Cost |
|---|---|---|
| 1 | `confirm` | human gate |
| 1.5 | `ingest_returns` | free (Python) |
| 2 | `apply_review` | **N drafter agents** |
| 2b | `review_triage` | human gate |
| 3 | `taxonomy` (initial) | **1 agent** |
| 4 | `fill` | **N drafter agents** |
| 5 | `taxonomy` (incremental) | **1 agent** |
| 6 | `aggregate` | free (Python) |
| 7 | `registry_topup` | human gate |
| 8 | `reconcile` | free (Python) |
| **8.5** | **`draft_ready`** | **human gate (new)** |
| 9 | `synthesize` | **2 agents** |
| 10 | `render` | free (Python) — but opens the human review round |
| 11 | `review` | human gate |
| 12 | `done` | — |

The boundary is precise: everything at or before 8.5 is either free or already
spent; everything after commits **agents** (`synthesize`) or **people**
(`render` → kits → review). Note `render` costs no tokens — the reason it sits
after the gate is that it starts a human cycle, which is the scarcer resource.

This is also where M12's consolidator belongs; that ticket carries the argument.

## Design

### Guard 8.5 — `draft_ready`

Fires when the area is fully drafted and verified but nothing downstream has been
committed: manifest exists, no `unfilled` sentinels, `_sources/new/` empty,
aggregate current, zero unmatched-mention warnings, reconcile clean — **and** the
gate has not been accepted for the current basis.

Returns `human_gate: true` with three answers in `details`:

- **read it** — `render.py --slugs <all procedure slugs>`, which renders
  procedures with no front/back matter and never writes `.render.json`. Free, and
  it does not advance the state machine.
- **consolidate** — dispatch M12.
- **accept** — `orchestrate.py accept-draft --area <area>`, which lets guard 9
  through.

### Clearing it — mirror `accept_review`

`.draft_ready.json` holds `{"basis": <basis_hash>, "accepted": true}`. The gate
opens unless the recorded basis equals the current one, and a new
`accept-draft` subcommand is its only writer — exactly the shape of
`accept_review()` (`scripts/orchestrate.py:460`) and its `accept` CLI wiring:
sole writer of the flag, no-op with a stated reason when there is nothing to
accept.

Keyed on the **basis hash, not a boolean**, so any fragment or registry change
re-opens the gate. New text deserves a fresh look, and this is the same
reasoning `.render.json` already uses.

### `consolidate` becomes visible to the advisor

Today it exists only in skill prose, so `next --json` can never surface it and a
scripted driver is blind to it. It gains:

- a slot in the `draft_ready` gate's details, with `consolidated_at_basis` so the
  human can see whether this exact text already had a pass;
- validity as a `checkpoint --stage consolidate` name.

`decide()` still never *returns* `consolidate` as the action — readiness is human
judgment, per M12. Making it a visible option rather than an automatic step keeps
`decide()` pure while putting it in the machine.

> **Assumption to confirm.** The option is offered every time the gate opens,
> annotated when the basis already had a pass. The alternative — hiding it when
> nothing changed — makes the gate's shape vary run to run to save one line of
> output, and a driver then has to special-case a sometimes-absent field.

### Sticky holds

```yaml
# _client/consult.yaml  (area-level or engagement-level)
hold:
  - synthesize
  - render
```

Resolved area `_client/` first, then `components/_client/`, merged per top-level
key with the same level-provenance reporting M13 specifies.

Semantics, deliberately narrow: for a held action `decide()` returns **the same
action** with `human_gate: true` and `held_by: area|engagement`. It never skips,
never reorders, never forces. The driver stops and reports
`held: synthesize (engagement)`.

A hold is config, not state — it stays until edited. There is intentionally no
"clear once" verb: a one-shot hold is the draft-ready gate, which already exists.
Unknown action names in `hold[]` **fail loud at load**, per the repo's fail-loud
parsing contract; a typo must never read as "nothing held."

### Purity is preserved

Both `.draft_ready.json` and `_client/consult.yaml` are files in the tree, so
`decide()` remains a pure function of folder state — no run state, no memory of
prior invocations. That property is what makes the advisor restartable and
testable, and nothing here weakens it.

### What the orchestrator's prompt must gain

The skill's action→dispatch table teaches *what to run*. The gate makes *what it
costs* something the orchestrator has to reason about, so `SKILL.md` needs:

- the cost topology above, as a column on the dispatch table;
- the gate's three answers with exact commands;
- a replacement for the line "count the drafter dispatches, everything else is
  zero." That is true today and stops being true the moment `consolidate` and
  `synthesize` both matter.

## Build order

1. Guard 8.5 + `accept-draft` (no dependencies).
2. `consolidate` visibility in the gate details (with M12).
3. Sticky holds (needs M13).

## Acceptance

- A freshly filled area returns the `draft_ready` gate, not `synthesize`, with
  `.render.json` absent.
- `accept-draft` → next call returns `synthesize`.
- Touch one fragment after accepting → the gate re-opens (basis changed).
- `accept-draft` on an area with unfilled work is a no-op with a reason.
- `hold: [synthesize]` → `synthesize` returns with `human_gate: true` and
  `held_by`; the action name is unchanged.
- An unknown name in `hold[]` fails loudly.
- `next` on any state leaves `git diff` empty — the advisor stays read-only.
- `next --json` surfaces consolidate availability at the gate.

## Out of scope

- **Forcing a stage** (`run --stage X`) — breaks folder-state-as-authority and
  can fire a stage whose preconditions do not hold.
- **Per-run `--only` flags** — run-scoped, so they cannot express engagement
  policy, and they mislead: if the ladder's next action is `aggregate`, then
  `--only fill` is a no-op, not a drafter run.
- Reordering the ladder.
- Holding a gate (a gate is already a stop).
