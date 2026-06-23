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
- `locked(eid_or_dir)` — context manager taking an advisory `flock` on a **single
  engagement-level** sidecar lock (e.g. `<engagement_dir>/.consult.lock`), **not** per-file.
  Decision: `state.json` and `register.json` are mutated together (add-item writes the
  register then re-syncs state), so one lock per engagement covers the cross-file
  read-modify-write. Use `fcntl.flock`; no-op fallback + warn-once on platforms without it.

**Reentrancy:** `add-item` acquires the lock, then shells out to `improvement_log.py`, then
calls `cmd_sync` — all want the same lock. `flock` on a fresh `open()` is not reentrant →
self-deadlock. Make `locked()` reentrant within a process (track held locks by path +
depth-count, or expose a "already-held" check) so nested acquisitions are no-ops. Sidecar
`.lock` (separate inode) is **load-bearing**: an flock on the target file is lost after
`os.replace` swaps the inode — document this so it isn't "simplified" away.

Atomic writes must `fsync` the file **and** the parent dir after `os.replace` for durability.
Use a collision-safe tmp name (`tempfile.mkstemp` in the same dir, not `pid`-only).

Keep it import-light (stdlib only). Do **not** wire callers yet — T41–T47 adopt it in
their own files to avoid edit conflicts.

## Tests
`tests/test_io_util.py` (or a bash harness consistent with `tests/`):
- atomic write leaves no `.tmp` file and the target is either fully old or fully new after
  a simulated mid-write failure (raise between tmp-write and replace; assert old content intact);
- `locked()` serializes two processes contending on the same lock (sentinel ordering).

## DoD
Module + tests pass; no callers changed; stdlib-only.
