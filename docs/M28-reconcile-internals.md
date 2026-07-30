# M28 — reconcile.py internals: read-once, check registry, one parser

> **Status: PROPOSED — scoped from the 2026-07-30 subagent review
> (scratchpad `reconcile-review.md`, findings verified against the code);
> agreed with the user, not yet built.** Pure refactor + defect fixes:
> behavior-preserving except where a named false-positive/negative is
> fixed. Companion: M29 (the coverage expansion this refactor exists to
> receive — new checks should land on the registry shape, not the old
> copy-paste shape).

## Findings being acted on (value-for-effort order)

### 1. Read-once file cache (performance, high)

Each procedure fragment is fully re-read from disk ~13 times per run —
the step-2 parse, the step-3 xref scan, the step-5 consult-meta read,
nine check functions each doing their own walk, plus
`doc_model.callout_display_ids` — with ~11 redundant `blank_fences`
regex passes each. reconcile runs constantly (every drafter's finish
checklist, every advisor stage), so this is the cheapest real win.

Fix: a `reconcile()`-scoped cache — `{relpath: (raw, fenced_blanked)}` —
threaded to the checks. No mtime/invalidations: one run, one snapshot
(folder state is the state; a mid-run write is already undefined).

### 2. Structure: fragment iterator + check registry + dedup (high)

- The `_components`/read/UNFILLED preamble is copy-pasted 9×; checks 3
  and 5 live inline in `reconcile()` while every other check is a
  function. Fix: one `procedure_fragments(folder, manifest, cache)`
  iterator; every check becomes `def check_x(ctx) -> None` appending to
  `ctx.errors/warnings`, run from an ordered registry list. Comment/
  docstring/M22 numbering reconciled once, in that list.
- `_sibling_procedures` in reconcile duplicates
  `doc_model.sibling_procedures` — a drifted parallel scanner in a
  codebase whose ethos forbids exactly that. Delete; import the one.
- Drop the unused `PREFIXES` import.

### 3. Fence blanking fix in callouts.py (correctness)

`FENCE_BLOCK_RE` misses indented fences and unclosed fences, so example
callouts / xrefs / SRC- ids inside them parse as real — the one genuine
false-positive source found. Fix in callouts.py (the ONE implementation —
every consumer inherits): allow leading whitespace; blank an unclosed
fence to EOF. Regression tests for both forms.

### 4. Smaller verified edge cases

- `_TABLE_SEP_ROW_RE` matches a bare `---` thematic break.
- `BAKED_NUMBER_RE` and full-name matching miss hard-wrapped occurrences
  (line-by-line scan; the M4 citation scrub's one-newline `_WS` pattern
  is the precedent for a fix).
- A setext H1 (`Title\n===`) evades the M22.4 heading contract.
- The `unfilled` exemption is applied inconsistently across checks —
  make it a property of the iterator's ctx, decided once.

### 5. Output polish

Three message families lack line numbers (consult-meta warnings,
merged-sections, cross-area ownership); manifest-load failure alone
prints to stderr. Normalize to the house standard: `file:line`, the fix
named, one stream.

### 6. Missing constructed-violation tests

M22.6 (`check_quoted_callout_ids`) and the M16.1 merged-sections warning
have no test anywhere in the suite. Add both (they also pin the refactor).

## Acceptance

- One disk read + one fence-blanking per fragment per run (assert via a
  counting stub in a test).
- Every check a registry entry; checks 3 and 5 extracted; no behavior
  diff on the existing suite (~880 tests green unmodified except the two
  new ones and any message-format assertions the output polish touches).
- `_sibling_procedures` gone; `doc_model.sibling_procedures` the only
  sibling scanner.
- Indented/unclosed fence content never parses as callouts/xrefs/ids —
  regression-tested.
- No new checks in this ticket (that is M29's job, on this foundation).
