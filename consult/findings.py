"""findings — where the brain is allowed to hold an opinion.

Owns and writes: <root>/_registers/findings.yaml (one _dump). The only store
of judgment about the client's processes, fed exclusively by the analysis
loop: analysis.feeds computes candidates, the analyst agent proposes, the
human accepts or rejects in conversation, and only `accepted` ever renders
or grounds an answer.

Grounds are mandatory and must RESOLVE — to a ledger SRC id, a
procedure-qualified callout address (slug#LOCAL-ID), or an entity slug —
refused by name otherwise (the oracle's M57 currency, kept). Rejection is
terminal and kept: a rejected finding is case law, not deleted.
"""

from __future__ import annotations
from pathlib import Path


def propose(root: Path, claim: str, grounds: list, theme: str) -> str:
    """Mint FIND-nnn; every ground must resolve or the mint refuses by name."""
    raise NotImplementedError


def accept(root: Path, finding_id: str) -> None:
    """The human's yes, in conversation, recorded."""
    raise NotImplementedError


def reject(root: Path, finding_id: str, reason: str) -> None:
    """The human's no — terminal, kept, with reason."""
    raise NotImplementedError


def renderable(root: Path) -> list[dict]:
    """Accepted only — what a deliverable may bind and an answer may cite."""
    raise NotImplementedError


def by_theme(root: Path) -> dict:
    """Renderable findings grouped by theme, first-appearance order."""
    raise NotImplementedError
