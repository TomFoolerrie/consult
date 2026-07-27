"""Tests for M17 build item 3 — STICKY HOLDS (needs M13's `_client/` resolution).

One test per acceptance bullet the holds own, plus the invariants the design
promises:

  * `hold: [synthesize]` → `synthesize` comes back with `human_gate: true` and
    `details.held_by`; the ACTION NAME and its reason/details are unchanged
  * an unknown name in `hold[]` fails loudly (a typo must never read as
    "nothing held")
  * naming an action that is ALREADY a stop (a gate, `done`, `error`) is a
    validation error too — the judgment call docs/M17 leaves open
  * a hold never skips, never reorders, never forces: holding a LATER action
    does not change which action the ladder returns
  * area `hold:` shadows the engagement list whole; `held_by` reports which
    layer answered
  * a hold is CONFIG, not state: identical across repeated calls, and `next`
    with a hold in force still leaves `git status` clean (advisor purity)
  * no `hold:` key anywhere → byte-identical to pre-M17 output
  * HOLDABLE_ACTIONS + GATE_ACTIONS together cover every action `decide()` can
    return, so no action can be silently unholdable
"""
import json
import os
import re
import subprocess

import pytest

import client_config
import orchestrate

from test_stage_gates import FILLED, SYSTEMS_YAML, make_area, proc, derived


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def area_with(tmp_path, hold=None, engagement_hold=None, name="cash"):
    """A one-procedure area with the two agent-owned views, plus `hold:` lists
    written at the area and/or engagement `_client/` layer."""
    folder = make_area(tmp_path, name,
                       [proc("bank-rec"),
                        derived("82_dependencies.md", "dependencies", 82),
                        derived("84_raci.md", "raci", 84)],
                       {"10_bank-rec.md": FILLED,
                        "82_dependencies.md": "## Dependencies\n\nNone.\n",
                        "84_raci.md": "## Raci\n\nNo rows.\n",
                        "_reference/systems.yaml": SYSTEMS_YAML})
    if hold is not None:
        write_hold(os.path.join(folder, "_client"), hold)
    if engagement_hold is not None:
        write_hold(os.path.join(str(tmp_path), "_client"), engagement_hold)
    return folder


def write_hold(client_dir, actions):
    os.makedirs(client_dir, exist_ok=True)
    body = "hold:\n" + "".join(f"  - {a}\n" for a in actions) if actions else "hold: []\n"
    with open(os.path.join(client_dir, "consult.yaml"), "w", encoding="utf-8") as fh:
        fh.write(body)


def at_synthesize(folder):
    """Walk the area to the point where `synthesize` is the next action: the two
    free stages, then the human's draft-ready accept."""
    orchestrate.emit_aggregate(folder, warnings=[])
    orchestrate.emit_reconcile(folder, clean=True, failing_files=[])
    assert orchestrate.decide(folder)["action"] == "draft_ready"
    orchestrate.accept_draft(folder)
    return orchestrate.decide(folder)


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True)


# --------------------------------------------------------------------------- #
# The acceptance bullets
# --------------------------------------------------------------------------- #

def test_held_action_is_the_same_action_as_a_gate(tmp_path):
    """Acceptance: `hold: [synthesize]` → `synthesize` returns with
    `human_gate: true` and `held_by`. The action name is unchanged, and so is
    everything the unheld result carried."""
    plain = at_synthesize(area_with(tmp_path / "a"))
    assert plain["action"] == "synthesize" and plain["human_gate"] is False

    d = at_synthesize(area_with(tmp_path / "b", hold=["synthesize"]))
    assert d["action"] == "synthesize"
    assert d["human_gate"] is True
    assert d["details"]["held_by"] == "area"
    # the hold ANNOTATES; it does not rewrite the work order
    assert d["reason"] == plain["reason"]
    assert d["details"]["stale_kinds"] == plain["details"]["stale_kinds"]
    assert d["details"]["pending"] == plain["details"]["pending"]


def test_engagement_level_hold_covers_the_area(tmp_path):
    """`hold:` at `components/_client/` is engagement policy: it applies to an
    area with no `_client/` of its own, and `held_by` says so."""
    d = at_synthesize(area_with(tmp_path, engagement_hold=["synthesize"]))
    assert d["action"] == "synthesize"
    assert d["human_gate"] is True
    assert d["details"]["held_by"] == "engagement"


