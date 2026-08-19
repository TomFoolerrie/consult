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
                         "order", "group_by",
                         # M37: the DERIVED selection verb, and its domain key.
                         # Consumer: kernel/deliverables/information-request.yaml
                         # (the client information-request list), which selects
                         # taxonomy nodes by their coverage status —
                         # `{coverage: [thin, claimed, conflicted], of:
                         # taxonomy}`. `coverage` binds the output of
                         # coverage_map.coverage(), a PURE FUNCTION over the
                         # engagement (never a file — the charter's hard
                         # guardrail), so unlike every verb above it names no
                         # entity type and there is nothing on disk for stage 3
                         # to look for. `of` is its companion: what is being
                         # covered.
                         "coverage", "of",
                         # M38: the COUNT verb of the join/group/count family
                         # M35 reserved headroom for.
                         # Consumer: kernel/deliverables/process-controls-matrix
                         # .yaml, binding `open-items` — the matrix's last
                         # column reaches the reader as "how many open items
                         # does this step carry" (with their ids), not as one
                         # row per callout. `count: true` says exactly that:
                         # this selection is consumed AS A COUNT. It is a
                         # presentation-independent fact about the QUERY (a
                         # register and a matrix cell over the same callouts
                         # differ in nothing else), which is why it belongs in
                         # bindings rather than in skin. Boolean-only —
                         # see _check_count_shape.
                         "count",
                         # M39: the FINDINGS verb — the analysis layer's
                         # population, admitted exactly like `coverage` was.
                         # Consumer: kernel/deliverables/findings-report.yaml,
                         # binding `accepted-findings` — `{findings: accepted,
                         # group_by: theme}`. Like `coverage` it names no entity
                         # type: a finding is not an entity in an area's corpus,
                         # it is an entry in the engagement findings register
                         # (scripts/findings.py), reached through
                         # `findings.renderable()` — so there is nothing for the
                         # declaration half of stage 2 to check, and its
                         # value-shape check (below) is the whole of stage 2 for
                         # it. Status-valued rather than boolean because the
                         # lifecycle IS the point: `accepted` is the only status
                         # a rendered deliverable may bind, and saying so in the
                         # definition keeps that visible to a reader of the YAML
                         # instead of hiding it inside the feeder.
                         "findings"}

#: The coverage statuses a `coverage:` binding may name. Four come straight from
#: coverage_map.coverage()'s contract; `thin` is the SURVEYOR's sufficiency word
#: for "known but not yet evidenced" (claimed-or-sourced), which is the altitude
#: a client-facing request list actually asks at. Kept here rather than imported
#: from coverage_map because stage 2 must stay loadable with zero engagement and
#: zero coverage machinery — this is a VALUE-SHAPE check, not a computation.
_ALLOWED_COVERAGE_STATUSES = {"conflicted", "evidenced", "sourced", "claimed",
                              "thin"}

#: The domains a `coverage:` binding may be `of`. One today (the taxonomy nodes
#: of M37 Part A); the key exists so a second domain arrives as a new value
#: rather than as a reinterpretation of an implicit one.
_ALLOWED_COVERAGE_DOMAINS = {"taxonomy"}

#: The finding statuses a `findings:` binding may name (M39). Kept here rather
#: than imported from findings.py for the same reason the coverage statuses are:
#: stage 2 must stay loadable with zero engagement and zero analysis machinery —
#: this is a VALUE-SHAPE check, not a computation. Parity with
#: findings.STATUSES is test-enforceable and the vocabulary is closed.
_ALLOWED_FINDING_STATUSES = {"proposed", "accepted", "rejected"}

#: The one status a RENDERED deliverable may bind (M39: `findings.renderable()`
#: is accepted-only). A definition naming any other status is refused rather
#: than silently narrowed — a report that thinks it renders proposals is a
#: definition defect, not a presentation choice.
_RENDERABLE_FINDING_STATUS = "accepted"
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

