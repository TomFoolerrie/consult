"""asks — the engagement's client-engagement register.

Owns and writes: <root>/_registers/asks.yaml (one _dump, the module's only
write). The charter makes this FIRST CLASS: the brain generates client
engagement throughout the engagement, and this register is where every
curated, client-voiced request lives from proposal to settlement.

Lifecycle (oracle-proven, run 3 "worked on first contact"):

    proposed -> accepted -> sent -> answered -> settled
                                 \\-> retired (with reason)
    plus the unasked bucket: gaps deliberately NOT put to the client, with why.

Invariants, kept as checks not memories:
  1. every gap id appears in the register exactly once (asked or unasked);
  2. answered-but-unsettled is a visible debt (the librarian's follow-up list);
  3. only `accepted` is bindable by a deliverable (checked at definition load);
  4. mark-sent sweeps accepted only — sent is not re-sent.

The return path: the client's response is put back in as a source drop;
match() records the answer AND stamps the ledger in one verb.
"""

from __future__ import annotations
from pathlib import Path


def propose(root: Path, text: str, gaps: list, audience: str, artifact: str) -> str:
    """Mint a proposed ask (client-voiced, referencing the gaps it would close)."""
    raise NotImplementedError


def accept(root: Path, ask_id: str) -> None:
    """The human gate's yes, recorded."""
    raise NotImplementedError


def mark_sent(root: Path) -> int:
    """Record every accepted ask as sent (the render verb's sibling)."""
    raise NotImplementedError


def match(root: Path, src_id: str, ask_ids: list) -> list[dict]:
    """A response came back: record answered + stamp the ledger, one verb."""
    raise NotImplementedError


def settle(root: Path, ask_id: str) -> None:
    """The answer has been folded into capture; the loop for this ask closes."""
    raise NotImplementedError


def retire(root: Path, ask_id: str, reason: str) -> None:
    """Withdraw an ask with a durable reason."""
    raise NotImplementedError


def unask(root: Path, gap: str, reason: str) -> None:
    """Record that a gap is deliberately not the client's to answer."""
    raise NotImplementedError


def entries(root: Path, status: str | None = None) -> list[dict]:
    """Asks in mint order (copies)."""
    raise NotImplementedError


def unsettled(root: Path) -> list[dict]:
    """Answered-but-unsettled — the librarian's follow-up debt."""
    raise NotImplementedError
