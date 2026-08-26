"""render — any pinned definition to a client-ready document.

Owns and writes: <root>/_exports/. ONE verb: render(deliverable) —
materialize the plan's views, aggregate, compile, REFUSE ON PLACEHOLDER by
view name, then emit the docx wearing the definition's own shell (its title,
its skin's furniture — never another deliverable's). The whole M78 lesson,
present from birth instead of retrofitted.

Demand-driven by charter: nothing schedules a render; the librarian proposes
one when needs.standing says the shape is served (or the human asks), and a
render of the information request is immediately followed by asks.mark_sent.

Readiness runs on exactly what the client would read, and a placeholder of
any spelling is a refusal, not a warning. Body cleaning is line-count-
preserving (the provenance discipline kept, cheap insurance even with the
markup loop dead).

Killed: working/final mode split collapses to one honest mode with --draft
watermarking; kits; tracked-changes; screenshot machinery until a run
demands it.
"""

from __future__ import annotations
from pathlib import Path


def deliverable(root: Path, name: str, out: Path | None = None, draft: bool = False) -> dict:
    """Render one pinned definition end to end; refuses placeholders by view
    name; returns the stats report with the output path."""
    raise NotImplementedError
