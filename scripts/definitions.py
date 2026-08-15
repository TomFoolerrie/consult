#!/usr/bin/env python3
"""
definitions.py — the M35 deliverable-definition language
(docs/v2/M35-deliverable-definitions.md).

A deliverable is DATA the user brings: one YAML file with three top-level
keys — `shape` (what the document is), `bindings` (what the brain must
supply), `skin` (how it looks). This module carries the fail-loud loader for
that language:

  stage 1  syntax      — keys, blocks, kinds, binding references, dup ids
  stage 2  vocabulary  — every type/part/callout/channel a binding names is
                         DECLARED (kernel.load_type); zero engagement needed
  stage 3  serviceability — WP-D2 (a REPORT, never an exception)
  stage 4  skin        — format is a registered renderer and skin.requires
                         is a subset of that renderer's capabilities

Layer boundaries are load-bearing: nothing in shape/bindings names a font,
nothing in skin names an entity type — which is why the unknown-key posture
below is strict rather than permissive.

Every refusal names the definition FILE and the offending key/id/value, and
a definition never half-loads (the M33 loader posture, mirrored).

Python 3, stdlib + pyyaml only (like every other engine module).
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

from dataclasses import dataclass, field
from pathlib import Path

import yaml

import kernel


class DefinitionError(Exception):
    """Raised when a deliverable definition is invalid. The message always
    names the definition file and the offending block id / binding name /
    key / value (fail-loud, same posture as kernel.TypeDeclError)."""


# --------------------------------------------------------------------------- #
# The loaded shape of a definition
# --------------------------------------------------------------------------- #

@dataclass
class Block:
    """One ordered block of a shape."""
    id: str
    title: str
    kind: str                       # entity-part | view | static
    binding: str | None = None      # the named binding this block consumes
    repeat: object | None = None    # the entity query this block repeats over
    numbering: str | None = None    # display-only numbering scheme
    text: str | None = None         # static blocks: the fixed prose
    writer: str | None = None       # view blocks: python | agent


@dataclass
class Skin:
    """The render target: format + the capabilities it is asked for."""
    format: str
    requires: list[str] = field(default_factory=list)


@dataclass
class Definition:
    """A loaded, validated deliverable definition."""
    name: str
    shape: list[Block] = field(default_factory=list)
    bindings: dict[str, dict] = field(default_factory=dict)
    skin: Skin | None = None
    path: Path | None = None


# --------------------------------------------------------------------------- #
# Vocabularies the loader admits (unknown = refused, named)
# --------------------------------------------------------------------------- #

_ALLOWED_TOP_KEYS = {"deliverable", "shape", "bindings", "skin"}
_ALLOWED_BLOCK_KEYS = {"id", "title", "kind", "binding", "repeat",
                       "numbering", "text", "writer"}
_ALLOWED_BLOCK_KINDS = {"entity-part", "view", "static"}
_ALLOWED_WRITERS = {"python", "agent"}
#: Binding verbs. DISCIPLINE (M35): every verb here has a named consumer
#: among the committed definitions — desktop-procedure (entities/parts/
#: callouts/channels/order) and its derived views (group_by). New verbs
#: arrive only when a real definition cannot be expressed.
_ALLOWED_BINDING_KEYS = {"entities", "parts", "callouts", "channels",
                         "order", "group_by"}
_ALLOWED_SKIN_KEYS = {"format", "requires"}

#: Renderer capability registry — renderers DECLARE what they can do and the
#: loader checks skins against them, so a skin asking for something the
#: renderer cannot do is a load-time error, not a rendering surprise. One
#: renderer ships in M35 (docx); the mechanism is the point, the list is
#: deliberately small and honest — each entry is something render.py
#: demonstrably does today.
RENDERERS: dict[str, dict] = {
    "docx": {
        "capabilities": [
            "toc",                  # TOC field over H1-H2 (render.py)
            "cover-page",           # cover / title page
            "document-control",     # front-matter document-control table
            "numbering-display",    # display numbers stamped at render
            "portrait-tables",
            "landscape-tables",     # --landscape section support
            "tracked-changes",      # review kits open with changes on
        ],
    },
}


# --------------------------------------------------------------------------- #
# Small helpers (message shape mirrors kernel.py: file + offending thing)
# --------------------------------------------------------------------------- #

def _require_str(fname: str, where: str, entry: dict, key: str) -> str:
    val = entry.get(key)
    if not isinstance(val, str) or not val.strip():
        raise DefinitionError(
            f'{fname}: {where} missing or invalid required key "{key}" '
            f"(got {val!r})")
    return val.strip()


# --------------------------------------------------------------------------- #
# Stage 1 — syntax
# --------------------------------------------------------------------------- #

def _stage1_syntax(path: Path, data) -> Definition:
    """Keys, blocks, kinds, binding references, duplicate ids."""
    fname = path.name

    if not isinstance(data, dict):
        raise DefinitionError(f"{fname}: definition is not a mapping")

    for key in data:
        if key not in _ALLOWED_TOP_KEYS:
            raise DefinitionError(f'{fname}: unknown top-level key "{key}"')

    name = data.get("deliverable") or path.stem
    if not isinstance(name, str) or not name.strip():
        raise DefinitionError(
            f'{fname}: "deliverable" must be a non-empty name '
            f"(got {data.get('deliverable')!r})")
    name = name.strip()

    raw_bindings = data.get("bindings")
    if raw_bindings is None:
        raw_bindings = {}
    if not isinstance(raw_bindings, dict):
        raise DefinitionError(f'{fname}: "bindings" must be a mapping')
    bindings: dict[str, dict] = {}
    for bname, spec in raw_bindings.items():
        if not isinstance(spec, dict):
            raise DefinitionError(
                f'{fname}: binding "{bname}" must be a mapping '
                f"(got {spec!r})")
        for key in spec:
            if key not in _ALLOWED_BINDING_KEYS:
                raise DefinitionError(
                    f'{fname}: binding "{bname}" unknown key "{key}"')
        bindings[str(bname)] = dict(spec)

    raw_shape = data.get("shape")
    if not isinstance(raw_shape, list) or not raw_shape:
        raise DefinitionError(f'{fname}: "shape" must be a non-empty list')

    blocks: list[Block] = []
    seen_ids: set[str] = set()
    for i, entry in enumerate(raw_shape):
        where = f"shape[{i}]"
        if not isinstance(entry, dict):
            raise DefinitionError(f"{fname}: {where} is not a mapping")
        for key in entry:
            if key not in _ALLOWED_BLOCK_KEYS:
                raise DefinitionError(f'{fname}: {where} unknown key "{key}"')
        bid = _require_str(fname, where, entry, "id")
        title = _require_str(fname, where, entry, "title")
        kind = _require_str(fname, where, entry, "kind")
        if bid in seen_ids:
            raise DefinitionError(f'{fname}: duplicate block id "{bid}"')
        seen_ids.add(bid)
        if kind not in _ALLOWED_BLOCK_KINDS:
            raise DefinitionError(
                f'{fname}: block "{bid}" unknown kind "{kind}" '
                f"(expected one of {sorted(_ALLOWED_BLOCK_KINDS)})")
        binding = entry.get("binding")
        if binding is not None:
            if not isinstance(binding, str) or not binding.strip():
                raise DefinitionError(
                    f'{fname}: block "{bid}" invalid "binding" '
                    f"(got {binding!r})")
            binding = binding.strip()
            if binding not in bindings:
                raise DefinitionError(
                    f'{fname}: block "{bid}" references undefined binding '
                    f'"{binding}"')
        elif kind == "entity-part":
            raise DefinitionError(
                f'{fname}: block "{bid}" of kind "entity-part" must name a '
                f'"binding"')
        writer = entry.get("writer")
        if writer is not None:
            if writer not in _ALLOWED_WRITERS:
                raise DefinitionError(
                    f'{fname}: block "{bid}" unknown writer "{writer}" '
                    f"(expected one of {sorted(_ALLOWED_WRITERS)})")
        elif kind == "view":
            raise DefinitionError(
                f'{fname}: view block "{bid}" must declare a "writer" '
                f"(python|agent)")
        numbering = entry.get("numbering")
        if numbering is not None and not isinstance(numbering, str):
            raise DefinitionError(
                f'{fname}: block "{bid}" invalid "numbering" '
                f"(got {numbering!r})")
        text = entry.get("text")
        if text is not None and not isinstance(text, str):
            raise DefinitionError(
                f'{fname}: block "{bid}" invalid "text" (got {text!r})')
        blocks.append(Block(id=bid, title=title, kind=kind, binding=binding,
                            repeat=entry.get("repeat"), numbering=numbering,
                            text=text, writer=writer))

    return Definition(name=name, shape=blocks, bindings=bindings, path=path)


# --------------------------------------------------------------------------- #
# Stage 2 — vocabulary (against type DECLARATIONS; zero engagement content)
# --------------------------------------------------------------------------- #

def _stage2_vocabulary(defn: Definition, path: Path) -> None:
    """Every type / part / callout kind / channel a binding names must be
    DECLARED by that binding's entity type (kernel.load_type)."""
    fname = path.name

    for bname, spec in defn.bindings.items():
        tname = spec.get("entities")
        if tname is None:
            # No entity type named: nothing declaration-checkable here. Any
            # part/callout/channel talk without a type is meaningless.
            for key in ("parts", "callouts", "channels"):
                if key in spec:
                    raise DefinitionError(
                        f'{fname}: binding "{bname}" names "{key}" without '
                        f'an "entities" type to check it against')
            continue
        if not isinstance(tname, str) or not tname.strip():
            raise DefinitionError(
                f'{fname}: binding "{bname}" invalid "entities" '
                f"(got {tname!r})")
        tname = tname.strip()
        try:
            tdecl = kernel.load_type(tname)
        except kernel.TypeDeclError as exc:
            raise DefinitionError(
                f'{fname}: binding "{bname}" names undeclared entity type '
                f'"{tname}" ({exc})') from exc

        declared_parts = {p.slug for p in tdecl.parts}
        declared_callouts = {c.label for c in tdecl.callouts}
        declared_callouts |= {c.prefix for c in tdecl.callouts}
        declared_channels = {c.name for c in tdecl.channels}

        for key, declared in (("parts", declared_parts),
                              ("callouts", declared_callouts),
                              ("channels", declared_channels)):
            if key not in spec:
                continue
            named = spec[key]
            if isinstance(named, str):
                named = [named]
            if not isinstance(named, list) or not all(
                    isinstance(n, str) for n in named):
                raise DefinitionError(
                    f'{fname}: binding "{bname}" "{key}" must be a name or a '
                    f"list of names (got {spec[key]!r})")
            for item in named:
                if item not in declared:
                    raise DefinitionError(
                        f'{fname}: binding "{bname}" names {key[:-1]} '
                        f'"{item}", which type "{tname}" does not declare '
                        f"(declared: {sorted(declared)})")