def _check_coverage_shape(fname: str, bname: str, spec: dict) -> None:
    """Stage-2's check for a `coverage:` binding (M37).

    WHAT STAGE 2 CAN CHECK HERE, DECIDED AND WRITTEN DOWN: a coverage binding
    names no entity type, so there is no declaration to check its selection
    against — the type/part/callout half of stage 2 has nothing to say about it.
    What remains, and what is therefore enforced, is the VALUE SHAPE: the verb
    takes a status name or list of names drawn from a closed vocabulary, it
    requires its `of` domain (also closed), and it may not be mixed with an
    entity selection in the same binding (an entity population and a derived
    selection are two different queries; one binding, one query). That is the
    whole of stage 2 for coverage — deliberately, not by omission."""
    has_cov = "coverage" in spec
    if "of" in spec and not has_cov:
        raise DefinitionError(
            f'{fname}: binding "{bname}" names "of" without "coverage" '
            f"(the domain key belongs to the coverage verb)")
    if not has_cov:
        return

    if "entities" in spec:
        raise DefinitionError(
            f'{fname}: binding "{bname}" names both "coverage" and "entities" '
            f"— a derived coverage selection and an entity population are two "
            f"different queries; use two bindings")

    named = spec["coverage"]
    if isinstance(named, str):
        named = [named]
    if not isinstance(named, list) or not named or not all(
            isinstance(n, str) for n in named):
        raise DefinitionError(
            f'{fname}: binding "{bname}" "coverage" must be a status name or a '
            f"non-empty list of names (got {spec['coverage']!r})")
    for status in named:
        if status not in _ALLOWED_COVERAGE_STATUSES:
            raise DefinitionError(
                f'{fname}: binding "{bname}" names unknown coverage status '
                f'"{status}" '
                f"(known: {sorted(_ALLOWED_COVERAGE_STATUSES)})")

    domain = spec.get("of")
    if not isinstance(domain, str) or domain.strip() not in \
            _ALLOWED_COVERAGE_DOMAINS:
        raise DefinitionError(
            f'{fname}: binding "{bname}" coverage needs an "of" domain '
            f"(known: {sorted(_ALLOWED_COVERAGE_DOMAINS)}; got {domain!r})")


def _check_count_shape(fname: str, bname: str, spec: dict) -> None:
    """Stage-2's check for the M38 `count:` verb.

    All stage 2 can say about it is its VALUE SHAPE (a boolean) and that it
    counts SOMETHING: a count with no selection to count is meaningless, so the
    binding must also carry an entity population. The selection itself
    (`callouts:`/`parts:`) is checked against the declaration by the walk
    below, exactly as it would be without the count."""
    if "count" not in spec:
        return
    if not isinstance(spec["count"], bool):
        raise DefinitionError(
            f'{fname}: binding "{bname}" "count" must be true or false '
            f"(got {spec['count']!r})")
    if "entities" not in spec:
        raise DefinitionError(
            f'{fname}: binding "{bname}" names "count" without an "entities" '
            f"selection to count")


def _check_findings_shape(fname: str, bname: str, spec: dict) -> None:
    """Stage-2's check for a `findings:` binding (M39).

    Same situation as `coverage`: no entity type, so the declaration half of
    stage 2 is vacuous and what remains is the VALUE SHAPE — a single status
    name from a closed vocabulary, which must be the renderable one, and no
    entity population in the same binding (a register selection and an entity
    population are two different queries; one binding, one query). The
    accepted-only rule is enforced HERE, at load, so a definition can never
    quietly ask a renderer for unconfirmed analysis."""
    if "findings" not in spec:
        return
    if "entities" in spec:
        raise DefinitionError(
            f'{fname}: binding "{bname}" names both "findings" and "entities" '
            f"— a findings-register selection and an entity population are two "
            f"different queries; use two bindings")
    status = spec["findings"]
    if not isinstance(status, str) or status.strip() not in \
            _ALLOWED_FINDING_STATUSES:
        raise DefinitionError(
            f'{fname}: binding "{bname}" "findings" must be one status name '
            f"(known: {sorted(_ALLOWED_FINDING_STATUSES)}; got {status!r})")
    if status.strip() != _RENDERABLE_FINDING_STATUS:
        raise DefinitionError(
            f'{fname}: binding "{bname}" binds "{status.strip()}" findings — '
            f'only "{_RENDERABLE_FINDING_STATUS}" findings may reach a '
            f"rendered deliverable (M39: the human gate)")


