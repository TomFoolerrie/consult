#!/usr/bin/env python3
"""
kinds.py — M53's shared public home for the kind resolvers (docs/v2/
M53-engine-housekeeping.md Parts A and C): the declaration-driven reads that
analysis, hygiene, needs, agenda and plan_views were sharing through private
`_`-named imports across module lines. Pure relocation — same functions, same
behavior, one public home.

WHAT LIVES HERE, and where each piece came from:

  * the step walk (`area_steps`) and the callout reads (`callouts`,
    `callout_blob`, `nature`) — analysis.py's resolvers;
  * the gap-kind resolver (`gap_prefix`) — the prefix-through-the-declaration
    read analysis.py and hygiene.py each carried, one body now;
  * the declared `Nature:` vocabulary (`declared_natures`) — needs.py's read
    of the type declaration's `field_enums`;
  * the area→engagement-root derivation (`engagement_root`) — plan_views'
    `_root_of`, published once instead of reimplemented module-by-module;
  * the coverage-status selection (`selected_statuses`) with the ONE
    documented alias expansion this codebase performs: the surveyor's
    sufficiency word `thin` collapses to `THIN_MEANS` (`claimed`, `sourced`) —
    scripts/definitions.py's `_ALLOWED_COVERAGE_STATUSES` comment states the
    sentence this expansion is; `coverage_map.coverage()` never returns
    `thin`, so any consumer of a `coverage:` binding must collapse it, and
    this is the one place that does.

VOCABULARY COMES FROM THE DECLARATION AND THE BINDINGS (the M36 shape-audit
rule, honoured here as in every consumer). No part slug, part title, callout
label or callout prefix is typed in this module. The only names typed are
definition and binding names — the contract with the definition files:

  * `kernel.load_type(STEP_TYPE)` carries the parts and the callout kinds;
  * the GAP kind is whatever the shipped information-request definition's
    `step-gaps` binding selects, translated into the prefix the fragments
    carry through the declaration (`matrix_views._prefixes`' discipline);
  * the `Nature:` FIELD name is the one prose-furniture constant
    (`NATURE_FIELD`, the v1 conflict grammar's field) — a field name, not
    document shape, and analysis.py re-exports it as before.

READ-ONLY, CACHE-FREE (analysis.py's rule, inherited with the functions):
everything here opens files for reading only, and nothing is memoized.

REFUSALS. `KindsError` is raised only when the declaration or a binding does
not support the question (`gap_prefix` resolving to zero or several kinds);
`engagement_root` refuses BY NAME (ValueError naming the area) for an area
outside any engagement's `components/` tree. Callers that historically raised
their own error types (`AnalysisError`, `HygieneError`) pass them through
`gap_prefix`'s private `_err` seam, so no existing catch site changes meaning.

IMPORT DISCIPLINE: kernel and definitions are imported LAZILY inside the
functions, plan_views' pattern and for the same reason — aggregate.py imports
the builder modules at import time and kernel.py imports aggregate, so a
module-level import here would close the cycle for any builder that imports
this module at its top. matrix_views has no such edge and is imported plainly.

Python 3, stdlib + the engine's own modules.
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

from pathlib import Path

from matrix_views import (
    _binding as _binding,
    _names as _names,
    _prefixes as _prefixes,
    _steps as _steps,
    STEP_TYPE as STEP_TYPE,
)

#: The definition whose binding names the gap kind, and that binding's name —
#: the contract with the definition file (analysis.py's constants, relocated
#: with the resolver; analysis re-exports them for its own consumers).
REQUEST_DEFINITION = "information-request"
BINDING_GAPS = "step-gaps"

#: The v1 conflict grammar's field NAME — hand-authored prose furniture, not
#: document shape (the shape audit's concern is part/callout vocabulary, which
#: still comes from the declaration). Matched case-insensitively everywhere.
NATURE_FIELD = "nature"

#: The surveyor's alias, and what it collapses to. See the module docstring
#: for where definitions.py documents this sentence; it is the ONE status
#: expansion the codebase performs, and this module owns it.
THIN_ALIAS = "thin"
THIN_MEANS = ("claimed", "sourced")


class KindsError(RuntimeError):
    """A resolver refused: the declaration or a binding does not support the
    question being asked. Never raised for a corpus that is merely thin."""


def _definition_bindings(name: str, area) -> dict:
    import definitions
    return definitions.load_definition(name, area=area).bindings or {}


# --------------------------------------------------------------------------- #
# The step walk and the callout reads (from analysis.py)
# --------------------------------------------------------------------------- #

def area_steps(area):
    """`(tdecl, steps)` — the step type declaration and one area's steps in
    manifest order, parsed against it (matrix_views' walk, one call)."""
    import kernel
    tdecl = kernel.load_type(STEP_TYPE)
    return tdecl, _steps(Path(area), tdecl)


def callouts(entity, prefix: str) -> list[dict]:
    """One entity's callouts of one kind, in document order."""
    return [c for c in entity.callout_dicts() if c.get("prefix") == prefix]


def callout_blob(callout: dict) -> str:
    """A callout's text and every sub-field value as one searchable string."""
    return " ".join([str(callout.get("text") or "")]
                    + [str(v) for v in (callout.get("fields") or {}).values()])


def nature(callout: dict) -> str | None:
    """The v1 `Nature:` field's value, lowercased, or None when absent.

    The field NAME is matched case-insensitively too: a drafter who wrote
    `nature:` said the same thing as one who wrote `Nature:`, and a record
    that depended on the capital would be a silent miss."""
    for key, value in (callout.get("fields") or {}).items():
        if str(key).strip().lower() == NATURE_FIELD:
            return str(value).strip().lower()
    return None


# --------------------------------------------------------------------------- #
# The gap kind and its declared vocabulary
# --------------------------------------------------------------------------- #

def gap_prefix(tdecl, area, *, _err=None) -> str:
    """The validation-gap callout kind's prefix — read from the information
    request's `step-gaps` binding, never from a typed label, so a reshape of
    the type fails the definition rather than silently changing what a gap is.

    `_err` is a private seam for the owner modules whose callers catch their
    historical error types (`analysis.AnalysisError`, `hygiene.HygieneError`);
    everyone else gets `KindsError`."""
    err = _err or KindsError
    prefixes = _prefixes(tdecl, _names(
        _binding(_definition_bindings(REQUEST_DEFINITION, area), BINDING_GAPS),
        "callouts"))
    if len(prefixes) != 1:
        raise err(
            f"{BINDING_GAPS!r} selects {len(prefixes)} callout kind(s) "
            f"({prefixes}) — the gap resolvers ask about one kind and "
            f"will not fall back on a typed label")
    return prefixes[0]


def declared_natures(tdecl, prefix: str) -> dict[str, str]:
    """The gap callout's declared `Nature:` vocabulary: {lowered -> declared}.

    Read off the `CalloutDecl.field_enums` the type declaration carries (M50
    Part A), keyed by `NATURE_FIELD` and matched case-insensitively on both
    the key and the values — no field name and no enum value is typed by a
    caller. An empty dict when the declaration carries no enum for the field,
    which makes every fragment undiscriminated rather than a refusal
    (optional metadata, never a gate)."""
    for decl in tdecl.callouts:
        if decl.prefix != prefix:
            continue
        for key, values in (getattr(decl, "field_enums", None) or {}).items():
            if str(key).strip().lower() == NATURE_FIELD:
                return {str(v).strip().lower(): str(v).strip() for v in values}
    return {}


# --------------------------------------------------------------------------- #
# The engagement root and the coverage-status selection (from plan_views)
# --------------------------------------------------------------------------- #

def engagement_root(area) -> Path:
    """The engagement root for an area.

    `engagement.py` publishes no area→root helper (its own root derivations
    are private to the intake router), so this reuses the derivation the
    DEFINITION layer already owns — `definitions._engagement_root`, "the
    parent of the `components/` directory the area lives in" (M13's layout) —
    rather than spelling the layout again. An area outside an engagement tree
    refuses by name instead of reading the filesystem root."""
    import definitions
    area = Path(area)
    root = definitions._engagement_root(area)
    if root is None:
        raise ValueError(
            f"{area}: not inside an engagement's components/ tree, so the "
            f"engagement root (the ledger and the findings register) cannot "
            f"be derived")
    return root


def selected_statuses(spec: dict) -> set[str]:
    """The coverage statuses a `coverage:` binding selects, with `thin`
    expanded.

    Every word here came out of the definition file; the expansion is the one
    documented alias (module docstring), performed here and nowhere else."""
    out: set[str] = set()
    for status in _names(spec, "coverage"):
        out.update(THIN_MEANS if status == THIN_ALIAS else [status])
    return out
