"""desk — the librarian's desk.

Owns and writes: the hold block of _client/consult.yaml (line surgery with
post-edit self-verification and restore-on-mismatch — the oracle's M78
editor, ported), git (checkpoint), and the budget line of the session
record. Everything else here is a read.

state() replaces the oracle's thirteen-guard advisor AS THE SEAT OF CONTROL:
it does not command, it DESCRIBES — one structured snapshot the librarian
consults: unrouted sources, coverage summary, needs summary, ask debts
(unsettled, open flags), pinned shapes and their serviceability, git health,
holds, budget spent/remaining. The playbook order lives in the librarian's
contract, not in code. Two hard rules survive as structure, not advice:
  * a self-contradictory folder is its own state ("contradiction"), and
    state-changing verbs refuse while it stands;
  * "all quiet" requires positive evidence of completeness — quiet-by-damage
    is a contradiction, never done (the run-3 wipe, structural).

checkpoint() commits the WHOLE engagement (root pathspec — no curated list
to forget a directory; the run-1 F5 window closed by construction) and
appends the machinery-written session record.

budget: the D9 mechanism. The human sets a per-sitting token budget; every
dispatch is proposed with a cost estimate and auto-proceeds under the
remaining budget; over it — or anything client-facing — waits for the
human's word. spend() records actuals so estimates are auditable.
"""

from __future__ import annotations
from pathlib import Path


def state(root: Path) -> dict:
    """The engagement snapshot the librarian consults — describes, never commands."""
    raise NotImplementedError


def checkpoint(root: Path, label: str, dry_run: bool = False) -> dict:
    """Commit the whole engagement as consult: <label>; append the session record."""
    raise NotImplementedError


def edit_hold(root: Path, action: str, release: bool = False) -> None:
    """The gate-answer verb: add/remove one hold, self-verify, restore on mismatch."""
    raise NotImplementedError


def budget_set(root: Path, tokens: int) -> None:
    """The human sets the sitting's spend budget."""
    raise NotImplementedError


def budget(root: Path) -> dict:
    """{limit, spent, remaining} for the sitting."""
    raise NotImplementedError


def spend(root: Path, estimate: int, actual: int, what: str) -> None:
    """Record one dispatch's estimated and actual cost in the session record."""
    raise NotImplementedError