# --------------------------------------------------------------------------- #
# Stage 3 — serviceability
#
# ===================== WP-D2 OWNS THIS STAGE ============================== #
# `serviceability(defn, area)` (kernel.can_serve per binding, aggregated,
# gap strings carrying the binding name) is NOT implemented here — it is a
# REPORT, never an exception, and it needs a real engagement area. It is
# deliberately absent so the gate's WP-D2 classes fail loudly rather than
# passing on a stub. Do NOT add it to load_definition_file's stage run:
# loading must stay engagement-free.
# ========================================================================== #
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# Stage 4 — skin capability
# --------------------------------------------------------------------------- #

def _stage4_skin(defn: Definition, path: Path, raw_skin) -> Skin:
    """format must be a registered renderer; skin.requires must be a subset
    of that renderer's DECLARED capabilities."""
    fname = path.name

    if not isinstance(raw_skin, dict):
        raise DefinitionError(f'{fname}: "skin" must be a mapping '
                              f"(got {raw_skin!r})")
    for key in raw_skin:
        if key not in _ALLOWED_SKIN_KEYS:
            raise DefinitionError(f'{fname}: skin unknown key "{key}"')

    fmt = _require_str(fname, "skin", raw_skin, "format")
    if fmt not in RENDERERS:
        raise DefinitionError(
            f'{fname}: skin names unregistered renderer format "{fmt}" '
            f"(registered: {sorted(RENDERERS)})")

    requires = raw_skin.get("requires") or []
    if isinstance(requires, str):
        requires = [requires]
    if not isinstance(requires, list) or not all(
            isinstance(r, str) for r in requires):
        raise DefinitionError(
            f'{fname}: skin "requires" must be a capability name or a list '
            f"of names (got {raw_skin.get('requires')!r})")
    capabilities = set(RENDERERS[fmt].get("capabilities") or [])
    for cap in requires:
        if cap not in capabilities:
            raise DefinitionError(
                f'{fname}: skin requires capability "{cap}", which the '
                f'"{fmt}" renderer does not declare '
                f"(declared: {sorted(capabilities)})")
    return Skin(format=fmt, requires=list(requires))


