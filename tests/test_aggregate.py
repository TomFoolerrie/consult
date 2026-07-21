"""Tests for scripts/aggregate.py — mechanical derived-view rebuilds,
registry-mismatch WARNINGs, fail-loud grammar ERRORs, and the .aggregate.json
signal file."""

import json

import aggregate


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
    responsibilities: Owns the monthly close
"""


def fragment(title, callouts="", systems=("netsuite",), roles=("controller",),
             body_extra=""):
    meta_sys = "".join(f"  - {s}\n" for s in systems)
    meta_roles = "".join(f"  - {r}\n" for r in roles)
    return f"""## {title}

### A. Purpose & Scope

Reconcile all cash accounts against the bank statement.
{body_extra}

### B. Quick Reference

- **Frequency:** Monthly
- **Primary Owner:** Controller
- **Preparer:** Senior Accountant
- **Reviewer:** Controller

### E. Step-by-Step Procedure

1. Export the bank statement from the portal.

{callouts}

```consult-meta
systems:
{meta_sys}roles:
{meta_roles}```
"""


DERIVED_COMPONENTS = [
    {"file": "06_procedure-index.md", "heading": "Procedure Index", "order": 6,
     "role": "derived", "derived_kind": "procedure-index", "writer": "python"},
    {"file": "07_role-dictionary.md", "heading": "Role Dictionary", "order": 7,
     "role": "derived", "derived_kind": "role-dictionary", "writer": "python"},
    {"file": "08_systems.md", "heading": "Systems", "order": 8,
     "role": "derived", "derived_kind": "systems", "writer": "python"},
    {"file": "82_dependencies.md", "heading": "Dependencies", "order": 82,
     "role": "derived", "derived_kind": "dependencies", "writer": "agent"},
    {"file": "88_appendix-a.md", "heading": "Appendix A", "order": 88,
     "role": "derived", "derived_kind": "appendix-a", "writer": "python"},
    {"file": "90_appendix-b-gaps.md", "heading": "Appendix B — Gap Log",
     "order": 90, "role": "derived", "derived_kind": "gap-log",
     "writer": "python"},
]


def make_area(tmp_path, fragments, extra_components=(), registries=True):
    """fragments: {slug: text}, order 10,20,... Returns the area folder."""
    comps = []
    for i, slug in enumerate(fragments):
        comps.append({
            "file": f"{10 + 10 * i}_{slug}.md",
            "heading": slug.replace("-", " ").title(),
            "order": 10 + 10 * i,
            "role": "procedure", "slug": slug, "l2": "bank-ops",
        })
    comps += list(DERIVED_COMPONENTS) + list(extra_components)
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
    if registries:
        ref = tmp_path / "_reference"
        ref.mkdir()
        (ref / "systems.yaml").write_text(SYSTEMS_YAML, encoding="utf-8")
        (ref / "roles.yaml").write_text(ROLES_YAML, encoding="utf-8")
    return tmp_path


GOOD_CALLOUTS = """\
> **CONTROL — CTRL-001:** Controller reviews and signs off the reconciliation.

> **PAIN POINT — PP-001:** Matching transactions is fully manual.
> - **Impact:** Two extra days per close
> - **Severity:** High

> **IMPROVEMENT OPPORTUNITY — IO-001:** Automate matching via bank rules.
> - **Addresses:** PP-001

> **VALIDATION REQUIRED — GAP-001:** Confirm the statement cutoff date.
> - **Nature:** Assumption
> - **Owner to confirm:** Controller

