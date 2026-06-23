# T41 — `state_machine.py` hardening

**Slice 3 · Wave 2 (parallel) · Depends: T40 · Touches: `scripts/state_machine.py`**

## Fixes (from review)
1. **`cmd_init` directory ordering** — `edir.mkdir(parents=True)` currently runs *after*
   writes that depend on it (`state_machine.py:~196`); survives only because the node-MD
   loop happens to create the dir. A zero-L2 taxonomy → `FileNotFoundError`. Move `edir.mkdir`
   to the top of `cmd_init`.
2. **Atomic writes** — route `_save_state`, `cmd_init` state write, and the register write
   through `_io.write_json_atomic`; wrap each mutating command's read-modify-write in
   `_io.locked(state_path)`.
3. **Malformed-node guards** — `derive_coverage`, `cmd_show`, `cmd_query`, `build_status`
   directly subscript `node["counts"]`/`node["lenses"]`. Add a clean validation error
   (not `KeyError`) when a node is missing required keys; point the user at `validate`.
4. **`_next_item_id` race / O(n)** — minting max-id+1 under no lock can duplicate ids on
   concurrent `add-item`. Mint under the register lock (T40).
5. **ISO timestamp compare** — `is_diagnosis_dirty` compares ISO strings lexically. Parse to
   `datetime` before comparing so it's robust to offset/precision drift (keep the
   microsecond tie behavior documented in T32).

## Tests
Extend the Slice-1 harness or add `tests/test_state_machine_hardening.sh`:
- init with an empty/zero-L2 taxonomy fixture succeeds (or errors cleanly, not a traceback);
- a node missing `counts` yields a clean validation error from `show`/`derive`;
- simulated mid-write failure on `_save_state` leaves prior `state.json` intact (T40 pattern);
- dirty predicate correct when timestamps differ only by timezone representation.

## DoD
Tests pass; `state_machine.py validate` still green on the r2r-demo fixture; no scratch left.
