"""analysis — the mechanical half of the analyst license.

Owns: nothing. Pure candidate GENERATORS, never verdicts (the oracle's
M39/M49 license, kept whole): each feed computes, deterministically, the
population the analyst is allowed to judge. The analyst receives candidates;
it never goes hunting. candidates_received must equal candidates_assessed in
its attestation — the feed is the boundary that keeps "likely" out of the
record.

Reframed per charter D6: these feeds fire when the human asks an analytical
question, not at a pipeline milestone. The librarian picks the verb(s) a
question implies, runs the feeds, dispatches the analyst over them, and
brings the proposals back to the conversation.

The four verbs (each one feed, each with its boundary):
  pain-synthesis      every pain callout verbatim with its sources
  control-coverage    steps that produce output and declare no control
  conflict-support    every gap that is a conflict on its face
  handoff-friction    orphan outputs and shared inputs across IPO edges
"""

from __future__ import annotations
from pathlib import Path

VERBS = ("pain-synthesis", "control-coverage", "conflict-support", "handoff-friction")


def feeds(root: Path, verb: str) -> list[dict]:
    """The candidate feed for one verb, deterministic, engagement-scoped."""
    raise NotImplementedError


def normalize_artifact(item: str) -> str:
    """THE artifact identity rule for edge matching, in one place (oracle-ported)."""
    raise NotImplementedError
