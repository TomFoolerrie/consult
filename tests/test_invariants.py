"""Tests for M22 — reconcile enforces the constitution (audit Part 3, F12–F18).

One seeded violation per check, plus the sanctioned form of the same sentence
where the ticket names one:

  1. SRC- citations resolve            (F13)  + the zero-citation rule
  2. `touches` ⊆ manifest slugs        (F14)  at sources.py LOAD and at the gate
  3. ownership markers match           (F12)
  4. the heading contract (`# `)       (F15)
  5. no baked display numbers          (F16)
  6. no callout ids in agent prose     (F17)

Also pinned: what the ticket deliberately does NOT check (citation truth,
coverage of every sentence, registry descriptions) and the two documented
boundaries (no manifest yet / no populated sources.yaml yet).
"""

import json

import pytest

import reconcile
import sources


SYSTEMS_YAML = "systems:\n  - slug: netsuite\n    name: NetSuite\n"
ROLES_YAML = "roles:\n  - slug: controller\n    name: Controller\n"

SOURCES_YAML = """\
sources:
- id: SRC-001
  file: _sources/new/interview.md
  touches:
  - bank-rec
  state: new
"""

DEP_MARKER = "<!-- derived: dependencies; writer: agent -->"
GAP_MARKER = "<!-- derived: gap-log; writer: python -->"


def fragment(body_extra="", citation="(SRC-001)", callouts=None):
    """A minimally-valid drafted procedure: real content, one citation, one
    CONTROL and one VALIDATION REQUIRED callout, consult-meta end matter."""
    if callouts is None:
        callouts = ("> **CONTROL — CTRL-001:** Controller reviews the rec.\n\n"
                    "> **VALIDATION REQUIRED — GAP-001:** Confirm the cutoff.\n")
    return f"""## Bank Rec

### A. Process Overview

The Controller reconciles cash accounts against the bank statement. {citation}
{body_extra}

### E. Step-by-Step Procedure

#### Step 1: Export the statement

Export the bank statement from the portal.

{callouts}

```consult-meta
systems: [netsuite]
roles:   [controller]
```
"""


DEP_CLEAN = f"""## Key Dependencies

{DEP_MARKER}

| Procedure | Upstream | Downstream |
|---|---|---|
| `[[bank-rec]]` | Bank statement feed | Month-end close |
"""


def make_area(tmp_path, fragments=None, dep_text=DEP_CLEAN,
              dep_kind="dependencies", dep_writer="agent",
              sources_yaml=SOURCES_YAML, with_manifest=True,
              with_dependencies=True):
    """A synthetic area: N procedures + (optionally) the agent-owned 82 view."""
    if fragments is None:
        fragments = {"bank-rec": fragment()}
    comps = [{
        "file": f"{10 + 10 * i}_{slug}.md",
        "heading": slug.replace("-", " ").title(),
        "order": 10 + 10 * i,
        "role": "procedure", "slug": slug, "l2": "bank-ops",
    } for i, slug in enumerate(fragments)]
    if with_dependencies:
        comps.append({"file": "82_dependencies.md", "heading": "Key Dependencies",
                      "order": 8200, "role": "derived",
                      "derived_kind": dep_kind, "writer": dep_writer})
    if with_manifest:
        manifest = {
            "schema": "consult-mvp-manifest/v1",
            "area": "cash", "l1": "Cash Management",
            "title": "Cash Management Processes",
            "l2_order": ["bank-ops"],
            "components": comps,
        }
        (tmp_path / "manifest.json").write_text(json.dumps(manifest),
                                                encoding="utf-8")
    for slug, text in fragments.items():
        comp = next(c for c in comps if c.get("slug") == slug)
        (tmp_path / comp["file"]).write_text(text, encoding="utf-8")
    if with_dependencies and dep_text is not None:
        (tmp_path / "82_dependencies.md").write_text(dep_text, encoding="utf-8")
    ref = tmp_path / "_reference"
    ref.mkdir()
    (ref / "systems.yaml").write_text(SYSTEMS_YAML, encoding="utf-8")
    (ref / "roles.yaml").write_text(ROLES_YAML, encoding="utf-8")
    if sources_yaml is not None:
        (ref / "sources.yaml").write_text(sources_yaml, encoding="utf-8")
    new = tmp_path / "_sources" / "new"
    new.mkdir(parents=True)
    (new / "interview.md").write_text("transcript\n", encoding="utf-8")
    return tmp_path


