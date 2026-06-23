# T52 — Ingest robustness: per-file isolation + graceful degradation

**Slice 3 (Remediation & Hardening) · Follow-up · Depends: T43 (completes its #4) ·
Touches: `scripts/ingest_normalize.py`, `tests/test_ingest_hardening.sh` (extend),
`tests/test_ingest_robustness.sh` (new)**

> **Relationship to T43.** T43 #4 ("per-file error isolation") already shipped the
> `try/except Exception` batch loop and a test (`tests/test_ingest_hardening.sh` Test 4) — but
> that test only exercises a **corrupt `.docx`**, which raises an ordinary `Exception` (caught).
> It never hit the `SystemExit` paths, which silently *defeat* the same isolation. **T52
> completes T43 #4**: it closes the `SystemExit` holes and extends T43's isolation test rather
> than asserting an overlapping contract in isolation. The new robustness test cross-links to it.

## Problem

`ingest_normalize.py` is the only stage facing untrusted, heterogeneous external input. The
deterministic core (content-hash immutability, dir-dedup by `source_hash`, atomic writes under
an advisory lock, schema-validated headers, "never re-ingest our own output") is sound and
**must not regress**. The gaps are at the messy-input edges.

**Tier 1 — correctness bugs (per-file isolation is violated):**

1. **`SystemExit` escapes the batch loop's `except Exception`.** The per-file loop
   (`cmd_ingest`, `ingest_normalize.py:427-434`) catches `except Exception` (`:430`) to isolate
   one bad file — but `SystemExit` is a `BaseException`, **not** an `Exception`, so it is **not**
   caught and **kills the whole batch**. Two paths hit this from inside the `try`:
   - Unsupported extension passed *by path* → `dispatch()` raises `SystemExit` (`:294-295`),
     reached via `ingest_one` → `dispatch` (`:349`). So `--source good.docx weird.pdf good2.txt`
     aborts instead of writing the two good files and quarantining `weird.pdf`.
   - Genuine name-collision refusal → `SystemExit` (`:378`) inside `ingest_one` (`:429`). One
     file's conflict aborts the batch.
   - Same class, lower likelihood: `handle_docx` missing-`python-docx` guard (`:238-240`);
     `parse_header_from_text` internal-invariant guards (`:388,391`).

2. **A missing/typo'd source path aborts everything before the loop runs.** `iter_sources`
   raises `SystemExit("Source not found")` (`:412`) and is called (`:421`) *before* the loop.
   `--source a.txt typo.txt b.txt` ingests **nothing**. `iter_sources` also does **not** check
   that an explicitly-passed file's extension is supported (`:409-410`) — that omission is the
   exact channel feeding an unsupported file into bug #1 (the directory-scan path *does* filter,
   `:402`).

