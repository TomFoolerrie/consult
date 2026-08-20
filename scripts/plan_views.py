#!/usr/bin/env python3
"""
plan_views.py — the three python view writers M40 Part B owes the two shipped
definitions that had never rendered: the information request list
(kernel/deliverables/information-request.yaml, M37) and the findings report
(kernel/deliverables/findings-report.yaml, M39).

WHY A NEW MODULE AND NOT BUILDERS IN aggregate.py: same ruling matrix_views.py
cites — a v2-native writer over v2-native machinery belongs in a new builder
module registered through `aggregate.PY_BUILDERS` (one import + one entry per
kind). Nothing in the loader, the compiler or the renderer learns these three
names; the manifest's `derived_kind` and the definition's view-block `id` are
the same string, and that string is the registry key.

WHAT THE THREE EMIT (all in aggregate's derived-view idiom: an italic lead-in
line, then list content, `—` for an empty cell, `[[#slug]]` tokens ONLY for
step slugs of THIS area, which render.py can resolve):

  information-requests   one entry per taxonomy node the coverage map reports
                         at one of the binding's statuses: the node, its
                         status, the evidence already held, and the ask.
  open-validations       one entry per process step carrying the bound callout
                         kind, in manifest order, with the SRC attribution the
                         drafters wrote into each callout body.
  findings-by-theme      the accepted findings, grouped by theme, each claim
                         with its grounds as citations.

VOCABULARY COMES FROM THE BINDINGS AND THE DECLARATIONS, NEVER FROM HERE (the
M36 shape-audit rule, honoured rather than allowlisted). This module names no
part slug, no part title, no callout label and no callout prefix. The callout
kind `open-validations` is a register of is whatever the definition's `step-gaps`
binding names, translated into the prefix the fragments actually carry through
`kernel.load_type(...).callouts` — matrix_views' `_prefixes` discipline, reused
rather than re-typed. The coverage statuses the request list selects are
whatever the `requests` binding names. The finding status is not selectable at
all: the register is reached only through `findings.renderable` /
`findings.by_theme`, which are accepted-only by construction, so a proposed or
rejected claim is STRUCTURALLY unable to reach a rendered document (M40's named
review risk: register leakage).

THE ONE ALIAS THE REQUEST LIST EXPANDS, and who owns it since M53: the
surveyor's sufficiency word `thin` (scripts/definitions.py's
`_ALLOWED_COVERAGE_STATUSES` comment states the sentence it collapses to).
`coverage_map.coverage()` never returns `thin`, so a consumer of a `coverage:`
binding has to collapse it; the expansion lives with the shared kind resolvers
(`kinds.selected_statuses`), and this module delegates to it. No status word
is typed here — every one of them arrives from the binding.

GROUPING IS NOT REDERIVED HERE. `coverage(root, node_steps)` takes the
node→step relation as a parameter (it is not a declared relation yet), and
matrix_views already owns the mechanical rule with its three documented
tie-breaks. This module IMPORTS that machinery (`_steps`, `_nodes`,
`group_steps`) instead of copying it, so the request list and the matrix can
never disagree about which steps a node covers.

Read-only over the engagement (like every builder here — `write_derived` owns
the file write). Python 3, stdlib + the engine's own modules.
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import re

from pathlib import Path

# kernel / definitions / findings / coverage_map / doc_model are imported LAZILY
# inside the functions: aggregate.py registers this module at import time and
# kernel.py imports aggregate, so a module-level import would close an import
# cycle (matrix_views.py's note, same reason).

#: The three derived kinds / view-block ids / `PY_BUILDERS` keys. One string,
#: three roles (D1's convention).
REQUESTS_KIND = "information-requests"
VALIDATIONS_KIND = "open-validations"
FINDINGS_KIND = "findings-by-theme"

#: Which DEFINITION each view belongs to — the file whose `bindings:` block
#: carries that view's vocabulary, loaded when the ctx does not hand it over
#: (matrix_views._definition_bindings' pattern; aggregate's ctx carries no
#: binding map).
REQUESTS_DEFINITION = "information-request"
FINDINGS_DEFINITION = "findings-report"

#: The binding names this module expects those definitions to carry. THE
#: contract between the two YAML files and this writer — the only names typed
#: here, exactly as in matrix_views.
BINDING_REQUESTS = "requests"        # the coverage feeder (M37)
BINDING_STEP_GAPS = "step-gaps"      # the step-level callout feeder (M37)
BINDING_FINDINGS = "accepted-findings"   # the register feeder (M39)

#: The surveyor's alias, and what it collapses to — owned by the shared
#: resolver home since M53 (kinds.py), re-exported here for older importers.
import kinds as _kinds  # noqa: E402  (no cycle: kinds imports no engine loader)

THIN_ALIAS = _kinds.THIN_ALIAS
THIN_MEANS = _kinds.THIN_MEANS

#: An SRC id as it appears in a callout body — coverage_map.SRC_ID_RE's grammar,
#: mirrored here rather than imported so a view never drags the coverage join in
#: just to highlight a citation.
_SRC_ID_RE = re.compile(r"\bSRC-[A-Za-z0-9]+\b")


# --------------------------------------------------------------------------- #
# Bindings (the vocabulary seam)
# --------------------------------------------------------------------------- #

def _bindings(ctx, definition: str, area) -> dict:
    """The binding map for a view: the caller's if it has one, else the view's
    own definition's."""
    given = (ctx or {}).get("bindings")
    if given:
        return given
    import definitions
    return definitions.load_definition(definition, area=area).bindings


