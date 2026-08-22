#!/usr/bin/env python3
"""
agenda.py — M46's interview agenda (docs/v2/M46-interview-agenda.md): the
per-role RENDER over M44's needs view, joined to the roles registry and the
source ledger.

WHAT THIS IS AND WHAT IT IS NOT. It is the thing you walk into a client meeting
holding, for one named person. It is NOT a second gap engine: every line traces
to a needs entry (`needs.needs(area)`), a ledger row (`ledger.outstanding` /
`ledger.area_view`) or the roles join — this module mints no need, ranks
nothing, and adds no judgment of its own. That is the whole design rule of the
ticket, and it is why the agenda needed no new binding verb and no engine
special-case: `kernel/deliverables/interview-agenda.yaml` binds
`engagement-needs` and the `roles` channel, and this module reads its vocabulary
off those bindings.

HUMAN-TRIGGERED, ALWAYS (the ruling's note: *"I would like to be in charge of
when this generates. It will be an ad hoc item."*). The verb is
`python3 scripts/agenda.py <area> --role <slug>`, run by a human. No agent
contract names this file and no loop fires it; nothing in the system decides
that an interview is needed. The taxonomist may CITE agenda-worthy clusters and
may not generate.

THE ROLE JOIN, MECHANICAL AND NEVER GUESSED. A role's TERRITORY is the set of
process steps that name the role on the channel the definition's `role-territory`
binding selects — the consult-meta channel whose registry is the area's
`_reference/roles.yaml` (`kernel.load_type(...).channels` says which file that
is; `matrix_views._channel_names`' own read, reused). A taxonomy node belongs to
the territory when any step it covers does (`plan_views.node_steps`, the same
relation the matrix groups by). Nothing about seniority, nothing about wording:
if the record does not put the role on the step, the step is not on the agenda.

THE FIVE SECTIONS, one per FEED — the spec's shape mapped onto M44's three feeds
plus the ledger, with no reclassification in between; the recorded-gap feed
alone feeds two sections, and only because the record itself now says which
(M50, below):

  what we need you to settle         needs `recorded-gap` in the territory whose
                                     entry carries the DECLARED conflict nature
                                     (two sources disagree)
  what we would like to confirm      every OTHER `recorded-gap` in the territory:
                                     the declared evidenced-absence nature, and
                                     every undiscriminated entry (v1-grammar and
                                     legacy fragments keep rendering exactly
                                     where they always did)
  what we believe is missing         needs `coverage` on nodes the territory
                                     touches (coverage + evidenced absence)
  what we have not asked yet         needs `binding-unserved` — the deliverable's
                                     structurally unserved bindings, area-level
                                     ground, shown to a role that HAS territory
                                     here and to nobody else
  what you gave us, we still owe a read on
                                     the ledger's outstanding rows whose
                                     touched slugs fall in the territory

ONE FEED, ONE SECTION — AMENDED BY M50. M44 originally deferred the
conflict/absence discriminator on gap callouts, so this render merged both mints
into one confirm section and said so (M46 A1 item 1: "revisit when the
discriminator lands"). M50 landed it: the GAP callout declaration carries a
`Nature:` enum, and `needs.py` puts the stated value on the entry as its
optional `nature` key. The split above is therefore a FIELD READ, not new
judgment — this module still mints nothing and ranks nothing, and an entry with
no `nature` is never guessed at. **The M46 A1.1 revisit is hereby done.**

THE POSITIONAL RULE, STATED HERE AND NOWHERE ELSE. This module types no enum
value: it reads the declared vocabulary off the process-step type's GAP callout
(`CalloutDecl.field_enums`, resolved through `kinds.declared_natures` — the
same read needs.py does) and takes the FIRST DECLARED value as the conflict
nature, because the declaration states the two-sources-disagree mint first and
the evidenced-absence mint second. That ordering is the contract between
`kernel/types/process-step.yaml` and this file; a declaration that reorders the
enum must update it here. No enum declared at all → nothing is a conflict and
the confirm section renders exactly as it did before M50.

THE LEDGER RULE (M40's, reused): never ask for what we already hold. Section
four lists only rows the ledger still reports OUTSTANDING for the territory, so a
source already read is never asked for again; and every item in the first three
sections carries the SRC ids already in hand, so nobody re-requests a document
mid-meeting.

REFUSALS. An unknown role raises `AgendaError` NAMING it (resolved against the
registry's slugs, canonical names and aliases). Everything that is merely NOT
YET — no objective, no needs, no ledger, a role with an empty territory — is an
honest short agenda, never a crash.

READ-ONLY, DETERMINISTIC. Nothing is written and nothing is cached; the order is
the roles registry's, then the manifest's, then each feed's own document order.
Two calls are byte-equal (pinned in tests/test_agenda_m46.py).

LAZY IMPORTS INSIDE FUNCTIONS: aggregate.py registers this module's builder at
import time and kernel.py imports aggregate, so a module-level import of
kernel/definitions/needs/... would close an import cycle — the note plan_views.py,
matrix_views.py and needs.py all carry, applying here verbatim.

Python 3, stdlib + the engine's own modules.
"""

