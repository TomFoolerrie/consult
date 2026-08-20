"""M63 gate — fail-loud edges: three silent drops become refusals or reports
(plus the render's discarded validate_manifest return).

Repros F-21, F-22, F-23 + the fact-check find.
docs/v2/M63-fail-loud-edges.md is the spec.
"""

import json
import shutil
from pathlib import Path

import pytest
from docx import Document
from docx.oxml.ns import qn

import aggregate
import doc_model
import render as render_mod
import review_apply
import split_doc

from test_review_apply import (BANK_REC, JOURNAL, MANIFEST, apply_run,
                               load_notes, track_replace)


# --------------------------------------------------------------------------- #
# Part A — split_doc preserves front matter
# --------------------------------------------------------------------------- #

IMPORT_MD = """\
# Payroll Process Documentation

_Working Draft_

This document describes the payroll cycle as observed in March. It was
prepared for the steering committee and is not a policy statement.

Scope note: hourly and salaried populations only; equity compensation is
covered by the stock administration SOP.

## Run Payroll

### A. Purpose

Payroll is run bi-weekly.
"""


class TestPartAFrontMatterPreserved:
    def test_both_paragraphs_reachable_in_split_output(self, tmp_path,
                                                       capsys):
        src = tmp_path / "legacy.md"
        src.write_text(IMPORT_MD, encoding="utf-8")
        out = tmp_path / "out"
        rc = split_doc.main([str(src), str(out), "--area", "payroll"])
        assert rc == 0
        # the import reports what it did with those lines
        assert "front matter" in capsys.readouterr().out
        blob = "\n".join(p.read_text(encoding="utf-8")
                         for p in out.glob("*.md"))
        assert "prepared for the steering committee" in blob
        assert "equity compensation is" in blob
        # …and the fragment is a manifest component, so it round-trips
        manifest = json.loads((out / "manifest.json").read_text(
            encoding="utf-8"))
        files = {c["file"] for c in manifest["components"]}
        assert "00_front-matter.md" in files

    def test_split_then_assemble_round_trips_the_lines(self, tmp_path,
                                                       capsys):
        src = tmp_path / "legacy.md"
        src.write_text(IMPORT_MD, encoding="utf-8")
        out = tmp_path / "out"
        split_doc.main([str(src), str(out), "--area", "payroll"])
        doc = doc_model.assemble(out)
        body = "\n".join(s.body for s in doc.sections)
        assert "steering committee" in body
        assert "stock administration SOP" in body

    def test_title_and_subtitle_only_writes_no_extra_fragment(self, tmp_path,
                                                              capsys):
        src = tmp_path / "legacy.md"
        src.write_text("# Title\n\n_Sub_\n\n## Proc\n\nBody.\n",
                       encoding="utf-8")
        out = tmp_path / "out"
        split_doc.main([str(src), str(out), "--area", "a"])
        assert not (out / "00_front-matter.md").exists()


# --------------------------------------------------------------------------- #
# Part B — per-anchor deletion warnings (the fixtures come from
# test_review_apply's rendered area)
# --------------------------------------------------------------------------- #

class TestPartBPerAnchorWarnings:
    def test_corrupted_bookmark_and_vanished_anchor_both_reported(
            self, tmp_path):
        # local copies of the module-scoped fixtures, without importing them
        area = tmp_path / "area"
        area.mkdir()
        (area / "manifest.json").write_text(json.dumps(MANIFEST),
                                            encoding="utf-8")
        (area / "bank-rec.md").write_text(BANK_REC, encoding="utf-8")
        (area / "journal-entries.md").write_text(JOURNAL, encoding="utf-8")
        render_mod.render_folder(area, area / "draft.docx", emit_signal=False)
        (area / "_review" / "returned").mkdir(parents=True)
        rv = area / "_review" / "returned" / "reviewed.docx"
        shutil.copy(area / "draft.docx", rv)

        d = Document(str(rv))
        # 1. corrupt one bookmark (the old guard's global silencer)
        p_el = track_replace(d, "monthly bank statement", "monthly", "weekly")
        for bm in p_el.iter(qn("w:bookmarkStart")):
            bm.set(qn("w:name"), "cw_99999")
        # 2. genuinely delete a DIFFERENT anchored paragraph, marks and all
        victim = None
        for p in d.paragraphs:
            if "journal entries" in p.text.lower() or "month end" in p.text:
                victim = p
                break
        assert victim is not None
        victim._p.getparent().remove(victim._p)
        d.save(str(rv))

        apply_run(area, rv)
        items = []
        for f in sorted((area / "_review").glob("*.notes.yaml")):
            items.extend(load_notes(area, f.name.replace(".notes.yaml", "")))
        types = {it.get("type") for it in items}
        assert "unknown-anchor" in types, (
            "the corrupted bookmark must be reported as its own defect")
        assert "untracked-deletion" in types, (
            "one corrupted bookmark must not silence the vanished-anchor "
            "warning (the old global guard)")


# --------------------------------------------------------------------------- #
# Parts C + D — aggregate and render run the rule validate_manifest owns
# --------------------------------------------------------------------------- #

def make_area(tmp_path, l2_order):
    area = tmp_path / "area"
    area.mkdir()
    manifest = {
        "schema": "consult-mvp-manifest/v1",
        "area": "ap", "l1": "finance", "title": "AP", "subtitle": "WD",
        "l2_order": l2_order,
        "components": [
            {"file": "10_pay.md", "heading": "Pay Run", "role": "procedure",
             "slug": "pay-run", "l2": "payments", "order": 10},
            {"file": "20_ghost.md", "heading": "Ghost", "role": "procedure",
             "slug": "ghost", "l2": "unfiled", "order": 20},
        ],
    }
    (area / "manifest.json").write_text(json.dumps(manifest),
                                        encoding="utf-8")
    (area / "10_pay.md").write_text(
        "## Pay Run\n\n### A. Purpose\n\nPay.\n", encoding="utf-8")
    (area / "20_ghost.md").write_text(
        "## Ghost\n\n### A. Purpose\n\nHaunt.\n", encoding="utf-8")
    return area


class TestPartCAggregateRefusesUnlistedL2:
    def test_unlisted_l2_fails_named(self, tmp_path, capsys):
        area = make_area(tmp_path, ["payments"])
        rc = aggregate.run(str(area))
        assert rc != 0
        out = capsys.readouterr().out
        assert "unfiled" in out and "l2_order" in out
        assert "20_ghost.md" in out or "ghost" in out

    def test_with_l2_listed_the_procedure_appears(self, tmp_path, capsys):
        area = make_area(tmp_path, ["payments", "unfiled"])
        rc = aggregate.run(str(area))
        assert rc == 0
        # the procedure index now carries the ghost procedure
        text = "\n".join(p.read_text(encoding="utf-8")
                         for p in area.glob("*.md"))
        assert "Ghost" in text


class TestPartDRenderValidatorHasTeeth:
    def test_manifest_defect_fails_the_render_with_the_error_text(
            self, tmp_path):
        area = make_area(tmp_path, ["payments"])
        with pytest.raises(SystemExit) as exc:
            render_mod.render_folder(area, area / "draft.docx",
                                     emit_signal=False)
        assert "unfiled" in str(exc.value)
        assert "l2_order" in str(exc.value)

    def test_clean_manifest_renders_as_before(self, tmp_path):
        area = make_area(tmp_path, ["payments", "unfiled"])
        render_mod.render_folder(area, area / "draft.docx", emit_signal=False)
        assert (area / "draft.docx").is_file()
