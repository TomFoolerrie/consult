"""views — the aggregate: every derived view, rebuilt mechanically.

Owns and writes: the derived view files a pinned definition's plan names
(via one write_derived, with the derived-kind marker). Zero tokens: pure
regeneration from capture, run whenever a fragment changed.

Hosts PY_BUILDERS — the one registry a new deliverable's view builder joins
(the extension point that keeps D3's "YAML-sized act" honest: a new shape is
a definition plus at most one entry here). Ships with exactly the builders
the two shipped definitions need:

  client-asks             the curated ask list (the information request's lead)
  information-requests    one entry per taxonomy node at a bound coverage status
  open-validations        the bound gap kind per step, manifest order, cited
  findings-by-theme       accepted findings grouped by theme

Unregistered plan kinds are refused BY NAME before any render (the run-3
placeholder lesson: a view that cannot be built is an error, never a stub
that ships).
"""

from __future__ import annotations
from pathlib import Path

PY_BUILDERS: dict = {}


def aggregate(root: Path, area: str) -> dict:
    """Rebuild every python-owned derived view the pinned plans name; report."""
    raise NotImplementedError


def write_derived(path: Path, heading: str, kind: str, body: str) -> None:
    """The one derived-file writer, marker-stamped."""
    raise NotImplementedError