> **SCREENSHOT PLACEHOLDER — SC-001:** Bank reconciliation summary screen.
"""


# --------------------------------------------------------------------------- #
# Pure helpers
# --------------------------------------------------------------------------- #

def test_split_subsections_letters_and_boundaries():
    """split_subsections keys A–H bodies and a `## ` heading ends the run."""
    text = ("### A. Purpose\nalpha\n\n### B. Quick Reference\nbravo\n"
            "## Next Fragment\nignored\n### C. Systems\ncharlie\n")
    got = aggregate.split_subsections(text)
    assert got["A"] == "alpha"
    assert got["B"] == "bravo"
    assert got["C"] == "charlie"
    assert "ignored" not in got.get("B", "")


def test_parse_bullets_key_value():
    """parse_bullets turns `- **Label:** value` lines into a dict."""
    got = aggregate.parse_bullets(
        "- **Frequency:** Monthly\nplain line\n- **Owner:** Controller\n")
    assert got == {"Frequency": "Monthly", "Owner": "Controller"}


def test_parse_consult_meta_missing_block_is_empty():
    """A fragment with no consult-meta block yields empty slug lists."""
    assert aggregate.parse_consult_meta("## T\nbody\n") == {
        "systems": [], "roles": []}


def test_parse_callouts_subfields_and_wrapped_text():
    """Continuation `> ` lines extend the callout text and the current field."""
    text = ("> **PAIN POINT — PP-001:** First line\n"
            "> second line.\n"
            "> - **Impact:** big\n"
            ">   really big\n")
    (c,) = aggregate.parse_callouts("s", text)
    assert c["text"] == "First line second line."
    assert c["fields"]["Impact"] == "big really big"


# --------------------------------------------------------------------------- #
# run(): happy path
# --------------------------------------------------------------------------- #

def test_run_clean_area_builds_all_derived_views(tmp_path, capsys):
    """A valid area exits 0 and rebuilds every python-owned derived file with
    its `<!-- derived: KIND; writer: python -->` marker."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)})
    assert aggregate.run(str(area)) == 0
    for comp in DERIVED_COMPONENTS:
        if comp["writer"] != "python":
            continue
        text = (area / comp["file"]).read_text(encoding="utf-8")
        assert f"<!-- derived: {comp['derived_kind']}; writer: python -->" in text
        assert text.startswith(f"## {comp['heading']}\n")


def test_run_derived_rows_use_display_ids_and_tokens(tmp_path):
    """Appendix rows carry global display IDs and [[#slug]] procedure tokens."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)})
    assert aggregate.run(str(area)) == 0
    gaps = (area / "90_appendix-b-gaps.md").read_text(encoding="utf-8")
    assert "| GAP-01 ([[#bank-rec]]) |" in gaps
    appendix = (area / "88_appendix-a.md").read_text(encoding="utf-8")
    assert "PP-01 ([[#bank-rec]])" in appendix
    # IO's local `Addresses: PP-001` is translated to the display ID.
    assert "PP-001" not in appendix
    index = (area / "06_procedure-index.md").read_text(encoding="utf-8")
    assert "[[#bank-rec]]" in index and "Monthly" in index


def test_run_agent_placeholder_written_but_never_clobbered(tmp_path):
    """Agent-owned views get the pending placeholder when empty, and real
    agent content survives re-aggregation."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec")})
    assert aggregate.run(str(area)) == 0
    dep = area / "82_dependencies.md"
    assert aggregate.PENDING_PLACEHOLDER in dep.read_text(encoding="utf-8")
    dep.write_text("## Dependencies\n\n<!-- derived: dependencies; writer: agent -->\n\nReal synthesis.\n",
                   encoding="utf-8")
    assert aggregate.run(str(area)) == 0
    assert "Real synthesis." in dep.read_text(encoding="utf-8")


def test_run_is_idempotent(tmp_path):
    """Two runs with unchanged inputs produce byte-identical derived files."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec", GOOD_CALLOUTS)})
    assert aggregate.run(str(area)) == 0
    first = {c["file"]: (area / c["file"]).read_bytes()
             for c in DERIVED_COMPONENTS}
    assert aggregate.run(str(area)) == 0
    second = {c["file"]: (area / c["file"]).read_bytes()
              for c in DERIVED_COMPONENTS}
    assert first == second


def test_run_emits_extract_bundle_and_aggregate_signal(tmp_path):
    """run() writes <area>.extract.json (M5 inputs) and the .aggregate.json
    signal file recording warnings."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec")})
    assert aggregate.run(str(area)) == 0
    bundle = json.loads((area / "cash.extract.json").read_text(encoding="utf-8"))
    assert bundle["area"] == "cash"
    assert "bank-rec" in bundle["raw_dependencies"]
    assert bundle["raci_inputs"]["bank-rec"]["preparer"] == "Senior Accountant"
    signal = json.loads((area / ".aggregate.json").read_text(encoding="utf-8"))
    assert signal["warnings"] == []
    assert "bank-rec" in signal["proc_hashes"]  # keyed by procedure slug


