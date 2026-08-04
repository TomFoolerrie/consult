"""Tests for scripts/reconcile.py — the QC gate: clean pass, each major ERROR
and WARNING check on a constructed violation, and the .reconcile.json signal."""

import json

import reconcile


# --------------------------------------------------------------------------- #
# Synthetic area factory
# --------------------------------------------------------------------------- #

SYSTEMS_YAML = """\
systems:
  - slug: netsuite
    name: NetSuite
    description: ERP of record
"""

ROLES_YAML = """\
roles:
  - slug: controller
    name: Controller
    reports_to: CFO
    people:
      - Jane Doe
"""

DERIVED_MARKER = "<!-- derived: gap-log; writer: python -->"


def fragment(title, callouts="", body_extra="", systems=("netsuite",),
             roles=("controller",)):
    meta_sys = "".join(f"  - {s}\n" for s in systems)
    meta_roles = "".join(f"  - {r}\n" for r in roles)
    return f"""## {title}

### A. Purpose & Scope

Reconcile all cash accounts against the bank statement.
{body_extra}

### B. Quick Reference

- **Frequency:** Monthly
- **Primary Owner:** Controller

### E. Step-by-Step Procedure

1. Export the bank statement from the portal.

{callouts}

```consult-meta
systems:
{meta_sys}roles:
{meta_roles}```
"""


GOOD_CALLOUTS = (
    "> **CONTROL — CTRL-001:** Controller reviews the reconciliation.\n\n"
    "> **VALIDATION REQUIRED — GAP-001:** Confirm the cutoff date.\n"
)


def make_area(tmp_path, fragments, derived_text=None, extra_components=(),
              roles_yaml=ROLES_YAML):
    """fragments: {slug: text}. Includes one gap-log derived file by default."""
    comps = []
    for i, slug in enumerate(fragments):
        comps.append({
            "file": f"{10 + 10 * i}_{slug}.md",
            "heading": slug.replace("-", " ").title(),
            "order": 10 + 10 * i,
            "role": "procedure", "slug": slug, "l2": "bank-ops",
        })
    comps.append({"file": "90_appendix-b-gaps.md",
                  "heading": "Appendix B — Gap Log", "order": 90,
                  "role": "derived", "derived_kind": "gap-log",
                  "writer": "python"})
    comps += list(extra_components)
    manifest = {
        "schema": "consult-mvp-manifest/v1",
        "area": "cash", "l1": "Cash Management",
        "title": "Cash Management Processes",
        "l2_order": ["bank-ops"],
        "components": comps,
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest),
                                            encoding="utf-8")
    for comp in comps:
        if comp["role"] == "procedure":
            (tmp_path / comp["file"]).write_text(
                fragments[comp["slug"]], encoding="utf-8")
    if derived_text is None:
        derived_text = (f"## Appendix B — Gap Log\n\n{DERIVED_MARKER}\n\n"
                        f"_No open validation gaps._\n")
    (tmp_path / "90_appendix-b-gaps.md").write_text(derived_text,
                                                    encoding="utf-8")
    ref = tmp_path / "_reference"
    ref.mkdir()
    (ref / "systems.yaml").write_text(SYSTEMS_YAML, encoding="utf-8")
    (ref / "roles.yaml").write_text(roles_yaml, encoding="utf-8")
    return tmp_path


def run(area, capsys):
    rc = reconcile.reconcile(str(area))
    return rc, capsys.readouterr().out


# --------------------------------------------------------------------------- #
# Clean pass + signal file
# --------------------------------------------------------------------------- #

def test_clean_area_exits_zero(tmp_path, capsys):
    """A valid area reconciles with exit 0 and 'No blocking errors'."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)})
    rc, out = run(area, capsys)
    assert rc == 0
    assert "No blocking errors" in out
    assert "WARNINGS" not in out


def test_signal_file_records_clean_flag(tmp_path, capsys):
    """.reconcile.json carries a basis hash and clean=True on a clean pass,
    clean=False when errors were found."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)})
    assert reconcile.reconcile(str(area)) == 0
    sig = json.loads((area / ".reconcile.json").read_text(encoding="utf-8"))
    assert sig["clean"] is True and sig["basis"]

    (area / "10_bank-rec.md").write_text(
        fragment("Bank Rec", "> **PAIN POINT — CTRL-001:** mismatch.\n"),
        encoding="utf-8")
    assert reconcile.reconcile(str(area)) == 1
    capsys.readouterr()
    sig = json.loads((area / ".reconcile.json").read_text(encoding="utf-8"))
    assert sig["clean"] is False


