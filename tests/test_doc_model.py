"""Tests for scripts/doc_model.py — manifest load/validate, display numbering,
callout display IDs, [[slug]] token resolution, and assemble()."""

import json

import pytest

import doc_model


# --------------------------------------------------------------------------- #
# Synthetic area factory
# --------------------------------------------------------------------------- #

def make_manifest(components, l2_order=("bank-ops", "reporting")):
    return {
        "schema": doc_model.SCHEMA_V1,
        "area": "cash",
        "l1": "Cash Management",
        "title": "Cash Management Processes",
        "subtitle": "FY26",
        "l2_order": list(l2_order),
        "components": components,
    }


def proc_comp(slug, order, l2="bank-ops", file=None, heading=None):
    return {
        "file": file or f"{order}_{slug}.md",
        "heading": heading or slug.replace("-", " ").title(),
        "order": order,
        "role": "procedure",
        "slug": slug,
        "l2": l2,
    }


FRAG_TEMPLATE = """## {title}

### A. Purpose & Scope

Reconcile all cash accounts to the bank statement.

### B. Quick Reference

- **Frequency:** Monthly
- **Primary Owner:** Controller

### E. Step-by-Step Procedure

1. Export the bank statement from the banking portal.

{callouts}

```consult-meta
systems:
  - netsuite
roles:
  - controller
```
"""


def write_area(tmp_path, manifest, fragments):
    """fragments: {file-name: text}. Returns the area folder."""
    (tmp_path / "manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8")
    for fname, text in fragments.items():
        (tmp_path / fname).write_text(text, encoding="utf-8")
    return tmp_path


# --------------------------------------------------------------------------- #
# load_manifest
# --------------------------------------------------------------------------- #

def test_load_manifest_from_folder(tmp_path):
    """load_manifest accepts an area folder and reads its manifest.json."""
    m = make_manifest([])
    write_area(tmp_path, m, {})
    assert doc_model.load_manifest(tmp_path)["area"] == "cash"


def test_load_manifest_from_file_path(tmp_path):
    """load_manifest also accepts the manifest.json file path itself."""
    write_area(tmp_path, make_manifest([]), {})
    assert doc_model.load_manifest(tmp_path / "manifest.json")["l1"] == "Cash Management"


def test_load_manifest_missing_raises(tmp_path):
    """A folder with no manifest.json raises ManifestError."""
    with pytest.raises(doc_model.ManifestError):
        doc_model.load_manifest(tmp_path)


