#!/usr/bin/env python3
"""consult_io.py — shared atomic-write + advisory-lock helpers (stdlib only).

Named `consult_io` (not `_io`) on purpose: `_io` is a stdlib C-extension module
and built-ins shadow sys.path, so `import _io` would never resolve here.

Every engine that writes state.json / register.json / temp CSVs used to do a
direct `open(path, "w") + json.dump` in place: a crash mid-write truncates the
file, and concurrent sibling subprocess calls race on read-modify-write. This
module centralises two primitives so callers (T41–T47) can adopt them:

  - write_json_atomic / write_text_atomic — write to a collision-safe temp file
    in the same directory, flush+fsync it, os.replace onto the target (atomic on
    POSIX), then fsync the parent directory for durability.
  - locked(eid_or_dir) — context manager taking a single engagement-level
    advisory flock on a sidecar `<engagement_dir>/.consult.lock`, NOT per-file.

Design notes:
  - One lock per engagement (not per file): state.json and register.json are
    mutated together (add-item writes the register, then re-syncs state), so a
    single lock covers the cross-file read-modify-write.
  - The sidecar `.consult.lock` is a SEPARATE inode and is load-bearing: an
    flock held on a data file is lost the moment os.replace swaps in a new inode
    underneath it, so we never flock the target files themselves. Do not
    "simplify" this away.
  - locked() is reentrant within a process (tracked by lock-file path +
    depth-count): add-item acquires the lock, then nested cmd_sync re-acquires
    it. flock on a fresh open() is NOT reentrant and would self-deadlock, so
    nested acquisitions on an already-held path are no-ops.
  - Locking uses fcntl.flock; on platforms without fcntl it degrades to a no-op
    and warns once.

Dependency-light: standard library only.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, Union

try:
    import fcntl  # POSIX only
except ImportError:  # pragma: no cover - exercised only on non-POSIX platforms
    fcntl = None  # type: ignore[assignment]

LOCK_FILENAME = ".consult.lock"

# Whether we have already warned about the missing flock primitive (warn-once).
_FLOCK_WARNED = False

# Process-local reentrancy table: lock-file path (resolved str) -> nesting depth.
# A second `locked()` on the same path while depth > 0 is a no-op; the fd is held
# until the outermost context exits.
_HELD_LOCKS: Dict[str, Dict[str, Any]] = {}


def write_text_atomic(path: Union[str, os.PathLike], text: str) -> None:
    """Atomically write `text` to `path`.

    Writes to a collision-safe temp file in the same directory (so os.replace is
    a same-filesystem rename), flushes + fsyncs the file, replaces the target,
    then fsyncs the parent directory so the rename itself is durable.
    """
    _atomic_write(path, text.encode("utf-8"))


def write_json_atomic(path: Union[str, os.PathLike], obj: Any) -> None:
    """Atomically write `obj` as pretty JSON to `path` (see write_text_atomic)."""
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    write_text_atomic(path, text)


def _atomic_write(path: Union[str, os.PathLike], data: bytes) -> None:
    target = Path(path)
    directory = target.parent
    directory.mkdir(parents=True, exist_ok=True)
    # tempfile.mkstemp gives a unique, collision-safe name in the same dir — not
    # a pid-only suffix, which could collide across threads/retries.
    fd, tmp_name = tempfile.mkstemp(
        prefix=target.name + ".", suffix=".tmp", dir=str(directory))
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, str(target))
    except BaseException:
        # On any failure (including a simulated mid-write crash) leave no temp
        # litter and leave the existing target untouched.
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    _fsync_dir(directory)


def _fsync_dir(directory: Path) -> None:
    """fsync a directory so a rename within it is durable. Best-effort."""
    try:
        dir_fd = os.open(str(directory), os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(dir_fd)
    except OSError:
        # Some filesystems / platforms do not support directory fsync.
        pass
    finally:
        os.close(dir_fd)


def _warn_once_no_flock() -> None:
    global _FLOCK_WARNED
    if not _FLOCK_WARNED:
        _FLOCK_WARNED = True
        sys.stderr.write(
            "warning: fcntl.flock unavailable on this platform; "
            "locked() is a no-op (no cross-process serialization).\n")


def _lock_path(eid_or_dir: Union[str, os.PathLike]) -> Path:
    """Resolve the sidecar lock-file path for an engagement dir (or a dir-ish
    path). The sidecar is always `<dir>/.consult.lock`."""
    p = Path(eid_or_dir)
    # If the caller already handed us the lock file itself, honour it.
    if p.name == LOCK_FILENAME:
        return p
    return p / LOCK_FILENAME


@contextmanager
def locked(eid_or_dir: Union[str, os.PathLike]) -> Iterator[None]:
    """Hold an engagement-level advisory flock for the duration of the block.

    Takes an exclusive flock on the sidecar `<engagement_dir>/.consult.lock`.
    Reentrant within a process: nested acquisitions on the same lock path are
    no-ops (depth-counted), so add-item -> cmd_sync nesting does not deadlock.
    On platforms without fcntl this is a no-op (warns once).
    """
    lock_path = _lock_path(eid_or_dir).resolve()
    key = str(lock_path)

    # Reentrant fast-path: already held by this process — bump depth, no flock.
    held = _HELD_LOCKS.get(key)
    if held is not None:
        held["depth"] += 1
        try:
            yield
        finally:
            held["depth"] -= 1
            # The outermost holder (below) owns fd release; we only adjust depth.
        return

    if fcntl is None:
        _warn_once_no_flock()
        yield
        return

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(lock_path), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        _HELD_LOCKS[key] = {"fd": fd, "depth": 1}
        try:
            yield
        finally:
            entry = _HELD_LOCKS.pop(key, None)
            if entry is not None:
                try:
                    fcntl.flock(entry["fd"], fcntl.LOCK_UN)
                except OSError:
                    pass
    finally:
        os.close(fd)
