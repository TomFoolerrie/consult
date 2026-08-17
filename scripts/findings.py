#!/usr/bin/env python3
"""
findings.py — the engagement findings register (M39 Part A,
docs/v2/M39-analysis-verbs.md).

A finding is the FIRST place the system is allowed an opinion: a CLAIM in the
system's voice, resting on GROUNDS that resolve against the engagement, moving
through the lifecycle M30 A1 deferred — `proposed` -> `accepted` | `rejected`
(rejection is terminal and KEPT: the record of what was considered and set
aside is part of the analysis trail).

    propose(root, claim=..., grounds=[...], theme=...) -> "FIND-001"
    entries(root, status=None)   -> [entry dicts]
    accept(root, fid)            -> the accepted entry
    reject(root, fid, reason=..) -> the rejected entry
    renderable(root)             -> accepted only (what a deliverable may bind)

GROUNDS ARE MANDATORY AND MUST RESOLVE. Every finding traces or it does not
exist (the M30 A1 provenance discipline, verbatim). A ground resolves when it
names one of:

  * an SRC id in the engagement ledger (`_sources/sources.yaml`, read through
    `ledger.entries`);
  * a callout id in the area corpus (PP / GAP / CTRL — every callout of every
    manifest-listed procedure fragment and every `_taxonomy/` node, parsed
    through `kernel.parse_entity` against the DECLARED types, never against a
    typed-out label list);
  * an entity slug named by an area manifest.

An unresolvable ground is refused BY NAME and nothing is written.

ONE DIRECTION — STRUCTURAL, NOT POLICED. Findings never flow back into the
capture layer (M39: the brain records what IS, findings record what the system
THINKS). This module contains no code path that writes outside its own file:
the only write in it is `_dump` -> `findings_path(root)`
(`<root>/_registers/findings.yaml`), and every other filesystem touch —
ledger, manifests, fragments, taxonomy nodes — is a read. There is no other
`write_text`, no `mkdir` outside that file's parent, and no delegation to a
writing verb anywhere below.

WHY ITS OWN FILE AND NOT M30's REGISTER HOME (decision, recorded): M30's
register machinery (`scripts/registers.py`) is the one writer of
`components/_client/registers/*.md` — i.e. it writes UNDER `components/`,
which is exactly the tree the one-direction rule forbids an analysis verb to
touch (pinned by fingerprint in tests/test_findings_m39.py). So the M30 verb
shape does not fit, and findings get a register-CLASS home of their own at the
engagement root, owned by this module: `_registers/findings.yaml`. YAML, not
M30's markdown, because a finding carries structured fields (grounds list,
status, theme, reason) that the markdown entry grammar has no slot for.
`registers.py` is untouched.

Ids are minted ENGAGEMENT-GLOBALLY (`FIND-001`, `FIND-002`, ... — max existing
+ 1, never reused, rejected findings included), so a finding id is stable and
citable for the life of the engagement.

Python 3, stdlib + pyyaml (like every other engine module). Fail-loud: every
refusal is a FindingsError naming the offending value.
"""

from __future__ import annotations

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import json
import re

from pathlib import Path

import yaml

import kernel
import ledger


class FindingsError(Exception):
    """Raised when a findings operation is refused. The message always names
    the offending value — the unresolvable ground, the unknown id, the
    terminal status (fail-loud, same posture as kernel.TypeDeclError)."""


#: The findings file's home, relative to the engagement root. A register-class
#: citizen with its own directory OUTSIDE components/ (see the module docstring
#: for why M30's home cannot be used).
REGISTERS_DIRNAME = "_registers"
FINDINGS_FILENAME = "findings.yaml"

#: The lifecycle. `proposed` is the only non-terminal status; both terminal
#: statuses are KEPT (nothing is ever deleted from the file).
PROPOSED, ACCEPTED, REJECTED = "proposed", "accepted", "rejected"
STATUSES = (PROPOSED, ACCEPTED, REJECTED)

#: `FIND-nnn` — the id grammar, mirroring the ledger's `SRC-nnn`.
ID_PREFIX = "FIND"
ID_RE = re.compile(rf"^{ID_PREFIX}-(\d+)$")

#: Where an area keeps its taxonomy-node fragments (coverage_map's convention).
TAXONOMY_DIRNAME = "_taxonomy"

