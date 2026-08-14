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
    """One admitted callout kind (general form of LABEL_TO_PREFIX + home)."""
    label: str
    prefix: str
    home: str  # part slug the callout is homed to


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
_ALLOWED_CALLOUT_KEYS = {"label", "prefix", "home"}
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
        callouts.append(CalloutDecl(label=label, prefix=prefix, home=home))

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
# WP2 — parse_entity / Entity (the generalization of aggregate's
# split_subsections + parse_consult_meta + parse_callouts and doc_model's
# duplicate_sections, driven by a TypeDecl). Lands after WP1 merges.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# WP4 — can_serve(view_requirements, area) -> [error strings] (the
# serviceability half; pure function over declarations + area state).
# --------------------------------------------------------------------------- #
