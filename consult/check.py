"""check — the QC gate, distilled.

Owns: writes only its signal file. The oracle's reconcile rebuilt at v2's
size: the checks that defended live runs, none that defended v1. Errors exit
nonzero; warnings print; every message names its file and line.

The kept checks (each a function, registered in CHECKS):
  grammar        per-fragment callout/ID/gap parse through the declaration
  substance      a zero-byte or heading-only fragment is a blocking error
  citations      every cited SRC resolves; drafted prose cites
  touches        ledger touches ⊆ manifest slugs
  xrefs          every [[slug]] resolves; dangling is an error
  hedges         uncertainty lives in callouts, never body prose
  individuals    people appear by role, never by name
  markers        derived files carry the right kind marker
  ask-coverage   every gap id in the ask register exactly once
  placeholders   no pending stub in anything a render would emit
  registers      referenced register entries resolve; citable fields not blank

Killed: the v1 shape checks, letter checks, British-spelling nannying moved
to the drafter contract, merged-section archaeology.
"""

from __future__ import annotations
from pathlib import Path

CHECKS: tuple = ()


def run(root: Path, area: str) -> int:
    """Run the whole gate over one area; 0 clean, nonzero with named defects."""
    raise NotImplementedError
