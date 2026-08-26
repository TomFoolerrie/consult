"""answers — the question interface. This module is the product.

Owns: nothing. A pure read that assembles the GROUNDED MATERIAL for
answering a human question about the client, with the honesty contract
attached to every statement:

  evidenced   in capture, cited — here are the SRC ids
  claimed     in capture, uncited — flagged as such
  contested   a lens conflict — BOTH readings, both sources, never a winner
  absent      not in the record — and here is the ask or the cheap
              source-read that would close it (the proposal, not the spend)

Division of labor, stated plainly: this module does NOT phrase the answer —
the librarian does, in conversation. ground() returns the material: the
relevant entities, callouts, coverage statuses, register entries, and
conflicts for a topic, each tagged with its standing. Determinism stays in
the engine; judgment stays in the tenancy. That split is what makes "the AI
just needs to know the answer or how to get it" auditable — every sentence
the librarian says can point at the material it stood on.

"I don't know, and here's how we find out" is a first-class result: an
absent/thin grounding comes back with proposed_ask / proposed_read stubs the
librarian can put to the human.
"""

from __future__ import annotations
from pathlib import Path


def ground(root: Path, topic: str) -> dict:
    """The grounded material for a topic: entities, callouts, coverage,
    register entries, conflicts — each tagged evidenced|claimed|contested|absent,
    plus proposed_ask/proposed_read stubs for what's missing."""
    raise NotImplementedError


def cite(root: Path, statement_grounds: list) -> list[str]:
    """Resolve grounds to citable form (SRC ids, slug#ID addresses) or refuse by name."""
    raise NotImplementedError
