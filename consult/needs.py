"""needs — what the objective's shapes still lack.

Owns: nothing. A pure read (never authored, never cached) over three inputs:
the PINNED definitions (definitions.pinned — the shapes the relationship has
produced so far), the coverage map, and the registers. Each need names the
deliverable it blocks, what is missing, where, and on what grounds.

This is the charter's "the needs behind a document are first-class standing
state" — realized as a derived view, because folder state is the only state:
the needs ARE standing (ask any time, always current) precisely because they
are recomputed, not kept.

The engagement loop runs on this module: needs -> the librarian curates asks
-> answers come back -> needs shrink. A deliverable is renderable when its
needs list is empty or every remaining need is a recorded, deliberate gap.
"""

from __future__ import annotations
from pathlib import Path


def standing(root: Path, deliverable: str | None = None) -> list[dict]:
    """Every need blocking the pinned shapes (or one named shape), with grounds."""
    raise NotImplementedError


def render(root: Path, deliverable: str | None = None) -> str:
    """The needs view as printable text, grouped per deliverable then per feed."""
    raise NotImplementedError