def test_missing_manifest_exits_two(tmp_path, capsys):
    """A folder with no manifest.json exits 2."""
    assert reconcile.reconcile(str(tmp_path)) == 2


# --------------------------------------------------------------------------- #
# ERROR checks (exit 1)
# --------------------------------------------------------------------------- #

def test_invalid_manifest_schema_is_error(tmp_path, capsys):
    """A manifest failing v1 validation is a blocking error."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec")})
    m = json.loads((area / "manifest.json").read_text(encoding="utf-8"))
    m["schema"] = "wrong/v0"
    (area / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
    rc, out = run(area, capsys)
    assert rc == 1
    assert "manifest.json" in out


def test_malformed_callout_id_is_error(tmp_path, capsys):
    """A known label with an ID failing the strict grammar is an ERROR."""
    frag = fragment("Bank Rec", "> **CONTROL — CTRL-0a1:** bad.\n")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 1
    assert "MALFORMED ID" in out


def test_prefix_label_mismatch_is_error(tmp_path, capsys):
    """A PAIN POINT callout carrying a CTRL- ID is an ERROR."""
    frag = fragment("Bank Rec", "> **PAIN POINT — CTRL-001:** mislabeled.\n")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 1
    assert "ID PREFIX MISMATCH" in out


def test_duplicate_callout_id_is_error(tmp_path, capsys):
    """The same local ID defined twice within one procedure is an ERROR."""
    frag = fragment("Bank Rec",
                    "> **CONTROL — CTRL-001:** one.\n\n"
                    "> **CONTROL — CTRL-001:** two.\n")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 1
    assert "DUPLICATE ID CTRL-001" in out


def test_bare_gap_tag_is_error(tmp_path, capsys):
    """[[GAP — reason]] with no numeric ID is an ERROR."""
    frag = fragment("Bank Rec",
                    body_extra="Pending [[GAP — confirm cutoff]].")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 1
    assert "BARE GAP TAG" in out


def test_dangling_local_id_reference_is_error(tmp_path, capsys):
    """An ID mentioned in prose but never defined in the SAME procedure is a
    per-fragment dangling ERROR."""
    frag = fragment("Bank Rec", body_extra="See CTRL-009 for the control.")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 1
    assert "DANGLING ID CTRL-009" in out


def test_dangling_slug_crossref_is_error(tmp_path, capsys):
    """A [[slug]] token naming no known procedure is an ERROR."""
    frag = fragment("Bank Rec", body_extra="Feeds into [[no-such-proc]].")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 1
    assert "DANGLING [[no-such-proc]]" in out


def test_valid_crossref_is_not_flagged(tmp_path, capsys):
    """[[slug]] tokens naming a real procedure reconcile clean."""
    frags = {"bank-rec": fragment("Bank Rec",
                                  body_extra="Feeds into [[petty-cash]]."),
             "petty-cash": fragment("Petty Cash")}
    rc, _ = run(make_area(tmp_path, frags), capsys)
    assert rc == 0


def test_derived_missing_marker_is_error(tmp_path, capsys):
    """A manifest derived file without its <!-- derived: --> marker is an ERROR."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec")},
                     derived_text="## Appendix B\n\nno marker here\n")
    rc, out = run(area, capsys)
    assert rc == 1
    assert "missing its" in out and "derived" in out


