#!/usr/bin/env python3
"""orchestrate.py — the CONSULT read-only state advisor (M7).

Given an engagement *area* folder, derive the SINGLE next action from folder
state and print it (``next --area <area> --json``). The advisor (``next`` /
``decide``) **never mutates**: it is a pure function of on-disk state, so
re-running it is always safe and idempotent (M7 "Design note"). The only
mutating pieces hosted here are the centralized signal-file writers (emit_*),
the two human-acceptance verbs (``accept`` → ``.render.json``, ``accept-draft``
→ ``.draft_ready.json``: each the SOLE writer of its flag) and the ``checkpoint``
subcommand — a git commit of the area folder the driver
runs after each successful mutating stage, so engagement state is durable
without any agent remembering to commit. All state changes happen in the stage
scripts (scaffold/aggregate/reconcile/render) and the subagents' writes; the
driver skill (skills/consult-orchestrate/SKILL.md) performs them.

Precedence (M7 table) — evaluated top to bottom, FIRST MATCH WINS:

  1  confirm          _reference/.proposed/ exists           (HUMAN GATE)
  2  apply_review     _review/<live-slug>.notes.yaml present
                      (M32 step-aside: defers to guard 5 when unassessed
                      sources also wait AND every queued item's kind is
                      merge-safe — see MERGE_SAFE_NOTE_KINDS — so one
                      drafter batch carries notes + sources together)
 2b  review_triage    notes naming no live slug / _unassigned  (HUMAN GATE)
  3  taxonomy         no manifest.json AND _sources/new/*     (mode=initial)
  4  fill             manifest AND any procedure `unfilled`
4.5  reprofile        profile section(s) absent from N fragments (HUMAN GATE)
  5  taxonomy         manifest AND UNASSESSED _sources/new/*  (mode=incremental)
 5a  unresolvable     every source in new/ assessed + unconsumable (HUMAN GATE)
 5b  unresolvable     manifest slug whose fragment is absent   (HUMAN GATE)
  6  aggregate        procedure/registry hash changed vs aggregate state
  7  registry_topup   aggregate emitted unmatched-mention warnings (HUMAN GATE)
  8  reconcile        derived views not clean/current this pass
8.5  draft_ready      a spend is due and the draft is not accepted (HUMAN GATE)
  9  synthesize       procedures changed vs synthesis basis / pending placeholders
 10  render           all views current+reconciled, no fresh .docx
 11  review           rendered, awaiting human review           (HUMAN GATE)
 12  done             nothing outstanding

STICKY HOLDS (M17) sit OUTSIDE that table: `hold:` in `_client/consult.yaml`
(area list shadows engagement) turns any of HOLDABLE_ACTIONS into a human gate —
the SAME action, with `human_gate: true` and `details.held_by`. It never skips,
never reorders and never forces, so the ladder above is untouched: the hold only
decides whether a human sees the next action before it runs. Holding something
that is already a stop (a gate, `done`, `error`) is a load-time validation error,
and so is an unknown name — see client_config.parse_holds.

The overlap between guards is real (e.g. after scaffold `_sources/new/` is still
full because sources move only after fill) — precedence is what makes the walk
deterministic and non-looping. See M7 "Why the order matters".

THE RESOLVABLE-ACTION INVARIANT (M18) — an action is returnable only if running
it can change the state that selected it. Two non-stage results exist for the
states where nothing satisfies that:

  * ``unresolvable`` (``human_gate: true``) — a RESTING GATE like ``review``, not
    an error: the folder is consistent, the ladder is out of moves. It carries
    ``details.state`` (what was detected), ``details.why_no_stage`` (why no stage
    clears it) and ``details.human_action`` (the specific fix). Reached by a
    stranded source in ``_sources/new/`` (5a, M6/F7), an orphaned manifest slug
    (5b), and by reconcile failures that no producer can regenerate (8).
  * ``error`` (not a gate; ``next`` exits 2) — the area folder does not exist.
    A typo'd ``--area`` used to read as ``done`` (audit F3); it can no longer.

The M18/M6 partitions, all of them pure reads:

  guard 2  a note is applicable only when its basename names a LIVE manifest
           procedure slug; orphans are ``review_triage``. With NO manifest at
           all guard 2 steps aside for guard 3 — nothing can be applied to an
           unscoped area (audit F1).
  guard 5  a file in ``_sources/new/`` is work for the taxonomy agent only while
           it is UNASSESSED — unregistered in ``_reference/sources.yaml``, or
           registered at a different ``hash``. Sources registered at their
           current bytes have already been read and proposed against, and the
           guards above have already ruled out the two things that could consume
           them (a pending note, an ``unfilled`` skeleton), so they are stranded:
           ``unresolvable`` naming the ``SRC-`` ids (audit F7 / M6).
  guard 4.5 the DOCUMENT PROFILE (M14) is a pure read too, and so is its drift
           signal: a fragment missing a `### X.` heading the profile requires
           predates the profile change. No `profile_hash` in the manifest —
           nothing to keep in sync, it survives hand edits, and it is
           per-procedure rather than all-or-nothing. Inert when no layer
           supplies a `profile:` key (there is no requirement to drift from).
  guard 8  when reconcile's recorded failures (``.reconcile.json``
           ``failing_files``) are confined to agent-owned derived views the
           change signal already marks stale, ``synthesize`` takes precedence:
           the producer runs, then reconcile re-verifies. Failures touching
           drafter-owned fragments are ``unresolvable`` (audit F8).

STATE FILES (all git-ignored, at the area root) — the advisor only READS these;
the named stage script WRITES each. This is the M7 orchestration contract:

  .aggregate.json  written by aggregate.py:
      {"proc_hashes": {slug: {file: sha}}, "registry_hash": sha,
       "warnings": [ ... ]}
      Records the procedure + registry state aggregate last consumed, plus the
      unmatched-mention WARNINGs it emitted (the registry top-up worklist).
      `proc_hashes` is per FILE inside each slug (M18/F5) so a duplicate slug
      cannot drop a file's hash out of the change signal.
  .hashes.json     written by scope_delta.commit (the driver runs it after each
      M5 agent succeeds — see the orchestrate skill's `synthesize` handler):
      {derived_kind: {slug: sha}}  — a per-kind baseline of the procedure hashes
      each agent-owned file was last built from. The "M5 change signal" (README
      folder model): scope_delta.changed_procedure_slugs compares current hashes
      against a kind's baseline to re-derive only changed procedures.
  .reconcile.json  written by reconcile.py:
      {"basis": sha, "clean": bool, "failing_files": [rel, ...]}  — the combined
      hash of procedures+derived+manifest at the last reconcile, whether it
      passed, and (M18/F8) the area-relative files its errors named. The
      `failing_files` key is OPTIONAL: absent means "not recorded" and guard 8
      then behaves exactly as it did before M18.
  .draft_ready.json  written ONLY by `accept-draft` (M17):
      {"draft_basis": sha, "accepted": true}
      The human's answer to "am I happy with the verbs and the nouns" at guard
      8.5, keyed to the TWO DATABASES ONLY (procedures + registry), never to
      basis_hash — see AreaState.draft_basis().
  .consolidate.json  written ONLY by `consolidate.py mark` (M12):
      {"draft_basis": sha}
      The last consolidation pass, keyed like .draft_ready.json to the two
      databases — surfaced in the draft-ready gate's `consolidate` answer as
      consolidated_at_basis (informational; never a guard: the stage is
      human-invoked and the advisor never demands it).
  .render.json     written by the renderer (M4):
      {"basis": sha, "docx": path, "awaiting_review": bool}

If a state file is absent, its stage is treated as never-run (so the guard that
would run it fires). This keeps a fresh area walking forward from zero state.
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

import argparse
import glob
import hashlib
import json
import os
import re
import sys

import console_compat  # noqa: F401  (stdout errors='replace' on narrow consoles)

# --- doc_model is OWNED BY M2 (do not create it here) -----------------------
# Prefer the shared spine's load_manifest. Until M2 lands, degrade to a minimal
# json read of manifest.json so the advisor is runnable in isolation; the
# contract is still "import load_manifest from doc_model".
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from doc_model import load_manifest  # type: ignore
except Exception:  # pragma: no cover - fallback only until M2 ships doc_model
    def load_manifest(folder: str) -> dict:
        with open(os.path.join(folder, "manifest.json"), encoding="utf-8") as fh:
            return json.load(fh)

# The SECTION REGISTRY (M23) is doc_model's too: guard 4.5 asks "which sections
# does this fragment carry?", and the answer must be slugs, not letters.
import doc_model  # noqa: E402

# The `[[slug]]` grammar is owned by callouts.py (shared with aggregate + render).
# Borrowed, never restated, so the M18 diagnosis of a dangling reference cannot
# drift from the reconcile gate that reports it.
try:
    from callouts import XREF_RE, blank_fences as _blank_fences  # type: ignore
except Exception:  # pragma: no cover - callouts is always present
    XREF_RE = re.compile(
        r"\[\[#?([a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)?)\]\]")

    def _blank_fences(text: str) -> str:
        return text

# `_reference/sources.yaml` is OWNED BY sources.py (the `touches` validator, the
# SRC- registry read, and M6's "has the taxonomy agent already read these bytes"
# assessment). Borrowed, never restated, so guard 5 and `mark-processed` cannot
# drift apart on what "assessed" means.
try:
    from sources import assess_new_sources as _assess_new_sources  # type: ignore
except Exception:  # pragma: no cover - sources.py ships beside us
    _assess_new_sources = None

# M34: the ONE central-mode detection seam, borrowed the same defensive way.
# Non-None means the engagement carries a central ledger (`_sources/sources.yaml`
# at its root), so the STAGING dir every source guard reads is the root's
# `_sources/new/`, not the area's. None (or an unimportable sources.py) means v1:
# every path below is byte-identical to pre-M34.
try:
    from sources import central_root as _central_root  # type: ignore
except Exception:  # pragma: no cover - sources.py ships beside us
    _central_root = None

#: M37 dispatch hints: which agent BRIEF serves the `taxonomy` action in central
#: mode, by mode. The action name is deliberately stable (v1 tests pin it, and
#: the ladder's shape is the contract) — only the brief the driver dispatches
#: differs, so this table is the whole of the rename that would otherwise have
#: rippled through the advisor. Since M45 BOTH modes route to the one
#: taxonomist brief — the mode still selects which half of its contract the
#: dispatch prompt emphasizes: `initial` = structure + sufficiency +
#: information requests, before drafting spends tokens; `incremental` = the
#: delta plus curation (M6's reassessment and M24's placement pass, unified).
#: Since M52 the value is the ONE assembled work-order COMMAND
#: (`brief.py taxonomist`, agent contract `agents/consult-taxonomist.md`),
#: with the dispatch kind the mode maps to — the kind selects emphasis, never
#: content. Paths are plugin-relative, like every other path in the skill
#: prose; `<area>` is the driver's substitution.
_CENTRAL_TAXONOMY_BRIEFS = {
    "initial": "scripts/brief.py taxonomist <area> --kind SCOPING",
    "incremental": "scripts/brief.py taxonomist <area> --kind CURATION",
}

# NOTE KINDS are owned by notes_util (the M6 bus contract). Borrowed for the
# guard-2 step-aside (M32) only: the advisor reads each queued item's `kind`
# to decide whether the notes are merge-safe, never to route or apply them.
try:
    from notes_util import load_items_from as _load_note_items  # type: ignore
except Exception:  # pragma: no cover - notes_util ships beside us
    _load_note_items = None

#: The guard-2 step-aside ALLOWLIST (M32): queued notes defer to incremental
#: taxonomy — so one drafter batch carries notes + new sources together —
#: only when EVERY queued item's kind is in this set. These kinds never
#: change the procedure set, so tagging sources first cannot mis-tag.
#: Anything else (consolidation, rename, retirement, an unknown or missing
#: kind, an unreadable file) keeps the old order: safe-by-default, new kinds
#: are slow-and-right until proven merge-safe and added here.
MERGE_SAFE_NOTE_KINDS = frozenset({"review", "source"})

# The DOCUMENT PROFILE is owned by client_config (M13 resolution, M14 profile).
# Borrowed for guard 4.5 only: the advisor reads the profile to see which
# fragments predate a profile change, and never decides shape itself.
try:
    import client_config  # type: ignore
except Exception:  # pragma: no cover - client_config ships beside us
    client_config = None


# --------------------------------------------------------------------------- #
# Small filesystem / hashing helpers (deterministic, read-only)
# --------------------------------------------------------------------------- #

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _file_sha(path: str) -> str:
    with open(path, "rb") as fh:
        return _sha(fh.read())


def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _load_json(path: str):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


def _area_local_entry(entry: dict, area: str) -> dict:
    """A source entry with `touches`/`consumed` guaranteed FLAT for `area`.

    v1 entries already carry flat area-local lists and pass through unchanged
    (copied, never mutated). A central-mode ledger entry carries NAMESPACED MAPS
    (`{area: [slugs]}`) covering every area it touches, so this takes this area's
    slice — the only slugs this area's guards may reason about."""
    out = dict(entry)
    for key in ("touches", "consumed"):
        value = out.get(key)
        if isinstance(value, dict):
            out[key] = list(value.get(area) or [])
    out.setdefault("id", "")
    return out


