#!/usr/bin/env python3
"""
render_glue.py — the bridge from a compiled Plan to a .docx.

WHY A SEPARATE MODULE: this is the docx ADAPTER seam. `render.py` owns the
mechanics of the v1 document (numbering, token resolution, callout display ids,
profile enforcement, modes, provenance) and knows nothing about the definition
language; this module owns the translation from `plan.blocks` into the ordered
section list render.py builds from. M35 (WP-D3) proved a plan EXECUTABLE;
M36 (WP-G1) makes the document ASSEMBLED FROM IT.

# FIDELITY STATEMENT (M36 WP-G1)

What this glue DOES provide — SHAPE FIDELITY. The document is assembled from
`plan.blocks`, not from the area's manifest walk:
  * BLOCK ORDER — the sections come out in the plan's block order. Reordering
    two blocks in the definition reorders them in the .docx; a block the plan
    does not carry (a view a profile pruned) does not render at all.
  * BLOCK TITLES — a static or view block's rendered `## ` heading is the
    BLOCK's `title`, not the manifest component's `heading`. (An entity-part
    block's sections are titled per ENTITY — the procedure's own heading plus
    its display number — because the block covers many of them; the block title
    is the shape's name for the group, and v1 emits no heading for it.)
  * STATIC TEXT INJECTION — a `static` block whose text the area does not carry
    as a fragment renders the block's own `text:`. When the area DOES carry the
    fragment, the fragment wins: authored engagement content is the truth about
    itself and the definition's prose is the default. (This is what lets v1's
    own definition ship a paraphrase of the shipped scaffold text without
    rewriting any engagement's Process Overview.)
  * ENTITY-PART PART SELECTION — an entity-part block renders the area's
    entities of the bound type, and the binding's `parts:` selection decides
    which parts reach the body: every part the type DECLARES but the binding
    does not select is kept out (blanked, line-count-preserving, by the same
    machinery M14's profile uses). `Block.body_omit` is honored the same way:
    the part stays bound (drafted, aggregated, register-collected) and leaves
    the body only.
  * VIEW PLACEMENT — a view block renders the area's derived fragment of that
    kind (the view block `id` IS the derived kind) at the plan's position.
  * v1's whole document apparatus, unchanged and shared: cover page + Document
    Profile card, TOC, Document Control, L2 chapter dividers, display numbering,
    callout display ids, registers, working/final modes, tracked changes,
    provenance maps. The proof is `tests/test_plan_assembly_m36.py`: the shipped
    desktop-procedure definition, resolved over the frozen p2p fixture and
    compiled, renders NORMALIZED-IDENTICAL to the committed v1 golden.

What this glue does NOT provide (recorded, not built):
  * VIEW-WRITER DISPATCH (WP-G2). Assembling derived fragments that ALREADY
    exist in the area is this module's job and is done; BUILDING a missing one
    is not. `PlanView.writer` (python|agent) is still read only for the
    executability check — no python or agent writer is invoked here, so a plan
    whose view the area has not aggregated yet renders nothing for it (with
    `require_views=False`) or is refused by name (the default).
  * `plan.name` does not select a skin: the only renderer is v1's docx path
    (`skin.format: docx`, the single registered renderer).
  * An entity-part block's `repeat:` is honored only in its shipped form
    (`{over: <type>, order: manifest}`); any other `order:` is refused by name
    rather than guessed at.
  * The M30 Shared Reference appendix and the Document Profile cover card are
    SKIN, not blocks: they are emitted by render.py wherever a plan render
    carries a cover / the engagement carries citable registers, and no block
    names them. (A definition therefore cannot yet move or suppress them.)
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import json
import re

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
    whether an unserved view is fatal; `render_plan` treats it as fatal by
    default (`require_views=False` downgrades it to render-nothing)."""
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


# --------------------------------------------------------------------------- #
# The shape adapter: plan.blocks -> render.py's ordered section list
# --------------------------------------------------------------------------- #

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_FILE_PREFIX_RE = re.compile(r"^\d+[_-]")

#: A section dict render.py's `_attr` accessors read. Built for a static block
#: the area carries no fragment for (definition-supplied prose), and as the
#: retitled copy of a matched section.
_SECTION_KEYS = ("heading", "role", "body", "slug", "number", "derived_kind",
                 "writer", "file")


def _slugify(text) -> str:
    return _SLUG_RE.sub("-", (text or "").strip().lower()).strip("-")


def _as_dict(section) -> dict:
    from render import _attr
    return {k: _attr(section, k) for k in _SECTION_KEYS}


