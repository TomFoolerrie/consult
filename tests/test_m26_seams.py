"""Tests for M26 — the engagement seam model: [[area/slug]] cross-area
tokens (grammar, resolution, reconcile validation), scaffold's preservation
of cross-area upstream declarations, the advisor's non-blocking behavior on
them (pinned), the drafter brief's seam context, and the audit's derived
spine. All fixtures are synthetic, under tmp_path."""
import json
from pathlib import Path

import pytest

import brief
import callouts
import doc_model
import engagement
import orchestrate
import reconcile
import render as render_mod
import scaffold


# --------------------------------------------------------------------------- #
# Engagement fixture: components/{cash,p2p}
# --------------------------------------------------------------------------- #

def _area(root: Path, name: str, procs, title=None, body_extra="",
          drafted=True):
    """procs: [(slug, heading)] — first procedure carries body_extra."""
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    comps = []
    for i, entry in enumerate(procs):
        slug, heading = entry[0], entry[1]
        comp = {"file": f"10_{slug}.md", "role": "procedure", "slug": slug,
                "heading": heading, "l2": "ops", "order": 10 + 10 * i}
        if len(entry) > 2 and entry[2]:
            comp["upstream"] = list(entry[2])
        comps.append(comp)
        extra = body_extra if i == 0 else ""
        body = (f"## {heading}\n\n{extra}\n\nDrafted content.\n" if drafted
                else f"## {heading}\n\n<!-- unfilled -->\n\nTBD.\n")
        (d / f"10_{slug}.md").write_text(body, encoding="utf-8")
    manifest = {"schema": "consult-mvp-manifest/v1", "area": name,
                "l1": "finance", "l2_order": ["ops"],
                "title": title or name.upper(), "subtitle": "S",
                "components": comps}
    (d / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return d


def make_engagement(tmp_path: Path, cash_extra="", cash_upstream=None,
                    p2p_drafted=True):
    root = tmp_path / "components"
    cash_procs = [("bank-rec", "Bank Reconciliation",
                   cash_upstream or []),
                  ("cash-forecast", "Cash Forecasting")]
    _area(root, "cash", cash_procs, title="Cash Management",
          body_extra=cash_extra)
    _area(root, "p2p", [("goods-receipt", "Goods Receipt"),
                        ("payment-run", "Payment Run")],
          title="Procure to Pay", drafted=p2p_drafted)
    return root


# --------------------------------------------------------------------------- #
# 1. Grammar + resolution (the load-bearing XREF_RE extension)
# --------------------------------------------------------------------------- #

def test_xref_re_matches_cross_area_token():
    assert callouts.XREF_RE.findall("x [[p2p/goods-receipt]] y") \
        == ["p2p/goods-receipt"]
    # local form unchanged; two slashes never match
    assert callouts.XREF_RE.findall("[[bank-rec]] [[a/b/c]]") == ["bank-rec"]


def test_resolve_tokens_cross_area_always_full_label():
    labels = {"bank-rec": "1.1", "p2p/goods-receipt":
              "Goods Receipt (Procure to Pay)"}
    out = doc_model.resolve_tokens(
        "See [[bank-rec]] and [[p2p/goods-receipt]].", labels, "number")
    # cross token NEVER renders a number, whatever the mode
    assert out == "See 1.1 and Goods Receipt (Procure to Pay)."


def test_resolve_tokens_number_only_cross_form_raises():
    labels = {"p2p/goods-receipt": "Goods Receipt (Procure to Pay)"}
    with pytest.raises(ValueError):
        doc_model.resolve_tokens("[[#p2p/goods-receipt]]", labels, "number")


def test_unknown_cross_token_raises_keyerror():
    with pytest.raises(KeyError):
        doc_model.resolve_tokens("[[p2p/nope]]", {}, "number")


def test_cross_labels_built_from_sibling_manifests(tmp_path):
    root = make_engagement(tmp_path)
    labels = doc_model.cross_labels(root / "cash")
    assert labels["p2p/goods-receipt"] == "Goods Receipt (Procure to Pay)"
    assert "cash/bank-rec" not in labels  # own area is never a sibling
    # outside a components/ root: empty map (cross tokens fail loud upstream)
    assert doc_model.cross_labels(tmp_path) == {}


def test_raw_cross_token_never_survives_to_render(tmp_path):
    """The acceptance test the sanity pass demanded: a cross token either
    resolves to heading + area title or fails loud — never raw brackets."""
    root = make_engagement(tmp_path)
    labels = dict(doc_model.cross_labels(root / "cash"))
    out = render_mod._clean_body(
        "## Bank Reconciliation\n\nFeeds from [[p2p/goods-receipt]].\n",
        labels)
    assert "[[" not in out
    assert "Goods Receipt (Procure to Pay)" in out
    with pytest.raises(KeyError):
        render_mod._clean_body("From [[p2p/goods-receipt]].", {})


# --------------------------------------------------------------------------- #
# 2. Reconcile validation (identity = the sibling MANIFEST)
# --------------------------------------------------------------------------- #

def _reconcile_out(area, capsys):
    rc = reconcile.reconcile(str(area))
    return rc, capsys.readouterr().out


def test_valid_cross_token_is_not_dangling(tmp_path, capsys):
    root = make_engagement(
        tmp_path, cash_extra="Feeds from [[p2p/goods-receipt]].")
    _rc, out = _reconcile_out(root / "cash", capsys)
    assert "DANGLING [[p2p/goods-receipt]]" not in out


def test_token_to_scoped_but_unfilled_sibling_is_valid(tmp_path, capsys):
    root = make_engagement(
        tmp_path, cash_extra="Feeds from [[p2p/goods-receipt]].",
        p2p_drafted=False)
    _rc, out = _reconcile_out(root / "cash", capsys)
    assert "DANGLING [[p2p/goods-receipt]]" not in out


def test_dangling_area_and_slug_are_errors_naming_the_siblings(tmp_path,
                                                               capsys):
    root = make_engagement(
        tmp_path,
        cash_extra="From [[nope/x]] and [[p2p/wrong-slug]].")
    rc, out = _reconcile_out(root / "cash", capsys)
    assert rc != 0
    assert "DANGLING [[nope/x]] — no sibling area 'nope'" in out
    assert "DANGLING [[p2p/wrong-slug]]" in out
    assert "goods-receipt" in out  # the fix names the sibling's known slugs


def test_cross_token_outside_components_root_is_layout_error(tmp_path,
                                                             capsys):
    area = _area(tmp_path, "standalone",
                 [("bank-rec", "Bank Reconciliation")],
                 body_extra="From [[p2p/goods-receipt]].")
    rc, out = _reconcile_out(area, capsys)
    assert rc != 0
    assert "not under a components/ engagement root" in out


def test_number_only_cross_token_is_error(tmp_path, capsys):
    root = make_engagement(tmp_path,
                           cash_extra="Ref [[#p2p/goods-receipt]].")
    rc, out = _reconcile_out(root / "cash", capsys)
    assert rc != 0
    assert "no display number" in out


# --------------------------------------------------------------------------- #
# 3. Scaffold preserves cross-area upstream (regression: it dropped them)
# --------------------------------------------------------------------------- #

def test_build_manifest_preserves_valid_cross_upstream(tmp_path, capsys):
    root = make_engagement(tmp_path)
    procs = [{"slug": "bank-rec", "title": "Bank Reconciliation",
              "l2": "ops",
              "upstream": ["cash-forecast", "p2p/goods-receipt",
                           "p2p/nope", "ghost/x"]},
             {"slug": "cash-forecast", "title": "Cash Forecasting",
              "l2": "ops"}]
    m = scaffold.build_manifest(root / "cash", "finance", "T", "S", procs,
                                ["ops"],
                                {"bank-rec": 10, "cash-forecast": 20})
    comp = next(c for c in m["components"] if c.get("slug") == "bank-rec")
    assert comp["upstream"] == ["cash-forecast", "p2p/goods-receipt"]
    out = capsys.readouterr().out
    assert "dropping cross-area upstream hint 'p2p/nope'" in out
    assert "dropping cross-area upstream hint 'ghost/x'" in out


# --------------------------------------------------------------------------- #
# 4. The advisor NEVER defers on a cross-area hint (pinning what was
#    accidental: a cross entry is never in the local pending set)
# --------------------------------------------------------------------------- #

def test_wave_logic_never_defers_on_cross_area_upstream(tmp_path):
    root = make_engagement(
        tmp_path, cash_upstream=["p2p/goods-receipt"], p2p_drafted=False)
    # make BOTH cash fragments unfilled so the fill guard fires
    for slug in ("bank-rec", "cash-forecast"):
        (root / "cash" / f"10_{slug}.md").write_text(
            f"## X\n\n<!-- unfilled -->\n\nTBD.\n", encoding="utf-8")
    d = orchestrate.decide(str(root / "cash"))
    assert d["action"] == "fill"
    assert sorted(d["details"]["unfilled"]) == ["bank-rec", "cash-forecast"]
    assert "deferred" not in d["details"]


# --------------------------------------------------------------------------- #
# 5. Drafter brief — cross-area seam context, both drafting states
# --------------------------------------------------------------------------- #

def _brief_out(area, slug, capsys):
    assert brief.main([str(area), "--slug", slug]) == 0
    return capsys.readouterr().out


def test_brief_lists_drafted_cross_upstream_read_only(tmp_path, capsys):
    root = make_engagement(tmp_path, cash_upstream=["p2p/goods-receipt"])
    out = _brief_out(root / "cash", "bank-rec", capsys)
    assert "CROSS-AREA upstream seam" in out
    assert "10_goods-receipt.md" in out
    assert "[[p2p/goods-receipt]]" in out


def test_brief_says_scoped_not_yet_drafted_honestly(tmp_path, capsys):
    root = make_engagement(tmp_path, cash_upstream=["p2p/goods-receipt"],
                           p2p_drafted=False)
    out = _brief_out(root / "cash", "bank-rec", capsys)
    assert "scoped, not" in out and "yet drafted" in out
    assert "seam_unverified" in out
    assert "10_goods-receipt.md" not in out.split("OWNERSHIP MAP")[0] \
        or "seam context UNAVAILABLE" in out


# --------------------------------------------------------------------------- #
# 6. The derived spine (audit section 5)
# --------------------------------------------------------------------------- #

def test_audit_interfaces_section_lists_tokens_and_upstream(tmp_path,
                                                            capsys):
    root = make_engagement(
        tmp_path, cash_extra="Feeds from [[p2p/goods-receipt]].",
        cash_upstream=["p2p/goods-receipt"])
    assert engagement.main(["audit", str(root)]) == 0
    out = capsys.readouterr().out
    assert "5. INTERFACES" in out
    assert "cash/bank-rec  --token-->  p2p/goods-receipt" in out
    assert "cash/bank-rec  --upstream-->  p2p/goods-receipt" in out
    # p2p declares nothing back: asymmetric seam flagged with the fix
    assert "asymmetric seam" in out
    assert "incremental taxonomy pass on p2p" in out


def test_audit_spine_empty_when_nothing_declared(tmp_path, capsys):
    root = make_engagement(tmp_path)
    assert engagement.main(["audit", str(root)]) == 0
    out = capsys.readouterr().out
    assert "none declared yet" in out
