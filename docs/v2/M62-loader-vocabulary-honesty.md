# M62 — Loader vocabulary honesty: the kernel validates what it claims

**Status: BUILT** (`2.4.0-alpha.7`, gate 9/9 — see Amendment A1).
Origin: the adversarial review of `main` @ 8b22e9e (2026-08-20),
findings F-08, F-19, F-18 — F-08 reproduced against the documented
extension path.

## Why

The kernel's stated contract is that shipped and user types go through
the same loader, with only the VOCABULARY coming from the type
declaration (`kernel.py:12–14, 314–318`), and that the four-stage
definition loader is fail-loud on names. Three places where the claim
and the code part ways:

1. **Callout id grammar is hard-anchored to v1's five prefixes**
   (`callouts.py:54–56`, enforced at `kernel.py:487`). `ID_STRICT_RE`
   is compiled once from the hard-coded table —
   `^(CTRL|GAP|IO|PP|SC)-…` — so a user type declaring
   `{label: RISK, prefix: RSK, home: issues}` loads cleanly, passes
   definition stage 2, and then EVERY fragment carrying its callouts is
   refused at parse: *"malformed callout ID 'RSK-001' … (grammar:
   <PREFIX>-<ALNUM> e.g. RSK-001)"* — an error citing the rejected id
   as the example of correctness. The documented extension path is
   unusable.

2. **`repeat.over` is never vocabulary-checked**
   (`definitions.py:311–312`). Stage 2 validates every binding's
   `entities:` type against `kernel.load_type`, but a shape block's
   `repeat` is stored opaque in stage 1 and its `over:` type never
   checked — an undeclared type there sails through the loader that is
   advertised as refusing unknown names.

3. **A non-int `order` crashes the wrong verb with the wrong error**
   (`doc_model.py:427, 719` vs 455–456). `display_numbers` defends
   (`order if isinstance(order, int) else 0`); `procedures()` and
   `assemble()` sort on the raw value, so `order: null` mixed with ints
   raises an uncaught `TypeError` — which escapes through
   `ledger.register/credit` (they catch only `ManifestError`) as a raw
   crash in an unrelated ledger write.

## The shape

### Part A — the id grammar is built from loaded declarations

The prefix alternation comes from the union of prefixes declared by the
types in play (shipped + user), assembled where the types are loaded
and passed to (or looked up by) the parser — `ID_STRICT_RE` becomes a
function of the declaration set, not a module constant. The v1 five
remain the shipped floor; a declared `RSK` parses; an UNdeclared prefix
still refuses, now with an error that lists the declared prefixes
instead of quoting the rejected id as its own counterexample.

### Part B — stage 2 covers `repeat.over`

The vocabulary stage resolves `repeat.over`'s entity type exactly as it
resolves `entities:` — unknown type → the same fail-loud refusal naming
the definition, the block, and the name. Serviceability (stage 3)
reporting follows wherever `entities:` already reports.

### Part C — one `order` rule, one error type

`_order_of(c)` (int or 0, the `display_numbers` rule) is used by every
sorter — `procedures()` and `assemble()`; `callout_display_ids()`
inherits through `procedures()` — so the model never crashes on a
tolerated field. `validate_manifest` keeps
reporting non-int order as a defect; ledger verbs that traverse
manifests wrap traversal failures in `LedgerError`/`ManifestError` so
no raw `TypeError` escapes a named-error contract.

## The gate

- A test type declaring a new prefix: fragment with `RSK-001` parses;
  the callout lands with its declared kind; undeclared `ZZZ-001` still
  refused, error lists declared prefixes.
- A definition whose `repeat.over` names an undeclared type → stage 2
  refusal; a valid one still compiles.
- `order: null` manifest: `procedures()`/`assemble()` return the
  `display_numbers` ordering; `ledger.register` on that area either
  succeeds or raises a named error — never `TypeError`.
- Full suite + compat gate untouched (v1's five prefixes and all frozen
  fixtures parse identically).

## Amendment A1 — build rulings (2026-08-20)

* Part A landed as `callouts.id_strict_re(prefixes)` — grammar assembled
  where the parse happens (`kernel.parse_entity` builds it from the tdecl's
  declared prefixes, floor-unioned with the v1 five). `ID_STRICT_RE` stays as
  the floor-only constant for the v1 aggregate/reconcile path, which is
  behind the compat gate and reads only the shipped vocabulary.
* Part C: `_order_of` is shared by `procedures()`, `display_numbers` and
  `assemble()`; the file tiebreak is coerced through `str()` so a null
  `file:` can't crash the sort either.
* Full suite + compat gate verified untouched (v1 five parse identically).
