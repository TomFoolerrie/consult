"""journal — judgment's homes.

Owns and writes: <root>/_journal/ — flags.yaml, tenure.yaml, sessions/.
The charter's law made concrete: a token spent on judgment lands in a file
the machine reads; a transcript is not a home.

Three records, one module:
  * FLAGS — any agent's judgment aimed at something its pass doesn't own
    (FLAG-nnn; open until actioned/declined WITH a reference). The open
    count is a visible debt in desk.state.
  * TENURE — the librarian's own precedent record (ruling | deferred |
    doubt; TEN-nnn). A new sitting inherits case law instead of re-deriving
    it (~100k tokens saved per sitting, run-2 evidence).
  * SESSIONS — the session record, written BY THE MACHINERY at checkpoint
    time (never by orchestrator virtue — the oracle's three audits living
    only in transcripts is the named evidence gap this closes). Timeline,
    dispatch/cost table, deviations, end-state checks.

Engagement-scoped (one journal per engagement), unlike the oracle's per-area
flags — the librarian is engagement-wide, so its memory is too.
"""

from __future__ import annotations
from pathlib import Path


def flag(root: Path, target: str, origin: str, text: str) -> str:
    """File one flag -> FLAG-nnn."""
    raise NotImplementedError


def flag_close(root: Path, flag_id: str, state: str, reference: str) -> None:
    """actioned | declined, always with the actioning reference."""
    raise NotImplementedError


def open_flags(root: Path) -> list[dict]:
    """The open judgment debt."""
    raise NotImplementedError


def tenure(root: Path, kind: str, text: str) -> str:
    """File one precedent entry (ruling | deferred | doubt) -> TEN-nnn."""
    raise NotImplementedError


def tenure_standing(root: Path) -> list[dict]:
    """The standing case law a new sitting inherits."""
    raise NotImplementedError


def session_append(root: Path, event: dict) -> None:
    """Machinery-written session record: every verb/dispatch appends itself."""
    raise NotImplementedError