def run(area, capsys):
    rc = reconcile.reconcile(str(area))
    return rc, capsys.readouterr().out


def test_baseline_area_is_clean(tmp_path, capsys):
    """The fixture itself satisfies all six checks — so every failure below is
    caused by its seeded violation and nothing else."""
    rc, out = run(make_area(tmp_path), capsys)
    assert rc == 0, out
    assert "No blocking errors" in out
    assert "WARNINGS" not in out


# --------------------------------------------------------------------------- #
# 1. SRC- citations resolve (F13)
# --------------------------------------------------------------------------- #

def test_unregistered_src_citation_fails_naming_file_line_id(tmp_path, capsys):
    """`SRC-99` with no sources.yaml entry fails, naming file, line and id."""
    area = make_area(tmp_path, {"bank-rec": fragment(citation="(SRC-001, SRC-99)")})
    rc, out = run(area, capsys)
    assert rc == 1
    assert "UNREGISTERED CITATION SRC-99" in out
    assert "10_bank-rec.md:5:" in out


def test_zero_citation_procedure_fails(tmp_path, capsys):
    """A drafted procedure citing no SRC- id at all is untraceable text."""
    area = make_area(tmp_path, {"bank-rec": fragment(citation="")})
    rc, out = run(area, capsys)
    assert rc == 1
    assert "NO SOURCE CITATION" in out and "10_bank-rec.md" in out


def test_literal_id_match_is_required(tmp_path, capsys):
    """`SRC-1` does not satisfy a registry holding `SRC-001` — ids are compared
    as written, so a truncated citation is named rather than guessed."""
    area = make_area(tmp_path, {"bank-rec": fragment(citation="(SRC-1)")})
    rc, out = run(area, capsys)
    assert rc == 1
    assert "UNREGISTERED CITATION SRC-1" in out


def test_sentinel_skeleton_exempt_from_zero_citation(tmp_path, capsys):
    """An `<!-- unfilled -->` skeleton cites nothing BY CONSTRUCTION; it is
    routed to `fill`, not failed here (same documented exemption as M19)."""
    skeleton = ("## Bank Rec\n\n<!-- unfilled -->\n\n### A. Process Overview\n\n"
                "TBD — what this procedure accomplishes.\n")
    rc, out = run(make_area(tmp_path, {"bank-rec": skeleton}), capsys)
    assert rc == 0, out


def test_citation_check_skipped_loudly_without_a_registry(tmp_path, capsys):
    """BOUNDARY: with no populated sources.yaml there is nothing to validate
    against, so the check no-ops — but says so (WARNING, exit 0)."""
    area = make_area(tmp_path, sources_yaml=None)
    rc, out = run(area, capsys)
    assert rc == 0
    assert "WARNINGS" in out
    assert "citation check skipped" in out


def test_absorbed_review_text_needs_no_fake_citation(tmp_path, capsys):
    """Deliberately NOT checked: coverage. Sentences absorbed from review notes
    carry no SRC- vocabulary; check 1 validates only that cited ids exist."""
    extra = ("\n\nThe cutoff moved to the 3rd business day (per the reviewer's "
             "tracked change; no source id exists for reviewer-supplied facts).")
    area = make_area(tmp_path, {"bank-rec": fragment(body_extra=extra)})
    rc, out = run(area, capsys)
    assert rc == 0, out


# --------------------------------------------------------------------------- #
# 2. touches ⊆ manifest procedure slugs (F14) — at LOAD and at the GATE
# --------------------------------------------------------------------------- #

BAD_TOUCHES = SOURCES_YAML.replace("  - bank-rec\n", "  - bank-recon-typo\n")


