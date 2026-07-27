#!/usr/bin/env python3
"""
aggregate.py — CONSULT mechanical aggregator (M3).

Deterministic, zero-token regeneration of the python-owned derived views for one
area folder. Reads `manifest.json`, every `role: procedure` fragment, and the
`_reference/*.yaml` registry, then:

  (a) rebuilds the python-owned derived files in full, each with a single writer,
      `[[slug]]` cross-reference tokens, and a re-emitted
      `<!-- derived: KIND; writer: python -->` marker:
        06_procedure-index   (procedure-index)
        07_role-dictionary   (role-dictionary)
        08_systems           (systems)
        88_appendix-a        (appendix-a; typed PP / IO rows)
        89_appendix-controls (appendix-controls; CTRL rows — M14, opt-in)
        90_appendix-b-gaps   (gap-log)
        91_appendix-c-screens(screenshot-index)
  (b) writes a `> _Pending synthesis (M5)._` placeholder (+ marker) into the
      agent-owned derived files (82_dependencies, 84_raci);
  (c) emits the scratch extract bundle `<area>.extract.json` (git-ignored) with
      `raw_dependencies` + `raci_inputs` for the M5 agents.

Contract (see docs/README.md "Extraction / matching contract"):
  - Inline callout label line:  `> **<LABEL> — <ID>:** <text>`
    Delimiter parsed tolerantly (`-`/`–`/`—`); ID grammar strict; IDs are
    procedure-local. LABEL→prefix map enforced (fail-loud ERROR on mismatch).
  - Callout sub-fields: `> - **<Field>:** <value>` bullets directly under the
    label line. A missing optional field parses as blank (NOT an error).
  - Body gap tags: `[[GAP-NN — TEXT]]`; a bare `[[GAP — …]]` is an ERROR.
  - Nouns are bound via each procedure's `consult-meta` slug lists — never by
    scraping prose. A slug absent from `_reference/*.yaml` is a WARNING (the human
    registry top-up loop resolves it), never dropped, never guessed.

Fail-loud ERRORs (nonzero exit, nothing dropped):
  - bare gap tag;
  - referenced-but-undefined ID within a procedure;
  - ID prefix not matching its callout label;
  - conflicting duplicate ID within a procedure.

Idempotent: two runs with no procedure/registry change produce byte-identical
outputs.

Usage:
    python3 scripts/aggregate.py components/<area>

Exit code:
    0 = derived views rebuilt (WARNINGs allowed)
    1 = fail-loud ERROR in a procedure fragment (nothing written)
    2 = bad usage / unreadable input
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

# doc_model.py is the M2-owned shared spine (manifest + display_numbers). Import
# it; never re-implement it here. Ensure the scripts/ dir is importable when this
# file is run as `python3 scripts/aggregate.py …` from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import doc_model  # noqa: E402  (M2 deliverable)


# ---------------------------------------------------------------------------
# Callout grammar: the drift-critical primitives (LABEL→prefix map, severity
# enum, tolerant delimiter, ID / gap grammar, fence util, FragmentError) live in
# the shared `callouts.py` — imported here and by reconcile.py so they never
# drift. This file keeps only the aggregate-specific matchers built on top.
# ---------------------------------------------------------------------------
from callouts import (  # noqa: E402
    LABEL_TO_PREFIX, SEVERITY_ENUM, DELIM as _DELIM, ID_STRICT_RE,
    BODY_GAP_RE, BARE_GAP_RE, FragmentError, blank_fences as _blank_fences,
    DETAIL_FIELD,
)

# Callout label line: `> **<LABEL> — <ID>:** <text>` (colon INSIDE the bold).
CALLOUT_LINE_RE = re.compile(
    r"^\s*>\s*\*\*\s*(?P<label>[A-Z][A-Z ]*?)\s*" + _DELIM + r"\s*"
    r"(?P<id>[A-Za-z]+-[A-Za-z0-9\-]+)\s*:\s*\*\*\s*(?P<text>.*?)\s*$"
)

# Callout sub-field bullet: `> - **<Field>:** <value>`. Leading whitespace is
# allowed — drafters legitimately nest callouts inside list items.
SUBFIELD_RE = re.compile(
    r"^\s*>\s*-\s*\*\*\s*(?P<field>[^:*]+?)\s*:\s*\*\*\s*(?P<value>.*?)\s*$"
)

# consult-meta fenced block (info-string `consult-meta`, YAML body).
CONSULT_META_RE = re.compile(
    r"^(?P<fence>`{3,}|~{3,})\s*consult-meta\s*$(?P<body>.*?)^(?P=fence)\s*$",
    re.MULTILINE | re.DOTALL,
)

# A `### A. Heading` sub-section line.
SUBSECTION_RE = re.compile(r"^###\s+(?P<letter>[A-H])\.\s+(?P<title>.*?)\s*$")

# A `- **Label:** value` list bullet (Quick Reference etc.).
BULLET_KV_RE = re.compile(r"^\s*-\s*\*\*\s*(?P<k>[^:*]+?)\s*:\s*\*\*\s*(?P<v>.*?)\s*$")


def split_subsections(text: str) -> dict[str, str]:
    """Return {letter: body_text} for the `### A.`..`### H.` sub-sections."""
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    for line in text.splitlines():
        m = SUBSECTION_RE.match(line)
        if m:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = m.group("letter")
            buf = []
            continue
        if line.startswith("## "):  # next fragment / non A-H heading ends the run
            if current is not None:
                sections[current] = "\n".join(buf).strip()
                current = None
            buf = []
            continue
        if current is not None:
            buf.append(line)
    if current is not None:
        sections[current] = "\n".join(buf).strip()
    return sections


def parse_bullets(body: str) -> dict[str, str]:
    """Parse `- **Label:** value` bullets from a section body into a dict."""
    out: dict[str, str] = {}
    for line in body.splitlines():
        m = BULLET_KV_RE.match(line)
        if m:
            out[m.group("k").strip()] = m.group("v").strip()
    return out


def _pick(d: dict[str, str], *candidates: str) -> str:
    for c in candidates:
        for k, v in d.items():
            if k.lower() == c.lower():
                return v
    return ""


def parse_consult_meta(raw_text: str) -> dict[str, list[str]]:
    """Extract the `consult-meta` slug lists. Missing block → empty lists."""
    m = CONSULT_META_RE.search(raw_text)
    if not m:
        return {"systems": [], "roles": []}
    try:
        data = yaml.safe_load(m.group("body")) or {}
    except yaml.YAMLError as exc:
        raise FragmentError(f"malformed consult-meta YAML: {exc}") from exc
    if not isinstance(data, dict):
        return {"systems": [], "roles": []}

    def _slugs(key: str) -> list[str]:
        v = data.get(key) or []
        if isinstance(v, str):
            v = [v]
        return [str(s).strip() for s in v if str(s).strip()]

    return {"systems": _slugs("systems"), "roles": _slugs("roles")}


def parse_callouts(slug: str, raw_text: str) -> list[dict]:
    """Parse every inline callout in a procedure fragment.

    Fail-loud (raises FragmentError) on: bad ID grammar, unknown callout label,
    a prefix that does not match its label, or a duplicate ID within this
    procedure. Missing optional sub-fields parse as blank, not an error.

    Returns a list of dicts: {label, prefix, id, text, fields, section?}.
    """
    text = _blank_fences(raw_text)
    lines = text.splitlines()
    callouts: list[dict] = []
    seen: dict[str, int] = {}

    i = 0
    while i < len(lines):
        m = CALLOUT_LINE_RE.match(lines[i])
        if not m:
            i += 1
            continue
        label = re.sub(r"\s+", " ", m.group("label")).strip()
        cid = m.group("id").strip()

        if label not in LABEL_TO_PREFIX:
            raise FragmentError(
                f"unknown callout label {label!r} at {slug}:{i + 1} "
                f"(expected one of {', '.join(sorted(LABEL_TO_PREFIX))})"
            )
        expected = LABEL_TO_PREFIX[label]

        if not ID_STRICT_RE.match(cid):
            raise FragmentError(
                f"malformed callout ID {cid!r} at {slug}:{i + 1} "
                f"(grammar: <PREFIX>-<ALNUM> e.g. {expected}-001)"
            )
        prefix = cid.split("-", 1)[0]
        if prefix != expected:
            raise FragmentError(
                f"ID prefix/label mismatch at {slug}:{i + 1}: label {label!r} "
                f"requires prefix {expected}- but ID is {cid!r}"
            )
        if cid in seen:
            raise FragmentError(
                f"duplicate ID {cid!r} within procedure {slug} "
                f"(first at line {seen[cid]}, again at line {i + 1})"
            )
        seen[cid] = i + 1

        # Consume the WHOLE contiguous blockquote below the label line:
        # plain `> ...` continuation lines extend the callout text (drafters
        # hard-wrap long sentences), `> - **Field:** value` bullets become
        # sub-fields, and a wrapped field value's continuation lines extend
        # that field. Stop at the first non-quote line or a new callout.
        fields: dict[str, str] = {}
        text_parts = [m.group("text").strip()]
        cur_field: str | None = None
        j = i + 1
        while j < len(lines):
            line = lines[j]
            if CALLOUT_LINE_RE.match(line):
                break  # a new callout starts its own block
            sm = SUBFIELD_RE.match(line)
            if sm:
                cur_field = sm.group("field").strip()
                fields[cur_field] = sm.group("value").strip()
                j += 1
                continue
            qm = re.match(r"^\s*>\s?(.*)$", line)
            if qm is None:
                break  # blockquote ended
            cont = qm.group(1).strip()
            if cont:
                if cur_field is not None:
                    fields[cur_field] = (fields[cur_field] + " " + cont).strip()
                else:
                    text_parts.append(cont)
            j += 1

        callouts.append(
            {"label": label, "prefix": prefix, "id": cid,
             "text": " ".join(p for p in text_parts if p), "fields": fields}
        )
        i = j
    return callouts


def check_body_gap_refs(slug: str, raw_text: str, defined_gap_ids: set[str]) -> None:
    """Fail-loud on bare gap tags and body gap refs with no matching callout."""
    text = _blank_fences(raw_text)
    if BARE_GAP_RE.search(text):
        raise FragmentError(
            f"bare gap tag in {slug}: use [[GAP-NN — reason]] with an ID"
        )
    for m in BODY_GAP_RE.finditer(text):
        gid = "GAP-" + m.group(1)
        if gid not in defined_gap_ids:
            raise FragmentError(
                f"referenced-but-undefined ID {gid!r} in {slug}: the body tag has "
                f"no matching VALIDATION REQUIRED callout in this procedure"
            )


# ---------------------------------------------------------------------------
# Registry loading (nouns).
# ---------------------------------------------------------------------------

def _normalize_registry(data, name_default_key: str) -> dict[str, dict]:
    """Accept either {slug: {...}} mapping or [ {slug, ...} ] list; key by slug."""
    out: dict[str, dict] = {}
    if isinstance(data, dict):
        # Could be {slug: entry} or {"systems": {...}} / {"systems": [...]}.
        if name_default_key in data and isinstance(data[name_default_key], (dict, list)):
            return _normalize_registry(data[name_default_key], name_default_key)
        for slug, entry in data.items():
            entry = dict(entry or {})
            entry.setdefault("slug", slug)
            out[str(slug)] = entry
    elif isinstance(data, list):
        for entry in data:
            entry = dict(entry or {})
            slug = str(entry.get("slug", "")).strip()
            if slug:
                out[slug] = entry
    return out


def load_registry(area: Path, filename: str, top_key: str) -> dict[str, dict]:
    path = area / "_reference" / filename
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return _normalize_registry(data, top_key)


# ---------------------------------------------------------------------------
# Rendering helpers.
# ---------------------------------------------------------------------------

def tok(slug: str) -> str:
    return f"[[{slug}]]"


def cell(v: str) -> str:
    """Escape a value for a Markdown table cell."""
    v = (v or "").strip()
    if not v:
        return "—"
    return v.replace("|", "\\|").replace("\n", " ")


def marker(kind: str, writer: str) -> str:
    return f"<!-- derived: {kind}; writer: {writer} -->"


# ---------------------------------------------------------------------------
# Derived-view builders. Each returns the section BODY (below heading+marker).
# All ordering is deterministic for idempotency.
# ---------------------------------------------------------------------------

def build_procedure_index(ctx) -> str:
    lines = ["_In-scope procedures, grouped by sub-process. Numbers are rendered "
             "late from the cross-reference tokens in the Ref column._", ""]
    for l2 in ctx["l2_order"]:
        procs = ctx["procs_by_l2"].get(l2, [])
        if not procs:
            continue
        lines.append(f"### {ctx['l2_titles'].get(l2, l2)}")
        lines.append("")
        lines.append("| Ref | Procedure | Frequency | Primary Owner |")
        lines.append("|---|---|---|---|")
        for p in procs:
            qr = p["quick_ref"]
            lines.append(
                f"| [[#{p['slug']}]] | {cell(p['title'])} | "
                f"{cell(_pick(qr, 'Frequency', 'Cadence'))} | "
                f"{cell(_pick(qr, 'Primary Owner', 'Owner', 'Preparer'))} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def build_role_dictionary(ctx) -> str:
    roles = ctx["roles_registry"]
    appears = ctx["role_appears_in"]  # slug -> set(procedure slugs)
    lines = ["_Canonical functional roles (from `_reference/roles.yaml`) with the "
             "procedures each appears in._", ""]
    lines.append("| Functional Role | Reports To | Standard Responsibilities |")
    lines.append("|---|---|---|")
    for slug in sorted(roles):
        r = roles[slug]
        resp = r.get("responsibilities", "")
        if isinstance(resp, list):
            resp = "; ".join(str(x) for x in resp)
        resp = str(resp).strip()
        used = ctx["order_sorted"](appears.get(slug, set()))
        if used:
            # Bare ref numbers only — appended after the responsibilities text
            # (or standing alone when there is none).
            refs = ", ".join(f"[[#{s}]]" for s in used)
            resp = f"{resp} ({refs})".strip() if resp else refs
        lines.append(
            f"| {cell(r.get('name', slug))} | "
            f"{cell(str(r.get('reports_to', r.get('reports-to', ''))))} | "
            f"{cell(resp)} |"
        )
    return "\n".join(lines)


def build_systems(ctx) -> str:
    systems = ctx["systems_registry"]
    related = ctx["system_related"]  # slug -> set(procedure slugs)
    lines = ["_Canonical systems (from `_reference/systems.yaml`) with the "
             "procedures that use each, from `consult-meta` bindings._", ""]
    lines.append("| System / Tool | Role in Process | Related Procedures |")
    lines.append("|---|---|---|")
    for slug in sorted(systems):
        s = systems[slug]
        used = ctx["order_sorted"](related.get(slug, set()))
        rel_cell = ", ".join(f"[[#{x}]]" for x in used) if used else "—"
        lines.append(
            f"| {cell(s.get('name', slug))} | "
            f"{cell(str(s.get('description', s.get('role', ''))))} | "
            f"{rel_cell} |"
        )
    return "\n".join(lines)


def _grouped_by_l2(ctx, prefix: str):
    """Yield (l2-title, [(procedure, callout), ...]) in document order.

    Appendix layout convention: rows are grouped under an `#### <L2 title>`
    sub-heading per sub-process, each row carrying its procedure token as a
    number-only `[[#slug]]` inside the combined FIRST cell alongside the
    display ID (reconcile's derived-row check pairs the first-cell ID with
    the last [[token]] on the row).
    IDs shown are the document-global display IDs from
    doc_model.callout_display_ids (ctx["disp"]) — drafters' local IDs never
    reach the reader, so nothing looks duplicated.
    """
    for l2 in ctx["l2_order"]:
        rows = []
        for p in ctx["procs_by_l2"].get(l2, []):
            for c in p["callouts"]:
                if c["prefix"] == prefix:
                    rows.append((p, c))
        if rows:
            yield ctx["l2_titles"].get(l2, l2), rows


def _disp(ctx, p, c) -> str:
    return ctx["disp"].get((p["slug"], c["id"]), c["id"])


_ID_MENTION_RE = re.compile(r"\b(?:CTRL|GAP|PP|IO|SC)-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")


def _disp_text(ctx, p, text: str) -> str:
    """Translate local callout IDs quoted INSIDE a callout's text (e.g. a
    body-gap token `[[GAP-02 — label]]`) to display IDs. Same context rule as
    render: an ID inside procedure content is that procedure's local ID."""
    slug = p["slug"]
    return _ID_MENTION_RE.sub(
        lambda m: ctx["disp"].get((slug, m.group(0)), m.group(0)), text or ""
    )


