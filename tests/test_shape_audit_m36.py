"""M36 WP-G3 — the SHAPE-LIVES-IN-DATA absence audit (anti-compatibility-theater).

M36's acceptance carries a `grep`-level absence proof: *no engine module outside
the kernel and the docx adapter names an `activity` part slug or callout label as
a code constant*. The risk it exists to catch is named in the ticket's complexity
accounting: **compatibility theater** — a re-expression that keeps a private side
channel (a hard-coded constant consulted "just for the default case") passes
every behavioral test and defeats the purpose.

A pure ban is not implementable against v1's real code and would be theater of
its own: several literals are legitimately not shape (a spreadsheet column header
that happens to read "Procedure"), and several ARE shape but are the DOCUMENTED
v1 fallback path that WP-G2 deliberately kept (a stripped install with no
declaration must still produce a document, visibly rather than silently). So the
audit is ALLOWLIST-DRIVEN: every occurrence of an audited literal in `scripts/`
must be on the list below with a reason. A new, unlisted occurrence FAILS with a
message telling the developer to derive it from the declaration or justify it
here. Adding `SECTION_TITLES = {...}` to a new module fails on both checks.

THE AUDIT'S PRECISION, STATED HONESTLY (what it does and does not see):

  R1  Only string literals in the parsed AST are audited. Comments and
      docstrings are EXCLUDED BY RULE — prose cannot decide document shape, and
      auditing it would punish the explanatory comments this codebase wants.
      (Module, class and function docstrings are skipped explicitly; `#`
      comments never reach the AST.)
  R2  EXACT full-value equality, never substring. `"IO"` inside `"VERSION"` is
      not a callout prefix; `"scope"` inside `"--scope-delta"` is not a part
      slug. This is why the audit is precise enough to be enforceable — and also
      why it cannot see a slug assembled at runtime (`"quick" + "-reference"`),
      which is a limit, not a loophole worth closing: the reviewer reads diffs.
  R3  The allowlist is keyed (module, category, literal) and is LINE-AGNOSTIC —
      moving code does not churn the list, but introducing a NEW audited literal
      into a module does fail, which is the tripwire that matters.
  R4  Three modules are exempt wholesale, per the acceptance bullet's own
      carve-out: `kernel.py` (the declared-data authority itself),
      `definitions.py` (the deliverable-definition loader) and `render_glue.py`
      (the plan/adapter seam). `render.py` — the docx adapter, which the bullet
      also exempts — is deliberately NOT exempted wholesale but allowlisted
      entry by entry, because it is the module most able to hide a side channel.
  R5  The structural check (`test_no_new_shape_table...`) is stricter than the
      literal check: it bans a LITERAL TABLE of the shape vocabulary (a dict or
      list collecting several audited slugs/titles/labels) anywhere outside the
      enumerated homes, whatever it is named.
"""

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import kernel  # noqa: E402


# --------------------------------------------------------------------------- #
# The audited vocabulary — read from the DECLARATION, never typed here. If the
# declaration gains a part or a callout kind, the audit widens automatically.
# --------------------------------------------------------------------------- #
def _vocabulary() -> dict[str, set[str]]:
    tdecl = kernel.load_type("activity")
    return {
        "part-slug": {p.slug for p in tdecl.parts},
        "part-title": {p.title for p in tdecl.parts},
        "callout-label": {c.label for c in tdecl.callouts},
        "callout-prefix": {c.prefix for c in tdecl.callouts},
        # The agent-written derived kinds: shape in the same sense (which views
        # the deliverable has), and the constant WP-G2 re-pointed at the plan.
        "derived-kind": {"dependencies", "raci"},
    }


#: Wholesale exemptions — see R4.
EXEMPT_MODULES = {"kernel.py", "definitions.py", "render_glue.py"}