def _dir_has_files(path: str) -> bool:
    """True iff `path` is a directory containing at least one regular file
    (recursively; ignores empty dirs and dotfiles like .gitkeep)."""
    if not os.path.isdir(path):
        return False
    for _root, _dirs, files in os.walk(path):
        for name in files:
            if not name.startswith("."):
                return True
    return False


def _unrouted_sources(central_root: str) -> list[str]:
    """The files staged in `<root>/_sources/new/` that the ledger does not
    know — root-relative, in directory-listing order (M68).

    Central mode only, and the discriminator is REGISTRATION, not hash: a file
    with no entry has no SRC id, so a scoping dispatch against it can only
    propose `sources: []`. Matched by basename, because that is what the
    ledger's `file` records (`_sources/new/<name>`) and a consumed source
    moves to `processed/` without ceasing to be routed.

    Degrades to "nothing unrouted" whenever the ledger cannot be read: an
    unreadable ledger is the loaders' error to raise, never a reason for the
    advisor to invent a gate.
    """
    new_dir = os.path.join(central_root, "_sources", "new")
    if not os.path.isdir(new_dir):
        return []
    try:
        import ledger
        known = {os.path.basename(str(e.get("file") or "").replace("\\", "/"))
                 for e in ledger.entries(central_root)}
    except Exception:
        return []
    out = []
    for name in sorted(os.listdir(new_dir)):
        if name.startswith("."):
            continue
        if not os.path.isfile(os.path.join(new_dir, name)):
            continue
        if name not in known:
            out.append("_sources/new/" + name)
    return out


def _engagement_areas(central_root: str) -> list[str]:
    """The scoped areas under `<root>/components/`, name order — `_client` and
    other underscore/dot layers excluded (they are layers, not areas)."""
    comps = os.path.join(central_root, "components")
    if not os.path.isdir(comps):
        return []
    return sorted(n for n in os.listdir(comps)
                  if os.path.isdir(os.path.join(comps, n))
                  and not n.startswith(("_", ".")))


def resolve_area(area: str) -> str:
    """Accept either a path to the area folder or a bare area name resolved
    under components/. Returns an absolute-ish folder path.

    NOTE (M18/F3): the returned path is NOT guaranteed to exist — a bare name
    with no folder still resolves to the components/ candidate so `checkpoint`
    and the "not scoped yet" messages can talk about where the area WOULD live.
    Existence is `decide()`'s business: it returns the `error` result for a
    folder that is not there, so a typo can never read as `done`."""
    if os.path.isdir(area):
        return area.rstrip("/")
    candidate = os.path.join("components", area)
    if os.path.isdir(candidate):
        return candidate
    # Return the components/ candidate anyway so downstream "missing manifest"
    # logic can still fire on a not-yet-created area.
    return candidate


# --------------------------------------------------------------------------- #
# State extraction
# --------------------------------------------------------------------------- #

UNFILLED_RE = re.compile(r"(<!--\s*unfilled\s*-->)|(status\s*:\s*unfilled)", re.I)
PENDING_RE = re.compile(r"_Pending synthesis", re.I)
# A `###` sub-section heading inside a procedure fragment (M14 guard 4.5).
# The HEADING IS THE SIGNAL: scaffold always writes one per profile section, so
# a fragment missing one predates the profile change. No state file, nothing to
# keep in sync, and it survives hand edits.
#
# M23: keyed on the section SLUG the shared registry resolves the heading to,
# not on the letter — `### Key Controls` and a not-yet-migrated
# `### F. Key Controls` are the same section, so the migration itself can never
# read as profile drift.
def _present_sections(text: str, resolver=None) -> set:
    """The section slugs a fragment carries.

    `resolver` is the area's CAPTURE-TYPE heading parser (M66 A2/1,
    `kernel.heading_resolver`); with none supplied the v1 parser answers, which
    is what it always answered. On a process-step fragment the v1 parser
    mis-files `### Inputs` and cannot see `### Transformation` / `### Issues`
    at all — and guard 4.5 would then report them permanently missing and
    dispatch a reprofile wave that can never terminate."""
    resolve = resolver or doc_model.section_of_heading
    return {s for line in text.splitlines()
            if (s := resolve(line)) is not None}