def test_bad_touches_slug_fails_at_sources_load(tmp_path):
    """Fail loud at the source: _load_sources raises, naming id and slug."""
    area = make_area(tmp_path, sources_yaml=BAD_TOUCHES)
    with pytest.raises(sources.SourcesError) as exc:
        sources._load_sources(str(area))
    assert "SRC-001" in str(exc.value) and "bank-recon-typo" in str(exc.value)


def test_bad_touches_slug_fails_mark_processed_without_moving(tmp_path, capsys):
    """The CLI path exits nonzero and moves nothing (F14's livelock is the
    source that can never retire — it is named instead)."""
    area = make_area(tmp_path, sources_yaml=BAD_TOUCHES)
    rc = sources.main(["mark-processed", str(area), "--filled", "bank-rec"])
    assert rc == 1
    assert (area / "_sources" / "new" / "interview.md").is_file()
    assert not (area / "_sources" / "processed").exists()


def test_bad_touches_slug_fails_at_reconcile(tmp_path, capsys):
    """And again at the gate, with the identical message."""
    rc, out = run(make_area(tmp_path, sources_yaml=BAD_TOUCHES), capsys)
    assert rc == 1
    assert "_reference/sources.yaml" in out
    assert "bank-recon-typo" in out


def test_touches_check_noops_before_the_manifest_exists(tmp_path):
    """BOUNDARY: during initial scoping taxonomy writes sources.yaml BEFORE
    scaffold writes manifest.json. With no manifest there is no authority to
    validate against, so the check no-ops and mark-processed still works."""
    area = make_area(tmp_path, sources_yaml=BAD_TOUCHES, with_manifest=False,
                     with_dependencies=False)
    assert sources.touches_errors(str(area)) == []
    assert sources.mark_processed(str(area), {"bank-recon-typo"}) == 0
    assert (area / "_sources" / "processed" / "interview.md").is_file()


def test_touches_string_instead_of_list_is_named(tmp_path):
    """A scalar `touches:` is a schema defect, not a per-character iteration."""
    area = make_area(tmp_path, sources_yaml=SOURCES_YAML.replace(
        "  touches:\n  - bank-rec\n", "  touches: bank-rec\n"))
    errs = sources.touches_errors(str(area))
    assert errs and "must be a list" in errs[0]


# --------------------------------------------------------------------------- #
# 3. Ownership markers match the manifest (F12)
# --------------------------------------------------------------------------- #

def test_marker_writer_mismatch_is_error(tmp_path, capsys):
    """A python writer stamped on an agent-owned view — the detection layer for
    one-writer-per-file."""
    area = make_area(tmp_path, dep_text=DEP_CLEAN.replace(
        DEP_MARKER, "<!-- derived: dependencies; writer: python -->"))
    rc, out = run(area, capsys)
    assert rc == 1
    assert "OWNERSHIP MARKER MISMATCH" in out
    assert "82_dependencies.md" in out and "python" in out


def test_marker_kind_mismatch_is_error(tmp_path, capsys):
    """A marker claiming another section's kind (a drafter overwrote the file)."""
    area = make_area(tmp_path, dep_text=DEP_CLEAN.replace(
        DEP_MARKER, "<!-- derived: raci; writer: agent -->"))
    rc, out = run(area, capsys)
    assert rc == 1
    assert "OWNERSHIP MARKER MISMATCH" in out and "'raci'" in out


def test_unparseable_marker_is_error(tmp_path, capsys):
    """A marker present but not in the `kind; writer` grammar is an error, not a
    silent pass."""
    area = make_area(tmp_path, dep_text=DEP_CLEAN.replace(
        DEP_MARKER, "<!-- derived: dependencies -->"))
    rc, out = run(area, capsys)
    assert rc == 1
    assert "UNPARSEABLE OWNERSHIP MARKER" in out


def test_matching_marker_passes(tmp_path, capsys):
    """Whitespace and case in the marker are not the defect."""
    area = make_area(tmp_path, dep_text=DEP_CLEAN.replace(
        DEP_MARKER, "<!--  derived:  dependencies ;  writer:  Agent  -->"))
    rc, out = run(area, capsys)
    assert rc == 0, out