#: (module, category) -> (literals, why). Every audited literal occurrence in
#: `scripts/` lives here. `why` is the review record: a reader must be able to
#: tell a legitimate reference from a side channel WITHOUT rerunning the audit.
ALLOWLIST: dict[tuple[str, str], tuple[set[str], str]] = {

    # ---- doc_model.py — the V1 ENGINE'S REGISTRY, and its documented home.
    # M33 amendment A3 ruled that `doc_model`/`callouts` remain the tables' HOME
    # while the kernel loads its declarations from YAML, with the parity tests
    # (test_kernel_m33.py) as the anti-drift bond. These are therefore NOT
    # shims: they are the v1 engine's internal implementation of a shape the
    # kernel independently declares, and the parity test fails the moment the
    # two disagree. Retiring them is M37+ work (it moves the v1 parsers), not a
    # compatibility-gate deletion.
    ("doc_model.py", "part-slug"): (
        {"scope", "quick-reference", "before-you-start", "steps", "outputs",
         "controls", "issues"},
        "SECTION_TITLES + the frozen letter/title/slug alias maps: the v1 "
        "registry itself (M33 A3 home ruling), bonded to the declaration by "
        "tests/test_kernel_m33.py's parity assertion.",
    ),
    ("doc_model.py", "part-title"): (
        {"Scope", "At a Glance", "Before You Start", "Procedure",
         "Outputs & Evidence", "Key Controls",
         "Known Issues & Improvement Opportunities"},
        "Same registry, title half — the canonical titles the parity test "
        "diffs against kernel.load_type('activity').parts.",
    ),

    # ---- callouts.py — the V1 CALLOUT GRAMMAR'S HOME, same A3 ruling.
    ("callouts.py", "callout-label"): (
        {"CONTROL", "VALIDATION REQUIRED", "PAIN POINT",
         "IMPROVEMENT OPPORTUNITY", "SCREENSHOT PLACEHOLDER"},
        "LABEL_TO_PREFIX / LABEL_TO_HOME_SECTION: the v1 callout vocabulary's "
        "home (M33 A3), bonded to the declaration by the kernel parity test.",
    ),
    ("callouts.py", "callout-prefix"): (
        {"CTRL", "GAP", "PP", "IO", "SC"},
        "The prefix half of the same two maps, plus the ID-grammar regexes "
        "built from PREFIXES (which is derived, not typed).",
    ),
    ("callouts.py", "part-slug"): (
        {"controls", "issues", "steps"},
        "LABEL_TO_HOME_SECTION's values — the HOME of each callout kind, the "
        "table the declaration's `home:` field is derived from.",
    ),

    # ---- client_config.py — POLICY over the shape, not the shape.
    ("client_config.py", "part-slug"): (
        {"scope", "quick-reference", "steps", "controls", "issues"},
        "MANDATORY_SECTIONS (the three sections no profile may drop — a "
        "POLICY subset, not derivable from a declaration that says nothing "
        "about droppability) plus the two _declared_home() fallback values and "
        "one diagnostic that names `scope` in prose. ALL_SECTIONS, "
        "ALL_CALLOUTS, CONTROLS_SECTION and ISSUES_SECTION were re-pointed at "
        "the declaration in M36 WP-G3 and are no longer literals here.",
    ),
    ("client_config.py", "callout-label"): (
        {"CONTROL", "PAIN POINT"},
        "_declared_home() lookup keys (which callout's home each body_omit "
        "rule protects) and the BODY_OMIT_REGISTERS diagnostic text naming "
        "what would silently vanish.",
    ),
    ("client_config.py", "derived-kind"): (
        {"dependencies", "raci"},
        "DEFAULT_DERIVED — the v1 manifest's derived-kind vocabulary, which "
        "WP-G2 kept as the v1 fallback path when no definition resolves. "
        "Documented fallback, not a side channel.",
    ),

    # ---- scaffold.py — DOCUMENTED v1-FALLBACK SITE (WP-G2).
    ("scaffold.py", "part-slug"): (
        {"scope", "quick-reference", "before-you-start", "steps", "outputs",
         "controls", "issues"},
        "_FALLBACK_PART_BODIES keys: the per-section PLACEHOLDER PROSE. The "
        "declaration says a procedure has an `outputs` part titled 'Outputs & "
        "Evidence'; it does not say what a blank one should suggest to a "
        "drafter. Content, not shape — and WP-G2 removed every ordered section "
        "list from this module (declared_parts() reads the declaration).",
    ),
    ("scaffold.py", "derived-kind"): (
        {"dependencies", "raci"},
        "DERIVED_FILES: the v1 manifest's derived set (the fallback path when "
        "no definition resolves), same documented carve-out as client_config.",
    ),

    # ---- scope_delta.py — DOCUMENTED v1-FALLBACK SITE (WP-G2).
    ("scope_delta.py", "derived-kind"): (
        {"dependencies", "raci"},
        "AGENT_DERIVED_KINDS: WP-G2 re-pointed the reader at the plan's "
        "agent-writer kinds and KEPT this tuple as the documented fallback, so "
        "a missing definition never turns a work-order CLI into a refusal. The "
        "fallback is named in the docstring beside it.",
    ),

    # ---- render.py — the docx adapter (allowlisted, not exempted: R4).
    ("render.py", "derived-kind"): (
        {"raci"},
        "One behavior branch: the RACI register's rows are re-ordered by "
        "[[slug]] before token resolution. A per-view rendering rule keyed on "
        "the view's own kind, not a statement about what views exist.",
    ),

    # ---- The shipped python WRITERS: each names the callout kind it is a
    # register OF. `build_gap_log` aggregating `GAP` is the writer's identity;
    # the plan decides WHETHER it runs (WP-G2), the writer decides what it says.
    ("aggregate.py", "callout-prefix"): (
        {"CTRL", "GAP", "PP", "IO", "SC"},
        "_grouped_by_l2(ctx, <prefix>) inside build_appendix_a / "
        "build_appendix_controls / build_gap_log / build_screenshot_index, "
        "plus the PP severity-enum warning. Each shipped writer names the "
        "callout kind it aggregates — its own identity. The build LIST comes "
        "from the plan (WP-G2), never from these.",
    ),
    ("aggregate.py", "part-slug"): (
        {"scope", "quick-reference", "steps"},
        "Extraction reads of three NAMED sections: the At a Glance card "
        "bullets, and the scope/steps bodies carried into the extract bundle. "
        "A view that summarises the card must be able to name the card.",
    ),
    # (aggregate.py names NO callout label and NO derived kind as a literal —
    # its extract-bundle keys are `raci_inputs` / `raw_dependencies`, which are
    # field names, not kinds. The staleness test below proved that: entries
    # written for them on first draft failed as unmatched.)

    ("brief.py", "derived-kind"): (
        {"dependencies", "raci"},
        "SYNTH_KINDS + the per-kind reading list assembled for an agent "
        "writer's brief: which evidence file and which registry that kind's "
        "author must read. Brief CONTENT for a kind the plan named.",
    ),

    ("consolidate.py", "part-slug"): (
        {"scope", "quick-reference", "steps"},
        "PRIMER_SECTIONS (the two sections the cross-bucket digest carries "
        "verbatim) and the steps/scope digest branches — a summarizer naming "
        "the sections it summarises, at a declared-slug granularity.",
    ),

    ("engagement.py", "part-slug"): (
        {"scope"},
        "One read: the scope section's first lines, quoted into the "
        "engagement-level primer. Resolved THROUGH doc_model."
        "section_of_heading(), so the letter/alias handling stays shared.",
    ),

    ("kits.py", "callout-prefix"): (
        {"GAP", "SC"},
        "The gap kit and screenshot kit each select the callout kind they are "
        "a kit FOR — same writer-identity reasoning as aggregate's builders.",
    ),
    ("kits.py", "part-slug"): (
        {"quick-reference"},
        "Reads the At a Glance card to find the preparer a gap should be "
        "addressed to (M23 replaced `subs['B']` with this slug).",
    ),
    ("kits.py", "part-title"): (
        {"Procedure"},
        "FALSE POSITIVE of exact-match auditing, kept listed rather than "
        "special-cased: GAP_HEADER's spreadsheet column header 'Procedure' "
        "happens to equal a part title. It is a column label, not a section "
        "reference.",
    ),

    ("reconcile.py", "callout-label"): (
        {"PAIN POINT"},
        "One WARNING's text and its label match: a PAIN POINT missing "
        "Impact/Severity ships a blank register row. Validation of a kind the "
        "grammar (callouts.py) admits, matched via that shared map.",
    ),
}