def test_area_hold_shadows_the_engagement_list_whole(tmp_path):
    """M13 merges per top-level key with no deep merge: an area `hold:` replaces
    the engagement list entirely, so an engagement hold the area list omits is
    NOT in force."""
    folder = area_with(tmp_path, hold=["render"], engagement_hold=["synthesize"])
    d = at_synthesize(folder)
    assert d["action"] == "synthesize"
    assert d["human_gate"] is False          # the engagement hold was shadowed away
    assert "held_by" not in (d.get("details") or {})

    holds = client_config.holds(folder, orchestrate.HOLDABLE_ACTIONS,
                                orchestrate.GATE_ACTIONS)
    assert holds.actions == ["render"]
    assert holds.layer == "area"


def test_unknown_action_name_fails_loudly(tmp_path):
    """Acceptance: a typo must never read as "nothing held"."""
    folder = area_with(tmp_path, hold=["synthesise"])   # British spelling, wrong
    with pytest.raises(client_config.HoldError) as exc:
        orchestrate.decide(folder)
    assert "synthesise" in str(exc.value)
    assert "synthesize" in str(exc.value)               # the holdable vocabulary
    assert "consult.yaml" in str(exc.value)             # the file is named


def test_holding_a_gate_is_a_validation_error(tmp_path):
    """docs/M17 puts "holding a gate" out of scope and allows either reading.
    We fail loud: an inert line in a policy file reads as policy in force."""
    for name in ("review", "draft_ready", "done"):
        folder = area_with(tmp_path / name, hold=[name])
        with pytest.raises(client_config.HoldError) as exc:
            orchestrate.decide(folder)
        assert name in str(exc.value)
    assert "already a stop" in str(exc.value)


def test_a_typo_fails_on_every_lap_not_just_the_held_one(tmp_path):
    """Holds are resolved before the ladder walks, so a bad list stops an area
    that is nowhere near the held action."""
    folder = area_with(tmp_path, hold=["not-an-action"])
    # this area's next action is `aggregate`, not the held one
    with pytest.raises(client_config.HoldError):
        orchestrate.decide(folder)


# --------------------------------------------------------------------------- #
# Never skips, never reorders, never forces
# --------------------------------------------------------------------------- #

def test_holding_a_later_action_does_not_change_the_next_action(tmp_path):
    """A hold is not a filter: with `render` held, an area whose next action is
    `aggregate` still returns `aggregate`, ungated."""
    folder = area_with(tmp_path, hold=["render"])
    d = orchestrate.decide(folder)
    assert d["action"] == "aggregate"
    assert d["human_gate"] is False


def test_holding_an_earlier_action_does_not_reorder_the_ladder(tmp_path):
    """With `aggregate` held but already done, the ladder moves on: a hold
    annotates the action the ladder chose, it does not pull one forward."""
    folder = area_with(tmp_path, hold=["aggregate"])
    assert orchestrate.decide(folder)["action"] == "aggregate"
    assert orchestrate.decide(folder)["human_gate"] is True
    d = at_synthesize(folder)
    assert d["action"] == "synthesize"
    assert d["human_gate"] is False


def test_a_hold_never_forces_an_unready_stage(tmp_path):
    """`hold: [fill]` on an area with nothing unfilled produces no `fill` — the
    hold has nothing to annotate, so it is simply invisible."""
    folder = area_with(tmp_path, hold=["fill"])
    for _ in range(2):
        assert orchestrate.decide(folder)["action"] != "fill"
    assert at_synthesize(folder)["action"] == "synthesize"


# --------------------------------------------------------------------------- #
# Config, not state — and the advisor stays pure
# --------------------------------------------------------------------------- #

def test_a_hold_is_sticky_because_it_is_config(tmp_path):
    """No "clear once" verb exists: repeated calls return the same gate until the
    human edits `_client/`, and editing it releases the hold immediately."""
    folder = area_with(tmp_path, hold=["synthesize"])
    at_synthesize(folder)
    for _ in range(3):
        d = orchestrate.decide(folder)
        assert d["action"] == "synthesize" and d["human_gate"] is True

    write_hold(os.path.join(folder, "_client"), [])       # the human releases it
    d = orchestrate.decide(folder)
    assert d["action"] == "synthesize" and d["human_gate"] is False


