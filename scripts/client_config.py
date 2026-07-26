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

`_reference/` is deliberately NOT part of this: it is agent-proposed and
human-confirmed per area, and sharing it would let one area's low-confidence
guess become another area's fact.

Python 3, stdlib + pyyaml.
"""

from __future__ import annotations

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
