"""definitions — the deliverable definition language.

Owns: nothing on disk. Loads kernel/deliverables/<name>.yaml (or an
engagement-local definition, which shadows the shipped one) through the
oracle's proven four fail-loud stages:

  1. syntax        keys, blocks (static | view | entity-part), duplicate ids
  2. vocabulary    every type/part/callout/channel a binding names must be
                   declared by the bound type; the special binding verbs
                   (coverage:/of:, asks:, findings:, count:) each name their
                   admitted shape here
  3. serviceability  a REPORT (records, never an exception): what this
                   engagement is missing for this definition
  4. skin          format must be a registered renderer; requires must be a
                   subset of its capabilities

CHARTER PROPERTY (D3): adding a deliverable is a YAML-sized act. This module
is the wall that keeps it true — if a new shape needs code beyond a view
builder registered in views.PY_BUILDERS, stage 2 refuses it by name and the
engine does not grow an exception.

Definitions are expected to EVOLVE with the client relationship: pinning and
amending a shape are the same cheap act, and the needs view re-reads the
definition every call, so an amended shape changes what the engagement owes
with no migration step.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Definition:
    """One validated definition: name, title, ordered blocks, bindings, skin."""
    name: str
    title: str
    blocks: tuple
    bindings: dict
    skin: dict


def load(name: str, engagement=None) -> Definition:
    """Load by name; an engagement-local file shadows the shipped one; fail-loud."""
    raise NotImplementedError


def serviceability(defn: Definition, engagement) -> list[dict]:
    """Stage 3 as records: every gap between this engagement and this shape."""
    raise NotImplementedError


def compile_plan(defn: Definition, engagement) -> dict:
    """The ordered render plan: views to build, blocks to emit, in shape order."""
    raise NotImplementedError


def pinned(engagement) -> list[Definition]:
    """The shapes this engagement has pinned so far — what needs.standing reads."""
    raise NotImplementedError
