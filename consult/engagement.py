"""engagement — the folder truth.

Owns and writes: components/<area>/manifest.json and fragment SKELETONS, both
only inside the scaffold verb (the confirm gate's deterministic half). After
scaffold, fragments belong to their drafters and the manifest changes only
through verbs that own a slice of it.

The locate rule: an engagement root is the directory holding _sources/ — one
mode, one marker (charter D1). locate() walks up from any path inside; a tree
that LOOKS like an engagement (has components/ and area dirs) but has no
_sources/ is a named contradiction, returned as such — never a silent
downgrade and never `done` (the run-3 wipe lesson, structural).

Ported: manifest as membership + ordering authority (order: manifest is what
makes two renders byte-equal), slugs permanent, display numbers derived,
scaffold-as-merge (promotion never wipes what it promotes — the run-1
lesson, M65, kept as a test not a memory).

Killed: per-area _reference/sources, the v1 letter/band conventions,
split_doc, every alias.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Engagement:
    """Resolved paths for one engagement: root, areas, registers, journal, exports."""
    root: Path
    areas: tuple


def locate(path: Path) -> Engagement:
    """Walk up to the _sources/ marker; contradiction and absence are named refusals."""
    raise NotImplementedError


def manifest(area: Path) -> dict:
    """Load + validate one area manifest; fail-loud."""
    raise NotImplementedError


def entities(area: Path) -> list:
    """Every capture entity of the area, manifest order, parsed through kernel."""
    raise NotImplementedError


def taxonomy(area: Path) -> list:
    """Every taxonomy-node entity of the area's _taxonomy/, name order."""
    raise NotImplementedError


def scaffold(area: Path, proposed: Path) -> dict:
    """The confirm gate's deterministic half: MERGE proposals live, scaffold
    manifest + skeletons, promote staged asks, stamp the record. Returns the
    report of everything it did; destroys nothing it promotes."""
    raise NotImplementedError