from __future__ import annotations

# M67 interpreter floor: this block runs BEFORE any first-party import, because
# a < 3.10 interpreter dies inside `callouts.py` at import time and a check
# placed after those imports could never fire.
import os as _os  # noqa: E402
import sys as _sys  # noqa: E402
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import _pyfloor  # noqa: E402  (3.9-importable by contract)

_pyfloor.require()

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

import sys

from pathlib import Path

# definitions / kernel / needs / people / plan_views / matrix_views / ledger /
# client_config are imported LAZILY inside the functions — see the import-cycle
# note in the docstring.

#: The derived kind / view-block id / `PY_BUILDERS` key (D1's convention, as in
#: plan_views and needs). Also the definition's name — this deliverable's view
#: is its whole body.
AGENDA_KIND = "interview-agenda"

#: The definition whose bindings carry this render's vocabulary.
AGENDA_DEFINITION = "interview-agenda"

#: The binding names that definition must carry. THE contract between the YAML
#: and this writer — the only binding names typed here, exactly as in plan_views.
BINDING_NEEDS = "engagement-needs"        # the M44 feed
BINDING_TERRITORY = "role-territory"      # the roles join (and the ledger key)


class AgendaError(Exception):
    """Raised when an agenda cannot be rendered as asked — today, exactly one
    case: a role nobody in this area's registry answers to. The message always
    NAMES the role that was asked for (the loader posture, mirrored)."""


# --------------------------------------------------------------------------- #
# Vocabulary (the bindings seam)
# --------------------------------------------------------------------------- #

def _bindings(area: Path) -> dict:
    """This deliverable's binding map — the definition is the authority on its
    own vocabulary, user file shadowing shipped (M13)."""
    import definitions
    return definitions.load_definition(AGENDA_DEFINITION, area=area).bindings


def _role_channel(area: Path) -> str:
    """The consult-meta channel the roles join reads, from the binding.

    Named in `role-territory`'s `channels:` and checked against the step type's
    declaration by the loader's stage 2, so this module types no channel name of
    its own. A definition that selects several channels joins on the first, the
    same convention matrix_views' owner column uses."""
    from matrix_views import _binding, _names
    named = _names(_binding(_bindings(area), BINDING_TERRITORY), "channels")
    if not named:
        raise AgendaError(
            f'{AGENDA_DEFINITION}.yaml: binding "{BINDING_TERRITORY}" names no '
            f"channel for the roles join, so no need can be attributed to a "
            f"role")
    return named[0]


# --------------------------------------------------------------------------- #
# Role resolution — against the area's registry, refusing BY NAME
# --------------------------------------------------------------------------- #

