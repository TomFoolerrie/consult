# M60 — Notes-bus integrity: escape, dedup, atomic

**Status: RECORDED** (not scheduled).
Origin: the adversarial review of `main` @ 8b22e9e (2026-08-20),
findings F-05, F-10, F-24 — F-05 and F-10 reproduced with exact inputs.

## Why

`scripts/notes_util.py` is the bus every reviewer comment, tracked
change, and gap answer rides to the drafter. It is also the one store
in the engine holding REAL CLIENT INPUT that cannot be regenerated —
and it has three integrity holes:

1. **One control character silently erases a slug's whole history**
   (lines 64–67, 143–144, 169–181). `_scalar` — the sole writer for
   every producer — escapes only backslash and double-quote and
   flattens `\n`/`\t`. Other control characters pass through raw:
   C1 controls (U+0080–U+009F) and DEL are legal in docx/xlsx XML and
   arrive routinely via Windows-1252 mojibake of smart quotes and
   em-dashes. Once written inside a double-quoted scalar the file is
   invalid YAML. `load_items_from` catches the `YAMLError` and returns
   `[]` — all accumulated feedback invisible — and the NEXT
   `append_items` reads "empty" and rewrites the file with only its new
   items. Reproduced: invisible, then permanently erased.

2. **Idempotence is broken for multiline items** (line 90–91 vs 64–67).
   `_fingerprint` reads RAW values; `_scalar` flattens `\n`/`\t` on
   write. A reloaded item never matches its raw incoming twin, so
   re-running an ingest appends the same note again — against the
   module's documented "re-running an ingest is idempotent" guarantee.
   The live trigger is `gaps_ingest`: answers are taken with `.strip()`
   and keep interior newlines (multi-line Excel answers are normal).

3. **The rewrite is non-atomic** (lines 169–181). `append_items`
   truncates and rebuilds `{slug}.notes.yaml` in place via
   `write_text`. A crash mid-write loses the accumulated notes — unlike
   the engine's regenerable `.aggregate.json`-style caches, this file
   is unrecoverable client input.

## The shape

### Part A — the writer emits YAML that always parses

`_scalar` escapes every character outside printable-safe range using
YAML double-quote escapes (`\x7F`, `\x9F`, …) — or the emitter is
replaced by `yaml.safe_dump` for the value line if hand-formatting can
be preserved elsewhere. Property: for ANY Python string, write → load
round-trips. (Flattening `\n`/`\t` to spaces may remain a deliberate
normalization — see Part B — but it must be an *encoding decision*,
not a parse hazard.)

### Part B — fingerprint what is stored

Dedup compares like with like: `_fingerprint` normalizes exactly as
`_scalar` stores (same flatten, same squeeze), so an unchanged item is
a duplicate no matter how many times the workbook is re-ingested.

### Part C — the file is never mid-state on disk

Write to `{slug}.notes.yaml.tmp` in the same directory, `os.replace`
into place. And the silent-empty amplifier goes: `load_items_from` on
an EXISTING file that fails to parse raises (or quarantines the file
to `{slug}.notes.yaml.corrupt-<ts>` and reports loudly) — it never
returns `[]` for a file that has content. Fail-loud doctrine applies:
the bus never pretends an unreadable history is an empty one.

## The gate

- Property test: append an item containing each of U+0000–U+001F,
  U+007F–U+009F, quotes, backslashes, newlines → file parses, item
  round-trips, drafter-visible.
- The F-05 repro: mojibake character in one comment → all prior notes
  still load; a later append PRESERVES them.
- The F-10 repro: same multiline gap answer ingested twice →
  `added: 1` then `added: 0`, one stored entry.
- Kill-between-truncate-and-write simulation (monkeypatched
  `os.replace`): original file intact.
- Corrupt-on-disk file + append → loud failure or quarantine; never a
  silent overwrite. Existing producer tests (review_extract,
  review_apply, gaps_ingest) pass untouched.
