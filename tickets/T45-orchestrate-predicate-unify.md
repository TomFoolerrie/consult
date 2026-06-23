# T45 — `orchestrate.py` predicate unification + guards

**Slice 3 · Wave 2 (parallel) · Depends: — · Touches: `scripts/orchestrate.py`**

## Fixes (from review)
1. **`decide_next` vs `frontier` drift** — the two entry points reimplement readiness
   predicates separately and disagree (notably `synthesize`: `decide_next` gates only on
   `synthesis.md` absence at `:208`, `frontier` also requires `drafted_any` at `:349`).
   Extract one shared set of readiness predicates and have both call it, so `next` and
   `next --all` never report inconsistent steps for the same state.
2. **`_l1s_of_nodes` missing-l1 handling** (`:121`) — a node dict without an `l1` key yields
   `l1=None`, which the `if l1` guard drops, understating draft fan-out. Fall back to the
   key split for present-but-malformed nodes, or surface it as a validation error.
3. **Engagement-existence check** — `decide_next`/`frontier` call `build_status`/`load_state`
   with no guard; a bad `--engagement` is a raw traceback. Add a clean "no such engagement"
   message (match `render_deliverables.py:137`'s style).

## Tests
`tests/test_orchestrate_predicates.sh`:
- `next` and `next --all` agree on the recommended stage across a small matrix of crafted
   states (pre-draft, mid-draft, post-draft);
- bad `--engagement` gives a clean error, not a traceback;
- a node missing `l1` doesn't silently drop from the draft target.

## DoD
Tests pass; read-only behavior preserved (orchestrate writes nothing); no scratch left.
