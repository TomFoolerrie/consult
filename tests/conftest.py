"""Shared test setup: make scripts/ and the docx-builder importable.

Conventions for this suite (all test modules follow them):
- Every filesystem fixture lives under pytest's tmp_path — tests never read
  or write repo-tracked files, and never depend on test execution order.
- Tests exercise observable contracts (function results, files produced, CLI
  exit codes), not implementation internals.
- No network, no wall-clock dependence, no randomness without a seed.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "scripts",
          ROOT / "skills" / "consult-docx-builder" / "scripts"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)
