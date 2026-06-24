# T58 — Slice-4 integration & regression (dispatch path swap, spine output unchanged)

**Slice 4 (Cost & Runtime Efficiency) · Integration (build last) ·
Depends: T54, T55, T56, T57 · Touches: `tests/` (new e2e + a committed golden), `fixtures/`
(reuse r2r demo + its `canned/` stubs).**

> **Why.** Slice 4 changes **how** fan-out work is *dispatched* (deterministic workflow) and **how**
> the classify artifact is *emitted* (schema-constrained) — it must **not** change what the
> deterministic Python spine produces from identical inputs. This is the "prove no spine regression
> + capture the win" ticket, mirroring T20 (Slice-1 e2e) and T49. It is the acceptance gate the
> other four tickets cite.

> **Hard reality this ticket is built around (was wrong in the first draft).** Both the workflow
> path and the prose path run **real LLM workers** whose NL outputs (classify artifacts, node MDs,
> SOP/improvement/synthesis prose) are **non-deterministic** — two runs are never byte-identical,
> and there is **no captured golden in the repo today** (the current e2e asserts *structure and
> counts*, not bytes). Every existing CONSULT e2e gets determinism by **stubbing the LLM** (Slice-1
> hardcodes deliverable MDs as `printf` strings and classify artifacts as fixed templates via
> `fixtures/r2r/canned/build_canned.py`; Slice-2 stubs the resolver). So this ticket asserts
> byte-stability **only on the Python spine, given identical stubbed LLM outputs fed through both
> dispatch paths** — never on LLM-authored content.

## What is deterministic vs LLM-authored (the assertion boundary)

- **Deterministic given identical artifacts/MDs (CAN be byte-identical):** `classify_merge.py` →
  `state.json` / `register.json`; the consolidator's inline command-path writes (T57 Decision B);
  `gap_report.py`
  scan; the `*_inputs.py` bundles; `render_deliverables.py` MD→`.docx`. **This is the spine T58
  pins.**
- **LLM-authored (CANNOT be byte-identical; assert structure/validation instead):** the
  `classify/*.artifact.json` content, the consolidator's confirmed rows, and the drafter/
  synthesizer deliverable MDs.

## Build / Tests

A new e2e (`tests/test_slice4_workflow_e2e.sh`) over the **r2r demo fixture** + its `canned/`
stubs (no client data), driving the pipeline with the **stubbed LLM outputs** (reuse Slice-1's
`printf`/template mechanism + `build_canned.py`, and T57's mock agent) through the **workflow
dispatch path**, asserting:

1. **Spine output equivalence (the headline — corrected).** Feed the **same canned classify
   artifacts and canned consolidate/draft/synth outputs** through (a) the existing prose-stub
   dispatch and (b) the T57 workflow dispatch. Assert `state.json` + `register.json` +
   spine-rendered outputs are **byte-identical between the two paths**, after a **documented
   normalization** (sort keys; freeze/strip timestamps + run-ids — `state.json` carries
   non-stable stamps, which is exactly why Slice-1 avoids raw byte-diffs). Create this golden as
   part of the build — there is none to "refresh."
   - **Deliverable MDs:** assert they **validate structurally and render to `.docx`** (matching
     Slice-1's existing checks) — **not** byte-identity (LLM-authored).
   - **The one documented classify-artifact difference:** T55 Phase 1 **drops `quote`** from the
     emit contract (a field-set change, not whitespace). Normalize by stripping `quote` before any
     artifact compare; record this as the single allowed difference.
2. **Constrained classify validates (T55).** Each `classify/{hash}.artifact.json` from the workflow
   schema path schema-validates **and** passes `validate_artifact.py` cross-field checks; the
   flat-union enum trap (`process: machine`) is still rejected.
3. **Per-stage dispatch count (T54/T57).** Via T57's mock harness, assert the **per-stage** counts
   from T57's table: classify = #docs, consolidate = #nodes, **draft = 2 × #L1s**, synthesize = 1.
   (Not a flat "one per target".)
4. **Human gates preserved (T54/T57 hard constraint).** The workflow makes **no** `orchestrate.py
   next` / `render` / `final` call; the run **stops at the render gate** and at any
   `status.needs_human` signal. Assert the halt where a human is owed (confirm this is assertable
   via the T57 mock harness — add as an explicit dependency).
5. **Cost map is real + content-free (T56).** The per-phase `cost_map.json` is produced (with
   `budget.spent()` deltas under the workflow); grep it for a known fixture **evidence-ref** token
   (not just a prose token) and assert **absent**; assert the size figures are deterministic for
   the fixed fixture.
6. **No regression to prior suites.** `tests/test_slice1_e2e.sh` and `tests/test_slice2_e2e.sh`
   stay green; `__t58__` scratch engagement removed via `trap cleanup EXIT`.

## DoD

- Given identical stubbed LLM outputs, the workflow dispatch path and the prose-stub path produce
  **byte-identical `state.json` + `register.json` + spine-rendered outputs** (after the documented
  normalization), with `quote`-drop as the single recorded artifact difference. A committed,
  normalized golden is created by this ticket.
- Deliverable MDs validate structurally and render to `.docx` (no byte-identity claimed on
  LLM-authored content).
- Constrained classify emission validates and the cross-field gate still bites.
- Human gates demonstrably fire; the workflow issues no `next`/`render`/`final` call.
- A content-free, deterministic per-phase cost map is produced and asserted (evidence-ref absent).
- All prior e2e suites green; no scratch engagement left behind.
- This e2e is the named acceptance artifact referenced by T54/T55/T56.
