"""Tests for scripts/consolidate.py — the deterministic half of M12.

Acceptance list from docs/M12-consolidator.md: notes only (fragments
untouched), every finding cites >=2 procedures, dedupe on rerun, the
cross-bucket digest carries the step layer, mark records the draft basis and
the draft-ready gate surfaces it.
"""
import json
from pathlib import Path

import pytest
import yaml

import consolidate
import notes_util
import orchestrate


FRAG = """## {heading}

### Scope

{slug} covers its business. PRIMER-{slug}.

### At a Glance

| Field | Value |
|---|---|
| Preparer | AP Clerk |

### Procedure

#### Step 1: Do the first thing

First line of step one for {slug}.
Deep body line DEEP-{slug} that the digest must not carry.

#### Step 2: Do the second thing

> **VALIDATION REQUIRED — VAL-01:** callout first, prose after.

Prose line of step two for {slug}.

```consult-meta
systems: [netsuite]
roles: [ap-clerk]
```
"""


def make_area(tmp_path: Path) -> Path:
    area = tmp_path / "ap"
    (area / "_reference").mkdir(parents=True)
    (area / "_review").mkdir()
    manifest = {
        "schema": "consult-mvp-manifest/v1", "area": "ap", "l1": "finance",
        "title": "AP", "l2_order": ["invoices", "payments"],
        "components": [
            {"file": "10_bank-rec.md", "heading": "Bank Rec",
             "role": "procedure", "slug": "bank-rec", "l2": "invoices",
             "order": 10},
            {"file": "20_invoice-entry.md", "heading": "Invoice Entry",
             "role": "procedure", "slug": "invoice-entry", "l2": "invoices",
             "order": 20},
            {"file": "30_payment-run.md", "heading": "Payment Run",
             "role": "procedure", "slug": "payment-run", "l2": "payments",
             "order": 30},
        ],
    }
    (area / "manifest.json").write_text(json.dumps(manifest),
                                        encoding="utf-8")
    for slug, fname in (("bank-rec", "10_bank-rec.md"),
                        ("invoice-entry", "20_invoice-entry.md"),
                        ("payment-run", "30_payment-run.md")):
        (area / fname).write_text(
            FRAG.format(slug=slug, heading=slug.replace("-", " ").title()),
            encoding="utf-8")
    (area / "_reference" / "systems.yaml").write_text(yaml.safe_dump(
        {"systems": [{"slug": "netsuite", "name": "NetSuite"}]}),
        encoding="utf-8")
    (area / "_reference" / "roles.yaml").write_text(yaml.safe_dump(
        {"roles": [{"slug": "ap-clerk", "name": "AP Clerk"}]}),
        encoding="utf-8")
    return area


def snapshot(area: Path) -> dict[str, str]:
    return {str(p): (p.read_text(encoding="utf-8") if p.is_file() else "")
            for p in area.rglob("*")}


def test_plan_counts_buckets_and_cross(tmp_path, capsys):
    area = make_area(tmp_path)
    assert consolidate.main(["plan", str(area)]) == 0
    out = capsys.readouterr().out
    assert "2 L2 bucket(s) · 3 agent(s)" in out
    assert "bucket invoices" in out and "bucket payments" in out
    assert "cross-bucket" in out