# --------------------------------------------------------------------------- #
# The loader
# --------------------------------------------------------------------------- #

def load_definition_file(path) -> Definition:
    """Load + validate one definition YAML by explicit path.

    Runs stages 1 (syntax), 2 (vocabulary) and 4 (skin) IN THAT ORDER —
    syntax before vocabulary before skin, so the first refusal a user sees is
    the outermost defect. Stage 3 (serviceability) is not a load stage: it
    needs an engagement and it is a report, not an error.

    A definition never half-loads: the returned Definition is assembled only
    after every stage has passed."""
    path = Path(path)
    if not path.is_file():
        raise DefinitionError(
            f"{path.name}: definition file not found at {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise DefinitionError(f"{path.name}: not valid YAML: {exc}") from exc

    defn = _stage1_syntax(path, data)          # 1
    _stage2_vocabulary(defn, path)             # 2
    skin = _stage4_skin(defn, path, data.get("skin"))  # 4
    defn.skin = skin
    return defn


#: Repo root = parent of scripts/ — shipped definitions live in
#: kernel/deliverables/, the twin of kernel/types/.
_REPO_ROOT = Path(__file__).resolve().parent.parent
DELIVERABLES_DIR = _REPO_ROOT / "kernel" / "deliverables"


def _engagement_root(area) -> Path | None:
    """The engagement root for an area: the parent of the `components/`
    directory the area lives in (M13's layout)."""
    area = Path(area).resolve()
    for parent in area.parents:
        if parent.name == "components":
            return parent.parent
    return None


def user_definition_path(name: str, area) -> Path | None:
    """Where a user-authored definition of this name would live, or None
    when the area is not inside an engagement's components/ tree."""
    root = _engagement_root(area)
    if root is None:
        return None
    return root / "components" / "_client" / "deliverables" / f"{name}.yaml"


def load_definition(name: str, area=None) -> Definition:
    """Load the definition `name`, user file shadowing shipped file.

    Resolution (M13's per-file doctrine): when `area` is given, a
    `<engagement>/components/_client/deliverables/<name>.yaml` wins over
    `<repo>/kernel/deliverables/<name>.yaml`. `area=None` -> shipped only.
    Shipped and user definitions load through the SAME loader and the same
    refusals — no name is special-cased."""
    if area is not None:
        candidate = user_definition_path(name, area)
        if candidate is not None and candidate.is_file():
            return load_definition_file(candidate)
    shipped = DELIVERABLES_DIR / f"{name}.yaml"
    if not shipped.is_file():
        raise DefinitionError(
            f'{name}.yaml: no definition named "{name}" '
            f"(looked for a user definition under components/_client/"
            f"deliverables/ and the shipped {shipped})")
    return load_definition_file(shipped)