class AreaState:
    def __init__(self, folder: str):
        self.folder = folder
        self.manifest_path = os.path.join(folder, "manifest.json")
        self.has_manifest = os.path.isfile(self.manifest_path)
        self.manifest = load_manifest(folder) if self.has_manifest else None

        self.proposed_dir = os.path.join(folder, "_reference", ".proposed")
        # M34: in central mode the staging dir is the ENGAGEMENT's `_sources/new/`
        # (one drop point for every area); in v1 it is the area's own.
        self.central_root = _central_root(folder) if _central_root else None
        self.sources_new = os.path.join(self.central_root or folder,
                                        "_sources", "new")

        # procedure + derived components from the manifest
        self.procedures = []   # list of (slug, abspath)
        self.upstream = {}     # slug -> [upstream slugs] (M11 ordering hints)
        # M74: slug -> the taxonomist's confidence call, only where the
        # manifest carries one. A missing slug is NO OPINION, which behaves
        # as `high` — so a pre-M74 manifest partitions exactly as it did.
        self.confidence = {}
        self.agent_derived = []  # abspaths of writer==agent derived files
        self.derived_files = []  # all derived abspaths
        # M14: the agent-owned derived KINDS this manifest actually lists. The
        # manifest is the profile's footprint (scaffold lists only what the
        # profile asks for), so a `derived:` set without `raci` yields no raci
        # kind here — and guard 9 therefore never dispatches that agent. Read
        # from the manifest rather than a constant so absent-from-manifest means
        # absent-from-signal, which is the fail-safe direction: an unlisted view
        # has no file, no writer and nothing to be stale against.
        self.agent_derived_kinds = []
        # M18: who owns each manifest file, keyed by the area-relative path
        # reconcile names in its error messages ("procedure" | "agent-derived" |
        # "python-derived"). The guard-8 partition reads nothing else.
        self.owner_of = {}
        if self.manifest:
            for c in self.manifest.get("components", []):
                path = os.path.join(folder, c["file"])
                role = c.get("role")
                if role == "procedure":
                    slug = c.get("slug", c["file"])
                    self.procedures.append((slug, path))
                    self.owner_of[c["file"]] = "procedure"
                    if c.get("upstream"):
                        self.upstream[slug] = list(c["upstream"])
                    if c.get("confidence"):
                        self.confidence[slug] = str(c["confidence"])
                elif role == "derived":
                    self.derived_files.append(path)
                    if c.get("writer") == "agent":
                        self.agent_derived.append(path)
                        self.owner_of[c["file"]] = "agent-derived"
                        kind = c.get("derived_kind")
                        if kind and kind not in self.agent_derived_kinds:
                            self.agent_derived_kinds.append(kind)
                    else:
                        self.owner_of[c["file"]] = "python-derived"

    @property
    def procedure_slugs(self):
        """The live procedure slugs — the manifest is the only authority on
        which procedures exist (M18 guard-2 partition + xref diagnosis)."""
        return {slug for slug, _p in self.procedures}

    def owner(self, rel: str) -> str:
        """Who writes the area-relative file `rel`: "procedure",
        "agent-derived", "python-derived", "manifest" or "other" (a path outside
        the manifest, e.g. `_reference/sources.yaml`)."""
        rel = rel.replace(os.sep, "/")
        if rel.startswith("./"):
            rel = rel[2:]
        if rel == "manifest.json":
            return "manifest"
        return self.owner_of.get(rel, "other")

    # ---- guard signals ----------------------------------------------------

    def returned_files(self):
        """Un-ingested review-kit returns (M9/M10): anything the human dropped
        into _review/returned/ — reviewed docs, gap workbooks, screenshot
        templates. Ingestion scripts consume + archive them."""
        pat = os.path.join(self.folder, "_review", "returned", "*")
        return sorted(p for p in glob.glob(pat) if os.path.isfile(p))

    NOTES_SUFFIX = ".notes.yaml"

    def note_slug(self, path: str) -> str:
        """The procedure slug a notes file is anchored to: notes are written as
        `_review/{slug}.notes.yaml` by every producer on the M6 notes bus."""
        return os.path.basename(path)[: -len(self.NOTES_SUFFIX)]

    def review_notes(self):
        """Un-archived procedure-anchored review notes (M8), partitioned into
        ``(applicable, orphaned)`` — M18/F1.

        Excludes _review/processed/ and the _unassigned bucket (items
        review_extract could not attribute to a procedure — those need a human,
        not a drafter dispatch; surfaced separately via unassigned_notes()).

        A note is APPLICABLE only when its basename names a live manifest
        procedure slug: `apply_review` dispatches an update drafter for that
        procedure and the note is archived only after the drafter succeeds, so a
        note for a procedure that does not exist can never clear by machine.
        Orphans route to the `review_triage` gate instead. With no manifest at
        all every note is orphaned — nothing is applicable to an unscoped area.
        """
        pat = os.path.join(self.folder, "_review", "*" + self.NOTES_SUFFIX)
        found = sorted(p for p in glob.glob(pat)
                       if os.path.basename(p) != "_unassigned" + self.NOTES_SUFFIX)
        live = self.procedure_slugs
        applicable = [p for p in found if self.note_slug(p) in live]
        orphaned = [p for p in found if self.note_slug(p) not in live]
        return applicable, orphaned

    def unassigned_notes(self):
        """Path to _review/_unassigned.notes.yaml if present, else None."""
        p = os.path.join(self.folder, "_review", "_unassigned.notes.yaml")
        return p if os.path.isfile(p) else None

    def queued_note_kinds(self):
        """Every `kind:` across the APPLICABLE queued notes (M32) — the
        guard-2 step-aside asks whether all queued work is merge-safe. Pure
        read. Conservative on any defect: an unreadable file, a kind-less
        item, or an unavailable loader contributes "?" so the caller stays
        on the old ordering."""
        kinds: set[str] = set()
        applicable, _ = self.review_notes()
        for p in applicable:
            if _load_note_items is None:
                return {"?"}
            try:
                for it in _load_note_items(p):
                    kinds.add(str(it.get("kind") or "?").strip() or "?")
            except Exception:
                kinds.add("?")
        return kinds

    def new_source_assessment(self):
        """`(unassessed, assessed)` for `_sources/new/` — guard 5's partition
        (M6/F7), delegated to sources.py, which owns `sources.yaml`.

        Unassessed = registered at a different hash, or not registered at all:
        the taxonomy agent has never read these bytes. Assessed = already read
        and already proposed against, so a taxonomy re-dispatch would propose
        nothing new. Degrades to "everything unassessed" (pre-M6 behaviour:
        `taxonomy`) if sources.py cannot be imported."""
        if _assess_new_sources is None:  # pragma: no cover - sources.py is present
            return ["_sources/new/"], []
        return _assess_new_sources(self.folder)

    def unfilled_slugs(self):
        out = []
        for slug, path in self.procedures:
            if os.path.isfile(path) and UNFILLED_RE.search(_read_text(path)):
                out.append(slug)
        return out

    def profile(self):
        """The resolved document profile, or None when M14 is not in play.

        None means BOTH "client_config is unimportable" and "no layer supplied a
        `profile:` key" — in either case there is no recorded requirement to
        drift from, so guard 4.5 is inert and the ladder behaves exactly as it
        did pre-M14. A MALFORMED profile is not silence: `client_config` raises,
        and the run stops with the file named."""
        if client_config is None:  # pragma: no cover - ships beside us
            return None
        prof = client_config.profile(self.folder)
        return prof if prof.configured else None

    def _heading_resolver(self):
        """The heading parser for THIS area's capture type (M66 A2/1).

        Degrades to the v1 parser when the kernel or client_config is not
        importable — a v1 read of a v1 area is correct, and every stripped
        install is v1."""
        if client_config is None:  # pragma: no cover - ships beside us
            return doc_model.section_of_heading
        try:
            import kernel
            return kernel.heading_resolver(
                client_config.capture_type(self.folder))
        except Exception:      # pragma: no cover - stripped install
            return doc_model.section_of_heading

    def profile_drift(self):
        """{slug: [sections]} — profile sections whose heading is missing from a
        fragment (M14 guard 4.5).

        The drift signal is the missing heading ITSELF: scaffold writes one
        `###` heading per profile section, so a fragment lacking one predates the
        profile change and needs a drafter update pass. Nothing to reconcile
        against a state file, and per-procedure rather than all-or-nothing.

        `body_omit` can never appear here — its sections are in `sections:` and
        their headings are present, which is exactly why omitting one is free
        and reversible. Missing FILES are guard 5b's business, not ours."""
        prof = self.profile()
        if prof is None:
            return {}
        resolver = self._heading_resolver()
        out = {}
        for slug, path in self.procedures:
            if not os.path.isfile(path):
                continue
            present = _present_sections(_read_text(path), resolver)
            absent = [s for s in prof.sections if s not in present]
            if absent:
                out[slug] = absent
        return out

    def proc_hashes(self):
        """{slug: {file: sha}} — the aggregate change signal (guard 6).

        Hashed per FILE inside each slug (M18/F5). The old comprehension was
        keyed by slug alone, so two manifest entries sharing a slug silently
        dropped one file's hash and guard 6 could not see edits to the shadowed
        file; the inner map mirrors basis_hash()'s per-file accumulation, so no
        file can vanish. Slug stays the OUTER key because it is the identity
        every other component uses. A pre-existing .aggregate.json in the old
        {slug: sha} shape simply compares unequal — one harmless aggregate pass
        rewrites it (aggregate is deterministic and idempotent)."""
        out = {}
        for slug, p in self.procedures:
            if os.path.isfile(p):
                rel = os.path.relpath(p, self.folder).replace(os.sep, "/")
                out.setdefault(slug, {})[rel] = _file_sha(p)
        return out

    def missing_procedure_files(self):
        """[(slug, relpath), ...] for manifest procedures with no file on disk.

        Both unfilled_slugs() and proc_hashes() skip a missing file, so without
        this the area reports `aggregate` / "content changed" forever while
        aggregate.py exits 1 on the real cause (M18/F4)."""
        out = []
        for slug, p in self.procedures:
            if not os.path.isfile(p):
                out.append((slug, os.path.relpath(p, self.folder).replace(os.sep, "/")))
        return sorted(out)

    def dangling_xrefs(self, rel_files):
        """{relfile: [slug, ...]} — `[[slug]]` references in the named files
        that no live manifest procedure defines.

        DIAGNOSIS ONLY: reconcile owns the gate and has already reported these;
        decide() re-reads them so an `unresolvable` result can name the
        reference, not just the file."""
        live = self.procedure_slugs
        out = {}
        for rel in rel_files:
            path = os.path.join(self.folder, rel)
            if not os.path.isfile(path):
                continue
            missing = []
            for m in XREF_RE.finditer(_blank_fences(_read_text(path))):
                slug = m.group(1)
                if "/" in slug:
                    # M26 cross-area token — validated against the SIBLING
                    # manifest by reconcile (which owns the gate), never
                    # against this area's live slugs.
                    continue
                if slug not in live and slug not in missing:
                    missing.append(slug)
            if missing:
                out[rel] = missing
        return out

    def registry_hash(self):
        ref = os.path.join(self.folder, "_reference")
        parts = []
        for name in sorted(os.listdir(ref)) if os.path.isdir(ref) else []:
            if name.endswith(".yaml"):
                parts.append(name.encode())
                parts.append(_file_sha(os.path.join(ref, name)).encode())
        return _sha(b"|".join(parts))

    def basis_hash(self):
        """Combined hash of procedures + derived files + manifest — the unit
        reconcile and render gate on."""
        parts = []
        for _slug, p in sorted(self.procedures):
            if os.path.isfile(p):
                parts.append(_file_sha(p).encode())
        for p in sorted(self.derived_files):
            if os.path.isfile(p):
                parts.append(_file_sha(p).encode())
        if self.has_manifest:
            parts.append(_file_sha(self.manifest_path).encode())
        return _sha(b"|".join(parts))

    def draft_basis(self, proc_hashes=None, registry_hash=None) -> str:
        """The M17 draft basis: a hash of the TWO DATABASES the draft-ready gate
        asks about — the procedures (`proc_hashes`) and the registry
        (`registry_hash`). Nothing else.

        Deliberately NOT basis_hash(): that one includes the DERIVED files, so
        `synthesize` rewriting 82/84 would move it and re-open a gate the human
        had just accepted — two accepts for one decision (M17 "Clearing it").
        The gate's question is "am I happy with the verbs and the nouns", so its
        key is exactly the verbs and the nouns: any fragment or registry edit
        re-opens it, derived-view regeneration and renders do not.

        Canonical over the nested {slug: {file: sha}} shape (M18/F5) via
        json.dumps(sort_keys=True) rather than string concatenation, so the key
        cannot drift with dict ordering. Callers that already computed the two
        inputs may pass them in; the default re-reads them."""
        parts = [self.proc_hashes() if proc_hashes is None else proc_hashes,
                 self.registry_hash() if registry_hash is None else registry_hash]
        return _sha(json.dumps(parts, sort_keys=True).encode())

    def pending_placeholders(self):
        """Agent-owned derived files still carrying the M3 pending placeholder."""
        out = []
        for p in self.agent_derived:
            if os.path.isfile(p) and PENDING_RE.search(_read_text(p)):
                out.append(os.path.relpath(p, self.folder))
        return out


# --------------------------------------------------------------------------- #
# Decision (the M7 precedence table)
# --------------------------------------------------------------------------- #

def _synthesis_signal(folder: str, st: "AreaState"):
    """(pending, stale_kinds) — the guard-9 inputs, read once for guards 8+9.

    `pending` is the agent-owned derived files still carrying M3's placeholder.
    `stale_kinds` comes from scope_delta's per-kind .hashes.json baseline (the
    single change-signal authority — no second flat basis here).

    Staleness is accumulated PER KIND (M18/F6): a kind whose delta computation
    raises is skipped, never allowed to discard a kind already found stale. An
    unimportable scope_delta degrades to "synthesize only if pending".

    The KINDS come from the manifest (M14): the document profile decides which
    derived views exist, and a view the profile dropped has no component, no
    file and no writer — so it must not appear in the work order either. Both
    inputs are now manifest-driven, `pending` through the component list and
    `stale_kinds` through `agent_derived_kinds`, which is the fail-safe
    direction: nothing can be dispatched for a view that is not in the document.
    """
    pending = st.pending_placeholders()
    stale_kinds = []
    if st.has_manifest:
        try:
            import scope_delta
        except Exception:  # pragma: no cover - scope_delta ships beside us
            scope_delta = None
        if scope_delta is not None:
            for kind in st.agent_derived_kinds:
                try:
                    if scope_delta.changed_procedure_slugs(folder, kind):
                        stale_kinds.append(kind)
                except Exception:
                    continue  # one kind's failure must not erase another's
    return pending, stale_kinds


#: Every action `decide()` can return that is NOT already a stop — the M17
#: `hold:` vocabulary. A hold turns one of these into a gate without changing it.
HOLDABLE_ACTIONS = ("ingest_returns", "apply_review", "taxonomy", "fill",
                    "aggregate", "reconcile", "synthesize", "render")

#: The actions that are already a stop. Naming one in `hold:` is a validation
#: error, not a no-op — docs/M17-stage-gates.md puts "holding a gate" out of
#: scope, and a silently inert line in a policy file reads as policy in force.
#: `done` and `error` are here too: neither spends anything and neither is a
#: stage, so there is nothing a hold could stop.
#: `route` (M68) is here for the `done`/`error` reason rather than the gate
#: reason: it spends nothing and is not a stage — it hands back the exact
#: `engagement.py route` commands (single-area) or stops for the human's
#: classification (multi-area), so there is nothing a hold could stop.
GATE_ACTIONS = ("confirm", "review_triage", "reprofile", "registry_topup",
                "draft_ready", "review", "unresolvable", "route", "done",
                "error")


def _holds(folder: str):
    """The area's resolved sticky holds (M17). Empty when client_config is
    unimportable or no layer supplies a `hold:` key — pre-M17 behaviour. A
    MALFORMED or typo'd hold list is not silence: client_config raises."""
    if client_config is None:  # pragma: no cover - ships beside us
        return None
    return client_config.holds(folder, HOLDABLE_ACTIONS, GATE_ACTIONS)


