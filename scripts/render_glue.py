#!/usr/bin/env python3
"""
render_glue.py — the M35 (WP-D3) bridge from a compiled Plan to a .docx.

WHY A SEPARATE MODULE: `render.py` and `aggregate.py` are v1's byte-identical
pipeline and M35 is additive-only, so nothing here edits them. This module is
the whole seam: it takes a `definitions.Plan`, checks it is executable against
a real area, and drives the EXISTING public entry point
(`render.render_folder`) over that area.

# FIDELITY STATEMENT (read this before starting M36)

What this glue DOES provide:
  * proof that a compiled Plan is EXECUTABLE — the plan is checked against the
    area (a plan with no blocks, or a view whose derived kind the area's
    manifest does not carry, is refused by name) and then rendered;
  * a real .docx on disk at `out_path`, produced by v1's renderer, with v1's
    fidelity: cover page, TOC, document control, display numbering, registers,
    profile enforcement, working/final modes, tracked changes;
  * the plan's own `mode` / cover / landscape / tracked-changes knobs passed
    straight through to `render_folder`.

What this glue does NOT provide (M36's build):
  * SHAPE FIDELITY. The output document's block order, block set and titles
    come from the AREA's manifest (v1's `doc_model.assemble`), NOT from
    `plan.blocks`. A toy three-block plan rendered over the p2p fixture still
    yields the fixture's full v1 document. Nothing is dropped, reordered or
    retitled to match the plan.
  * `static` block text is not injected; a plan's static prose does not appear
    in the output unless the area already carries that fragment.
  * `entity-part` bindings do not filter what is rendered: `parts` selections
    and `Block.body_omit` flags are ignored here — the profile that render.py
    itself resolves is what shapes sections, exactly as in v1.
  * `view` blocks are not DISPATCHED. Derived views are rendered from the
    aggregated fragments already in the area; this glue never invokes a python
    or agent writer, so `PlanView.writer` is read only for the executability
    check below.
  * `plan.name` does not select a skin: the only renderer is v1's docx path.

So: M36 starts from "the plan compiles and a docx lands" and owes the
document-shaped half — assembling the .docx FROM `plan.blocks` (dispatching
view writers, honoring part selections and body_omit) rather than from the
manifest.
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import json

from pathlib import Path


class RenderGlueError(Exception):
    """A plan that cannot be executed over this area. Fail-loud and NAMED
    (same posture as DefinitionError): the offending plan/block/view is in the
    message, because "rendered the wrong document" is the failure this guards."""


def _manifest_derived_kinds(area: Path) -> set[str]:
    try:
        manifest = json.loads(
            (area / "manifest.json").read_text(encoding="utf-8"))
    except OSError as exc:
        raise RenderGlueError(
            f"{area.name}: no readable manifest.json to render a plan over "
            f"({exc})") from exc
    except ValueError as exc:
        raise RenderGlueError(
            f"{area.name}: manifest.json is not valid JSON ({exc})") from exc
    return {c.get("derived_kind") for c in (manifest.get("components") or [])
            if isinstance(c, dict) and c.get("derived_kind")}


def check_plan(plan, area) -> list[str]:
    """Is this plan executable over this area? Returns a list of reasons,
    [] when it is. A REPORT (serviceability's posture), so a caller can decide
    whether an unserved view is fatal; `render_plan` treats it as fatal."""
    area = Path(area)
    reasons: list[str] = []
    if not plan.blocks:
        reasons.append(f'plan "{plan.name}" has no blocks to render')
    if not (area / "manifest.json").is_file():
        reasons.append(f"area {area.name} has no manifest.json")
        return reasons
    have = _manifest_derived_kinds(area)
    for view in plan.views:
        if view.kind not in have:
            reasons.append(
                f'plan "{plan.name}" view "{view.kind}" ({view.writer}) has no '
                f"component in {area.name}'s manifest")
    return reasons


def render_plan(plan, area, out_path, *, mode: str = "working",
                landscape: bool = False, do_cover: bool = True,
                track_changes: bool = False,
                emit_signal: bool = False) -> dict:
    """Render a compiled Plan over `area` to `out_path`. Returns render.py's
    stats dict.

    The plan is checked first (`check_plan`) so an unexecutable plan refuses by
    name instead of quietly rendering v1's document anyway. Then v1's public
    entry point does the work — see the fidelity statement at the top of this
    module for exactly which half of the plan is honored.

    `emit_signal` defaults to False here (a plan render is not v1's pipeline
    step, so it must not drop v1's signal file into the area unless asked)."""
    area = Path(area)
    out_path = Path(out_path)
    reasons = check_plan(plan, area)
    if reasons:
        raise RenderGlueError("; ".join(reasons))

    import render                  # local: keeps this module cheap to import

    return render.render_folder(
        area, out_path, landscape=landscape, do_cover=do_cover, mode=mode,
        slugs=None, track_changes=track_changes, emit_signal=emit_signal)