def _body(ctx, p, c) -> str:
    """The register's view of a callout body — M16 move 3, the appendix half.

    The label-line text is the short headline the drafter also shows in the
    step; a `detail:` sub-field is the FULL account, authored once and rendered
    ONLY here (render blanks it out of the procedure body). Appending rather
    than replacing keeps the headline in front of the dossier and means a
    callout with no `detail:` produces exactly the cell it produced before M16.

    This reads the FRAGMENT, so a detail whose home section is `body_omit`ed —
    or hidden by the profile entirely — still lands in its register. Not being
    in the body is precisely why the register exists.
    """
    text = _disp_text(ctx, p, c["text"])
    detail = _disp_text(ctx, p, _pick(c["fields"], DETAIL_FIELD))
    return f"{text} {detail}".strip() if detail else text


def build_appendix_a(ctx) -> str:
    lines = ["_Pain Points and Improvement Opportunities, aggregated mechanically "
             "from the `H` section callouts (observation, impact, severity authored "
             "in the callout). IDs are numbered sequentially through the document; "
             "rows are grouped by sub-process._", ""]

    lines.append("### Pain Points")
    any_pp = False
    for l2_title, rows in _grouped_by_l2(ctx, "PP"):
        any_pp = True
        lines += ["", f"#### {l2_title}", "",
                  "| ID | Observation | Impact | Severity |",
                  "|---|---|---|---|"]
        for p, c in rows:
            f = c["fields"]
            lines.append(
                f"| {_disp(ctx, p, c)} ([[#{p['slug']}]]) | "
                f"{cell(_body(ctx, p, c))} | "
                f"{cell(_pick(f, 'Impact'))} | {cell(_pick(f, 'Severity'))} |"
            )
    if not any_pp:
        lines += ["", "_No pain points recorded._"]
    lines.append("")

    lines.append("### Improvement Opportunities")
    any_io = False
    for l2_title, rows in _grouped_by_l2(ctx, "IO"):
        any_io = True
        lines += ["", f"#### {l2_title}", "",
                  "| ID | Recommendation | Addresses |",
                  "|---|---|---|"]
        for p, c in rows:
            f = c["fields"]
            # `Addresses:` names sibling PPs by LOCAL id (possibly a comma-
            # separated list) — same procedure by contract — translate each.
            addresses = _disp_text(ctx, p, _pick(f, "Addresses"))
            lines.append(
                f"| {_disp(ctx, p, c)} ([[#{p['slug']}]]) | "
                f"{cell(_body(ctx, p, c))} | {cell(addresses)} |"
            )
    if not any_io:
        lines += ["", "_No improvement opportunities recorded._"]
    return "\n".join(lines)


