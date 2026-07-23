"""Tests for scripts/render.py and the bundled converter
skills/consult-docx-builder/scripts/cfgi_markdown_to_word.py.

All fixtures are synthetic areas built under tmp_path (see conftest.py).
`make_area` is also imported by test_kits.py so the two suites exercise the
same synthetic area shape.
"""
import base64
import json
import zipfile
from pathlib import Path

import pytest
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.oxml.ns import qn

import cfgi_markdown_to_word as cfgi
import render


# 1x1 transparent PNG.
PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ"
    "AAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)

MANIFEST = {
    "schema": "consult-mvp-manifest/v1",
    "area": "ap",
    "l1": "finance",
    "title": "Accounts Payable Process",
    "subtitle": "Current State Documentation",
    "l2_order": ["invoices", "payments"],
    "components": [
        {"file": "00_document-profile.md", "heading": "Document Profile",
         "role": "static", "order": 0},
        {"file": "10_vendor-onboarding.md", "heading": "Vendor Onboarding",
         "role": "procedure", "slug": "vendor-onboarding", "l2": "invoices",
         "order": 10},
        {"file": "20_payment-run.md", "heading": "Payment Run",
         "role": "procedure", "slug": "payment-run", "l2": "payments",
         "order": 20},
        {"file": "30_cash-application.md", "heading": "Cash Application",
         "role": "procedure", "slug": "cash-application", "l2": "payments",
         "order": 30},
        {"file": "90_appendix-b-gaps.md", "heading": "Appendix B - Gap Log",
         "role": "derived", "derived_kind": "gap-log", "writer": "python",
         "order": 90},
    ],
}

PROFILE_MD = """## Document Profile

| Field | Value |
|---|---|
| Client / Organization | Acme Corp |
| Version | v1.0 |
"""

VENDOR_MD = """## Vendor Onboarding

### A. Process Overview

New vendors are set up before the first invoice; see [[payment-run]].

### B. Quick Reference

- **Preparer:** AP Clerk
- **Reviewer:** Controller

### C. Pre-Requisites

- Approved vendor request form

### D. Inputs

- Vendor W-9

### E. Step-by-Step Procedure

#### Step 1 - Enter vendor

1. Open the vendor portal.
2. Enter the vendor master details.

> **VALIDATION REQUIRED - GAP-01:** Confirm the approval threshold amount.
> - **Nature:** Missing detail
> - **Owner to confirm:** AP Clerk

> **SCREENSHOT PLACEHOLDER - SC-01:** Vendor master entry screen.
> - **System:** SAP

The threshold is applied here [[GAP-01 - threshold unknown]].

#### Step 2 - Approve

1. Route the vendor for approval.
2. Confirm activation.

### F. Key Controls

> **CONTROL - CTRL-01:** Vendor changes require dual approval.
> - **Control type:** Preventive

### G. Outputs

- Active vendor master record

### H. Known Issues / Improvement Notes

- None noted.
"""

PAYMENT_MD = """## Payment Run

### A. Process Overview

Weekly payment run for approved invoices.

### B. Quick Reference

- **Preparer:** Controller

### E. Step-by-Step Procedure

#### Step 1 - Select invoices

1. Build the payment proposal.
2. Review exceptions.

> **VALIDATION REQUIRED - GAP-01:** Confirm the bank cut-off time.
> - **Nature:** Missing detail
> - **Owner to confirm:** AP Clerk

> **SCREENSHOT PLACEHOLDER - SC-01:** Payment proposal screen.

### G. Outputs

- Payment file
"""

CASH_MD = """## Cash Application

### A. Process Overview

Cash receipts are applied daily.

### B. Quick Reference

- **Preparer:** Mystery Person

### E. Step-by-Step Procedure

#### Step 1 - Apply cash

1. Match receipts to open invoices.
"""

GAPLOG_MD = """## Appendix B - Gap Log

<!-- derived: gap-log; writer: python -->

| Gap | Procedure |
|---|---|
| GAP-01 | [[#vendor-onboarding]] |
"""

ROLES_YAML = """roles:
  - slug: ap-clerk
    name: AP Clerk
    people:
      - Mark Manager
      - Jane Junior
  - slug: controller
    name: Controller
    people:
      - Carol Chief
"""

ORG_YAML = """people:
  - name: Carol Chief
    title: Controller
  - name: Mark Manager
    title: AP Manager
    reports_to: Carol Chief
  - name: Jane Junior
    title: AP Clerk
    reports_to: Mark Manager
"""


