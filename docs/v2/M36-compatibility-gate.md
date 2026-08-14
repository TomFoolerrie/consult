# M36 — The compatibility gate: v1 re-expressed, byte-for-byte, on the kernel

> **Status: DRAFT — contract under review.** Companions: M33 (the kernel this
> proves), M34 (whose dual-layout adapter this exercises), M35 (whose
> `desktop-procedure.yaml` this makes real). This is the charter's merge
> gate: v2 does not reach `main` until this ticket is green. Charter:
> [`README.md`](README.md).

## The one-sentence contract

The v1 desktop-procedure deliverable runs as a **user-space deliverable
definition on the kernel** — `desktop-procedure.yaml` over the `activity`
type — and the entire v1 surface is **behavior-identical**: all 803 v1
tests pass unchanged, and the procure-to-pay fixture renders byte-identical
docx XML.

If v1's own deliverable cannot be expressed in the definition language, no
user's can. This ticket is where that claim gets paid.

## What actually moves (the second half of M33's table)

M33 wrapped; M36 migrates. The modules M33 left delegating to v1 code move
onto the kernel + plan path:

- **`aggregate.py`** — the view builders become the shipped python-writer
  views the desktop-procedure definition's bindings name; the hard-coded
  view list dies. `run(area)` survives as a thin CLI over the plan.
- **`render.py` + the docx-builder skill** — become the docx skin adapter:
  consume a compiled plan instead of knowing the section order; numbering,
  token resolution, callout display-id assignment unchanged in behavior,
  relocated behind the adapter boundary.
- **`scaffold.py`** — skeletons come from the entity-type declaration
  (`activity.yaml`'s parts) instead of module constants.
- **`scope_delta.py` / the M21 render signal** — keyed per definition
  (one definition today, so behavior-identical).
- **The back-compat shims** (`doc_model.SECTION_TITLES` re-exports etc.)
  are **removed** — this ticket is their planned retirement; anything still
  importing them fails loudly here, inside the gate, not in the field.

**What still does not change:** every agent definition, every skill brief,
the orchestrator/advisor contract, the review pipeline, all file formats,
all `_client/` semantics. A drafter cannot tell M36 happened.

## The proof obligations, in order of severity

1. **The v1 suite: 803 tests, zero edits.** Test files are read-only in
   this ticket (mechanical import-path fixes allowed only if a shim
   retirement forces them, each one listed in the ticket's landing note).
2. **Byte-compatible render.** The p2p fixture (v1 layout, per M34) renders
   through the definition path; the docx `document.xml` (and styles/
   numbering parts) diff empty against a v1-built reference committed as a
   golden artifact. Timestamp-bearing docx metadata is normalized by the
   comparison harness, and the harness itself is validated by a test that
   corrupts one run and confirms the diff catches it.
3. **Advisor equivalence.** The state advisor, replayed over the fixture's
   recorded state sequence, returns the identical action at every step.
4. **Plan equivalence** (already sketched in M35's acceptance, hardened
   here): the compiled desktop-procedure plan's view set, writer map, and
   dispatch order match v1's hard-coded pipeline exactly.

## What this ticket must NOT do

- No new capability rides the gate — no second entity type in engagement
  state, no new bindings, no new views. A pure re-expression: the diff is
  deletions, relocations, and the definition file.
- No test "updates to match the new architecture." A failing v1 test means
  the re-expression is wrong, full stop. The single admissible exception is
  a test that asserts a shim's existence — deleted, with the landing note
  naming it.
- No fixture edits. The p2p fixture is frozen; it proves the adapter.

## Acceptance sketch (firm up at build time)

- The four proof obligations above, as CI-runnable checks.
- `grep`-level absence proof: no engine module outside the kernel and the
  docx adapter names an `activity` part slug or callout label as a code
  constant (the "shape lives in data now" audit).
- The merge choreography: `v2` → `main` PR carries this ticket's green run;
  `2.0.0` stamped; CHANGELOG Unreleased section closed to `[2.0.0]`.

## Complexity accounting (the standing test)

This ticket REMOVES complexity: the shims die, the hard-coded view list
dies, render's section knowledge dies. New state files: zero. New gates:
zero (this ticket IS a gate). New agent judgment: zero. The review risk to
police: **compatibility theater** — a re-expression that keeps a private
side channel (a hard-coded constant consulted "just for the default case")
passes every test and defeats the purpose; the grep-level absence proof
exists to catch exactly this.

## Deferred (recorded, not built)

- **Retiring the v1 per-area source layout** (and M34's adapter) — after
  one real engagement runs centralized end-to-end; the fixture keeps the
  adapter honest until then.
- **Dropping the M14 profile alias** — not before a major version beyond
  2.0; it is one adapter function and existing engagements use it.