class PlanShape:
    """The ordered section list a compiled Plan asks for, over one area.

    Handed to `render.render_folder(..., shape=...)`, which calls `arrange`
    once. Read-only over the area (it only inspects the sections render.py
    already assembled, plus the entity type DECLARATION for part slugs)."""

    def __init__(self, plan, area, *, require_views: bool = True,
                 bindings: dict | None = None):
        self.plan = plan
        self.area = Path(area)
        self.require_views = require_views
        #: The definition's binding map. Bindings are not carried on the Plan
        #: (M35's Plan is views + blocks), so the caller supplies them. None ->
        #: no part selection is applied and `body_omit` alone shapes the body.
        self.plan_bindings = bindings

    # -- part selection ---------------------------------------------------- #
    def _hidden_parts(self, block) -> frozenset:
        """The part slugs this entity-part block keeps OUT of the body: every
        part its type declares that the binding does not select, plus the
        block's `body_omit`. Empty when the binding selects everything."""
        import kernel

        spec = (self.plan_bindings or {}).get(block.binding) or {}
        tname = spec.get("entities")
        selected = spec.get("parts")
        if isinstance(selected, str):
            selected = [selected]
        hidden = set(block.body_omit or ())
        if selected and isinstance(tname, str):
            try:
                declared = {p.slug for p in kernel.load_type(tname).parts}
            except kernel.TypeDeclError as exc:      # pragma: no cover
                raise RenderGlueError(
                    f'plan "{self.plan.name}" block "{block.id}" binds '
                    f'undeclared entity type "{tname}" ({exc})') from exc
            hidden |= declared - set(selected)
        return frozenset(hidden)

    # -- the arrangement --------------------------------------------------- #
    def arrange(self, sections) -> list[tuple[object, tuple]]:
        from render import _attr, _PROFILE_HEADINGS

        by_derived: dict[str, list] = {}
        statics: dict[str, list] = {}
        procedures: list = []
        cover: list = []
        for s in sections:
            heading = (_attr(s, "heading") or "").strip()
            if heading.lower() in _PROFILE_HEADINGS:
                # SKIN, not a block: render.py lifts it onto the cover card
                # (or, with --no-cover, renders it where it sits).
                cover.append(s)
                continue
            role = _attr(s, "role")
            kind = _attr(s, "derived_kind")
            if kind:
                by_derived.setdefault(kind, []).append(s)
            elif role == "procedure":
                procedures.append(s)
            else:
                stem = _FILE_PREFIX_RE.sub("", Path(_attr(s, "file") or "").stem)
                for key in {_slugify(heading), _slugify(stem)}:
                    if key:
                        statics.setdefault(key, []).append(s)

        out: list[tuple[object, tuple]] = [(s, ()) for s in cover]
        for block in self.plan.blocks:
            if block.kind == "view":
                for s in by_derived.get(block.id, []):
                    out.append((self._titled(s, block.title), ()))
                if block.id not in by_derived and self.require_views:
                    raise RenderGlueError(
                        f'plan "{self.plan.name}" view block "{block.id}" has '
                        f"no derived component in {self.area.name}'s manifest")
            elif block.kind == "static":
                found = (statics.get(_slugify(block.id))
                         or statics.get(_slugify(block.title)))
                if found:
                    for s in found:
                        out.append((self._titled(s, block.title), ()))
                elif block.text:
                    out.append((self._injected(block), ()))
            elif block.kind == "entity-part":
                self._check_repeat(block)
                hidden = self._hidden_parts(block)
                for s in procedures:
                    out.append((s, tuple(sorted(hidden))))
            else:                                    # pragma: no cover
                raise RenderGlueError(
                    f'plan "{self.plan.name}" block "{block.id}" has '
                    f'unrenderable kind "{block.kind}"')
        return out

    def _check_repeat(self, block) -> None:
        rep = block.repeat
        order = rep.get("order") if isinstance(rep, dict) else None
        if order not in (None, "manifest"):
            raise RenderGlueError(
                f'plan "{self.plan.name}" block "{block.id}" asks for entity '
                f'order "{order}"; the docx adapter only serves "manifest"')

    def _titled(self, section, title: str):
        """The section with the BLOCK's title as its heading (the definition is
        the naming authority for its own blocks)."""
        if (_as_dict(section)["heading"] or "").strip() == (title or "").strip():
            return section                    # nothing to override
        data = _as_dict(section)
        data["heading"] = title
        return data

    def _injected(self, block) -> dict:
        """A static block the area carries no fragment for: the definition's
        own prose becomes the section body."""
        return {"heading": block.title, "role": "static", "body": block.text,
                "slug": None, "number": None, "derived_kind": None,
                "writer": None, "file": None}


def render_plan(plan, area, out_path, *, mode: str = "working",
                landscape: bool = False, do_cover: bool = True,
                track_changes: bool = False,
                emit_signal: bool = False,
                bindings: dict | None = None,
                require_views: bool = True) -> dict:
    """Assemble a compiled Plan over `area` into `out_path`. Returns render.py's
    stats dict.

    The plan is checked first (`check_plan`) so an unexecutable plan refuses by
    name instead of quietly rendering v1's document anyway; then the document is
    built FROM `plan.blocks` through render.py's `shape` seam — see the fidelity
    statement at the top of this module for exactly what that honors.

    `bindings` is the definition's binding map (`Definition.bindings`); pass it
    to have entity-part `parts:` selections honored (without it only
    `Block.body_omit` shapes the body — a Plan does not carry its bindings).

    `require_views` False downgrades "the area has no derived component for this
    view block" from a refusal to render-nothing — the semantics a plan block
    whose fragment has not been aggregated yet needs.

    `emit_signal` defaults to False here (a plan render is not v1's pipeline
    step, so it must not drop v1's signal file into the area unless asked)."""
    area = Path(area)
    out_path = Path(out_path)
    reasons = check_plan(plan, area)
    if reasons and require_views:
        raise RenderGlueError("; ".join(reasons))
    if not plan.blocks:
        raise RenderGlueError(f'plan "{plan.name}" has no blocks to render')

    import render                  # local: keeps this module cheap to import

    shape = PlanShape(plan, area, require_views=require_views,
                      bindings=bindings)
    return render.render_folder(
        area, out_path, landscape=landscape, do_cover=do_cover, mode=mode,
        slugs=None, track_changes=track_changes, emit_signal=emit_signal,
        shape=shape)
