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

import json

from dataclasses import dataclass, field, replace
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
    #: WP-D3 profile shading: parts this block still BINDS (they are drafted,
    #: aggregated and register-collected) but which the M14 profile keeps out
    #: of the rendered body (`body_omit`). Empty on every unshaded block.
    body_omit: list[str] = field(default_factory=list)


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
    #: WP-D3: the M14 document-profile provenance line for the area this
    #: definition was resolved for (`client_config.Profile.report_line()`).
    #: None when the definition was loaded without an area (no profile in
    #: play); the unconfigured line ("… none (full A–G, nothing omitted)")
    #: when an area has no `profile:` key anywhere.
    provenance: str | None = None


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
# Stage 3 — serviceability (a REPORT, never an exception)
#
# NOT part of load_definition_file's stage run: loading stays engagement-free,
# and "not yet" is an answer, not a refusal.
# --------------------------------------------------------------------------- #

#: The keys kernel.can_serve understands. A binding may carry compile-time
#: verbs too (order, group_by) — those are WP-D2/D3 concerns and would trip
#: can_serve's own unknown-key check, so they are DROPPED before the call.
_CAN_SERVE_KEYS = ("entities", "parts", "callouts", "channels")

#: The manifest component `role` that holds each entity type's entities in an
#: engagement area. v1's areas carry exactly one entity population — the
#: hand-authored procedures — and those ARE the `activity` entities (the M33
#: compatibility type). Any other declared type has zero entities in a v1-
#: shaped area until an area learns to hold them.
_TYPE_MANIFEST_ROLE = {"activity": "procedure"}


