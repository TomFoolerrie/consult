"""coverage — what the brain knows it knows.

Owns: nothing. A pure function, never a file (oracle doctrine, kept): every
call re-reads the ledger and the fragments; nothing is cached, so the map can
never be stale.

For every taxonomy node: a status from the evidence —
  evidenced    steps drafted AND citing sources
  claimed      known to exist, asserted, uncited
  thin         mapped, but the record holds nearly nothing
  conflicted   carries a lens-conflict record (two sources disagree — both
               readings held, never adjudicated; v0's "single most valuable
               thing to port back", kept as first-class here)
  outstanding  a registered source still owes this node a read

This is the honesty substrate: answers.ground reads it to label an answer's
standing, needs.standing reads it to know what a shape lacks, and the
librarian reads it to decide what to ask the client next.
"""

from __future__ import annotations
from pathlib import Path


def node_steps(root: Path) -> dict:
    """{node slug: [step slugs]} — the derived node<->step join (never stored)."""
    raise NotImplementedError


def status(root: Path) -> dict:
    """{node slug: status} for every taxonomy node, recomputed from disk."""
    raise NotImplementedError


def conflicts(root: Path) -> list[dict]:
    """Every lens-conflict record: node, both claims, both source ids."""
    raise NotImplementedError


def report(root: Path) -> str:
    """The map as printable text — the human's and librarian's shared picture."""
    raise NotImplementedError