def test_derived_missing_file_is_error(tmp_path, capsys):
    """A manifest derived component with no file on disk is an ERROR."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec")})
    (area / "90_appendix-b-gaps.md").unlink()
    rc, out = run(area, capsys)
    assert rc == 1
    assert "missing on disk" in out


def test_derived_row_unknown_pair_is_error(tmp_path, capsys):
    """A derived-table row pairing an ID with a procedure that never defines
    it (neither local nor display ID) is an ERROR."""
    derived = (f"## Appendix B — Gap Log\n\n{DERIVED_MARKER}\n\n"
               "| Gap ID | Description |\n|---|---|\n"
               "| GAP-99 ([[#bank-rec]]) | bogus row |\n")
    area = make_area(tmp_path,
                     {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)},
                     derived_text=derived)
    rc, out = run(area, capsys)
    assert rc == 1
    assert "(bank-rec, GAP-99)" in out


def test_derived_row_display_id_pair_is_clean(tmp_path, capsys):
    """A derived row using the procedure's global display ID reconciles clean."""
    derived = (f"## Appendix B — Gap Log\n\n{DERIVED_MARKER}\n\n"
               "| Gap ID | Description |\n|---|---|\n"
               "| GAP-01 ([[#bank-rec]]) | Confirm the cutoff date. |\n")
    area = make_area(tmp_path,
                     {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)},
                     derived_text=derived)
    rc, _ = run(area, capsys)
    assert rc == 0


# --------------------------------------------------------------------------- #
# Named-individual checks
# --------------------------------------------------------------------------- #

def test_full_name_in_procedure_prose_is_error(tmp_path, capsys):
    """A known individual's full name (roles.yaml people:) in procedure prose
    is an ERROR."""
    frag = fragment("Bank Rec",
                    body_extra="Jane Doe signs off the reconciliation.")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 1
    assert "NAMED INDIVIDUAL 'Jane Doe'" in out


def test_standalone_name_token_is_warning_only(tmp_path, capsys):
    """A standalone first-name token warns (possible coincidence) but does not
    block: exit stays 0."""
    frag = fragment("Bank Rec", body_extra="Jane signs off the reconciliation.")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 0
    assert "possible named individual 'Jane'" in out


def test_static_front_matter_exempt_from_name_check(tmp_path, capsys):
    """role: static files may legitimately credit people by name — exempt."""
    static = {"file": "00_profile.md", "heading": "Document Profile",
              "order": 1, "role": "static"}
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec")},
                     extra_components=[static])
    (area / "00_profile.md").write_text(
        "Interviewees: Jane Doe (Controller).\n", encoding="utf-8")
    rc, out = run(area, capsys)
    assert rc == 0
    assert "NAMED INDIVIDUAL" not in out


def test_no_people_lists_means_name_check_noop(tmp_path, capsys):
    """With no people: lists anywhere, names in prose are not flagged."""
    frag = fragment("Bank Rec", body_extra="Jane Doe signs off.")
    area = make_area(tmp_path, {"bank-rec": frag},
                     roles_yaml="roles:\n  - slug: controller\n    name: Controller\n")
    rc, out = run(area, capsys)
    assert rc == 0


# --------------------------------------------------------------------------- #
# WARNING checks (exit stays 0)
# --------------------------------------------------------------------------- #

def test_unregistered_consult_meta_slug_is_warning(tmp_path, capsys):
    """A consult-meta slug absent from _reference/*.yaml warns without
    blocking, and (M28) the warning points at the fence's file:line."""
    frag = fragment("Bank Rec", systems=("mystery-tool",))
    fence_line = frag.splitlines().index("```consult-meta") + 1
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 0
    assert "WARNINGS" in out
    assert "'mystery-tool' not in" in out
    assert f"10_bank-rec.md:{fence_line}: consult-meta" in out


def test_merged_sections_is_warning_with_line(tmp_path, capsys):
    """M16.1 — two headings resolving to ONE section (`Pre-Requisites` +
    `Inputs` after the merge) warns, pointing at the second heading (the
    merge point), and never blocks: aggregate keeps every fact."""
    frag = fragment("Bank Rec", GOOD_CALLOUTS,
                    body_extra="\n### C. Pre-Requisites\n\nAccess to the "
                               "portal.\n\n### D. Inputs\n\nThe bank "
                               "statement.\n")
    line = frag.splitlines().index("### D. Inputs") + 1
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 0
    assert "headings resolve to the one `Before You Start` section" in out
    assert "AWAITING THE" in out
    assert f"10_bank-rec.md:{line}:" in out