# --------------------------------------------------------------------------- #
# run(): WARNINGs (exit stays 0)
# --------------------------------------------------------------------------- #

def test_run_unmatched_meta_slug_is_warning_not_error(tmp_path, capsys):
    """A consult-meta slug missing from the registry is a WARNING; the run
    still succeeds and the warning lands in .aggregate.json."""
    frag = fragment("Bank Rec", systems=("mystery-tool",))
    area = make_area(tmp_path, {"bank-rec": frag})
    assert aggregate.run(str(area)) == 0
    out = capsys.readouterr().out
    assert "WARNINGS" in out and "mystery-tool" in out
    signal = json.loads((area / ".aggregate.json").read_text(encoding="utf-8"))
    assert any("mystery-tool" in w for w in signal["warnings"])


def test_run_bad_severity_is_warning(tmp_path, capsys):
    """A PP severity outside {High|Medium|Low} warns but never fails."""
    frag = fragment("Bank Rec", (
        "> **PAIN POINT — PP-001:** Slow.\n> - **Severity:** Catastrophic\n"))
    area = make_area(tmp_path, {"bank-rec": frag})
    assert aggregate.run(str(area)) == 0
    assert "Catastrophic" in capsys.readouterr().out


# --------------------------------------------------------------------------- #
# run(): fail-loud ERRORs (exit 1, nothing written)
# --------------------------------------------------------------------------- #

def _assert_fails_loud(tmp_path, capsys, callouts, needle, extra=""):
    frag = fragment("Bank Rec", callouts, body_extra=extra)
    area = make_area(tmp_path, {"bank-rec": frag})
    assert aggregate.run(str(area)) == 1
    assert needle in capsys.readouterr().out
    # Fail-loud means nothing was written.
    assert not (area / "90_appendix-b-gaps.md").exists()
    assert not (area / "cash.extract.json").exists()


def test_run_malformed_callout_id_fails_loud(tmp_path, capsys):
    """A lowercase/invalid callout ID exits 1 with no derived output."""
    _assert_fails_loud(tmp_path, capsys,
                       "> **CONTROL — CTRL-0a1:** bad id.\n",
                       "malformed callout ID")


def test_run_unknown_label_fails_loud(tmp_path, capsys):
    """A callout label outside the LABEL→prefix map exits 1."""
    _assert_fails_loud(tmp_path, capsys,
                       "> **RANDOM NOTE — PP-001:** nope.\n",
                       "unknown callout label")


def test_run_prefix_label_mismatch_fails_loud(tmp_path, capsys):
    """A PAIN POINT carrying a CTRL- ID exits 1."""
    _assert_fails_loud(tmp_path, capsys,
                       "> **PAIN POINT — CTRL-001:** mislabeled.\n",
                       "prefix/label mismatch")


def test_run_duplicate_id_fails_loud(tmp_path, capsys):
    """The same local ID defined twice in one procedure exits 1."""
    _assert_fails_loud(
        tmp_path, capsys,
        "> **CONTROL — CTRL-001:** one.\n\n> **CONTROL — CTRL-001:** two.\n",
        "duplicate ID")


def test_run_bare_gap_tag_fails_loud(tmp_path, capsys):
    """A [[GAP — reason]] tag with no numeric ID exits 1."""
    _assert_fails_loud(tmp_path, capsys, "",
                       "bare gap tag",
                       extra="Pending [[GAP — confirm cutoff]] here.")


def test_run_undefined_body_gap_ref_fails_loud(tmp_path, capsys):
    """A body [[GAP-NN — ...]] tag with no matching callout exits 1."""
    _assert_fails_loud(tmp_path, capsys, "",
                       "referenced-but-undefined ID 'GAP-07'",
                       extra="Pending [[GAP-07 — confirm cutoff]] here.")


def test_run_missing_procedure_file_fails(tmp_path, capsys):
    """A manifest procedure whose file is absent exits 1."""
    area = make_area(tmp_path, {"bank-rec": fragment("Bank Rec")})
    (area / "10_bank-rec.md").unlink()
    assert aggregate.run(str(area)) == 1
    assert "missing procedure file" in capsys.readouterr().out


def test_run_bad_usage(tmp_path, capsys):
    """A non-directory argument exits 2."""
    assert aggregate.run(str(tmp_path / "nope")) == 2
