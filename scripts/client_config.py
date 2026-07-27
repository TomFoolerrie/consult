"""client_config.py — engagement-level client config resolution (M13).

Client context is human-authored ground truth, so it may live **once per
engagement** instead of once per area:

    components/
      _client/              engagement-wide (org-chart.yaml, taxonomy.yaml, ...)
        conventions/        optional engagement-wide phrasing digest
      accounts-payable/
        _client/            optional per-area override, same file names

`load(area)` walks the **area `_client/` first, then the parent
`components/_client/`** and merges **per top-level YAML key**:

  - a top-level key present in the area layer wins *entirely* for that key
    (no deep merge — deep-merging hand-edited YAML is how silent surprises
    happen);
  - keys absent from the area layer come from the engagement layer;
  - neither layer present → an empty mapping, i.e. today's "no client
    context" behavior, unchanged.

`conventions/` merges by **file**: parent files plus area files, and an area
`conventions/{slug}.md` shadows a parent file of the same name.

Malformed YAML anywhere in the walk is fatal (`ClientConfigError`, naming the
file). There is no schema validator — these are small hand-written files, so
the contract is "parse or stop".

`profile(area) -> Profile` (M14) is the one typed accessor built on top of this
resolution: the DOCUMENT PROFILE is engagement config like any other, so it is
one top-level `profile:` key in `_client/profile.yaml` and gets merging,
shadowing and provenance for free. It is validated fail-loud (see `ProfileError`)
because it decides the shape of the client deliverable.

`holds(area, holdable, gates) -> Holds` (M17) is the second typed accessor, and
the same story: STICKY HOLDS are engagement policy, so they are one top-level
`hold:` key (conventionally `_client/consult.yaml`) and an area list shadows the
engagement's whole. Validated fail-loud (see `HoldError`) — a typo'd action name
that read as "nothing held" would spend the agents the hold exists to stop.

`_reference/` is deliberately NOT part of this: it is agent-proposed and
human-confirmed per area, and sharing it would let one area's low-confidence
guess become another area's fact.

Python 3, stdlib + pyyaml.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

CLIENT_DIR = "_client"
CONVENTIONS_DIR = "conventions"

AREA = "area"
ENGAGEMENT = "engagement"

#: How each layer is named in stage output (see the spec's Reporting section).
LAYER_LABELS = {
    AREA: "_client/ (area)",
    ENGAGEMENT: "_client/ (engagement)",
    None: "none",
}


class ClientConfigError(RuntimeError):
    """Malformed client config — the run stops, with the file named."""


class ClientConfig(dict):
    """The merged client config.

    A plain `dict` of merged top-level keys (so `load(area)` returns a dict,
    as the spec says), carrying provenance on the side:

      - ``layers``            top-level key -> "area" | "engagement"
      - ``conventions``       file name -> resolved Path
      - ``convention_layers`` file name -> "area" | "engagement"
      - ``present``           layers that exist on disk with at least one file
    """

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.layers: dict[str, str] = {}
        self.conventions: dict[str, Path] = {}
        self.convention_layers: dict[str, str] = {}
        self.present: list[str] = []

    # ---------------------------------------------------------- reporting
    @property
    def layer(self) -> str | None:
        """The highest-precedence layer that answered, or None.

        "area" whenever the area's own `_client/` contributed anything —
        that is the layer a surprised reader needs pointed out first.
        """
        for name in (AREA, ENGAGEMENT):
            if name in self.present:
                return name
        return None

    def layer_label(self) -> str:
        """`_client/ (area)`, `_client/ (engagement)`, or `none`."""
        return LAYER_LABELS[self.layer]

    def report_line(self, prefix: str = "client config") -> str:
        """The one line every stage that reads client config prints."""
        return f"{prefix}: {self.layer_label()}"


# --------------------------------------------------------------------- yaml
def _read_yaml(path: Path) -> dict:
    """Parse one client YAML file. Malformed → fatal, with the file named."""
    if yaml is None:  # pragma: no cover - pyyaml absent
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ClientConfigError(f"malformed YAML in {path}: {exc}") from exc
    except OSError as exc:
        raise ClientConfigError(f"unreadable client config {path}: {exc}") from exc
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ClientConfigError(
            f"malformed YAML in {path}: expected a mapping at the top level, "
            f"got {type(data).__name__}"
        )
    return data


def _layer_keys(client_dir: Path) -> tuple[dict, list[Path]]:
    """Merge every `*.yaml` / `*.yml` in one `_client/` into a key namespace.

    The files carry disjoint top-level keys by convention (`org-chart.yaml` →
    `people:`, `taxonomy.yaml` → `taxonomy:`, `profile.yaml` → `profile:`).
    Two files in the SAME layer claiming the same top-level key is ambiguous,
    so it stops the run rather than picking one.
    """
    merged: dict = {}
    owners: dict[str, Path] = {}
    files = sorted(
        p for p in client_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".yaml", ".yml")
    ) if client_dir.is_dir() else []
    for path in files:
        for key, value in _read_yaml(path).items():
            if key in owners:
                raise ClientConfigError(
                    f"duplicate top-level key {key!r} in {path} — already set "
                    f"by {owners[key].name} in the same _client/ layer"
                )
            owners[key] = path
            merged[key] = value
    return merged, files


def _layer_conventions(client_dir: Path) -> dict[str, Path]:
    """File name -> path for one layer's `conventions/`."""
    conv = client_dir / CONVENTIONS_DIR
    if not conv.is_dir():
        return {}
    return {p.name: p for p in sorted(conv.iterdir()) if p.is_file()}


