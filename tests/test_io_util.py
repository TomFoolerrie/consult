#!/usr/bin/env python3
"""test_io_util.py — tests for scripts/consult_io.py (T40).

Covers:
  - atomic write leaves no .tmp litter and the target is all-old-or-all-new
    after a simulated mid-write failure (old content stays intact);
  - locked() serializes two contending processes (sentinel ordering);
  - locked() is reentrant within one process (nested acquire does not deadlock).

Stdlib only. Run: python3 tests/test_io_util.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

# consult_io is importable by name (it deliberately avoids the `_io` stdlib clash).
sys.path.insert(0, str(SCRIPTS))
import consult_io as _io  # noqa: E402

_failures = 0


def check(cond: bool, msg: str) -> None:
    global _failures
    status = "ok" if cond else "FAIL"
    print(f"  [{status}] {msg}")
    if not cond:
        _failures += 1


def test_atomic_write_basic(tmp: Path) -> None:
    print("test_atomic_write_basic")
    target = tmp / "out.json"
    _io.write_json_atomic(target, {"a": 1, "b": [2, 3]})
    check(target.exists(), "target written")
    check(json.loads(target.read_text()) == {"a": 1, "b": [2, 3]}, "content round-trips")
    leftovers = [p.name for p in tmp.iterdir() if ".tmp" in p.name]
    check(not leftovers, f"no .tmp litter ({leftovers})")


def test_atomic_write_midfailure(tmp: Path) -> None:
    print("test_atomic_write_midfailure")
    target = tmp / "state.json"
    _io.write_text_atomic(target, "OLD-CONTENT")
    before = target.read_text()

    # Simulate a mid-write crash: monkeypatch os.replace to raise *after* the
    # temp file has been written + fsynced but before the rename completes.
    orig_replace = os.replace

    def boom(src, dst):  # noqa: ANN001
        raise RuntimeError("simulated crash before replace")

    os.replace = boom
    try:
        _io.write_text_atomic(target, "NEW-CONTENT")
    except RuntimeError:
        pass
    else:
        check(False, "expected simulated crash to propagate")
    finally:
        os.replace = orig_replace

    check(target.read_text() == before == "OLD-CONTENT",
          "target is fully old (no torn write)")
    leftovers = [p.name for p in tmp.iterdir() if ".tmp" in p.name]
    check(not leftovers, f"no .tmp litter after failure ({leftovers})")


def test_reentrant(tmp: Path) -> None:
    print("test_reentrant")
    edir = tmp / "eng"
    edir.mkdir()
    # Nested acquisition in the same process must NOT deadlock.
    with _io.locked(edir):
        with _io.locked(edir):
            with _io.locked(edir):
                check(True, "nested locked() did not deadlock")
    # After the outermost exits, the held-table is clean and re-lockable.
    with _io.locked(edir):
        check(True, "re-acquire after full release works")
    check(not _io._HELD_LOCKS, "held-locks table empty after release")


_CONTENDER = r"""
import sys, time, os
sys.path.insert(0, sys.argv[1])
import consult_io as _io
edir, sentinel, tag, hold = sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
with _io.locked(edir):
    with open(sentinel, "a") as f:
        f.write(tag + "-enter\n"); f.flush()
    time.sleep(hold)
    with open(sentinel, "a") as f:
        f.write(tag + "-exit\n"); f.flush()
"""


def test_serializes_two_processes(tmp: Path) -> None:
    print("test_serializes_two_processes")
    edir = tmp / "eng2"
    edir.mkdir()
    sentinel = tmp / "sentinel.log"
    script = tmp / "contender.py"
    script.write_text(_CONTENDER)

    def spawn(tag: str):
        return subprocess.Popen(
            [sys.executable, str(script), str(SCRIPTS), str(edir),
             str(sentinel), tag, "0.4"])

    p1 = spawn("A")
    time.sleep(0.1)  # ensure A grabs the lock first
    p2 = spawn("B")
    p1.wait(timeout=30)
    p2.wait(timeout=30)

    lines = sentinel.read_text().split()
    check(len(lines) == 4, f"four sentinel events ({lines})")
    # Whoever entered first must exit before the other enters (no interleave).
    first = lines[0].split("-")[0]
    expected = [f"{first}-enter", f"{first}-exit"]
    check(lines[:2] == expected,
          f"first holder completes before second enters ({lines})")
    check(p1.returncode == 0 and p2.returncode == 0, "both contenders exit 0")


def main() -> int:
    # fresh subdir per test for isolation
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        for i, t in enumerate((test_atomic_write_basic, test_atomic_write_midfailure,
                               test_reentrant, test_serializes_two_processes)):
            sub = base / f"t{i}"
            sub.mkdir()
            t(sub)
    print()
    if _failures:
        print(f"FAILED: {_failures} check(s) failed.")
        return 1
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