def test_load_manifest_bad_json_raises(tmp_path):
    """Invalid JSON raises ManifestError, not a raw JSONDecodeError."""
    (tmp_path / "manifest.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(doc_model.ManifestError):
        doc_model.load_manifest(tmp_path)


# --------------------------------------------------------------------------- #
# validate_manifest
# --------------------------------------------------------------------------- #

def test_validate_manifest_clean():
    """A well-formed v1 manifest validates with zero errors."""
    m = make_manifest([proc_comp("bank-rec", 10)])
    assert doc_model.validate_manifest(m) == []


def test_validate_manifest_wrong_schema_and_missing_fields():
    """Wrong schema string and missing area/l1/title each produce an error."""
    errors = doc_model.validate_manifest(
        {"schema": "nope", "l2_order": [], "components": []})
    assert any("schema" in e for e in errors)
    for key in ("area", "l1", "title"):
        assert any(f'"{key}"' in e for e in errors)


def test_validate_manifest_duplicate_order_slug_file():
    """Duplicate order, slug, and file across components are each reported."""
    a = proc_comp("bank-rec", 10)
    b = proc_comp("bank-rec", 10, file=a["file"])
    errors = doc_model.validate_manifest(make_manifest([a, b]))
    assert any('duplicate "order" 10' in e for e in errors)
    assert any("duplicate procedure" in e for e in errors)
    assert any('duplicate "file"' in e for e in errors)


def test_validate_manifest_procedure_l2_not_in_order():
    """A procedure whose l2 bucket is absent from l2_order is an error."""
    errors = doc_model.validate_manifest(
        make_manifest([proc_comp("bank-rec", 10, l2="unknown-bucket")]))
    assert any("not in manifest l2_order" in e for e in errors)


def test_validate_manifest_derived_requires_kind_and_writer():
    """Derived components must carry derived_kind and a valid writer."""
    comp = {"file": "90_gaps.md", "heading": "Gaps", "order": 90, "role": "derived"}
    errors = doc_model.validate_manifest(make_manifest([comp]))
    assert any("derived_kind" in e for e in errors)
    assert any('"writer"' in e for e in errors)


def test_validate_manifest_not_a_dict():
    """A non-dict manifest returns a single explanatory error."""
    assert doc_model.validate_manifest([]) == ["manifest is not a JSON object"]


# --------------------------------------------------------------------------- #
# display_numbers
# --------------------------------------------------------------------------- #

def test_display_numbers_l2_ordinal_and_sequence():
    """Numbers are {l2-ordinal}.{1-based rank by manifest order within the L2}."""
    m = make_manifest([
        proc_comp("cash-forecast", 30, l2="reporting"),
        proc_comp("bank-rec", 20, l2="bank-ops"),
        proc_comp("petty-cash", 10, l2="bank-ops"),
    ])
    assert doc_model.display_numbers(m) == {
        "petty-cash": "1.1", "bank-rec": "1.2", "cash-forecast": "2.1"}


def test_display_numbers_skips_unknown_l2():
    """A procedure whose l2 is not in l2_order is silently skipped."""
    m = make_manifest([proc_comp("orphan", 10, l2="nowhere")])
    assert doc_model.display_numbers(m) == {}


# --------------------------------------------------------------------------- #
# callout_display_ids
# --------------------------------------------------------------------------- #

def test_callout_display_ids_global_per_prefix_counters(tmp_path):
    """Local IDs map to one global 2-digit counter per prefix, walked in
    manifest order (not component list position)."""
    p1 = proc_comp("bank-rec", 10)
    p2 = proc_comp("petty-cash", 20)
    m = make_manifest([p2, p1])  # list position deliberately reversed
    frag1 = FRAG_TEMPLATE.format(title="Bank Rec", callouts=(
        "> **PAIN POINT — PP-001:** Manual matching is slow.\n"
        "> - **Severity:** High\n\n"
        "> **VALIDATION REQUIRED — GAP-001:** Confirm cutoff date.\n"
    ))
    frag2 = FRAG_TEMPLATE.format(title="Petty Cash", callouts=(
        "> **PAIN POINT — PP-001:** Receipts go missing.\n"
    ))
    write_area(tmp_path, m, {p1["file"]: frag1, p2["file"]: frag2})
    ids = doc_model.callout_display_ids(tmp_path)
    assert ids == {
        ("bank-rec", "PP-001"): "PP-01",
        ("bank-rec", "GAP-001"): "GAP-01",
        ("petty-cash", "PP-001"): "PP-02",
    }


def test_callout_display_ids_ignores_fenced_examples(tmp_path):
    """Callouts inside fenced code blocks are not numbered."""
    p1 = proc_comp("bank-rec", 10)
    frag = FRAG_TEMPLATE.format(title="Bank Rec", callouts=(
        "```\n> **PAIN POINT — PP-001:** example only.\n```\n"
    ))
    write_area(tmp_path, make_manifest([p1]), {p1["file"]: frag})
    assert doc_model.callout_display_ids(tmp_path) == {}


# --------------------------------------------------------------------------- #
# resolve_tokens
# --------------------------------------------------------------------------- #

NUMBERS = {"bank-rec": {"number": "1.1", "title": "Bank Reconciliation"},
           "petty-cash": "1.2"}


def test_resolve_tokens_number_mode():
    """[[slug]] resolves to the display number in mode='number'."""
    assert doc_model.resolve_tokens("See [[bank-rec]].", NUMBERS) == "See 1.1."


def test_resolve_tokens_title_and_number_title_modes():
    """mode='title' yields the title; 'number+title' yields both."""
    assert doc_model.resolve_tokens(
        "[[bank-rec]]", NUMBERS, "title") == "Bank Reconciliation"
    assert doc_model.resolve_tokens(
        "[[bank-rec]]", NUMBERS, "number+title") == "1.1 Bank Reconciliation"


def test_resolve_tokens_hash_forces_number_only():
    """[[#slug]] is number-only regardless of mode."""
    assert doc_model.resolve_tokens(
        "[[#bank-rec]]", NUMBERS, "number+title") == "1.1"


def test_resolve_tokens_string_value_number_is_leading_token():
    """For a plain-string mapping value, [[#slug]] takes the leading token."""
    assert doc_model.resolve_tokens(
        "[[#petty-cash]]", {"petty-cash": "1.2 Petty Cash"}) == "1.2"


def test_resolve_tokens_leaves_gap_tags_untouched():
    """[[GAP-01 — reason]] body tags are not procedure cross-refs."""
    text = "Open item [[GAP-01 — confirm cutoff]] remains."
    assert doc_model.resolve_tokens(text, NUMBERS) == text


def test_resolve_tokens_unknown_slug_raises_keyerror():
    """A dangling [[slug]] raises KeyError (an ERROR upstream)."""
    with pytest.raises(KeyError):
        doc_model.resolve_tokens("[[missing-proc]]", NUMBERS)


def test_resolve_tokens_unknown_mode_raises():
    """An unsupported mode raises ValueError."""
    with pytest.raises(ValueError):
        doc_model.resolve_tokens("x", NUMBERS, mode="bogus")


def test_resolve_tokens_unterminated_token_passes_through():
    """An unterminated [[ token is left verbatim rather than crashing."""
    assert doc_model.resolve_tokens("see [[bank-rec", NUMBERS) == "see [[bank-rec"


# --------------------------------------------------------------------------- #
# assemble
# --------------------------------------------------------------------------- #

def test_assemble_orders_sections_and_attaches_numbers(tmp_path):
    """assemble() orders sections by manifest order and stamps procedure
    display numbers; bodies come back raw."""
    p1 = proc_comp("bank-rec", 20)
    p2 = proc_comp("petty-cash", 10)
    static = {"file": "00_intro.md", "heading": "Introduction",
              "order": 1, "role": "static"}
    m = make_manifest([p1, static, p2])
    frag = FRAG_TEMPLATE.format(title="Bank Rec", callouts="")
    write_area(tmp_path, m, {
        p1["file"]: frag, p2["file"]: frag, "00_intro.md": "Welcome.\n"})
    doc = doc_model.assemble(tmp_path)
    assert doc.title == "Cash Management Processes"
    assert doc.subtitle == "FY26"
    assert [s.heading for s in doc.sections] == [
        "Introduction", "Petty Cash", "Bank Rec"]
    procs = doc.procedures()
    assert [(s.slug, s.number) for s in procs] == [
        ("petty-cash", "1.1"), ("bank-rec", "1.2")]
    assert "consult-meta" in procs[0].body  # raw, not stripped


def test_assemble_missing_file_yields_empty_body(tmp_path):
    """A component whose file is absent assembles with an empty body."""
    p1 = proc_comp("bank-rec", 10)
    write_area(tmp_path, make_manifest([p1]), {})
    doc = doc_model.assemble(tmp_path)
    assert doc.sections[0].body == ""