# --------------------------------------------------------------------------- #
# 4. The heading contract (F15)
# --------------------------------------------------------------------------- #

def test_h1_in_fragment_is_error(tmp_path, capsys):
    """"The one rule" now has a police officer: `# ` in a fragment fails."""
    area = make_area(tmp_path, {"bank-rec": "# Bank Rec\n" + fragment()})
    rc, out = run(area, capsys)
    assert rc == 1
    assert "H1 IN FRAGMENT" in out and "10_bank-rec.md:1:" in out


def test_h1_inside_a_fence_is_not_an_h1(tmp_path, capsys):
    """A `#` comment inside a fenced block is code, not a heading."""
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\n\n```bash\n# export the statement\nrun --export\n```")})
    rc, out = run(area, capsys)
    assert rc == 0, out


# --------------------------------------------------------------------------- #
# 5. No baked display numbers (F16)
# --------------------------------------------------------------------------- #

def test_baked_display_number_in_fragment_is_error(tmp_path, capsys):
    """`see 3.2` in prose fails — display numbers are render-time only."""
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\n\nThe cash sweep is documented in see 3.2 of this document.")})
    rc, out = run(area, capsys)
    assert rc == 1
    assert "BAKED DISPLAY NUMBER 'see 3.2'" in out


def test_same_sentence_with_slug_token_passes(tmp_path, capsys):
    """The sanctioned form of the identical sentence reconciles clean."""
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\n\nThe cash sweep is documented in [[bank-rec]].")})
    rc, out = run(area, capsys)
    assert rc == 0, out


def test_baked_number_in_agent_derived_prose_is_error(tmp_path, capsys):
    """Check 5 covers agent-derived prose too (82/84)."""
    area = make_area(tmp_path, dep_text=DEP_CLEAN.replace(
        "| Procedure |", "Ordering follows section 1.2.\n\n| Procedure |"))
    rc, out = run(area, capsys)
    assert rc == 1
    assert "BAKED DISPLAY NUMBER 'section 1.2'" in out


def test_pattern_stays_narrow(tmp_path, capsys):
    """Deliberately narrow: a bare decimal (a tolerance, a dollar amount, a
    version) is not a display-number reference."""
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\n\nVariances above 2.5 percent are escalated; the portal "
                   "runs release 4.11 and step 12 posts the entry.")})
    rc, out = run(area, capsys)
    assert rc == 0, out


def test_capitalized_section_reference_is_caught(tmp_path, capsys):
    """`Section 3.2` at a sentence start is the same defect (case-insensitive)."""
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\n\nSection 3.2 covers the sweep.")})
    rc, out = run(area, capsys)
    assert rc == 1
    assert "BAKED DISPLAY NUMBER" in out


# --------------------------------------------------------------------------- #
# 6. Callout ids stay out of agent-view prose (F17)
# --------------------------------------------------------------------------- #

def test_callout_id_in_agent_prose_is_error(tmp_path, capsys):
    """A GAP- id quoted in 82_dependencies.md prose fails: render rewrites ids
    only inside procedure sections, so the quoted id disagrees with the
    document's display numbering."""
    area = make_area(tmp_path, dep_text=DEP_CLEAN.replace(
        "| Procedure |",
        "The cutoff is unconfirmed (GAP-001).\n\n| Procedure |"))
    rc, out = run(area, capsys)
    assert rc == 1
    assert "CALLOUT ID GAP-001 in" in out and "82_dependencies.md" in out


def test_callout_id_in_a_derived_table_row_passes(tmp_path, capsys):
    """The same id in a derived-table row is the sanctioned carrier."""
    dep = (f"## Key Dependencies\n\n{DEP_MARKER}\n\n"
           "| Gap ID | Note | Procedure |\n|---|---|---|\n"
           "| GAP-01 | Confirm the cutoff. | `[[bank-rec]]` |\n")
    rc, out = run(make_area(tmp_path, dep_text=dep), capsys)
    assert rc == 0, out