#: The types the corpus is read through when collecting callout ids. Declared
#: types only, and each fragment is tried against each in turn — a fragment a
#: type cannot parse is simply not an entity of it (definitions.py's posture).
#: `process-step` and `activity` are the two shapes a procedure fragment can
#: have (M33's compatibility ruling); `taxonomy-node` is the node shape.
PROCEDURE_TYPES = ("process-step", "activity")
NODE_TYPE = "taxonomy-node"

#: The manifest component role holding an area's hand-authored entities.
ENTITY_ROLE = "procedure"


# --------------------------------------------------------------------------- #
# The file — the ONE thing this module writes
# --------------------------------------------------------------------------- #

def findings_path(root) -> Path:
    """`<engagement root>/_registers/findings.yaml` — the only write target
    of this module."""
    return Path(root) / REGISTERS_DIRNAME / FINDINGS_FILENAME


def _load(root) -> dict:
    """The findings file as a mapping. A missing file is an EMPTY register, not
    an error (an engagement that has not analysed anything yet is normal); a
    malformed one is fail-loud."""
    path = findings_path(root)
    if not path.is_file():
        return {"findings": []}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise FindingsError(f"{path}: findings register is unreadable "
                            f"({exc})") from exc
    if data is None:
        return {"findings": []}
    if not isinstance(data, dict) or not isinstance(
            data.get("findings"), list):
        raise FindingsError(
            f'{path}: findings register must be a mapping with a "findings" '
            f"list (got {type(data).__name__})")
    for entry in data["findings"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise FindingsError(
                f"{path}: every findings entry must be a mapping with an "
                f"id (got {entry!r})")
    return data


def _dump(root, data: dict) -> None:
    """THE ONLY WRITE IN THIS MODULE (see the one-direction note in the module
    docstring). Writes `<root>/_registers/findings.yaml` and nothing else."""
    path = findings_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True,
                       default_flow_style=False),
        encoding="utf-8")


# --------------------------------------------------------------------------- #
# Grounds resolution (READ-ONLY over the engagement)
# --------------------------------------------------------------------------- #

def _area_dirs(root) -> list[Path]:
    comp = Path(root) / "components"
    if not comp.is_dir():
        return []
    return [p for p in sorted(comp.iterdir())
            if p.is_dir() and not p.name.startswith("_")]


