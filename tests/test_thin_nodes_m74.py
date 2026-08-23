"""Tests for M74 — thin nodes wait for evidence.

The taxonomist's per-procedure `confidence` call survives confirm into the
manifest (Part A), and the `fill` guard partitions its wave on it (Part B):
`low` nodes leave the dispatchable wave and are named in `details.thin` with
their values, while `fill` stays a NON-gate holdable throughout.

The ruling these tests pin, in order:

  * confidence gates COST, never SCOPE — a thin node keeps its manifest
    component, its skeleton and its place in every count
  * `details.unfilled` keeps its name and shape; `thin` is purely additive,
    so confidence-free areas are byte-identical to pre-M74 output
  * a thin-EXCLUDED upstream is treated as ABSENT for wave release (Part D):
    a downstream node whose only blocker is a thin node still rides this
    wave, with no `upstream_files` entry for it — the drafter's seam read
    degrades to the node scope prose rather than stranding the ladder
"""
import json
import os

import orchestrate
import scaffold

from test_orchestrate import make_area, FILLED_BODY, UNFILLED_BODY


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def make_conf_area(tmp_path, procs, name="treasury"):
    """`make_area` plus a per-component `confidence` key where asked.

    `procs` entries accept the same keys as `make_area` plus `confidence`.
    """
    folder = make_area(tmp_path, procs, name=name)
    path = os.path.join(folder, "manifest.json")
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    conf = {p["slug"]: p["confidence"] for p in procs if p.get("confidence")}
    for c in manifest["components"]:
        if c.get("slug") in conf:
            c["confidence"] = conf[c["slug"]]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh)
    return folder


def _fill_details(decision):
    """`details` minus the M73 checkpoint advisory, which every action
    carries and which has nothing to do with the fill partition."""
    return {k: v for k, v in decision["details"].items() if k != "git"}


def _mk_manifest(tmp_path, procedures, name="areax"):
    area = tmp_path / name
    area.mkdir(exist_ok=True)
    orders = {p["slug"]: 10 * (i + 1) for i, p in enumerate(procedures)}
    return scaffold.build_manifest(area, "finance", "T", "S", procedures,
                                   ["ops"], orders)


# --------------------------------------------------------------------------- #
# Part A — confirm carries the call into the manifest
# --------------------------------------------------------------------------- #

def test_build_manifest_carries_procedure_confidence(tmp_path):
    """A staged procedure's `confidence` lands on its manifest component."""
    m = _mk_manifest(tmp_path, [
        {"slug": "a", "title": "A", "l2": "ops", "confidence": "low"},
        {"slug": "b", "title": "B", "l2": "ops", "confidence": "medium"},
        {"slug": "c", "title": "C", "l2": "ops", "confidence": "high"},
    ])
    got = {c["slug"]: c.get("confidence")
           for c in m["components"] if c.get("role") == "procedure"}
    assert got == {"a": "low", "b": "medium", "c": "high"}


def test_build_manifest_omits_absent_confidence(tmp_path):
    """No key staged, no key written — a pre-M74 or hand-built entry
    round-trips as no-opinion (which behaves as high)."""
    m = _mk_manifest(tmp_path, [{"slug": "a", "title": "A", "l2": "ops"}])
    comp = next(c for c in m["components"] if c.get("slug") == "a")
    assert "confidence" not in comp


def test_build_manifest_confidence_does_not_disturb_other_keys(tmp_path):
    """The passthrough is one key: heading (NOT title), l2, order, upstream
    and the rest are exactly what a confidence-free build produces."""
    plain = _mk_manifest(tmp_path, [
        {"slug": "a", "title": "A", "l2": "ops"},
        {"slug": "b", "title": "B", "l2": "ops", "upstream": ["a"]},
    ], name="plain")
    conf = _mk_manifest(tmp_path, [
        {"slug": "a", "title": "A", "l2": "ops", "confidence": "low"},
        {"slug": "b", "title": "B", "l2": "ops", "upstream": ["a"],
         "confidence": "high"},
    ], name="conf")
    for pc, cc in zip(plain["components"], conf["components"]):
        cc = {k: v for k, v in cc.items() if k != "confidence"}
        assert pc == cc


def test_manifest_with_confidence_still_validates(tmp_path):
    """doc_model.validate_manifest is positive-only — no schema change."""
    import doc_model
    m = _mk_manifest(tmp_path, [
        {"slug": "a", "title": "A", "l2": "ops", "confidence": "low"}])
    assert doc_model.validate_manifest(m) == []


def test_merge_by_key_carries_confidence_forward():
    """The confirm merge already delivers `confidence` on the proposed
    procedure, and a re-emission omitting it does not clear it."""
    existing = [{"slug": "pay", "title": "Pay", "l2": "ops",
                 "confidence": "low"}]
    (merged,) = scaffold._merge_by_key(
        existing, [{"slug": "pay", "title": "Payment Run", "l2": "ops"}])
    assert merged["confidence"] == "low"
    (raised,) = scaffold._merge_by_key(
        existing, [{"slug": "pay", "confidence": "high"}])
    assert raised["confidence"] == "high"