def test_gap_tag_in_agent_prose_is_error(tmp_path, capsys):
    """A body gap tag is a quoted id too — agent views reference [[slug]] and
    describe the item in words."""
    area = make_area(tmp_path, dep_text=DEP_CLEAN.replace(
        "| Procedure |",
        "Blocked by [[GAP-001 — CUTOFF DATE]].\n\n| Procedure |"))
    rc, out = run(area, capsys)
    assert rc == 1
    assert "CALLOUT ID GAP-001" in out


def test_callout_id_in_python_derived_prose_is_not_this_check(tmp_path, capsys):
    """Scope: check 6 polices AGENT-owned views (82/84). Python-owned derived
    prose is machine-written and already display-transformed by aggregate."""
    area = make_area(tmp_path, dep_kind="gap-log", dep_writer="python",
                     dep_text=(f"## Appendix B — Gap Log\n\n{GAP_MARKER}\n\n"
                               "Open gaps: GAP-01 remains unconfirmed.\n"))
    rc, out = run(area, capsys)
    assert rc == 0, out


# --------------------------------------------------------------------------- #
# 14. hedge phrases in body prose (drafter contract: uncertainty in callouts)
# --------------------------------------------------------------------------- #

def test_hedge_phrase_in_body_prose_warns(tmp_path, capsys):
    """'TBD' in body prose is review debt that would ship in a final export —
    WARNING (exit 0), naming file, line and the phrase."""
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\nThe match tolerance is TBD - confirm with owner.\n")})
    rc, out = run(area, capsys)
    assert rc == 0
    assert "HEDGE IN PROSE" in out
    assert "'TBD'" in out and "10_bank-rec.md" in out


def test_hedge_inside_callout_is_not_flagged(tmp_path, capsys):
    """A GAP callout is exactly where uncertainty belongs — hedge words on
    `>` lines are the contract being followed, not broken."""
    area = make_area(tmp_path, {"bank-rec": fragment(callouts=(
        "> **CONTROL — CTRL-001:** Controller reviews the rec.\n\n"
        "> **VALIDATION REQUIRED — GAP-001:** Tolerance value unconfirmed —\n"
        "> confirm with process owner.\n"))})
    rc, out = run(area, capsys)
    assert rc == 0
    assert "HEDGE IN PROSE" not in out


# --------------------------------------------------------------------------- #
# 15. British spellings (drafter contract: American English, always)
# --------------------------------------------------------------------------- #

def test_british_spelling_warns_naming_word_and_line(tmp_path, capsys):
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\nThe run is authorised and synchronised nightly.\n")})
    rc, out = run(area, capsys)
    assert rc == 0
    assert "BRITISH SPELLING" in out and "'authorised'" in out


def test_shared_spellings_never_flag(tmp_path, capsys):
    """'analysis', 'analyst', 'advise', 'premise' are correct American
    English — the check is a word list, not a general -ise detector."""
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\nThe analyst documents the analysis on this premise "
                   "and can advise the Controller.\n")})
    rc, out = run(area, capsys)
    assert rc == 0
    assert "BRITISH SPELLING" not in out


# --------------------------------------------------------------------------- #
# 16. sheared table rows (bare '|' in cell text)
# --------------------------------------------------------------------------- #

def test_bare_pipe_in_table_cell_warns_as_sheared_row(tmp_path, capsys):
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\n| Field | Value |\n|---|---|\n"
                   "| System | SAP | S4 job schedule |\n")})
    rc, out = run(area, capsys)
    assert rc == 0
    assert "SHEARED TABLE ROW" in out and "1 more cell" in out


def test_escaped_pipe_and_short_rows_are_fine(tmp_path, capsys):
    """`\\|` is the sanctioned escape and a row with FEWER cells than the
    header is a writer choice — neither flags."""
    area = make_area(tmp_path, {"bank-rec": fragment(
        body_extra="\n| Field | Value |\n|---|---|\n"
                   "| System | SAP \\| S4 job schedule |\n"
                   "| Owner |\n")})
    rc, out = run(area, capsys)
    assert rc == 0
    assert "SHEARED TABLE ROW" not in out