def _registry(area: Path):
    """The area's role registry, through the shared resolver.

    `people.People` is the engine's roles.yaml reader (slug -> canonical name,
    aliases, the people who hold it, and the org-chart rank behind
    `contact_for_role`); reusing it means an agenda and a review kit can never
    disagree about who a role is."""
    import people
    return people.People(area)


def known_roles(area) -> list[str]:
    """The role slugs this area's registry declares, registry order."""
    return list(_registry(Path(area)).role_names)


def resolve_role(area, role: str) -> str:
    """The registry slug for what the caller asked for, or a refusal naming it.

    Matched, in order, against the slug, the canonical name and each alias —
    case- and space-insensitively, because a human types "AP Manager" as
    readily as `ap-manager`. Deterministic string work, no judgment: an
    unrecognised role is a REFUSAL rather than a best guess, because an agenda
    addressed to the wrong person is worse than no agenda."""
    reg = _registry(Path(area))
    asked = " ".join(str(role or "").split()).strip().lower()
    if not asked:
        listed = ", ".join(reg.role_names) or "none — this area declares no roles"
        raise AgendaError(
            f"interview agenda: no role named, so there is nobody to address "
            f"the agenda to (this area's registry declares: {listed})")
    for slug in reg.role_names:
        candidates = [slug, reg.role_names[slug]] + reg.role_aliases.get(slug, [])
        if any(asked == " ".join(str(c).split()).strip().lower()
               for c in candidates):
            return slug
    raise AgendaError(
        f'interview agenda: no role "{role}" in area '
        f"{Path(area).resolve().name or area} — its registry declares "
        f"{', '.join(reg.role_names) or 'no roles at all'} "
        f"(_reference/roles.yaml). An agenda is addressed to somebody the "
        f"record knows.")


# --------------------------------------------------------------------------- #
# Territory — the mechanical role join
# --------------------------------------------------------------------------- #

def territory(area, slug: str) -> dict:
    """What the record puts in one role's hands, in the area's own order.

    `{"entities": [step slug, …], "headings": {slug: heading},
      "nodes": [node slug, …]}` — the steps whose bound channel names the role,
    and the taxonomy nodes any of those steps is covered by. Manifest order for
    the steps (the manifest is membership/ordering authority), node order for the
    nodes. An area with no steps, no manifest or no channel data yields empty
    lists — a thin area, not a defect."""
    area = Path(area)
    try:
        channel = _role_channel(area)
    except Exception:
        return {"entities": [], "headings": {}, "nodes": []}

    mine: list[str] = []
    headings: dict[str, str] = {}
    try:
        import kernel
        from matrix_views import STEP_TYPE, _steps
        tdecl = kernel.load_type(STEP_TYPE)
        found = _steps(area, tdecl)
    except Exception:
        found = []
    for step in found:
        named = [str(s) for s in (step["entity"].bindings().get(channel) or [])]
        if slug in named:
            mine.append(step["slug"])
            headings[step["slug"]] = step["heading"]

    nodes: list[str] = []
    if mine:
        try:
            import plan_views
            relation = plan_views.node_steps(area)
        except Exception:
            relation = {}
        for node, covered in relation.items():
            if any(s in mine for s in covered) and node not in nodes:
                nodes.append(node)
    return {"entities": mine, "headings": headings, "nodes": nodes}


# --------------------------------------------------------------------------- #
# The needs join
# --------------------------------------------------------------------------- #

def _entries(area: Path) -> list[dict]:
    """M44's needs view for this area's objective targets — the whole feed.

    Raises only what the needs view raises (an uninstalled deliverable named by
    an objective: the loader's refusal, which names it). No objective → `[]`."""
    import needs
    return needs.needs(area)


