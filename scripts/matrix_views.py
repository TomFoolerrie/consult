#!/usr/bin/env python3
"""
matrix_views.py — the python view writer for M38's second deliverable, the
process & controls matrix (kernel/deliverables/process-controls-matrix.yaml).

WHY A NEW MODULE AND NOT A BUILDER IN aggregate.py: aggregate.py holds v1's
seven shipped writers; this is a v2-native writer over a v2-native type, and
the M38 ruling names "a NEW view-builder module registered through the existing
`aggregate.PY_BUILDERS` registry (one-line hook)" as the sanctioned extension
mechanism. Nothing in the loader, the compiler or the renderer learns this
deliverable's name.

WHAT IT EMITS: one markdown table per taxonomy node — the derived-view idiom
(compare aggregate.build_systems / build_procedure_index: a lead-in line, then
`###` sub-headings with a fresh header row per group, `[[#slug]]` tokens for
cross-references, `—` for an empty cell). aggregate.write_derived wraps it in
the heading + `<!-- derived: … -->` marker, and render.py resolves the tokens.

  | Process Step | Owner | Systems | Inputs | Outputs | Control | Open … |

THE COLUMN VOCABULARY IS DATA, NOT CODE (the M36 shape-audit rule, honoured
rather than allowlisted). This module names NO part slug, part title, callout
label or callout prefix as a literal. Everything comes from two declared
sources:

  * `kernel.load_type("process-step")` — the part titles used as column
    headings, and the label→prefix map used to turn a binding's callout LABELS
    into the prefixes the fragments carry;
  * the DEFINITION's bindings — which parts are the IPO columns, which callout
    kinds are the control column, which are the counted open-items column, and
    which channels are the owner / systems columns. The loader's stage 2 has
    already checked every one of those names against the declaration, so a
    reshape of the type fails the definition rather than silently changing this
    table.

The only names this module types are its own BINDING NAMES (below) — the
contract between the definition file and its writer.

NODE GROUPING — the mechanical rule, decided and written down. The node→step
relation is not a declared relation yet (kernel/types/taxonomy-node.yaml says
so, and coverage_map.coverage takes `node_steps` as a parameter for exactly
this reason), so the caller owns it. This writer derives it, in this order:

  1. NODE SLUG == STEP SLUG — the L3 convention: a node whose slug is a step's
     slug covers that step, and nothing else can outbid it.
  2. A NODE THAT NAMES ITS STEPS — the L2-ish case (one node grouping several
     steps). A node covers every step it MENTIONS in its fragment text: as a
     cross-reference token (`[[slug]]` / `[[#slug]]`), as the bare step slug,
     or by the step's manifest heading. Mentions are read from the whole node
     fragment (its `scope` prose and any callout on it) because a node's
     boundary statement is prose, not a list. A step named by two nodes goes to
     the FIRST in node order (slug order) — deterministically one row, never
     two, and reconcile-style duplicate reporting is not this view's job.
  3. UNGROUPED — steps no node claims still appear, in a trailing group. A
     matrix that silently dropped a step would be worse than an ugly one.

Group ORDER follows the rows: a node sorts by the manifest position of its
first step (so the matrix reads in manifest order), ties by slug, with the
ungrouped tail last.

Python 3, stdlib + pyyaml, read-only over the area (like every builder here).
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import json
import re

from pathlib import Path

# kernel / doc_model / aggregate / definitions are imported LAZILY inside the
# functions below. aggregate.py registers this module at import time and
# kernel.py imports aggregate, so a module-level import here would close an
# import cycle — the builders' own imports are cheap and this keeps the registry
# hook a one-liner.


#: The derived kind / view-block id / definition name — one string, three roles
#: (D1's convention: a view block's id IS its derived kind).
MATRIX_KIND = "process-controls-matrix"

#: The entity type whose entities are the matrix's ROWS. A type name, not shape.
#: (The taxonomy-node fragments this view groups by are read as TEXT — their
#: mentions of a step, per rule 2 — so this writer never needs the node type's
#: declaration; coverage_map.py owns the typed read of a node.)
STEP_TYPE = "process-step"

#: Where an area keeps its taxonomy-node fragments (coverage_map's convention:
#: one file per node, the slug is the filename stem).
TAXONOMY_DIRNAME = "_taxonomy"

#: The manifest `role` that holds an area's step fragments.
STEP_ROLE = "procedure"

#: The binding names this writer expects its definition to carry. THE contract
#: between kernel/deliverables/process-controls-matrix.yaml and this module: the
#: definition says which parts/callouts/channels each column is made of, and
#: these four names say which column is which.
BINDING_IDENTITY = "step-identity"        # rows + owner/systems columns
BINDING_IO = "io-edges"                   # the IPO columns (list parts)
BINDING_CONTROLS = "control-callouts"     # the control-callout column
BINDING_OPEN = "open-items"               # the counted open-items column

#: The heading a step with no covering node lands under (see rule 3 above).
UNGROUPED_TITLE = "Ungrouped"

_TOKEN_RE = re.compile(r"\[\[#?([^\]|]+?)\]\]")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?P<item>.*\S)\s*$")
_HEADING_RE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)


# --------------------------------------------------------------------------- #
# Small local helpers (cell escaping is aggregate's, imported lazily so this
# module never participates in an import cycle with the module that registers
# it).
# --------------------------------------------------------------------------- #

def _cell(value) -> str:
    from aggregate import cell
    return cell(value)


def _registry(area: Path, filename: str, top_key: str) -> dict:
    from aggregate import load_registry
    return load_registry(area, filename, top_key)


def _binding(bindings: dict, name: str) -> dict:
    spec = (bindings or {}).get(name) or {}
    return spec if isinstance(spec, dict) else {}


def _names(spec: dict, key: str) -> list[str]:
    """A binding's `parts:` / `callouts:` / `channels:` selection as a list."""
    val = spec.get(key)
    if isinstance(val, str):
        val = [val]
    return [str(v) for v in (val or [])]


