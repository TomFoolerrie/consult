# M29 — Constitution coverage: enforce the contract-only rules

> **Status: PROPOSED — agreed direction with the user 2026-07-30, not yet
> built. Build AFTER M28** (new checks land on the check-registry shape).
> **Resequenced (system review, 2026-07-30): Part 2.1 (the register
> checks) builds AFTER M30**, not before — it validates entry structure
> only M30's verb creates; building it first means validating freeform
> files. Chain: M28 → M29 (sweep + checks 2–4) → M30 → M29 Part 2.1.
> The system's standing pattern is moving rules from prompt to gate —
> everything it does reliably, it does because a script enforces what a
> contract instructs. This ticket closes the gap for the MUST-rules that
> are mechanically checkable but today live only in agent contracts.

## Part 1 — The rules sweep (do this first; it IS the spec)

Read every agent contract (`agents/*.md`) and skill, list every MUST-rule,
and classify each:

- **enforced** — a reconcile check / notes-bus validation / verb refusal
  already exists (cite it);
- **mechanically enforceable** — becomes a check in Part 2, with its
  ERROR-vs-WARNING call argued;
- **judgment-only** — stays contract-side, with one line on why (the
  gate-gaming rule below).

The sweep's output table goes in this ticket as an amendment, so coverage
is a decision on record rather than an accident of history.

**The gate-gaming rule (what stays OUT):** a check that needs judgment
(one-linking-sentence limits, tone, "did the handoff grow into
documentation") does not go in. A false-positive-prone gate is worse than
a contract rule: drafters write to satisfy the gate instead of the
reader. Reconcile's checks must be ones a drafter can satisfy only by
doing the right thing.

## Part 2 — Checks already agreed

1. **Register references (the engagement-level citation check).**
   Contract says "reference the register, never restate" — nothing
   validates either half. Add: (a) a prose reference naming a register
   that does not exist under `components/_client/registers/` (resolved
   through the M13 shadowing pattern reconcile already uses) is an ERROR
   naming the known registers; (b) a distinctive value that appears in a
   register entry restated in fragment prose is a WARNING naming the
   register ("reference, don't restate"). Restatement matching is
   deliberately conservative (exact distinctive strings — dollar
   thresholds, cutoff phrases — never fuzzy). See M30 for the open
   design question on a formal register reference form.
   **Builds AFTER M30** (see status note), and gains a third half then:
   (c) a prose reference naming a class-CONTEXT entry is an ERROR —
   context entries are never cited by name (the mechanical backstop for
   M30's align-never-evidence rule, moved from prompt to gate per the
   house doctrine).
2. **consult-meta presence** — a DRAFTED fragment (no `unfilled`
   sentinel) with no `consult-meta` block at all silently skips noun
   binding, so the Systems view / Role Dictionary / RACI just omit it —
   invisible today (only unknown slugs warn). ERROR.
3. **Hard-wrap ~80 columns** — the contract rule that anchor matching
   (M12) and the citation scrub's one-newline window (M4) depend on.
   WARNING on prose lines past ~100 cols (tables, code, URLs exempt).
4. **`[[#slug]]` outside a table row** — the number-only form is for Ref
   cells where the title is its own column; in prose it renders a
   cryptic bare number. WARNING with the fix ("use [[slug]]").

## Citation locality — settled here, discussion continuing in M30

`SRC-` citations remain AREA-LOCAL, validated against the area's own
ledger (M22.1 unchanged). The sanctioned crossings are `adopt` (M24 —
the evidence moves, as a hash-stamped local source) and the registers
(shared recurring facts, checked by Part 2.1). A raw cross-area citation
would silently bind to the wrong ledger today (ids collide by
construction: every area has an SRC-004) and would break retirement
accounting, the drafter reading list, and the render scrub. Any change
to this is M30's conversation, not a side effect here.

## Acceptance

- The sweep table exists as an amendment, every MUST-rule classified.
- Each Part-2 check: constructed-violation test + clean-pass test;
  messages carry file:line + the fix (house standard).
- Register checks resolve through client_config's M13 layering (area
  shadows engagement), and say which layer answered.
- No judgment-only rule got a gate (the gate-gaming rule is cited in
  the sweep table for each exclusion).
