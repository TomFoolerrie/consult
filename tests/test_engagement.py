"""Tests for scripts/engagement.py — the cross-area duplication audit."""
import json
from pathlib import Path

import engagement


LONG = ("The sales package is assembled from the trial balance schedules "
        "and circulated to the site controllers for sign-off.")


def make_engagement(tmp_path: Path) -> Path:
    root = tmp_path / "components"
    for area, procs in {
        "fscp": [("sales-package-preparation", "Sales Package Preparation",
                  f"## Sales Package Preparation\n\n{LONG}\n"),
                 ("close-calendar", "Close Calendar Management",
                  "## Close Calendar Management\n\nOwn text here.\n")],
        "inventory": [("cycle-counts", "Cycle Counts",
                       f"## Cycle Counts\n\nCounting text.\n\n{LONG}\n\n"
                       "The sales package preparation is described here "
                       "too.\n"),
                      ("sales-package-prep", "Preparation of the Sales "
                       "Package",
                       "## Preparation of the Sales Package\n\nDup.\n")],
    }.items():
        d = root / area
        d.mkdir(parents=True)
        comps = [{"file": f"10_{s}.md", "role": "procedure", "slug": s,
                  "heading": h, "order": 10 + i}
                 for i, (s, h, _) in enumerate(procs)]
        (d / "manifest.json").write_text(json.dumps(
            {"area": area, "title": area.upper(), "components": comps}),
            encoding="utf-8")
        for s, _h, text in procs:
            (d / f"10_{s}.md").write_text(text, encoding="utf-8")
    return root


def test_audit_finds_all_three_shapes(tmp_path, capsys):
    root = make_engagement(tmp_path)
    assert engagement.main(["audit", str(root)]) == 0
    out = capsys.readouterr().out
    # twin L3s: 'Sales Package Preparation' vs 'Preparation of the Sales
    # Package' (token containment across word order)
    assert "fscp/sales-package-preparation" in out
    assert "inventory/sales-package-prep" in out
    # cross mention: inventory prose names fscp's procedure title
    assert "names 'Sales Package Preparation'" in out
    # shared prose: the identical long sentence in both areas
    assert "8-word run(s)" in out
    assert "duplication finding(s)" in out


def test_clean_engagement_reports_clean(tmp_path, capsys):
    root = make_engagement(tmp_path)
    # remove the duplication: distinct titles, distinct prose
    inv = root / "inventory"
    m = json.loads((inv / "manifest.json").read_text(encoding="utf-8"))
    m["components"] = [c for c in m["components"]
                       if c["slug"] == "cycle-counts"]
    (inv / "manifest.json").write_text(json.dumps(m), encoding="utf-8")
    (inv / "10_cycle-counts.md").write_text(
        "## Cycle Counts\n\nEntirely distinct counting prose that shares "
        "nothing with the close process narrative at all.\n",
        encoding="utf-8")
    assert engagement.main(["audit", str(root)]) == 0
    out = capsys.readouterr().out
    assert "Clean: no cross-area duplication, no open gaps." in out


def test_single_area_engagement_explains_layout(tmp_path, capsys):
    root = tmp_path / "components"
    (root / "only").mkdir(parents=True)
    (root / "only" / "manifest.json").write_text(
        json.dumps({"area": "only", "components": []}), encoding="utf-8")
    assert engagement.main(["audit", str(root)]) == 0
    assert "at least two scoped areas" in capsys.readouterr().out


def test_missing_root_exits_2(tmp_path, capsys):
    assert engagement.main(["audit", str(tmp_path / "nope")]) == 2
    assert "engagement root" in capsys.readouterr().err


def test_note_queues_review_item_idempotently(tmp_path, capsys):
    root = make_engagement(tmp_path)
    area = root / "inventory"
    args = ["note", str(area), "--slug", "cycle-counts", "--note",
            "Reduce the sales package text to a handoff; owner is "
            "fscp/sales-package-preparation."]
    assert engagement.main(args) == 0
    assert "queued 1 review note" in capsys.readouterr().out
    notes = (area / "_review" / "cycle-counts.notes.yaml") \
        .read_text(encoding="utf-8")
    assert 'kind: "review"' in notes and "handoff" in notes
    # idempotent: same note again is a no-op
    assert engagement.main(args) == 0
    assert "no-op" in capsys.readouterr().out


