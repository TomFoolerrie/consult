"""gatecheck.py — the M64 skip-budget helper.

Every feature the old feature-detect skip gates guarded is BUILT, so a gate
that fires no longer un-tests a feature quietly: `landed()` ASSERTS the
feature is present (a rename breaks loudly at import time) and returns a
no-op mark so the `@needs_x` decorator sites keep working unchanged.
tests/test_suite_honesty.py owns the budget: no new skip construct enters
the tree without landing on its allowlist deliberately.
"""

import pytest


def landed(missing, reason: str = ""):
    """`missing` is the old gate's skip condition. The feature is BUILT:
    its absence is a FAILURE, never a skip."""
    assert not missing, (
        f"BUILT feature missing (the old skip gate would have hidden this): "
        f"{reason}")
    return pytest.mark.gate_retired