def test_plan_single_bucket_skips_cross(tmp_path, capsys):
    area = make_area(tmp_path)
    m = json.loads((area / "manifest.json").read_text())
    for c in m["components"]:
        c["l2"] = "invoices"
    m["l2_order"] = ["invoices"]
    (area / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
    assert consolidate.main(["plan", str(area)]) == 0
    out = capsys.readouterr().out
    assert "1 agent(s)" in out and "no cross-bucket agent" in out
    assert "brief" in out and "--cross" not in out


def test_bucket_brief_lists_only_its_fragments(tmp_path, capsys):
    area = make_area(tmp_path)
    before = snapshot(area)
    assert consolidate.main(["brief", str(area), "--bucket", "payments"]) == 0
    out = capsys.readouterr().out
    assert snapshot(area) == before                      # read-only
    assert "30_payment-run.md" in out
    assert "10_bank-rec.md" not in out
    assert "seam + sequence" in out
    assert "note" in out and "--peers" in out


def test_unknown_bucket_exits_2_naming_known(tmp_path, capsys):
    area = make_area(tmp_path)
    with pytest.raises(SystemExit) as e:
        consolidate.main(["brief", str(area), "--bucket", "nope"])
    assert e.value.code == 2
    assert "invoices" in capsys.readouterr().err


def test_cross_brief_digest_is_bounded_and_tallies_bindings(tmp_path,
                                                            capsys):
    area = make_area(tmp_path)
    assert consolidate.main(["brief", str(area), "--cross"]) == 0
    out = capsys.readouterr().out
    # primer layer carried verbatim; step headings + FIRST body line only
    assert "PRIMER-bank-rec" in out
    assert "Step 1: Do the first thing" in out
    assert "First line of step one for bank-rec." in out
    assert "DEEP-bank-rec" not in out                    # depth excluded
    # a step opening with a callout digests its first PROSE line
    assert "Prose line of step two for bank-rec." in out
    assert "VALIDATION REQUIRED" not in out
    # mechanical majority basis, counted over consult-meta bindings
    assert "netsuite (canonical name: NetSuite): bound by 3" in out
    assert "Do NOT open the fragment files" in out


def test_note_writes_notes_only_and_dedupes(tmp_path, capsys):
    area = make_area(tmp_path)
    before = snapshot(area)
    args = ["note", str(area), "--slug", "bank-rec", "--category", "naming",
            "--note", "minority form", "--peers", "payment-run",
            "--anchor", "the AP aging report"]
    assert consolidate.main(args) == 0
    after = snapshot(area)
    notes = area / "_review" / "bank-rec.notes.yaml"
    changed = {p for p in set(before) ^ set(after)} | \
              {p for p in before if before.get(p) != after.get(p)}
    assert changed == {str(notes)}                       # notes ONLY
    items = notes_util.load_items(area, "bank-rec")
    assert items[0]["kind"] == "consolidation"
    assert items[0]["category"] == "naming"
    assert items[0]["peers"] == "payment-run"
    # rerun is a no-op (idempotent)
    assert consolidate.main(args) == 0
    assert "deduped" in capsys.readouterr().out
    assert len(notes_util.load_items(area, "bank-rec")) == 1


def test_single_procedure_nit_is_refused(tmp_path, capsys):
    area = make_area(tmp_path)
    with pytest.raises(SystemExit) as e:
        consolidate.main(["note", str(area), "--slug", "bank-rec",
                          "--category", "naming", "--note", "x",
                          "--peers", "bank-rec"])   # self only = no evidence
    assert e.value.code == 2
    assert ">=2 procedures" in capsys.readouterr().err
    assert not (area / "_review" / "bank-rec.notes.yaml").exists()


def test_category_outside_taxonomy_is_refused(tmp_path, capsys):
    area = make_area(tmp_path)
    with pytest.raises(SystemExit) as e:
        consolidate.main(["note", str(area), "--slug", "bank-rec",
                          "--category", "style", "--note", "x",
                          "--peers", "payment-run"])
    assert e.value.code == 2
    assert "out of bounds" in capsys.readouterr().err


def test_bus_enforces_consolidation_shape(tmp_path):
    # the evidence rule holds even for a producer bypassing the CLI
    with pytest.raises(notes_util.NotesError, match="peers"):
        notes_util.validate_item(
            {"kind": "consolidation", "category": "naming", "note": "x"})
    with pytest.raises(notes_util.NotesError, match="category"):
        notes_util.validate_item(
            {"kind": "consolidation", "peers": "a", "note": "x"})


def test_report_counts_by_category_and_headlines_dispatches(tmp_path,
                                                            capsys):
    area = make_area(tmp_path)
    for slug, cat in (("bank-rec", "naming"), ("bank-rec", "seam"),
                      ("payment-run", "duplication")):
        assert consolidate.main(
            ["note", str(area), "--slug", slug, "--category", cat,
             "--note", f"{cat} finding", "--peers", "invoice-entry"]) == 0
    capsys.readouterr()
    assert consolidate.main(["report", str(area)]) == 0
    out = capsys.readouterr().out
    assert "naming         1 finding(s)" in out
    assert "seam           1 finding(s)" in out
    assert "duplication    1 finding(s)" in out
    assert "3 finding(s) · 2 procedure(s) touched" in out
    assert "2 DRAFTER DISPATCH(ES)" in out               # per slug, not per finding
    assert "Delete any note you disagree with" in out


def test_mark_records_draft_basis_and_gate_surfaces_it(tmp_path, capsys):
    area = make_area(tmp_path)
    assert consolidate.main(["mark", str(area)]) == 0
    capsys.readouterr()
    data = json.loads((area / ".consolidate.json").read_text())
    st = orchestrate.AreaState(str(area))
    assert data["draft_basis"] == st.draft_basis()
    # walk the fixture to guard 8.5 the way the stage-gate tests do, and
    # check the gate's consolidate answer carries the recorded basis
    orchestrate.emit_aggregate(str(area), warnings=[])
    orchestrate.emit_reconcile(str(area), clean=True, failing_files=[])
    d = orchestrate.decide(str(area))
    assert d.get("action") == "draft_ready"
    ans = {a["name"]: a for a in d["details"]["answers"]}
    assert ans["consolidate"]["consolidated_at_basis"] == data["draft_basis"]
    assert ans["consolidate"]["consolidated_at_basis"] == \
        d["details"]["draft_basis"]                      # this draft: done
    assert "consolidate.py plan" in ans["consolidate"]["command"]
    # a fragment edit moves the basis: the mark reads as stale
    frag = area / "10_bank-rec.md"
    frag.write_text(frag.read_text() + "\nedit\n", encoding="utf-8")
    assert orchestrate.AreaState(str(area)).draft_basis() != \
        data["draft_basis"]


def test_mark_file_is_in_the_seeded_gitignore():
    assert ".consolidate.json" in orchestrate.AREA_GITIGNORE


def test_missing_manifest_exits_2(tmp_path, capsys):
    with pytest.raises(SystemExit) as e:
        consolidate.main(["plan", str(tmp_path)])
    assert e.value.code == 2
    assert "manifest.json" in capsys.readouterr().err
