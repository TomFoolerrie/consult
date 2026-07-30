"""Tests for scripts/scaffold.py — the M0 confirm-gate scaffolder.

Covers L2/procedure order stability, M11 upstream-hint validation in
build_manifest, variant scope-note stamping, and the full --confirm flow on a
synthetic area under tmp_path.
"""
import json
from pathlib import Path

import yaml

import scaffold


# --------------------------------------------------------------------------- #
# compute_l2_order
# --------------------------------------------------------------------------- #

def test_compute_l2_order_taxonomy_order_for_used_buckets():
    """Fresh area: used buckets appear in taxonomy order, unused buckets are omitted."""
    procs = [{"slug": "a", "l2": "b2"}, {"slug": "b", "l2": "b1"}]
    order = scaffold.compute_l2_order(procs, ["b1", "b2", "b3"], [])
    assert order == ["b1", "b2"]


def test_compute_l2_order_preserves_existing_verbatim():
    """Merge: an existing l2_order is preserved verbatim (ordinals never drift), new buckets appended after."""
    procs = [{"slug": "a", "l2": "b2"}, {"slug": "b", "l2": "b1"},
             {"slug": "c", "l2": "b3"}]
    order = scaffold.compute_l2_order(procs, ["b1", "b2", "b3"], ["b2", "b1"])
    assert order == ["b2", "b1", "b3"]


def test_compute_l2_order_appends_new_buckets_first_seen():
    """Approved NEW buckets (used but absent from the taxonomy) append in first-seen order."""
    procs = [{"slug": "a", "l2": "custom-x"}, {"slug": "b", "l2": "b1"}]
    order = scaffold.compute_l2_order(procs, ["b1"], [])
    assert order == ["b1", "custom-x"]


# --------------------------------------------------------------------------- #
# assign_procedure_orders
# --------------------------------------------------------------------------- #

def test_assign_orders_fresh_area_sparse_sequence():
    """All-new procedures get the sparse 10/20/30 sequence in l2_order grouping."""
    procs = [{"slug": "a", "l2": "b1"}, {"slug": "b", "l2": "b2"},
             {"slug": "c", "l2": "b1"}]
    orders = scaffold.assign_procedure_orders(procs, ["b1", "b2"], {})
    assert orders == {"a": 10, "c": 20, "b": 30}


def test_assign_orders_existing_preserved_new_in_gap():
    """Existing orders are kept unchanged; a new procedure slots strictly between its neighbours."""
    procs = [{"slug": "a", "l2": "b1"}, {"slug": "new", "l2": "b1"},
             {"slug": "b", "l2": "b2"}]
    existing = {"a": 10, "b": 20}
    orders = scaffold.assign_procedure_orders(procs, ["b1", "b2"], existing)
    assert orders["a"] == 10 and orders["b"] == 20
    assert 10 < orders["new"] < 20


def test_assign_orders_new_at_end_gets_gap_after_last():
    """A new procedure with no following neighbour extends past the last existing order by the sparse gap."""
    procs = [{"slug": "a", "l2": "b1"}, {"slug": "new", "l2": "b1"}]
    orders = scaffold.assign_procedure_orders(procs, ["b1"], {"a": 10})
    assert orders == {"a": 10, "new": 20}


def test_assign_orders_renormalizes_when_gap_exhausted():
    """When no gap can hold the insert, the whole sequence renormalizes to the sparse base/gap grid."""
    procs = [{"slug": "a", "l2": "b1"}, {"slug": "new", "l2": "b1"},
             {"slug": "b", "l2": "b2"}]
    orders = scaffold.assign_procedure_orders(procs, ["b1", "b2"],
                                              {"a": 10, "b": 11})
    assert orders == {"a": 10, "new": 20, "b": 30}


# --------------------------------------------------------------------------- #
# build_manifest — M11 upstream validation
# --------------------------------------------------------------------------- #

def _mk_manifest(tmp_path, procedures):
    area = tmp_path / "areax"
    area.mkdir(exist_ok=True)
    orders = {p["slug"]: 10 * (i + 1) for i, p in enumerate(procedures)}
    return scaffold.build_manifest(area, "finance", "T", "S", procedures,
                                   ["ops"], orders)


def test_build_manifest_keeps_valid_upstream(tmp_path):
    """A valid upstream hint (known slug, not self) is carried into the manifest component."""
    m = _mk_manifest(tmp_path, [
        {"slug": "a", "title": "A", "l2": "ops"},
        {"slug": "b", "title": "B", "l2": "ops", "upstream": ["a"]},
    ])
    comp = next(c for c in m["components"] if c.get("slug") == "b")
    assert comp["upstream"] == ["a"]


