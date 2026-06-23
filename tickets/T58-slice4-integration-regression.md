# T58 — Slice-4 integration & regression (workflow path == prose path, + cost map)

**Slice 4 (Cost & Runtime Efficiency) · Integration (build last) ·
Depends: T54, T55, T56, T57 · Touches: `tests/` (new e2e), `fixtures/` (reuse r2r demo).**

> **Why.** Slice 4 changes **how** work is dispatched (deterministic workflow) and **how** the
> classify artifact is emitted (schema-constrained) — it must **not** change the deliverables.
> This is the "prove no regression + capture the win" ticket, mirroring T20 (Slice-1 e2e) and T49
> (coverage hardening). It is the acceptance gate the other four tickets cite.

## Problem

T54–T57 are individually tested, but nothing proves end-to-end that the **workflow-driven** path
produces the **same** merged state and deliverables as today's prose path, that human gates still
fire, and that the cost map is real and content-free. Without this, "we made it cheaper" is
unverified and a silent output regression could slip in.

## Build / Tests

A new e2e (`tests/test_slice4_workflow_e2e.sh` or equiv) over the synthesized **r2r demo fixture**
(no client data), asserting:

1. **Output equivalence (the headline).** Run the engagement through the **workflow-driven**
   fan-out (T57) end-to-end to the render gate. Assert `state.json`, `register.json`, and the
   deliverable MDs are **byte-identical** to the prose-path baseline (capture/refresh the baseline
   from the current Slice-1/2 e2e). The dispatch mechanism changed; the **output must not**.
   - If constrained emission (T55 Phase 2) introduces any *benign* ordering/whitespace difference
     in `classify/*.json`, normalize-then-compare and **document** the exact allowed difference —
     do not silently widen the assertion.
2. **Constrained classify validates (T55).** Each `classify/{hash}.artifact.json` produced via the
   workflow schema path schema-validates **and** passes `validate_artifact.py` cross-field checks;
   the flat-union enum trap (`process: machine`) is still rejected.
3. **Determinism of dispatch (T54/T57).** The fan-out issues exactly one worker per target for each
   `llm_fanout` stage (assert via the mock/dry-run harness from T57).
4. **Human gates preserved (T54 hard constraint).** The run **stops at the render gate** and at any
   `status.needs_human` signal — it does **not** auto-render-and-finalize. Assert the loop halts
   where a human is owed.
5. **Cost map is real + content-free (T56).** The per-phase map emits (with `budget.spent()` deltas
   under the workflow); grep it for a known fixture content token and assert **absent**; assert the
   size figures are deterministic for the fixed fixture.
6. **No regression to prior suites.** `tests/test_slice1_e2e.sh` and the Slice-2 e2e stay green;
   `__t58__`-style scratch engagement removed via `trap cleanup EXIT`.

## DoD

- The workflow-driven path produces **byte-identical** deliverables + state to the prose-path
  baseline (or a single, documented, normalized difference) on the r2r fixture.
- Constrained classify emission validates and the cross-field gate still bites.
- Human gates demonstrably fire; the workflow never bulldozes the render hand-off.
- A content-free, deterministic per-phase cost map is produced and asserted.
- All prior e2e suites green; no scratch engagement left behind.
- This e2e is the named acceptance artifact referenced by T54/T55/T56.
