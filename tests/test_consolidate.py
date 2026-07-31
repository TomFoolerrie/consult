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


def _man(sizes: list[int]) -> dict:
    """A synthetic manifest with one bucket per size entry (bN, sN.M slugs)."""
    comps, order = [], []
    for i, n in enumerate(sizes):
        order.append(f"b{i}")
        for j in range(n):
            comps.append({"role": "procedure", "slug": f"s{i}.{j}",
                          "file": f"10_s{i}{j}.md", "heading": f"S{i}{j}",
                          "l2": f"b{i}", "order": len(comps) * 10})
    return {"l2_order": order, "components": comps}


def test_groups_pack_consecutive_buckets_under_budget():
    # [3,3,2,4,3] at budget 5: 3 | 3+2 | 4 | 3 — adjacency preserved,
    # buckets never split, greedy (not optimal bin-packing) by design
    assert consolidate._groups(_man([3, 3, 2, 4, 3])) == \
        [["b0"], ["b1", "b2"], ["b3"], ["b4"]]
    # an oversized bucket rides alone, over budget
    assert consolidate._groups(_man([7, 2])) == [["b0"], ["b1"]]
    # everything fits in one group
    assert consolidate._groups(_man([1, 2, 1, 1])) == \
        [["b0", "b1", "b2", "b3"]]


def test_one_fragment_groups_fold_into_a_neighbor():
    # [5,1]: the trailing singleton would be a structurally-useless agent
    # (the run-4 waste) — folded into the previous group, over budget
    assert consolidate._groups(_man([5, 1])) == [["b0", "b1"]]
    # [1,5]: a LEADING singleton folds forward
    assert consolidate._groups(_man([1, 5])) == [["b0", "b1"]]


def test_plan_dispatches_groups_and_cross(tmp_path, capsys):
    area = make_area(tmp_path)   # invoices(2) + payments(1) = one group of 3
    assert consolidate.main(["plan", str(area)]) == 0
    out = capsys.readouterr().out
    assert "2 L2 bucket(s) · 1 bucket group(s)" in out
    assert "1 agent(s)" in out
    assert "bucket group [invoices, payments]" in out
    assert "--bucket invoices,payments" in out
    # single group covers the area → no cross agent
    assert "no cross-bucket agent" in out and "--cross" not in out