def test_build_manifest_drops_unknown_and_self_upstream_with_warning(tmp_path, capsys):
    """Unknown-slug and self-reference upstream hints are dropped (with a WARNING each), never written."""
    m = _mk_manifest(tmp_path, [
        {"slug": "a", "title": "A", "l2": "ops", "upstream": ["ghost", "a"]},
    ])
    comp = next(c for c in m["components"] if c.get("slug") == "a")
    assert "upstream" not in comp
    out = capsys.readouterr().out
    assert "dropping upstream hint 'ghost'" in out
    assert "dropping upstream hint 'a'" in out


def test_build_manifest_dedupes_upstream(tmp_path):
    """Duplicate upstream hints collapse to one occurrence in the manifest."""
    m = _mk_manifest(tmp_path, [
        {"slug": "a", "title": "A", "l2": "ops"},
        {"slug": "b", "title": "B", "l2": "ops", "upstream": ["a", "a"]},
    ])
    comp = next(c for c in m["components"] if c.get("slug") == "b")
    assert comp["upstream"] == ["a"]


def test_merge_by_key_preserves_omitted_fields():
    """A re-emitted entry merges field-wise: fields the re-emission omits
    (upstream, variants, people) survive; explicit values still override."""
    existing = [{"slug": "pay", "title": "Pay", "l2": "ops",
                 "upstream": ["intake"], "variants": ["Wire", "ACH"]}]
    proposed = [{"slug": "pay", "title": "Payment Run", "l2": "ops"}]
    (merged,) = scaffold._merge_by_key(existing, proposed)
    assert merged["title"] == "Payment Run"
    assert merged["upstream"] == ["intake"]
    assert merged["variants"] == ["Wire", "ACH"]
    # explicit empty value still clears
    (cleared,) = scaffold._merge_by_key(
        existing, [{"slug": "pay", "upstream": []}])
    assert cleared["upstream"] == []


def test_build_manifest_validates_against_doc_model(tmp_path):
    """The manifest build_manifest produces passes doc_model.validate_manifest cleanly."""
    import doc_model
    m = _mk_manifest(tmp_path, [{"slug": "a", "title": "A", "l2": "ops"}])
    assert doc_model.validate_manifest(m) == []


# --------------------------------------------------------------------------- #
# confirm flow on a synthetic area
# --------------------------------------------------------------------------- #

def _setup_confirm_area(tmp_path):
    """Build tmp area + taxonomy: .proposed/ with procedures.yaml (one variant
    proc, one with a mixed-validity upstream) and a systems.yaml registry."""
    area = tmp_path / "components" / "treasury"
    proposed = area / "_reference" / ".proposed"
    proposed.mkdir(parents=True)
    (proposed / "procedures.yaml").write_text(yaml.safe_dump({
        "procedures": [
            {"slug": "cash-recon", "title": "Cash Reconciliation", "l2": "cash",
             "variants": ["domestic", "foreign"]},
            {"slug": "payment-run", "title": "Payment Run", "l2": "payments",
             "upstream": ["cash-recon", "nonexistent"]},
        ]
    }), encoding="utf-8")
    (proposed / "systems.yaml").write_text(yaml.safe_dump({
        "systems": [{"slug": "sap", "name": "SAP"}]
    }), encoding="utf-8")
    taxonomy = tmp_path / "taxonomy.yaml"
    taxonomy.write_text(yaml.safe_dump({
        "taxonomy": {"categories": [
            {"slug": "finance", "subcategories": [{"slug": "cash"},
                                                  {"slug": "payments"}]},
        ]}
    }), encoding="utf-8")
    return area, taxonomy


