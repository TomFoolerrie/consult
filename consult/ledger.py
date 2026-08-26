"""ledger — the source of sources.

Owns and writes: <root>/_sources/ — sources.yaml (the ledger), new/,
processed/, parked/. THE one SRC-id minter. Doctrine, ported verbatim from
the oracle: file position is display; the ledger is truth — no question is
ever answered by listing a folder.

The intake door is ONE door (charter D4): a fresh source and a client's
response to an ask arrive the same way — a file in new/, registered, routed.
record_answers ties a source to the asks it answers; asks.match is its
caller. Every touches map is validated against the area manifests
(touches ⊆ manifest slugs) at write time.

credit() records consumption per slug and retires a source to processed/
only when every touch is credited — kind-aware, cross-batch (the balanced
ledger that made run 2 clean).

Killed: every _v1_* compatibility read, per-area registries, centralize().
"""

from __future__ import annotations
from pathlib import Path


def register(root: Path, filename: str, touches: dict) -> str:
    """Register a staged file, tag what it informs; mints and returns SRC-nnn."""
    raise NotImplementedError


def route(root: Path, filename: str, to_areas: list, notes: dict | None = None) -> str:
    """Intake routing: tag, one idempotent-by-hash ledger entry, no copies."""
    raise NotImplementedError


def park(root: Path, filename: str, reason: str) -> None:
    """Decline a staged file into parked/ with a durable reason."""
    raise NotImplementedError


def credit(root: Path, area: str, filled: tuple = (), updated: tuple = ()) -> int:
    """Record consumption; retire fully-read sources; return how many moved."""
    raise NotImplementedError


def record_answers(root: Path, src_id: str, ask_ids: list) -> list:
    """Stamp which asks this source answers (called by asks.match)."""
    raise NotImplementedError


def entries(root: Path) -> list[dict]:
    """The ledger in registration order — a read-only view."""
    raise NotImplementedError


def outstanding(root: Path, area: str) -> dict:
    """{src_id: [slugs this area still owes a read]} — the librarian's debt list."""
    raise NotImplementedError


def status(root: Path) -> dict:
    """The loud-until-empty new/ vs ledger diff — unrouted work by name."""
    raise NotImplementedError
