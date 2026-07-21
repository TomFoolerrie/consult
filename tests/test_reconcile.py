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
    blocking."""
    frag = fragment("Bank Rec", systems=("mystery-tool",))
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 0
    assert "WARNINGS" in out
    assert "'mystery-tool' not in" in out