def test_plan_keeps_cross_when_groups_split(tmp_path, capsys):
    area = make_area(tmp_path)
    m = json.loads((area / "manifest.json").read_text())
    # grow invoices to 4 so invoices(4)+payments(1)>5 — but the payments
    # singleton folds back in, so force a real split with 4+2
    for extra in ("x1", "x2"):
        m["components"].append(
            {"file": f"40_{extra}.md", "heading": extra, "role": "procedure",
             "slug": extra, "l2": "invoices", "order": 40})
    m["components"].append(
        {"file": "50_pay2.md", "heading": "Pay2", "role": "procedure",
         "slug": "pay2", "l2": "payments", "order": 50})
    (area / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
    for f in ("40_x1.md", "40_x2.md", "50_pay2.md"):
        (area / f).write_text("## X\n\n### Scope\n\nx\n", encoding="utf-8")
    assert consolidate.main(["plan", str(area)]) == 0
    out = capsys.readouterr().out
    assert "2 bucket group(s)" in out and "3 agent(s)" in out
    assert "cross-bucket" in out and "--cross" in out


def test_group_brief_lists_its_buckets_and_flags_between_seams(tmp_path,
                                                               capsys):
    area = make_area(tmp_path)
    before = snapshot(area)
    assert consolidate.main(["brief", str(area), "--bucket",
                             "invoices,payments"]) == 0
    out = capsys.readouterr().out
    assert snapshot(area) == before                      # read-only
    assert "10_bank-rec.md" in out and "30_payment-run.md" in out
    assert "l2: invoices" in out and "l2: payments" in out
    # full-area group carries the cross lens + the mechanical tally
    assert "covers the whole area" in out
    assert "NAMING TALLY" in out
    assert "netsuite (canonical name: NetSuite): bound by 3" in out
    assert "note" in out and "--peers" in out


def test_partial_group_brief_has_no_tally(tmp_path, capsys):
    area = make_area(tmp_path)
    before = snapshot(area)
    assert consolidate.main(["brief", str(area), "--bucket", "payments"]) == 0
    out = capsys.readouterr().out
    assert snapshot(area) == before                      # read-only
    assert "30_payment-run.md" in out
    assert "10_bank-rec.md" not in out
    assert "seam + sequence" in out
    assert "NAMING TALLY" not in out                     # cross agent's job
    assert "note" in out and "--peers" in out


def test_unknown_bucket_exits_2_naming_known(tmp_path, capsys):
    area = make_area(tmp_path)
    with pytest.raises(SystemExit) as e:
        consolidate.main(["brief", str(area), "--bucket", "nope,invoices"])
    assert e.value.code == 2
    err = capsys.readouterr().err
    assert "nope" in err and "invoices" in err


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


# --------------------------------------------------------------------------- #
# M12/A2 — gap-answer + engagement registers in the briefs
# --------------------------------------------------------------------------- #

def test_gap_answer_is_a_valid_category(tmp_path, capsys):
    area = make_area(tmp_path)
    assert consolidate.main(
        ["note", str(area), "--slug", "bank-rec", "--category",
         "gap-answer", "--note",
         "GAP-01 appears answered in [[payment-run]], sourced to SRC-004",
         "--peers", "payment-run"]) == 0
    items = notes_util.load_items(area, "bank-rec")
    assert items[0]["category"] == "gap-answer"


def test_cross_digest_carries_the_open_gap_register(tmp_path, capsys):
    area = make_area(tmp_path)
    frag = area / "10_bank-rec.md"
    frag.write_text(frag.read_text(encoding="utf-8").replace(
        "#### Step 2: Do the second thing\n",
        "#### Step 2: Do the second thing\n\n"
        "> **VALIDATION REQUIRED — GAP-01:** How the goods receipt posts\n"
        "> to the sub-ledger is unconfirmed.\n"), encoding="utf-8")
    assert consolidate.main(["brief", str(area), "--cross"]) == 0
    out = capsys.readouterr().out
    # the digest skips `>` lines, so the gap register must carry it —
    # wrapped callout text joined, flagged as gap-answer material
    assert "open gaps" in out
    assert ("GAP-01 — How the goods receipt posts to the sub-ledger is "
            "unconfirmed.") in out
    assert "gap-answer" in out


def test_group_brief_lists_engagement_registers(tmp_path, capsys):
    root = tmp_path / "components"
    area = make_area(root)
    regs = root / "_client" / "registers"
    regs.mkdir(parents=True)
    (regs / "accounting-dates.md").write_text("| txn | date |\n",
                                              encoding="utf-8")
    assert consolidate.main(["brief", str(area), "--bucket", "payments"]) == 0
    out = capsys.readouterr().out
    assert "accounting-dates.md" in out
    assert "ENGAGEMENT REGISTER" in out


# --------------------------------------------------------------------------- #
# CROSS-AREA SEAMS in the group brief (M26/M12-A3 item 1)
# --------------------------------------------------------------------------- #

P2P_FRAG = """## Goods Receipt

### Scope

Receipt of goods at the dock against the open PO.
The receipt log is the artifact handed downstream.
{back}
### Procedure

#### Step 1: Receive

Match the delivery to the PO.
"""


def make_seam_engagement(tmp_path: Path, back_ref=True) -> Path:
    """components/{ap,p2p}: the make_area fixture as `ap`, plus a `p2p`
    sibling; ap/bank-rec holds a [[p2p/goods-receipt]] token."""
    root = tmp_path / "components"
    area = make_area(root)
    frag = area / "10_bank-rec.md"
    frag.write_text(frag.read_text(encoding="utf-8")
                    + "\nFeeds from [[p2p/goods-receipt]] daily.\n",
                    encoding="utf-8")
    p2p = root / "p2p"
    p2p.mkdir()
    (p2p / "manifest.json").write_text(json.dumps({
        "schema": "consult-mvp-manifest/v1", "area": "p2p", "l1": "finance",
        "title": "Procure to Pay", "l2_order": ["ops"],
        "components": [{"file": "10_goods-receipt.md", "role": "procedure",
                        "slug": "goods-receipt", "heading": "Goods Receipt",
                        "l2": "ops", "order": 10}]}), encoding="utf-8")
    back = ("Hands the receipt log to [[ap/bank-rec]] for matching.\n\n"
            if back_ref else "")
    (p2p / "10_goods-receipt.md").write_text(P2P_FRAG.format(back=back),
                                             encoding="utf-8")
    return area


def test_group_brief_seam_block_carries_the_back_reference(tmp_path, capsys):
    area = make_seam_engagement(tmp_path, back_ref=True)
    assert consolidate.main(["brief", str(area), "--bucket", "invoices"]) == 0
    out = capsys.readouterr().out
    assert "CROSS-AREA SEAMS (M26/M12-A3)" in out
    assert "[[p2p/goods-receipt]] (in [[bank-rec]])" in out
    assert "Goods Receipt (Procure to Pay, area p2p)" in out
    # the counterpart's back-reference line, verbatim and quoted
    assert ("> Hands the receipt log to [[ap/bank-rec]] for matching."
            in out)
    # the instruction: mismatch = seam finding on the LOCAL side
    assert "ordinary `seam` finding on YOUR side's procedure" in out
    assert "seam_unverified_counterpart" in out


def test_group_brief_seam_block_falls_back_to_scope_lines(tmp_path, capsys):
    area = make_seam_engagement(tmp_path, back_ref=False)
    assert consolidate.main(["brief", str(area), "--bucket", "invoices"]) == 0
    out = capsys.readouterr().out
    assert "no back-reference to this area found" in out
    assert "> Receipt of goods at the dock against the open PO." in out
    assert "> The receipt log is the artifact handed downstream." in out
    # first 2 non-empty Scope lines only — the step body never rides along
    assert "Match the delivery to the PO." not in out


def test_group_brief_seam_block_absent_without_cross_tokens(tmp_path,
                                                            capsys):
    area = make_seam_engagement(tmp_path)
    # payments bucket (payment-run) holds no cross token — block absent
    assert consolidate.main(["brief", str(area), "--bucket", "payments"]) == 0
    assert "CROSS-AREA SEAMS" not in capsys.readouterr().out


def test_group_brief_seam_block_absent_outside_components_root(tmp_path,
                                                               capsys):
    area = make_area(tmp_path)   # tmp_path/ap — NOT under components/
    frag = area / "10_bank-rec.md"
    frag.write_text(frag.read_text(encoding="utf-8")
                    + "\nFeeds from [[p2p/goods-receipt]] daily.\n",
                    encoding="utf-8")
    assert consolidate.main(["brief", str(area), "--bucket", "invoices"]) == 0
    assert "CROSS-AREA SEAMS" not in capsys.readouterr().out