def _spec(bindings: dict, name: str) -> dict:
    from matrix_views import _binding
    return _binding(bindings or {}, name)


def _values(spec: dict, key: str) -> list[str]:
    from matrix_views import _names
    return _names(spec, key)


def _area_of(ctx, kind: str) -> Path:
    """The area this view is built over, or a refusal naming the kind."""
    area = (ctx or {}).get("area")
    if not area:
        raise KeyError(
            f"{kind}: the builder ctx carries no 'area' — this view is built "
            f"over an engagement area (see plan_views)")
    return Path(area)


def _root_of(area: Path) -> Path:
    """The engagement root for an area.

    `engagement.py` publishes no area→root helper (its own root derivations are
    private to the intake router), and the derivation is published once from the
    shared resolver home since M53 — `kinds.engagement_root`, itself the
    DEFINITION layer's `definitions._engagement_root` read ("the parent of the
    `components/` directory the area lives in", M13's layout). This private
    name delegates to it for this module's own callers. A view of an area
    outside an engagement tree refuses by name instead of reading the
    filesystem root."""
    return _kinds.engagement_root(area)


# --------------------------------------------------------------------------- #
# 1. information-requests — the coverage feeder
# --------------------------------------------------------------------------- #

def _selected_statuses(spec: dict) -> set[str]:
    """The coverage statuses this binding selects, with `thin` expanded.

    Every word here came out of the definition file; the expansion is the one
    documented alias, owned by `kinds.selected_statuses` since M53 — this
    private name delegates for this module's own callers."""
    return _kinds.selected_statuses(spec)


def node_steps(area: Path) -> dict[str, list[str]]:
    """`{node slug: [step slug, …]}` for one area — matrix_views' grouping.

    Imported, never re-derived: `group_step_slugs` carries the node SLUG
    through (M57 Part C — the old title-keyed round-trip collapsed two nodes
    sharing an H2 title onto the first slug, and coverage then reported the
    losing node as covered when it wasn't). The trailing ungrouped group
    belongs to no node and simply has no key here — an unclaimed step is not
    evidence for any node."""
    import kernel
    from matrix_views import STEP_TYPE, _nodes, _steps, group_step_slugs

    nodes = _nodes(area)
    tdecl = kernel.load_type(STEP_TYPE)

    out: dict[str, list[str]] = {}
    for slug, steps in group_step_slugs(_steps(area, tdecl), nodes):
        if slug:
            out[slug] = [s["slug"] for s in steps]
    return out


def _node_evidence(area: Path, slug: str, steps: list[str]) -> list[str]:
    """The SRC ids already held on a node: cited by its own fragment or by any
    step it covers. Document order, de-duplicated — this is the "what we hold"
    half of an ask (asking again for what we have is the fastest way to lose a
    client's patience)."""
    from matrix_views import TAXONOMY_DIRNAME

    texts = []
    node_file = area / TAXONOMY_DIRNAME / f"{slug}.md"
    if node_file.is_file():
        texts.append(node_file.read_text(encoding="utf-8"))
    import json
    try:
        manifest = json.loads((area / "manifest.json").read_text(
            encoding="utf-8"))
    except (OSError, ValueError):
        manifest = {}
    files = {str(c.get("slug")): str(c.get("file") or "")
             for c in (manifest.get("components") or [])
             if isinstance(c, dict) and c.get("slug")}
    for step in steps:
        path = area / files.get(step, "")
        if files.get(step) and path.is_file():
            texts.append(path.read_text(encoding="utf-8"))

    seen: list[str] = []
    for text in texts:
        for sid in _SRC_ID_RE.findall(text):
            if sid not in seen:
                seen.append(sid)
    return seen