# --------------------------------------------------------------------------- #
# M22.6 — quoted callout IDs in agent-owned derived prose
# --------------------------------------------------------------------------- #

AGENT_DERIVED = {"file": "80_deps.md", "heading": "Dependencies & Watch Items",
                 "order": 80, "role": "derived",
                 "derived_kind": "dependencies", "writer": "agent"}
AGENT_MARKER = "<!-- derived: dependencies; writer: agent -->"


def test_quoted_callout_id_in_agent_prose_is_error(tmp_path, capsys):
    """M22.6 — a callout ID quoted in agent-owned derived PROSE is an ERROR
    (render display-transforms ids only inside procedures)."""
    area = make_area(tmp_path,
                     {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)},
                     extra_components=[AGENT_DERIVED])
    (area / "80_deps.md").write_text(
        f"## Dependencies\n\n{AGENT_MARKER}\n\n"
        f"The control CTRL-001 covers the [[bank-rec]] handoff.\n",
        encoding="utf-8")
    rc, out = run(area, capsys)
    assert rc == 1
    assert "CALLOUT ID CTRL-001 in agent-owned prose" in out


def test_quoted_callout_id_in_table_row_is_exempt(tmp_path, capsys):
    """M22.6's table-row exemption: rows are the sanctioned ID carrier —
    they are validated as (slug, id) pairs by check_derived_tables instead."""
    area = make_area(tmp_path,
                     {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)},
                     extra_components=[AGENT_DERIVED])
    (area / "80_deps.md").write_text(
        f"## Dependencies\n\n{AGENT_MARKER}\n\n"
        "| ID | Depends on |\n|---|---|\n"
        "| CTRL-01 ([[#bank-rec]]) | the bank statement export |\n",
        encoding="utf-8")
    rc, out = run(area, capsys)
    assert rc == 0
    assert "CALLOUT ID" not in out


# --------------------------------------------------------------------------- #
# M28 — edge-case fixes + read-once cache
# --------------------------------------------------------------------------- #

def test_setext_h1_is_heading_contract_error(tmp_path, capsys):
    """M22.4 — a setext `Title` + `===` underline is the same H1 defect as an
    ATX `# ` line (it evaded the contract before M28)."""
    frag = fragment("Bank Rec", GOOD_CALLOUTS,
                    body_extra="\nBank Reconciliation\n===\n")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 1
    assert "H1 IN FRAGMENT" in out and "setext" in out


def test_bare_thematic_break_is_not_a_table_separator(tmp_path, capsys):
    """A bare `---` under a prose line containing '|' is a thematic break,
    not a table header separator — no SHEARED TABLE ROW false positive."""
    frag = fragment("Bank Rec", GOOD_CALLOUTS,
                    body_extra="\nEither portal A | portal B applies.\n"
                               "---\n"
                               "Later C | D | E may follow in prose.\n")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 0
    assert "SHEARED TABLE ROW" not in out


def test_each_fragment_read_and_blanked_once(tmp_path, capsys, monkeypatch):
    """M28's read-once property: one disk read and one fence-blanking pass
    per component file per reconcile() run (the pre-M28 gate re-read every
    fragment ~13 times)."""
    from pathlib import Path

    import callouts

    area = make_area(tmp_path,
                     {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS),
                      "petty-cash": fragment("Petty Cash", GOOD_CALLOUTS)})
    reads: dict = {}
    orig_read = Path.read_text

    def counting_read(self, *a, **kw):
        p = str(self)
        if p.endswith(".md"):
            reads[p] = reads.get(p, 0) + 1
        return orig_read(self, *a, **kw)

    blank_calls = []
    orig_blank = callouts.blank_fences

    def counting_blank(text):
        blank_calls.append(1)
        return orig_blank(text)

    monkeypatch.setattr(Path, "read_text", counting_read)
    monkeypatch.setattr(callouts, "blank_fences", counting_blank)
    monkeypatch.setattr(reconcile, "strip_fences", counting_blank)
    rc, _ = run(area, capsys)
    assert rc == 0
    # 2 fragments + 1 derived file: each read exactly once...
    assert reads and set(reads.values()) == {1}
    assert len(reads) == 3
    # ...and each fence-blanked exactly once.
    assert len(blank_calls) == 3