def _area_entity_count(area: Path, type_name: str) -> int:
    """How many entities of `type_name` this area actually holds.

    WHY THIS LIVES HERE AND NOT IN kernel.can_serve: can_serve (M33, closed)
    is pure over DECLARATIONS plus channel-registry files on disk — it never
    counts entities, so a type that declares fine but has no instances in the
    area reads as "serviceable" to it. That is the engagement half of
    serviceability, and M35 owns it. Read-only: the manifest only."""
    try:
        manifest = json.loads(
            (area / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # Loader-grade problem: propagate naturally rather than mis-report it
        # as an unserved binding.
        raise
    role = _TYPE_MANIFEST_ROLE.get(type_name)
    if role is None:
        return 0
    components = manifest.get("components") or []
    return sum(1 for c in components
               if isinstance(c, dict) and c.get("role") == role)


def serviceability(defn: Definition, area) -> list[str]:
    """Can this engagement area serve every binding of this definition?

    Returns a list of gap strings — [] means fully served. NEVER raises for an
    unserved binding: "not yet" is a report. Each gap names the BINDING, so a
    definition with several bindings stays diagnosable.

    Two halves, deliberately:
      * declaration half — kernel.can_serve over the binding's admitted keys
        (types/parts/callouts declared, channel registries present on disk);
      * engagement half — the area must actually HOLD entities of the bound
        type (see _area_entity_count for why can_serve cannot answer this)."""
    area = Path(area)
    gaps: list[str] = []

    for bname, spec in defn.bindings.items():
        requirements = {k: spec[k] for k in _CAN_SERVE_KEYS if k in spec}
        for err in kernel.can_serve(requirements, area):
            gaps.append(f'binding "{bname}": {err}')

        tname = requirements.get("entities")
        if isinstance(tname, str) and tname.strip():
            tname = tname.strip()
            if _area_entity_count(area, tname) == 0:
                gaps.append(
                    f'binding "{bname}": area {area.name} holds no entities '
                    f'of type "{tname}"')

    return gaps


# --------------------------------------------------------------------------- #
# Compile — definition + area -> Plan (deterministic, READ-ONLY)
# --------------------------------------------------------------------------- #

@dataclass
class PlanView:
    """One derived view the plan will build. `kind` is the view block's id
    (D1's convention: the id IS the derived kind); `writer` is python|agent."""
    kind: str
    writer: str


@dataclass
class Plan:
    """A compiled deliverable: the ordered views the brain must build, plus
    the full ordered block shape (D3/M36 assemble from this)."""
    name: str
    views: list[PlanView] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)


def compile_plan(defn: Definition, area) -> Plan:
    """Compile a loaded definition against an area into a Plan.

    Deterministic and READ-ONLY: it walks defn.shape in declaration order and
    touches nothing on disk — no writes, no cache files. `area` is taken for
    the signature the pipeline needs (and so future compile steps can resolve
    area-relative selections) without being read here.

    View blocks become PlanViews in shape order; entity-part and static blocks
    carry through as plan blocks. `.blocks` is the full ordered shape."""
    plan = Plan(name=defn.name)
    for block in defn.shape:
        plan.blocks.append(block)
        if block.kind == "view":
            plan.views.append(PlanView(kind=block.id, writer=block.writer))
    return plan


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


# --------------------------------------------------------------------------- #
# WP-D3 — the M14 PROFILE ALIAS
#
# An engagement that never wrote a deliverable definition is not
# undefined: it has an M14 document profile, and a profile is exactly a set
# of SUBTRACTIONS from v1's document. So `resolve_definition(area)` routes:
#
#   * the area's engagement carries `_client/deliverables/` with files ->
#     the ORDINARY load path (user file shadows shipped; this function is
#     just routing, no shading — a hand-written definition is the whole
#     truth about its own shape);
#   * otherwise -> the shipped desktop-procedure definition with the area's
#     profile applied as subtractions.
#
# Subtractions, all three of them (nothing is ever ADDED — a profile cannot
# invent a block, so a `derived:` entry with no block in the shipped shape,
# e.g. `appendix-controls`, is a no-op here):
#
#   1. dropped sections  — a section absent from `sections:` does not exist
#      at all, so its part slug is removed from every binding's `parts:`
#      (sections and the `activity` type's part slugs are the same seven
#      names, one-to-one). A binding left with no parts at all loses its
#      `parts:` key rather than carrying an empty selection.
#   2. `body_omit`       — the section EXISTS (it is drafted, aggregated and
#      caught by its register) but is not rendered in the procedure body.
#      That is a render fact, not a subtraction from the binding, so it is
#      recorded on the affected block as `Block.body_omit` and its part stays
#      in the binding.
#   3. pruned derived    — a view block whose id is not in `derived:` leaves
#      the shape. Bindings orphaned by that pruning are dropped too, so
#      serviceability does not report gaps for work the profile cancelled.
#
# The shaded definition is RE-VALIDATED through stages 1, 2 and 4 before it
# is returned: shading is a transformation of the language, so its output has
# to be a legal definition by the same loader that admits hand-written ones.
# --------------------------------------------------------------------------- #

#: The shipped definition the profile alias shades. v1's document.
DEFAULT_DEFINITION = "desktop-procedure"


def _definition_to_raw(defn: Definition) -> dict:
    """Serialize a Definition back into the raw mapping the loader admits.

    Used only by the profile alias, so that a shaded definition is proven
    legal by the SAME stages a hand-written file passes (never a private
    "trust me" path). `body_omit` is deliberately NOT serialized: it is
    render-side bookkeeping, not language syntax, and stage 1 would refuse
    the unknown block key."""
    shape = []
    for b in defn.shape:
        entry: dict = {"id": b.id, "title": b.title, "kind": b.kind}
        for key, val in (("binding", b.binding), ("repeat", b.repeat),
                         ("numbering", b.numbering), ("text", b.text),
                         ("writer", b.writer)):
            if val is not None:
                entry[key] = val
        shape.append(entry)
    raw = {"deliverable": defn.name, "shape": shape,
           "bindings": {k: dict(v) for k, v in defn.bindings.items()}}
    if defn.skin is not None:
        raw["skin"] = {"format": defn.skin.format,
                       "requires": list(defn.skin.requires)}
    return raw


def _revalidate(defn: Definition, path: Path) -> Definition:
    """Run stages 1, 2 and 4 over a shaded definition and return the result.

    `Block.body_omit` cannot survive the round trip (it is not language), so
    it is carried across by block id afterwards."""
    raw = _definition_to_raw(defn)
    fresh = _stage1_syntax(path, raw)
    _stage2_vocabulary(fresh, path)
    fresh.skin = _stage4_skin(fresh, path, raw.get("skin"))
    fresh.path = defn.path
    omits = {b.id: list(b.body_omit) for b in defn.shape if b.body_omit}
    for block in fresh.shape:
        block.body_omit = omits.get(block.id, [])
    return fresh


def _shade_with_profile(defn: Definition, prof) -> Definition:
    """Apply one resolved M14 Profile to a definition as SUBTRACTIONS."""
    dropped = prof.dropped_sections()
    omitted = set(prof.body_omit)

    bindings: dict[str, dict] = {}
    for bname, spec in defn.bindings.items():
        spec = dict(spec)
        parts = spec.get("parts")
        if parts is not None:
            if isinstance(parts, str):
                parts = [parts]
            kept = [p for p in parts if p not in dropped]
            if kept:
                spec["parts"] = kept
            else:
                spec.pop("parts", None)
        bindings[bname] = spec

    shape: list[Block] = []
    for block in defn.shape:
        if block.kind == "view" and not prof.wants(block.id):
            continue                      # (3) the profile cancelled this view
        block = replace(block)            # never mutate the loaded definition
        spec = bindings.get(block.binding) if block.binding else None
        parts = spec.get("parts") if isinstance(spec, dict) else None
        if isinstance(parts, str):
            parts = [parts]
        if parts:
            block.body_omit = [p for p in parts if p in omitted]  # (2)
        shape.append(block)

    referenced = {b.binding for b in shape if b.binding}
    bindings = {k: v for k, v in bindings.items() if k in referenced}

    return Definition(name=defn.name, shape=shape, bindings=bindings,
                      skin=defn.skin, path=defn.path)


def _has_user_deliverables(area) -> bool:
    """Does this area's engagement carry a non-empty `_client/deliverables/`?"""
    root = _engagement_root(area)
    if root is None:
        return False
    ddir = root / "components" / "_client" / "deliverables"
    return ddir.is_dir() and any(p.is_file() for p in ddir.iterdir())


def resolve_definition(area, name: str = DEFAULT_DEFINITION) -> Definition:
    """The definition to build for `area` — the M14 profile alias (WP-D3).

    Routing (see the block comment above): an engagement that authored
    definitions gets the ordinary shadowing load path; an engagement that did
    not gets the shipped desktop-procedure definition shaded by its M14
    profile. An UNCONFIGURED profile (no `profile:` key in any layer) leaves
    the shipped definition unchanged — the M14 "absent profile = today"
    posture, mirrored here.

    The profile is read through `client_config.profile(area)` — the one
    accessor; this module never parses profile YAML. Its provenance line
    (`Profile.report_line()`) is surfaced on the returned
    `Definition.provenance` so a caller can print WHICH layer shaped the
    document, exactly as scaffold and render do."""
    import client_config          # local: keeps definitions importable alone

    area = Path(area)
    prof = client_config.profile(area)
    line = prof.report_line()

    if _has_user_deliverables(area):
        defn = load_definition(name, area=area)
        defn.provenance = line
        return defn

    defn = load_definition(name)
    if prof.configured:
        defn = _revalidate(_shade_with_profile(defn, prof),
                           defn.path or Path(f"{name}.yaml"))
    defn.provenance = line
    return defn


def render_plan(plan: Plan, area, out_path, **kwargs) -> dict:
    """Render a compiled Plan to a .docx. See scripts/render_glue.py for the
    fidelity statement — this is a convenience delegate so callers that
    already hold `definitions` do not need a second import."""
    import render_glue
    return render_glue.render_plan(plan, area, out_path, **kwargs)
