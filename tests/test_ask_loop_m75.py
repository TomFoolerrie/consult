"""M75 acceptance tests — the ask loop, written BEFORE the build.

Pins:

  * `scripts/asks.py` — the curated request register (`_registers/asks.yaml`,
    one writer), its lifecycle (proposed -> accepted -> sent -> answered ->
    retired), the `unasked` bucket, and `renderable()` = accepted + sent;
  * the `match` verb — an answering source recorded on the ask AND on the
    ledger entry (`answers: [ASK-…]`), through the ledger module's own writer
    seam (asks.py writes exactly one file: its own);
  * the `asks:` binding verb in definitions.py, its serviceability producer,
    and the information-request definition's new LEAD view with the coverage
    and step-gap feeders DEMOTED, never dropped;
  * the needs feed, the client-asks view writer and the agenda's ask content
    — all CONDITIONAL on the register existing, so a register-less engagement
    is byte-identical to pre-M75;
  * confirm's consumption of the taxonomist's staged `.proposed/asks.yaml`
    BEFORE the step-6 rmtree, with the M65 stdout strings untouched;
  * the confirm gate's two answers (fill now / ask first + the exact hold
    edit), with NOTHING programmatic writing `_client/consult.yaml`;
  * the M74 join — a thin node with an answered, unsettled ask touching it
    re-enters the fill wave;
  * the reconcile invariant — every area gap id in the register exactly once,
    SCOPED to engagements that have a register at all;
  * the contract text: taxonomist stages, intake matches, drafter's fourth
    update trigger, and the skill's two-path confirm relay.
"""

import json
import os
import shutil
from pathlib import Path

import pytest
import yaml

import asks
import ledger

REPO = Path(__file__).resolve().parent.parent
IPO_ROOT = Path(__file__).resolve().parent / "fixtures" / "ipo-engagement"

TAXONOMIST = REPO / "agents" / "consult-taxonomist.md"
INTAKE = REPO / "agents" / "consult-intake.md"
DRAFTER = REPO / "agents" / "consult-drafter.md"
ORCH_SKILL = REPO / "skills" / "consult-orchestrate" / "SKILL.md"


def ipo_copy(tmp_path):
    dest = tmp_path / "eng"
    shutil.copytree(IPO_ROOT, dest)
    return dest, dest / "components" / "purchasing"


def fingerprint(base):
    return {p: (p.stat().st_mtime_ns, p.stat().st_size)
            for p in Path(base).rglob("*") if p.is_file()}


def an_ask(root, text="Who approves a payment run over $50k, and where is "
                      "that recorded?", gaps=("match-po:GAP-02",),
           audience="AP Manager", artifact="a short written answer"):
    return asks.propose(root, text=text, gaps=list(gaps), audience=audience,
                        artifact=artifact)


# --------------------------------------------------------------------------- #
# 1. The register — lifecycle, refusals, one writer
# --------------------------------------------------------------------------- #