def _uncommitted_proposals(folder: str, proposed_dir: str) -> bool:
    """True when the area is in a git work tree and `.proposed/` carries work
    HEAD does not (untracked or modified).

    Advisory only (M65): `--confirm` CONSUMES the proposal set — staged
    taxonomy nodes included — so an un-checkpointed `.proposed/` is evidence
    that exists only until the gate runs. Outside a work tree there is nothing
    to say that `git` in `details` does not already say."""
    import subprocess
    try:
        probe = subprocess.run(
            ["git", "-C", folder, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True)
        if probe.returncode != 0 or probe.stdout.strip() != "true":
            return False
        status = subprocess.run(
            ["git", "-C", folder, "status", "--porcelain", "--", proposed_dir],
            capture_output=True, text=True)
    except OSError:
        return False
    return status.returncode == 0 and bool(status.stdout.strip())


def _ask_register(folder: str):
    """The engagement's ask register module + root, or `(None, None)`.

    ONE conditional seam for every M75 read below, the central-mode pattern
    verbatim: no register file, no engagement root, or an unimportable module
    and the advisor behaves exactly as it did before M75. Nothing here writes,
    and nothing here can raise into a decision."""
    try:
        import asks
        import kinds
        root = kinds.engagement_root(folder)
    except Exception:
        return None, None
    try:
        if not asks.asks_path(root).is_file():
            return None, None
    except Exception:
        return None, None
    return asks, root


def _ask_counts(folder: str) -> dict | None:
    """`{"open": n, "answered": n}` for the gates that size the ask loop
    (M75's advisor signal), or None where there is no register. Open counts
    the outstanding client requests; answered counts the answered-but-unsettled
    ones — the work the engagement now owes itself (invariant 2, surfaced as a
    gate DETAIL and never as an error)."""
    asks, root = _ask_register(folder)
    if asks is None:
        return None
    try:
        return asks.counts(root)
    except Exception:
        return None


def _asks_release(folder: str) -> set:
    """The slugs an ANSWERED, UNSETTLED ask touches (M75 x M74's join).

    The two release rules are ONE rule: M74 says a thin node drafts on new
    evidence or the human's explicit go, and an ask flipping to answered IS
    the arrival of new evidence, made machine-readable. So guard 4's partition
    reads one predicate — `confidence == low AND no answered-unsettled asks
    touching the node` — and this is its second half.

    The mapping goes through the ask's own gap references (everything left of
    the `:` qualifier IS the slug), which keeps the join at node level and
    free: no display-id resolution, no corpus walk, no fragment read."""
    asks, root = _ask_register(folder)
    if asks is None:
        return set()
    try:
        return asks.touched(root, status=asks.ANSWERED, unsettled=True)
    except Exception:
        return set()


def _register_warnings(folder: str, manifest: dict | None) -> int | None:
    """How many check-23 warnings the area carries right now (M73, run-2 7.2).

    Check 23 is `reconcile.check_required_register_fields` — the register cells
    a client deliverable must not ship blank (`reports_to`, a system's role
    text, a PAIN POINT without `Impact:`). WARNING-only, so it never blocks —
    which meant it surfaced only in reconcile output, after drafting had
    already shipped. The draft-ready gate is the last free stop, so the COUNT
    rides in its details: cheap to re-derive, additive, and no severity change.

    Re-derived here rather than read from `.reconcile.json` because that file
    records pass/fail, not warning bodies. Defensive like every other seam
    read in this module: `None` (the key is then omitted) if reconcile is
    unimportable or the check raises. This is the seam M76's open-flag count
    joins — one helper per count, both keys additive in guard 8.5's details.
    """
    if not manifest:
        return None
    try:
        import reconcile as _reconcile
        from pathlib import Path as _Path
        ctx = _reconcile.Ctx(_Path(folder), manifest)
        _reconcile.check_required_register_fields(ctx)
        return len(ctx.warnings)
    except Exception:
        return None


def _open_flags(folder: str) -> int | None:
    """How many OPEN flags this area carries (M76 Part C), or None where the
    area has no flag queue at all (the key is then omitted — a queue-less
    area's gate is byte-identical to pre-M76).

    The seam M73's `_register_warnings` documented: a standalone helper
    feeding an ADDITIVE key in guard 8.5's details, no severity change and
    the `answers` list untouched. ADVISOR-ONLY, never a reconcile check —
    accepting a draft with unactioned flags stays a visible choice, and the
    count is what makes it visible at the last free stop."""
    try:
        import flags as _flags
        if not _flags.flags_path(folder).is_file():
            return None
        return _flags.open_count(folder)
    except Exception:
        return None


def _deliverable_report(folder: str, name: str) -> dict | None:
    """What the area's deliverable would report if it were rendered NOW (M71).

    `{"definition": <name>, "gaps": [...], "note": <one sentence>}` when the
    target reports "not yet"; `{"definition": <name>, "gaps": []}` when it is
    fully serviceable; `None` where the question cannot be asked at all (no
    deliverable is declared, the definition will not resolve, the manifest is
    unreadable).

    The serviceability read is REUSED, never re-derived:
    `definitions.serviceability_records` is the one place a gap is formatted,
    and its `gap` sentences ARE what the flat `definitions.serviceability`
    renders (M51 pins that parity), so this surface cannot disagree with
    brief.py, needs.py or the renderer about what a deliverable still needs.

    Only the ENGAGEMENT-side binding kinds count as "not yet" here —
    `findings:`, `asks:`, `coverage:`, the three whose whole question is what
    the engagement has produced. A declaration-half gap (a registry file the
    area has not got) is a different ladder's business — guard 7's registry
    top-up — and reporting it as the deliverable's "not yet" would make the
    render action noisier for every v1 area without telling the human anything
    the ladder does not already say.

    Read-only and never raising into a decision — the posture every seam read
    in this module has."""
    if not name or name == UNSET_DEFINITION:
        return None
    try:
        import definitions
        defn = definitions.resolve_definition(folder, name)
        records = definitions.serviceability_records(defn, folder)
        bindings = defn.bindings or {}
    except Exception:
        return None

    def _engagement_side(bname: str) -> bool:
        spec = bindings.get(bname) or {}
        return any(k in spec for k in ("findings", "asks", "coverage"))

    gaps = [r["gap"] for r in records if _engagement_side(r.get("binding"))]
    report = {"definition": name, "gaps": gaps}
    if not gaps:
        return report
    unserved = {r.get("binding") for r in records}
    findings_bound = any("findings" in (bindings.get(b) or {})
                         for b in unserved if b in bindings)
    note = ("render would report: not yet — %s" % "; ".join(gaps))
    if findings_bound:
        # A STATEMENT of the path, never a dispatch: the analyst is
        # human-called by design (M39/M49) and no handler fires it.
        note += (". The deliverable renders from ACCEPTED findings and none "
                 "exist yet; the analyst is the human-called verb that "
                 "proposes them — no handler dispatches it, so the human "
                 "decides whether to call one before paying a render")
    else:
        note += (". The human decides whether to close these gaps before "
                 "paying a render")
    report["note"] = note
    return report


def _committed_content(folder: str) -> bool | None:
    """Does the committed tree carry anything under `folder`? (M73, audit 6.1)

    `True` — the folder is absent from disk but HEAD has content under that
    path: a typo, or a deletion. `False` — HEAD has never carried anything
    there: most likely an area that was never scaffolded. `None` —
    INCONCLUSIVE (no git, no commits yet, path outside the work tree, no git
    binary), and guard 0 keeps today's message for it.

    Strictly read-only and cheap: `rev-parse` on the nearest EXISTING ancestor
    (the folder itself is gone, so `git -C <folder>` cannot run) plus one
    `ls-tree` restricted to the path. Nothing is staged, written or fetched.
    """
    import subprocess
    target = os.path.abspath(folder)
    anc = os.path.dirname(target)
    while not os.path.isdir(anc):
        parent = os.path.dirname(anc)
        if parent == anc:
            return None
        anc = parent
    try:
        top = subprocess.run(["git", "-C", anc, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True)
        if top.returncode != 0:
            return None
        root = top.stdout.strip()
        if not root:
            return None
        rel = os.path.relpath(target, root)
        if rel == os.pardir or rel.startswith(os.pardir + os.sep):
            return None
        listing = subprocess.run(
            ["git", "-C", root, "ls-tree", "-r", "--name-only", "HEAD",
             "--", rel],
            capture_output=True, text=True)
    except OSError:
        return None
    if listing.returncode != 0:      # unborn HEAD, or any other refusal
        return None
    return bool(listing.stdout.strip())


def _git_note(folder: str) -> dict | None:
    """None when the area is inside a git work tree; otherwise the advisory
    payload every decision carries. Checked fresh each call (a `git init`
    clears it on the next lap) and cheap (~ms). The suggested init location
    is the ENGAGEMENT ROOT — the parent of components/ — so one repo covers
    every area; an area parked elsewhere suggests its own parent."""
    if not os.path.isdir(folder):
        return None
    import subprocess
    try:
        probe = subprocess.run(
            ["git", "-C", folder, "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True)
    except OSError:
        probe = None
    if probe is not None and probe.returncode == 0 \
            and probe.stdout.strip() == "true":
        return None
    parent = os.path.dirname(os.path.abspath(folder))
    root = (os.path.dirname(parent)
            if os.path.basename(parent) == "components" else parent)
    return {
        "tracked": False,
        "note": ("CHECKPOINTS ARE OFF — this engagement is not in a git "
                 "repository, so there is no history, no diffs to review "
                 "and no revert. Fix once: run `git init` in %s (the "
                 "engagement root). Keep the repository PRIVATE — "
                 "checkpoints deliberately include _sources/ (client "
                 "material)." % root),
        "init_at": root,
    }


def decide(folder: str) -> dict:
    # Resolved after the folder-existence check below, so a typo'd --area still
    # reports `error` rather than failing on a config read. The closure reads it
    # at call time, which is what lets ONE place apply every hold.
    held = {"holds": None}

    def result(action, reason, gate=False, **details):
        d = {"area": folder, "action": action, "reason": reason,
             "human_gate": gate}
        # M17 sticky holds: a held action comes back UNCHANGED except that it is
        # now a gate. Never skipped, never reordered, never forced — the ladder
        # above has already decided what is next, and the hold only decides
        # whether a human sees it first. Applied here, at the single exit point,
        # so no guard can forget it and no guard can be reordered by it.
        holds = held["holds"]
        if holds is not None and action in holds:
            d["human_gate"] = True
            details["held_by"] = holds.held_by(action)
        # Git health, at the single exit point so every decision carries it.
        # Advisory, never a gate: an untracked engagement still builds — it
        # just has no checkpoints, no diffs, no revert, and the human should
        # hear that ONCE rather than discover it after a bad pass.
        note = _git_note(folder)
        if note:
            details["git"] = note
        if details:
            d["details"] = details
        return d

    def taxonomy_result(reason, mode, **details):
        """The `taxonomy` action, plus the M37 dispatch hint.

        The ACTION NAME never changes — v1 tests pin it and the ladder's shape
        is the contract — but in central mode the judgment behind it split in
        two and the briefs are new (M37): the surveyor owns the initial survey
        (structure + sufficiency + information requests), the librarian owns the
        incremental curation pass (M6 reassessment + M24 placement, unified).
        So the advisor states WHICH BRIEF serves this dispatch rather than
        leaving the driver to infer it from mode. Additive and central-only: a
        v1 engagement carries no `brief` key and the caller's v1 behavior (the
        `consult-taxonomy` dispatch) is byte-unchanged. Defensive like every
        other central-mode read here — if the seam is unimportable, `st` has no
        central root and nothing is added."""
        if st.central_root:
            details["brief"] = _CENTRAL_TAXONOMY_BRIEFS.get(
                mode, _CENTRAL_TAXONOMY_BRIEFS["initial"])
        return result("taxonomy", reason, mode=mode, **details)

    def unresolvable(state, why_no_stage, human_action, **details):
        """The M18 terminal gate: a resting result (like `review`), NOT an error
        — the folder is consistent, the ladder is out of moves. Carries what was
        detected, why no stage can clear it, and the fix that would."""
        return result("unresolvable", state, gate=True, state=state,
                      why_no_stage=why_no_stage, human_action=human_action,
                      **details)

    # 0 — the area must exist. resolve_area() happily returns components/<name>
    #     for a name that was never scoped, and "no manifest and no sources"
    #     used to report `done` — the most reassuring possible answer for an
    #     area that is not there (audit F3). An error, never a gate: `next`
    #     exits nonzero so the driver stops instead of resting.
    if not os.path.isdir(folder):
        #     M73: the error states BOTH readings it can distinguish. A folder
        #     absent from disk but PRESENT in the committed tree is a typo (or
        #     a deletion) — today's message. A folder the committed tree has
        #     never carried is more likely a never-scaffolded area, and saying
        #     only "check the --area name" is the wrong explanation offered
        #     alone (audit 6.1: it invites a silent mkdir). Both keep the
        #     substring "does not exist"; both stay `error` and exit nonzero —
        #     the folder is still not there and it is still the human's call.
        seen = _committed_content(folder)
        if seen is False:
            return result(
                "error",
                "area folder does not exist: %s — no committed content under "
                "this path — if this is a new area, create the folder and "
                "re-run (otherwise check the --area name; a bare name "
                "resolves under components/)" % folder,
                missing_folder=folder,
                committed_content=False,
            )
        extra = {} if seen is None else {"committed_content": True}
        return result(
            "error",
            "area folder does not exist: %s — check the --area name (a bare "
            "name resolves under components/)" % folder,
            missing_folder=folder,
            **extra,
        )

    st = AreaState(folder)
    # A pure read, like the profile: `hold:` is a file in the tree, so the
    # advisor stays a pure function of folder state. Read BEFORE the ladder so a
    # typo'd action name fails loud on every call, not only on the lap that would
    # have returned the held action.
    held["holds"] = _holds(folder)

    # 1 — pending proposal outranks everything (never re-scope an edited proposal)
    if _dir_has_files(st.proposed_dir):
        pending = {}
        if _uncommitted_proposals(folder, st.proposed_dir):
            pending["uncommitted_proposals"] = True
            pending["checkpoint_first"] = (
                "`.proposed/` holds uncommitted work — checkpoint BEFORE the "
                "human gate. `--confirm` consumes the whole proposal set "
                "(the taxonomist's staged _taxonomy/ nodes included), so "
                "without a commit there is nothing to diff and nothing to "
                "revert to.")
        # M75 Part C3/D: the gate OFFERS the ask-first loop as a first-class
        # second answer. `fill now` is today's behavior, untouched and still
        # the default shape; `ask first` hands the human the EXACT hold edit
        # and stops. Nothing here writes `consult.yaml` — holds are
        # human-owned config with no programmatic writer, and that doctrine is
        # the reason the answer carries an instruction rather than a command.
        # The counts, where a register exists, size the choice.
        counts = _ask_counts(folder)
        if counts is not None:
            pending["asks"] = counts
        return result(
            "confirm",
            "_reference/.proposed/ exists — human must review/edit, then confirm",
            gate=True,
            proposed_dir=os.path.relpath(st.proposed_dir, folder),
            answers=[
                {"name": "fill now",
                 "cost": "1 drafter dispatch per unfilled procedure",
                 "note": "confirm, then let the ladder dispatch the fill wave "
                         "against the evidence in hand — the default shape"},
                {"name": "ask first",
                 "cost": "free (the information-request render is python)",
                 "human_action": "add `fill` to `hold:` in "
                                 "%s/_client/consult.yaml, then confirm: the "
                                 "fill wave stops at a gate while the curated "
                                 "asks go out, and removing the hold is your "
                                 "\"I have what I need — draft\""
                                 % os.path.basename(os.path.abspath(folder)),
                 "note": "each round: render information-request -> client "
                         "material arrives -> route -> taxonomist curation "
                         "-> updated register -> re-render. The fill fan-out "
                         "then runs ONCE against full evidence"},
            ],
            **pending,
        )

    # 1.5 — returned review-kit files must be ingested before anything else:
    #       deterministic apply/ingest first, so drafters only see what
    #       actually needs judgment (M9/M10).
    returned = st.returned_files()
    if returned:
        return result(
            "ingest_returns",
            "_review/returned/ holds un-ingested review returns — run the "
            "deterministic ingest scripts (screens, gaps, apply, extract)",
            files=[os.path.relpath(p, folder) for p in returned],
        )

    # 2 — review notes route straight to the drafter (skip taxonomy).
    #     M18/F1: only notes naming a LIVE manifest slug are applicable, and the
    #     whole guard steps aside when there is no manifest at all.
    notes, orphans = st.review_notes()
    unassigned = st.unassigned_notes()
    def rel(p):
        return os.path.relpath(p, folder)

    def orphan_triage(paths, why):
        """The gate for reviewer material no drafter can consume. Names the
        orphaned slug(s) and the two legitimate resolutions — restore the
        procedure, or archive the note."""
        slugs = sorted({st.note_slug(p) for p in paths})
        return result(
            "review_triage",
            "%d review note(s) name no live procedure slug (%s) — %s"
            % (len(paths), ", ".join(slugs), why),
            gate=True,
            orphan_notes=[rel(p) for p in paths],
            orphan_slugs=slugs,
            resolutions=[
                "restore the procedure: re-scope it (or git-restore the "
                "manifest entry + fragment), then `next` dispatches the drafter",
                "archive the note: move it to _review/processed/ (its procedure "
                "is gone, the note is history)",
            ],
        )

    merge_deferred_notes = None
    if st.has_manifest:
        if notes:
            details = {"notes": [rel(n) for n in notes]}
            if orphans:
                details["orphan_notes"] = [rel(n) for n in orphans]
            if unassigned:
                details["unassigned"] = rel(unassigned)
            # Guard-2 step-aside (M32): when UNASSESSED sources are also
            # waiting and every queued item's kind is merge-safe (allowlist
            # above), defer to guard 5 — taxonomy folds the sources into the
            # same notes files as `kind: source` rows, so ONE drafter batch
            # carries notes + sources together instead of two. Precedent:
            # guard 2 already steps aside for guard 3 when no manifest
            # exists. Self-extinguishing: taxonomy assesses the sources,
            # guard 5 stops matching, guard 2 fires next pass with the
            # merged notes files.
            unassessed_now, _ = (st.new_source_assessment()
                                 if _dir_has_files(st.sources_new)
                                 else ([], []))
            if unassessed_now:
                kinds = st.queued_note_kinds()
                if kinds and kinds <= MERGE_SAFE_NOTE_KINDS:
                    merge_deferred_notes = details["notes"]
                else:
                    # Structural (or unknown-kind) notes must land before
                    # tagging — two batches are genuinely required. Say so
                    # in the result so the driver can disclose the second
                    # spend BEFORE dispatching this one.
                    details["also_pending_sources"] = [
                        rel(u) if isinstance(u, str) else u
                        for u in unassessed_now]
                    details["second_batch_required"] = (
                        "queued notes include structural kinds (%s) that "
                        "must apply before sources are tagged — after this "
                        "batch, taxonomy + confirm + a SECOND drafter batch "
                        "will run for the new sources"
                        % ", ".join(sorted(kinds - MERGE_SAFE_NOTE_KINDS)))
                    return result(
                        "apply_review",
                        "review notes present — dispatch consult-drafter "
                        "(update) per slug; NOTE: unassessed sources also "
                        "wait, a second batch follows (see "
                        "second_batch_required)",
                        **details,
                    )
            if merge_deferred_notes is None:
                return result(
                    "apply_review",
                    "review notes present — dispatch consult-drafter (update) per slug",
                    **details,
                )
        if orphans:
            return orphan_triage(
                orphans,
                "the drafter has no procedure to update and notes archive only "
                "on a successful dispatch, so no stage can clear them")
        if unassigned:
            # Only unattributed items remain — a human must triage them (move each
            # item into the right {slug}.notes.yaml, or archive the file).
            return result(
                "review_triage",
                "_review/_unassigned.notes.yaml holds items review_extract could "
                "not attribute to a procedure — triage by hand",
                gate=True,
                unassigned=rel(unassigned),
            )

    # 3 — initial scope: no manifest yet, raw sources waiting.
    #     Guard 2 does NOT outrank this: nothing can be applied to an unscoped
    #     area, so one stray notes file must not divert a brand-new area from
    #     being scoped at all (audit F1, the worst instance).
    if not st.has_manifest and _dir_has_files(st.sources_new):
        # M68 — the ladder routes BEFORE it scopes, in CENTRAL MODE ONLY.
        # Centrally, sources enter through `route`/`adopt`; a file sitting in
        # `<root>/_sources/new/` with no ledger entry has no SRC id, so a
        # scoping dispatch can only come back proposing `sources: []` and a
        # second full dispatch is needed purely to stamp ids. Spending an
        # agent to discover that routing was not done is the ladder's mistake.
        # v1 doctrine is deliberately untouched: there, an unregistered source
        # IS genuine taxonomy work (registration happens via proposals at the
        # confirm gate), which is why this keys off the central seam.
        unrouted = _unrouted_sources(st.central_root) if st.central_root else []
        if unrouted:
            areas = _engagement_areas(st.central_root)
            verb = ('python3 "${CLAUDE_PLUGIN_ROOT}/scripts/engagement.py" '
                    'route')
            cmd = verb + " <root>/_sources/new/<file> --to <area>"
            if len(areas) == 1:
                # A single-area engagement makes the target trivial — and only
                # then. Naming it is the whole reason this is not a gate.
                only = areas[0]
                return result(
                    "route",
                    "%d staged source(s) in %s/_sources/new/ carry no ledger "
                    "entry — route them before any scoping dispatch, or the "
                    "taxonomist runs against an empty ledger"
                    % (len(unrouted), st.central_root),
                    unrouted=unrouted,
                    target_area=only,
                    commands=["%s %s --to %s"
                              % (verb, os.path.join(st.central_root, u), only)
                              for u in unrouted],
                    then="re-run `next --area %s`; the ladder returns "
                         "`taxonomy` once every staged file is routed" % only,
                )
            return result(
                "route",
                "%d staged source(s) in %s/_sources/new/ carry no ledger "
                "entry, and this engagement has %d areas — which area each "
                "source informs is a classification decision, never a default"
                % (len(unrouted), st.central_root, len(areas)),
                gate=True,
                unrouted=unrouted,
                areas=areas,
                command_shape=cmd,
                human_action="classify each file above and route it: "
                             + cmd + " (repeat `--to a,b` for a source two "
                             "areas both owe a read on), then re-run `next`",
            )
        return taxonomy_result("no manifest and _sources/new/ non-empty",
                               "initial")

    if not st.has_manifest:
        if orphans:  # with no manifest EVERY note is orphaned, by construction
            return orphan_triage(
                orphans,
                "the area has no manifest and nothing left to scope, so no "
                "stage can consume them")
        if unassigned:
            return result(
                "review_triage",
                "_review/_unassigned.notes.yaml holds items in an unscoped area "
                "— triage by hand (there is no procedure to attribute them to)",
                gate=True,
                unassigned=rel(unassigned),
            )
        return result("done", "no manifest and no sources to scope")

    # 4 — fill: skeletons still stamped `unfilled` (precedes incremental taxonomy
    #     so a freshly-scaffolded area fills rather than re-scoping)
    unfilled = st.unfilled_slugs()
    if unfilled:
        # M11 waves: dispatch only the slugs whose upstream hints are already
        # filled; the rest are deferred to the next pass. Wave progress needs
        # no state file — it IS the set of remaining `unfilled` sentinels, so
        # the advisor stays a pure function of folder state. A cycle (empty
        # wave while work remains) degrades to dispatching everything.
        pending = set(unfilled)
        # M74 Part B: confidence gates COST, never SCOPE. A `low`-confidence
        # node keeps its component, its skeleton and its place in the count
        # above — it just leaves the DISPATCHABLE wave and is named in
        # `details.thin` with its value, so the orchestrator can put the
        # choice to the human. Only `low` waits (one word, one place, so a
        # later ruling can move the boundary); anything else — `medium`,
        # `high`, an unrecognised value, or no key at all — dispatches, which
        # is the fail-safe direction. `fill` stays a NON-gate holdable: the
        # HOLDABLE ∩ GATE disjointness doctrine is untouched, the human's
        # brake is the M17 hold and the human's go is dispatching the list.
        # M75 join, per the M74 reconciliation: an answered-and-unsettled ask
        # touching a node IS new evidence for it, so the node leaves the thin
        # partition and rides this wave. Empty set without a register, which
        # is what keeps every pre-M75 area's partition byte-identical.
        released = _asks_release(folder)
        thin = {s: st.confidence[s] for s in unfilled
                if st.confidence.get(s) == "low" and s not in released}
        dispatchable = [s for s in unfilled if s not in thin]
        # M74 Part D ruling: a thin-and-excluded upstream is treated as
        # ABSENT for wave release. Deferring on it would strand its whole
        # downstream behind a node that is, by design, waiting indefinitely;
        # the drafter simply gets no `upstream_files` entry for it and its
        # seam read degrades to the node scope prose. Blockers are therefore
        # the unfilled nodes that are still coming: `pending` minus `thin`.
        blocking = pending - set(thin)
        wave = [s for s in dispatchable
                if not any(u in blocking for u in st.upstream.get(s, []))]
        deferred = [s for s in dispatchable if s not in wave]
        thin_tail = ("; %d thin node(s) wait on evidence (details.thin)"
                     % len(thin)) if thin else ""
        if not wave and not dispatchable:
            # Only thin nodes remain. An empty work order plus the choice —
            # the orchestrator relays it and stops for the human exactly as
            # it does for any empty wave. No gate, no doctrine change.
            reason = ("%d thin node(s) remain: dispatch them [details.thin], "
                      "or hold `fill` and chase the asks" % len(thin))
        elif not wave:
            wave, deferred = dispatchable, []
            reason = ("%d procedure(s) unfilled; upstream hints form a cycle "
                      "— dispatching all at once%s" % (len(unfilled), thin_tail))
        elif deferred:
            reason = ("%d procedure(s) unfilled; wave of %d ready "
                      "(upstream filled), %d deferred to later waves%s"
                      % (len(unfilled), len(wave), len(deferred), thin_tail))
        else:
            reason = ("%d procedure(s) still carry the unfilled sentinel%s"
                      % (len(unfilled), thin_tail))
        details = {"unfilled": wave}
        if deferred:
            details["deferred"] = deferred
        if thin:
            details["thin"] = thin
        paths = dict(st.procedures)
        upstream_files = {}
        for s in wave:
            ups = [os.path.relpath(paths[u], folder)
                   for u in st.upstream.get(s, [])
                   if u in paths and u not in pending
                   and os.path.isfile(paths[u])]
            if ups:
                upstream_files[s] = ups
        if upstream_files:
            details["upstream_files"] = upstream_files
        return result("fill", reason, **details)

    # 4.5 — reprofile (M14): the profile requires section(s) a fragment does not
    #       have. Same family as `fill` — both are "fragments aren't in their
    #       target shape yet" — so it sits immediately below it, and above
    #       `aggregate`, because building derived views from a shape that is
    #       about to change wastes the pass.
    #
    #       A COST GATE, so human_gate is true: the handler reports the dispatch
    #       COUNT first ("12 drafter dispatches to add F. Key Controls —
    #       proceed?") and only dispatches on the go-ahead. Partial acceptance
    #       is fine: the guard is per-procedure, so an area can sit half-migrated
    #       indefinitely without wedging the loop.
    #
    #       Only the EXPENSIVE direction fires. Removing a section from the
    #       profile needs no action at all — render omits it and the fragments
    #       keep their text — and `body_omit` never fires here at all, because
    #       its sections' headings are present by construction.
    #
    #       Termination: the drafter contract has it write the heading even when
    #       the answer is "no controls identified in the current state", so the
    #       heading appears, the guard clears, and it cannot re-fire forever.
    drift = st.profile_drift()
    if drift:
        wanted = sorted({s for secs in drift.values() for s in secs})
        return result(
            "reprofile",
            "the document profile requires section(s) %s that %d fragment(s) do "
            "not have — %d drafter dispatch(es) to add them"
            % (", ".join(wanted), len(drift), len(drift)),
            gate=True,
            missing={slug: list(secs) for slug, secs in sorted(drift.items())},
            dispatches=len(drift),
            sections=wanted,
        )

    # 5 — incremental scope: new sources arrived after scaffolding.
    #     M6/F7: only sources the taxonomy agent has NOT yet assessed are work
    #     for it. `sources.yaml` is the discriminator (a pure read): a file in
    #     new/ that is unregistered, or registered at a different hash, is
    #     unassessed. A source registered at its current hash has already been
    #     read and proposed against — and by the time this guard is reached,
    #     guard 2 has ruled out any pending note (or deliberately stepped
    #     aside for this guard — the M32 merge path) and guard 4 any
    #     `unfilled` skeleton, so NOTHING can consume it: re-dispatching
    #     taxonomy proposes nothing new and re-spends a dispatch per lap.
    #     That is the gate below.
    # M25: route sidecars (`*.route.md`) are metadata, not sources — a folder
    # holding only them has nothing to assess and must not gate.
    unassessed, assessed = (st.new_source_assessment()
                            if _dir_has_files(st.sources_new) else ([], []))
    if unassessed or assessed:
        if unassessed:
            extra = {}
            reason = ("manifest exists and _sources/new/ holds %d unassessed "
                      "source file(s) (no unfilled)" % len(unassessed))
            if merge_deferred_notes:
                extra["merged_with_notes"] = merge_deferred_notes
                reason += ("; queued review notes DEFERRED to merge with "
                           "these sources (M32) — after taxonomy + confirm, "
                           "ONE apply_review batch carries both")
            return taxonomy_result(reason, "incremental",
                                   unassessed=unassessed, **extra)
        # M34 shape bridge: v1 assessed entries carry FLAT area-local
        # `touches`/`consumed`; central mode returns RAW ledger entries whose
        # touches/consumed are NAMESPACED MAPS ({area: [slugs]}). Flatten to this
        # area's slice so the message material below (and any consumer of
        # `stranded_sources`) sees one shape. v1 entries pass through untouched.
        area_name = os.path.basename(os.path.abspath(folder))
        stranded = sorted((_area_local_entry(e, area_name) for e in assessed),
                          key=lambda e: e["id"])
        ids = ", ".join(e["id"] for e in stranded)
        if st.central_root:
            remediation = (
                "per SRC- id: (a) re-issue its notes — re-run the taxonomy/"
                "confirm pass, whose promote step writes one `kind: source` "
                "note per drafted procedure it touches; (b) correct its "
                "`touches` for this area in the ENGAGEMENT LEDGER "
                "(_sources/sources.yaml at %s) so it names the procedures it "
                "really informs — edit it through `scripts/ledger.py` rather "
                "than by hand (the area has no _reference/sources.yaml in "
                "central mode); or (c) retire it by crediting the reads it is "
                "owed — `scripts/sources.py mark-processed %s` retires it from "
                "archived evidence, and a source fully consumed across EVERY "
                "area it touches moves to _sources/processed/ automatically."
                % (st.central_root, folder))
        else:
            remediation = (
                "per SRC- id: (a) re-issue its notes — re-run the taxonomy/confirm "
                "pass, whose promote step writes one `kind: source` note per drafted "
                "procedure it touches; (b) edit its `touches` in "
                "_reference/sources.yaml to name the procedures it really informs "
                "(the sanctioned veto, and the fix when `touches` is empty or "
                "typo'd); or (c) retire it by hand — move the file to "
                "_sources/processed/ and set `state: processed`. If its notes were "
                "already applied and archived, `scripts/sources.py mark-processed "
                "%s` retires it from that archived evidence." % folder)
        return unresolvable(
            "_sources/new/ holds %d already-assessed source(s) (%s) that nothing "
            "can consume: every procedure they touch is drafted, and no "
            "`kind: source` note is pending for them"
            % (len(stranded), ids),
            "`taxonomy` (incremental) would re-read sources already registered "
            "at these exact bytes and propose nothing new (audit F7: one wasted "
            "dispatch per lap, forever); `fill` dispatches on the `unfilled` "
            "sentinel, which a drafted procedure does not carry, and "
            "`apply_review` needs a note on the bus — the source notes that "
            "would have carried these sources to their drafters are not on disk "
            "(deleted, or never written because `touches` names nothing drafted)",
            remediation,
            stranded_sources=stranded,
            stranded_ids=[e["id"] for e in stranded],
        )

    # ---- steady-state derived pipeline (needs real procedures) ----
    if not st.procedures:
        return result("done", "no procedures in manifest")

    # 5b — a manifest slug whose fragment file is absent (audit F4). Both
    #      unfilled_slugs() and proc_hashes() skip it, so guard 6 used to fire
    #      forever with the wrong cause ("content changed"), while aggregate.py
    #      exited 1 on the real one. No advisor stage writes a fragment from
    #      nothing — scaffold is reachable only through the confirm flow — so
    #      this is a gate, named precisely.
    missing = st.missing_procedure_files()
    if missing:
        return unresolvable(
            "manifest procedure(s) %s declare fragment file(s) %s that are not "
            "on disk" % (", ".join(repr(s) for s, _f in missing),
                         ", ".join(f for _s, f in missing)),
            "no stage in the ladder writes a fragment from nothing: `fill` "
            "dispatches on the `unfilled` sentinel inside an existing file, and "
            "`aggregate` exits 1 without writing its signal, so the ladder would "
            "otherwise report `aggregate` forever",
            "restore the fragment (git restore / move it back), or re-run "
            "scripts/scaffold.py to recreate the skeleton so `fill` can redraft "
            "it, or drop the component from manifest.json",
            missing_procedures=[{"slug": s, "file": f} for s, f in missing],
        )

    cur_proc = st.proc_hashes()
    cur_reg = st.registry_hash()

    # 6 — aggregate: procedures or registry changed since the last aggregate.
    agg = _load_json(os.path.join(folder, ".aggregate.json")) or {}
    agg_stale = (agg.get("proc_hashes") != cur_proc
                 or agg.get("registry_hash") != cur_reg)
    if agg_stale:
        return result("aggregate",
                      "procedure/registry content changed since last aggregate")

    # 7 — registry top-up: aggregate flagged unmatched consult-meta slugs
    warnings = agg.get("warnings") or []
    if warnings:
        return result("registry_topup",
                      "aggregate emitted %d unmatched-mention warning(s)" % len(warnings),
                      gate=True,
                      warnings=warnings)

    # The guard-9 inputs, needed by guard 8's partition as well: whether the
    # producer of the agent-owned views has work queued decides whether the
    # verifier or the producer goes first.
    pending, stale_kinds = _synthesis_signal(folder, st)

    # 8 — reconcile: derived views not verified against current basis this pass
    basis = st.basis_hash()
    rec = _load_json(os.path.join(folder, ".reconcile.json")) or {}
    if rec.get("basis") != basis or not rec.get("clean"):
        # M18/F8 — the verifier must not precede its producer. Only failures
        # recorded at the CURRENT basis are trusted: with a stale basis the area
        # has moved and re-running reconcile really can change the answer.
        recorded = None
        if rec.get("basis") == basis and not rec.get("clean"):
            recorded = rec.get("failing_files")  # None => older signal, not recorded
        if recorded:
            frags = [f for f in recorded if st.owner(f) == "procedure"]
            agent = [f for f in recorded if st.owner(f) == "agent-derived"]
            other = [f for f in recorded if st.owner(f) not in
                     ("procedure", "agent-derived")]
            if frags:
                # Drafter-owned prose. reconcile verifies, it cannot regenerate;
                # no notes exist for these slugs and nothing writes them (M6).
                return unresolvable(
                    "reconcile failed at the current basis on drafter-owned "
                    "procedure fragment(s): %s" % ", ".join(sorted(frags)),
                    "reconcile has already verified this exact basis and "
                    "failed, so re-running it reproduces the same errors; no "
                    "stage regenerates a procedure fragment (`fill` needs the "
                    "`unfilled` sentinel, `apply_review` needs a note, and "
                    "nothing writes notes for these slugs)",
                    "fix the named fragment(s) by hand — or re-scope so the "
                    "referenced procedures exist again — then re-run "
                    "scripts/reconcile.py; run it directly for the full error "
                    "list (this gate names the files, not every check)",
                    failing_files=sorted(recorded),
                    dangling_refs=st.dangling_xrefs(sorted(recorded)),
                )
            if agent and not other:
                if pending or stale_kinds:
                    # The producer is ready and was unreachable: run it first,
                    # then reconcile re-verifies at the new basis.
                    return result(
                        "synthesize",
                        "reconcile's failures are confined to agent-owned "
                        "derived views the change signal already marks stale — "
                        "regenerate them, then reconcile re-verifies",
                        pending=pending, stale_kinds=stale_kinds,
                        failing_files=sorted(agent))
                return unresolvable(
                    "reconcile failed at the current basis on agent-owned "
                    "derived view(s) %s, and the change signal marks nothing "
                    "stale" % ", ".join(sorted(agent)),
                    "`synthesize` would dispatch with an empty work order "
                    "(scope_delta reports no changed procedures for either "
                    "kind and no file carries a pending placeholder), so it "
                    "cannot rewrite these views",
                    "fix the view by hand, or force a re-derive by removing the "
                    "kind's baseline from .hashes.json, then re-run "
                    "scripts/reconcile.py",
                    failing_files=sorted(recorded),
                    dangling_refs=st.dangling_xrefs(sorted(recorded)),
                )
        return result("reconcile",
                      "derived views changed or not yet reconciled clean this pass")

    # Read once, for guard 8.5 (is a spend outstanding?) and guards 10/11.
    ren = _load_json(os.path.join(folder, ".render.json")) or {}

    # 8.5 — draft_ready (M17): the last FREE stop. The area is fully drafted and
    #       verified (everything above is either free Python or already spent),
    #       and the two moves below it are the expensive ones: `synthesize`
    #       dispatches two judgment agents, `render` starts a human review cycle.
    #       So the gate asks the one question worth asking here — "am I happy
    #       with the verbs and the nouns?" — before either is paid for.
    #
    #       It fires ONLY when one of those moves is actually outstanding. A gate
    #       is a stop before a cost; with nothing left to spend there is nothing
    #       to stop, and firing anyway would preempt the `review` gate (asking
    #       the human to accept a draft whose document they have already read)
    #       and make `done` unreachable. Cheap to re-derive, so it is read here
    #       rather than remembered.
    #
    #       Keyed to draft_basis() — procedures + registry, NOT basis_hash — so
    #       one accept covers the whole pass: `synthesize` rewriting the derived
    #       views cannot re-open it, while any fragment or registry edit does.
    if pending or stale_kinds or ren.get("basis") != basis:
        draft_basis = st.draft_basis(cur_proc, cur_reg)
        dr = _load_json(os.path.join(folder, ".draft_ready.json")) or {}
        if not (dr.get("accepted") is True
                and dr.get("draft_basis") == draft_basis):
            slugs = ",".join(sorted(st.procedure_slugs))
            cons = _load_json(os.path.join(folder, ".consolidate.json")) or {}
            # M73: check-23's blank register cells, counted at the last free
            # stop. ADDITIVE — `answers` and `would_spend` are unchanged.
            reg_warn = _register_warnings(folder, st.manifest)
            extra = {} if reg_warn is None else {"register_warnings": reg_warn}
            # M75's advisor signal: accepting this draft with open asks ships
            # KNOWN holes, and an answered-unsettled ask is a settle dispatch
            # nobody has run. Additive keys, absent without a register.
            ask_counts = _ask_counts(folder)
            if ask_counts is not None:
                extra["asks"] = ask_counts
            # M76: the open-flag count, beside the register warnings — agent
            # judgment filed against this area that nothing has closed yet.
            # Additive, absent without a queue, and advisory: it never blocks.
            open_flags = _open_flags(folder)
            if open_flags is not None:
                extra["open_flags"] = open_flags
            # M71: the gate reads the deliverable it is gating FOR. The note
            # names the spend the gate is actually holding back (already
            # computed below as `would_spend`), and a render-bound gate carries
            # the render TARGET plus, when that target would report "not yet",
            # the one sentence naming the path to it. Additive: `answers`,
            # `would_spend` and the accept COMMAND are unchanged.
            spend = "synthesize" if (pending or stale_kinds) else "render"
            if spend == "render":
                dname = area_definition(folder)
                extra["definition"] = dname
                report = _deliverable_report(folder, dname)
                if report is not None and report["gaps"]:
                    extra["deliverable_not_yet"] = {
                        "gaps": report["gaps"], "note": report["note"]}
            return result(
                "draft_ready",
                "drafted and verified, and this draft has not been accepted — "
                "everything past here spends agents (synthesize) or people "
                "(render -> kits -> review)",
                gate=True,
                draft_basis=draft_basis,
                question="am I happy with the verbs and the nouns before "
                         "anything else is paid for?",
                answers=[
                    {"name": "read",
                     "command": "scripts/render.py %s -o <out.docx> --slugs %s"
                                % (folder, slugs),
                     "cost": "free",
                     "note": "procedures only (no front/back matter); never "
                             "writes .render.json, so it does not advance the "
                             "state machine"},
                    {"name": "consolidate",
                     "command": "scripts/consolidate.py plan %s" % folder,
                     "cost": "1 agent per bucket group (~5 fragments each) "
                             "+ 1 cross-bucket (none when one group covers "
                             "the area)",
                     "consolidated_at_basis": cons.get("draft_basis"),
                     "note": "M12 cross-procedure consistency pass — emits "
                             "notes only, fragments untouched. "
                             "consolidated_at_basis equal to draft_basis "
                             "means this exact draft already had a pass; "
                             "null or stale means it has not "
                             "(consolidate.py mark records it)"},
                    {"name": "accept",
                     "command": "scripts/orchestrate.py accept-draft --area %s"
                                % folder,
                     "cost": "free",
                     "note": "records this draft_basis in .draft_ready.json and "
                             "lets the ladder through to %s" % spend},
                ],
                would_spend=spend,
                **extra,
            )

    # 9 — synthesize: judgment views stale vs the changed procedures.
    # The "what changed per agent kind" signal is owned by scope_delta (its
    # per-kind .hashes.json baseline) — reuse it rather than re-reading a flat
    # basis, so there is one change-signal authority and no filename-shape clash.
    if pending or stale_kinds:
        return result("synthesize",
                      "judgment views stale vs changed procedures",
                      pending=pending, stale_kinds=stale_kinds)

    # 10 — render: everything current + reconciled, no fresh docx.
    #      Keyed per DEFINITION as well as per basis (M36 WP-G2): a .docx of a
    #      different deliverable is not this area's document, however current its
    #      basis. One deliverable exists today and a pre-M36 signal reads as it,
    #      so this is behavior-identical for every v1 area.
    target = area_definition(folder)
    if (ren.get("basis") != basis or signal_definition(ren) != target):
        # M71 Part B: refuse FORWARD. A deliverable whose serviceability is
        # "not yet" would answer the render with a report, not a document —
        # so the report rides the action and the human decides before paying
        # for it. Same read as guard 8.5, and additive: a serviceable target
        # (every v1 area at this point) carries nothing new.
        extra = {}
        report = _deliverable_report(folder, target)
        if report is not None and report["gaps"]:
            extra = {"definition": target, "serviceability": "not yet",
                     "gaps": report["gaps"], "note": report["note"]}
        return result("render", "views current and reconciled; no fresh .docx",
                      **extra)

    # 11 — review: rendered, awaiting human sign-off (resting gate)
    if ren.get("awaiting_review"):
        return result("review",
                      "rendered; awaiting human review of the .docx",
                      gate=True,
                      docx=ren.get("docx"))

    # 12 — nothing outstanding
    return result("done", "all views current, reconciled, rendered and reviewed",
                  docx=ren.get("docx"))


# --------------------------------------------------------------------------- #
# Signal-file writers (called by the mutating stages, not by `decide`).
# Centralized here so the signal shapes + hash computation match exactly what
# the advisor reads. `decide`/`next` remain strictly read-only.
# --------------------------------------------------------------------------- #

def _write_json(path: str, obj) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, sort_keys=True)
        fh.write("\n")


def emit_aggregate(folder: str, warnings) -> None:
    """Written by aggregate.py after a successful rebuild → guards 6/7."""
    st = AreaState(folder)
    _write_json(os.path.join(folder, ".aggregate.json"), {
        "proc_hashes": st.proc_hashes(),
        "registry_hash": st.registry_hash(),
        "warnings": list(warnings or []),
    })


def emit_reconcile(folder: str, clean: bool, failing_files=None) -> None:
    """Written by reconcile.py after an area-wide check → guard 8.

    `failing_files` (M18/F8) records WHICH area-relative files the run's errors
    named, so guard 8 can tell a failure a producer would fix (agent-owned
    derived views the change signal marks stale → `synthesize` first) from one no
    stage can fix (a drafter-owned fragment → `unresolvable`). Ordering, not
    logic, was the F8 deadlock; this is the only new input it needs.

    Backward compatible in both directions: passing None (the pre-M18 signature,
    or a caller that does not track it) omits the key entirely, and guard 8 then
    behaves exactly as before — it returns `reconcile`. Reading an older signal
    that lacks the key does the same."""
    st = AreaState(folder)
    sig = {
        "basis": st.basis_hash(),
        "clean": bool(clean),
    }
    if failing_files is not None:
        sig["failing_files"] = sorted({str(f) for f in failing_files})
    _write_json(os.path.join(folder, ".reconcile.json"), sig)


#: M36 WP-G2 — the deliverable a render signal is ABOUT. v1 has exactly one
#: deliverable, so this is the name every v1 render signal carries and the
#: value a pre-M36 signal (which carries no `definition` key at all) reads as.
DEFAULT_DEFINITION = "desktop-procedure"


def signal_definition(sig) -> str:
    """Which deliverable a render signal describes — TOLERANT READ: a signal
    written before M36 has no `definition` key, and v1's only deliverable is
    the default, so an old file reads exactly as a new one written by the same
    pipeline. Never raises; a junk value is returned as-is so the comparison in
    guard 10 fails loudly-by-mismatch rather than being silently coerced."""
    name = (sig or {}).get("definition")
    if not isinstance(name, str) or not name.strip():
        return DEFAULT_DEFINITION
    return name.strip()


#: M66 A2/5 — what a render signal says when NOTHING declares this area's
#: deliverable. An explicit token, not a silent default: a v2 area that has
#: not been told what to produce must not report the v1 document.
UNSET_DEFINITION = "unset"


def area_definition(folder: str) -> str:
    """The deliverable name this area builds — `UNSET_DEFINITION` when nothing
    names one.

    Read-only and best-effort: an unresolvable definition (stripped install,
    unreadable profile) reads as the area's declared name, which is what keeps
    `decide` from ever failing on a config read. M66 A2/5 moved the AUTHORITY
    from "the one v1 document" to the objective — see
    `definitions.area_deliverable`; a v1 area still reads `desktop-procedure`,
    and the fallback below is the same v1 answer for a stripped install where
    the capture type itself cannot be read."""
    try:
        import definitions
        name = definitions.area_deliverable(folder)
        if name is None:
            return UNSET_DEFINITION
        return definitions.resolve_definition(folder, name).name
    except Exception:
        return DEFAULT_DEFINITION


def area_definition_note(folder: str) -> str | None:
    """The sentence an `unset` signal carries — or None when one is declared."""
    try:
        import definitions
        return definitions.area_deliverable_note(folder)
    except Exception:
        return None


def emit_render(folder: str, docx: str, awaiting_review: bool = True,
                definition: str | None = None) -> None:
    """Written by the renderer after producing the .docx → guards 10/11.

    M36 WP-G2: the signal is KEYED PER DEFINITION — it records WHICH deliverable
    was rendered, so a .docx of one deliverable can never satisfy guard 10 for
    another. Additive in both directions: the key is omitted from nothing that
    reads it (see `signal_definition`'s tolerant read) and `definition=None`
    records the area's own deliverable, which for every v1 area is
    `desktop-procedure` — the one deliverable that exists today, so behavior is
    unchanged."""
    st = AreaState(folder)
    name = definition or area_definition(folder)
    sig = {
        "basis": st.basis_hash(),
        "docx": str(docx),
        "awaiting_review": bool(awaiting_review),
        "definition": name,
    }
    # M66 A2/5: `unset` is an honest state, so it says WHY on the same read —
    # additive, and written only in that state (every declared render's signal
    # is byte-identical to what it was).
    if name == UNSET_DEFINITION:
        note = area_definition_note(folder)
        if note:
            sig["definition_note"] = note
    _write_json(os.path.join(folder, ".render.json"), sig)


# --------------------------------------------------------------------------- #
# Git checkpoint (called by the driver after each successful mutating stage).
# Folder state is the only state, so losing the folder loses the engagement —
# the checkpoint makes every advisor-step durable without relying on an agent
# remembering to commit. Scoped strictly to the area folder; never pushes.
# --------------------------------------------------------------------------- #

def accept_review(folder: str) -> dict:
    """Clear `awaiting_review` in .render.json — the user's explicit acceptance
    of the rendered document. This is the ONLY writer that flips the flag; the
    renderer always sets it true. Without it the advisor returns the `review`
    gate forever. No-op (with a reason) when there is no render signal."""
    path = os.path.join(folder, ".render.json")
    ren = _load_json(path)
    if not ren:
        return {"accepted": False, "reason": "no .render.json — nothing rendered"}
    ren["awaiting_review"] = False
    _write_json(path, ren)
    return {"accepted": True, "docx": ren.get("docx")}


def accept_draft(folder: str) -> dict:
    """Record the human's acceptance of the drafted verbs+nouns — the ONLY
    writer of `.draft_ready.json`, and the only thing that opens guard 8.5.

    Same shape as accept_review(): a no-op WITH A REASON when there is nothing
    to accept. "Nothing to accept" is asked of `decide()` itself rather than
    re-derived here, so the flag can never be written for a state the gate does
    not describe (an area with unfilled work, an unreconciled area, an area
    already accepted at this draft basis). decide() is read-only, so asking is
    free and cannot mutate anything.

    The recorded key is the draft basis — procedures + registry only — so one
    accept covers a whole pass (M17 "Clearing it")."""
    d = decide(folder)
    if d.get("action") != "draft_ready":
        return {"accepted": False,
                "reason": "area is not at the draft-ready gate — `next` says "
                          "%s: %s" % (d.get("action"), d.get("reason")),
                "next_action": d.get("action")}
    draft_basis = (d.get("details") or {}).get("draft_basis")
    _write_json(os.path.join(folder, ".draft_ready.json"),
                {"draft_basis": draft_basis, "accepted": True})
    return {"accepted": True, "draft_basis": draft_basis,
            "next_action": decide(folder).get("action")}


# Seeded into an area on first checkpoint if no .gitignore exists: keeps the
# advisor's signal files and regenerable kit output out of the host repo, per
# the documented state-file contract. Everything else (fragments, registry,
# sources, review returns, maps) IS the engagement and gets committed.
AREA_GITIGNORE = """\
# consult advisor signal files (derived; regenerated by the stage scripts)
.aggregate.json
.consolidate.json
.draft_ready.json
.hashes.json
.reconcile.json
.render.json
*.extract.json
# per-owner review kits (derived; regenerate with kits.py)
_review/kits/
"""

# M68: seeded into the ENGAGEMENT ROOT on the first central-mode checkpoint,
# for the same reason the area gets one — the ignore rules have to live in the
# host repo, and centrally the checkpoint now stages engagement-level folders
# that collect OS noise. Deliberately minimal: everything at the root that is
# not noise (`_sources/`, `components/_client/`) IS the engagement.
ENGAGEMENT_GITIGNORE = """\
# consult engagement root (M68): OS noise only — the engagement state under
# _sources/ and components/_client/ IS committed, on purpose.
.DS_Store
Thumbs.db
"""


def _checkpoint_pathspecs(folder: str, central_root: str | None) -> list[str]:
    """The pathspecs one checkpoint stages, diffs and commits — ALL THREE git
    calls take this same list (M68).

    Always the area itself (`.`). In central mode the stages also mutate state
    OUTSIDE the area — the engagement ledger and its `new/`→`processed/` moves
    (`<root>/_sources/`) and the shared client layer
    (`<root>/components/_client/`) — and, since M76, the engagement's
    JUDGMENT STATE: the registers (`<root>/_registers/` — findings.yaml,
    asks.yaml) and the session records (`<root>/_records/`). Those two were a
    live leak: a register written every pass and committed by no checkpoint
    ever. Same one-list-three-calls discipline; a checkpoint that stopped at
    the area left the run's most valuable state uncommitted. Still a pathspec
    commit:
    unrelated repo work is never swept in.

    Paths are relative to `folder`, because every call runs `git -C <folder>`.
    A pathspec that does not exist is dropped rather than passed: `git add`
    and `git commit` both refuse an unmatched pathspec outright, and the
    absence of `components/_client/` is ordinary.
    """
    specs = ["."]
    if not central_root:
        return specs
    for extra in (os.path.join(central_root, "_sources"),
                  os.path.join(central_root, "_registers"),
                  os.path.join(central_root, "_records"),
                  os.path.join(central_root, "components", "_client"),
                  os.path.join(central_root, ".gitignore")):
        if os.path.exists(extra):
            rel_spec = os.path.relpath(extra, folder)
            if rel_spec not in specs:
                specs.append(rel_spec)
    return specs


def checkpoint(folder: str, stage: str, dry_run: bool = False) -> dict:
    """Commit the area folder's current state as `consult(<area>): <stage>`.

    Deterministic and safe to over-call: a no-op (with a reason) when the area
    is not inside a git work tree or nothing under it changed. Stages only the
    checkpoint's pathspecs, and commits only those, so unrelated staged work
    elsewhere in the repo is never swept into the checkpoint.

    Ignore contract: the docs promise the signal files (.aggregate.json etc.)
    and regenerable kit output stay out of git, but those ignore rules must
    exist in the HOST repo — so if the area has no .gitignore yet, one is
    seeded here before staging (and, in central mode, one at the engagement
    root). `_sources/` IS committed on purpose: folder state is the only
    state, and a checkpoint that omits the sources can't restore the
    engagement. That is why the central-mode pathspec reaches OUTSIDE the area
    to `<root>/_sources/` and `<root>/components/_client/` (M68) — the area
    alone is not the engagement. Keep engagement areas in a private repo.

    `dry_run=True` is the DISCLOSURE seam (M73, audit 7.3): a strictly
    read-only preview that stages nothing, seeds no `.gitignore` and commits
    nothing — it returns the pathspecs this checkpoint would commit and the
    porcelain lines already dirty under them. The pathspecs are engine
    knowledge (M68 widened them past the area), so the caller cannot compute
    this list itself; the skill runs it before the FIRST checkpoint of a
    session and names the pre-existing dirt it is about to commit under this
    stage's message.
    """
    import subprocess

    def _git(*args):
        return subprocess.run(["git", "-C", folder, *args],
                              capture_output=True, text=True)

    probe = _git("rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        out = {"committed": False, "stage": stage,
               "reason": "area is not inside a git work tree"}
        if dry_run:
            out.update(dry_run=True, pathspecs=[], dirty=[])
        return out

    if dry_run:
        specs = _checkpoint_pathspecs(
            folder, _central_root(folder) if _central_root else None)
        status = _git("status", "--porcelain", "--", *specs)
        dirty = [ln for ln in status.stdout.splitlines() if ln.strip()]
        return {"committed": False, "stage": stage, "dry_run": True,
                "reason": "dry run — nothing staged, nothing committed",
                "pathspecs": specs, "dirty": dirty}

    gi = os.path.join(folder, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w", encoding="utf-8") as fh:
            fh.write(AREA_GITIGNORE)

    central = _central_root(folder) if _central_root else None
    if central:
        root_gi = os.path.join(central, ".gitignore")
        if not os.path.exists(root_gi):
            with open(root_gi, "w", encoding="utf-8") as fh:
                fh.write(ENGAGEMENT_GITIGNORE)

    specs = _checkpoint_pathspecs(folder, central)

    add = _git("add", "-A", "--", *specs)
    if add.returncode != 0:
        return {"committed": False, "stage": stage,
                "reason": "git add failed: " + add.stderr.strip()}

    if _git("diff", "--cached", "--quiet", "--", *specs).returncode == 0:
        return {"committed": False, "stage": stage,
                "reason": "nothing to commit"}

    area_name = os.path.basename(os.path.abspath(folder))
    commit = _git("commit", "-m", f"consult({area_name}): {stage}",
                  "--", *specs)
    if commit.returncode != 0:
        return {"committed": False, "stage": stage,
                "reason": "git commit failed: " + commit.stderr.strip()}
    sha = _git("rev-parse", "--short", "HEAD").stdout.strip()
    return {"committed": True, "stage": stage, "commit": sha}


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_next = sub.add_parser("next", help="print the single next action")
    p_next.add_argument("--area", required=True,
                        help="area folder path or bare area name under components/")
    p_next.add_argument("--json", action="store_true",
                        help="emit JSON (default; kept for explicitness)")
    p_ckpt = sub.add_parser(
        "checkpoint",
        help="commit the area folder's state after a successful stage")
    p_ckpt.add_argument("--area", required=True,
                        help="area folder path or bare area name under components/")
    p_ckpt.add_argument("--stage", required=True,
                        help="stage name just completed (goes in the commit message)")
    p_ckpt.add_argument("--dry-run", action="store_true",
                        help="read-only preview: print the pathspecs this "
                             "checkpoint would commit and what is already "
                             "dirty under them; stage and commit nothing "
                             "(M73 first-checkpoint disclosure)")
    p_acc = sub.add_parser(
        "accept",
        help="record the user's acceptance of the rendered docx "
             "(clears awaiting_review so the advisor can reach `done`)")
    p_acc.add_argument("--area", required=True,
                       help="area folder path or bare area name under components/")
    p_dra = sub.add_parser(
        "accept-draft",
        help="record the user's acceptance of the drafted procedures + registry "
             "(opens the draft-ready gate so the ladder can reach synthesize)")
    p_dra.add_argument("--area", required=True,
                       help="area folder path or bare area name under components/")
    args = parser.parse_args(argv)

    if args.cmd == "accept":
        print(json.dumps(accept_review(resolve_area(args.area)), indent=2))
        return 0

    if args.cmd == "accept-draft":
        print(json.dumps(accept_draft(resolve_area(args.area)), indent=2))
        return 0

    if args.cmd == "next":
        folder = resolve_area(args.area)
        decision = decide(folder)
        print(json.dumps(decision, indent=2, sort_keys=False))
        # M18/F3: the `error` result (a nonexistent area) exits nonzero so a
        # typo'd --area stops the driver instead of reading as progress. Every
        # real action — including the `unresolvable` gate, which is a resting
        # state, not a failure — exits 0.
        return 2 if decision.get("action") == "error" else 0
    if args.cmd == "checkpoint":
        folder = resolve_area(args.area)
        outcome = checkpoint(folder, args.stage, dry_run=args.dry_run)
        print(json.dumps(outcome, indent=2, sort_keys=False))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