def _node_asks(area: Path, slug: str) -> list[str]:
    """The open questions the node fragment itself records — its callout
    bodies, in document order.

    The node type declares exactly ONE callout kind (coverage_map says so, and
    says why), so this reads every callout on the node rather than naming a
    label. These are the surveyor's own words for what is unsettled, which is
    what a client-facing ask should carry; a node with none gets the generic ask
    below."""
    import kernel
    import coverage_map
    from matrix_views import TAXONOMY_DIRNAME

    path = area / TAXONOMY_DIRNAME / f"{slug}.md"
    if not path.is_file():
        return []
    tdecl = kernel.load_type(coverage_map.NODE_TYPE)
    try:
        entity = kernel.parse_entity(path.read_text(encoding="utf-8"), tdecl,
                                     slug=slug)
    except Exception:
        return []
    asks = []
    for callout in entity.callout_dicts():
        text = " ".join(
            [str(callout.get("text") or "")]
            + [str(v) for v in (callout.get("fields") or {}).values()]).strip()
        if text:
            asks.append(" ".join(text.split()))
    return asks


def build_information_requests(ctx) -> str:
    """`information-requests` — the M37 coverage feeder's section body.

    Reads `ctx["area"]` and, when the caller has it, `ctx["bindings"]`.
    `coverage_map.coverage()` is computed ON DEMAND over the whole engagement
    (nothing is persisted for this view to read — the charter's guardrail), and
    the nodes it reports at the binding's statuses become the asks. Read-only.
    """
    import coverage_map
    from matrix_views import _cell, _nodes

    area = _area_of(ctx, REQUESTS_KIND)
    spec = _spec(_bindings(ctx, REQUESTS_DEFINITION, area), BINDING_REQUESTS)
    wanted = _selected_statuses(spec)

    root = _root_of(area)
    relation = node_steps(area)
    cov = coverage_map.coverage(root, relation)

    titles = {n["slug"]: n["title"] for n in _nodes(area)}
    picked = [(slug, cov[slug]) for slug in titles if cov.get(slug) in wanted]

    lines = ["_Each request below names a process area we could not yet "
             "document with confidence, what we already hold on it, and what "
             "we are asking for. Nothing here is a finding: these are the "
             "questions we would rather ask than guess at._", ""]
    if not picked:
        lines += ["—", "",
                  "_Every area in scope is evidenced well enough to draft; no "
                  "information requests outstanding._"]
        return "\n".join(lines)

    for slug, status in picked:
        held = _node_evidence(area, slug, relation.get(slug) or [])
        asks = _node_asks(area, slug)
        lines += [f"### {titles.get(slug, slug)}", ""]
        lines += [f"- **Coverage:** {_cell(status)}"]
        lines += [f"- **What we hold:** {_cell(', '.join(held)) or '—'}"]
        if asks:
            lines += ["- **What we are asking for:**"]
            lines += [f"    - {_cell(ask)}" for ask in asks]
        else:
            lines += ["- **What we are asking for:** a walkthrough, an "
                      "existing SOP or a short written answer covering this "
                      "area end to end — we hold no settled account of it yet."]
        lines.append("")

    return "\n".join(lines).rstrip()


# --------------------------------------------------------------------------- #
# 2. open-validations — the step-level callout feeder
# --------------------------------------------------------------------------- #