def _manifest(area: Path) -> dict:
    """One area's manifest as a mapping, or {} when absent/unreadable. An area
    mid-scaffold reads as "nothing known here" — grounds resolution is a
    lookup, not a validator (reconcile owns manifest defects)."""
    try:
        data = json.loads((area / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _src_ids(root) -> set[str]:
    """Every SRC id the engagement ledger holds. Read through `ledger.entries`
    — the one read seam, so findings can never disagree with the ledger about
    what a source is."""
    try:
        return {str(e.get("id")) for e in ledger.entries(root)
                if e.get("id")}
    except Exception:
        # No ledger yet (or an unreadable one) is not a findings defect: it
        # simply means no SRC id resolves. The refusal below still names the
        # ground the caller passed.
        return set()


def _load_types(names) -> list:
    out = []
    for name in names:
        try:
            out.append(kernel.load_type(name))
        except Exception:
            continue
    return out


def _callout_ids_of(path: Path, tdecls) -> set[str]:
    """Every callout id in one fragment, tried against each declared type.
    Declaration-driven: no callout label is typed out here (the shape audit's
    rule) — the ids come from whatever the type declares."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return set()
    ids: set[str] = set()
    for tdecl in tdecls:
        try:
            entity = kernel.parse_entity(text, tdecl, slug=path.stem)
        except Exception:
            continue
        for callout in entity.callout_dicts():
            cid = callout.get("id")
            if isinstance(cid, str) and cid:
                ids.add(cid)
    return ids


def _area_corpus_ids(area: Path, proc_types=None,
                     node_types=None) -> tuple[set[str], set[str]]:
    """(callout ids, entity slugs) for ONE area — the unit `_corpus_ids` sums
    over and the scope `for_area` filters by, so the engagement-wide universe
    and the per-area one can never be assembled by two different rules."""
    proc_types = _load_types(PROCEDURE_TYPES) if proc_types is None \
        else proc_types
    node_types = _load_types([NODE_TYPE]) if node_types is None else node_types
    callouts: set[str] = set()
    slugs: set[str] = set()
    manifest = _manifest(area)
    for comp in manifest.get("components") or []:
        if not isinstance(comp, dict):
            continue
        slug = comp.get("slug")
        if isinstance(slug, str) and slug:
            slugs.add(slug)
        if comp.get("role") != ENTITY_ROLE:
            continue
        fpath = area / str(comp.get("file") or "")
        if fpath.is_file():
            callouts |= _callout_ids_of(fpath, proc_types)
    tdir = area / TAXONOMY_DIRNAME
    if tdir.is_dir():
        for node in sorted(tdir.glob("*.md")):
            slugs.add(node.stem)
            callouts |= _callout_ids_of(node, node_types)
    return callouts, slugs


def _corpus_ids(root) -> tuple[set[str], set[str]]:
    """(callout ids, entity slugs) over the whole engagement corpus.

    Callout ids come from the manifest-listed procedure fragments and every
    `_taxonomy/` node (GAP-05 in the IPO fixture lives on a node — a ground may
    cite it, so the node walk is not optional). Slugs come from the manifests,
    which are membership authority. The per-area read is `_area_corpus_ids`;
    this is its sum over the areas."""
    proc_types = _load_types(PROCEDURE_TYPES)
    node_types = _load_types([NODE_TYPE])
    callouts: set[str] = set()
    slugs: set[str] = set()
    for area in _area_dirs(root):
        acallouts, aslugs = _area_corpus_ids(area, proc_types, node_types)
        callouts |= acallouts
        slugs |= aslugs
    return callouts, slugs


def resolve_grounds(root, grounds) -> list[str]:
    """Normalise + resolve a grounds list, or refuse naming the first ground
    that does not resolve.

    Read-only. The resolution universe is `SRC ids ∪ corpus callout ids ∪
    manifest entity slugs` — assembled once per call (like coverage, derived on
    demand and therefore unable to drift)."""
    if isinstance(grounds, str):
        grounds = [grounds]
    if not isinstance(grounds, (list, tuple)) or not grounds:
        raise FindingsError(
            "a finding requires GROUNDS — the SRC ids, callout ids (PP/GAP/"
            "CTRL) and entity slugs it rests on. Every finding traces or it "
            "does not exist; nothing written")
    cleaned: list[str] = []
    for ground in grounds:
        if not isinstance(ground, str) or not ground.strip():
            raise FindingsError(
                f"bad ground {ground!r} — grounds are non-empty id strings; "
                f"nothing written")
        cleaned.append(ground.strip())

    src = _src_ids(root)
    callouts, slugs = _corpus_ids(root)
    universe = src | callouts | slugs
    for ground in cleaned:
        if ground not in universe:
            raise FindingsError(
                f"ground {ground!r} does not resolve against this engagement "
                f"— it is not a ledger SRC id ({len(src)} known), a corpus "
                f"callout id ({len(callouts)} known) or an entity slug "
                f"({len(slugs)} known); nothing written")
    # Order-preserving de-duplication: citing the same id twice is not two
    # grounds.
    seen: set[str] = set()
    return [g for g in cleaned if not (g in seen or seen.add(g))]


# --------------------------------------------------------------------------- #
# The lifecycle
# --------------------------------------------------------------------------- #

def _mint(existing: list[dict]) -> str:
    """`FIND-nnn`, engagement-global, max existing + 1 (ids are never reused —
    a rejected finding keeps its id forever)."""
    highest = 0
    for entry in existing:
        m = ID_RE.match(str(entry.get("id") or ""))
        if m:
            highest = max(highest, int(m.group(1)))
    return f"{ID_PREFIX}-{highest + 1:03d}"


def propose(root, claim: str, grounds, theme: str) -> str:
    """Mint a `proposed` finding and return its id.

    Refuses (nothing written) a blank claim, a blank theme, an empty grounds
    list, or a ground that does not resolve — named. The human gate is the M30
    conversation: `propose` records what the analysis says, `accept`/`reject`
    records what the human decided."""
    if not isinstance(claim, str) or not claim.strip():
        raise FindingsError("a finding requires a CLAIM (the assessment, in "
                            "the system's voice); nothing written")
    if not isinstance(theme, str) or not theme.strip():
        raise FindingsError(
            f"a finding requires a THEME (the grouping a findings report "
            f"renders by); got {theme!r}, nothing written")
    resolved = resolve_grounds(root, grounds)

    data = _load(root)
    fid = _mint(data["findings"])
    data["findings"].append({
        "id": fid,
        "status": PROPOSED,
        "theme": theme.strip(),
        "claim": claim.strip(),
        "grounds": resolved,
    })
    _dump(root, data)
    return fid


def entries(root, status: str | None = None) -> list[dict]:
    """The findings, in mint order; `status` filters (proposed|accepted|
    rejected). Read-only; returns copies, so a caller cannot edit the register
    through the list it was handed."""
    if status is not None and status not in STATUSES:
        raise FindingsError(f"unknown status {status!r} "
                            f"(known: {', '.join(STATUSES)})")
    out = []
    for entry in _load(root)["findings"]:
        if status is not None and entry.get("status") != status:
            continue
        out.append(dict(entry))
    return out


def _transition(root, fid: str, to: str, reason: str | None) -> dict:
    data = _load(root)
    hit = next((e for e in data["findings"] if e.get("id") == fid), None)
    if hit is None:
        known = ", ".join(str(e.get("id")) for e in data["findings"]) or "none"
        raise FindingsError(f"no finding {fid!r} in {findings_path(root)} "
                            f"(known: {known})")
    current = hit.get("status")
    if current != PROPOSED:
        # Both terminal statuses are terminal. A rejected finding cannot be
        # accepted later and an accepted one is not re-adjudicated by a verb:
        # re-opening a decision is a new finding, so the trail keeps both.
        raise FindingsError(
            f"{fid} is {current} — terminal. Only a proposed finding can be "
            f"{to} (a reconsidered claim is a NEW finding; the record of what "
            f"was decided is kept)")
    hit["status"] = to
    if reason is not None:
        hit["reason"] = reason.strip()
    _dump(root, data)
    return dict(hit)


def accept(root, fid: str, reason: str | None = None) -> dict:
    """Accept a proposed finding — the human gate's yes. Accepted findings are
    the only ones `renderable` returns."""
    return _transition(root, fid, ACCEPTED, reason)


def reject(root, fid: str, reason: str) -> dict:
    """Reject a proposed finding — terminal and KEPT (with its reason: what was
    considered and set aside is part of the analysis trail)."""
    if not isinstance(reason, str) or not reason.strip():
        raise FindingsError(f"rejecting {fid} requires a reason (the record of "
                            f"why the claim was set aside); nothing written")
    return _transition(root, fid, REJECTED, reason)


def renderable(root) -> list[dict]:
    """The findings a deliverable may bind: ACCEPTED ONLY.

    The findings-report definition (kernel/deliverables/findings-report.yaml)
    reaches the register through here and nowhere else, so a proposed or
    rejected finding cannot reach a rendered document by any route."""
    return entries(root, status=ACCEPTED)


def for_area(root, area, status: str | None = None) -> list[dict]:
    """The findings whose GROUNDS resolve into one area (M49 Part C).

    `entries` is engagement-wide, and every consumer that wants "the findings
    about this area" was re-filtering by hand. The membership rule, stated once
    here: a finding belongs to an area when at least one of its grounds is a
    callout id or an entity slug in THAT AREA'S corpus — the same
    `_area_corpus_ids` read `resolve_grounds` builds its universe from, scoped
    to one area instead of summed over all of them, so a ground that resolves
    can never fail to be attributable.

    A finding grounded ONLY in SRC ids is deliberately EXCLUDED: a source is
    engagement-wide evidence, not an area, and a claim resting only on sources
    is a claim about the engagement (the p2p-wide "the SOP predates the
    migration" shape). So is a finding grounded only in another area's ids.
    Nothing here infers an area from a claim's WORDS — the grounds are the only
    address a finding has.

    `area` is a NAME (resolved against `<root>/components/<name>`) or a PATH.
    `status` passes straight through to `entries`, so an unknown status is that
    verb's refusal, named. Read-only; returns copies, in mint order."""
    apath = Path(area)
    if not apath.is_absolute() and len(apath.parts) == 1:
        apath = Path(root) / "components" / apath.name
    callouts, slugs = _area_corpus_ids(apath)
    mine = callouts | slugs
    if not mine:
        return []
    return [e for e in entries(root, status=status)
            if mine & {str(g) for g in (e.get("grounds") or [])}]


def by_theme(root) -> dict[str, list[dict]]:
    """`renderable` grouped by theme, themes in first-appearance order — the
    shape the findings-report's `group_by: theme` binding consumes."""
    grouped: dict[str, list[dict]] = {}
    for entry in renderable(root):
        grouped.setdefault(str(entry.get("theme") or ""), []).append(entry)
    return grouped