# --------------------------------------------------------------------------- #
# M29 check 2 — consult-meta PRESENCE (noun binding skipped)
# --------------------------------------------------------------------------- #

NO_META_FRAGMENT = """## Bank Rec

### A. Purpose & Scope

Reconcile all cash accounts against the bank statement.

### E. Step-by-Step Procedure

1. Export the bank statement from the portal.
"""


def test_drafted_fragment_without_consult_meta_is_error(tmp_path, capsys):
    """M29 — a drafted fragment (no sentinel) with NO consult-meta block
    silently skips noun binding: ERROR naming the file and the fix."""
    rc, out = run(make_area(tmp_path, {"bank-rec": NO_META_FRAGMENT}), capsys)
    assert rc == 1
    assert "10_bank-rec.md: NOUN BINDING SKIPPED" in out
    assert "add a" in out and "consult-meta" in out


def test_fragment_with_consult_meta_passes_presence_check(tmp_path, capsys):
    """Clean pass: the standard fixture carries a consult-meta block."""
    rc, out = run(make_area(tmp_path,
                            {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)}),
                  capsys)
    assert rc == 0
    assert "NOUN BINDING SKIPPED" not in out


def test_unfilled_skeleton_exempt_from_presence_check(tmp_path, capsys):
    """A scaffolded skeleton declares itself unfinished — routed to `fill`,
    not failed here (the documented sentinel exemption)."""
    skeleton = ("## Bank Rec\n\n<!-- unfilled -->\n\n### A. Purpose & Scope\n\n"
                "TBD — what this procedure accomplishes.\n")
    rc, out = run(make_area(tmp_path, {"bank-rec": skeleton}), capsys)
    assert rc == 0
    assert "NOUN BINDING SKIPPED" not in out


def test_presence_check_noops_without_a_noun_registry(tmp_path, capsys):
    """BOUNDARY (M22 pattern): with neither systems.yaml nor roles.yaml on
    disk there is no binding authority — the presence check no-ops."""
    area = make_area(tmp_path, {"bank-rec": NO_META_FRAGMENT})
    (area / "_reference" / "systems.yaml").unlink()
    (area / "_reference" / "roles.yaml").unlink()
    rc, out = run(area, capsys)
    assert rc == 0
    assert "NOUN BINDING SKIPPED" not in out


# --------------------------------------------------------------------------- #
# M29 check 3 — hard-wrap (long prose lines)
# --------------------------------------------------------------------------- #

LONG = "The reconciliation is performed against the statement " * 3  # >100


def test_long_prose_line_warns_once_with_count(tmp_path, capsys):
    """Two over-limit prose lines produce ONE warning: first line + 'and N
    more' (noise discipline), exit stays 0."""
    frag = fragment("Bank Rec", GOOD_CALLOUTS,
                    body_extra=f"\n{LONG}\n\nShort line.\n\n{LONG}\n")
    first = frag.splitlines().index(LONG) + 1
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 0
    assert out.count("LONG PROSE LINE") == 1
    assert f"10_bank-rec.md:{first}: LONG PROSE LINE" in out
    assert "(and 1 more)" in out
    assert "hard-wrap" in out


def test_hard_wrap_exemptions_do_not_warn(tmp_path, capsys):
    """Table rows, headings, callout `>` lines, URL lines, HTML comments and
    fenced-block bodies are exempt however long they run."""
    pad = "x" * 110
    frag = fragment("Bank Rec", GOOD_CALLOUTS, body_extra=(
        f"\n| Field | {pad} |\n"
        f"### Heading {pad}\n"
        f"> **CONTROL — CTRL-002:** {pad}\n"
        f"See https://example.com/{pad} for the portal.\n"
        f"<!-- note: {pad} -->\n"
        f"```\n{pad} {pad}\n```\n"))
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 0
    assert "LONG PROSE LINE" not in out