def test_note_unknown_slug_exits_2(tmp_path, capsys):
    root = make_engagement(tmp_path)
    assert engagement.main(["note", str(root / "inventory"),
                            "--slug", "nope", "--note", "x"]) == 2
    assert "cycle-counts" in capsys.readouterr().err


def test_shared_prose_catches_paraphrase_with_shared_skeleton(tmp_path,
                                                              capsys):
    """Exact-sentence matching missed paraphrases; shingling must not. Two
    fragments share an 11+ word run inside otherwise different sentences."""
    root = make_engagement(tmp_path)
    skeleton = ("the invoice is matched against the purchase order and the "
                "goods receipt before any payment is released")
    (root / "fscp" / "10_close-calendar.md").write_text(
        f"## Close Calendar Management\n\nAt period end {skeleton} by the "
        "AP team.\n", encoding="utf-8")
    (root / "inventory" / "10_cycle-counts.md").write_text(
        f"## Cycle Counts\n\nFor received stock, {skeleton}, per policy.\n",
        encoding="utf-8")
    assert engagement.main(["audit", str(root)]) == 0
    out = capsys.readouterr().out
    assert "fscp/close-calendar  <->  inventory/cycle-counts" in out
    assert "8-word run(s)" in out


def test_shared_prose_survives_hard_wrapping(tmp_path, capsys):
    """Fragments hard-wrap at ~80 columns — shingles must run across line
    breaks inside a paragraph."""
    root = make_engagement(tmp_path)
    wrapped = ("the invoice is matched against the purchase\n"
               "order and the goods receipt before any payment\n"
               "is released to the supplier bank account")
    unwrapped = wrapped.replace("\n", " ")
    (root / "fscp" / "10_close-calendar.md").write_text(
        f"## X\n\n{wrapped}\n", encoding="utf-8")
    (root / "inventory" / "10_cycle-counts.md").write_text(
        f"## Y\n\n{unwrapped}\n", encoding="utf-8")
    assert engagement.main(["audit", str(root)]) == 0
    assert "fscp/close-calendar  <->  inventory/cycle-counts" in \
        capsys.readouterr().out


# --------------------------------------------------------------------------- #
# M24 — the knowledge-placement layer: gap register, placement brief, adopt
# --------------------------------------------------------------------------- #

GAPPY = """## Cycle Counts

### Scope

Counting text with an open question [[GAP-02 — where the recount
sheets are retained]].

### Procedure

> **VALIDATION REQUIRED — GAP-01:** How the goods receipt posts to the
> sub-ledger is unconfirmed.
"""


def add_gaps(root):
    (root / "inventory" / "10_cycle-counts.md").write_text(
        GAPPY, encoding="utf-8")


def test_audit_gap_register_reads_both_gap_forms(tmp_path, capsys):
    root = make_engagement(tmp_path)
    add_gaps(root)
    before = {str(p) for p in root.rglob("*")}
    assert engagement.main(["audit", str(root)]) == 0
    out = capsys.readouterr().out
    assert {str(p) for p in root.rglob("*")} == before        # read-only
    assert "4. OPEN GAPS" in out
    assert "inventory/cycle-counts" in out
    # callout form, with hard-wrapped text joined
    assert "GAP-01 — How the goods receipt posts to the sub-ledger" in out
    # body-tag form, wrap rejoined
    assert "GAP-02 — where the recount sheets are retained" in out
    assert "2 open gap(s)" in out


def test_gap_defined_as_callout_and_tagged_counts_once(tmp_path, capsys):
    root = make_engagement(tmp_path)
    (root / "inventory" / "10_cycle-counts.md").write_text(
        "## Cycle Counts\n\nSee [[GAP-01 — short label]].\n\n"
        "> **VALIDATION REQUIRED — GAP-01:** The full question text.\n",
        encoding="utf-8")
    assert engagement.main(["audit", str(root)]) == 0
    out = capsys.readouterr().out
    assert "1 open gap(s)" in out
    assert "The full question text" in out            # callout text wins
    assert "short label" not in out