# --------------------------------------------------------------------------- #
# Part B — the fill action partitions the wave
# --------------------------------------------------------------------------- #

def test_fill_wave_excludes_low_and_names_it_thin(tmp_path):
    """Mixed-confidence area: `low` leaves the wave and appears in
    `details.thin` with its value; `medium` and `high` stay dispatchable."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": False, "confidence": "high"},
        {"slug": "b", "filled": False, "confidence": "medium"},
        {"slug": "c", "filled": False, "confidence": "low"},
    ])
    d = orchestrate.decide(area)
    assert d["action"] == "fill"
    assert d["details"]["unfilled"] == ["a", "b"]
    assert d["details"]["thin"] == {"c": "low"}
    assert d.get("human_gate") is not True


def test_fill_thin_values_are_reported_per_slug(tmp_path):
    """`thin` names each waiting slug WITH its confidence value."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": False},
        {"slug": "b", "filled": False, "confidence": "low"},
        {"slug": "c", "filled": False, "confidence": "low"},
    ])
    d = orchestrate.decide(area)
    assert d["details"]["unfilled"] == ["a"]
    assert d["details"]["thin"] == {"b": "low", "c": "low"}


def test_fill_counts_thin_nodes_in_the_total(tmp_path):
    """Confidence gates COST, never SCOPE: the reason still counts every
    unfilled skeleton, thin ones included."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": False},
        {"slug": "b", "filled": False, "confidence": "low"},
    ])
    d = orchestrate.decide(area)
    assert d["reason"].startswith("2 procedure(s) ")
    assert "1 thin node(s) wait on evidence" in d["reason"]


def test_fill_all_thin_returns_empty_wave_and_the_choice(tmp_path):
    """All-thin remainder: `fill` with an EMPTY `unfilled`, a populated
    `thin`, and a reason naming the human's two options. NOT a gate — the
    HOLDABLE ∩ GATE disjointness doctrine stands untouched."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": True},
        {"slug": "b", "filled": False, "confidence": "low"},
        {"slug": "c", "filled": False, "confidence": "low"},
    ])
    d = orchestrate.decide(area)
    assert d["action"] == "fill"
    assert d["details"]["unfilled"] == []
    assert d["details"]["thin"] == {"b": "low", "c": "low"}
    assert d.get("human_gate") is not True
    assert "2 thin node(s) remain" in d["reason"]
    assert "dispatch them" in d["reason"]
    assert "hold `fill`" in d["reason"]
    # the all-thin remainder is NOT a cycle degradation
    assert "cycle" not in d["reason"]
    assert "deferred" not in d["details"]


def test_fill_stays_a_holdable_non_gate_with_thin_nodes(tmp_path):
    """`fill` is in HOLDABLE_ACTIONS and never in GATE_ACTIONS, all-thin or
    not — M74 introduces no sometimes-gate."""
    assert "fill" in orchestrate.HOLDABLE_ACTIONS
    assert "fill" not in orchestrate.GATE_ACTIONS
    area = make_conf_area(tmp_path, [
        {"slug": "b", "filled": False, "confidence": "low"}])
    d = orchestrate.decide(area)
    assert d["action"] == "fill"
    assert d.get("human_gate") is not True


def test_medium_confidence_never_waits(tmp_path):
    """Only `low` waits — the boundary is one word in one place."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": False, "confidence": "medium"}])
    d = orchestrate.decide(area)
    assert d["details"]["unfilled"] == ["a"]
    assert "thin" not in d["details"]


def test_unknown_confidence_value_reads_as_no_opinion(tmp_path):
    """Anything that is not `low` is dispatchable — a garbled value must
    never silently park a node."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": False, "confidence": "unknowable"}])
    d = orchestrate.decide(area)
    assert d["details"]["unfilled"] == ["a"]
    assert "thin" not in d["details"]


# --------------------------------------------------------------------------- #
# Part D — a thin-excluded upstream must not strand its downstream
# --------------------------------------------------------------------------- #

def test_thin_upstream_is_absent_for_wave_release(tmp_path):
    """THE RULING: a thin-and-excluded upstream is treated as ABSENT for wave
    release. `b`'s only blocker is thin `a`, so `b` rides THIS wave — with no
    `upstream_files` entry, because `a` has no drafted fragment to read."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": False, "confidence": "low"},
        {"slug": "b", "filled": False, "upstream": ["a"]},
    ])
    d = orchestrate.decide(area)
    assert d["details"]["unfilled"] == ["b"]
    assert d["details"]["thin"] == {"a": "low"}
    assert "deferred" not in d["details"]
    assert "upstream_files" not in d["details"]


def test_non_thin_upstream_still_defers_its_downstream(tmp_path):
    """The M11 wave is otherwise untouched: an unfilled upstream WITH
    evidence behind it still defers its downstream."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": False},
        {"slug": "b", "filled": False, "upstream": ["a"]},
        {"slug": "c", "filled": False, "upstream": ["b"], "confidence": "low"},
    ])
    d = orchestrate.decide(area)
    assert d["details"]["unfilled"] == ["a"]
    assert d["details"]["deferred"] == ["b"]
    assert d["details"]["thin"] == {"c": "low"}