def test_confirm_scaffolds_area(tmp_path, capsys):
    """--confirm promotes the registry, writes manifest + skeletons + stubs, and clears .proposed/."""
    area, taxonomy = _setup_confirm_area(tmp_path)
    rc = scaffold.confirm(area, "finance", taxonomy, None, None)
    assert rc == 0

    manifest = json.loads((area / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "consult-mvp-manifest/v1"
    assert manifest["l2_order"] == ["cash", "payments"]
    proc = {c["slug"]: c for c in manifest["components"]
            if c.get("role") == "procedure"}
    assert set(proc) == {"cash-recon", "payment-run"}
    # valid upstream kept, unknown dropped with warning
    assert proc["payment-run"]["upstream"] == ["cash-recon"]
    assert "dropping upstream hint 'nonexistent'" in capsys.readouterr().out

    # skeletons carry the unfilled sentinel; variant proc gets the scope note
    cash = (area / "10_cash-recon.md").read_text(encoding="utf-8")
    assert "<!-- unfilled -->" in cash
    assert "covers variants — domestic; foreign" in cash
    pay = (area / "10_payment-run.md").read_text(encoding="utf-8")
    assert "<!-- unfilled -->" in pay
    assert "scope note" not in pay

    # registry promoted, proposal set consumed
    live = yaml.safe_load((area / "_reference" / "systems.yaml").read_text(encoding="utf-8"))
    assert live["systems"] == [{"slug": "sap", "name": "SAP"}]
    assert not (area / "_reference" / ".proposed").exists()

    # static + derived stubs exist
    assert (area / "00_document-profile.md").is_file()
    assert (area / "82_dependencies.md").is_file()


def test_confirm_is_idempotent_and_merges_registry(tmp_path):
    """Re-confirming with the same proposal set overwrites no fragment and preserves live registry entries not re-emitted."""
    area, taxonomy = _setup_confirm_area(tmp_path)
    scaffold.confirm(area, "finance", taxonomy, None, None)
    manifest1 = (area / "manifest.json").read_text(encoding="utf-8")
    frag = area / "10_cash-recon.md"
    frag.write_text("## Cash Reconciliation\n\nDrafted.\n", encoding="utf-8")

    # second proposal round: same procedures, registry adds one system
    proposed = area / "_reference" / ".proposed"
    proposed.mkdir(parents=True)
    (proposed / "procedures.yaml").write_text(yaml.safe_dump({
        "procedures": [
            {"slug": "cash-recon", "title": "Cash Reconciliation", "l2": "cash"},
            {"slug": "payment-run", "title": "Payment Run", "l2": "payments"},
        ]
    }), encoding="utf-8")
    (proposed / "systems.yaml").write_text(yaml.safe_dump({
        "systems": [{"slug": "blackline", "name": "BlackLine"}]
    }), encoding="utf-8")
    scaffold.confirm(area, "finance", taxonomy, None, None)

    # drafted fragment untouched, orders stable
    assert frag.read_text(encoding="utf-8") == "## Cash Reconciliation\n\nDrafted.\n"
    manifest2 = json.loads((area / "manifest.json").read_text(encoding="utf-8"))
    old = json.loads(manifest1)
    orders_old = {c["slug"]: c["order"] for c in old["components"]
                  if c.get("role") == "procedure"}
    orders_new = {c["slug"]: c["order"] for c in manifest2["components"]
                  if c.get("role") == "procedure"}
    assert orders_new == orders_old
    # registry merged, never wiped
    live = yaml.safe_load((area / "_reference" / "systems.yaml").read_text(encoding="utf-8"))
    slugs = [s["slug"] for s in live["systems"]]
    assert slugs == ["sap", "blackline"]


def test_confirm_stamps_source_hashes(tmp_path):
    """promote+stamp: a source file listed in sources.yaml gets its sha256 hash and state 'new'."""
    import hashlib
    area, taxonomy = _setup_confirm_area(tmp_path)
    (area / "_sources").mkdir()
    payload = b"interview notes"
    (area / "_sources" / "notes.txt").write_bytes(payload)
    proposed = area / "_reference" / ".proposed"
    (proposed / "sources.yaml").write_text(yaml.safe_dump({
        "sources": [{"id": "s1", "file": "_sources/notes.txt"}]
    }), encoding="utf-8")
    scaffold.confirm(area, "finance", taxonomy, None, None)
    live = yaml.safe_load((area / "_reference" / "sources.yaml").read_text(encoding="utf-8"))
    src = live["sources"][0]
    assert src["hash"] == hashlib.sha256(payload).hexdigest()
    assert src["state"] == "new"


def test_confirm_preserves_manifest_procedures_missing_from_proposal(tmp_path):
    """The live manifest is authoritative: a later proposal round that omits an
    existing procedure must NOT drop it from the rebuilt manifest."""
    area, taxonomy = _setup_confirm_area(tmp_path)
    scaffold.confirm(area, "finance", taxonomy, None, None)

    # second round proposes only ONE new procedure; existing two are omitted
    proposed = area / "_reference" / ".proposed"
    proposed.mkdir(parents=True)
    (proposed / "procedures.yaml").write_text(yaml.safe_dump({
        "procedures": [
            {"slug": "fx-hedging", "title": "FX Hedging", "l2": "cash"},
        ]
    }), encoding="utf-8")
    scaffold.confirm(area, "finance", taxonomy, None, None)

    manifest = json.loads((area / "manifest.json").read_text(encoding="utf-8"))
    procs = {c["slug"]: c for c in manifest["components"]
             if c.get("role") == "procedure"}
    assert set(procs) == {"cash-recon", "payment-run", "fx-hedging"}
    # preserved procedure keeps its upstream hint and heading
    assert procs["payment-run"]["upstream"] == ["cash-recon"]
    assert procs["cash-recon"]["heading"] == "Cash Reconciliation"


def test_confirm_with_empty_procedures_does_registry_only_pass(tmp_path):
    """Incremental pass touching only existing procedures: an empty
    procedures.yaml still merges the registry, keeps the manifest intact, and
    consumes .proposed/."""
    area, taxonomy = _setup_confirm_area(tmp_path)
    scaffold.confirm(area, "finance", taxonomy, None, None)
    manifest1 = (area / "manifest.json").read_text(encoding="utf-8")

    proposed = area / "_reference" / ".proposed"
    proposed.mkdir(parents=True)
    (proposed / "procedures.yaml").write_text(
        yaml.safe_dump({"procedures": []}), encoding="utf-8")
    (proposed / "systems.yaml").write_text(yaml.safe_dump({
        "systems": [{"slug": "blackline", "name": "BlackLine"}]
    }), encoding="utf-8")
    rc = scaffold.confirm(area, None, taxonomy, None, None)
    assert rc == 0

    # manifest procedures unchanged, registry merged, proposal set consumed
    manifest2 = json.loads((area / "manifest.json").read_text(encoding="utf-8"))
    old_procs = {c["slug"] for c in json.loads(manifest1)["components"]
                 if c.get("role") == "procedure"}
    new_procs = {c["slug"] for c in manifest2["components"]
                 if c.get("role") == "procedure"}
    assert new_procs == old_procs
    live = yaml.safe_load((area / "_reference" / "systems.yaml").read_text(encoding="utf-8"))
    assert [s["slug"] for s in live["systems"]] == ["sap", "blackline"]
    assert not (area / "_reference" / ".proposed").exists()


def test_confirm_empty_procedures_and_no_manifest_still_errors(tmp_path):
    """Initial scoping with an empty procedures.yaml has nothing to scaffold —
    that is still a hard error."""
    import pytest
    area, taxonomy = _setup_confirm_area(tmp_path)
    proposed = area / "_reference" / ".proposed"
    (proposed / "procedures.yaml").write_text(
        yaml.safe_dump({"procedures": []}), encoding="utf-8")
    with pytest.raises(SystemExit):
        scaffold.confirm(area, "finance", taxonomy, None, None)


def test_confirm_rejects_duplicate_slug(tmp_path):
    """Proposal sanity: a duplicate procedure slug aborts the confirm with SystemExit."""
    import pytest
    area, taxonomy = _setup_confirm_area(tmp_path)
    proposed = area / "_reference" / ".proposed"
    (proposed / "procedures.yaml").write_text(yaml.safe_dump({
        "procedures": [
            {"slug": "x", "title": "X", "l2": "cash"},
            {"slug": "x", "title": "X2", "l2": "cash"},
        ]
    }), encoding="utf-8")
    with pytest.raises(SystemExit):
        scaffold.confirm(area, "finance", taxonomy, None, None)


def test_main_refuses_without_confirm(tmp_path):
    """The CLI is a human gate: running without --confirm raises SystemExit."""
    import pytest
    with pytest.raises(SystemExit):
        scaffold.main(["--area", str(tmp_path)])


def test_unknown_l1_is_advisory_not_fatal(tmp_path, capsys):
    """The reference taxonomy is a menu, not a gate: an L1 it does not list
    returns an empty backbone (loudly), and compute_l2_order then files every
    used bucket as an approved new bucket in first-seen order."""
    import yaml as _yaml
    tax = tmp_path / "taxonomy.yaml"
    tax.write_text(_yaml.safe_dump({"taxonomy": {"categories": [
        {"name": "Procure to Pay", "slug": "procure-to-pay",
         "subcategories": [{"name": "Payments", "slug": "payments"}]},
    ]}}), encoding="utf-8")
    buckets = scaffold.load_l1_buckets(tax, "field-services")
    assert buckets == []
    assert "advisory" in capsys.readouterr().out
    order = scaffold.compute_l2_order(
        [{"l2": "dispatch"}, {"l2": "billing"}, {"l2": "dispatch"}],
        buckets, [])
    assert order == ["dispatch", "billing"]
