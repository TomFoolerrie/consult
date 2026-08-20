# M56 — Evidence identity: the ledger stops keying bytes by basename

**Status: BUILT** (`2.4.0-alpha.1`, gate 10/10 — see Amendment A1).
Origin: the adversarial review of `main` @ 8b22e9e (2026-08-20),
findings F-01 (critical), F-02, F-03, F-17 — all four reproduced
end-to-end. First of the hardening line: the only critical in the
review, and the one place the engine can destroy registered evidence.

## Why

The ledger mints SRC ids by **content hash** but stores, moves, and
diffs evidence files by **basename**. Identity and location disagree,
and three independent defects fall out of that one mismatch:

1. **`credit()` destroys retired evidence** (`ledger.py:656–672`).
   The move rule retires a fully-consumed source with
   `shutil.move(new/<basename>, processed/<basename>)`, and
   `shutil.move` silently replaces an existing destination. `register()`
   is idempotent by hash, not name, so a re-sent `interview.md` with new
   content mints SRC-002 — and when SRC-002 is consumed, its move
   overwrites SRC-001's bytes in `_sources/processed/`. Reproduced
   through the public API: both entries end up recording the same path,
   SRC-001's hash matches nothing on disk, every provenance string
   citing SRC-001 is unverifiable. Silent destruction of registered
   evidence through the core register → draft → credit flow.

2. **`centralize()` collapses distinct sources** (`ledger.py:1033–1037`).
   The v1→v2 fold places each entry's bytes at
   `_sources/{new,processed}/<basename>` and copies only
   `if not dest.is_file()`. Two v1 areas each holding their own
   `interview.md` collide: the second entry's bytes are never copied,
   yet its `file:` field still claims the shared path. The central
   ledger is corrupted at the moment of migration — a hash that matches
   nothing, a drafter reading the wrong source's content.

3. **`status()` hides un-ingested evidence** (`ledger.py:515–523`).
   The loud-until-empty diff skips a staged candidate when its
   *basename* appears among registered basenames — before the hash
   check runs. `_new_file_names()` deliberately walks subdirectories,
   so `new/batch2/interview.md` with different bytes reports quiet:
   `{'unregistered': [], 'parked': []}`. The one guard whose job is to
   make un-ingested evidence loud decides by name, against the module's
   own line-26 doctrine ("whether a name is unregistered is decided by
   the ledger").

4. **`centralize()` swallows a malformed area** (`ledger.py:823–826`).
   The migration enumerates areas through `_v1_entries`, the *tolerant*
   reader — `[]` on `yaml.YAMLError`/`OSError`/non-mapping. One typo in
   one area's `sources.yaml` and that whole area contributes nothing to
   the fold, no error raised. Tolerance is right for the read-only
   adapter; it is wrong for a write verb.

## The shape

### Part A — collision-proof placement

Evidence bytes are stored under a name the ledger controls, not the
name the client chose: `_sources/{new,processed}/<SRC-id>--<basename>`
(id prefix preserves uniqueness; basename preserved for humans). The
move rule and `centralize()` both write to the id-qualified path;
`entry["file"]` records it. Where the destination somehow exists with
DIFFERENT bytes, the verb refuses with `LedgerError` naming both ids —
it never overwrites, never skips silently.

Migration note: existing engagements hold unqualified paths. `credit()`
and readers accept both forms; a small `ledger.py` verb (or the first
`credit()` touch) upgrades entries in place. The frozen compat fixtures
must pass untouched.

### Part B — `status()` diffs by hash alone

Drop the basename short-circuit. A staged file is "known" iff its
content hash appears in the ledger — the check that already exists on
the next line becomes the only check. (Keep the basename set only if a
measured perf case demands a pre-filter, and then only as a candidate
filter *before* hashing, never as a verdict.)

### Part C — `centralize()` fails loud

The fold enumerates areas through a strict reader: a registry that
exists but cannot be parsed, or parses to a non-mapping, raises
`LedgerError` naming the file. The tolerant `_v1_entries` remains for
the read-only adapter; the write verb gets its own strict path (or a
`strict=` mode).

## The gate

- The F-01 repro as a test: register → credit → re-drop same basename,
  new bytes → register → credit; BOTH byte streams exist on disk, both
  entries' hashes verify against their recorded files.
- The F-02 repro: two v1 areas, same basename, different bytes →
  centralize; both central entries verify hash-against-file.
- The F-03 repro: registered `interview.md` + staged
  `batch2/interview.md` with new bytes → `status()` lists it.
- Malformed v1 registry → `centralize` raises `LedgerError` naming the
  file; nothing partially folded.
- Compat gate: v1 golden and all frozen-engagement fixtures pass
  untouched (path-form acceptance in Part A's migration note).

## Amendment A1 — build rulings (2026-08-20)

* **Migration approach (Part A's "pick one"):** acceptance-of-both plus a
  lazy in-place upgrade — readers accept unqualified legacy paths verbatim,
  and the first `credit()` touch of a legacy `processed/` entry moves its
  bytes to the id-qualified path *after verifying the recorded hash*; an
  entry whose bytes were already clobbered is left alone so the defect stays
  visible. No eager migration verb.
* Retirement to an occupied destination with the SAME bytes deletes the
  staged duplicate rather than refusing (same evidence, one copy); DIFFERENT
  bytes refuse with `LedgerError` naming both ids.
* `centralize` validates every v1 registry strictly (`_v1_entries_strict`)
  BEFORE folding anything, so a malformed area can never leave a partial
  fold; the tolerant `_v1_entries` remains the read-only adapter's reader.
* Three pre-existing tests that pinned the basename-keyed placement were
  updated to the id-qualified paths (`test_ledger_m34.py` ×4 assertions,
  `test_central_mode_m34.py` ×1). Compat gate and frozen fixtures untouched.