# --------------------------------------------------------------------- load
def load(area) -> ClientConfig:
    """Resolve client config for one area folder.

    Area `_client/` first, then the parent `components/_client/`; merged per
    top-level key, with `conventions/` merged per file.
    """
    area = Path(area)
    dirs = {AREA: area / CLIENT_DIR, ENGAGEMENT: area.parent / CLIENT_DIR}

    cfg = ClientConfig()
    # Engagement first so the area layer can shadow it key by key.
    for name in (ENGAGEMENT, AREA):
        client_dir = dirs[name]
        keys, files = _layer_keys(client_dir)
        conventions = _layer_conventions(client_dir)
        if files or conventions:
            cfg.present.append(name)
        for key, value in keys.items():
            cfg[key] = value
            cfg.layers[key] = name
        for fname, path in conventions.items():
            cfg.conventions[fname] = path
            cfg.convention_layers[fname] = name
    cfg.present.sort(key=lambda n: 0 if n == AREA else 1)
    return cfg


def conventions(area) -> list[Path]:
    """Resolved `conventions/` files for an area, name-sorted (drafters)."""
    cfg = load(area)
    return [cfg.conventions[n] for n in sorted(cfg.conventions)]


def report_line(area, prefix: str = "client config") -> str:
    """Convenience: the resolution line for `area`, without keeping the dict."""
    return load(area).report_line(prefix)


# --------------------------------------------------------------------- M14
# The DOCUMENT PROFILE — which sections exist, which are hidden from the
# procedure body, which callout kinds and derived views are in play.
#
# It lives here because it is engagement config resolved by exactly the rule
# above: `profile:` is one top-level key in `_client/profile.yaml`, so
# `load(area)` merges and shadows it for free, and `.layers["profile"]` says
# which layer answered. Its THREE consumers — scaffold (enforcement point 1),
# render (enforcement point 2) and the advisor's `reprofile` guard — can all
# import this module without importing each other.
#
# ABSENT PROFILE = TODAY. `profile(area)` with no `profile:` key anywhere
# returns the full A–H set, an EMPTY `body_omit`, today's derived set (which
# does NOT include `appendix-controls`), and `configured = False`; every
# consumer short-circuits on that, so the manifest, the skeletons and the
# render stay byte-identical to pre-M14 output.
# ---------------------------------------------------------------------------

PROFILE_KEY = "profile"

#: A–H is the heading contract (M14 out of scope: reordering / renaming).
ALL_SECTIONS = ["A", "B", "C", "D", "E", "F", "G", "H"]
#: Sections no engagement may drop: scope, card, steps.
MANDATORY_SECTIONS = ["A", "B", "E"]
#: The section whose callouts would vanish if it left the body with no register.
CONTROLS_SECTION = "F"
#: The register that catches them (M14 `appendix-controls`).
CONTROLS_REGISTER = "appendix-controls"

#: Today's callout kinds — the `callouts.py` LABEL→prefix map, in reading order.
ALL_CALLOUTS = ["CONTROL", "VALIDATION REQUIRED", "PAIN POINT",
                "IMPROVEMENT OPPORTUNITY", "SCREENSHOT PLACEHOLDER"]

#: Today's derived set, as `derived_kind` values (the manifest's vocabulary).
DEFAULT_DERIVED = ["procedure-index", "role-dictionary", "systems",
                   "dependencies", "raci", "appendix-a", "gap-log",
                   "screenshot-index"]
