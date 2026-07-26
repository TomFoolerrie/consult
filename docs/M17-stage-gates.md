# M17 — Stage gates (draft-ready boundary + sticky holds)

> **Status: BUILT — build order item 1 only** (`scripts/orchestrate.py`; tests in
> `tests/test_stage_gates.py`): guard 8.5, the `accept-draft` subcommand, and the
> `AREA_GITIGNORE` entry. Item 2 (`consolidate` visibility) still waits on M12 —
> the gate carries the slot with `consolidated_at_basis: null` so its shape is
> stable, and `checkpoint --stage consolidate` is NOT yet a validated name. Item 3
> (sticky holds) still waits on M13 (`_client/` resolution). Deltas from this
> design:
>
> - **The gate fires only when a spend is actually outstanding** — `synthesize`
>   (stale kinds or a pending placeholder) or `render` (no `.docx` at the current
>   basis). A gate is a stop before a cost, so with nothing left to spend there is
>   nothing to stop: an unconditional gate at 8.5 would preempt the `review` gate
>   (asking the human to accept a draft whose document they have just read), make
>   `done` unreachable, and demand a fresh accept from every area drafted before
>   M17. `render` is still fully covered, per the cost topology — it starts a human
>   cycle, so the gate stands in front of it too.
> - **`details` shape**: `draft_basis`, `question`, `would_spend`, and `answers` —
>   a LIST of `{name, command, cost, note}` for `read` / `consolidate` / `accept`,
>   always all three (the ticket's "assumption to confirm", confirmed). `read`
>   carries the real `--slugs` list; `consolidate` carries `command: null` +
>   `consolidated_at_basis: null` until M12; `accept` carries the exact
>   `accept-draft --area <area>` command.
> - **`accept_draft()` asks `decide()`** whether the area is at the gate instead
>   of re-deriving the six conditions, so the flag cannot be written for a state
>   the gate does not describe (unfilled work, a dirty reconcile, an already-open
>   ladder). `decide()` is read-only, so asking is free. No-op results carry
>   `next_action` beside the reason.
> - **`draft_basis` is `sha256(json.dumps([proc_hashes, registry_hash],
>   sort_keys=True))`** — canonical over M18's nested `{slug: {file: sha}}` shape,
>   so the key cannot drift with dict ordering.
> - **Eight existing tests pinned the pre-gate ladder** (`reconcile`-clean →
>   `synthesize`/`render`) and each gained one `accept_draft()` step:
>   `tests/test_orchestrate.py` (2), `tests/test_advisor_honesty.py` (4),
>   `tests/test_decide_states.py` (1), `tests/test_render_signal.py` (the shared
>   `_walk_to_render_guard` helper). The ladder change is the ticket; the pins were
>   correct before it.
> - **Not done here: the orchestrator's prompt.** "What the orchestrator's prompt
>   must gain" (cost column, the three answers, the dispatch-count line) is
>   untouched — `skills/consult-orchestrate/SKILL.md` was outside this pass's file
>   ownership. Until it lands, a driver following the skill has no `draft_ready`
>   handler and will stop at the gate without knowing `accept-draft` exists.

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

`.draft_ready.json` holds `{"draft_basis": <sha over proc_hashes + registry_hash>,
"accepted": true}`. The gate opens unless the recorded value equals the current
one, and a new `accept-draft` subcommand is its only writer — exactly the shape
of `accept_review()` (`scripts/orchestrate.py:460`) and its `accept` CLI wiring:
sole writer of the flag, no-op with a stated reason when there is nothing to
accept.

Keyed on a **hash of the two databases — `proc_hashes` + `registry_hash` — not a
boolean, and NOT the full `basis_hash`**. The distinction is load-bearing, and
the first revision of this ticket got it wrong: `basis_hash()` includes the
derived files, so `synthesize` rewriting `82`/`84` would re-open a gate the
human had just accepted, and every pass would demand two accepts for one
decision. The gate's question is "am I happy with the verbs and the nouns"; its
key must be exactly the verbs and the nouns. Any fragment or registry change
re-opens it; derived-view regeneration and renders do not.

`.draft_ready.json` joins the ignored signal-file family: it is added to the
`AREA_GITIGNORE` seed next to `.render.json` (advisor state, not engagement
content).

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
- `synthesize` rewrites `82`/`84` → the gate does **not** re-open. One accept
  per pass.
- Touch one fragment after accepting → the gate re-opens (draft basis changed).
- Edit `_reference/*.yaml` after accepting → the gate re-opens.
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
