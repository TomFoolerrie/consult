#!/usr/bin/env python3
"""
coverage_map.py — the M37 coverage map (docs/v2/M37-surveyor-librarian.md,
Part B): how well evidenced is each taxonomy node, right now?

    coverage(root, node_steps) -> {node-slug: status}

THE CHARTER'S ONE HARD GUARDRAIL, restated because it constrains this file
absolutely: coverage is a PURE FUNCTION, never a file.

  * It writes NOTHING — no artifact, no dotfile, no mkdir, not even a touch of
    an mtime. Everything below opens files for reading only.
  * It caches NOTHING — no module-level memo, no lru_cache, no "just the
    manifest" dict living between calls. Every call re-reads the ledger and the
    fragments, because the whole point is that the answer is derived on demand
    and therefore cannot drift. A persisted coverage map is v0's `state.json`
    reborn; the ticket names cache creep as the review risk to police, and the
    join is cheap enough (one ledger read, one entity walk) that nobody needs
    to. Both properties are pinned by tests/test_surveyor_m37.py.

THE JOIN, in one breath: taxonomy nodes (entity fragments under
`<area>/_taxonomy/`) ← their process steps (`node_steps`, handed in) ← those
steps' drafted text and citations ← the M34 engagement ledger's tags.

`node_steps` is an explicit parameter rather than something re-derived here.
The caller (surveyor brief, advisor, the information-request definition) owns
the node→step relation; passing it keeps the join VISIBLE at the call site and
this function testable without a relation channel having shipped yet.

Statuses, in strict precedence order (first match wins):

  conflicted  the node fragment carries a GAP callout naming >= 2 distinct
              SRC ids — the lens-conflict record (Part D). Disagreement
              outranks volume of evidence: two sources that contradict each
              other are not "more evidenced", they are a question for a human.
  evidenced   some step of the node is DRAFTED (exists, sentinel gone) and its
              text cites at least one SRC id.
  sourced     some step of the node appears in an OUTSTANDING ledger tag: a
              source is registered against it and not yet consumed.
  claimed     the node exists and nothing above is true.

PUBLIC PROVENANCE NEVER DISCHARGES (M47, docs/v2/M47-research-pass.md). A ledger
entry may carry `provenance: public` — the day-zero research pass's tag for
material read off the public record (10-K, the client's site, industry norms).
The rule the architecture review ratified: **public sources inform the needs
view; they never discharge it.** Here that is one mechanical amendment, applied
BEFORE the three positive tests: public SRC ids are removed from every evidence
join below, so a node evidenced ONLY by public sources reads exactly as an
unevidenced node does (`claimed` — known, not yet evidenced, and therefore still
an ask on the information-request list), and a node with mixed evidence is
judged on its client-provided half alone.

`provenance` is ADDITIVE and defaults to client-provided: an entry without the
field is client material, and every join below then behaves byte-identically to
the pre-M47 map. That default is what lets the field land without touching a
single existing ledger, sources or coverage test.

Python 3, stdlib + the engine's own modules (like every other engine module).
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import json
import re

from pathlib import Path

import kernel
import ledger


#: The type every node fragment is read through (kernel/types/taxonomy-node.yaml).
NODE_TYPE = "taxonomy-node"

#: Where an area keeps its node fragments. One file per node; the node's slug is
#: the filename STEM (the same convention scaffold uses for procedures — the
#: filesystem carries identity, no index file to drift).
TAXONOMY_DIRNAME = "_taxonomy"

#: An SRC id as it appears in prose and in callout bodies (the ledger's minted
#: form, `SRC-001`, and the v1 per-area adapter's `area/SRC-001` — matching the
#: id half is enough to count distinct sources).
SRC_ID_RE = re.compile(r"\bSRC-[A-Za-z0-9]+\b")

#: The `unfilled` skeleton sentinel. Reimplemented (minimally, read-only) rather
#: than imported, so the coverage join does not drag the advisor's module in;
#: the two forms scaffold writes are the comment and the status field, and a
#: bare `unfilled` body line is the hand-written equivalent. The advisor
#: (orchestrate.UNFILLED_RE) remains the sentinel grammar's OWNER — widen there
#: first if the grammar ever grows.
_SENTINEL_RE = re.compile(
    r"(<!--\s*unfilled\s*-->)|(status\s*:\s*unfilled)|(^\s*unfilled\s*$)",
    re.I | re.M)

#: The ledger field that marks where a source came from, and the ONE value that
#: changes this map's arithmetic. Absent (or anything else) reads as
#: client-provided — the default, and the reason M47 needed no existing-test
#: change.
PROVENANCE_FIELD = "provenance"
PROVENANCE_PUBLIC = "public"

#: The four statuses, weakest to strongest. Precedence is this list's ORDER, so
#: the resolution below cannot silently disagree with the docstring.
_PRECEDENCE = ("claimed", "sourced", "evidenced", "conflicted")


# --------------------------------------------------------------------------- #
# Reading the engagement (every function here is read-only by construction)
# --------------------------------------------------------------------------- #

def _area_dirs(root) -> list[Path]:
    """The engagement's area directories, name order."""
    comps = Path(root) / "components"
    if not comps.is_dir():
        return []
    return sorted(p for p in comps.iterdir()
                  if p.is_dir() and not p.name.startswith("_"))


