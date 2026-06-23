# T40 — Shared atomic-write + advisory-lock IO util

**Slice 3 (Remediation & Hardening) · Wave 1 (foundation) · Depends: — · Touches: `scripts/_io.py` (new)**

## Problem
Every engine that writes `state.json` / `register.json` / temp CSVs does a direct
`open(path, "w") + json.dump` in place, with no locking (review findings: non-atomic
writes everywhere; no advisory lock; read-modify-write races between sibling subprocess
calls). A crash mid-write truncates the file; concurrent mutations silently lose updates.

## Build
Add a tiny dependency-free helper module `scripts/_io.py` exposing:
- `write_json_atomic(path, obj)` — write to `path + ".tmp.<pid>"`, `flush`+`fsync`, then
  `os.replace` onto the target (atomic on POSIX). Same for `write_text_atomic`.
- `locked(path)` — context manager taking an advisory `flock` on a sidecar `<path>.lock`
  (use `fcntl.flock`; no-op fallback + warning on platforms without it).

Keep it import-light (stdlib only). Do **not** wire callers yet — T41–T47 adopt it in
their own files to avoid edit conflicts.

## Tests
`tests/test_io_util.py` (or a bash harness consistent with `tests/`):
- atomic write leaves no `.tmp` file and the target is either fully old or fully new after
  a simulated mid-write failure (raise between tmp-write and replace; assert old content intact);
- `locked()` serializes two processes contending on the same lock (sentinel ordering).

## DoD
Module + tests pass; no callers changed; stdlib-only.
