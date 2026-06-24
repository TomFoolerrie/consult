#!/usr/bin/env python3
"""test_cost_instrumentation.py — T56 per-phase cost instrumentation.

Asserts the content-free measurement surface:
  - gatherer `--measure` is a side-channel: the `--json` stdout bundle the
    worker consumes is BYTE-IDENTICAL with vs without `--measure`; the size
    summary goes to STDERR only;
  - `orchestrate.py measure` is READ-ONLY (state/register byte-identical after)
    and content-free;
  - `cost_report.py` reads the persisted cost_map.json (measured output tokens),
    is graceful when it's absent, and is content-free;
  - CONTENT-FREE everywhere: no evidence-ref shape (`...#L<n>-<n>`) leaks into any
    measure/report stream or cost_map.json.

Stdlib only. Isolated scratch engagement (__t56__), removed at the end.
Run: python3 tests/test_cost_instrumentation.py
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
PY = sys.executable

EID = "__t56__"
EDIR = REPO_ROOT / "engagements" / EID
NODE = "record-to-report.close"
L1 = "record-to-report"
REF = re.compile(r"#L\d+(-\d+)?")  # evidence-ref leak shape

_failures = 0


def check(cond: bool, msg: str) -> None:
    global _failures
    print(f"  [{'ok' if cond else 'FAIL'}] {msg}")
    if not cond:
        _failures += 1


def run(args, expect_ok=True):
    """Run a scripts/ command; return (stdout, stderr, rc)."""
    p = subprocess.run([PY, str(SCRIPTS / args[0]), *args[1:]],
                       cwd=str(REPO_ROOT), capture_output=True, text=True)
    if expect_ok and p.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} exited {p.returncode}\n{p.stderr}")
    return p.stdout, p.stderr, p.returncode


def main() -> int:
    if EDIR.exists():
        shutil.rmtree(EDIR)
    try:
        run(["state_machine.py", "init", "--engagement", EID, "--region", "NA"])
        run(["state_machine.py", "set-lens", "--engagement", EID,
             "--node", NODE, "--lens", "automation", "--value", "mixed"])
        state_path = EDIR / "state.json"
        reg_path = EDIR / "register.json"

        # --- 1. gatherer --measure is a side-channel ---
        gather = ["consolidate_inputs.py", "gather", "--engagement", EID,
                  "--node", NODE, "--json"]
        out_plain, _, _ = run(gather)
        out_meas, err_meas, _ = run(gather + ["--measure"])
        check(out_plain == out_meas,
              "gatherer: --json stdout byte-identical with vs without --measure")
        check(err_meas.strip() != "", "gatherer: --measure writes a summary to stderr")
        check(re.search(r"char|token", err_meas, re.I) is not None,
              "gatherer: stderr summary carries size/token figures")
        check(not REF.search(err_meas),
              "gatherer: stderr summary is content-free (no evidence-ref shape)")

        # --- 2. orchestrate measure is read-only + content-free ---
        sb, rb = state_path.read_bytes(), (reg_path.read_bytes() if reg_path.exists() else b"")
        m_out, _, _ = run(["orchestrate.py", "measure", "--engagement", EID])
        check(state_path.read_bytes() == sb,
              "orchestrate measure: state.json byte-identical after (read-only)")
        check((reg_path.read_bytes() if reg_path.exists() else b"") == rb,
              "orchestrate measure: register.json byte-identical after (read-only)")
        check(not REF.search(m_out), "orchestrate measure: output content-free (no ref shape)")
        # and its --json map is valid + content-free
        mj_out, _, _ = run(["orchestrate.py", "measure", "--engagement", EID, "--json"])
        json.loads(mj_out)
        check(not REF.search(mj_out), "orchestrate measure --json: content-free")

        # --- 3. cost_report: graceful absent, populated present, content-free ---
        cmap = EDIR / "cost_map.json"
        if cmap.exists():
            cmap.unlink()
        r_absent, _, rc_a = run(["cost_report.py", "--engagement", EID], expect_ok=False)
        check(rc_a == 0, "cost_report: succeeds with no cost_map.json (graceful)")
        check(not REF.search(r_absent), "cost_report (absent): content-free")

        # inject a CONTENT-FREE cost_map and confirm the measured column populates
        cmap.write_text(json.dumps(
            [{"stage": "draft", "targets": 2, "outputTokensDelta": 8400}]),
            encoding="utf-8")
        r_present, _, _ = run(["cost_report.py", "--engagement", EID])
        check("8400" in r_present, "cost_report: measured output-token column populated")
        check(not REF.search(r_present), "cost_report (present): content-free")

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