class TestLifecycle:
    def test_propose_mints_an_id_and_a_proposed_entry(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        aid = an_ask(root)
        assert aid == "ASK-001"
        entry = asks.entries(root)[0]
        assert entry["status"] == asks.PROPOSED
        assert entry["gaps"] == ["match-po:GAP-02"]
        assert entry["audience"] == "AP Manager"
        assert entry["artifact"] == "a short written answer"

    def test_the_register_lives_at_the_engagement_root(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        an_ask(root)
        assert asks.asks_path(root) == root / "_registers" / "asks.yaml"
        assert asks.asks_path(root).is_file()

    def test_blank_text_refused(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        with pytest.raises(asks.AsksError):
            asks.propose(root, text="  ", gaps=["match-po:GAP-02"],
                         audience="AP", artifact="answer")
        assert not asks.asks_path(root).exists()

    def test_an_ask_with_no_gaps_is_refused(self, tmp_path):
        # the gap mapping is the whole point of the register
        root, _ = ipo_copy(tmp_path)
        with pytest.raises(asks.AsksError) as exc:
            asks.propose(root, text="Tell us everything", gaps=[],
                         audience="AP", artifact="answer")
        assert "gap" in str(exc.value).lower()

    def test_blank_audience_refused_by_name(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        with pytest.raises(asks.AsksError) as exc:
            asks.propose(root, text="Who approves?", gaps=["match-po:GAP-02"],
                         audience="", artifact="answer")
        assert "audience" in str(exc.value).lower()

    def test_the_full_lifecycle_walks(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        aid = an_ask(root)
        assert asks.accept(root, aid)["status"] == asks.ACCEPTED
        assert asks.send(root, aid)["status"] == asks.SENT
        assert asks.answer(root, aid, src_id=None)["status"] == asks.ANSWERED
        assert asks.retire(root, aid, reason="settled by the walkthrough"
                           )["status"] == asks.RETIRED

    def test_an_unaccepted_ask_cannot_be_sent(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        aid = an_ask(root)
        with pytest.raises(asks.AsksError) as exc:
            asks.send(root, aid)
        assert aid in str(exc.value)

    def test_retiring_needs_a_reason(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        aid = an_ask(root)
        asks.accept(root, aid)
        with pytest.raises(asks.AsksError):
            asks.retire(root, aid, reason="  ")

    def test_unknown_id_refused_by_name(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        an_ask(root)
        with pytest.raises(asks.AsksError) as exc:
            asks.accept(root, "ASK-404")
        assert "ASK-404" in str(exc.value)

    def test_ids_are_never_reused(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        a = an_ask(root)
        asks.accept(root, a)
        asks.retire(root, a, reason="withdrawn")
        b = an_ask(root, text="A second ask", gaps=["receive-invoice:GAP-01"])
        assert (a, b) == ("ASK-001", "ASK-002")

    def test_entries_filters_by_status_and_refuses_an_unknown_one(self,
                                                                 tmp_path):
        root, _ = ipo_copy(tmp_path)
        aid = an_ask(root)
        asks.accept(root, aid)
        assert [e["id"] for e in asks.entries(root, status=asks.ACCEPTED)] \
            == [aid]
        with pytest.raises(asks.AsksError) as exc:
            asks.entries(root, status="pondered")
        assert "pondered" in str(exc.value)

    def test_a_missing_register_reads_as_empty_not_an_error(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        assert asks.entries(root) == []
        assert asks.renderable(root) == []
        assert asks.unasked(root) == []


class TestRenderable:
    """The human gate, structurally: renderable() is accepted + sent — the
    OUTSTANDING client-facing asks. A proposal has not been through the human
    yet; an answered or retired ask is no longer a request."""

    def test_only_accepted_and_sent_render(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        proposed = an_ask(root, text="proposed one")
        accepted = an_ask(root, text="accepted one",
                          gaps=["receive-invoice:GAP-01"])
        sent = an_ask(root, text="sent one", gaps=["schedule-payment:GAP-03"])
        answered = an_ask(root, text="answered one",
                          gaps=["reconcile-statements:GAP-04"])
        asks.accept(root, accepted)
        asks.accept(root, sent)
        asks.send(root, sent)
        asks.accept(root, answered)
        asks.answer(root, answered, src_id=None)
        ids = [e["id"] for e in asks.renderable(root)]
        assert ids == [accepted, sent]
        assert proposed not in ids and answered not in ids


class TestUnasked:
    def test_a_gap_can_be_deliberately_not_asked(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        asks.unask(root, "match-po:GAP-02",
                   reason="ours to resolve, not the client's")
        entry = asks.unasked(root)[0]
        assert entry["gap"] == "match-po:GAP-02"
        assert "ours to resolve" in entry["reason"]

    def test_unasking_needs_a_reason(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        with pytest.raises(asks.AsksError):
            asks.unask(root, "match-po:GAP-02", reason="")

    def test_unasking_a_gap_an_ask_already_carries_is_refused(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        an_ask(root)
        with pytest.raises(asks.AsksError) as exc:
            asks.unask(root, "match-po:GAP-02", reason="second thoughts")
        assert "match-po:GAP-02" in str(exc.value)


class TestOneWriter:
    def test_the_module_writes_exactly_one_file(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        before = fingerprint(root)
        aid = an_ask(root)
        asks.accept(root, aid)
        asks.unask(root, "receive-invoice:GAP-01", reason="internal")
        after = fingerprint(root)
        new = set(after) - set(before)
        assert new == {asks.asks_path(root)}
        assert {p for p in before if before[p] != after.get(p)} == set()

    def test_source_carries_one_write_call(self):
        src = (REPO / "scripts" / "asks.py").read_text(encoding="utf-8")
        assert src.count("write_text(") == 1, \
            "asks.py owns exactly one write target — its own register"

    def test_reads_resolve_gaps_against_the_live_corpus(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        aid = asks.propose(root, text="Both of these",
                           gaps=["match-po:GAP-02", "nowhere:GAP-99"],
                           audience="AP Manager", artifact="a walkthrough")
        report = asks.resolve_gaps(root, aid)
        assert report["resolved"] == ["match-po:GAP-02"]
        assert report["unresolved"] == ["nowhere:GAP-99"]


# --------------------------------------------------------------------------- #
# 2. The matcher — the answer routes back
# --------------------------------------------------------------------------- #

def _route_a_source(root, name="walkthrough.md", body="AP walkthrough notes"):
    new = ledger.new_dir(root)
    new.mkdir(parents=True, exist_ok=True)
    (new / name).write_text(body, encoding="utf-8")
    return ledger.register(root, name, {"purchasing": ["match-po"]})


class TestMatch:
    def test_match_answers_the_ask_and_stamps_the_ledger(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        aid = an_ask(root)
        asks.accept(root, aid)
        sid = _route_a_source(root)
        asks.match(root, sid, [aid])
        entry = asks.entries(root)[0]
        assert entry["status"] == asks.ANSWERED
        assert entry["answered_by"] == [sid]
        led = [e for e in ledger.entries(root) if e["id"] == sid][0]
        assert led["answers"] == [aid]

    def test_match_is_idempotent(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        aid = an_ask(root)
        asks.accept(root, aid)
        sid = _route_a_source(root)
        asks.match(root, sid, [aid])
        asks.match(root, sid, [aid])
        led = [e for e in ledger.entries(root) if e["id"] == sid][0]
        assert led["answers"] == [aid]
        assert asks.entries(root)[0]["answered_by"] == [sid]

    def test_match_refuses_an_unknown_source_by_name(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        aid = an_ask(root)
        asks.accept(root, aid)
        with pytest.raises(Exception) as exc:
            asks.match(root, "SRC-999", [aid])
        assert "SRC-999" in str(exc.value)

    def test_match_refuses_an_unknown_ask_by_name_and_writes_nothing(
            self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        sid = _route_a_source(root)
        before = fingerprint(root)
        with pytest.raises(asks.AsksError) as exc:
            asks.match(root, sid, ["ASK-404"])
        assert "ASK-404" in str(exc.value)
        assert fingerprint(root) == before

    def test_the_ledger_write_goes_through_the_ledger_module(self):
        src = (REPO / "scripts" / "asks.py").read_text(encoding="utf-8")
        assert "ledger.record_answers" in src
        assert "_dump_ledger" not in src

    def test_answered_asks_join_back_to_the_nodes_they_touch(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        aid = asks.propose(root, text="the settlement ask",
                           gaps=["match-po:GAP-02", "invoice-handling"],
                           audience="AP Manager", artifact="a walkthrough")
        asks.accept(root, aid)
        sid = _route_a_source(root)
        asks.match(root, sid, [aid])
        assert asks.touched(root, status=asks.ANSWERED, unsettled=True) == \
            {"match-po", "invoice-handling"}

    def test_settling_takes_an_ask_out_of_the_join(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        aid = an_ask(root)
        asks.accept(root, aid)
        sid = _route_a_source(root)
        asks.match(root, sid, [aid])
        asks.settle(root, aid)
        assert asks.touched(root, status=asks.ANSWERED, unsettled=True) == set()

    def test_counts_report_open_and_answered(self, tmp_path):
        root, _ = ipo_copy(tmp_path)
        a = an_ask(root)
        b = an_ask(root, text="second", gaps=["receive-invoice:GAP-01"])
        asks.accept(root, a)
        asks.accept(root, b)
        sid = _route_a_source(root)
        asks.match(root, sid, [b])
        assert asks.counts(root) == {"open": 1, "answered": 1}


class TestCli:
    def test_round_trip_through_the_cli(self, tmp_path, capsys):
        root, _ = ipo_copy(tmp_path)
        assert asks.main(["propose", str(root), "--text", "Who approves?",
                          "--gap", "match-po:GAP-02", "--audience",
                          "AP Manager", "--artifact", "a written answer"]) == 0
        out = capsys.readouterr().out
        assert "ASK-001" in out
        assert asks.main(["accept", str(root), "ASK-001"]) == 0
        assert asks.main(["list", str(root)]) == 0
        assert "ASK-001" in capsys.readouterr().out

    def test_cli_refusal_is_nonzero_and_named(self, tmp_path, capsys):
        root, _ = ipo_copy(tmp_path)
        assert asks.main(["accept", str(root), "ASK-404"]) != 0
        assert "ASK-404" in capsys.readouterr().err


# --------------------------------------------------------------------------- #
# 3. The definitions language — the `asks:` verb
# --------------------------------------------------------------------------- #

class TestBindingVerb:
    def test_the_verb_is_admitted(self):
        import definitions
        assert "asks" in definitions._ALLOWED_BINDING_KEYS

    def test_status_vocabulary_matches_the_module(self):
        import definitions
        assert definitions._ALLOWED_ASK_STATUSES == set(asks.STATUSES)
        assert definitions._RENDERABLE_ASK_STATUS in asks.RENDERABLE_STATUSES

    def _defn(self, tmp_path, spec):
        path = tmp_path / "d.yaml"
        path.write_text(yaml.safe_dump({
            "deliverable": "d",
            "shape": [{"id": "b", "title": "B", "kind": "view",
                       "writer": "python", "binding": "x"}],
            "bindings": {"x": spec},
            "skin": {"format": "docx"},
        }), encoding="utf-8")
        return path

    def test_an_unknown_ask_status_is_refused(self, tmp_path):
        import definitions
        with pytest.raises(definitions.DefinitionError) as exc:
            definitions.load_definition_file(
                self._defn(tmp_path, {"asks": "pondered"}))
        assert "pondered" in str(exc.value)

    def test_a_non_renderable_status_is_refused(self, tmp_path):
        import definitions
        with pytest.raises(definitions.DefinitionError) as exc:
            definitions.load_definition_file(
                self._defn(tmp_path, {"asks": "proposed"}))
        assert "proposed" in str(exc.value)

    def test_asks_and_entities_in_one_binding_are_refused(self, tmp_path):
        import definitions
        with pytest.raises(definitions.DefinitionError):
            definitions.load_definition_file(
                self._defn(tmp_path, {"asks": "accepted",
                                      "entities": "process-step"}))


class TestInformationRequestDefinition:
    def test_the_asks_binding_leads_and_the_feeds_stay(self):
        import definitions
        d = definitions.load_definition("information-request")
        assert any("asks" in (b or {}) for b in d.bindings.values())
        # NEVER dropped — demoted only
        assert any("coverage" in (b or {}) for b in d.bindings.values())
        assert "step-gaps" in d.bindings

    def test_the_ask_view_is_the_lead_and_the_feeds_are_the_appendix(self):
        import definitions
        d = definitions.load_definition("information-request")
        order = [b.id for b in d.shape if b.kind == "view"]
        assert order.index("client-asks") < order.index("information-requests")
        assert order.index("information-requests") < \
            order.index("open-validations")

    def test_serviceability_is_an_honest_not_yet_naming_the_register(
            self, tmp_path):
        import definitions
        root, area = ipo_copy(tmp_path)
        d = definitions.load_definition("information-request", area=area)
        gaps = [r["gap"] for r in definitions.serviceability_records(d, area)]
        assert any("_registers/asks.yaml" in g and "asks" in g for g in gaps)

    def test_an_accepted_ask_serves_the_binding(self, tmp_path):
        import definitions
        root, area = ipo_copy(tmp_path)
        asks.accept(root, an_ask(root))
        d = definitions.load_definition("information-request", area=area)
        gaps = [r["gap"] for r in definitions.serviceability_records(d, area)]
        assert not any("_registers/asks.yaml" in g for g in gaps)


# --------------------------------------------------------------------------- #
# 4. The needs feed and the renders
# --------------------------------------------------------------------------- #

def write_objective(area, deliverables=("information-request",)):
    cdir = Path(area) / "_client"
    cdir.mkdir(exist_ok=True)
    (cdir / "objective.yaml").write_text(
        "objective:\n"
        "  goal: Deliver what the engagement was hired for.\n"
        "  deliverables:\n"
        + "".join(f"    - {d}\n" for d in deliverables)
        + "  cycles:\n    - procure-to-pay\n",
        encoding="utf-8")


class TestNeedsFeed:
    def test_no_register_no_ask_entries(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        assert not [e for e in needs.needs(area)
                    if e["kind"] == needs.KIND_ASK]

    def test_accepted_asks_reach_the_needs_view(self, tmp_path):
        import needs
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        aid = an_ask(root)
        asks.accept(root, aid)
        entries = [e for e in needs.needs(area, deliverable="information-request")
                   if e["kind"] == needs.KIND_ASK]
        assert len(entries) == 1
        e = entries[0]
        assert e["where"] == aid
        assert "payment run" in e["need"]
        assert e["grounds"] and any(aid in g for g in e["grounds"])

    def test_the_ask_kind_is_in_the_feed_order(self):
        import needs
        assert needs.KIND_ASK in needs.KIND_ORDER


class TestClientAsksView:
    def test_registered_in_py_builders(self):
        import aggregate
        import plan_views
        assert plan_views.ASKS_KIND in aggregate.PY_BUILDERS

    def test_empty_register_says_so_instead_of_crashing(self, tmp_path):
        import plan_views
        root, area = ipo_copy(tmp_path)
        body = plan_views.build_client_asks({"area": area})
        assert isinstance(body, str) and body.strip()

    def test_accepted_asks_render_in_the_clients_words(self, tmp_path):
        import plan_views
        root, area = ipo_copy(tmp_path)
        asks.accept(root, an_ask(root))
        body = plan_views.build_client_asks({"area": area})
        assert "payment run" in body
        assert "ASK-001" not in body       # pipeline vocabulary stays inside
        assert "AP Manager" in body

    def test_a_proposed_ask_never_renders(self, tmp_path):
        import plan_views
        root, area = ipo_copy(tmp_path)
        an_ask(root)
        body = plan_views.build_client_asks({"area": area})
        assert "payment run" not in body


class TestAgenda:
    def test_agenda_without_a_register_is_unchanged(self, tmp_path):
        import agenda
        root_a, area_a = ipo_copy(tmp_path / "a")
        write_objective(area_a)
        baseline = agenda.render(area_a, role="ap-manager").replace(
            str(root_a), "<ROOT>")
        root_b, area_b = ipo_copy(tmp_path / "b")
        write_objective(area_b)
        # the register is the only difference: b gets one, a does not
        asks.accept(root_b, an_ask(root_b))
        got = agenda.render(area_b, role="ap-manager").replace(
            str(root_b), "<ROOT>")
        assert got != baseline          # the feature is visible where it exists
        root_c, area_c = ipo_copy(tmp_path / "c")
        write_objective(area_c)
        assert agenda.render(area_c, role="ap-manager").replace(
            str(root_c), "<ROOT>") == baseline

    def test_agenda_draws_ask_text_from_the_register(self, tmp_path):
        import agenda
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        asks.accept(root, an_ask(root))
        out = agenda.render(area, role="ap-manager")
        assert "payment run" in out

    def test_agenda_and_the_request_list_share_one_source(self, tmp_path):
        # shared-source, not byte-equality: both read asks.renderable()
        import agenda
        import plan_views
        root, area = ipo_copy(tmp_path)
        write_objective(area)
        asks.accept(root, an_ask(root, text="One distinctive sentence here"))
        assert "One distinctive sentence here" in agenda.render(
            area, role="ap-manager")
        assert "One distinctive sentence here" in plan_views.build_client_asks(
            {"area": area})


# --------------------------------------------------------------------------- #
# 5. Confirm consumes the taxonomist's staging
# --------------------------------------------------------------------------- #

from test_confirm_survey_m65 import make_area as make_survey_area, NODE_A  # noqa: E402


def _stage_asks(area, entries):
    staged = Path(area) / "_reference" / ".proposed" / "asks.yaml"
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_text(yaml.safe_dump({"asks": entries}, sort_keys=False),
                      encoding="utf-8")
    return staged


STAGED = [
    {"text": "The three-way match tolerance in force today",
     "gaps": ["match-po:GAP-02"], "audience": "AP Manager",
     "artifact": "a short written answer"},
    {"text": "Where the signed reconciliations are filed",
     "gaps": ["reconcile-statements:GAP-04"], "audience": "Controller",
     "artifact": "a walkthrough"},
]


class TestConfirmConsumption:
    def test_staged_asks_land_in_the_engagement_register(self, tmp_path,
                                                         capsys):
        import scaffold
        area, taxonomy = make_survey_area(tmp_path)
        staged = _stage_asks(area, STAGED)
        assert scaffold.confirm(area, "finance", taxonomy, None, None) == 0
        root = area.parent.parent
        entries = asks.entries(root)
        assert [e["text"] for e in entries] == [s["text"] for s in STAGED]
        assert all(e["status"] == asks.PROPOSED for e in entries)
        assert not staged.exists()
        assert "promoted 2 staged ask(s) to the engagement register" \
            in capsys.readouterr().out

    def test_the_m65_lines_are_untouched(self, tmp_path, capsys):
        import scaffold
        area, taxonomy = make_survey_area(tmp_path,
                                          nodes={"cash-management": NODE_A})
        _stage_asks(area, STAGED)
        assert scaffold.confirm(area, "finance", taxonomy, None, None) == 0
        out = capsys.readouterr().out
        assert "promoted taxonomy nodes: cash-management" in out

    def test_no_staged_asks_prints_no_ask_line(self, tmp_path, capsys):
        import scaffold
        area, taxonomy = make_survey_area(tmp_path)
        assert scaffold.confirm(area, "finance", taxonomy, None, None) == 0
        assert "staged ask(s)" not in capsys.readouterr().out

    def test_a_late_failure_leaves_the_asks_staged(self, tmp_path):
        # M65 discipline: the collision refusal fires before anything moves
        import scaffold
        area, taxonomy = make_survey_area(tmp_path,
                                          nodes={"cash-management": NODE_A})
        live = scaffold.live_taxonomy_dir(area)
        live.mkdir(parents=True, exist_ok=True)
        (live / "cash-management.md").write_text("live", encoding="utf-8")
        staged = _stage_asks(area, STAGED)
        with pytest.raises(Exception):
            scaffold.confirm(area, "finance", taxonomy, None, None)
        assert staged.is_file()
        assert not asks.asks_path(area.parent.parent).exists()

    def test_a_malformed_staged_file_refuses_the_gate(self, tmp_path):
        import scaffold
        area, taxonomy = make_survey_area(tmp_path)
        staged = Path(area) / "_reference" / ".proposed" / "asks.yaml"
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_text("asks: [{gaps: [x]}]\n", encoding="utf-8")
        with pytest.raises(Exception) as exc:
            scaffold.confirm(area, "finance", taxonomy, None, None)
        assert "asks.yaml" in str(exc.value)


# --------------------------------------------------------------------------- #
# 6. The confirm gate offers the loop; nothing writes consult.yaml
# --------------------------------------------------------------------------- #

class TestConfirmGate:
    def _decide(self, area):
        import orchestrate
        return orchestrate.decide(str(area))

    def test_the_gate_carries_both_answers(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        (area / "_reference" / ".proposed").mkdir(parents=True, exist_ok=True)
        (area / "_reference" / ".proposed" / "procedures.yaml").write_text(
            "procedures: []\n", encoding="utf-8")
        d = self._decide(area)
        assert d["action"] == "confirm"
        names = [a["name"] for a in d["details"]["answers"]]
        assert names == ["fill now", "ask first"]

    def test_ask_first_hands_over_the_exact_hold_edit(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        (area / "_reference" / ".proposed").mkdir(parents=True, exist_ok=True)
        (area / "_reference" / ".proposed" / "procedures.yaml").write_text(
            "procedures: []\n", encoding="utf-8")
        d = self._decide(area)
        ask_first = d["details"]["answers"][1]
        assert "add `fill` to `hold:`" in ask_first["human_action"]
        assert "_client/consult.yaml" in ask_first["human_action"]

    def test_the_gate_sizes_the_path_from_the_register(self, tmp_path):
        root, area = ipo_copy(tmp_path)
        (area / "_reference" / ".proposed").mkdir(parents=True, exist_ok=True)
        (area / "_reference" / ".proposed" / "procedures.yaml").write_text(
            "procedures: []\n", encoding="utf-8")
        assert "asks" not in self._decide(area)["details"]
        asks.accept(root, an_ask(root))
        assert self._decide(area)["details"]["asks"] == {"open": 1,
                                                         "answered": 0}

    def test_nothing_programmatic_writes_client_yaml(self):
        import re
        bad = []
        for path in (REPO / "scripts").glob("*.py"):
            text = path.read_text(encoding="utf-8")
            for m in re.finditer(r"write_text|safe_dump|json\.dump", text):
                line_start = text.rfind("\n", 0, m.start()) + 1
                line = text[line_start:text.find("\n", m.start())]
                if "consult.yaml" in line or "_client" in line:
                    bad.append(f"{path.name}: {line.strip()}")
        assert bad == [], bad


# --------------------------------------------------------------------------- #
# 7. The M74 join — an answered ask releases a thin node
# --------------------------------------------------------------------------- #

from test_orchestrate import make_area, UNFILLED_BODY  # noqa: E402


def make_eng_area(tmp_path, procs, name="treasury"):
    """A confidence-carrying area INSIDE an engagement tree, so the engagement
    root (and its ask register) is derivable."""
    comp = tmp_path / "eng" / "components"
    comp.mkdir(parents=True, exist_ok=True)
    folder = make_area(comp, procs, name=name)
    path = os.path.join(folder, "manifest.json")
    with open(path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    conf = {p["slug"]: p["confidence"] for p in procs if p.get("confidence")}
    for c in manifest["components"]:
        if c.get("slug") in conf:
            c["confidence"] = conf[c["slug"]]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh)
    return tmp_path / "eng", folder


class TestThinRelease:
    PROCS = [{"slug": "a", "filled": False, "confidence": "low"},
             {"slug": "b", "filled": False}]

    def _fill(self, folder):
        import orchestrate
        return orchestrate.decide(folder)

    def test_m74_behaviour_stands_without_a_register(self, tmp_path):
        root, folder = make_eng_area(tmp_path, self.PROCS)
        d = self._fill(folder)
        assert d["action"] == "fill"
        assert d["details"]["thin"] == {"a": "low"}
        assert d["details"]["unfilled"] == ["b"]

    def test_an_answered_unsettled_ask_releases_the_thin_node(self, tmp_path):
        root, folder = make_eng_area(tmp_path, self.PROCS)
        aid = asks.propose(root, text="the missing evidence for a",
                           gaps=["a:GAP-01"], audience="Treasury",
                           artifact="a walkthrough")
        asks.accept(root, aid)
        asks.answer(root, aid, src_id=None)
        d = self._fill(folder)
        assert d["action"] == "fill"
        assert "thin" not in d["details"]
        assert sorted(d["details"]["unfilled"]) == ["a", "b"]

    def test_an_open_ask_does_not_release_it(self, tmp_path):
        root, folder = make_eng_area(tmp_path, self.PROCS)
        aid = asks.propose(root, text="still open", gaps=["a:GAP-01"],
                           audience="Treasury", artifact="a walkthrough")
        asks.accept(root, aid)
        d = self._fill(folder)
        assert d["details"]["thin"] == {"a": "low"}

    def test_a_settled_ask_does_not_release_it(self, tmp_path):
        root, folder = make_eng_area(tmp_path, self.PROCS)
        aid = asks.propose(root, text="already worked through",
                           gaps=["a:GAP-01"], audience="Treasury",
                           artifact="a walkthrough")
        asks.accept(root, aid)
        asks.answer(root, aid, src_id=None)
        asks.settle(root, aid)
        d = self._fill(folder)
        assert d["details"]["thin"] == {"a": "low"}


# --------------------------------------------------------------------------- #
# 8. The reconcile invariant — scoped to engagements that have a register
# --------------------------------------------------------------------------- #

class TestReconcileInvariant:
    def _run(self, area, capsys):
        import reconcile
        code = reconcile.reconcile(str(area))
        return code, capsys.readouterr().out

    ALL_GAPS = ["receive-invoice:GAP-01", "match-po:GAP-02",
                "schedule-payment:GAP-03", "reconcile-statements:GAP-04",
                "invoice-handling:GAP-05"]

    def test_silent_without_a_register(self, tmp_path, capsys):
        root, area = ipo_copy(tmp_path)
        code, out = self._run(area, capsys)
        assert "asks register" not in out

    def test_an_uncovered_gap_is_an_error_naming_it(self, tmp_path, capsys):
        root, area = ipo_copy(tmp_path)
        asks.propose(root, text="one", gaps=self.ALL_GAPS[:-1],
                     audience="AP", artifact="answer")
        code, out = self._run(area, capsys)
        assert code != 0
        assert "invoice-handling:GAP-05" in out

    def test_full_coverage_across_asks_and_unasked_passes(self, tmp_path,
                                                          capsys):
        root, area = ipo_copy(tmp_path)
        asks.propose(root, text="one", gaps=self.ALL_GAPS[:3],
                     audience="AP", artifact="answer")
        for gap in self.ALL_GAPS[3:]:
            asks.unask(root, gap, reason="ours to resolve, not the client's")
        code, out = self._run(area, capsys)
        assert "asks register" not in out

    def test_a_gap_in_two_asks_is_an_error(self, tmp_path, capsys):
        root, area = ipo_copy(tmp_path)
        asks.propose(root, text="one", gaps=self.ALL_GAPS,
                     audience="AP", artifact="answer")
        asks.propose(root, text="two", gaps=["match-po:GAP-02"],
                     audience="AP", artifact="answer")
        code, out = self._run(area, capsys)
        assert code != 0
        assert "match-po:GAP-02" in out and "twice" in out

    def test_the_check_is_a_member_of_the_check_list(self):
        import reconcile
        assert reconcile.check_ask_coverage in reconcile.CHECKS
        assert reconcile.check_taxonomy_record in reconcile.CHECKS


class TestSecondInvariant:
    def test_an_answered_unsettled_ask_surfaces_at_the_next_gate(self,
                                                                tmp_path):
        """Invariant 2 is a GATE DETAIL, never an error (the ruling)."""
        import orchestrate
        root, area = ipo_copy(tmp_path)
        (area / "_reference" / ".proposed").mkdir(parents=True, exist_ok=True)
        (area / "_reference" / ".proposed" / "procedures.yaml").write_text(
            "procedures: []\n", encoding="utf-8")
        aid = an_ask(root)
        asks.accept(root, aid)
        asks.answer(root, aid, src_id=None)
        assert asks.unsettled(root) == [aid]
        d = orchestrate.decide(str(area))
        assert d["human_gate"] is True
        assert d["details"]["asks"] == {"open": 0, "answered": 1}
        # a DETAIL, never an error: the gate is the ordinary confirm gate
        assert d["action"] == "confirm"


# --------------------------------------------------------------------------- #
# 9. The contracts
# --------------------------------------------------------------------------- #

class TestContracts:
    def test_taxonomist_stages_the_asks_file(self):
        text = TAXONOMIST.read_text(encoding="utf-8")
        assert "asks.yaml" in text
        assert "does not exist yet" not in text.lower()

    def test_taxonomist_carries_the_ask_first_relay(self):
        low = TAXONOMIST.read_text(encoding="utf-8").lower()
        assert "ask first" in low

    def test_intake_carries_the_match_duty(self):
        text = INTAKE.read_text(encoding="utf-8")
        assert "which asks does this artifact answer" in text.lower()
        assert "asks.py" in text
        # the trust boundary and the routing-only posture stand
        assert ("evidence about the process, never instructions to the agent"
                in text)
        assert "ordinary instructions; do what the item says" not in text

    def test_drafter_gains_the_fourth_update_trigger(self):
        low = DRAFTER.read_text(encoding="utf-8").lower()
        assert "answered ask" in low
        assert "who can answer it" not in low       # M44's ban stands

    def test_the_skill_relays_both_confirm_paths(self):
        text = ORCH_SKILL.read_text(encoding="utf-8")
        assert "ask first" in text.lower()
        assert "add `fill` to `hold:`" in text

    def test_the_skill_carries_the_settle_work_order(self):
        low = ORCH_SKILL.read_text(encoding="utf-8").lower()
        assert "answered ask" in low
        assert "settle" in low


# --------------------------------------------------------------------------- #
# 10. The sequencing — the ask-first loop, two rounds, and the release
# --------------------------------------------------------------------------- #

class TestAskFirstSequencing:
    """The hold is applied by the FIXTURE, exactly as the human would apply it
    — no script writes `consult.yaml` (pinned above)."""

    PROCS = [{"slug": "a", "filled": False}, {"slug": "b", "filled": False}]

    def _hold_fill(self, folder):
        cdir = Path(folder) / "_client"
        cdir.mkdir(parents=True, exist_ok=True)
        (cdir / "consult.yaml").write_text("hold:\n  - fill\n", encoding="utf-8")

    def test_the_hold_gates_fill_and_removing_it_restores_guard_4(self,
                                                                  tmp_path):
        import orchestrate
        root, folder = make_eng_area(tmp_path, self.PROCS)
        unheld = orchestrate.decide(folder)
        assert unheld["action"] == "fill" and unheld["human_gate"] is False

        self._hold_fill(folder)
        held = orchestrate.decide(folder)
        assert held["action"] == "fill"          # same action, now a stop
        assert held["human_gate"] is True
        assert held["details"]["held_by"]

        os.remove(os.path.join(folder, "_client", "consult.yaml"))
        back = orchestrate.decide(folder)
        assert back == unheld                    # guard 4 exactly as today

    def test_two_rounds_of_the_loop_refresh_the_register(self, tmp_path):
        """route -> curation -> updated register -> re-render, twice: the
        request list is re-derived from the register each round, and the
        round-2 ask is in it while the answered round-1 ask is not."""
        import plan_views
        root, area = ipo_copy(tmp_path)
        self._hold_fill(area)

        # round 1 — the taxonomist's curation is accepted and rendered
        first = an_ask(root, text="Round one: the match tolerance",
                       gaps=["match-po:GAP-02"])
        asks.accept(root, first)
        body = plan_views.build_client_asks({"area": area})
        assert "Round one" in body

        # the client answers: a file lands, route mints the id, intake matches
        sid = _route_a_source(root, name="tolerance-memo.md")
        asks.match(root, sid, [first])

        # round 2 — the curation pass adds what the answer opened up
        second = an_ask(root, text="Round two: who may override the tolerance",
                        gaps=["receive-invoice:GAP-01"])
        asks.accept(root, second)
        body = plan_views.build_client_asks({"area": area})
        assert "Round two" in body
        assert "Round one" not in body           # answered, no longer a request
        assert asks.counts(root) == {"open": 1, "answered": 1}

    def test_the_loop_never_writes_the_hold_file(self, tmp_path):
        import orchestrate
        root, folder = make_eng_area(tmp_path, self.PROCS)
        self._hold_fill(folder)
        before = fingerprint(folder)
        orchestrate.decide(folder)
        orchestrate.decide(folder)
        assert fingerprint(folder) == before