def build_open_validations(ctx) -> str:
    """`open-validations` — the bound callout kind, per step, in manifest order.

    The binding names the callout kind by LABEL or by prefix (stage 2 admits
    either); `matrix_views._prefixes` / `_labels` turn that into what the
    fragments carry, so no label and no prefix is typed in this module. Ids are
    shown through `doc_model.callout_display_ids` — the document-global
    numbering authority, the same map render.py uses in the body — and each
    entry keeps the SRC attribution the drafter wrote, because a validation
    point without its sources is a question with no provenance. Read-only."""
    import doc_model
    import kernel
    from matrix_views import (STEP_TYPE, _cell, _ids, _labels, _prefixes,
                              _steps)

    area = _area_of(ctx, VALIDATIONS_KIND)
    spec = _spec(_bindings(ctx, REQUESTS_DEFINITION, area), BINDING_STEP_GAPS)

    tdecl = kernel.load_type(STEP_TYPE)
    wanted = _values(spec, "callouts")
    prefixes = _prefixes(tdecl, wanted)
    labels = _labels(tdecl, wanted)
    kind_name = " / ".join(lb.title() for lb in labels) or "open item"

    disp = doc_model.callout_display_ids(area)
    steps = _steps(area, tdecl)

    lines = [f"_Every {kind_name} still open on a process step, in document "
             f"order, with the sources behind it. Each one is a point two "
             f"readings of the process disagree on, or one no source we hold "
             f"settles._", ""]
    if not steps or not prefixes:
        lines += ["—"]
        return "\n".join(lines)

    any_row = False
    for step in steps:
        rows = []
        for prefix in prefixes:
            mine = [c for c in step["entity"].callout_dicts()
                    if c["prefix"] == prefix]
            # `_ids` is matrix_views' display-id read for one kind, in document
            # order — the same list `mine` is in, so they zip.
            for callout, shown in zip(mine, _ids(step, prefix, disp)):
                text = " ".join(
                    [str(callout.get("text") or "")]
                    + [str(v) for v in (callout.get("fields") or {}).values()])
                text = " ".join(text.split())
                srcs = []
                for sid in _SRC_ID_RE.findall(text):
                    if sid not in srcs:
                        srcs.append(sid)
                rows.append((shown, text, srcs))
        if not rows:
            continue
        any_row = True
        lines += [f"### {step['heading']} ([[#{step['slug']}]])", ""]
        for shown, text, srcs in rows:
            attribution = f" _(sources: {', '.join(srcs)})_" if srcs else ""
            lines.append(f"- **{shown}** — {_cell(text) or '—'}{attribution}")
        lines.append("")

    if not any_row:
        lines += ["—", "",
                  f"_No {kind_name} recorded against any process step in this "
                  f"area._"]
    return "\n".join(lines).rstrip()


# --------------------------------------------------------------------------- #
# 3. findings-by-theme — the register feeder
# --------------------------------------------------------------------------- #

def build_findings_by_theme(ctx) -> str:
    """`findings-by-theme` — the accepted findings, grouped by theme.

    The register is reached ONLY through `findings.by_theme` /
    `findings.renderable` (accepted-only by construction), so no status filter
    exists in this builder to get wrong. The binding's `group_by` says which
    grouping the definition asked for; a binding that groups by nothing gets one
    flat list rather than an invented section per finding. An engagement with no
    accepted findings gets a "not yet" line — the expected state before the
    analysis verbs have run, and a report, never a crash. Read-only."""
    import findings
    from matrix_views import _cell

    area = _area_of(ctx, FINDINGS_KIND)
    spec = _spec(_bindings(ctx, FINDINGS_DEFINITION, area), BINDING_FINDINGS)
    group_by = str(spec.get("group_by") or "")

    root = _root_of(area)

    lines = ["_Our assessment of the current state, grouped by theme. Each "
             "claim lists the grounds it rests on — the sources, process "
             "points and process steps behind it — so every claim can be "
             "traced back to its evidence. Only reviewed and accepted findings "
             "appear here._", ""]

    def _entry(entry: dict) -> list[str]:
        grounds = [str(g) for g in (entry.get("grounds") or [])]
        cite = f" _(grounds: {', '.join(grounds)})_" if grounds else " _(—)_"
        return [f"- **{entry.get('id')}** — {_cell(entry.get('claim'))}{cite}"]

    if group_by:
        grouped = findings.by_theme(root)
        if not grouped:
            lines += ["—", "",
                      "_No accepted findings in this engagement yet._"]
            return "\n".join(lines)
        for theme, entries in grouped.items():
            lines += [f"### {_cell(theme) or '—'}", ""]
            for entry in entries:
                lines += _entry(entry)
            lines.append("")
        return "\n".join(lines).rstrip()

    entries = findings.renderable(root)
    if not entries:
        lines += ["—", "", "_No accepted findings in this engagement yet._"]
        return "\n".join(lines)
    for entry in entries:
        lines += _entry(entry)
    return "\n".join(lines).rstrip()
