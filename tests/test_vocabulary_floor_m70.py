"""M70 gate — the last floor-only prefix readers.

M62 made the callout id grammar a function of the DECLARED prefixes
(`callouts.id_strict_re`). Three readers still held the floor-only
constant or a hand-typed alternation: aggregate's `parse_callouts`,
reconcile's `parse_procedure`, and the two inline id regexes in
aggregate/render. This module pins the rewiring: a declared new prefix
survives those paths, the hand-typed alternations are gone, and the
shipped five behave byte-identically.

docs/v2/M70-vocabulary-floor-leftovers.md is the spec.
"""

import re
from pathlib import Path

import aggregate
import callouts
import kernel
import reconcile
import render

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"

# The M62 gate's fixture vocabulary: one type declaring a new prefix.
RISK_TYPE = """\
type: risk-log

parts:
  - slug: summary
    title: Summary
    kind: prose
  - slug: issues
    title: Issues
    kind: prose

callouts:
  - {label: RISK, prefix: RSK, home: issues}
"""

RISK_FRAGMENT = """\
## Vendor Risk

### A. Summary

Concentration risk on the sole logistics vendor.

### B. Issues

> **RISK — RSK-001:** Sole-source dependency with no fallback contract.
"""

FIVE_FRAGMENT = """\
## Step

### A. Scope

Body referencing PP-01 and CTRL-02.

### F. Issues

> **PAIN POINT — PP-01:** Slow. (Severity: Low)
> - **Severity:** Low

> **CONTROL — CTRL-02:** Approval required.
"""


def _risk_vocab(tmp_path):
    """The declared {label: prefix} map of a type declaring RSK."""
    f = tmp_path / "risk-log.yaml"
    f.write_text(RISK_TYPE, encoding="utf-8")
    tdecl = kernel.load_type_file(f)
    return {c.label: c.prefix for c in tdecl.callouts}


class TestDeclaredPrefixSurvivesTheRewiredPaths:
    def test_kernel_still_parses_the_declared_prefix(self, tmp_path):
        f = tmp_path / "risk-log.yaml"
        f.write_text(RISK_TYPE, encoding="utf-8")
        tdecl = kernel.load_type_file(f)
        entity = kernel.parse_entity(RISK_FRAGMENT, tdecl, slug="vendor-risk")
        assert any(c.get("id") == "RSK-001" for c in entity.callout_dicts())

    def test_aggregate_accepts_the_declared_prefix(self, tmp_path):
        vocab = _risk_vocab(tmp_path)
        got = aggregate.parse_callouts(
            "vendor-risk", RISK_FRAGMENT, label_to_prefix=vocab)
        assert [(c["prefix"], c["id"]) for c in got] == [("RSK", "RSK-001")]

    def test_reconcile_accepts_the_declared_prefix(self, tmp_path):
        vocab = _risk_vocab(tmp_path)
        frag = reconcile.parse_procedure(
            "vendor-risk", "10_vendor-risk.md", RISK_FRAGMENT,
            label_to_prefix=vocab)
        assert "RSK-001" in frag.defined
        assert frag.errors == []

    def test_reconcile_tracks_a_declared_prefix_reference(self, tmp_path):
        vocab = _risk_vocab(tmp_path)
        text = RISK_FRAGMENT + "\nMitigation for RSK-001 is pending.\n"
        frag = reconcile.parse_procedure(
            "vendor-risk", "10_vendor-risk.md", text, label_to_prefix=vocab)
        assert "RSK-001" in frag.referenced, (
            "an id in prose must be tracked over the DECLARED vocabulary")
        assert frag.errors == []

    def test_undeclared_prefix_still_refused_by_aggregate(self, tmp_path):
        vocab = _risk_vocab(tmp_path)
        bad = RISK_FRAGMENT.replace("RSK-001", "ZZZ-001")
        try:
            aggregate.parse_callouts(
                "vendor-risk", bad, label_to_prefix=vocab)
        except aggregate.FragmentError as exc:
            assert "ZZZ-001" in str(exc)
        else:  # pragma: no cover - the refusal is the contract
            raise AssertionError("an undeclared prefix must still refuse")


class TestTheInlineAlternationsAreGone:
    #: The hand-typed shape M70 removes, in any prefix order.
    HAND_TYPED = re.compile(r"\(\?:?(?:CTRL|GAP|PP|IO|SC)\|")

    def test_no_hand_typed_alternation_in_aggregate_or_render(self):
        for name in ("aggregate.py", "render.py"):
            text = (SCRIPTS / name).read_text(encoding="utf-8")
            assert not self.HAND_TYPED.search(text), (
                f"{name} re-types the prefix vocabulary; build it from "
                "callouts instead")

    def test_the_id_regexes_are_built_from_the_vocabulary(self):
        assert aggregate._ID_MENTION_RE.pattern == \
            callouts.id_mention_re().pattern
        assert render._CALLOUT_ID_RE.pattern == \
            callouts.id_mention_re().pattern

    def test_a_declared_prefix_mention_matches(self):
        rx = callouts.id_mention_re(["RSK"])
        assert rx.findall("see RSK-001 and PP-01") == ["RSK-001", "PP-01"]


class TestShippedFiveRegression:
    def test_aggregate_parses_the_five_unchanged(self):
        got = aggregate.parse_callouts("s", FIVE_FRAGMENT)
        assert [(c["prefix"], c["id"]) for c in got] == [
            ("PP", "PP-01"), ("CTRL", "CTRL-02")]

    def test_reconcile_parses_the_five_unchanged(self):
        frag = reconcile.parse_procedure("s", "10_s.md", FIVE_FRAGMENT)
        assert sorted(frag.defined) == ["CTRL-02", "PP-01"]
        assert sorted(frag.referenced) == ["CTRL-02", "PP-01"]

    def test_mention_regex_matches_the_five_byte_identically(self):
        old = re.compile(r"\b(?:CTRL|GAP|PP|IO|SC)-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
        text = ("CTRL-1 GAP-02-A PP-3 IO-4 SC-5 RSK-006 ctrl-7 "
                "PP- X-1 CTRLX-1")
        assert callouts.id_mention_re().findall(text) == old.findall(text)
        assert aggregate._ID_MENTION_RE.findall(text) == old.findall(text)
        assert render._CALLOUT_ID_RE.findall(text) == old.findall(text)

    def test_floor_strict_grammar_unchanged(self):
        for cid in ("CTRL-01", "GAP-02-A", "PP-3", "IO-4", "SC-5"):
            assert callouts.ID_STRICT_RE.match(cid)
            assert callouts.id_strict_re().match(cid)
        for bad in ("RSK-001", "ctrl-01", "CTRL-", "CTRL_01"):
            assert not callouts.ID_STRICT_RE.match(bad)