def _stage2_vocabulary(defn: Definition, path: Path) -> None:
    """Every type / part / callout kind / channel a binding names must be
    DECLARED by that binding's entity type (kernel.load_type)."""
    fname = path.name

    for bname, spec in defn.bindings.items():
        _check_coverage_shape(fname, bname, spec)      # M37, see below
        _check_count_shape(fname, bname, spec)         # M38, see above
        _check_findings_shape(fname, bname, spec)      # M39, see above

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
# and "not yet" is an answer, not a refusal. Two surfaces since M51:
# `serviceability_records` (one record per gap, binding attribution as data —
# what needs.py consumes) and `serviceability` (the flat sentences brief.py
# renders, derived from the records so the two can never disagree).
# --------------------------------------------------------------------------- #

#: The keys kernel.can_serve understands. A binding may carry compile-time
#: verbs too (order, group_by) — those are WP-D2/D3 concerns and would trip
#: can_serve's own unknown-key check, so they are DROPPED before the call.
_CAN_SERVE_KEYS = ("entities", "parts", "callouts", "channels")

#: Where an area keeps its taxonomy-node fragments. Coverage's engagement-side
#: precondition is exactly "this area has nodes to cover" — the directory name is
#: coverage_map's convention, mirrored here rather than imported so that
#: serviceability stays a cheap directory question with no coverage machinery
#: loaded (it must answer for a v1 area that has none). Also the entity home for
#: the directory-resident lookup below.
_TAXONOMY_DIRNAME = "_taxonomy"

#: The engagement findings register's home (scripts/findings.py's convention,
#: mirrored — see _findings_gaps for why it is not imported). At the engagement
#: ROOT, deliberately outside components/: M39's one-direction rule forbids an
#: analysis verb to write anywhere in the capture layer, which is why findings
#: cannot live in M30's `components/_client/registers/` home.
_FINDINGS_DIRNAME = "_registers"
_FINDINGS_FILENAME = "findings.yaml"

#: The manifest component `role` that holds each entity type's entities in an
#: engagement area. v1's areas carry exactly one entity population — the
#: hand-authored procedures — and those ARE the `activity` entities (the M33
#: compatibility type). Any other declared type has zero entities in a v1-
#: shaped area until an area learns to hold them.
_TYPE_MANIFEST_ROLE = {"activity": "procedure"}

#: Types whose entities are DIRECTORY-RESIDENT: one hand-authored fragment per
#: entity in a named subfolder, with no manifest component at all. The manifest
#: role table above cannot express these — the manifest is membership/ordering
#: authority for PROCEDURES, and `taxonomy-node` entities live in
#: `<area>/_taxonomy/` (M37 Part A) — so widening it entry-wise for them would
#: state something untrue. This is the honest second lookup path instead, kept
#: deliberately narrow: one type, one directory, `*.md` fragments, same
#: convention `_coverage_gaps` reads below. A type that is neither manifest-roled
#: nor listed here still counts zero, which remains the truthful answer for a
#: v1-shaped area (`process-step`, for instance, has no population of its own in
#: an area whose entities are the v1 procedures — that binding reporting "not
#: yet" is the report working, not a mapping gap to paper over).
_TYPE_ENTITY_DIRNAME = {"taxonomy-node": _TAXONOMY_DIRNAME}


