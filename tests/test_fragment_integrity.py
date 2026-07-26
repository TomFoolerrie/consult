"""Tests for M19 — fragment substance in reconcile.

A zero-byte or heading-only procedure fragment is a blocking error naming the
file (audit F2: the only finding that reaches the deliverable silently). A
fragment still carrying the `<!-- unfilled -->` sentinel is EXEMPT — it declares
itself unfinished and the advisor routes it to `fill`; M19 targets SILENT
emptiness. No length or verbosity check exists (M15's retirement stands).

Fixture convention follows tests/test_reconcile.py: synthetic areas under
tmp_path, observable contract = reconcile's exit code + printed report.
"""

import json

import reconcile


SYSTEMS_YAML = "systems:\n  - slug: netsuite\n    name: NetSuite\n"
ROLES_YAML = "roles:\n  - slug: controller\n    name: Controller\n"
SOURCES_YAML = """\
sources:
- id: SRC-001
  file: _sources/processed/interview.md
  touches:
  - bank-rec
  state: processed
"""

REAL_FRAGMENT = """## Bank Rec

### A. Process Overview

The Controller reconciles every cash account against the bank statement in
NetSuite. (SRC-001)

### E. Step-by-Step Procedure

#### Step 1: Export the bank statement

Export the statement from the banking portal.

```consult-meta
systems: [netsuite]
roles:   [controller]
```
"""

# The scaffolded skeleton: sentinel present, only TBD placeholders inside.
SKELETON = """## Bank Rec

<!-- unfilled -->

### A. Process Overview

TBD — what this procedure accomplishes.

```consult-meta
systems: []
roles:   []
```
"""

HEADING_ONLY = """## Bank Rec

### A. Process Overview

### E. Step-by-Step Procedure
"""


def make_area(tmp_path, fragments, with_sources=True):
    """fragments: {slug: text}. One procedure per slug, no derived files."""
    comps = [{
        "file": f"{10 + 10 * i}_{slug}.md",
        "heading": slug.replace("-", " ").title(),
        "order": 10 + 10 * i,
        "role": "procedure", "slug": slug, "l2": "bank-ops",
    } for i, slug in enumerate(fragments)]
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
        (tmp_path / comp["file"]).write_text(fragments[comp["slug"]],
                                            encoding="utf-8")
    ref = tmp_path / "_reference"
    ref.mkdir()
    (ref / "systems.yaml").write_text(SYSTEMS_YAML, encoding="utf-8")
    (ref / "roles.yaml").write_text(ROLES_YAML, encoding="utf-8")
    if with_sources:
        (ref / "sources.yaml").write_text(SOURCES_YAML, encoding="utf-8")
    return tmp_path


def run(area, capsys):
    rc = reconcile.reconcile(str(area))
    return rc, capsys.readouterr().out


# --------------------------------------------------------------------------- #
# The defect M19 exists for
# --------------------------------------------------------------------------- #

def test_zero_byte_fragment_is_error_naming_the_file(tmp_path, capsys):
    """A zero-byte procedure file is a blocking error naming the file."""
    rc, out = run(make_area(tmp_path, {"bank-rec": ""}), capsys)
    assert rc == 1
    assert "EMPTY FRAGMENT" in out
    assert "10_bank-rec.md" in out


def test_whitespace_only_fragment_is_error(tmp_path, capsys):
    """A file holding only whitespace is as empty as a zero-byte one."""
    rc, out = run(make_area(tmp_path, {"bank-rec": "\n\n   \n"}), capsys)
    assert rc == 1
    assert "EMPTY FRAGMENT" in out


def test_heading_only_fragment_is_error(tmp_path, capsys):
    """Headings with no content under them is a blocking error."""
    rc, out = run(make_area(tmp_path, {"bank-rec": HEADING_ONLY}), capsys)
    assert rc == 1
    assert "HEADING-ONLY FRAGMENT" in out
    assert "10_bank-rec.md" in out


def test_meta_block_only_fragment_is_error(tmp_path, capsys):
    """A fragment whose only non-heading content is its consult-meta end matter
    has not been written — fence bodies are not substance."""
    frag = ("## Bank Rec\n\n### A. Process Overview\n\n"
            "```consult-meta\nsystems: [netsuite]\nroles:   [controller]\n```\n")
    rc, out = run(make_area(tmp_path, {"bank-rec": frag}), capsys)
    assert rc == 1
    assert "HEADING-ONLY FRAGMENT" in out


def test_one_empty_fragment_among_good_ones_is_named(tmp_path, capsys):
    """The failure names the offending file, not the area."""
    area = make_area(tmp_path, {"bank-rec": REAL_FRAGMENT, "petty-cash": ""})
    rc, out = run(area, capsys)
    assert rc == 1
    assert "20_petty-cash.md: EMPTY FRAGMENT" in out
    assert "10_bank-rec.md: EMPTY" not in out


# --------------------------------------------------------------------------- #
# What must NOT fail
# --------------------------------------------------------------------------- #

def test_real_content_fragment_passes(tmp_path, capsys):
    """The normal drafted state — real content, no sentinel — reconciles clean."""
    rc, out = run(make_area(tmp_path, {"bank-rec": REAL_FRAGMENT}), capsys)
    assert rc == 0
    assert "No blocking errors" in out


def test_sentinel_skeleton_is_exempt(tmp_path, capsys):
    """A scaffolded skeleton carrying `<!-- unfilled -->` is exempt: it declares
    itself unfinished and the advisor routes it to `fill`. (Documented M19
    judgment call — the defect class is SILENT emptiness.)"""
    rc, out = run(make_area(tmp_path, {"bank-rec": SKELETON}), capsys)
    assert rc == 0
    assert "FRAGMENT" not in out


def test_sentinel_does_not_exempt_a_zero_byte_file(tmp_path, capsys):
    """The exemption is carried by the sentinel, and a zero-byte file cannot
    carry one — so an interrupted drafter is still caught."""
    rc, out = run(make_area(tmp_path, {"bank-rec": ""}), capsys)
    assert rc == 1
    assert "EMPTY FRAGMENT" in out


def test_no_length_check_is_introduced(tmp_path, capsys):
    """A terse but real fragment passes: M19 is 'did the writer finish', never
    'is this long enough' (M15's retirement stands)."""
    terse = ("## Bank Rec\n\n### A. Process Overview\n\n"
             "Controller reconciles cash daily. (SRC-001)\n")
    rc, out = run(make_area(tmp_path, {"bank-rec": terse}), capsys)
    assert rc == 0


def test_has_substance_unit(tmp_path):
    """has_substance() is the whole substance rule: headings, blank lines,
    HTML comments, rules and fence bodies are not content."""
    assert reconcile.has_substance("## T\n\nreal prose\n")
    assert not reconcile.has_substance("")
    assert not reconcile.has_substance("## T\n\n### A\n\n---\n")
    assert not reconcile.has_substance("## T\n\n<!-- a note -->\n")
    assert not reconcile.has_substance("## T\n\n```consult-meta\nsystems: []\n```\n")
