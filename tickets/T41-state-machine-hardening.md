# T41 — `state_machine.py` hardening

**Slice 3 · Wave 2 (parallel) · Depends: T40 · Touches: `scripts/state_machine.py`**

## Fixes (from review)
1. **`cmd_init` directory ordering** — `edir.mkdir(parents=True)` currently runs *after*
   writes that depend on it (`state_machine.py:~196`); survives only because the node-MD
   loop happens to create the dir. A zero-L2 taxonomy → `FileNotFoundError`. Move `edir.mkdir`
   to the top of `cmd_init`.
2. **Atomic writes + engagement-level lock** — route `_save_state`, `cmd_init` state write,
   and the register write through `consult_io.write_json_atomic`; wrap each mutating command's
   read-modify-write in `consult_io.locked(<engagement>)` (single engagement lock per T40, **not**
   per-file). The lock must span the whole `add-item` → `improvement_log.py` subprocess →
   `cmd_sync` sequence; rely on T40's reentrancy so the nested `cmd_sync` doesn't re-block.
   `_next_item_id` (fix 4) must read the register *inside* that same held lock to close the
   race. Note `improvement_log.py` re-opens the register in the subprocess — holding the
   engagement lock in the parent is sufficient; do not add a second lock there.
3. **Malformed-node guards** — `derive_coverage`, `cmd_show`, `cmd_query`, `build_status`
   raw-subscript `node["counts"]`/`["lenses"]`/`["sop"]`/`["improvement"]`. Add a clean
   validation error (not `KeyError`) when a node is missing required keys; point the user at
   `validate`. Since `new_node` always emits these, any missing key means externally-corrupted
   state — raise (don't auto-heal). Keep it a **runtime** guard, not a new `validate` rule, so
   the r2r-demo fixture stays green.
4. **`_next_item_id` race / O(n)** — minting max-id+1 under no lock can duplicate ids on
   concurrent `add-item`. Mint under the register lock (T40).
5. **ISO timestamp compare** — `is_diagnosis_dirty` compares ISO strings lexically. This is
   currently *correct* (all timestamps come from `now_iso()` = UTC, microsecond precision) —
   so this is **hardening against foreign/hand-edited timestamps**, not a live bug. Parse to
   `datetime` before comparing; treat a tz-naive timestamp as UTC; preserve the strict-`>`
   microsecond tie semantics from T32.

## Tests
Extend the Slice-1 harness or add `tests/test_state_machine_hardening.sh`:
- init with an empty/zero-L2 taxonomy fixture succeeds (or errors cleanly, not a traceback);
- a node missing `counts` yields a clean validation error from `show`/`derive`;
- simulated mid-write failure on `_save_state` leaves prior `state.json` intact (T40 pattern);
- dirty predicate correct when timestamps differ only by timezone representation.

## DoD
Tests pass; `state_machine.py validate` still green on the r2r-demo fixture; no scratch left.
