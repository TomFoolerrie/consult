#!/usr/bin/env python3
"""
asks.py — the engagement ASK register (M75 Part A, docs/v2/M75-the-ask-loop.md).

An ask is the CURATED, CLIENT-VOICED request the engagement actually sends: one
question, phrased for a human to answer, carrying the GAP IDS it would settle.
It is the convergence point for the three gap homes (the staged forecast, the
taxonomist's node GAPs, the drafters' fragment GAP callouts) — the register
REFERENCES gaps, it never duplicates them, and each home keeps its owner.

    propose(root, text=..., gaps=[...], audience=..., artifact=...) -> "ASK-001"
    entries(root, status=None)      -> [entry dicts]
    accept(root, aid)               -> the accepted ask (the human gate's yes)
    send(root, aid)                 -> it has gone to the client
    answer(root, aid, src_id=...)   -> the client answered (advisory metadata)
    match(root, src_id, [aid, ...]) -> the MATCHER's verb: answer + ledger stamp
    settle(root, aid)               -> the settle dispatch closed its gaps
    retire(root, aid, reason=...)   -> terminal and KEPT
    unask(root, gap, reason=...)    -> the explicit "not the client's to answer"
    renderable(root)                -> accepted + sent (what a deliverable binds)

THE LIFECYCLE, and the two rulings inside it:

    proposed -> accepted -> sent -> answered -> retired
                    \\________________________/

  * **RENDERABLE = accepted + sent** (M75 ruling, recorded here). `accepted` is
    the human gate — nothing unaccepted can reach a client surface, exactly as
    `findings.renderable()` is accepted-only. `sent` is kept renderable because
    a sent ask is still an OUTSTANDING request: dropping it from the render the
    moment it goes out would empty the very list the client is answering from
    (and the information-request document is re-rendered every round of the
    ask loop). `answered` and `retired` are settled and do NOT render — a list
    of questions the client already answered is not a request.
  * **`settled` is a flag, not a status.** An ask is answered when a source
    arrives; its gaps are settled when the settle dispatch has run over them.
    Between those two moments the ask is "answered and unsettled" — the state
    that releases an M74 thin node into the fill wave and that invariant 2
    surfaces at the next gate.

THE UNASKED BUCKET (ruling (b)): a gap the engagement deliberately does NOT put
to the client ("ours to resolve, not the client's") is recorded, with a reason,
in `unasked:`. Reconcile's invariant 1 is what makes the bucket load-bearing:
every gap id appears in the register exactly once — inside an ask or in the
bucket — so a gap can never be quietly dropped by nobody asking about it.

ONE WRITER, ONE FILE. The only write in this module is `_dump` ->
`asks_path(root)` (`<root>/_registers/asks.yaml`), the findings.py home and the
findings.py rule. `match` also records `answers: [ASK-…]` on the SOURCE's
ledger entry — it does that through `ledger.record_answers`, the ledger
module's own writer seam, because the ledger has exactly one writer and it is
not this module. Everything else here — the corpus walk behind `resolve_gaps`,
the ledger read behind `match` — is a read.

Python 3, stdlib + pyyaml. Fail-loud: every refusal is an AsksError naming the
offending value, and nothing is written on a refusal.
"""

from __future__ import annotations

# M67 interpreter floor: this block runs BEFORE any first-party import, because
# a < 3.10 interpreter dies inside the engine modules at import time and a check
# placed after those imports could never fire.
import os as _os  # noqa: E402
import sys as _sys  # noqa: E402
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _pyfloor  # noqa: E402  (3.9-importable by contract)

_pyfloor.require()

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import argparse
import re

from pathlib import Path

import yaml

import ledger


class AsksError(Exception):
    """Raised when an ask operation is refused. The message always names the
    offending value — the unknown id, the duplicated gap, the terminal status
    (fail-loud, the findings.FindingsError posture)."""


