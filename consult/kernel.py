"""kernel — type declarations and fragment parsing.

Owns: nothing on disk. Loads kernel/types/<name>.yaml into a validated
TypeDecl and parses a fragment's markdown into an Entity through it. The
declaration is the vocabulary authority: parts, callout kinds (label, prefix,
home, declared fields), channels. Exactly two types exist (charter D2):
process-step (the capture substrate) and taxonomy-node (the map).

Ported from the oracle: the parse discipline (tdecl-driven section split,
callout grammar, consult-meta channels), the fail-loud loader (a refused type
is never half-registered), and the minting-bar field declarations (CONTROL's
four fields, GAP's Grounds+Nature) — vocabulary the checks read, never parse
gates.

Killed from the oracle: the activity type, every alias table (letters, slugs,
titles), heading_resolver's v1 fallbacks, can_serve's v1 paths.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TypeDecl:
    """One validated type: name, parts (slug/title/kind), callouts, channels."""
    name: str
    parts: tuple
    callouts: tuple
    channels: tuple


@dataclass(frozen=True)
class Entity:
    """One parsed fragment: slug, part bodies, callouts, channel bindings."""
    slug: str
    parts: dict
    callouts: tuple
    bindings: dict


def load_type(name: str) -> TypeDecl:
    """Load and validate kernel/types/<name>.yaml; cached; fail-loud."""
    raise NotImplementedError


def parse_entity(text: str, tdecl: TypeDecl, slug: str) -> Entity:
    """Parse one fragment through its declaration; grammar defects are named errors."""
    raise NotImplementedError


def open_gaps(entity: Entity) -> list[dict]:
    """Every open validation gap on one entity, document order."""
    raise NotImplementedError