def _conflict_nature(area: Path):
    """The DECLARED nature value that means "two sources disagree", or `None`.

    Resolved, never typed: the gap callout prefix comes from the definition
    binding (`kinds.gap_prefix`, the same read needs.py's recorded feed does)
    and the vocabulary off that callout's declared `field_enums`
    (`kinds.declared_natures`). The first declared value is the conflict mint —
    the positional rule documented in the module docstring, stated there once.
    Anything unresolvable (no enum, no declaration, an area whose bindings do not
    name one gap kind) yields `None`, which leaves every recorded gap in the
    confirm section: a "not yet", never a crash."""
    try:
        import kernel
        import kinds
        from matrix_views import STEP_TYPE
        tdecl = kernel.load_type(STEP_TYPE)
        declared = kinds.declared_natures(tdecl, kinds.gap_prefix(tdecl, area))
    except Exception:
        return None
    for value in declared.values():
        return value
    return None


def _split_recorded(area: Path, recorded: list[dict]) -> tuple[list, list]:
    """`(settle, confirm)` — the recorded-gap feed split on the declared nature.

    Feed order preserved in both halves. An entry goes to `settle` only when its
    `nature` key equals the declared conflict value; the declared
    evidenced-absence value and a MISSING key both stay in `confirm`, so legacy
    and v1-grammar fragments render where they always did."""
    conflict = _conflict_nature(area)
    settle, confirm = [], []
    for entry in recorded:
        mine = (conflict is not None and entry.get("nature") == conflict)
        (settle if mine else confirm).append(entry)
    return settle, confirm


def _for_role(area: Path, entries: list[dict], terr: dict) -> dict:
    """The needs entries this role can answer, split by feed.

    The attribution rule per feed, and nothing beyond it:
      * a recorded gap sits on a step — it is theirs when the step is theirs;
      * a coverage entry sits on a taxonomy node — theirs when the node covers a
        step of theirs;
      * an unserved binding sits on the DELIVERABLE, not on any step, so it is
        area-level ground: shown to a role with territory here (they can speak to
        their area) and withheld from a role with none, because attributing it to
        somebody the record never places in this area would be a guess."""
    import needs
    mine_steps = set(terr["entities"])
    mine_nodes = set(terr["nodes"])
    out = {kind: [] for kind in needs.KIND_ORDER}
    for entry in entries:
        kind, where = entry["kind"], entry["where"]
        if kind == needs.KIND_RECORDED and where in mine_steps:
            out[kind].append(entry)
        elif kind == needs.KIND_COVERAGE and where in mine_nodes:
            out[kind].append(entry)
        elif kind == needs.KIND_UNSERVED and mine_steps:
            out[kind].append(entry)
    return out


# --------------------------------------------------------------------------- #
# The ledger join — what they gave us that we still owe a read on
# --------------------------------------------------------------------------- #

def _owed(area: Path, terr: dict) -> list[dict]:
    """`[{id, file, slugs, note}]` — the ledger rows still outstanding for this
    role's territory, ledger order.

    `ledger.outstanding(root, area)` IS the question "what does this area still
    owe a read on", derived by the ledger from `touches ⊄ consumed` rather than
    from file position; the territory filter turns it into "…of what this person
    gave us". A source fully consumed for their steps never appears — the M40
    rule that an agenda must not ask for what we hold, applied to the one section
    where holding it is the point."""
    try:
        import kinds
        root = kinds.engagement_root(area)
    except Exception:
        return []
    import ledger
    name = area.resolve().name or area.name
    try:
        pending = ledger.outstanding(root, name)
        rows = ledger.area_view(root, name)
    except Exception:
        # A missing or unreadable ledger is a "not yet", not a broken agenda.
        return []
    mine = set(terr["entities"])
    out: list[dict] = []
    for row in rows:
        left = [s for s in (pending.get(row["id"]) or []) if s in mine]
        if not left:
            continue
        out.append({"id": row["id"], "file": row.get("file") or "",
                    "slugs": left, "note": row.get("note") or ""})
    return out