3. **Symlink hole (per-file isolation's quieter cousin).** `iter_sources` recurses with
   `rglob("*")` + `f.is_file()` (`:401-402`), which **follows symlinks**. The
   "don't re-ingest our own output" guard (`:404-407`) checks `"ingested" in <relative-to-source>
   .parts` — a symlink pointing into *another* engagement's `ingested/`, or a symlink loop,
   bypasses it and can re-ingest our own artifacts or wedge the walk.

**Tier 2 — silent fidelity loss (the "wide & easy" gaps):**

4. **`.docx` drops content silently.** `handle_docx` (`:260-277`) walks only top-level body
   paragraphs and tables. It silently loses embedded images, text boxes, SmartArt/charts,
   headers/footers, footnotes, list numbering (lives in `numbering.xml`), and nested tables
   (`cell.text` flattens them). Dropping these is acceptable for deterministic scope; doing it
   **silently** is not. *(Scope note: this ticket only **signals** the loss — see Build #4.
   Actual reconstruction of list numbering and nested tables is deferred to **T53**.)*

5. **Empty/whitespace-only body writes silently.** An image-only Word doc or an empty/all-blank
   CSV (`handle_table` drops blank rows at `:224` → `_md_table([]) == ""`, `:194-195`) produces a
   near-empty ingested MD (`build_md` writes whatever `body` it's handed) with no signal.

6. **Encoding is hard-wired to `utf-8` + `errors="replace"`** (`:169,177,149`; `utf-8-sig`
   at `:221`). A cp1252/latin-1 client file (Windows smart-quotes, em-dashes) gets silent `�`
   substitution — never fails, quietly corrupts.

## Decision (recorded)

**(A) Convert deep `SystemExit`s to a domain exception caught by the loop** — *chosen*.
Introduce `class IngestError(Exception)`, raise it from `dispatch` (unsupported ext) and the
collision-refusal path, and let `cmd_ingest`'s existing `except Exception` quarantine the file
as a `FAILED` row. Keep genuinely top-level/CLI-fatal conditions as `SystemExit`.

**(B) Broaden the loop to `except BaseException`** — *rejected*: also swallows
`KeyboardInterrupt` and genuine fatal exits; blunt. Raise the right *type*, don't catch the
wrong *base*.

## Build

**Invariants to preserve (do NOT touch behavior):** content-hash from **source bytes**
(`sha256_hex(raw)`, `:345`) — note the hash is over the raw input, *not* the MD text, so handler
output changes (markers, encoding) cannot change `source_hash` or break dedup; the immutability
guard (`:372-379`); dir-dedup (`:365`); atomic write + lock (`:364,381`); `output_name`/
`file_date` (`:330-334`) — **leave unchanged**. No file-size cap is added (out of scope).

**Tier 1**
1. Add `class IngestError(Exception)` near the top. Raise it (instead of `SystemExit`) from:
   - `dispatch` unsupported-extension (`:294-295`);
   - the collision-refusal in `ingest_one` (`:378`);
   - `handle_docx`'s missing-`python-docx` guard (`:238-240`) — a missing *optional* handler
     dep should quarantine that one `.docx`, not kill a batch of transcripts. Make the `FAILED`
     reason legible ("python-docx not installed — run `pip install -r requirements.txt`") so a
     missing install isn't mistaken for file corruption. Document the choice in a comment.
   - Leave `validate_header`'s missing-`jsonschema` guard (`:325`), `parse_header_from_text`'s
     internal-invariant guards (`:388,391`), and the no-subcommand CLI path as `SystemExit`
     (true environment/usage/invariant faults, not per-file data faults).
2. `iter_sources` (`:395-413`): never abort the batch for a single bad source. Return
   `(files, warnings)` (or collect warnings on a passed-in list):
   - non-existent path → record a warning, **continue** (no `SystemExit`);
   - explicitly-passed file whose suffix ∉ `SUPPORTED_EXTS` → record as an unsupported skip
     (mirror the dir-scan filter at `:402`), do **not** pass to `dispatch`;
   - **symlink guard**: skip symlinked files (or `resolve()` and skip any whose real path lands
     under *any* `engagements/*/ingested/` tree); don't follow symlinks during recursion.
   - If *every* source is bad/missing → keep the existing non-zero exit + "No supported source
     files found." (unchanged contract for the all-bad case).
3. `cmd_ingest`: thread `iter_sources` warnings into the summary + stderr `Failures:`/skips
   block and the **exit-code contract** (non-zero when there were any failures *or* surfaced
   unsupported/missing sources). Good files in the same batch are still written. The
   per-file-isolation contract is now honoured for *all* fault kinds.

**Tier 2**
4. **`.docx` omission *signalling* only** (`handle_docx`) — no reconstruction here. While walking
   the body, **count** dropped content: inline/anchored drawings (images) and list-style
   paragraphs (`w:numPr` present) that are emitted as plain text; if cheap, count nested `w:tbl`
   inside cells. Append **one** deterministic trailing marker when anything was dropped, e.g.
   `<!-- ingest: 3 image(s), 1 list(s) flattened, 0 nested table(s) omitted -->` (stable wording
   and order so the immutable output stays reproducible). Do **not** invent content. *Actual*
   list-numbering preservation and nested-table recursion → **T53** (larger, separable).
5. **Empty-body guard** (`ingest_one`): if produced `body.strip() == ""`, raise
   `IngestError("no extractable text")` → file quarantined as `FAILED`, no hollow MD written.
   **Documented behavior:** this is *sticky* — because nothing is written, dir-dedup can't skip
   it, so a corpus containing a legitimately-empty file reports that file `FAILED` on **every**
   run and the batch exit stays non-zero until the file is removed/replaced. This is intended
   (an empty source is a real, actionable input problem, surfaced loudly), not a bug.
6. **Encoding resilience**: add one decode helper used by `handle_transcript`/`handle_text`/
   `handle_table` (the *handlers* that produce user-visible output): try `utf-8` strict; on
   `UnicodeDecodeError` fall back `cp1252` → `latin-1` (fixed order → deterministic) and
   **record** that a non-utf-8 fallback occurred so `cmd_ingest` can surface a warning (and/or a
   header hint). **Preserve `handle_table`'s BOM stripping** (decode as `utf-8-sig` first so a
   UTF-8-BOM CSV doesn't newly retain a leading `﻿` in cell[0][0]). `looks_like_transcript`
   (`:149`) stays best-effort: its decode is a non-user-visible sniff already wrapped in a bare
   `except` (`:150-151`), so it does **not** drive the fallback warning (avoid double-counting).

Match existing code style (`scripts/state_machine.py`, `ingest_normalize.py` itself).

## Tests

**Extend `tests/test_ingest_hardening.sh`** (the T43 isolation test) so the isolation contract
lives in one place, **and** add `tests/test_ingest_robustness.sh` for the new surface, both with
a `__t52__` scratch engagement removed via `trap cleanup EXIT`:

- **Headline regression (Tier 1 #1):** `ingest --source good.txt weird.pdf good2.txt` (fabricate
  an unsupported `weird.pdf`) → non-zero exit, **both** good files written, `weird.pdf` reported
  `FAILED`/unsupported, batch **not** aborted. (This is the `SystemExit` path T43's corrupt-docx
  test missed — add it alongside that test.)
- **Collision-refusal is per-file, not fatal — concrete recipe:** ingest file `A` (writes
  `<name>.md`); then mutate that MD's header `source_hash` to a different value (so
  `find_existing_for_hash` no longer matches but `output_name` still collides); re-ingest `A`
  together with a sibling good file `B`. Assert: `A` → `FAILED` (collision), `B` → written,
  batch not aborted.
- **Bad path among many (Tier 1 #2):** `--source a.txt does-not-exist.txt b.txt` → `a.txt`,
  `b.txt` written, missing path reported, non-zero exit. All-bad case still prints "No supported
  source files found." and exits non-zero.
- **Explicit unsupported file is skipped, not crashed.**
- **Symlink guard (Tier 1 #3):** a symlink under the source dir pointing into an `ingested/`
  tree is not followed/ingested.
- **docx omission marker (Tier 2 #4):** a fixture `.docx` (generated deterministically with
  `python-docx` in test setup — no opaque committed binary) containing an image and a numbered
  list → MD carries the stable `<!-- ingest: … omitted -->` marker; **re-ingesting the same
  bytes is still a dedup `skip`** (marker didn't break immutability).
- **Empty-body guard (Tier 2 #5):** an all-blank CSV / image-only docx → `FAILED`, no hollow MD;
  re-run reports it `FAILED` again (sticky behavior asserted, not treated as a regression).
- **Encoding fallback (Tier 2 #6):** a cp1252 file with smart quotes → decodes without `�`,
  fallback recorded/warned; a clean utf-8 file and a UTF-8-BOM CSV are **byte-identical** to
  pre-ticket output.
- **No regression (mandatory):** `tests/test_slice1_e2e.sh` green; the canonical r2r-demo / Slice-1
  fixtures ingest to **byte-identical** MDs with identical `source_hash` (not "the relevant
  portion" — assert byte-identity).

## DoD

- One bad/unsupported/missing/symlink source no longer aborts a batch; good files in the same
  invocation are written; every quarantined item is reported with a reason and reflected in the
  exit code. T43 #4 is completed (its `SystemExit` holes closed; its test extended).
- `.docx` content omissions and non-utf-8 decoding are **signalled**, never silent.
- Empty-extraction inputs fail loudly (sticky, by design) instead of writing hollow MDs.
- Immutability / content-hash / atomic-write / lock / `output_name` behavior unchanged;
  unchanged inputs produce byte-identical MDs and still dedup by `source_hash`.
- Decision (A) recorded; `test_ingest_hardening.sh` (extended) + `test_ingest_robustness.sh` +
  Slice-1 e2e pass; no scratch engagement left behind.
- docx list-numbering / nested-table **reconstruction** explicitly deferred to **T53**.