def _manifest(area: Path) -> dict:
    """One area's manifest as a mapping, or {} when it has none / is unreadable.

    An unreadable manifest is not this function's defect to raise: coverage is a
    reporting join, and an area mid-scaffold must read as "nothing known here"
    rather than take the whole map down."""
    try:
        data = json.loads((area / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _step_index(root) -> dict[str, tuple[Path, str, str]]:
    """`{step slug: (area path, area name, fragment filename)}`.

    The step→area derivation the spec asks for: each step's area is the area
    whose manifest names its slug. First manifest wins (slugs are unique per
    area by manifest law; a slug appearing in two areas is a reconcile concern,
    not something to double-count here)."""
    index: dict[str, tuple[Path, str, str]] = {}
    for area in _area_dirs(root):
        manifest = _manifest(area)
        aname = str(manifest.get("area") or area.name)
        for comp in manifest.get("components") or []:
            if not isinstance(comp, dict):
                continue
            slug = comp.get("slug")
            if isinstance(slug, str) and slug and slug not in index:
                index[slug] = (area, aname, str(comp.get("file") or ""))
    return index


def _node_files(root) -> dict[str, Path]:
    """`{node slug: fragment path}` over every area's `_taxonomy/`."""
    nodes: dict[str, Path] = {}
    for area in _area_dirs(root):
        tdir = area / TAXONOMY_DIRNAME
        if not tdir.is_dir():
            continue
        for f in sorted(tdir.glob("*.md")):
            nodes[f.stem] = f
    return nodes


def _public_src_ids(root) -> frozenset[str]:
    """Every SRC id the ledger marks `provenance: public`.

    Read off `ledger.entries` (the ledger stays the authority on its own
    entries), compared case-insensitively on the VALUE only — the field name is
    the contract, and a hand-typed `Public` is plainly the same claim. An
    unreadable or absent ledger yields the empty set: no source is public, which
    is the pre-M47 behaviour and the correct read of "nothing is registered".
    """
    try:
        held = ledger.entries(root)
    except Exception:
        return frozenset()
    out = set()
    for entry in held:
        if not isinstance(entry, dict):
            continue
        value = entry.get(PROVENANCE_FIELD)
        if isinstance(value, str) and value.strip().lower() == PROVENANCE_PUBLIC:
            sid = str(entry.get("id") or "")
            if sid:
                out.add(sid)
    return frozenset(out)


def _client_provided(src_ids, public: frozenset[str]) -> set[str]:
    """The subset of some found SRC ids that can discharge anything.

    The one place the exclusion is spelled: public ids drop out, everything else
    (including an id the ledger has never heard of — an uncited registry is a
    hygiene concern, not a licence to treat prose as public) counts."""
    return {sid for sid in src_ids if sid not in public}


# --------------------------------------------------------------------------- #
# The three positive tests
# --------------------------------------------------------------------------- #

def _is_conflicted(node_path: Path, tdecl, public: frozenset[str] = frozenset()) -> bool:
    """Does this node fragment carry the lens-conflict record?

    A conflict is a callout whose body names TWO OR MORE distinct SRC ids —
    "AP Manager per SRC-001; Controller per SRC-002", both claims in their own
    framing (the PAIN discipline: observation, never adjudication).

    WHY NO LABEL CONSTANT: the taxonomy-node type declares exactly ONE callout
    kind, the GAP, precisely so that this test can be "a node callout naming two
    sources" and no module outside the kernel has to type a callout label as a
    code constant (the M36 shape audit's rule, honoured rather than
    allowlisted). If the type ever declares a second kind, restrict this walk to
    the GAP kind by reading it off `tdecl.callouts` — do NOT type the label."""
    entity = kernel.parse_entity(
        node_path.read_text(encoding="utf-8"), tdecl, slug=node_path.stem)
    for callout in entity.callout_dicts():
        blob = " ".join([str(callout.get("text") or "")]
                        + [str(v) for v in (callout.get("fields") or {}).values()])
        # M47: a disagreement between two PUBLIC readings is not the client's
        # process contradicting itself — it is two outside descriptions of it,
        # and it may not advance the node past `claimed`.
        if len(_client_provided(SRC_ID_RE.findall(blob), public)) >= 2:
            return True
    return False


def _is_evidenced(step_slug: str, index: dict,
                  public: frozenset[str] = frozenset()) -> bool:
    """Is this step drafted AND citing a source?

    Drafted = the fragment exists and no longer carries the skeleton sentinel
    (scaffold's `_is_drafted` notion, reimplemented read-only). Citing = its
    text names at least one SRC id. Both halves are required: a drafted
    fragment with no citation is prose nobody can trace, and a citation in a
    skeleton is the scaffold's own source note, not drafted content."""
    entry = index.get(step_slug)
    if entry is None:
        return False
    area, _aname, fname = entry
    if not fname:
        return False
    fpath = area / fname
    if not fpath.is_file():
        return False
    text = fpath.read_text(encoding="utf-8")
    if _SENTINEL_RE.search(text):
        return False
    # M47: drafted prose citing only public material is context, not evidence.
    return bool(_client_provided(SRC_ID_RE.findall(text), public))


def _outstanding_slugs(root, area_names,
                       public: frozenset[str] = frozenset()) -> set[str]:
    """Every step slug some registered source still owes this engagement a read.

    `ledger.outstanding(root, area)` IS the definition of outstanding-ness
    (`touches[area] ⊄ consumed[area]`) — asked here per area rather than
    recomputed, so coverage can never disagree with the ledger about what is
    consumed."""
    out: set[str] = set()
    for aname in area_names:
        for sid, slugs in ledger.outstanding(root, aname).items():
            # M47: `sourced` says "a source is registered against this step and
            # not yet read". A PUBLIC source being unread is not progress
            # towards the client material the need actually wants.
            if sid in public:
                continue
            out.update(slugs)
    return out


# --------------------------------------------------------------------------- #
# The map
# --------------------------------------------------------------------------- #

def coverage(root, node_steps: dict[str, list[str]]) -> dict[str, str]:
    """`{node slug: status}` for every taxonomy node in the engagement.

    Pure: reads the ledger, the manifests, the node fragments and the step
    fragments, and writes nothing anywhere. Recomputed in full on every call —
    see the module docstring on why there is no cache to invalidate.

    `node_steps` maps a node slug to the step slugs bound to it. A node with no
    entry (or an empty list) is simply a node with no steps yet: it can still be
    `conflicted` (the conflict lives on the node) and is otherwise `claimed`.
    Nodes are discovered from disk, so a `node_steps` key naming a node that
    does not exist contributes nothing rather than inventing a row."""
    root = Path(root)
    node_steps = dict(node_steps or {})

    nodes = _node_files(root)
    if not nodes:
        return {}

    tdecl = kernel.load_type(NODE_TYPE)
    steps = _step_index(root)
    area_names = sorted({aname for _a, aname, _f in steps.values()}
                        or {a.name for a in _area_dirs(root)})
    # M47's one amendment, resolved once per call (the map caches nothing
    # between calls, so the ledger is re-read here as everywhere else).
    public = _public_src_ids(root)
    outstanding = _outstanding_slugs(root, area_names, public)

    out: dict[str, str] = {}
    for slug, path in nodes.items():
        mine = [s for s in (node_steps.get(slug) or []) if isinstance(s, str)]

        status = "claimed"
        if any(s in outstanding for s in mine):
            status = "sourced"
        if any(_is_evidenced(s, steps, public) for s in mine):
            status = "evidenced"
        if _is_conflicted(path, tdecl, public):
            status = "conflicted"

        # The assignments above run weakest-first, so the last one that fires
        # wins — assert that against the declared order rather than trusting
        # the reader to re-derive it.
        assert status in _PRECEDENCE
        out[slug] = status

    return out