#: Every derived kind a profile may name — today's set plus M14's new register.
ALL_DERIVED = DEFAULT_DERIVED + [CONTROLS_REGISTER]

#: The spec writes the derived set in READER shorthand (`index`, `appendix-b`);
#: the manifest speaks `derived_kind`. Accept both and canonicalize to the
#: manifest's vocabulary, so one profile cannot mean two things.
DERIVED_ALIASES = {
    "index": "procedure-index",
    "procedure-index": "procedure-index",
    "roles": "role-dictionary",
    "role-dictionary": "role-dictionary",
    "appendix-b": "gap-log",
    "gap-log": "gap-log",
    "appendix-c": "screenshot-index",
    "screenshot-index": "screenshot-index",
    "controls": CONTROLS_REGISTER,
}

#: Inline step tags. Python never enforces these — they are the drafter's
#: vocabulary — but the profile is their one home, so they resolve here.
DEFAULT_INLINE_TAGS = ["System / Tool", "Navigation Path", "Fields / Parameters",
                       "Expected Result", "Evidence Required"]

PROFILE_FIELDS = ("sections", "body_omit", "callouts", "derived", "inline_tags")


class ProfileError(ClientConfigError):
    """A malformed document profile. Fail-loud and NAMED: the profile decides
    document shape, so a typo in it must stop the run, never quietly reshape
    the deliverable."""


@dataclass
class Profile:
    """The resolved document profile for one area.

    `configured` is False when no layer supplied a `profile:` key at all — the
    "absent file → today's behavior" case every consumer short-circuits on.
    """

    sections: list[str] = field(default_factory=lambda: list(ALL_SECTIONS))
    body_omit: list[str] = field(default_factory=list)
    callouts: list[str] = field(default_factory=lambda: list(ALL_CALLOUTS))
    derived: list[str] = field(default_factory=lambda: list(DEFAULT_DERIVED))
    inline_tags: list[str] = field(default_factory=lambda: list(DEFAULT_INLINE_TAGS))
    configured: bool = False
    layer: str | None = None

    # ---- what the two enforcement points ask ------------------------------
    def dropped_sections(self) -> set[str]:
        """Sections that do not exist at all (scaffold omits, render strips)."""
        return set(ALL_SECTIONS) - set(self.sections)

    def hidden_sections(self) -> set[str]:
        """Sections absent from the rendered procedure BODY: the ones that do
        not exist, plus the ones `body_omit` keeps out of it. Render's one
        question; scaffold must never ask it (a `body_omit` section is
        scaffolded, drafted and aggregated exactly as now)."""
        return self.dropped_sections() | set(self.body_omit)

    def dropped_callouts(self) -> set[str]:
        return set(ALL_CALLOUTS) - set(self.callouts)

    def wants(self, derived_kind: str) -> bool:
        return derived_kind in self.derived

    def layer_label(self) -> str:
        return LAYER_LABELS[self.layer]

    def report_line(self, prefix: str = "document profile") -> str:
        """The one line every stage that reads the profile prints.

        Layer provenance first (the M13 reporting shape), then the shape facts
        a surprised reader needs — but only when a profile is actually in play.
        """
        if not self.configured:
            return f"{prefix}: none (full A–H, nothing omitted)"
        line = f"{prefix}: {self.layer_label()} — sections {''.join(self.sections)}"
        if self.body_omit:
            line += f", body_omit {''.join(self.body_omit)}"
        return line