#: The register's home, relative to the engagement root — findings.py's
#: register-class convention, sibling file.
REGISTERS_DIRNAME = "_registers"
ASKS_FILENAME = "asks.yaml"

#: The lifecycle (see the module docstring for the two rulings).
PROPOSED, ACCEPTED, SENT, ANSWERED, RETIRED = (
    "proposed", "accepted", "sent", "answered", "retired")
STATUSES = (PROPOSED, ACCEPTED, SENT, ANSWERED, RETIRED)

#: What a deliverable may bind: the OUTSTANDING client-facing asks.
RENDERABLE_STATUSES = (ACCEPTED, SENT)

#: The transitions a verb may perform. A status not listed as a source is
#: terminal for that verb, and the refusal names the current status.
_FROM = {
    ACCEPTED: (PROPOSED,),
    SENT: (ACCEPTED,),
    ANSWERED: (ACCEPTED, SENT),
    RETIRED: (PROPOSED, ACCEPTED, SENT, ANSWERED),
}

#: `ASK-nnn` — the id grammar, mirroring FIND-nnn and SRC-nnn.
ID_PREFIX = "ASK"
ID_RE = re.compile(rf"^{ID_PREFIX}-(\d+)$")

#: A gap reference's qualifier: `<procedure-or-node-slug>:<LOCAL callout id>`
#: (findings.qualify_ground's currency, M57). A reference may also be a BARE
#: SLUG — a whole node the ask is about — which is what makes the ask→node join
#: cheap: the touched slug is everything left of the qualifier.
GAP_QUALIFIER = ":"


# --------------------------------------------------------------------------- #
# The file — the ONE thing this module writes
# --------------------------------------------------------------------------- #

def asks_path(root) -> Path:
    """`<engagement root>/_registers/asks.yaml` — this module's only write
    target."""
    return Path(root) / REGISTERS_DIRNAME / ASKS_FILENAME


def _empty() -> dict:
    return {"asks": [], "unasked": []}


def _load(root) -> dict:
    """The register as a mapping. A missing file is an EMPTY register, not an
    error (an engagement that has asked nothing yet is normal); a malformed one
    is fail-loud."""
    path = asks_path(root)
    if not path.is_file():
        return _empty()
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise AsksError(f"{path}: ask register is unreadable ({exc})") from exc
    if data is None:
        return _empty()
    if not isinstance(data, dict) or not isinstance(data.get("asks"), list):
        raise AsksError(
            f'{path}: ask register must be a mapping with an "asks" list '
            f"(got {type(data).__name__})")
    if data.get("unasked") is None:
        data["unasked"] = []
    if not isinstance(data["unasked"], list):
        raise AsksError(f'{path}: "unasked" must be a list of '
                        f"{{gap, reason}} entries")
    for entry in data["asks"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise AsksError(f"{path}: every ask entry must be a mapping with "
                            f"an id (got {entry!r})")
    return data


def _dump(root, data: dict) -> None:
    """THE ONLY WRITE IN THIS MODULE (see the module docstring)."""
    path = asks_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True,
                       default_flow_style=False),
        encoding="utf-8")


# --------------------------------------------------------------------------- #
# Shape checks (nothing is written on a refusal)
# --------------------------------------------------------------------------- #