def test_placement_brief_carries_rules_findings_and_digests(tmp_path,
                                                            capsys):
    root = make_engagement(tmp_path)
    add_gaps(root)
    regs = root / "_client" / "registers"
    regs.mkdir(parents=True)
    (regs / "approval-matrix.md").write_text("| band | approver |\n",
                                             encoding="utf-8")
    before = {str(p) for p in root.rglob("*")}
    assert engagement.main(["brief", str(root)]) == 0
    out = capsys.readouterr().out
    assert {str(p) for p in root.rglob("*")} == before        # read-only
    assert "knowledge-placement pass" in out
    # the three moves + the fourth non-move
    assert "reduce to handoff" in out
    assert "promote to register" in out and "PRIMARY MOVE" in out
    assert "adopt as source" in out
    assert "POLICY" in out and "unresolved" in out
    # registers listed; mechanical findings + gaps + digests present
    assert "approval-matrix.md" in out
    assert "twin L3s:" in out and "OPEN GAP REGISTER (2 gap(s))" in out
    assert "[[sales-package-preparation]]" in out
    assert "Report-don't-guess" in out


def test_adopt_registers_prose_as_source_idempotently(tmp_path, capsys):
    import yaml
    import notes_util
    root = make_engagement(tmp_path)
    inv = root / "inventory"
    args = ["adopt", str(inv), "--from", "fscp/sales-package-preparation",
            "--touches", "cycle-counts"]
    assert engagement.main(args) == 0
    out = capsys.readouterr().out
    assert "SRC-001" in out and "hash-stamped" in out
    copy = inv / "_sources" / "new" / "adopted-fscp-sales-package-preparation.md"
    assert copy.is_file()
    assert copy.read_text(encoding="utf-8") == \
        (root / "fscp" / "10_sales-package-preparation.md").read_text(
            encoding="utf-8")
    data = yaml.safe_load(
        (inv / "_reference" / "sources.yaml").read_text(encoding="utf-8"))
    entry = data["sources"][0]
    assert entry["id"] == "SRC-001" and entry["state"] == "new"
    assert entry["touches"] == ["cycle-counts"]
    assert "second-hand" in entry["note"]
    import hashlib
    assert entry["hash"] == hashlib.sha256(copy.read_bytes()).hexdigest()
    items = notes_util.load_items(inv, "cycle-counts")
    assert len(items) == 1
    assert items[0]["kind"] == "source" and items[0]["src"] == "SRC-001"
    # rerun: hash match -> no-op, note dedupes
    assert engagement.main(args) == 0
    assert "no-op" in capsys.readouterr().out
    data = yaml.safe_load(
        (inv / "_reference" / "sources.yaml").read_text(encoding="utf-8"))
    assert len(data["sources"]) == 1
    assert len(notes_util.load_items(inv, "cycle-counts")) == 1


def test_adopt_respects_the_sticky_hold(tmp_path, capsys):
    root = make_engagement(tmp_path)
    inv = root / "inventory"
    (inv / "_client").mkdir()
    (inv / "_client" / "consult.yaml").write_text("hold: [adopt]\n",
                                                  encoding="utf-8")
    before = {str(p) for p in root.rglob("*")}
    assert engagement.main(
        ["adopt", str(inv), "--from", "fscp/sales-package-preparation",
         "--touches", "cycle-counts"]) == 3
    err = capsys.readouterr().err
    assert "held: adopt" in err and "area" in err
    assert {str(p) for p in root.rglob("*")} == before   # nothing written


def test_adopt_validates_from_and_touches(tmp_path, capsys):
    root = make_engagement(tmp_path)
    inv = root / "inventory"
    assert engagement.main(
        ["adopt", str(inv), "--from", "fscp/nope",
         "--touches", "cycle-counts"]) == 2
    assert "sales-package-preparation" in capsys.readouterr().err
    assert engagement.main(
        ["adopt", str(inv), "--from", "fscp/sales-package-preparation",
         "--touches", "nope"]) == 2
    assert "cycle-counts" in capsys.readouterr().err