def build_appendix_controls(ctx) -> str:
    """The M14 controls register — `appendix-controls`.

    Pain points have had a register since M3 (Appendix A, built from the `H`
    callouts); controls had none, because `F. Key Controls` is a SECTION. So an
    engagement that moves F out of the procedure body (`body_omit: [F]`) needs
    this destination, or the controls simply vanish — which is why the profile
    validator refuses that combination.

    No new machinery: the callout parser, the ID scheme, the display-ID map and
    the by-L2 grouping are exactly what Appendix A uses, pointed at CTRL. Only
    emitted when the profile asks for it (the manifest is the authority: this
    builder runs iff an `appendix-controls` component is listed).
    """
    lines = ["_Key controls, aggregated mechanically from the `F` section "
             "callouts (statement, type, frequency and owner authored in the "
             "callout). IDs are numbered sequentially through the document; "
             "rows are grouped by sub-process._"]
    any_row = False
    for l2_title, rows in _grouped_by_l2(ctx, "CTRL"):
        any_row = True
        lines += ["", f"#### {l2_title}", "",
                  "| Control ID | Control | Type | Frequency | Owner |",
                  "|---|---|---|---|---|"]
        for p, c in rows:
            f = c["fields"]
            lines.append(
                f"| {_disp(ctx, p, c)} ([[#{p['slug']}]]) | "
                f"{cell(_body(ctx, p, c))} | "
                f"{cell(_pick(f, 'Type'))} | "
                f"{cell(_pick(f, 'Frequency'))} | "
                f"{cell(_pick(f, 'Owner'))} |"
            )
    if not any_row:
        lines += ["", "_No controls recorded._"]
    return "\n".join(lines)


