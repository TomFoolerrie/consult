#!/usr/bin/env python3
"""
kernel.py — the M33 brain kernel (docs/v2/M33-brain-kernel.md).

This module owns the five kernel concepts; this file currently carries the
TYPE-DECLARATION half (WP1): loading `kernel/types/<name>.yaml` into a
validated TypeDecl, with fail-loud refusals that name the file and the
offending key, and a registry that never half-registers a refused type.

Type declarations are plugin DATA, not engagement state: `activity.yaml` is
v1 written down (its parity with doc_model/callouts is test-enforced), and
the loader treats shipped and user types identically — no name is
special-cased.

Python 3, stdlib + pyyaml only (like every other engine module).
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

from dataclasses import dataclass, field
from pathlib import Path

import yaml


class TypeDeclError(Exception):
    """Raised when a type declaration file is invalid. The message always
    names the file and the offending key/value (fail-loud, same posture as
    doc_model.validate_manifest)."""


# --------------------------------------------------------------------------- #
# Declaration dataclasses — the loaded, validated shape of a type YAML.
# --------------------------------------------------------------------------- #

@dataclass
class PartDecl:
    """One part (the general form of an M23 section registry entry)."""
    slug: str
    title: str
    kind: str  # prose | table | list
    title_aliases: list[str] = field(default_factory=list)


@dataclass
class CalloutDecl:
    """One admitted callout kind (general form of LABEL_TO_PREFIX + home).

    `fields` is OPTIONAL declaration metadata (M43 Part C): the sub-field
    vocabulary this callout kind carries when the sources support it, e.g.
    process-step's CONTROL and its four M42 field names. It is DOCUMENTATION
    plus vocabulary for consumers (scripts/hygiene.py reads the names from
    here instead of typing prose constants) and is NEVER a parse gate — a
    fragment whose callout declares none of these fields parses exactly as it
    did before the key existed. A callout kind that declares no fields
    carries the empty tuple."""
    label: str
    prefix: str
    home: str  # part slug the callout is homed to
    fields: tuple[str, ...] = ()


@dataclass
class ChannelDecl:
    """One consult-meta binding channel (general form of systems/roles)."""
    name: str
    registry: str  # registry filename, e.g. "systems.yaml"


@dataclass
class TypeDecl:
    """A loaded entity-type declaration."""
    name: str
    parts: list[PartDecl] = field(default_factory=list)
    #: aggregate of every part's title aliases: {alias title -> part slug}
    title_aliases: dict[str, str] = field(default_factory=dict)
    #: frozen letter positions: {letter -> part slug}
    letter_aliases: dict[str, str] = field(default_factory=dict)
    #: past slugs: {old slug -> part slug}
    slug_aliases: dict[str, str] = field(default_factory=dict)
    callouts: list[CalloutDecl] = field(default_factory=list)
    channels: list[ChannelDecl] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# Loader + registry
# --------------------------------------------------------------------------- #

#: Repo root = parent of scripts/ — type declarations ship in kernel/types/.
_REPO_ROOT = Path(__file__).resolve().parent.parent
TYPES_DIR = _REPO_ROOT / "kernel" / "types"

#: Successfully loaded declarations, by name. A refused load never writes
#: here — validation completes before registration (never half-registers).
_REGISTRY: dict[str, TypeDecl] = {}

_ALLOWED_TOP_KEYS = {
    "type", "parts", "callouts", "channels", "letter_aliases", "slug_aliases",
}
_ALLOWED_PART_KEYS = {"slug", "title", "kind", "title_aliases"}
_ALLOWED_CALLOUT_KEYS = {"label", "prefix", "home", "fields"}
_ALLOWED_CHANNEL_KEYS = {"name", "registry"}


def _require_str(fname: str, where: str, entry: dict, key: str) -> str:
    val = entry.get(key)
    if not isinstance(val, str) or not val.strip():
        raise TypeDeclError(
            f'{fname}: {where} missing or invalid required key "{key}" '
            f"(got {val!r})")
    return val.strip()


def _parse_decl(path: Path, data) -> TypeDecl:
    """Validate raw YAML into a TypeDecl, raising TypeDeclError on any
    defect — every message names the file and the offending key/value."""
    fname = path.name

    if not isinstance(data, dict):
        raise TypeDeclError(f"{fname}: type declaration is not a mapping")

    for key in data:
        if key not in _ALLOWED_TOP_KEYS:
            raise TypeDeclError(f'{fname}: unknown top-level key "{key}"')

    name = data.get("type") or path.stem

    raw_parts = data.get("parts")
    if not isinstance(raw_parts, list) or not raw_parts:
        raise TypeDeclError(f'{fname}: "parts" must be a non-empty list')

    parts: list[PartDecl] = []
    title_aliases: dict[str, str] = {}
    seen_slugs: set[str] = set()
    for i, entry in enumerate(raw_parts):
        where = f"parts[{i}]"
        if not isinstance(entry, dict):
            raise TypeDeclError(f"{fname}: {where} is not a mapping")
        for key in entry:
            if key not in _ALLOWED_PART_KEYS:
                raise TypeDeclError(f'{fname}: {where} unknown key "{key}"')
        slug = _require_str(fname, where, entry, "slug")
        title = _require_str(fname, where, entry, "title")
        kind = _require_str(fname, where, entry, "kind")
        if slug in seen_slugs:
            raise TypeDeclError(f'{fname}: duplicate part slug "{slug}"')
        seen_slugs.add(slug)
        aliases = entry.get("title_aliases") or []
        if not isinstance(aliases, list) or not all(
                isinstance(a, str) for a in aliases):
            raise TypeDeclError(
                f'{fname}: {where} ("{slug}") "title_aliases" must be a '
                f"list of strings")
        for alias in aliases:
            if alias in title_aliases and title_aliases[alias] != slug:
                raise TypeDeclError(
                    f'{fname}: title alias "{alias}" collides across parts '
                    f'"{title_aliases[alias]}" and "{slug}"')
            title_aliases[alias] = slug
        parts.append(PartDecl(slug=slug, title=title, kind=kind,
                              title_aliases=list(aliases)))

    def _alias_map(key: str) -> dict[str, str]:
        raw = data.get(key) or {}
        if not isinstance(raw, dict):
            raise TypeDeclError(f'{fname}: "{key}" must be a mapping')
        out: dict[str, str] = {}
        for k, v in raw.items():
            if v not in seen_slugs:
                raise TypeDeclError(
                    f'{fname}: {key} "{k}" points at undeclared part "{v}"')
            out[str(k)] = str(v)
        return out

    letter_aliases = _alias_map("letter_aliases")
    slug_aliases = _alias_map("slug_aliases")

    callouts: list[CalloutDecl] = []
    raw_callouts = data.get("callouts") or []
    if not isinstance(raw_callouts, list):
        raise TypeDeclError(f'{fname}: "callouts" must be a list')
    for i, entry in enumerate(raw_callouts):
        where = f"callouts[{i}]"
        if not isinstance(entry, dict):
            raise TypeDeclError(f"{fname}: {where} is not a mapping")
        for key in entry:
            if key not in _ALLOWED_CALLOUT_KEYS:
                raise TypeDeclError(f'{fname}: {where} unknown key "{key}"')
        label = _require_str(fname, where, entry, "label")
        prefix = _require_str(fname, where, entry, "prefix")
        home = _require_str(fname, where, entry, "home")
        if home not in seen_slugs:
            raise TypeDeclError(
                f'{fname}: callout "{label}" homed to undeclared part '
                f'"{home}"')
        raw_fields = entry.get("fields")
        if raw_fields is None:
            fields: tuple[str, ...] = ()
        else:
            if not isinstance(raw_fields, list) or not all(
                    isinstance(f, str) and f.strip() for f in raw_fields):
                raise TypeDeclError(
                    f'{fname}: {where} ("{label}") "fields" must be a list of '
                    f"non-empty strings (got {raw_fields!r})")
            fields = tuple(f.strip() for f in raw_fields)
        callouts.append(CalloutDecl(label=label, prefix=prefix, home=home,
                                    fields=fields))

    channels: list[ChannelDecl] = []
    raw_channels = data.get("channels") or []
    if not isinstance(raw_channels, list):
        raise TypeDeclError(f'{fname}: "channels" must be a list')
    for i, entry in enumerate(raw_channels):
        where = f"channels[{i}]"
        if not isinstance(entry, dict):
            raise TypeDeclError(f"{fname}: {where} is not a mapping")
        for key in entry:
            if key not in _ALLOWED_CHANNEL_KEYS:
                raise TypeDeclError(f'{fname}: {where} unknown key "{key}"')
        cname = _require_str(fname, where, entry, "name")
        registry = entry.get("registry")
        if not isinstance(registry, str) or not registry.strip():
            raise TypeDeclError(
                f'{fname}: channel "{cname}" missing its "registry" '
                f"filename")
        channels.append(ChannelDecl(name=cname, registry=registry.strip()))

    return TypeDecl(name=name, parts=parts, title_aliases=title_aliases,
                    letter_aliases=letter_aliases, slug_aliases=slug_aliases,
                    callouts=callouts, channels=channels)


def load_type_file(path) -> TypeDecl:
    """Load + validate one type declaration YAML by explicit path.

    Registration happens only AFTER full validation succeeds, so a refused
    type never half-registers (is_type_loaded stays False)."""
    path = Path(path)
    if not path.is_file():
        raise TypeDeclError(f"{path.name}: type declaration file not found "
                            f"at {path}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise TypeDeclError(f"{path.name}: not valid YAML: {exc}") from exc
    decl = _parse_decl(path, data)
    _REGISTRY[decl.name] = decl
    return decl


def load_type(name: str) -> TypeDecl:
    """Load the shipped (or user-added) type `<repo>/kernel/types/<name>.yaml`.

    Names are never special-cased — shipped and user types go through the
    same loader and the same refusals."""
    return load_type_file(TYPES_DIR / f"{name}.yaml")


def is_type_loaded(name: str) -> bool:
    """True when a type of this name has been SUCCESSFULLY loaded — a
    refused load never registers, so this stays False after one."""
    return name in _REGISTRY


# --------------------------------------------------------------------------- #
# WP2 — parse_entity / Entity: the generalization of aggregate's
# split_subsections + parse_consult_meta + parse_callouts and doc_model's
# duplicate_sections, driven by a TypeDecl.
#
# DELEGATION POSTURE (M33 wraps; M36 migrates): the ALGORITHMS below are the
# v1 algorithms — the grammar primitives are imported from the v1 modules
# (doc_model.SECTION_HEADING_RE + _norm_section_key, callouts.blank_fences +
# ID_STRICT_RE + FragmentError, aggregate.CALLOUT_LINE_RE + SUBFIELD_RE +
# CONSULT_META_RE) so the two spellings of the grammar can never drift.
# Only the VOCABULARY (part titles/aliases, letter positions, callout
# label->prefix map, binding channels) comes from the TypeDecl, which is what
# lets a second type (process-step, WP3) route through these same paths.
# For the activity type the loaded tables are test-pinned identical to
# doc_model/callouts' module tables (TestActivityParity), so these paths are
# equivalence-tested byte-equal to the v1 functions over the frozen corpus
# (TestParseEquivalence). Parse errors stay v1 fail-loud: callouts'
# FragmentError propagates unchanged — never wrapped, never swallowed.
# --------------------------------------------------------------------------- #

import re

import doc_model
import aggregate
from callouts import FragmentError, ID_STRICT_RE, blank_fences  # noqa: F401


def _part_of_heading(line: str, tdecl: TypeDecl) -> str | None:
    """The part slug a `###` heading line identifies under `tdecl`, or None.

    The tdecl-driven twin of doc_model.section_of_heading: same regex, same
    normalizer, same precedence (title first, letter as legacy positional
    fallback), titles-only matching (a part's SLUG never resolves a heading).
    """
    m = doc_model.SECTION_HEADING_RE.match(line or "")
    if not m:
        return None
    norm = doc_model._norm_section_key
    titles: dict[str, str] = {}
    for part in tdecl.parts:
        for source in (part.title, *part.title_aliases):
            key = norm(source)
            titles.setdefault(key, part.slug)
            titles.setdefault(key.replace("-", ""), part.slug)
    # doc_model builds canonical titles before aliases; loop order above
    # preserves that precedence (setdefault: first writer wins).
    slug = titles.get(norm(m.group("title")))
    if slug is None and m.group("letter"):
        slug = tdecl.letter_aliases.get(m.group("letter"))
    return slug


@dataclass
class Entity:
    """One parsed entity: a fragment's text read through its TypeDecl.

    Built by parse_entity; the accessor methods answer exactly what the v1
    parsers answered (the M33 API contract pins them equal for activity)."""
    tdecl: TypeDecl
    slug: str | None
    text: str
    _parts_bodies: dict[str, str]
    _bindings: dict[str, list[str]]
    _callouts: list[dict]
    _duplicate_parts: dict[str, list[str]]

    def parts_bodies(self) -> dict[str, str]:
        """{part slug: body text} — v1: aggregate.split_subsections."""
        return self._parts_bodies

    def bindings(self) -> dict[str, list[str]]:
        """{channel name: [registry slugs]} — v1: aggregate.parse_consult_meta."""
        return self._bindings

    def callout_dicts(self) -> list[dict]:
        """[{label, prefix, id, text, fields}] — v1: aggregate.parse_callouts."""
        return self._callouts

    def duplicate_parts(self) -> dict[str, list[str]]:
        """{slug: [written titles]} for parts headed more than once —
        v1: doc_model.duplicate_sections (M16 doctrine: tolerate + report)."""
        return self._duplicate_parts


def _split_parts(text: str, tdecl: TypeDecl) -> dict[str, str]:
    """tdecl-driven twin of aggregate.split_subsections: two headings that
    resolve to one slug CONCATENATE their bodies in document order (M16 C+D
    merge doctrine — no fact lost); a `## ` line ends the current run."""
    sections: dict[str, str] = {}

    def _close(slug: str, buf: list[str]) -> None:
        body = "\n".join(buf).strip()
        prior = sections.get(slug)
        sections[slug] = f"{prior}\n\n{body}".strip() if prior else body

    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        slug = _part_of_heading(line, tdecl)
        if slug is not None:
            if current is not None:
                _close(current, buf)
            current = slug
            buf = []
            continue
        if line.startswith("## "):  # next fragment / unknown heading ends the run
            if current is not None:
                _close(current, buf)
                current = None
            buf = []
            continue
        if current is not None:
            buf.append(line)
    if current is not None:
        _close(current, buf)
    return sections


def _duplicates(text: str, tdecl: TypeDecl) -> dict[str, list[str]]:
    """tdecl-driven twin of doc_model.duplicate_sections."""
    seen: dict[str, list[str]] = {}
    for line in (text or "").split("\n"):
        slug = _part_of_heading(line, tdecl)
        if slug is not None:
            m = doc_model.SECTION_HEADING_RE.match(line)
            seen.setdefault(slug, []).append(m.group("title") if m else "")
    return {slug: titles for slug, titles in seen.items() if len(titles) > 1}


def _parse_bindings(text: str, tdecl: TypeDecl) -> dict[str, list[str]]:
    """tdecl-driven twin of aggregate.parse_consult_meta: the channel NAMES
    come from the declaration; the fenced-block grammar and the missing-block
    -> empty-lists behavior are v1's. Malformed YAML raises FragmentError
    (v1 fail-loud, propagated unchanged)."""
    names = [ch.name for ch in tdecl.channels]
    m = aggregate.CONSULT_META_RE.search(text)
    if not m:
        return {name: [] for name in names}
    try:
        data = yaml.safe_load(m.group("body")) or {}
    except yaml.YAMLError as exc:
        raise FragmentError(f"malformed consult-meta YAML: {exc}") from exc
    if not isinstance(data, dict):
        return {name: [] for name in names}

    def _slugs(key: str) -> list[str]:
        v = data.get(key) or []
        if isinstance(v, str):
            v = [v]
        return [str(s).strip() for s in v if str(s).strip()]

    return {name: _slugs(name) for name in names}


def _parse_callouts(slug: str | None, raw_text: str,
                    tdecl: TypeDecl) -> list[dict]:
    """tdecl-driven twin of aggregate.parse_callouts: same line grammar, same
    fence blanking, same blockquote-consumption, same fail-loud refusals —
    only the label->prefix vocabulary comes from the declaration."""
    label_to_prefix = {c.label: c.prefix for c in tdecl.callouts}
    where = slug if slug is not None else f"<{tdecl.name}>"
    text = blank_fences(raw_text)
    lines = text.splitlines()
    out: list[dict] = []
    seen: dict[str, int] = {}

    i = 0
    while i < len(lines):
        m = aggregate.CALLOUT_LINE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        label = re.sub(r"\s+", " ", m.group("label")).strip()
        cid = m.group("id").strip()

        if label not in label_to_prefix:
            raise FragmentError(
                f"unknown callout label {label!r} at {where}:{i + 1} "
                f"(expected one of {', '.join(sorted(label_to_prefix))})"
            )
        expected = label_to_prefix[label]

        if not ID_STRICT_RE.match(cid):
            raise FragmentError(
                f"malformed callout ID {cid!r} at {where}:{i + 1} "
                f"(grammar: <PREFIX>-<ALNUM> e.g. {expected}-001)"
            )
        prefix = cid.split("-", 1)[0]
        if prefix != expected:
            raise FragmentError(
                f"ID prefix/label mismatch at {where}:{i + 1}: label {label!r} "
                f"requires prefix {expected}- but ID is {cid!r}"
            )
        if cid in seen:
            raise FragmentError(
                f"duplicate ID {cid!r} within {tdecl.name} {where} "
                f"(first at line {seen[cid]}, again at line {i + 1})"
            )
        seen[cid] = i + 1

        # Consume the whole contiguous blockquote below the label line —
        # exactly aggregate.parse_callouts' walk (continuations extend the
        # text, `> - **Field:** value` bullets become sub-fields, wrapped
        # field values extend that field; stop at non-quote or new callout).
        fields: dict[str, str] = {}
        text_parts = [m.group("text").strip()]
        cur_field: str | None = None
        j = i + 1
        while j < len(lines):
            line = lines[j]
            if aggregate.CALLOUT_LINE_RE.match(line):
                break  # a new callout starts its own block
            sm = aggregate.SUBFIELD_RE.match(line)
            if sm:
                cur_field = sm.group("field").strip()
                fields[cur_field] = sm.group("value").strip()
                j += 1
                continue
            qm = re.match(r"^\s*>\s?(.*)$", line)
            if qm is None:
                break  # blockquote ended
            cont = qm.group(1).strip()
            if cont:
                if cur_field is not None:
                    fields[cur_field] = (fields[cur_field] + " " + cont).strip()
                else:
                    text_parts.append(cont)
            j += 1

        out.append(
            {"label": label, "prefix": prefix, "id": cid,
             "text": " ".join(p for p in text_parts if p), "fields": fields}
        )
        i = j
    return out


def parse_entity(text: str, tdecl: TypeDecl, slug: str | None = None) -> Entity:
    """Parse one fragment's text through a type declaration.

    `slug` is the entity's identity for callout error messages (mirroring
    aggregate.parse_callouts' signature); parts/bindings/duplicates never
    need it. FragmentError propagates unchanged (v1 fail-loud posture)."""
    return Entity(
        tdecl=tdecl,
        slug=slug,
        text=text,
        _parts_bodies=_split_parts(text, tdecl),
        _bindings=_parse_bindings(text, tdecl),
        _callouts=_parse_callouts(slug, text, tdecl),
        _duplicate_parts=_duplicates(text, tdecl),
    )


# --------------------------------------------------------------------------- #
# WP4 — can_serve(view_requirements, area) -> [error strings] (the
# serviceability half; pure function over declarations + area state).
# --------------------------------------------------------------------------- #

def can_serve(requirements: dict, area) -> list[str]:
    """Answer "can this area serve a view with these requirements?" with a
    list of precise error strings — [] means serviceable.

    Pure over declarations + area state: type/part/callout checks go against
    the loaded TypeDecl; channel checks additionally require the channel's
    registry file to exist under `<area>/_reference/`. Unserviceable
    requirements never raise — errors are the return value. (Deliberately
    NOT a query engine; M35 owns the binding language.)"""
    errors: list[str] = []
    area = Path(area)

    known_keys = {"entities", "parts", "callouts", "channels"}
    for key in requirements:
        if key not in known_keys:
            errors.append(f"unknown requirement key '{key}' "
                          f"(known: {', '.join(sorted(known_keys))})")

    tdecl = None
    type_name = requirements.get("entities")
    if type_name is not None:
        try:
            tdecl = load_type(type_name)
        except (TypeDeclError, OSError):
            errors.append(f"no type declaration '{type_name}' "
                          f"(kernel/types/{type_name}.yaml)")

    for part in requirements.get("parts", []) or []:
        if tdecl is None:
            errors.append(f"part '{part}': cannot check against unknown "
                          f"type '{type_name}'")
        elif part not in {p.slug for p in tdecl.parts}:
            errors.append(f"part '{part}' not declared by type "
                          f"'{tdecl.name}'")

    for callout in requirements.get("callouts", []) or []:
        if tdecl is None:
            errors.append(f"callout '{callout}': cannot check against "
                          f"unknown type '{type_name}'")
        elif not any(callout in (c.prefix, c.label)
                     for c in tdecl.callouts):
            errors.append(f"callout '{callout}' not declared by type "
                          f"'{tdecl.name}'")

    for channel in requirements.get("channels", []) or []:
        if tdecl is None:
            errors.append(f"channel '{channel}': cannot check against "
                          f"unknown type '{type_name}'")
            continue
        decl = next((c for c in tdecl.channels if c.name == channel), None)
        if decl is None:
            errors.append(f"channel '{channel}' not declared by type "
                          f"'{tdecl.name}'")
            continue
        registry = area / "_reference" / decl.registry
        if not registry.is_file():
            errors.append(f"channel '{channel}': registry "
                          f"_reference/{decl.registry} missing in {area}")

    return errors