#: Modules permitted to hold a LITERAL TABLE of the shape vocabulary (R5), with
#: the table named. Anything else — in any module, under any name — fails.
TABLE_HOMES = {
    "doc_model.py": "SECTION_TITLES + SECTION_*_ALIASES — the v1 registry's "
                    "home (M33 A3), parity-bonded to the declaration.",
    "callouts.py": "LABEL_TO_PREFIX + LABEL_TO_HOME_SECTION — the v1 callout "
                   "grammar's home (M33 A3), same bond.",
    "client_config.py": "MANDATORY_SECTIONS — the droppability POLICY subset, "
                        "which no declaration states.",
    "scaffold.py": "_FALLBACK_PART_BODIES — per-part placeholder PROSE "
                   "(content), the documented v1-fallback skeleton source.",
}

_FIX = (
    "\n\nEither DERIVE it from the declaration "
    "(kernel.load_type('activity').parts / .callouts, or the compiled plan for "
    "view/writer questions), or — if it is genuinely not document shape, or is "
    "a documented v1-fallback path — add it to ALLOWLIST in "
    "tests/test_shape_audit_m36.py WITH A REASON. The reason is the point: "
    "M36's review risk is compatibility theater, and an unexplained constant "
    "is what it looks like."
)


def _audited_strings(path: Path):
    """(lineno, value) for every non-docstring string literal in the module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    skip = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            first = node.body[0] if node.body else None
            if (isinstance(first, ast.Expr)
                    and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                skip.add(id(first.value))
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                and id(node) not in skip):
            yield node.lineno, node.value


def _modules():
    return [p for p in sorted(SCRIPTS.glob("*.py"))
            if p.name not in EXEMPT_MODULES]


# --------------------------------------------------------------------------- #
# The audit
# --------------------------------------------------------------------------- #
def test_every_shape_literal_in_scripts_is_allowlisted():
    """M36 acceptance bullet 2, mechanized: no engine module names an activity
    part slug/title, a callout label/prefix, or a derived kind as a code literal
    unless the ALLOWLIST above says why."""
    vocab = _vocabulary()
    offenders = []
    for path in _modules():
        for lineno, value in _audited_strings(path):
            for category, items in vocab.items():
                if value not in items:
                    continue
                allowed, _why = ALLOWLIST.get((path.name, category),
                                              (frozenset(), ""))
                if value not in allowed:
                    offenders.append(
                        f"{path.name}:{lineno}: {category} {value!r} is not on "
                        f"the shape-audit allowlist"
                    )
    assert offenders == [], (
        "Unjustified document-shape literal(s) in scripts/:\n  "
        + "\n  ".join(offenders) + _FIX
    )


def test_the_allowlist_has_no_stale_entries():
    """The list shrinks as the migration continues: an entry that no longer
    matches anything must be deleted, or the list becomes a fiction that hides
    the next real occurrence behind an already-blessed literal."""
    vocab = _vocabulary()
    seen: set[tuple[str, str, str]] = set()
    for path in _modules():
        for _lineno, value in _audited_strings(path):
            for category, items in vocab.items():
                if value in items:
                    seen.add((path.name, category, value))
    stale = []
    for (module, category), (literals, _why) in ALLOWLIST.items():
        for literal in literals:
            if (module, category, literal) not in seen:
                stale.append(f"{module} / {category} / {literal!r}")
    assert stale == [], (
        "Stale shape-audit allowlist entries (nothing in scripts/ matches "
        "them any more — delete them):\n  " + "\n  ".join(sorted(stale))
    )


def test_every_allowlist_entry_carries_a_reason():
    """An allowlist without reasons is an allowlist that always passes."""
    thin = [f"{m} / {c}" for (m, c), (_lits, why) in ALLOWLIST.items()
            if len(why.strip()) < 40]
    assert thin == [], f"Allowlist entries with no real justification: {thin}"
    assert not (set(ALLOWLIST) & {(m, c) for m, c in ALLOWLIST
                                  if m in EXEMPT_MODULES}), \
        "An exempt module must not also be allowlisted — one rule per module."


def test_no_new_shape_table_outside_its_declared_home():
    """R5: the tripwire that fails if someone adds `SECTION_TITLES = {...}` (or
    the same table under any other name) to a new module.

    A LITERAL TABLE is a dict/list/tuple/set literal collecting several members
    of the audited vocabulary: >=3 part slugs, >=2 part titles, >=3 callout
    labels or >=3 callout prefixes. That is a second spelling of the document's
    shape, whatever it is called and whatever it is used for.
    """
    vocab = _vocabulary()
    thresholds = {"part-slug": 3, "part-title": 2, "callout-label": 3,
                  "callout-prefix": 3}
    offenders = []
    for path in _modules():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Dict, ast.List, ast.Tuple, ast.Set)):
                continue
            members = []
            if isinstance(node, ast.Dict):
                members = [k for k in node.keys] + list(node.values)
            else:
                members = list(node.elts)
            values = {m.value for m in members
                      if isinstance(m, ast.Constant)
                      and isinstance(m.value, str)}
            for category, floor in thresholds.items():
                hits = values & vocab[category]
                if len(hits) >= floor and path.name not in TABLE_HOMES:
                    offenders.append(
                        f"{path.name}:{node.lineno}: literal table of "
                        f"{len(hits)} {category}s ({sorted(hits)})"
                    )
    assert offenders == [], (
        "A second spelling of the document's shape appeared outside its "
        "declared home:\n  " + "\n  ".join(offenders)
        + "\n\nThe shape lives in kernel/types/activity.yaml. Derive the list "
        "(kernel.load_type('activity')), or — if the module is a documented "
        "v1-fallback/prose site — add it to TABLE_HOMES with the table named."
        + _FIX
    )


def test_the_retired_symbols_stay_retired():
    """WP-G3's deletions, pinned: a re-export that comes back is a shim that
    came back. Each was verified unread by any module or test before removal."""
    import aggregate
    assert not hasattr(aggregate, "SUBSECTION_RE"), (
        "aggregate.SUBSECTION_RE was a bare re-export of "
        "doc_model.SECTION_HEADING_RE, read by nothing — retired in M36 WP-G3."
    )
    for dead in ("ISSUES_SECTION", "CONTROLS_SECTION"):
        assert not hasattr(aggregate, dead), (
            f"aggregate.{dead} was a duplicate of the callout's declared home "
            f"(callouts.home_section / the declaration's `home:`), read by "
            f"nothing — retired in M36 WP-G3."
        )


def test_the_repointed_constants_track_the_declaration(monkeypatch):
    """The re-pointing is REAL, not decorative: the profile vocabulary follows
    the declaration, so a reshape cannot leave client_config behind."""
    import importlib
    import client_config
    tdecl = kernel.load_type("activity")
    assert client_config.ALL_SECTIONS == [p.slug for p in tdecl.parts]
    assert client_config.ALL_CALLOUTS == [c.label for c in tdecl.callouts]
    homes = {c.label: c.home for c in tdecl.callouts}
    assert client_config.CONTROLS_SECTION == homes["CONTROL"]
    assert client_config.ISSUES_SECTION == homes["PAIN POINT"]

    # Reshape the declaration (a part renamed, a callout re-homed) and reimport:
    # the constants must MOVE. A hard-coded copy would not.
    import copy
    reshaped = copy.deepcopy(tdecl)
    reshaped.parts.append(kernel.PartDecl(slug="afterword", title="Afterword",
                                          kind="prose"))
    for c in reshaped.callouts:
        if c.label == "CONTROL":
            c.home = "afterword"
    monkeypatch.setattr(kernel, "load_type", lambda name: reshaped)
    reloaded = importlib.reload(client_config)
    try:
        assert reloaded.ALL_SECTIONS[-1] == "afterword"
        assert reloaded.CONTROLS_SECTION == "afterword"
    finally:
        monkeypatch.undo()
        importlib.reload(client_config)