def test_no_hold_key_anywhere_is_byte_identical_to_pre_m17(tmp_path):
    """The absent-config case: an area with a `_client/` that says nothing about
    holds decides exactly as one with no `_client/` at all."""
    bare = at_synthesize(area_with(tmp_path / "bare"))
    other = area_with(tmp_path / "other")
    os.makedirs(os.path.join(other, "_client"), exist_ok=True)
    with open(os.path.join(other, "_client", "org-chart.yaml"), "w",
              encoding="utf-8") as fh:
        fh.write("people: []\n")
    withcfg = at_synthesize(other)
    strip = lambda d: {k: v for k, v in d.items() if k != "area"}
    assert json.dumps(strip(bare), sort_keys=True) == \
        json.dumps(strip(withcfg), sort_keys=True)


def test_decide_stays_read_only_with_a_hold_in_force(tmp_path):
    """Advisor purity (M17 "Purity is preserved"): `hold:` is a file in the tree,
    so `next` under a hold writes nothing at all."""
    folder = area_with(tmp_path, hold=["synthesize", "render"])
    at_synthesize(folder)
    _git(folder, "init", "-q")
    _git(folder, "config", "user.email", "t@example.com")
    _git(folder, "config", "user.name", "T")
    _git(folder, "add", "-A")
    _git(folder, "commit", "-q", "-m", "state")
    for _ in range(3):
        assert orchestrate.main(["next", "--area", folder]) == 0
    assert _git(folder, "status", "--porcelain").stdout == ""


def test_held_action_json_carries_held_by_through_the_cli(tmp_path, capsys):
    """A driver reads `held_by` from `next --json` — the only thing it needs to
    print "held: synthesize (engagement)" and stop."""
    folder = area_with(tmp_path, engagement_hold=["synthesize"])
    at_synthesize(folder)
    capsys.readouterr()
    assert orchestrate.main(["next", "--area", folder, "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["action"] == "synthesize"
    assert payload["human_gate"] is True
    assert payload["details"]["held_by"] == "engagement"


# --------------------------------------------------------------------------- #
# The vocabulary cannot drift from the ladder
# --------------------------------------------------------------------------- #

def test_every_action_decide_can_return_is_classified():
    """HOLDABLE_ACTIONS + GATE_ACTIONS must cover every action name `decide()`
    returns. A new action missing from both would be silently unholdable AND
    silently un-nameable — the hold list would reject a legitimate name."""
    src = open(orchestrate.__file__, encoding="utf-8").read()
    body = src.split("def decide(", 1)[1].split("\ndef _write_json", 1)[0]
    returned = set(re.findall(r'result\(\s*"([a-z_]+)"', body))
    returned.add("unresolvable")            # returned via the unresolvable() helper
    classified = set(orchestrate.HOLDABLE_ACTIONS) | set(orchestrate.GATE_ACTIONS)
    assert returned <= classified, returned - classified
    assert not (set(orchestrate.HOLDABLE_ACTIONS) & set(orchestrate.GATE_ACTIONS))


def test_scalar_hold_and_blank_entries_are_tolerated():
    """The same tolerance the profile fields have: one action as a bare scalar
    is a one-item list, and duplicates collapse."""
    h = client_config.parse_holds("render", orchestrate.HOLDABLE_ACTIONS,
                                  orchestrate.GATE_ACTIONS)
    assert h.actions == ["render"]
    h = client_config.parse_holds(["render", " render ", ""],
                                  orchestrate.HOLDABLE_ACTIONS,
                                  orchestrate.GATE_ACTIONS)
    assert h.actions == ["render"]
    assert client_config.parse_holds(None, orchestrate.HOLDABLE_ACTIONS).actions == []


def test_malformed_hold_shapes_fail_loudly():
    for raw in ({"synthesize": True}, ["synthesize", 7], 3):
        with pytest.raises(client_config.HoldError):
            client_config.parse_holds(raw, orchestrate.HOLDABLE_ACTIONS,
                                      orchestrate.GATE_ACTIONS)


def test_holds_report_line():
    """The line a driver or stage prints when holds are in force."""
    assert client_config.Holds().report_line() == "holds: none"
    h = client_config.Holds(["synthesize"], "engagement")
    assert h.report_line() == "holds: synthesize (_client/ (engagement))"