def build_gap_log(ctx) -> str:
    lines = ["_Validation gaps aggregated from the `VALIDATION REQUIRED` "
             "callouts. IDs are numbered sequentially through the document; "
             "rows are grouped by sub-process._"]
    any_row = False
    for l2_title, rows in _grouped_by_l2(ctx, "GAP"):
        any_row = True
        lines += ["", f"#### {l2_title}", "",
                  "| Gap ID | Description | Nature | Owner to Confirm |",
                  "|---|---|---|---|"]
        for p, c in rows:
            f = c["fields"]
            lines.append(
                f"| {_disp(ctx, p, c)} ([[#{p['slug']}]]) | "
                f"{cell(_body(ctx, p, c))} | "
                f"{cell(_pick(f, 'Nature'))} | "
                f"{cell(_pick(f, 'Owner to confirm', 'Owner'))} |"
            )
    if not any_row:
        lines += ["", "_No open validation gaps._"]
    return "\n".join(lines)


def build_screenshot_index(ctx) -> str:
    lines = ["_Screenshot placeholders aggregated from the `SCREENSHOT "
             "PLACEHOLDER` callouts. IDs are numbered sequentially through "
             "the document; rows are grouped by sub-process._"]
    any_row = False
    for l2_title, rows in _grouped_by_l2(ctx, "SC"):
        any_row = True
        lines += ["", f"#### {l2_title}", "",
                  "| SC ID | Caption | Status |",
                  "|---|---|---|"]
        for p, c in rows:
            lines.append(
                f"| {_disp(ctx, p, c)} ([[#{p['slug']}]]) | "
                f"{cell(_body(ctx, p, c))} | Pending user input |"
            )
    if not any_row:
        lines += ["", "_No screenshot placeholders recorded._"]
    return "\n".join(lines)