def _held(area: Path, terr: dict) -> list[str]:
    """The SRC ids the ledger already holds against this role's territory,
    ledger order. Shown beside the asks so nothing already in hand is requested
    again (the M40 rule's other half)."""
    try:
        import kinds
        root = kinds.engagement_root(area)
    except Exception:
        return []
    import ledger
    name = area.resolve().name or area.name
    try:
        rows = ledger.area_view(root, name)
    except Exception:
        return []
    mine = set(terr["entities"])
    return [row["id"] for row in rows
            if any(s in mine for s in (row.get("touches") or []))]


# --------------------------------------------------------------------------- #
# The render
# --------------------------------------------------------------------------- #

#: The five section headings, and the client-facing lead-in each one opens with
#: (the plan_views idiom: an italic lead-in, then list content, `—` for an empty
#: section — an empty section must read as an answer, never as a failed build).
LEAD_SETTLE = (
    "_Points where two sources in the record disagree with each other: we hold "
    "both readings and cannot tell from the paper which one is right. We are "
    "asking you to settle each one — which account is true._")
LEAD_CONFIRM = (
    "_Points where the accounts we hold do not yet agree, or where the record "
    "says the answer is still open. We have deliberately not guessed at any of "
    "them — we would rather you settled each one._")
LEAD_MISSING = (
    "_Areas of your process we cannot yet document with confidence. A "
    "walkthrough, an existing procedure, a screenshot or a short written answer "
    "are all equally welcome._")
LEAD_UNASKED = (
    "_Ground we have not covered with anyone yet: what the document we are "
    "producing still needs before it can be written._")
LEAD_OWED = (
    "_What you have already given us and we have not finished working through. "
    "Nothing here is a request — it is on us, and it is listed so you know we "
    "have it._")

PREAMBLE = (
    "_Everything below comes from the record as it stands today: your own "
    "walkthroughs, the documents you have given us, and the points where two "
    "readings of the process differ. Nothing here is a finding, and nothing is "
    "ranked — what is worth the time in the meeting is a judgment for the "
    "meeting._")


def _bullet(entry: dict, headings: dict) -> list[str]:
    """One agenda item: the need in the record's own words, then its mechanical
    grounds — the same grounds the needs view carries, unedited, so a reader can
    always see why the item is on the page."""
    where = entry["where"]
    label = headings.get(where, where)
    lines = [f"- **{label}** — {entry['need']}"]
    for ground in entry["grounds"]:
        lines.append(f"    - _{ground}_")
    return lines


def render(area, role=None) -> str:
    """The interview agenda for one role in one area, as markdown.

    `role` is a registry slug, canonical name or alias (see `resolve_role`); an
    unknown one raises `AgendaError` naming it. A role whose territory carries
    nothing to ask gets a short honest agenda that says so — never an exception
    and never an empty string. Read-only and deterministic."""
    import needs

    area = Path(area)
    slug = resolve_role(area, role)
    reg = _registry(area)
    name = reg.role_names.get(slug, slug)
    contact = reg.contact_for_role(slug)

    terr = territory(area, slug)
    grouped = _for_role(area, _entries(area), terr)
    owed = _owed(area, terr)
    held = _held(area, terr)

    who = f"{name} ({slug})" + (f" — {contact}" if contact else "")
    lines = [f"# Interview agenda — {who}", ""]

    import client_config
    try:
        objective = client_config.objective(area)
        lines += [f"_{objective.report_line()}_", ""]
    except Exception:
        pass

    if terr["entities"]:
        covered = ", ".join(terr["headings"][s] for s in terr["entities"])
        lines += [f"_Territory on the record: {covered}._", ""]
    else:
        lines += ["_The record does not yet place this role on any part of the "
                  "process in this area, so this agenda is deliberately "
                  "short._", ""]
    if held:
        lines += [f"_Already in hand from this territory: {', '.join(held)} — "
                  f"please do not send them again._", ""]
    lines += [PREAMBLE, ""]

    settle, confirm = _split_recorded(area, grouped[needs.KIND_RECORDED])
    sections = [
        ("What we need you to settle", LEAD_SETTLE, settle),
        ("What we would like to confirm", LEAD_CONFIRM, confirm),
        ("What we believe is missing", LEAD_MISSING,
         grouped[needs.KIND_COVERAGE]),
        ("What we have not asked about yet", LEAD_UNASKED,
         grouped[needs.KIND_UNSERVED]),
    ]
    asked = 0
    for title, lead, items in sections:
        lines += [f"## {title}", "", lead, ""]
        if not items:
            lines += ["—", ""]
            continue
        asked += len(items)
        for entry in items:
            lines += _bullet(entry, terr["headings"])
        lines.append("")

    lines += ["## What you gave us that we still owe a read on", "", LEAD_OWED,
              ""]
    if not owed:
        lines += ["—", ""]
    else:
        for row in owed:
            where = ", ".join(terr["headings"].get(s, s) for s in row["slugs"])
            lines.append(f"- **{row['id']}** — {row['file']} (still to work "
                         f"through for: {where})")
            if row["note"]:
                lines.append(f"    - _{row['note']}_")
        lines.append("")

    if not asked and not owed:
        lines += ["_We have nothing outstanding for this role right now: the "
                  "record is square with what we hold. This meeting is a "
                  "confirmation, not a collection._", ""]
    return "\n".join(lines).rstrip() + "\n"


