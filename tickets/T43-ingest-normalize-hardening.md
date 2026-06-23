# T43 — `ingest_normalize.py` hardening

**Slice 3 · Wave 2 (parallel) · Depends: T40 · Touches: `scripts/ingest_normalize.py`** (and
import surface of `clean_vtt.py` — coordinate if another ticket touches it)

## Fixes (from review)
1. **Replace the `exec`-patched-source hack** — `handle_transcript` reads `clean_vtt.py`,
   regex-rewrites its path assignments (only the first match), and `exec`s it. Refactor
   `clean_vtt.py` to expose a `clean(input_path, output_path)` (or `clean_text(str)->str`)
   function and **import** it. Remove the regex/`exec` path entirely.
2. **Atomic write + dedup TOCTOU** — route the MD write through `_io.write_text_atomic`;
   take `_io.locked` over the ingested dir across the dedup-check→write window so two
   concurrent ingests of identical bytes don't both write.
3. **`iter_sources` excludes own output** — `rglob("*")` will re-ingest `ingested/*.md` when
   `--source` points at the engagement dir. Skip the `ingested/` subtree.
4. **Per-file error isolation** — `validate_header` raising `ValidationError` kills the whole
   batch. Catch per file, record a failure row, continue; print a batch summary.
5. **`_md_table` newline escaping** — cells containing `\n` break the Markdown table; escape
   or `<br>`-collapse newlines (and pipes, already handled).
6. **`parse_header_from_text` dict guard** — add the `isinstance(dict)` guard that
   `parse_header` has, so a non-dict front-matter doesn't reach `validate_header`.

## Tests
`tests/test_ingest_hardening.sh`:
- ingest a `.vtt` and assert cleaned body matches the imported `clean()` output (no `exec`);
- ingesting a dir that already contains `ingested/` does not re-ingest its own MD;
- one malformed file in a batch is reported but the batch completes the rest;
- a CSV/docx cell with embedded newline renders a valid Markdown table.

## DoD
Tests pass; `clean_vtt.py` still usable standalone; no scratch left.
