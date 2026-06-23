# T45 — `orchestrate.py` predicate unification + guards

**Slice 3 · Wave 2 (parallel) · Depends: — · Touches: `scripts/orchestrate.py`**

## Fixes (from review)
1. **`decide_next` vs `frontier` drift** — they disagree on `synthesize` (`decide_next`
   gates only on `synthesis.md` absence at `:208`; `frontier` also requires `drafted_any` at
   `:349`). **DECISION: `drafted_any` wins** — never synthesize before any stream is drafted,
   so `decide_next` adopts frontier's stricter predicate. Make drift structurally impossible:
   have `decide_next` consume `frontier(...)[0]` (single ordered builder) rather than
   maintaining a parallel predicate set.
2. **`_l1s_of_nodes` missing-l1 handling** (`:121`) — the fallback already exists but only
   fires when `node` is **None** (key absent); a node that *exists* but lacks/`None`s `l1` is
   still dropped by the `if l1` guard. Extend the fallback to also fire for present-but-
   malformed nodes (key split). Apply the **same fix to `_l1_ids` (`:131-137`)**, which has
   the identical gap (used by render targets). Read-only command → fall back, don't raise.
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