def _area_entity_count(area: Path, type_name: str) -> int:
    """How many entities of `type_name` this area actually holds.

    WHY THIS LIVES HERE AND NOT IN kernel.can_serve: can_serve (M33, closed)
    is pure over DECLARATIONS plus channel-registry files on disk — it never
    counts entities, so a type that declares fine but has no instances in the
    area reads as "serviceable" to it. That is the engagement half of
    serviceability, and M35 owns it. Read-only: the manifest, or — for a
    directory-resident type — one directory listing."""
    dirname = _TYPE_ENTITY_DIRNAME.get(type_name)
    if dirname is not None:
        # Checked BEFORE the manifest read on purpose: these entities are not
        # manifest members, so an area without a manifest.json (or with an
        # unreadable one) must still be able to report its node count.
        d = Path(area) / dirname
        return len(sorted(d.glob("*.md"))) if d.is_dir() else 0
    try:
        manifest = json.loads(
            (area / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        # Loader-grade problem: propagate naturally rather than mis-report it
        # as an unserved binding.
        raise
    components = [c for c in (manifest.get("components") or [])
                  if isinstance(c, dict)]
    role = _TYPE_MANIFEST_ROLE.get(type_name)
    if role is not None:
        return sum(1 for c in components if c.get("role") == role)
    return _typed_fragment_count(area, type_name, components)


#: The manifest role whose fragments are an area's hand-authored entity
#: population, whatever type they are of. v1's areas hold `activity` entities
#: there; a v2-native area holds `process-step` entities in the same place (the
#: manifest is membership/ordering authority for both — see M33's compatibility
#: ruling), which is why the count below asks the FRAGMENTS what they are
#: instead of widening the role table with a second entry that would make the
#: two types indistinguishable.
_ENTITY_ROLE = "procedure"


def _typed_fragment_count(area: Path, type_name: str, components: list) -> int:
    """How many of the area's entity fragments are of `type_name`, by SHAPE.

    THE QUESTION THIS ANSWERS, AND WHY IT IS ASKED THIS WAY (M38): the role
    table above maps a type to the manifest role that holds it, and `activity`
    and `process-step` share that role — so a role lookup alone would count v1's
    activity-shaped procedures as process steps and report the M38 matrix as
    fully served over the p2p fixture, which is exactly the honesty the M35 gate
    exists to protect ("not yet, and here is the type you are missing").

    The discriminator is DERIVED, never typed: a fragment counts as an entity of
    this type when it carries a non-empty body for every part the type declares
    that is NOT the home of one of its callout kinds. Those parts are the type's
    STRUCTURAL spine (for `process-step`: scope, inputs, outputs — the IPO edges
    an activity fragment simply does not have); the callout homes are excluded
    because a step legitimately carries no controls and no issues, and a
    populated area must not read as unpopulated because of that.

    Read-only, and cheap: one parse per fragment, only for a type with no role
    mapping. A type declaring no such parts counts 0 rather than matching
    everything — an undiscriminating shape is not evidence of a population."""
    try:
        tdecl = kernel.load_type(type_name)
    except (kernel.TypeDeclError, OSError):
        return 0
    homes = {c.home for c in tdecl.callouts}
    spine = [p.slug for p in tdecl.parts if p.slug not in homes]
    if not spine:
        return 0
    count = 0
    for comp in components:
        if comp.get("role") != _ENTITY_ROLE:
            continue
        fpath = area / str(comp.get("file") or "")
        if not fpath.is_file():
            continue
        try:
            entity = kernel.parse_entity(fpath.read_text(encoding="utf-8"),
                                         tdecl, slug=comp.get("slug"))
        except Exception:
            # A fragment this type cannot parse is not an entity of it. Loader
            # -grade defects in the AREA are reconcile's report, not a
            # serviceability exception (this function only ever counts).
            continue
        bodies = entity.parts_bodies()
        if all((bodies.get(slug) or "").strip() for slug in spine):
            count += 1
    return count


def _coverage_gaps(bname: str, spec: dict, area: Path) -> list[str]:
    """The engagement half of serviceability for a `coverage:` binding (M37).

    kernel.can_serve cannot answer this one at all: there is no entity type in
    the binding and no registry file to look for, so the declaration half is
    vacuous and the whole question is engagement-side — which per M35 A1 makes
    it definitions.py's, like _area_entity_count above.

    The precondition is one directory: an area with no `_taxonomy/` nodes has
    nothing whose coverage could be reported, and that is a **"not yet"**, never
    a refusal (a v1-shaped area simply has not been surveyed). The gap names
    taxonomy explicitly so the reader knows what to go and create."""
    tdir = Path(area) / _TAXONOMY_DIRNAME
    nodes = sorted(tdir.glob("*.md")) if tdir.is_dir() else []
    if nodes:
        return []
    domain = str(spec.get("of") or "taxonomy")
    return [f'binding "{bname}": area {Path(area).name} holds no {domain} '
            f"nodes yet ({_TAXONOMY_DIRNAME}/ is empty or absent), so "
            f"coverage has nothing to report"]


def _findings_gaps(bname: str, spec: dict, area: Path) -> list[str]:
    """The engagement half of serviceability for a `findings:` binding (M39).

    Like `_coverage_gaps`, kernel.can_serve cannot answer this at all (no entity
    type, no registry file), so the whole question is engagement-side. The
    precondition is the ENGAGEMENT's findings register, not the area's corpus:
    an engagement with no findings file, or one whose findings are all still
    proposed or rejected, has nothing a findings report could render — and that
    is a **"not yet"**, never a refusal. The gap names findings explicitly so
    the reader knows what to go and do (propose findings, then accept them at
    the gate).

    Read-only, and it does not import findings.py: one file existence check and
    one YAML read is cheaper than the analysis machinery, and serviceability
    must stay answerable for an engagement that has never run an analysis verb.
    The path convention is findings.py's, mirrored here for the same reason
    `_TAXONOMY_DIRNAME` mirrors coverage_map's."""
    root = _engagement_root(area)
    status = str(spec.get("findings") or "accepted").strip()
    fpath = None if root is None else \
        root / _FINDINGS_DIRNAME / _FINDINGS_FILENAME
    entries: list = []
    if fpath is not None and fpath.is_file():
        try:
            data = yaml.safe_load(fpath.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            data = {}
        if isinstance(data, dict) and isinstance(data.get("findings"), list):
            entries = [e for e in data["findings"] if isinstance(e, dict)
                       and e.get("status") == status]
    if entries:
        return []
    where = f"{_FINDINGS_DIRNAME}/{_FINDINGS_FILENAME}"
    return [f'binding "{bname}": this engagement holds no {status} findings '
            f"yet ({where} is absent or carries none), so the findings report "
            f"has nothing to render"]


def serviceability_records(defn: Definition, area) -> list[dict]:
    """Can this engagement area serve every binding of this definition? —
    the structured answer (M51).

    Returns one record per gap: `{"binding": <declared binding name>,
    "gap": <the sentence serviceability has always rendered>}`. `[]` means
    fully served. NEVER raises for an unserved binding: "not yet" is a
    report. Records come grouped in declaration order — the order the
    definition file lists its bindings in — because that is the only order
    this walk ever had.

    Two halves per binding, deliberately:
      * declaration half — kernel.can_serve over the binding's admitted keys
        (types/parts/callouts declared, channel registries present on disk);
      * engagement half — the area must actually HOLD entities of the bound
        type (see _area_entity_count for why can_serve cannot answer this);
    plus the two whole-question-engagement-side binding kinds, `coverage:`
    (_coverage_gaps) and `findings:` (_findings_gaps), whose sentences are
    attributed to their binding here exactly as the flat render always
    voiced them.

    This is the ONE place a gap is formatted. `serviceability` derives its
    flat strings from these records, so both surfaces — the sentences
    brief.py renders and the attribution needs.py consumes — can never
    disagree."""
    area = Path(area)
    records: list[dict] = []

    def _add(bname: str, sentences) -> None:
        records.extend({"binding": bname, "gap": s} for s in sentences)

    for bname, spec in defn.bindings.items():
        if "coverage" in spec:
            _add(bname, _coverage_gaps(bname, spec, area))
            continue
        if "findings" in spec:
            _add(bname, _findings_gaps(bname, spec, area))
            continue

        requirements = {k: spec[k] for k in _CAN_SERVE_KEYS if k in spec}
        _add(bname, (f'binding "{bname}": {err}'
                     for err in kernel.can_serve(requirements, area)))

        tname = requirements.get("entities")
        if isinstance(tname, str) and tname.strip():
            tname = tname.strip()
            if _area_entity_count(area, tname) == 0:
                _add(bname, [f'binding "{bname}": area {area.name} holds no '
                             f'entities of type "{tname}"'])

    return records


def serviceability(defn: Definition, area) -> list[str]:
    """The flat serviceability report — the gap sentences alone.

    A pure derivation from `serviceability_records` (M51): the strings ARE
    the records' `gap` sentences, in the records' order, so this surface and
    the structured one cannot drift apart. [] means fully served; never
    raises for an unserved binding. Kept as the human-facing render brief.py
    prints verbatim."""
    return [r["gap"] for r in serviceability_records(defn, area)]


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
    #: M36 WP-G2: the definition's binding map, carried on the compiled plan.
    #: A plan block names a binding by NAME, so a consumer that wants the
    #: binding's content (part selections, channels, callout kinds) previously
    #: had to be handed `Definition.bindings` alongside the plan — one plan, two
    #: arguments, and nothing forcing them to describe the same definition.
    #: Carrying them here makes the plan self-describing; the explicit
    #: `bindings=` kwarg of `render_glue.render_plan` still WINS when given.
    bindings: dict[str, dict] = field(default_factory=dict)


def compile_plan(defn: Definition, area) -> Plan:
    """Compile a loaded definition against an area into a Plan.

    Deterministic and READ-ONLY: it walks defn.shape in declaration order and
    touches nothing on disk — no writes, no cache files. `area` is taken for
    the signature the pipeline needs (and so future compile steps can resolve
    area-relative selections) without being read here.

    View blocks become PlanViews in shape order; entity-part and static blocks
    carry through as plan blocks. `.blocks` is the full ordered shape."""
    plan = Plan(name=defn.name,
                bindings={k: dict(v) for k, v in defn.bindings.items()})
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


# --------------------------------------------------------------------------- #
# M40 WP-V1 — the MATERIALIZE verb
#
# The language gap this closes (M38 A1, docs/v2/M40-definition-views.md): a
# definition's `kind: view` blocks are compiled into `Plan.views`, but only a
# `role: derived` manifest component ever CAUSES aggregate to build a view —
# and a plan carries neither a `file` nor an `order`. Two enumerations of the
# same views, nothing joining them.
#
# The join is an explicit VERB, not a side effect of compiling or rendering:
# compile_plan stays read-only and render_glue stays out of it (M36 WP-G1's
# refusal is the law here — a renderer that silently writes manifests is a
# special case in disguise). The shape is v1's `scaffold.sync_profile`, which
# already does exactly this reconciliation driven by an M14 profile instead of
# a compiled plan: idempotent, preserving, never deleting, re-validated.
# --------------------------------------------------------------------------- #

#: The manifest component role a materialized view becomes, and the file-name
#: shape minted for it. Both are doc_model/scaffold conventions, mirrored (see
#: _stub_text for the same posture on the stub body).
_DERIVED_ROLE = "derived"

#: File/order policy — MECHANICAL, DOCUMENTED, NOT CONFIGURABLE (the spec's
#: named review risk is placement-policy creep). A new view's order starts at
#: max(existing orders) + _ORDER_GAP and increments by _ORDER_STEP per
#: subsequent new view, so materialized views land after everything already in
#: the area, in the definition's block order. Position is DISPLAY: a
#: definition-level placement key is deliberately not added, and a hand-tuned
#: existing entry outranks this policy entirely (see _materialize below).
_ORDER_GAP = 10
_ORDER_STEP = 1


def _stub_text(kind: str, writer: str, heading: str) -> str:
    """The pending stub body for a newly materialized view.

    `scaffold.render_derived`'s shape — asked of scaffold itself when it
    imports cleanly, so the marker that aggregate/render read has exactly ONE
    author. The fallback is a MIRROR of that function (heading, the
    `<!-- derived: kind; writer: w -->` marker, the pending line) and exists
    only so materializing does not depend on the whole v1 scaffolder being
    importable; if the two ever drift, scaffold.py is the original."""
    try:
        import scaffold
    except Exception:                        # pragma: no cover - scaffold ships beside us
        return (f"## {heading}\n\n"
                f"<!-- derived: {kind}; writer: {writer} -->\n\n"
                "> _Pending generation._\n")
    return scaffold.render_derived(kind, writer, heading)


def _read_manifest(area: Path) -> dict:
    """The area's manifest, or a named refusal. Materialize RECONCILES an
    already-scaffolded area (sync_profile's precondition, same words): a
    fresh area goes through the confirm gate first."""
    path = area / "manifest.json"
    if not path.is_file():
        raise DefinitionError(
            f"{area.name}: no manifest at {path} — materialize_views "
            f"reconciles an ALREADY-SCAFFOLDED area's derived components with "
            f"a definition's view blocks; a fresh area goes through the "
            f"confirm gate first (scaffold.py --confirm)")
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise DefinitionError(
            f"{area.name}: manifest at {path} is unreadable ({exc})") from exc
    if not isinstance(manifest, dict) or not isinstance(
            manifest.get("components"), list):
        raise DefinitionError(
            f'{area.name}: manifest at {path} has no "components" list')
    return manifest


def materialize_views(area, name: str | None = None) -> dict:
    """Reflect a definition's `kind: view` blocks into the area manifest.

    For each view block of the compiled plan, ensure the manifest carries a
    `role: derived` component with the canonical six keys (`file`, `role`,
    `derived_kind` = the block id, `writer` = the block's writer, `heading` =
    the block's title, `order`) and ensure its stub file exists. Agent-writer
    views get the same entry with `writer: agent` — aggregate's placeholder
    discipline then applies, unchanged.

    Resolution: `name` picks the definition (user file shadowing shipped, the
    ordinary M13 path); `None` falls back to `resolve_definition(area)` (the
    M14 profile alias). Either way the definition loads through the ORDINARY
    four-stage loader before anything is written — an unloadable definition
    refuses with nothing touched.

    Discipline, all of it sync_profile's:
      * PRESERVATION — an existing derived component whose `derived_kind`
        matches is kept byte-for-byte: never renamed, re-ordered or re-titled.
        A hand-tuned entry (the IPO fixture's matrix at order 20) outranks the
        mechanical policy, because a human put it there.
      * IDEMPOTENCE — a second call adds nothing and writes nothing, not even
        a re-serialized manifest (mtimes are part of the contract).
      * NEVER DELETE — a view the definition dropped keeps its component and
        its file; removal is a human edit, as everywhere else in the system.
      * NEVER TOUCH NON-DERIVED — static and procedure components pass through
        in their existing sequence.

    Fail-loud: the assembled manifest is re-validated through
    `doc_model.validate_manifest` and a validation error REFUSES, leaving the
    manifest file unchanged (write-aside then replace). A minted `file` that
    collides with an existing file of a DIFFERENT kind refuses by name rather
    than overwriting somebody else's view.

    Returns the delta — `{"area", "definition", "added", "preserved",
    "created_files", "skipped_non_view"}` — so a caller (and a test) can see
    what happened instead of trusting silence."""
    import doc_model                 # local: keeps definitions importable alone

    area = Path(area)
    if not area.is_dir():
        raise DefinitionError(f"materialize_views: no such area folder: {area}")

    defn = (load_definition(name, area=area) if name is not None
            else resolve_definition(area))
    plan = compile_plan(defn, area)          # READ-ONLY, as ever
    titles = {b.id: b.title for b in plan.blocks}

    manifest = _read_manifest(area)
    components = [c for c in manifest["components"] if isinstance(c, dict)]
    existing_kinds = {c.get("derived_kind"): c for c in components
                      if c.get("role") == _DERIVED_ROLE}
    #: file -> the derived kind that owns it (None for a non-derived component),
    #: for the cross-kind collision refusal below.
    owners = {str(c.get("file")): c.get("derived_kind") for c in components}
    orders = [c["order"] for c in components if isinstance(c.get("order"), int)]
    next_order = (max(orders) if orders else 0) + _ORDER_GAP

    added: list[str] = []
    preserved: list[str] = []
    created: list[str] = []
    minted: list[dict] = []

    for view in plan.views:
        kind = view.kind
        if kind in existing_kinds:
            # The preservation rule: this component is the truth, whatever the
            # policy would have minted for it.
            preserved.append(kind)
            comp = existing_kinds[kind]
            fname = str(comp.get("file") or "")
            fpath = area / fname
            if fname and not fpath.exists():
                fpath.write_text(
                    _stub_text(kind, str(comp.get("writer") or view.writer),
                               str(comp.get("heading") or titles.get(kind, kind))),
                    encoding="utf-8")
                created.append(fname)
            continue

        fname = f"{next_order}_{kind}.md"
        owner = owners.get(fname, "")
        if fname in owners and owner != kind:
            raise DefinitionError(
                f'{area.name}: materializing view "{kind}" of definition '
                f'"{defn.name}" would mint file "{fname}", which the manifest '
                f"already lists for "
                + (f'derived kind "{owner}"' if owner else "a non-derived "
                   "component")
                + " — refusing to overwrite it (resolve the collision by hand)")
        comp = {"file": fname, "role": _DERIVED_ROLE, "derived_kind": kind,
                "writer": view.writer, "heading": titles.get(kind, kind),
                "order": next_order}
        minted.append(comp)
        owners[fname] = kind
        added.append(kind)
        next_order += _ORDER_STEP

    report = {"area": area.name, "definition": defn.name,
              "added": added, "preserved": preserved,
              "created_files": created}
    if not minted:
        # Idempotence: nothing minted means nothing to write. The manifest file
        # is not re-serialized — an unchanged area must stay byte- AND
        # mtime-identical.
        return report

    manifest = dict(manifest)
    manifest["components"] = components + minted
    errors = doc_model.validate_manifest(manifest)
    if errors:
        raise DefinitionError(
            f'{area.name}: materializing definition "{defn.name}" would leave '
            f"the manifest invalid, so nothing was written:\n  - "
            + "\n  - ".join(errors))

    # Write-aside then replace: a crash mid-write must not leave a half-written
    # manifest where the whole pipeline's membership authority should be.
    path = area / "manifest.json"
    tmp = path.with_suffix(".json.materialize-tmp")
    tmp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    tmp.replace(path)

    for comp in minted:
        fpath = area / comp["file"]
        if not fpath.exists():
            fpath.write_text(
                _stub_text(comp["derived_kind"], comp["writer"],
                           comp["heading"]),
                encoding="utf-8")
            created.append(comp["file"])
    report["created_files"] = created
    return report


def render_plan(plan: Plan, area, out_path, **kwargs) -> dict:
    """Render a compiled Plan to a .docx. See scripts/render_glue.py for the
    fidelity statement — this is a convenience delegate so callers that
    already hold `definitions` do not need a second import."""
    import render_glue
    return render_glue.render_plan(plan, area, out_path, **kwargs)
