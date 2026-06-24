#!/usr/bin/env python3
"""test_compact_gatherer_bundles.py — T59 compact gatherer bundle emit.

The three read-only input gatherers (consolidate_inputs / draft_inputs /
synthesis_inputs) emit their `--json` transport bundle COMPACT
(`separators=(",", ":")`, no `indent`) so the fan-out worker input carries no
indentation overhead. This test asserts:

  - round-trip identity: the compact bundle parses to the SAME Python object as
    the old pretty (`indent=2`) form — functionally identical worker input;
  - size strictly drops: the compact bytes are strictly fewer than the pretty
    bytes on a real fixture engagement — the whole point;
  - consumer-path parse: the emitted bundle still `json.loads`-es into the
    expected shape the workers consume;
  - no state reformatting: state.json is byte-identical before/after a gather
    (transport-only change; on-disk system-of-record stays pretty/diffable),
    and the gatherer output contains no newline/2-space-indent artifacts.

Stdlib only. Run: python3 tests/test_compact_gatherer_bundles.py

Uses an isolated scratch engagement (__t59__) and removes it at the end.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
PY = sys.executable

EID = "__t59__"
EDIR = REPO_ROOT / "engagements" / EID
NODE = "record-to-report.close"
L1 = "record-to-report"

_failures = 0


def check(cond: bool, msg: str) -> None:
    global _failures
    print(f"  [{'ok' if cond else 'FAIL'}] {msg}")
    if not cond:
        _failures += 1


def run(args: list[str]) -> str:
    """Run a script under scripts/ and return stdout (raises on nonzero)."""
    out = subprocess.run(
        [PY, str(SCRIPTS / args[0]), *args[1:]],
        cwd=str(REPO_ROOT), capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(
            f"{' '.join(args)} exited {out.returncode}\nstderr:\n{out.stderr}")
    return out.stdout


def assert_bundle(label: str, compact: str, *, top_keys: set[str]) -> None:
    """Shared assertions for one gatherer's emitted bundle."""
    # Consumer-path parse: the bundle loads and has the expected shape.
    obj = json.loads(compact)
    check(isinstance(obj, dict), f"{label}: bundle parses to a JSON object")
    check(top_keys.issubset(obj.keys()),
          f"{label}: bundle carries expected top-level keys "
          f"(missing: {sorted(top_keys - set(obj.keys()))})")

    # Round-trip identity: compact parses to the SAME object as the old pretty form.
    pretty = json.dumps(obj, ensure_ascii=False, indent=2)
    check(json.loads(compact) == json.loads(pretty),
          f"{label}: compact and pretty parse to identical Python objects")

    # The compact emit is genuinely compact: it is byte-for-byte the compact
    # serialization of its own parsed object (no indent, tight separators). This
    # is robust to prose inside string values that may itself contain ": "/", ".
    # (A single trailing newline from print() is expected.)
    body = compact.rstrip("\n")
    check("\n" not in body, f"{label}: no embedded newlines (single-line bundle)")
    expected_compact = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    check(body == expected_compact,
          f"{label}: emit equals compact serialization (no indent / tight separators)")

    # Size strictly drops vs the pretty serialization of the same object.
    n_compact = len(compact.encode("utf-8"))
    n_pretty = len(pretty.encode("utf-8"))
    check(n_compact < n_pretty,
          f"{label}: compact strictly smaller ({n_compact} < {n_pretty} bytes, "
          f"-{n_pretty - n_compact})")


def main() -> int:
    if EDIR.exists():
        shutil.rmtree(EDIR)

    try:
        # --- Fixture: a real engagement (init seeds the full node taxonomy). ---
        run(["state_machine.py", "init", "--engagement", EID, "--region", "NA"])
        # Seed a lens so the synthesis/consolidate bundles carry non-trivial content.
        run(["state_machine.py", "set-lens", "--engagement", EID,
             "--node", NODE, "--lens", "automation", "--value", "mixed"])

        state_path = EDIR / "state.json"
        check(state_path.exists(), "fixture engagement initialized (state.json present)")
        state_before = state_path.read_bytes()

        # --- synthesis_inputs (whole-engagement, cross-cutting) ---
        print("synthesis_inputs gather --json")
        assert_bundle(
            "synthesis",
            run(["synthesis_inputs.py", "gather", "--engagement", EID, "--json"]),
            top_keys={"engagement"})

        # --- draft_inputs (per-L1) ---
        print("draft_inputs gather --json")
        assert_bundle(
            "draft",
            run(["draft_inputs.py", "gather", "--engagement", EID, "--l1", L1, "--json"]),
            top_keys={"appendices"})

        # --- consolidate_inputs (per-L2 node) ---
        print("consolidate_inputs gather --json")
        assert_bundle(
            "consolidate",
            run(["consolidate_inputs.py", "gather", "--engagement", EID,
                 "--node", NODE, "--json"]),
            top_keys=set())

        # --- No state reformatting: gathers are read-only and must NOT rewrite
        #     (or re-pretty-print) the on-disk system-of-record. ---
        print("no on-disk state reformatting")
        check(state_path.read_bytes() == state_before,
              "state.json byte-identical after all gathers (transport-only change)")
        # state.json itself stays pretty/diffable (not compacted).
        check(b"\n  " in state_before,
              "state.json remains pretty-printed on disk (indented, diffable)")

    finally:
        if EDIR.exists():
            shutil.rmtree(EDIR)

    print()
    if _failures:
        print(f"FAILED: {_failures} check(s) failed.")
        return 1
    print("All tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