def _string_list(raw, key: str, where: str) -> list[str]:
    """A profile field as a list of non-empty strings. Scalars are accepted as
    a one-item list (the same tolerance `touches` has); anything else stops."""
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        raise ProfileError(
            f"{where}: `{key}:` must be a list of strings (got "
            f"{type(raw).__name__})"
        )
    out: list[str] = []
    for item in raw:
        if not isinstance(item, (str, int)):
            raise ProfileError(
                f"{where}: `{key}:` entries must be strings (got "
                f"{type(item).__name__})"
            )
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def _dedupe(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def parse_profile(raw, where: str = "_client/profile.yaml",
                  layer: str | None = None) -> Profile:
    """Validate one `profile:` mapping into a `Profile`. Fail-loud and named.

    Every error names the offending value and why it cannot stand, because the
    person reading it is hand-editing a five-line YAML file and the failure
    mode this replaces is a silently reshaped client deliverable.
    """
    if raw is None:
        return Profile()
    if not isinstance(raw, dict):
        raise ProfileError(
            f"{where}: `profile:` must be a mapping of "
            f"{', '.join(PROFILE_FIELDS)} (got {type(raw).__name__})"
        )
    unknown = sorted(k for k in raw if k not in PROFILE_FIELDS)
    if unknown:
        raise ProfileError(
            f"{where}: unknown profile field(s) {', '.join(unknown)} "
            f"(allowed: {', '.join(PROFILE_FIELDS)})"
        )

    # ---- sections -------------------------------------------------------
    if "sections" in raw:
        sections = _dedupe(s.upper() for s in _string_list(raw["sections"],
                                                           "sections", where))
        bad = [s for s in sections if s not in ALL_SECTIONS]
        if bad:
            raise ProfileError(
                f"{where}: `sections:` names {', '.join(bad)}, which is not a "
                f"section — A–H is the heading contract (renaming and "
                f"reordering are out of scope)"
            )
        missing = [s for s in MANDATORY_SECTIONS if s not in sections]
        if missing:
            raise ProfileError(
                f"{where}: `sections:` omits mandatory section(s) "
                f"{', '.join(missing)} — A (scope), B (quick reference) and "
                f"E (the steps) are what makes a procedure a procedure"
            )
        # Canonical document order, whatever order the human typed.
        sections = [s for s in ALL_SECTIONS if s in sections]
    else:
        sections = list(ALL_SECTIONS)

    # ---- body_omit ------------------------------------------------------
    body_omit = _dedupe(s.upper() for s in _string_list(raw.get("body_omit"),
                                                        "body_omit", where))
    absent = [s for s in body_omit if s not in sections]
    if absent:
        raise ProfileError(
            f"{where}: `body_omit:` names section(s) {', '.join(absent)} "
            f"absent from `sections:` ({''.join(sections)}) — omitting "
            f"something that does not exist is a profile error, not a no-op"
        )
    body_omit = [s for s in ALL_SECTIONS if s in body_omit]

    # ---- callouts -------------------------------------------------------
    if "callouts" in raw:
        callouts = _dedupe(c.upper() for c in _string_list(raw["callouts"],
                                                           "callouts", where))
        bad = [c for c in callouts if c not in ALL_CALLOUTS]
        if bad:
            raise ProfileError(
                f"{where}: `callouts:` names unknown callout kind(s) "
                f"{', '.join(repr(b) for b in bad)} (known: "
                f"{', '.join(ALL_CALLOUTS)})"
            )
        callouts = [c for c in ALL_CALLOUTS if c in callouts]
    else:
        callouts = list(ALL_CALLOUTS)

    # ---- derived --------------------------------------------------------
    if "derived" in raw:
        named = _string_list(raw["derived"], "derived", where)
        derived: list[str] = []
        for item in named:
            key = item.strip().lower()
            kind = DERIVED_ALIASES.get(key, key)
            if kind not in ALL_DERIVED:
                raise ProfileError(
                    f"{where}: `derived:` names unknown component {item!r} "
                    f"(known: {', '.join(ALL_DERIVED)})"
                )
            derived.append(kind)
        derived = _dedupe(derived)
        derived = [k for k in ALL_DERIVED if k in derived]
    else:
        derived = list(DEFAULT_DERIVED)

    # ---- the one cross-field rule that protects the deliverable ---------
    # `F` out of the body with no register means the controls are simply gone
    # from the document: F is a SECTION, so unlike H (Appendix A) it has no
    # destination unless the profile asks for one.
    if CONTROLS_SECTION in body_omit and CONTROLS_REGISTER not in derived:
        raise ProfileError(
            f"{where}: `body_omit:` hides section {CONTROLS_SECTION} from the "
            f"procedure body but `derived:` does not include "
            f"`{CONTROLS_REGISTER}` — the controls would vanish from the "
            f"document entirely. Add `{CONTROLS_REGISTER}` to `derived:` (the "
            f"register that collects the CONTROL callouts), or stop omitting "
            f"{CONTROLS_SECTION}."
        )

    inline_tags = (_string_list(raw["inline_tags"], "inline_tags", where)
                   if "inline_tags" in raw else list(DEFAULT_INLINE_TAGS))

    return Profile(sections=sections, body_omit=body_omit, callouts=callouts,
                   derived=derived, inline_tags=_dedupe(inline_tags),
                   configured=True, layer=layer)


def profile(area) -> Profile:
    """Resolve the document profile for one area folder (M14).

    Reads the `profile:` key through `load(area)`, so an engagement-wide
    `components/_client/profile.yaml` covers every area and an area's own
    `_client/profile.yaml` shadows it whole. No `profile:` key anywhere →
    today's shape, `configured = False`.
    """
    cfg = load(area)
    if PROFILE_KEY not in cfg:
        return Profile()
    layer = cfg.layers.get(PROFILE_KEY)
    where = f"{LAYER_LABELS[layer]} profile.yaml" if layer else "profile.yaml"
    return parse_profile(cfg[PROFILE_KEY], where, layer)


# --------------------------------------------------------------------------- #
# M17 — STICKY HOLDS
#
# `hold:` is engagement config resolved by exactly the same rule as `profile:`
# — one top-level key (conventionally `_client/consult.yaml`), so `load(area)`
# merges it and an area's own list SHADOWS the engagement's whole (a list is one
# key; there is no per-item merge, for the same reason nothing else deep-merges
# here). Provenance is therefore per-LIST, which is what `held_by` reports.
#
# The ACTION VOCABULARY lives in the caller (orchestrate.py owns the ladder), so
# it is passed in: this module must never import the advisor, and a hold list is
# only meaningful against the ladder that would honour it.
# --------------------------------------------------------------------------- #

HOLD_KEY = "hold"


class HoldError(ClientConfigError):
    """A malformed `hold:` list. Fail-loud and NAMED: a typo'd action name that
    parsed as "nothing held" would silently spend the very agents the hold was
    written to stop."""


@dataclass
class Holds:
    """Resolved sticky holds for one area.

    `actions` is the held action names in the order the human wrote them;
    `layer` is the layer whose list answered ("area" | "engagement" | None).
    """

    actions: list[str] = field(default_factory=list)
    layer: str | None = None

    def __contains__(self, action: str) -> bool:
        return action in self.actions

    def __bool__(self) -> bool:
        return bool(self.actions)

    def held_by(self, action: str) -> str | None:
        """The layer holding `action`, or None when it is not held. One list
        answers, so every held action shares its provenance."""
        return self.layer if action in self.actions else None

    def layer_label(self) -> str:
        return LAYER_LABELS[self.layer]

    def report_line(self, prefix: str = "holds") -> str:
        if not self.actions:
            return f"{prefix}: none"
        return f"{prefix}: {', '.join(self.actions)} ({self.layer_label()})"


def parse_holds(raw, holdable, gates=(), where: str = "_client/consult.yaml",
                layer: str | None = None) -> Holds:
    """Validate one `hold:` list against the caller's action vocabulary.

    `holdable` is every action a hold may name; `gates` is the actions that are
    ALREADY a stop. Naming a gate is a VALIDATION ERROR, not a silent no-op:
    docs/M17 puts "holding a gate" out of scope, and of the two readings the
    spec allows, a fail-loud one is the only one that tells the author their
    line does nothing — a no-op hold on `review` reads, forever, as a policy
    that is in force.
    """
    holdable = list(holdable)
    gates = set(gates)
    if raw is None:
        return Holds(layer=layer)
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        raise HoldError(
            f"{where}: `hold:` must be a list of action names (got "
            f"{type(raw).__name__})"
        )
    actions: list[str] = []
    for item in raw:
        if not isinstance(item, str):
            raise HoldError(
                f"{where}: `hold:` entries must be action names as strings "
                f"(got {type(item).__name__})"
            )
        name = item.strip()
        if not name:
            continue
        if name in gates:
            raise HoldError(
                f"{where}: `hold:` names {name!r}, which is already a stop (a "
                f"human gate, or a terminal state that spends nothing) — "
                f"holding it would be a no-op, and a no-op line in "
                f"this file reads as a policy that is in force (docs/"
                f"M17-stage-gates.md, Out of scope). Remove it."
            )
        if name not in holdable:
            raise HoldError(
                f"{where}: `hold:` names unknown action {name!r} — a typo must "
                f"never read as \"nothing held\" (holdable: "
                f"{', '.join(holdable)})"
            )
        actions.append(name)
    return Holds(actions=_dedupe(actions), layer=layer)


def holds(area, holdable, gates=()) -> Holds:
    """Resolve sticky holds for one area folder (M17 build item 3).

    Reads the `hold:` key through `load(area)`, so an engagement-wide
    `components/_client/consult.yaml` covers every area and an area's own list
    shadows it whole. No `hold:` key anywhere → nothing held, and the advisor
    behaves exactly as it did pre-M17.
    """
    cfg = load(area)
    if HOLD_KEY not in cfg:
        return Holds()
    layer = cfg.layers.get(HOLD_KEY)
    where = f"{LAYER_LABELS[layer]} consult.yaml" if layer else "consult.yaml"
    return parse_holds(cfg[HOLD_KEY], holdable, gates, where, layer)
