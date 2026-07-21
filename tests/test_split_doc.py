"""Tests for scripts/split_doc.py — legacy single-file .md → folder split."""
import json

from split_doc import main, parse_front_matter, slugify, split_sections

DOC = """# Monthly Close SOP
*How the close actually runs.*

Intro prose that belongs to the front matter.

## Process Overview
Static human section.

## Run The Close
Step one.

```
## Not A Heading
```

## Reconcile Accounts
Step two.

## Index
<!-- derived: index; writer: python -->
generated
"""


def run_split(tmp_path, text=DOC, area="close"):
    src = tmp_path / "src.md"
    src.write_text(text, encoding="utf-8")
    out = tmp_path / "out"
    rc = main([str(src), str(out), "--area", area, "--l1", "finance"])
    assert rc == 0
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    return out, manifest


def test_slugify():
    """slugify kebab-cases, truncates, and falls back to 'section'."""
    assert slugify("Run The Close!") == "run-the-close"
    assert slugify("") == "section"
    assert len(slugify("x" * 100)) <= 60


def test_split_sections_fences_hide_h2():
    """split_sections ignores ## lines inside ``` and ~~~ fences."""
    lines = DOC.splitlines()
    headings = [h for h, _ in split_sections(lines)]
    assert headings == [None, "Process Overview", "Run The Close",
                        "Reconcile Accounts", "Index"]


def test_parse_front_matter():
    """Front matter yields the H1 title and first italic line as subtitle."""
    front = ["# Title Here", "*tagline*", "body"]
    assert parse_front_matter(front) == ("Title Here", "tagline")
    assert parse_front_matter(["# T", "no italic"]) == ("T", "")


def test_manifest_shape(tmp_path):
    """The manifest records schema, area/l1, title/subtitle, and components."""
    _, m = run_split(tmp_path)
    assert m["schema"] == "consult-mvp-manifest/v1"
    assert m["area"] == "close" and m["l1"] == "finance"
    assert m["title"] == "Monthly Close SOP"
    assert m["subtitle"] == "How the close actually runs."
    assert m["l2_order"] == ["imported"]
    assert len(m["components"]) == 4


def test_role_inference(tmp_path):
    """Pre-procedure static hints → static; derived marker → derived; else procedure."""
    _, m = run_split(tmp_path)
    roles = {c["heading"]: c["role"] for c in m["components"]}
    assert roles == {"Process Overview": "static",
                     "Run The Close": "procedure",
                     "Reconcile Accounts": "procedure",
                     "Index": "derived"}
    derived = next(c for c in m["components"] if c["role"] == "derived")
    assert derived["derived_kind"] == "index" and derived["writer"] == "python"


def test_procedures_get_slug_and_bucket(tmp_path):
    """Procedure components carry slug + catch-all l2 bucket 'imported'."""
    _, m = run_split(tmp_path)
    proc = next(c for c in m["components"] if c["heading"] == "Run The Close")
    assert proc["slug"] == "run-the-close" and proc["l2"] == "imported"


def test_band_filenames_and_content(tmp_path):
    """Files are {band}_{slug}.md: static 00, procedures 10, derived 80."""
    out, m = run_split(tmp_path)
    files = {c["heading"]: c["file"] for c in m["components"]}
    assert files["Process Overview"] == "00_process-overview.md"
    assert files["Run The Close"] == "10_run-the-close.md"
    assert files["Index"] == "80_index.md"
    body = (out / "10_run-the-close.md").read_text(encoding="utf-8")
    assert body.startswith("## Run The Close")
    assert "## Not A Heading" in body  # fenced pseudo-heading stays in body


def test_front_matter_not_duplicated(tmp_path):
    """The title/subtitle block is recorded in the manifest only, never a fragment."""
    out, _ = run_split(tmp_path)
    for f in out.glob("*.md"):
        assert "# Monthly Close SOP" not in f.read_text(encoding="utf-8")


def test_slug_collision_suffix(tmp_path):
    """Duplicate headings get deterministic -2/-3 slug suffixes and distinct files."""
    text = "# T\n\n## Do Work\na\n\n## Do Work\nb\n\n## Do Work\nc\n"
    out, m = run_split(tmp_path, text=text)
    slugs = [c["slug"] for c in m["components"]]
    assert slugs == ["do-work", "do-work-2", "do-work-3"]
    assert len(list(out.glob("*.md"))) == 3


def test_static_hint_after_procedure_is_procedure(tmp_path):
    """A static-hinted heading after the first procedure is still a procedure."""
    text = "# T\n\n## Run Steps\nx\n\n## Overview\ny\n"
    _, m = run_split(tmp_path, text=text)
    roles = {c["heading"]: c["role"] for c in m["components"]}
    assert roles == {"Run Steps": "procedure", "Overview": "procedure"}


def test_order_increments_by_ten(tmp_path):
    """Component order values run 10, 20, 30, ... in document order."""
    _, m = run_split(tmp_path)
    assert [c["order"] for c in m["components"]] == [10, 20, 30, 40]


def test_no_headings_doc(tmp_path):
    """A doc with no ## produces an empty components list but a valid manifest."""
    _, m = run_split(tmp_path, text="# Only Title\n*sub*\nprose\n")
    assert m["components"] == []
    assert m["title"] == "Only Title" and m["subtitle"] == "sub"