def _definition_bindings(area=None) -> dict:
    """This view's own definition's bindings — the column vocabulary.

    Used when the caller does not hand them over (aggregate's ctx does not carry
    a binding map). Loading the shipped definition is not a special case in the
    engine: it is this WRITER reading the data that describes it, the same way
    every builder here reads the declaration it is a view of."""
    import definitions
    return definitions.load_definition(MATRIX_KIND, area=area).bindings


# --------------------------------------------------------------------------- #
# Reading the area (read-only)
# --------------------------------------------------------------------------- #

def _kernel():
    import kernel
    return kernel


def _manifest(area: Path) -> dict:
    data = json.loads((area / "manifest.json").read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _steps(area: Path, tdecl) -> list[dict]:
    """The area's step entities in MANIFEST ORDER (the binding's `order`).

    Each entry: slug, heading, the parsed Entity, and the manifest position."""
    components = _manifest(area).get("components") or []
    rows = []
    for pos, comp in enumerate(components):
        if not isinstance(comp, dict) or comp.get("role") != STEP_ROLE:
            continue
        slug = str(comp.get("slug") or "")
        fpath = area / str(comp.get("file") or "")
        if not slug or not fpath.is_file():
            continue
        entity = _kernel().parse_entity(fpath.read_text(encoding="utf-8"), tdecl,
                                     slug=slug)
        rows.append({"slug": slug,
                     "heading": str(comp.get("heading") or slug),
                     "entity": entity,
                     "order": (comp.get("order", pos), pos)})
    rows.sort(key=lambda r: r["order"])
    return rows


def _nodes(area: Path) -> list[dict]:
    """The area's taxonomy nodes, slug order: slug, title, full fragment text."""
    tdir = area / TAXONOMY_DIRNAME
    out = []
    for path in sorted(tdir.glob("*.md")) if tdir.is_dir() else []:
        text = path.read_text(encoding="utf-8")
        m = _HEADING_RE.search(text)
        title = m.group("title").strip() if m else path.stem.replace("-", " ").title()
        out.append({"slug": path.stem, "title": title, "text": text})
    return out


# --------------------------------------------------------------------------- #
# The node -> step relation (the three rules of the module docstring)
# --------------------------------------------------------------------------- #

def _mentions(node_text: str, step: dict) -> bool:
    """Does this node fragment NAME this step? (rule 2)"""
    slug = step["slug"]
    if slug in {t.strip() for t in _TOKEN_RE.findall(node_text)}:
        return True
    if re.search(r"(?<![\w-])%s(?![\w-])" % re.escape(slug), node_text):
        return True
    heading = step["heading"].strip()
    return bool(heading) and heading in node_text


def group_step_slugs(steps: list[dict],
                     nodes: list[dict]) -> list[tuple[str, list]]:
    """`[(node SLUG, [step, …]), …]` — the grouping keyed by node identity.

    The slug-keyed relation (M57 Part C): two taxonomy nodes may share a TITLE
    (two "Exceptions" sub-cycles), and a title-keyed round-trip silently hands
    both nodes' steps to whichever slug claimed the title first. The slug is
    the node's identity; the title is its display. Unclaimed steps form a
    trailing group keyed by the empty string."""
    owner: dict[str, str] = {}
    for step in steps:
        for node in nodes:                          # rule 1
            if node["slug"] == step["slug"]:
                owner[step["slug"]] = node["slug"]
                break
        if step["slug"] in owner:
            continue
        for node in nodes:                          # rule 2, slug order
            if _mentions(node["text"], step):
                owner[step["slug"]] = node["slug"]
                break

    grouped: dict[str, list] = {}
    for step in steps:
        grouped.setdefault(owner.get(step["slug"], ""), []).append(step)

    ordered = sorted((key for key in grouped if key),
                     key=lambda key: (grouped[key][0]["order"], key))
    out = [(key, grouped[key]) for key in ordered]
    if "" in grouped:                               # rule 3
        out.append(("", grouped[""]))
    return out


def group_steps(steps: list[dict], nodes: list[dict]) -> list[tuple[str, list]]:
    """`[(group title, [step, …]), …]` — the grouping, mechanically.

    Rule 1 (slug identity) wins over rule 2 (naming); a step claimed by two
    naming nodes goes to the first in slug order; unclaimed steps form the
    trailing `Ungrouped` group. Group order = the manifest position of each
    group's first step, so the matrix reads in row order.

    A DISPLAY view over `group_step_slugs` (M57): the slug-keyed relation is
    the identity; this projects each slug to its title for the table."""
    titles = {n["slug"]: n["title"] for n in nodes}
    return [(titles.get(slug, slug) if slug else UNGROUPED_TITLE, group)
            for slug, group in group_step_slugs(steps, nodes)]


# --------------------------------------------------------------------------- #
# Cells (every column's vocabulary comes from the declaration or the binding)
# --------------------------------------------------------------------------- #

def _prefixes(tdecl, labels) -> list[str]:
    """The callout PREFIXES a binding's callout LABELS select.

    A binding may name either half (stage 2 admits both), so match on both and
    keep the declaration's order — no label and no prefix is typed here."""
    wanted = set(labels)
    return [c.prefix for c in tdecl.callouts
            if c.label in wanted or c.prefix in wanted]


def _labels(tdecl, labels) -> list[str]:
    wanted = set(labels)
    return [c.label for c in tdecl.callouts
            if c.label in wanted or c.prefix in wanted]


def _ids(step: dict, prefix: str, disp: dict) -> list[str]:
    """The display ids of this step's callouts of one kind, document order."""
    return [disp.get((step["slug"], c["id"]), c["id"])
            for c in step["entity"].callout_dicts() if c["prefix"] == prefix]


def _channel_names(step: dict, channel: str, registry: dict) -> list[str]:
    """The display names behind a step's consult-meta slugs on one channel.

    A slug with no registry entry passes through AS WRITTEN — aggregate's
    posture (a missing registry entry is a top-up worklist item, never a
    dropped fact)."""
    out = []
    for slug in step["entity"].bindings().get(channel, []):
        entry = registry.get(slug) or {}
        out.append(str(entry.get("name") or slug))
    return out


def _list_items(step: dict, part: str) -> str:
    """One IPO cell: the authored list items of a part, compactly.

    `[[slug]]` cross-reference tokens inside an item are kept ONLY when the
    slug is a step of this area (render.py resolves those to a display number
    and raises on anything else); an edge pointing outside the area is shown as
    its bare name instead of taking the render down.

    A HARD-WRAPPED item is one item: drafters wrap long edges over several
    lines, so a continuation line is appended to the item above rather than
    dropped (the same tolerance aggregate's callout parser shows a wrapped
    field value — truncating an edge mid-sentence would be worse than a long
    cell)."""
    body = step["entity"].parts_bodies().get(part, "") or ""
    items: list[str] = []
    for line in body.splitlines():
        m = _LIST_ITEM_RE.match(line)
        if m:
            items.append(m.group("item").strip())
        elif items and line.strip():
            items[-1] = f"{items[-1]} {line.strip()}"
    return "; ".join(items)


def _flatten_tokens(text: str, known: set[str]) -> str:
    def repl(m):
        slug = m.group(1).strip()
        return m.group(0) if slug in known else slug
    return _TOKEN_RE.sub(repl, text)


# --------------------------------------------------------------------------- #
# The builder
# --------------------------------------------------------------------------- #

def build_matrix(area, bindings: dict | None = None) -> str:
    """The matrix's section BODY (markdown), for one area. Read-only."""
    area = Path(area)
    bindings = bindings if bindings is not None else _definition_bindings(area)

    import kernel

    tdecl = kernel.load_type(STEP_TYPE)
    part_titles = {p.slug: p.title for p in tdecl.parts}

    identity = _binding(bindings, BINDING_IDENTITY)
    io_parts = [p for p in _names(_binding(bindings, BINDING_IO), "parts")
                if p in part_titles]
    control_prefixes = _prefixes(
        tdecl, _names(_binding(bindings, BINDING_CONTROLS), "callouts"))
    control_labels = _labels(
        tdecl, _names(_binding(bindings, BINDING_CONTROLS), "callouts"))
    open_spec = _binding(bindings, BINDING_OPEN)
    open_prefixes = _prefixes(tdecl, _names(open_spec, "callouts"))
    open_labels = _labels(tdecl, _names(open_spec, "callouts"))
    counted = bool(open_spec.get("count"))

    channels = _names(identity, "channels")
    registries = {}
    for decl in tdecl.channels:
        if decl.name in channels:
            registries[decl.name] = _registry(area, decl.registry, decl.name)
    owner_channel = channels[0] if channels else None
    other_channels = [c for c in channels[1:]]

    steps = _steps(area, tdecl)
    known = {s["slug"] for s in steps}
    nodes = _nodes(area)

    import doc_model
    disp = doc_model.callout_display_ids(area)

    headers = ["Process Step"]
    if owner_channel:
        headers.append(f"Owner ({owner_channel})")
    headers += [c.title() for c in other_channels]
    headers += [part_titles[p] for p in io_parts]
    headers.append(" / ".join(lb.title() for lb in control_labels) or "Control")
    open_header = "Open " + (" / ".join(lb.title() for lb in open_labels)
                             or "Items")
    headers.append(open_header)

    rule = "|" + "|".join("---" for _ in headers) + "|"
    header_row = "| " + " | ".join(headers) + " |"

    lines = ["_One row per process step, grouped by the taxonomy node that "
             "covers it. Owner and systems come from each step's recorded "
             "bindings; inputs and outputs are the step's own process edges; "
             "the last column counts what is still open on that step._", ""]

    if not steps:
        lines += ["_No process steps recorded in this area._"]
        return "\n".join(lines)

    for title, rows in group_steps(steps, nodes):
        lines += [f"### {title}", "", header_row, rule]
        for step in rows:
            cells = [f"{step['heading']} ([[#{step['slug']}]])"]
            if owner_channel:
                owners = _channel_names(step, owner_channel,
                                        registries.get(owner_channel, {}))
                cells.append(_cell(owners[0] if owners else ""))
            for channel in other_channels:
                cells.append(_cell(", ".join(_channel_names(
                    step, channel, registries.get(channel, {})))))
            for part in io_parts:
                cells.append(_cell(_flatten_tokens(_list_items(step, part),
                                                   known)))
            ctrl = []
            for prefix in control_prefixes:
                ctrl += _ids(step, prefix, disp)
            cells.append(_cell(", ".join(ctrl)))
            open_bits = []
            for prefix, label in zip(open_prefixes, open_labels):
                ids = _ids(step, prefix, disp)
                if not ids:
                    continue
                open_bits.append(f"{len(ids)} {label.title()} "
                                 f"({', '.join(ids)})" if counted
                                 else ", ".join(ids))
            cells.append(_cell("; ".join(open_bits)))
            lines.append("| " + " | ".join(cells) + " |")
        lines.append("")

    return "\n".join(lines).rstrip()


def build_process_controls_matrix(ctx) -> str:
    """The `PY_BUILDERS` entry point (kind `process-controls-matrix`).

    Same contract as aggregate's shipped builders — one `ctx` mapping in, the
    section body out — reading two ctx keys: `area` (which area to build over)
    and, when the caller has it, `bindings` (the definition's binding map). With
    no `bindings` in ctx this writer loads its own definition for them; with no
    `area` it says so by name rather than guessing."""
    area = (ctx or {}).get("area")
    if not area:
        raise KeyError(
            f"{MATRIX_KIND}: the builder ctx carries no 'area' — this view is "
            f"built over an engagement area (see matrix_views.build_matrix)")
    return build_matrix(area, (ctx or {}).get("bindings"))
