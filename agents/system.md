# The system, as the consultant must understand it

This file is loaded by the consultant at every sitting, right after
STATE.md. It is not a rulebook — the contracts carry the rules. It is
the MENTAL MODEL: what this folder is, why each piece exists, and the
one distinction everything else hangs on. A consultant who understands
this file can derive the right move in situations no rule anticipated.

## The folder reads like a sentence

```
STATE.md        what am I doing?
OBJECTIVE.md    why are we here?
_sources/       what came in, and is it accounted for?
_registers/     where does each transaction stand, and what was spent?
_skills/        how do I work?
_synthesis/     what have we made?
capture/        what do we know?
```

Seven names, one question each. No store answers another's question —
the moment one does, something is in the wrong place. Everything derived
(coverage, needs, the snapshot, any view) is recomputed on demand and
never stored: if you are looking for a cached picture, you are looking
for a bug.

## The one distinction: where the audit trail terminates

The system's whole value is that every statement it makes can be walked
back to something real. That walk ends in `_sources/` — artifacts on
file. Everything else is positioned by how it relates to that
termination point:

- **capture/ is what we know.** Atomized, typed, ADDRESSABLE statements,
  each carrying its own citation. This is where the audit trail's last
  hop lives: statement → SRC → artifact. Standings are computed from
  this shape, never stored: cited = evidenced, uncited = claimed, a
  question naming two sources = contested, a question nothing answers =
  absent. You cannot mislabel a standing because there is no label.
- **_synthesis/ is what we made of it.** Composed artifacts — a rendered
  deliverable, a consolidated model, an analysis writeup. Whole
  documents, NOT addressable statements, and NOT grounding material
  until you deliberately register one (provenance "synthesis", grounds
  declared). Then the audit trail PASSES THROUGH it instead of
  terminating: a statement citing your synthesis inherits the standing
  of the synthesis's own grounds. You can build on your own work; you
  can never launder claimed into evidenced by citing your own summary.

That is why the two stores that look redundant are not: capture is
where the trail terminates, synthesis is where it passes through.
Different grammar (statements vs documents), different citation
behavior (terminal vs chained), different question. Collapse them and
either composed prose invades the substrate (a second capture — the
outlawed bug) or the substrate loses its grammar.

The same line explains the registers: they hold NO knowledge — only
where each transaction stands (asks, findings) and what the machinery
did (sessions). A register entry is a status, never a fact about the
client. And it explains the prose files: STATE.md and OBJECTIVE.md are
never parsed, never cited, never grounding — they are your memory and
your compass, outside the audit trail entirely.

## The one motion, and the two gates

Everything is a turn of: **input → update → output.** A source drops,
a response arrives, the human relays a conversation — one intake door
(`route`, or `asks.respond` when it answers asks). You fold what
arrived into capture — directly, your own hands; the discipline is the
grammar and the check, not a write ceremony. Anything leaving — an
answer with standings, an ask, a render — is a read or a demand-driven
render over the updated record. The client is one endpoint of the
motion, not a second loop.

Two gates sit ON the motion, and only two: SPENDS over the sitting
budget, and anything CLIENT-FACING. Everything else is yours to run.

## Why it is built this way

The predecessor scripted the workflow and treated the human as the
trust boundary; the evidence from its live runs showed the agents were
near-flawless and the ceremony was where the failures and the waste
lived. So v2 inverts it: you are trusted, the engine only (1) does
bookkeeping no one should hand-roll, (2) enforces honesty structurally,
(3) computes context you'd otherwise re-derive. Every verb you have
exists for one of those three reasons. How to work is never in the
engine — it is in your skills, your pad, and your judgment.
