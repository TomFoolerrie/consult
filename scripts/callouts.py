"""callouts.py — the single source of the callout/ID grammar primitives.

Both `aggregate.py` (extracts callouts into rows) and `reconcile.py` (validates
IDs) import from here so the drift-critical pieces — the LABEL→prefix map, the
LABEL→home-section-slug map, the severity enum, the tolerant delimiter, and the
ID/gap-tag grammar — are defined
exactly once. Each engine keeps its own higher-level callout-*line* matcher
(aggregate's is extract-strict; reconcile's is loose enough to still flag a
malformed ID), but both build it from the shared `DELIM` and validate against the
shared map + `ID_STRICT_RE`.
"""

import re

# LABEL → strict ID prefix (README "Extraction / matching contract").
LABEL_TO_PREFIX = {
    "CONTROL": "CTRL",
    "VALIDATION REQUIRED": "GAP",
    "PAIN POINT": "PP",
    "IMPROVEMENT OPPORTUNITY": "IO",
    "SCREENSHOT PLACEHOLDER": "SC",
}
# Back-compat alias (reconcile historically used this name).
LABEL_PREFIX = LABEL_TO_PREFIX
PREFIXES = sorted(set(LABEL_TO_PREFIX.values()))

# M23 — LABEL → HOME SECTION SLUG. The contract "CONTROL callouts live in Key
# Controls, PAIN POINT / IMPROVEMENT OPPORTUNITY in Known Issues, VALIDATION
# REQUIRED and SCREENSHOT PLACEHOLDER inline at their step" used to be written
# as CONTROL→F and PP/IO→H — a letter, which is a render-time POSITION, standing
# in for the section's identity. Re-keyed to the `doc_model` registry slugs, so
# a later reshape moves the section without silently re-pointing this map.
LABEL_TO_HOME_SECTION = {
    "CONTROL": "controls",
    "PAIN POINT": "issues",
    "IMPROVEMENT OPPORTUNITY": "issues",
    "VALIDATION REQUIRED": "steps",
    "SCREENSHOT PLACEHOLDER": "steps",
}


def home_section(label: str) -> str | None:
    """The section slug a callout of this LABEL belongs in, or None."""
    return LABEL_TO_HOME_SECTION.get(re.sub(r"\s+", " ", label or "").strip().upper())


# PP/IO severity enum (validated as a WARNING, never fail-loud).
SEVERITY_ENUM = {"High", "Medium", "Low"}

# Tolerant delimiter between label and id: hyphen-minus, en-dash, em-dash.
DELIM = r"[-–—]"

# Strict, anchored ID grammar: <PREFIX>-<UPPER-ALNUM segment>(-<segment>)*.
ID_STRICT_RE = re.compile(
    r"^(" + "|".join(PREFIXES) + r")-([A-Z0-9]+(?:-[A-Z0-9]+)*)$"
)
# Any well-formed ID occurrence in prose (for reference tracking).
ID_INLINE_RE = re.compile(
    r"\b(" + "|".join(PREFIXES) + r")-([A-Z0-9]+(?:-[A-Z0-9]+)*)\b"
)

# Body gap reference `[[GAP-NN — reason]]` and the bare (id-less) form.
BODY_GAP_RE = re.compile(r"\[\[\s*GAP-([A-Z0-9]+(?:-[A-Z0-9]+)*)\s*" + DELIM)
BARE_GAP_RE = re.compile(r"\[\[\s*GAP(?!-[A-Z0-9])\s*(?:" + DELIM + r"|\]\])")

# Procedure cross-reference token: `[[slug]]` (resolves to number + title) or
# `[[#slug]]` (number only — for table refs where the title is its own column).
# M26: an optional `area/` prefix makes it a CROSS-AREA token `[[area/slug]]`
# (resolves to heading + area title, never a number). This regex is the ONE
# token grammar — every consumer (resolve, reconcile's dangling check,
# orchestrate, review_apply) matches through it or mirrors it exactly.
XREF_RE = re.compile(
    r"\[\[#?([a-z0-9][a-z0-9-]*(?:/[a-z0-9][a-z0-9-]*)?)\]\]")

# A fenced code block (``` or ~~~) — blanked so callouts inside code/examples
# and the consult-meta block are not parsed as real callouts.
FENCE_BLOCK_RE = re.compile(r"^(`{3,}|~{3,}).*?^\1\s*$", re.MULTILINE | re.DOTALL)


class FragmentError(Exception):
    """Raised on a fail-loud callout/ID grammar defect in one procedure."""


def blank_fences(text: str) -> str:
    """Replace fenced-block bodies with blank lines, preserving line count."""
    return FENCE_BLOCK_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


# reconcile historically called this `strip_fences`.
strip_fences = blank_fences


# --------------------------------------------------------------------------- #
# M16 move 3 — the two-view callout body (`note` inline, `detail` in the
# appendix). Both are ORDINARY callout sub-fields: the `> - **Field:** value`
# bullet grammar already parses them and a missing optional field already parses
# as blank, so nothing about the callout shape changes. What is new is that two
# field NAMES are load-bearing at render/aggregate time, so their spelling and
# the "which kinds may carry a detail" set live here — the one home the three
# engines (render blanks it, aggregate carries it, reconcile validates it) read
# from, exactly like the LABEL→prefix map above.
# --------------------------------------------------------------------------- #

#: The one-or-two-sentence view; renders IN the step / home section.
NOTE_FIELD = "Note"
#: The full account; renders ONLY in the callout's appendix register row.
DETAIL_FIELD = "Detail"