def test_cycle_degradation_dispatches_only_the_non_thin(tmp_path):
    """A cycle among dispatchable nodes still degrades to dispatch-all — but
    the thin remainder is not swept into it."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": False, "upstream": ["b"]},
        {"slug": "b", "filled": False, "upstream": ["a"]},
        {"slug": "c", "filled": False, "confidence": "low"},
    ])
    d = orchestrate.decide(area)
    assert sorted(d["details"]["unfilled"]) == ["a", "b"]
    assert d["details"]["thin"] == {"c": "low"}
    assert "cycle" in d["reason"]


def test_hold_on_fill_still_works_with_thin_nodes(tmp_path):
    """Part D: the human's brake is the M17 hold. Holding `fill` on an
    all-thin remainder returns `fill` as a gate with `held_by`, details
    (thin included) intact."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": True},
        {"slug": "b", "filled": False, "confidence": "low"},
    ])
    client = os.path.join(area, "_client")
    os.makedirs(client, exist_ok=True)
    with open(os.path.join(client, "consult.yaml"), "w",
              encoding="utf-8") as fh:
        fh.write("hold:\n  - fill\n")
    d = orchestrate.decide(area)
    assert d["action"] == "fill"
    assert d["human_gate"] is True
    assert d["details"]["held_by"] == "area"
    assert d["details"]["thin"] == {"b": "low"}
    assert d["details"]["unfilled"] == []


# --------------------------------------------------------------------------- #
# scope guard — nothing disappears while a node waits
# --------------------------------------------------------------------------- #

def test_thin_node_keeps_its_manifest_component_and_skeleton(tmp_path):
    """A thin node stays a live procedure component with its file on disk —
    it waits VISIBLY."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": True},
        {"slug": "b", "filled": False, "confidence": "low"},
    ])
    with open(os.path.join(area, "manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    comp = next(c for c in manifest["components"] if c.get("slug") == "b")
    assert comp["role"] == "procedure"
    assert comp["confidence"] == "low"
    assert os.path.isfile(os.path.join(area, "10_b.md"))
    st = orchestrate.AreaState(area)
    assert "b" in dict(st.procedures)
    assert st.owner_of["10_b.md"] == "procedure"


def test_thin_node_still_reads_as_unfilled_for_downstream_guards(tmp_path):
    """The sentinel is untouched: the area is NOT `draft_ready` while a thin
    node waits, and the ladder keeps returning `fill` for it."""
    area = make_conf_area(tmp_path, [
        {"slug": "a", "filled": True},
        {"slug": "b", "filled": False, "confidence": "low"},
    ])
    st = orchestrate.AreaState(area)
    assert st.unfilled_slugs() == ["b"]
    assert orchestrate.decide(area)["action"] == "fill"
    # idempotent: the advisor is a pure function of folder state
    assert orchestrate.decide(area) == orchestrate.decide(area)


# --------------------------------------------------------------------------- #
# v1 byte-identity — confidence-free areas are untouched
# --------------------------------------------------------------------------- #

def test_confidence_free_fill_output_is_unchanged(tmp_path):
    """No `confidence` anywhere → no `thin` key, and the details/reason are
    exactly the pre-M74 shape the four pinned test modules assert."""
    area = make_area(tmp_path, [
        {"slug": "a", "filled": False},
        {"slug": "b", "filled": False, "upstream": ["a"]},
    ])
    d = orchestrate.decide(area)
    assert d["action"] == "fill"
    assert _fill_details(d) == {"unfilled": ["a"], "deferred": ["b"]}
    assert d["reason"] == ("2 procedure(s) unfilled; wave of 1 ready "
                           "(upstream filled), 1 deferred to later waves")


def test_confidence_free_flat_fill_reason_is_unchanged(tmp_path):
    """The no-upstream reason string is byte-identical too."""
    area = make_area(tmp_path, [{"slug": "a", "filled": False},
                                {"slug": "b", "filled": False}])
    d = orchestrate.decide(area)
    assert _fill_details(d) == {"unfilled": ["a", "b"]}
    assert d["reason"] == "2 procedure(s) still carry the unfilled sentinel"


def test_all_high_confidence_matches_confidence_free_output(tmp_path):
    """`high` everywhere is indistinguishable from no opinion at all."""
    plain = orchestrate.decide(make_area(
        tmp_path, [{"slug": "a", "filled": False},
                   {"slug": "b", "filled": False}], name="plain"))
    conf = orchestrate.decide(make_conf_area(
        tmp_path, [{"slug": "a", "filled": False, "confidence": "high"},
                   {"slug": "b", "filled": False, "confidence": "high"}],
        name="conf"))
    assert plain["reason"] == conf["reason"]
    assert _fill_details(plain) == _fill_details(conf)
