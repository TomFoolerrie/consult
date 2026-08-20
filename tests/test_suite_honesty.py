"""M64 gate — the skip budget: the suite cannot go quiet without failing.

The pre-M64 tree gated ~30 modules behind feature-detect skips
(`pytest.importorskip`, `_has(module, attr)` skipifs, module-level
`pytest.skip`). Every gated feature is BUILT, so the gates were retired:
importorskips became plain imports, gate variables became
`gatecheck.landed(...)` (which ASSERTS the feature is present — a rename
breaks loudly instead of un-testing a feature), and module-level skips
became asserts.

This module owns the budget going forward: the number of skip constructs in
the tree is PINNED (zero, plus the explicit allowlist below). A new skip
cannot enter the suite without landing here deliberately, with a reason.
"""

import re
import subprocess
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent

# The pinned budget: (filename, token) pairs that are ALLOWED to exist.
# Each entry needs a reason a reviewer would accept.
ALLOWED = {
    # environment guard, not a feature gate: the checkpoint test is
    # meaningless when tmp_path accidentally sits inside a git work tree.
    ("test_orchestrate.py",
     'pytest.skip("tmp_path unexpectedly inside a git work tree")'),
}

SKIP_TOKEN = re.compile(
    r"pytest\.importorskip|pytest\.mark\.skipif|pytest\.mark\.skip\b"
    r"|pytest\.skip\(|pytest\.mark\.xfail|pytest\.xfail\(")


def _skip_constructs():
    found = []
    for f in sorted(TESTS.glob("test_*.py")):
        if f.name == "test_suite_honesty.py":
            continue
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(),
                                 start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if SKIP_TOKEN.search(stripped):
                found.append((f.name, i, stripped))
    return found


class TestSkipBudget:
    def test_no_skip_construct_outside_the_allowlist(self):
        offenders = []
        for fname, lineno, line in _skip_constructs():
            if any(fname == a_file and a_tok in line
                   for a_file, a_tok in ALLOWED):
                continue
            offenders.append(f"{fname}:{lineno}: {line}")
        assert not offenders, (
            "skip/xfail constructs found outside the M64 allowlist — a "
            "feature-detect gate that starts skipping un-tests live code "
            "silently. Either fix the feature, or add the construct to "
            "tests/test_suite_honesty.py ALLOWED with a reason:\n  "
            + "\n  ".join(offenders))

    def test_allowlist_entries_still_exist(self):
        """A stale allowlist row is budget nobody is using — trim it."""
        constructs = {(f, line) for f, _n, line in _skip_constructs()}
        for a_file, a_tok in ALLOWED:
            assert any(f == a_file and a_tok in line
                       for f, line in constructs), (
                f"stale allowlist entry: {a_file!r} no longer contains "
                f"{a_tok!r}")

    def test_gatecheck_fails_loud_on_a_missing_feature(self):
        """The retired gates' replacement breaks loudly: a gate whose
        feature vanished FAILS (the rename demo the ticket asks for,
        kept as a unit test instead of a scratch branch)."""
        import gatecheck
        import pytest as _pytest
        mark = gatecheck.landed(False, reason="feature present")
        assert mark.name == "gate_retired"
        with _pytest.raises(AssertionError) as exc:
            gatecheck.landed(True, reason="scaffold.promote_client renamed")
        assert "promote_client" in str(exc.value)


class TestRunLevelAccounting:
    def test_full_collection_carries_no_skip_marks(self):
        """Collection-level accounting: pytest itself reports zero
        deselected/skip-marked tests over the whole tree."""
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q",
             str(TESTS)],
            capture_output=True, text=True,
            cwd=str(TESTS.parent))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        summary = proc.stdout.strip().splitlines()[-1]
        assert "error" not in summary.lower(), summary
        assert "skip" not in summary.lower(), (
            f"collection reports skips: {summary}")