#: Kinds whose bodies run long, and which therefore have a reason to split.
#: CONTROL and SCREENSHOT PLACEHOLDER are already short and take `note` only —
#: a `detail:` on one of them is a WARNING (reconcile), never dropped content:
#: every register carries the detail if it is there.
DETAIL_KINDS = {"VALIDATION REQUIRED", "PAIN POINT", "IMPROVEMENT OPPORTUNITY"}

# A callout sub-field bullet, NAME only: `> - **<Field>:** …`. aggregate's
# SUBFIELD_RE is the extract-strict twin that also captures the value; render
# and reconcile only ever ask "which field does this line open?", so they ask
# here instead of re-deriving the bullet grammar.
CALLOUT_FIELD_RE = re.compile(r"^\s*>\s*-\s*\*\*\s*(?P<field>[^:*]+?)\s*:\s*\*\*")


def callout_field(line: str) -> str | None:
    """Return the sub-field name this line opens, or None if it opens none."""
    m = CALLOUT_FIELD_RE.match(line)
    return re.sub(r"\s+", " ", m.group("field")).strip() if m else None


def is_callout_field(line: str, name: str) -> bool:
    """True when `line` opens the named sub-field (case-insensitive)."""
    f = callout_field(line)
    return f is not None and f.lower() == name.lower()


# A callout DEFINITION line: `> **<LABEL> — <ID>:**` (loose id; validation is
# the parsers' job). Used by iter_defined_ids for display-numbering walks.
_DEF_LINE_RE = re.compile(
    r"^\s*>\s*\*\*\s*(?P<label>[A-Z][A-Z ]+?)\s*" + DELIM + r"\s*"
    r"(?P<id>[A-Z0-9][A-Z0-9-]*)\s*:\*\*"
)


def iter_defined_ids(text: str):
    """Yield (prefix, id) for each callout defined in a fragment, in order.

    Fence bodies are blanked first. Only lines whose label is in
    LABEL_TO_PREFIX and whose id carries the matching prefix are yielded —
    malformed definitions are the fail-loud parsers' concern, not ours.
    """
    for line in blank_fences(text).splitlines():
        m = _DEF_LINE_RE.match(line)
        if not m:
            continue
        label = re.sub(r"\s+", " ", m.group("label")).strip()
        prefix = LABEL_TO_PREFIX.get(label)
        cid = m.group("id").strip()
        if prefix and cid.startswith(prefix + "-"):
            yield prefix, cid


# --------------------------------------------------------------------------- #
# M24 — open gaps, read one way everywhere. The engagement gap register and
# M12's cross-brief gap register both ask "what is still unanswered in this
# fragment?", and a second parser is how the two would drift. A gap is open
# by virtue of being present: closing one removes it from the fragment.
# --------------------------------------------------------------------------- #

# A GAP definition line WITH its text: `> **VALIDATION REQUIRED — GAP-NN:** …`.
_GAP_CALLOUT_RE = re.compile(
    r"^\s*>\s*\*\*\s*VALIDATION REQUIRED\s*" + DELIM + r"\s*"
    r"(?P<id>GAP-[A-Z0-9]+(?:-[A-Z0-9]+)*)\s*:\*\*\s*(?P<text>.*?)\s*$"
)
# A body gap tag WITH its text: `[[GAP-NN — reason]]` (may span a hard wrap).
_GAP_TAG_RE = re.compile(
    r"\[\[\s*(?P<id>GAP-[A-Z0-9]+(?:-[A-Z0-9]+)*)\s*" + DELIM
    + r"\s*(?P<text>.*?)\s*\]\]",
    re.DOTALL,
)


def open_gaps(text: str) -> list[tuple[str, str]]:
    """Every open gap in a fragment as (local id, text), in document order:
    VALIDATION REQUIRED callout definitions first-class, plus `[[GAP-NN — …]]`
    body tags. Fence bodies are blanked; hard-wrapped tag text is rejoined.
    Ids are procedure-LOCAL (they renumber at render) — callers key on
    (procedure, id), never on the id alone."""
    blanked = blank_fences(text)
    found: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    lines = blanked.splitlines(keepends=True)
    pos = 0
    offsets = []
    for ln in lines:
        offsets.append(pos)
        pos += len(ln)
    for i, line in enumerate(lines):
        m = _GAP_CALLOUT_RE.match(line)
        if not m or m.group("id") in seen:
            continue
        seen.add(m.group("id"))
        # Callout text hard-wraps across continuation quote lines — join
        # them until a blank quote, a sub-field bullet, or a new callout.
        parts = [m.group("text")]
        for nxt in lines[i + 1:]:
            s = nxt.strip()
            if (not s.startswith(">") or s in (">",)
                    or CALLOUT_FIELD_RE.match(nxt)
                    or _DEF_LINE_RE.match(nxt)):
                break
            parts.append(s.lstrip(">").strip())
        found.append((offsets[i], m.group("id"),
                      re.sub(r"\s+", " ", " ".join(parts)).strip()))
    # Body tags often REFERENCE a gap the callout defines (same local id) —
    # one gap, not two, so the callout's fuller text wins and the tag counts
    # only when no callout carries its id.
    for m in _GAP_TAG_RE.finditer(blanked):
        if m.group("id") not in seen:
            seen.add(m.group("id"))
            found.append((m.start(), m.group("id"),
                          re.sub(r"\s+", " ", m.group("text"))))
    return [(gid, txt) for _, gid, txt in sorted(found)]