def make_area(tmp_path: Path) -> Path:
    """Build a complete synthetic area folder under tmp_path."""
    area = tmp_path / "ap"
    area.mkdir()
    (area / "manifest.json").write_text(json.dumps(MANIFEST, indent=1),
                                        encoding="utf-8")
    (area / "00_document-profile.md").write_text(PROFILE_MD, encoding="utf-8")
    (area / "10_vendor-onboarding.md").write_text(VENDOR_MD, encoding="utf-8")
    (area / "20_payment-run.md").write_text(PAYMENT_MD, encoding="utf-8")
    (area / "30_cash-application.md").write_text(CASH_MD, encoding="utf-8")
    (area / "90_appendix-b-gaps.md").write_text(GAPLOG_MD, encoding="utf-8")
    ref = area / "_reference"
    ref.mkdir()
    (ref / "roles.yaml").write_text(ROLES_YAML, encoding="utf-8")
    client = area / "_client"
    client.mkdir()
    (client / "org-chart.yaml").write_text(ORG_YAML, encoding="utf-8")
    return area


def doc_text(doc) -> str:
    parts = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                parts.append(c.text)
    return "\n".join(parts)


def bookmark_names(doc) -> list[str]:
    return [bm.get(qn("w:name")) or ""
            for bm in doc.element.body.iter(qn("w:bookmarkStart"))]


# --------------------------------------------------------------------------- #
# working mode
# --------------------------------------------------------------------------- #

