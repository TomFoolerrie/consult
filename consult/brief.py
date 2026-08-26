"""brief — deterministic work orders for every dispatch.

Owns: nothing. Resolves the procedural half of a delegate's contract once,
from the same loaders the enforcement points use, and prints a reading list
+ finish checklist. Decides nothing about content (oracle discipline, kept):
the brief is why delegates could run near-error-free for three runs — the
facts arrive resolved, the judgment stays theirs.

Every dispatch's FIRST ACTION is its brief; every brief carries the standing
tenure (case law) and open flags so no sitting re-derives paid-for judgment.

Three brief kinds, one per delegate:
  drafter    one fragment: its sources, registries, queued notes, mode,
             upstream seams, the minting bars
  reader     one question against one-or-few sources: what to read, what to
             return (grounded material only — a reader writes nothing)
  analyst    one verb: the license text, the candidate feed, register state
Plus the librarian's own sitting brief: the engagement picture (state +
coverage + needs + debts + tenure) assembled in one place.
"""

from __future__ import annotations
from pathlib import Path


def librarian(root: Path) -> str:
    """The sitting brief: the whole engagement picture, one printable block."""
    raise NotImplementedError


def drafter(root: Path, area: str, slug: str, mode: str) -> str:
    """The per-fragment work order (first-draft | update; update is EDIT mode)."""
    raise NotImplementedError


def reader(root: Path, question: str, src_ids: list) -> str:
    """The bounded source-read work order: the cheap 'go find out' dispatch."""
    raise NotImplementedError


def analyst(root: Path, verb: str) -> str:
    """The analysis work order: license, feed, findings-register state."""
    raise NotImplementedError