# --------------------------------------------------------------------------- #
# M29 check 4 — [[#slug]] outside a table row
# --------------------------------------------------------------------------- #

def test_number_only_xref_in_prose_warns_with_fix(tmp_path, capsys):
    """[[#slug]] in prose renders a cryptic bare number — WARNING naming the
    plain-token fix."""
    frag = fragment("Bank Rec", GOOD_CALLOUTS,
                    body_extra="Feeds [[#petty-cash]] downstream.")
    frags = {"bank-rec": frag,
             "petty-cash": fragment("Petty Cash", GOOD_CALLOUTS)}
    rc, out = run(make_area(tmp_path, frags), capsys)
    assert rc == 0
    assert "[[#petty-cash]] outside a table row" in out
    assert "use [[petty-cash]]" in out


def test_number_only_xref_in_table_row_is_sanctioned(tmp_path, capsys):
    """The Ref-cell home of the form: a `|` row never warns."""
    frag = fragment("Bank Rec", GOOD_CALLOUTS,
                    body_extra="\n| Ref | Title |\n|---|---|\n"
                               "| [[#petty-cash]] | Petty Cash |\n")
    frags = {"bank-rec": frag,
             "petty-cash": fragment("Petty Cash", GOOD_CALLOUTS)}
    rc, out = run(make_area(tmp_path, frags), capsys)
    assert rc == 0
    assert "outside a table row" not in out


def test_cross_area_number_only_token_is_not_double_reported(tmp_path, capsys):
    """[[#area/slug]] is already an M26 ERROR — check 4 skips it, so the one
    defect gets exactly one report."""
    import json as _json
    sib = tmp_path / "components" / "p2p"
    sib.mkdir(parents=True)
    (sib / "manifest.json").write_text(_json.dumps({
        "area": "p2p", "title": "P2P",
        "components": [{"file": "10_x.md", "role": "procedure",
                        "slug": "goods-receipt", "heading": "Goods Receipt"}],
    }), encoding="utf-8")
    (tmp_path / "components" / "cash").mkdir(parents=True)
    frag = fragment("Bank Rec", GOOD_CALLOUTS,
                    body_extra="Ref [[#p2p/goods-receipt]].")
    area = make_area(tmp_path / "components" / "cash", {"bank-rec": frag})
    rc, out = run(area, capsys)
    assert rc == 1
    assert "no display number" in out          # the M26 error
    assert "outside a table row" not in out    # not double-reported


# --------------------------------------------------------------------------- #
# v1.18 — required register fields (blank Reports To / description / Impact)
# --------------------------------------------------------------------------- #

def test_blank_register_fields_warn(tmp_path, capsys):
    """A role with no reports_to and a PAIN POINT with no Impact: are
    advisory WARNINGs — the register cell would ship blank."""
    roles = ("roles:\n"
             "  - slug: controller\n"
             "    name: Controller\n"
             "    people:\n"
             "      - Jane Doe\n")
    pp = ("> **PAIN POINT — PP-001:** Statements are rekeyed by hand.\n"
          "> - **Severity:** Medium\n")
    area = make_area(
        tmp_path,
        {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS + "\n" + pp)},
        roles_yaml=roles)
    rc, out = run(area, capsys)
    assert rc == 0                       # advisory, never blocking
    assert "'controller' has no reports_to" in out
    assert "PAIN POINT without `Impact:`" in out
    assert "without `Severity:`" not in out


def test_explicit_not_applicable_passes(tmp_path, capsys):
    """An explicit 'Not applicable' reports_to and a filled Impact are
    clean — unknown is the defect, not absence."""
    roles = ("roles:\n"
             "  - slug: controller\n"
             "    name: Controller\n"
             "    reports_to: Not applicable\n")
    pp = ("> **PAIN POINT — PP-001:** Statements are rekeyed by hand.\n"
          "> - **Impact:** Slow close and keying errors.\n"
          "> - **Severity:** Medium\n")
    area = make_area(
        tmp_path,
        {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS + "\n" + pp)},
        roles_yaml=roles)
    rc, out = run(area, capsys)
    assert "has no reports_to" not in out
    assert "PAIN POINT without" not in out