def test_working_render_produces_docx_with_provenance(tmp_path):
    """Working mode writes the docx, per-paragraph cw_ bookmarks, and a
    _review/.maps sidecar keyed by the doc id stamped into core properties."""
    area = make_area(tmp_path)
    out = tmp_path / "draft.docx"
    stats = render.render_folder(area, out, emit_signal=False)
    assert out.is_file()
    doc = Document(str(out))
    cw = [n for n in bookmark_names(doc) if n.startswith("cw_")]
    assert cw, "working mode must stamp cw_ provenance bookmarks"
    map_path = Path(stats["map"])
    assert map_path.parent == area / "_review" / ".maps"
    payload = json.loads(map_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "consult-review-map/v1"
    assert payload["doc_id"] == stats["doc_id"]
    assert doc.core_properties.category == f"cw-map:{stats['doc_id']}"
    # every bookmark has a map entry pointing at a real fragment file
    assert set(cw) <= set(payload["entries"])
    files = {e["file"] for e in payload["entries"].values()}
    assert "10_vendor-onboarding.md" in files


def test_working_render_emits_signal_file(tmp_path):
    """Full working render (emit_signal=True) writes {area}/.render.json."""
    area = make_area(tmp_path)
    out = tmp_path / "draft.docx"
    render.render_folder(area, out, emit_signal=True)
    sig = json.loads((area / ".render.json").read_text(encoding="utf-8"))
    assert sig["docx"] == str(out)
    assert sig["awaiting_review"] is True


def test_no_signal_when_emit_signal_false(tmp_path):
    """emit_signal=False (programmatic/kit call) never writes .render.json."""
    area = make_area(tmp_path)
    render.render_folder(area, tmp_path / "d.docx", emit_signal=False)
    assert not (area / ".render.json").exists()


def test_working_render_shows_gaps_and_display_ids(tmp_path):
    """Working mode keeps VALIDATION REQUIRED callouts visible and rewrites
    procedure-local callout ids to global display ids (payment-run GAP-01 ->
    GAP-02)."""
    area = make_area(tmp_path)
    out = tmp_path / "draft.docx"
    render.render_folder(area, out, emit_signal=False)
    text = doc_text(Document(str(out)))
    assert "VALIDATION REQUIRED" in text
    assert "GAP-02" in text        # payment-run's local GAP-01, renumbered
    assert "SC-02" in text
    # cross-reference token resolved to number + title
    assert "2.1 Payment Run" in text
    # numbered procedure headings from the ONE display-number map
    assert any(p.text.startswith("1.1 Vendor Onboarding")
               for p in Document(str(out)).paragraphs)


# --------------------------------------------------------------------------- #
# final mode
# --------------------------------------------------------------------------- #

def test_final_mode_strips_gaps_and_reports_counts(tmp_path):
    """Final mode strips VR callouts, inline [[GAP-..]] tags, and the gap-log
    appendix; counts are reported and rendering never refuses."""
    area = make_area(tmp_path)
    out = tmp_path / "final.docx"
    stats = render.render_folder(area, out, mode="final", emit_signal=False)
    assert stats["gaps_stripped"] == 2
    assert stats["gap_tags_stripped"] == 1
    text = doc_text(Document(str(out)))
    assert "VALIDATION REQUIRED" not in text
    assert "[[GAP" not in text and "[GAP-" not in text
    assert "Gap Log" not in text                    # derived gap-log dropped
    assert "CTRL-01" in text                        # controls survive


def test_final_mode_placeholder_kept_when_no_image(tmp_path):
    """Final mode keeps the SCREENSHOT PLACEHOLDER callout when no captured
    image exists under _assets/screens/<slug>/."""
    area = make_area(tmp_path)
    out = tmp_path / "final.docx"
    stats = render.render_folder(area, out, mode="final", emit_signal=False)
    assert stats["screens_embedded"] == 0
    assert stats["screens_placeholder"] == 2
    assert "SCREENSHOT PLACEHOLDER" in doc_text(Document(str(out)))


def test_final_mode_embeds_captured_screenshot_with_caption(tmp_path):
    """Final mode swaps a placeholder for the image at
    _assets/screens/<slug>/<LOCAL-ID>.png, with an italic caption below."""
    area = make_area(tmp_path)
    shot = area / "_assets" / "screens" / "vendor-onboarding" / "SC-01.png"
    shot.parent.mkdir(parents=True)
    shot.write_bytes(PNG_1PX)
    out = tmp_path / "final.docx"
    stats = render.render_folder(area, out, mode="final", emit_signal=False)
    assert stats["screens_embedded"] == 1
    assert stats["screens_placeholder"] == 1     # payment-run's is still open
    doc = Document(str(out))
    assert len(doc.inline_shapes) == 1
    captions = [p for p in doc.paragraphs
                if "SC-01:" in p.text and "Vendor master entry screen" in p.text]
    assert captions and all(r.italic for r in captions[0].runs)


# --------------------------------------------------------------------------- #
# subset (--slugs) render
# --------------------------------------------------------------------------- #

def test_subset_unknown_slug_raises_systemexit(tmp_path):
    """--slugs with an unknown procedure slug exits with an error."""
    area = make_area(tmp_path)
    with pytest.raises(SystemExit, match="unknown procedure slug"):
        render.render_folder(area, tmp_path / "x.docx",
                             slugs=["nope"], emit_signal=False)


def test_subset_render_matches_full_numbering(tmp_path):
    """A kit subset render carries the FULL manifest's display numbers and
    global callout display ids, contains only the requested procedure, and
    never writes the .render.json signal."""
    area = make_area(tmp_path)
    out = tmp_path / "kit.docx"
    render.render_folder(area, out, slugs=["payment-run"], emit_signal=True)
    assert not (area / ".render.json").exists()
    text = doc_text(Document(str(out)))
    assert "2.1 Payment Run" in text     # not renumbered to 1.1
    assert "GAP-02" in text              # global display id, not local GAP-01
    assert "Vendor Onboarding" not in text
    assert "Document Profile" not in text    # no cover/front matter


# --------------------------------------------------------------------------- #
# converter: ordered-list numbering
# --------------------------------------------------------------------------- #

def _num_ids(doc):
    """[(paragraph, numId)] for List Number paragraphs, in document order."""
    out = []
    for p in doc.paragraphs:
        if p.style.name != "List Number":
            continue
        numPr = p._p.find(qn("w:pPr") + "/" + qn("w:numPr"))
        if numPr is None:
            pPr = p._p.find(qn("w:pPr"))
            numPr = pPr.find(qn("w:numPr")) if pPr is not None else None
        nid = numPr.find(qn("w:numId")) if numPr is not None else None
        out.append((p, nid.get(qn("w:val")) if nid is not None else None))
    return out


def test_two_ordered_lists_restart_numbering(tmp_path):
    """Two separate '1.'-starting lists get DIFFERENT numbering instances
    (shared within a list) and each <w:num> carries a startOverride, so the
    second list restarts at 1 instead of numbering continuously."""
    md = tmp_path / "lists.md"
    md.write_text(
        "## Section\n\nFirst list:\n\n1. alpha\n2. beta\n\n"
        "Interlude paragraph.\n\n1. gamma\n2. delta\n",
        encoding="utf-8")
    out = tmp_path / "lists.docx"
    cfgi.convert(md, out, include_toc=False, landscape=False, do_cover=False)
    doc = Document(str(out))
    nums = _num_ids(doc)
    assert [p.text for p, _ in nums] == ["alpha", "beta", "gamma", "delta"]
    ids = [nid for _, nid in nums]
    assert all(ids), "every ordered item must carry an explicit numId"
    assert ids[0] == ids[1], "items of one list share a numbering instance"
    assert ids[2] == ids[3]
    assert ids[0] != ids[2], "separate lists must NOT share a numId"
    # numbering part: each allocated <w:num> has an ilvl-0 startOverride
    numbering = doc.part.part_related_by(RT.NUMBERING).element
    by_id = {n.get(qn("w:numId")): n for n in numbering.findall(qn("w:num"))}
    for nid in {ids[0], ids[2]}:
        num = by_id[nid]
        so = num.find(qn("w:lvlOverride") + "/" + qn("w:startOverride"))
        if so is None:
            ov = num.find(qn("w:lvlOverride"))
            so = ov.find(qn("w:startOverride")) if ov is not None else None
        assert so is not None and so.get(qn("w:val")) == "1"


def test_repeated_one_idiom_is_one_continuous_list(tmp_path):
    """CommonMark semantics: a contiguous run numbered '1. / 1. / 1.' is ONE
    list (renders 1, 2, 3) — no per-item restart."""
    md = tmp_path / "ones.md"
    md.write_text("## S\n\n1. alpha\n1. beta\n1. gamma\n", encoding="utf-8")
    out = tmp_path / "ones.docx"
    cfgi.convert(md, out, include_toc=False, landscape=False, do_cover=False)
    nums = _num_ids(Document(str(out)))
    ids = [nid for _, nid in nums]
    assert len(ids) == 3 and len(set(ids)) == 1, \
        "contiguous ordered items must share one numbering instance"


def test_blank_separated_restart_seeds_literal_number(tmp_path):
    """An ordered item after a break restarts a fresh instance seeded with its
    own literal number, so displayed numbers always match the source."""
    md = tmp_path / "seed.md"
    md.write_text("## S\n\n1. alpha\n2. beta\n\n3. gamma\n", encoding="utf-8")
    out = tmp_path / "seed.docx"
    cfgi.convert(md, out, include_toc=False, landscape=False, do_cover=False)
    doc = Document(str(out))
    nums = _num_ids(doc)
    ids = [nid for _, nid in nums]
    assert ids[0] == ids[1] != ids[2]
    numbering = doc.part.part_related_by(RT.NUMBERING).element
    by_id = {n.get(qn("w:numId")): n for n in numbering.findall(qn("w:num"))}
    so = by_id[ids[2]].find(qn("w:lvlOverride") + "/" + qn("w:startOverride"))
    assert so is not None and so.get(qn("w:val")) == "3"


# --------------------------------------------------------------------------- #
# converter: tracked changes
# --------------------------------------------------------------------------- #

def test_enable_track_changes_schema_position_and_lock(tmp_path):
    """enable_track_changes puts <w:trackChanges/> at a schema-valid position
    (before any later-sequenced settings child) and adds
    <w:documentProtection w:edit="trackedChanges" w:enforcement="1"/>."""
    out = tmp_path / "tc.docx"
    cfgi.convert_assembled("## S\n\nBody paragraph.\n", out,
                           title="T", subtitle="", do_cover=False,
                           track_changes=True)
    doc = Document(str(out))
    settings = doc.settings.element
    names = [c.tag.rsplit("}", 1)[-1] for c in settings]
    assert "trackChanges" in names
    tc_i = names.index("trackChanges")
    # nothing sequenced AFTER trackChanges may appear before it
    assert not any(n in cfgi._SETTINGS_AFTER_TRACK_CHANGES
                   for n in names[:tc_i])
    dp = settings.find(qn("w:documentProtection"))
    assert dp is not None
    assert dp.get(qn("w:edit")) == "trackedChanges"
    assert dp.get(qn("w:enforcement")) == "1"
    assert names.index("documentProtection") > tc_i


def test_track_changes_survives_zip_roundtrip(tmp_path):
    """The trackChanges/documentProtection elements are actually persisted in
    the saved package's settings.xml."""
    out = tmp_path / "tc.docx"
    cfgi.convert_assembled("## S\n\nBody.\n", out, title="T", subtitle="",
                           do_cover=False, track_changes=True)
    with zipfile.ZipFile(out) as z:
        xml = z.read("word/settings.xml").decode("utf-8")
    assert "trackChanges" in xml and "documentProtection" in xml


# --------------------------------------------------------------------------- #
# CLI / input resolution
# --------------------------------------------------------------------------- #

def test_main_rejects_final_flags_for_single_file(tmp_path):
    """--mode/--slugs/--track-changes require an area folder, not a lone .md."""
    md = tmp_path / "one.md"
    md.write_text("# T\n\nBody.\n", encoding="utf-8")
    with pytest.raises(SystemExit, match="require an area folder"):
        render.main([str(md), "-o", str(tmp_path / "o.docx"),
                     "--mode", "final"])


def test_main_missing_input_errors(tmp_path):
    """A nonexistent input path exits with an error."""
    with pytest.raises(SystemExit, match="input not found"):
        render.main([str(tmp_path / "nowhere")])


def test_folder_without_manifest_rejected(tmp_path):
    """A directory lacking manifest.json is not a valid area."""
    d = tmp_path / "empty"
    d.mkdir()
    with pytest.raises(SystemExit, match="no manifest.json"):
        render.main([str(d)])