PY_BUILDERS = {
    "procedure-index": build_procedure_index,
    "role-dictionary": build_role_dictionary,
    "systems": build_systems,
    "appendix-a": build_appendix_a,
    "appendix-controls": build_appendix_controls,
    "gap-log": build_gap_log,
    "screenshot-index": build_screenshot_index,
}

PENDING_PLACEHOLDER = "> _Pending synthesis (M5)._"


def write_derived(path: Path, heading: str, kind: str, writer: str, body: str) -> None:
    content = f"## {heading}\n\n{marker(kind, writer)}\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Main.
# ---------------------------------------------------------------------------

def run(area_arg: str) -> int:
    area = Path(area_arg)
    if area.name == "manifest.json":
        area = area.parent
    if not area.is_dir():
        print(f"Not a directory: {area_arg}")
        return 2

    manifest = doc_model.load_manifest(area)
    numbers = doc_model.display_numbers(manifest)  # {slug: "L2.seq"}

    components = manifest.get("components", [])
    order_of = {}
    for c in components:
        if "slug" in c:
            order_of[c["slug"]] = c.get("order", 0)

    def order_sorted(slugs):
        return sorted(slugs, key=lambda s: (order_of.get(s, 10**9), s))

    # ---- Parse every procedure fragment (fail-loud). ----
    warnings: list[str] = []
    procedures: list[dict] = []
    for c in components:
        if c.get("role") != "procedure":
            continue
        slug = c["slug"]
        fpath = area / c["file"]
        if not fpath.exists():
            print(f"ERROR: missing procedure file {c['file']} for slug {slug}")
            return 1
        raw = fpath.read_text(encoding="utf-8")
        try:
            callouts = parse_callouts(slug, raw)
            gap_ids = {c2["id"] for c2 in callouts if c2["prefix"] == "GAP"}
            check_body_gap_refs(slug, raw, gap_ids)
            meta = parse_consult_meta(raw)
        except FragmentError as exc:
            print(f"ERROR [{slug}]: {exc}")
            return 1

        sections = split_subsections(raw)
        quick_ref = parse_bullets(sections.get("B", ""))

        # Severity enum sanity → WARNING (never fail-loud; ID grammar only fails).
        for co in callouts:
            if co["prefix"] == "PP":
                sev = co["fields"].get("Severity", "").strip()
                if sev and sev not in SEVERITY_ENUM:
                    warnings.append(
                        f"{slug}/{co['id']}: severity {sev!r} not in "
                        f"{{High|Medium|Low}}"
                    )

        procedures.append({
            "slug": slug,
            "title": c.get("heading", slug),
            "l2": c.get("l2"),
            "order": c.get("order", 0),
            "callouts": callouts,
            "meta": meta,
            "quick_ref": quick_ref,
            "section_a": sections.get("A", ""),
            "section_e": sections.get("E", ""),
        })

    # ---- Registry joins (nouns via consult-meta slug lists only). ----
    systems_registry = load_registry(area, "systems.yaml", "systems")
    roles_registry = load_registry(area, "roles.yaml", "roles")

    system_related: dict[str, set] = {}
    role_appears_in: dict[str, set] = {}
    for p in procedures:
        for s in p["meta"]["systems"]:
            system_related.setdefault(s, set()).add(p["slug"])
            if s not in systems_registry:
                warnings.append(
                    f"{p['slug']}: consult-meta system slug {s!r} not in "
                    f"_reference/systems.yaml — add an entry/alias"
                )
        for r in p["meta"]["roles"]:
            role_appears_in.setdefault(r, set()).add(p["slug"])
            if r not in roles_registry:
                warnings.append(
                    f"{p['slug']}: consult-meta role slug {r!r} not in "
                    f"_reference/roles.yaml — add an entry/alias"
                )

    # ---- Group procedures by L2 for the index. ----
    l2_order = manifest.get("l2_order", [])
    procs_by_l2: dict[str, list] = {l2: [] for l2 in l2_order}
    for p in sorted(procedures, key=lambda x: numbers.get(x["slug"], x["slug"])):
        procs_by_l2.setdefault(p["l2"], []).append(p)

    ctx = {
        # (slug, local-id) -> document-global display id (render-time
        # numbering authority; body sections use the same map in render.py).
        "disp": doc_model.callout_display_ids(area),
        "procedures": sorted(procedures, key=lambda x: order_of.get(x["slug"], 0)),
        "systems_registry": systems_registry,
        "roles_registry": roles_registry,
        "system_related": system_related,
        "role_appears_in": role_appears_in,
        "order_sorted": order_sorted,
        "l2_order": l2_order,
        "l2_titles": {l2: l2.replace("-", " ").title() for l2 in l2_order},
        "procs_by_l2": procs_by_l2,
    }

    # ---- Write derived files driven by the manifest. ----
    written: list[str] = []
    for c in components:
        if c.get("role") != "derived":
            continue
        kind = c.get("derived_kind")
        writer = c.get("writer")
        heading = c.get("heading", kind)
        path = area / c["file"]
        if writer == "python":
            builder = PY_BUILDERS.get(kind)
            if builder is None:
                warnings.append(f"no python builder for derived_kind {kind!r} "
                                f"({c['file']}) — skipped")
                continue
            write_derived(path, heading, kind, "python", builder(ctx))
            written.append(c["file"])
        elif writer == "agent":
            # Agent-owned view: the M5 agent is its ONE writer. Only stamp the
            # pending placeholder when there is no real content yet (missing file
            # or a scaffold/placeholder stub) — never clobber an agent's work on
            # re-aggregation. Staleness vs changed procedures is scope_delta's
            # job, not ours.
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            if (not existing or PENDING_PLACEHOLDER in existing
                    or "_Pending generation._" in existing):
                write_derived(path, heading, kind, "agent", PENDING_PLACEHOLDER)
                written.append(c["file"])

    # ---- Emit the scratch extract bundle for M5. ----
    raw_dependencies = {p["slug"]: p["section_a"] for p in procedures}
    raci_inputs = {
        p["slug"]: {
            "preparer": _pick(p["quick_ref"], "Preparer"),
            "reviewer": _pick(p["quick_ref"], "Reviewer"),
            "roles": p["meta"]["roles"],
            "steps_text": p["section_e"],
        }
        for p in procedures
    }
    bundle = {
        "area": manifest.get("area"),
        "raw_dependencies": raw_dependencies,
        "raci_inputs": raci_inputs,
    }
    bundle_path = area / f"{manifest.get('area', 'area')}.extract.json"
    bundle_path.write_text(
        json.dumps(bundle, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # ---- Report. ----
    print(f"Aggregated {len(procedures)} procedure(s); "
          f"rebuilt {len(written)} derived file(s).")
    for f in written:
        print(f"  - {f}")
    print(f"  - {bundle_path.name} (scratch extract bundle)")
    if warnings:
        print("\nWARNINGS (registry top-up worklist):")
        for w in warnings:
            print(f"- {w}")
    # M7 signal file: record proc/registry hashes + warnings so the read-only
    # orchestrator advisor knows aggregate ran clean this pass.
    import orchestrate
    orchestrate.emit_aggregate(str(area), warnings)
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    return run(argv[1])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