def build_interview_agenda(ctx) -> str:
    """`interview-agenda` — the view builder, over `ctx["area"]`.

    Registered through `aggregate.PY_BUILDERS` (one import + one entry, the
    plan_views/needs pattern). `ctx["role"]` renders one agenda; without it,
    every role the area's registry declares that HAS territory here gets one, in
    registry order — the plan path can carry no role argument, and rendering a
    role-less agenda would be a document about nobody. Read-only.

    THIS IS NOT AN AUTOMATIC TRIGGER: the builder runs only where a human has
    asked for this deliverable to be materialized. No agent loop reaches it."""
    area = (ctx or {}).get("area")
    if not area:
        raise KeyError(
            f"{AGENDA_KIND}: the builder ctx carries no 'area' — an agenda is "
            f"rendered over an engagement area (see agenda.py)")
    area = Path(area)
    role = (ctx or {}).get("role")
    if role:
        return render(area, role=role)
    parts = [render(area, role=slug) for slug in known_roles(area)
             if territory(area, slug)["entities"]]
    if not parts:
        return ("—\n\n_No role in this area's registry is placed on any part of "
                "the process yet, so there is nobody to hold an agenda for._")
    return "\n".join(parts).rstrip()


# --------------------------------------------------------------------------- #
# CLI — the HUMAN trigger, and the only one
# --------------------------------------------------------------------------- #

USAGE = "usage: agenda.py <area> --role SLUG"


def main(argv=None) -> int:
    """Print one role's interview agenda. 0 on a printed agenda (including the
    honest short one), 2 on bad usage, an area that is not a directory, an
    unknown role, or a deliverable the objective names and nobody installed."""
    argv = list(sys.argv[1:] if argv is None else argv)
    area = None
    role = None
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--role":
            if i + 1 >= len(argv):
                print(f"agenda.py: --role needs a role\n{USAGE}",
                      file=sys.stderr)
                return 2
            role = argv[i + 1]
            i += 2
            continue
        if arg.startswith("--"):
            print(f"agenda.py: unknown option {arg}\n{USAGE}", file=sys.stderr)
            return 2
        if area is not None:
            print(f"agenda.py: unexpected argument {arg}\n{USAGE}",
                  file=sys.stderr)
            return 2
        area = arg
        i += 1

    if area is None or not role:
        print(USAGE, file=sys.stderr)
        return 2
    path = Path(area)
    if not path.is_dir():
        print(f"agenda.py: {area} is not a directory", file=sys.stderr)
        return 2
    try:
        print(render(path, role=role))
    except Exception as exc:            # AgendaError / loader-grade, all named
        print(f"agenda.py: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":            # pragma: no cover
    raise SystemExit(main())