def _text_field(value, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AsksError(f"an ask requires {what} (got {value!r}); "
                        f"nothing written")
    return value.strip()


def clean_gaps(gaps) -> list[str]:
    """Normalise a gap reference list, or refuse.

    A reference is a non-empty id string: a qualified callout address
    (`<slug>:GAP-01`) or a bare slug (the whole node). Order-preserving
    de-duplication — naming the same gap twice is not two gaps."""
    if isinstance(gaps, str):
        gaps = [gaps]
    if not isinstance(gaps, (list, tuple)) or not gaps:
        raise AsksError(
            "an ask requires the GAP IDS it would settle — that mapping is "
            "what lets an answer route back to the fragments and nodes the "
            "gaps live in; nothing written")
    out: list[str] = []
    for gap in gaps:
        if not isinstance(gap, str) or not gap.strip():
            raise AsksError(f"bad gap reference {gap!r} — gap references are "
                            f"non-empty id strings; nothing written")
        ref = gap.strip()
        if ref not in out:
            out.append(ref)
    return out


def _known_gaps(data: dict) -> dict[str, str]:
    """`{gap reference: where it already lives}` across the whole register —
    the membership map behind invariant 1's "exactly once"."""
    seen: dict[str, str] = {}
    for entry in data["asks"]:
        for gap in (entry.get("gaps") or []):
            seen.setdefault(str(gap), str(entry.get("id")))
    for entry in data["unasked"]:
        if isinstance(entry, dict) and entry.get("gap"):
            seen.setdefault(str(entry["gap"]), "the unasked bucket")
    return seen


# --------------------------------------------------------------------------- #
# The lifecycle
# --------------------------------------------------------------------------- #

def _mint(existing: list[dict]) -> str:
    """`ASK-nnn`, engagement-global, max existing + 1 — ids are never reused
    (a retired ask keeps its id forever, and a client may have seen it)."""
    highest = 0
    for entry in existing:
        m = ID_RE.match(str(entry.get("id") or ""))
        if m:
            highest = max(highest, int(m.group(1)))
    return f"{ID_PREFIX}-{highest + 1:03d}"


def propose(root, text: str, gaps, audience: str, artifact: str) -> str:
    """Mint a `proposed` ask and return its id.

    `text` is the CLIENT-VOICED request (nothing rewrites it downstream);
    `audience` is WHO can answer it and `artifact` is WHAT would settle it —
    the two grouping fields the render and the agenda both key off. `gaps` is
    the mapping that makes one ask close many gaps.

    The human gate is `accept`: `propose` records what the curation pass says,
    `accept`/`retire` records what the human decided."""
    text = _text_field(text, "client-voiced TEXT (the request as the client "
                             "will read it)")
    audience = _text_field(audience, "an AUDIENCE (who can answer it)")
    artifact = _text_field(artifact, "an ARTIFACT (what would settle it — a "
                                     "walkthrough, an SOP, a config pull, a "
                                     "written answer)")
    refs = clean_gaps(gaps)

    data = _load(root)
    aid = _mint(data["asks"])
    data["asks"].append({
        "id": aid,
        "status": PROPOSED,
        "audience": audience,
        "artifact": artifact,
        "text": text,
        "gaps": refs,
    })
    _dump(root, data)
    return aid


def entries(root, status: str | None = None) -> list[dict]:
    """The asks, in mint order; `status` filters. Read-only; returns copies."""
    if status is not None and status not in STATUSES:
        raise AsksError(f"unknown status {status!r} "
                        f"(known: {', '.join(STATUSES)})")
    out = []
    for entry in _load(root)["asks"]:
        if status is not None and entry.get("status") != status:
            continue
        out.append(dict(entry))
    return out


def unasked(root) -> list[dict]:
    """The `unasked` bucket — gaps deliberately not put to the client, each
    with the reason it is ours (ruling (b))."""
    return [dict(e) for e in _load(root)["unasked"] if isinstance(e, dict)]


def _find(data: dict, aid: str) -> dict:
    hit = next((e for e in data["asks"] if e.get("id") == aid), None)
    if hit is None:
        known = ", ".join(str(e.get("id")) for e in data["asks"]) or "none"
        raise AsksError(f"no ask {aid!r} in the register (known: {known})")
    return hit


def _transition(root, aid: str, to: str, **fields) -> dict:
    data = _load(root)
    hit = _find(data, aid)
    current = hit.get("status")
    if current not in _FROM[to]:
        raise AsksError(
            f"{aid} is {current} — it cannot become {to} "
            f"(only {', '.join(_FROM[to])} can). The lifecycle is "
            f"{' -> '.join(STATUSES[:-1])}, with {RETIRED} reachable from "
            f"any of them")
    hit["status"] = to
    hit.update(fields)
    _dump(root, data)
    return dict(hit)


def accept(root, aid: str) -> dict:
    """Accept a proposed ask — the human gate's yes. Only accepted (and sent)
    asks are `renderable`."""
    return _transition(root, aid, ACCEPTED)


def send(root, aid: str) -> dict:
    """Record that an accepted ask has gone to the client. Still renderable:
    a sent ask is still outstanding until it is answered."""
    return _transition(root, aid, SENT)


def answer(root, aid: str, src_id: str | None = None) -> dict:
    """Record that the client answered — optionally naming the SRC id that
    carries the answer. Advisory metadata (the lifecycle ruling): no gate
    fires on it, and `settled` stays false until the settle dispatch runs."""
    data = _load(root)
    hit = _find(data, aid)
    answered_by = [str(s) for s in (hit.get("answered_by") or [])]
    if src_id and str(src_id) not in answered_by:
        answered_by.append(str(src_id))
    fields = {"settled": False}
    if answered_by:
        fields["answered_by"] = answered_by
    if hit.get("status") == ANSWERED:
        # Idempotent: a second source answering the same ask adds its id and
        # nothing else moves.
        hit.update(fields)
        _dump(root, data)
        return dict(hit)
    return _transition(root, aid, ANSWERED, **fields)


def settle(root, aid: str) -> dict:
    """Record that the settle dispatch closed this ask's gaps.

    Keeps the status at `answered` (the record of what was asked and answered
    is kept) and clears the ask out of the M74 join and invariant 2's list."""
    data = _load(root)
    hit = _find(data, aid)
    if hit.get("status") != ANSWERED:
        raise AsksError(f"{aid} is {hit.get('status')} — only an {ANSWERED} "
                        f"ask can be settled")
    hit["settled"] = True
    _dump(root, data)
    return dict(hit)


def retire(root, aid: str, reason: str) -> dict:
    """Retire an ask — terminal and KEPT, with its reason (what was asked and
    withdrawn is part of the trail)."""
    if not isinstance(reason, str) or not reason.strip():
        raise AsksError(f"retiring {aid} requires a reason (the record of why "
                        f"the ask was withdrawn); nothing written")
    return _transition(root, aid, RETIRED, reason=reason.strip())


def unask(root, gap: str, reason: str) -> dict:
    """Record a gap the engagement deliberately does NOT ask the client about.

    Refuses a gap some ask already carries, by name: invariant 1 is "exactly
    once", and the register is where that is kept true."""
    ref = clean_gaps([gap])[0]
    if not isinstance(reason, str) or not reason.strip():
        raise AsksError(
            f"not asking about {ref} requires a reason (\"ours to resolve, "
            f"not the client's\" is the shape); nothing written")
    data = _load(root)
    where = _known_gaps(data).get(ref)
    if where:
        raise AsksError(f"{ref} is already in the register ({where}) — a gap "
                        f"id appears exactly once; nothing written")
    data["unasked"].append({"gap": ref, "reason": reason.strip()})
    _dump(root, data)
    return {"gap": ref, "reason": reason.strip()}


def renderable(root) -> list[dict]:
    """The asks a deliverable may bind: ACCEPTED + SENT — the outstanding
    client-facing requests (see the module docstring's ruling).

    The information-request definition and the interview agenda reach the
    register through here and nowhere else, so a proposed ask cannot reach a
    client surface by any route."""
    return [e for e in entries(root) if e.get("status") in RENDERABLE_STATUSES]


# --------------------------------------------------------------------------- #
# Queries — the joins, all read-only
# --------------------------------------------------------------------------- #

def touched_slugs(entry: dict) -> set[str]:
    """The slugs one ask touches: everything left of the gap qualifier (a bare
    reference IS the slug). The whole gap→node join, in one line — full
    display-id resolution is not needed to know WHICH node an ask is about."""
    out = set()
    for gap in (entry.get("gaps") or []):
        ref = str(gap)
        out.add(ref.split(GAP_QUALIFIER, 1)[0] if GAP_QUALIFIER in ref
                else ref)
    return out


def touched(root, status: str | None = None, unsettled: bool = False) -> set:
    """The slugs the selected asks touch — the mechanical route-back join
    (zero tokens: ask -> gap ids -> the nodes/fragments those gaps live in).

    `unsettled=True` keeps only asks whose settle dispatch has not run — the
    M74 predicate's other half."""
    out: set[str] = set()
    for entry in entries(root, status=status):
        if unsettled and entry.get("settled"):
            continue
        out |= touched_slugs(entry)
    return out


def unsettled(root) -> list[str]:
    """Invariant 2's list: answered asks whose gaps are not settled yet. A
    GATE DETAIL, never an error (the ruling) — the settle dispatch closes
    them, or the curator splits the remainder into a follow-up ask."""
    return [str(e["id"]) for e in entries(root, status=ANSWERED)
            if not e.get("settled")]


def counts(root) -> dict:
    """`{"open": n, "answered": n}` — the advisor's signal. Open is what is
    renderable (accepted + sent); answered is answered-and-unsettled, the
    work the engagement now owes itself."""
    return {"open": len(renderable(root)), "answered": len(unsettled(root))}


def resolve_gaps(root, aid: str) -> dict:
    """`{"resolved": [...], "unresolved": [...]}` for one ask's gap mapping,
    checked against the LIVE corpus.

    A QUERY, never a gate: an ask is proposed while the corpus is still
    moving (the taxonomist stages asks before confirm), so refusing an
    unresolved reference at propose time would refuse the register's whole
    reason to exist. The resolution universe is findings.py's — the qualified
    callout addresses and entity slugs of every area — reached through its
    read-only corpus walk so an ask and a finding can never disagree about
    what a gap id is."""
    import findings
    data = _load(root)
    entry = _find(data, aid)
    callouts, slugs = findings._corpus_ids(root)
    universe = callouts | slugs
    resolved = [g for g in (entry.get("gaps") or []) if str(g) in universe]
    unresolved = [g for g in (entry.get("gaps") or []) if str(g) not in universe]
    return {"resolved": resolved, "unresolved": unresolved}


# --------------------------------------------------------------------------- #
# The matcher (M75 Part C2) — the one verb that touches the ledger
# --------------------------------------------------------------------------- #

def match(root, src_id: str, ask_ids) -> list[dict]:
    """Record that source `src_id` answers the named asks.

    The MATCHER's verb: intake reads a routed artifact against the open asks'
    text and records the reading HERE, never as free prose. Two effects, both
    advisory:

      * each named ask becomes `answered`, carrying the SRC id;
      * the SOURCE's ledger entry gains `answers: [ASK-…]` — written through
        `ledger.record_answers`, the ledger module's own writer seam, because
        the ledger has exactly one writer and it is not this module.

    Refuses (nothing written, in either file) an unknown SRC id or an unknown
    ask id, by name. Idempotent: matching the same pair twice is a no-op."""
    if isinstance(ask_ids, str):
        ask_ids = [ask_ids]
    wanted = [str(a).strip() for a in (ask_ids or []) if str(a).strip()]
    if not wanted:
        raise AsksError(f"match {src_id}: name at least one ASK id the source "
                        f"answers; nothing written")
    data = _load(root)
    for aid in wanted:
        _find(data, aid)                       # refuses by name, writes nothing
    sid = str(src_id).strip()
    known = {str(e.get("id")) for e in ledger.entries(root)}
    if sid not in known:
        raise AsksError(
            f"{sid}: no such source in the engagement ledger "
            f"({len(known)} known) — route the file first; nothing written")

    # The ledger half first, through its own module's writer: if it refuses,
    # the register is untouched.
    ledger.record_answers(root, sid, wanted)
    return [answer(root, aid, src_id=sid) for aid in wanted]


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def _render(root) -> str:
    lines = []
    for entry in _load(root)["asks"]:
        lines.append(f"{entry.get('id')}  {entry.get('status'):<9} "
                     f"[{entry.get('audience')} / {entry.get('artifact')}]  "
                     f"{entry.get('text')}")
        lines.append(f"    gaps: {', '.join(entry.get('gaps') or []) or '—'}")
    for entry in _load(root)["unasked"]:
        lines.append(f"unasked  {entry.get('gap')} — {entry.get('reason')}")
    return "\n".join(lines) or "(the ask register is empty)"


def main(argv=None) -> int:
    """`asks.py <verb> <engagement root> [...]` — the deterministic surface the
    curation pass and the matcher record through.

    Exit 0 on success, 2 on a refusal (named on stderr). Every verb is one of
    the lifecycle functions above; nothing here has judgment."""
    import sys

    ap = argparse.ArgumentParser(
        prog="asks.py",
        description="The engagement ask register (M75).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def _root(p):
        p.add_argument("root", help="the engagement root (the parent of "
                                    "components/)")
        return p

    p = _root(sub.add_parser("propose", help="mint a proposed ask"))
    p.add_argument("--text", required=True, help="the client-voiced request")
    p.add_argument("--gap", action="append", default=[], dest="gaps",
                   required=True, help="a gap id it would settle (repeatable)")
    p.add_argument("--audience", required=True, help="who can answer it")
    p.add_argument("--artifact", required=True, help="what would settle it")

    for verb, helptext in (("accept", "accept a proposed ask (the human gate)"),
                           ("send", "record that an accepted ask went out"),
                           ("settle", "record that its gaps were settled")):
        q = _root(sub.add_parser(verb, help=helptext))
        q.add_argument("ask", help="the ASK id")

    q = _root(sub.add_parser("answer", help="record a client answer"))
    q.add_argument("ask")
    q.add_argument("--src", default=None, help="the answering SRC id")

    q = _root(sub.add_parser("retire", help="retire an ask (terminal, kept)"))
    q.add_argument("ask")
    q.add_argument("--reason", required=True)

    q = _root(sub.add_parser(
        "match", help="record which asks a routed source answers"))
    q.add_argument("src", help="the SRC id")
    q.add_argument("ask", nargs="+", help="the ASK id(s) it answers")

    q = _root(sub.add_parser(
        "unask", help="record a gap deliberately not put to the client"))
    q.add_argument("gap")
    q.add_argument("--reason", required=True)

    _root(sub.add_parser("list", help="print the register"))

    a = ap.parse_args(argv)
    root = Path(a.root)
    try:
        if a.cmd == "propose":
            print(propose(root, text=a.text, gaps=a.gaps,
                          audience=a.audience, artifact=a.artifact))
        elif a.cmd == "accept":
            print(accept(root, a.ask)["status"])
        elif a.cmd == "send":
            print(send(root, a.ask)["status"])
        elif a.cmd == "settle":
            print(settle(root, a.ask)["status"])
        elif a.cmd == "answer":
            print(answer(root, a.ask, src_id=a.src)["status"])
        elif a.cmd == "retire":
            print(retire(root, a.ask, reason=a.reason)["status"])
        elif a.cmd == "match":
            for entry in match(root, a.src, a.ask):
                print(f"{entry['id']} {entry['status']}")
        elif a.cmd == "unask":
            unask(root, a.gap, reason=a.reason)
            print(f"unasked {a.gap}")
        else:
            print(_render(root))
    except (AsksError, ledger.LedgerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
