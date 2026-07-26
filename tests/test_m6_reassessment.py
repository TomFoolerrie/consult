"""M6 — taxonomy + registry reassessment on new sources (audit F7 + F8's workflow).

One test per bullet in docs/M6-scoping-reassessment.md "Acceptance", driven
through the REAL stages (scaffold.confirm → decide → sources.mark_processed →
reconcile) rather than synthetic folder states, because the whole finding was
that the *pass* did not converge:

  * a new source touching only drafted procedures produces notes for exactly
    those slugs, update drafters run, and the source moves to processed/
  * the same source run twice does not re-notify a procedure already updated for
    it (dedupe on the SRC- id)
  * a source touching a mix of new and existing procedures fills the new ones and
    updates the existing ones in the same pass — in either batch order
  * a source whose touched set partially fails keeps the source in new/
  * a retirement proposal enumerates inbound [[slug]] references and writes notes
    for each citing procedure; reconcile passes once those drafters run
  * the advisor never returns `taxonomy` twice for an unchanged _sources/new/
"""
import json
import os

import pytest
import yaml

import orchestrate
import reconcile
import scaffold
import sources
from notes_util import append_items, load_items_from

SYSTEMS = {"systems": [{"slug": "netsuite", "name": "NetSuite"}]}
ROLES = {"roles": [{"slug": "controller", "name": "Controller"}]}
TAXONOMY = {"taxonomy": {"categories": [{"slug": "finance",
                                         "subcategories": [{"slug": "ops"}]}]}}


def fragment(heading, extra=""):
    """A drafted fragment that passes every reconcile check (citation, control
    callout, registered consult-meta nouns) — no `unfilled` sentinel."""
    return f"""## {heading}

### A. Process Overview

The Controller reconciles the balance against the statement. (SRC-001)
{extra}

### E. Step-by-Step Procedure

#### Step 1: Export

Export the statement from the portal.

> **CONTROL — CTRL-001:** Controller signs off on the reconciliation.

```consult-meta
systems:
  - netsuite
roles:
  - controller
```
"""


# --------------------------------------------------------------------------- #
# harness: a real scaffolded area, driven through real stages
# --------------------------------------------------------------------------- #

@pytest.fixture()
def taxonomy(tmp_path):
    p = tmp_path / "taxonomy.yaml"
    p.write_text(yaml.safe_dump(TAXONOMY), encoding="utf-8")
    return p


def stage(area, procedures=None, srcs=None, notes=None, registry=False):
    """Write what `consult-taxonomy` writes: proposals under .proposed/."""
    proposed = area / "_reference" / ".proposed"
    proposed.mkdir(parents=True, exist_ok=True)
    if procedures is not None:
        (proposed / "procedures.yaml").write_text(
            yaml.safe_dump({"procedures": procedures}), encoding="utf-8")
    if srcs is not None:
        (proposed / "sources.yaml").write_text(
            yaml.safe_dump({"sources": srcs}), encoding="utf-8")
    if notes is not None:
        (proposed / "notes.yaml").write_text(
            yaml.safe_dump({"notes": notes}), encoding="utf-8")
    if registry:
        (proposed / "systems.yaml").write_text(yaml.safe_dump(SYSTEMS),
                                               encoding="utf-8")
        (proposed / "roles.yaml").write_text(yaml.safe_dump(ROLES),
                                             encoding="utf-8")
    return proposed


def drop_source(area, name, body="client words"):
    """A human dropping a file into _sources/new/."""
    f = area / "_sources" / "new" / name
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(body, encoding="utf-8")
    return f


def confirm(area, taxonomy):
    return scaffold.confirm(area, "finance", taxonomy, None, None)


def draft(area, slug, heading=None, extra=""):
    """What a `consult-drafter` first-draft pass leaves behind: prose, and the
    `unfilled` sentinel gone."""
    (area / f"10_{slug}.md").write_text(
        fragment(heading or slug.title(), extra), encoding="utf-8")


def apply_notes(area, slug, extra=""):
    """What an `apply_review` (mode: update) batch leaves behind: a revised
    fragment, and the consumed notes archived by the driver."""
    (area / f"10_{slug}.md").write_text(
        fragment(slug.title(), extra + "\n\nUpdated from the new source.\n"),
        encoding="utf-8")
    assert sources.archive_review(str(area), [slug], None) == 0


def entries(area):
    return {e["id"]: e for e in yaml.safe_load(
        (area / "_reference" / "sources.yaml").read_text(encoding="utf-8"))["sources"]}


def note_items(area, slug):
    return load_items_from(area / "_review" / f"{slug}.notes.yaml")


def initial_area(tmp_path, taxonomy, procedures, srcs, name="cash"):
    """An area scoped, scaffolded, drafted and with its first sources retired —
    the state every M6 scenario starts from."""
    area = tmp_path / "components" / name
    area.mkdir(parents=True)
    for s in srcs:
        drop_source(area, os.path.basename(s["file"]))
    stage(area, procedures=procedures, srcs=srcs, registry=True)
    assert confirm(area, taxonomy) == 0

    assert orchestrate.decide(str(area))["action"] == "fill"
    for p in procedures:
        draft(area, p["slug"], p["title"])
    assert sources.mark_processed(str(area), {p["slug"] for p in procedures}) == 0
    return area


@pytest.fixture()
def area(tmp_path, taxonomy):
    """One drafted procedure (`bank-rec`), SRC-001 retired."""
    return initial_area(
        tmp_path, taxonomy,
        [{"slug": "bank-rec", "title": "Bank Rec", "l2": "ops"}],
        [{"id": "SRC-001", "file": "_sources/new/kickoff.md",
          "touches": ["bank-rec"]}])


# --------------------------------------------------------------------------- #
# acceptance 1 — a new source touching only drafted procedures converges
# --------------------------------------------------------------------------- #

def test_new_source_on_drafted_procedures_notes_updates_and_retires(area, taxonomy,
                                                                    capsys):
    """The headline F7 loop, end to end: drop → taxonomy → confirm writes the
    note → apply_review dispatches the update drafter → the source retires.
    Before M6 this walked taxonomy → confirm → nothing → taxonomy → forever."""
    drop_source(area, "june.md")

    d = orchestrate.decide(str(area))
    assert d["action"] == "taxonomy" and d["details"]["mode"] == "incremental"
    assert d["details"]["unassessed"] == ["_sources/new/june.md"]

    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["bank-rec"]}],
          notes=[{"slug": "bank-rec", "kind": "source", "src": "SRC-002",
                  "note": "SRC-002 adds the FX revaluation step."}])
    assert orchestrate.decide(str(area))["action"] == "confirm"
    assert confirm(area, taxonomy) == 0

    # a note for exactly the touched, already-drafted slug
    assert os.listdir(area / "_review") == ["bank-rec.notes.yaml"]
    (item,) = note_items(area, "bank-rec")
    assert item == {"kind": "source", "src": "SRC-002",
                    "note": "SRC-002 adds the FX revaluation step."}

    d = orchestrate.decide(str(area))
    assert d["action"] == "apply_review"
    assert d["details"]["notes"] == [os.path.join("_review", "bank-rec.notes.yaml")]

    apply_notes(area, "bank-rec")
    assert sources.mark_processed(str(area), set()) == 0
    assert (area / "_sources" / "processed" / "june.md").is_file()
    assert not (area / "_sources" / "new" / "june.md").exists()
    assert entries(area)["SRC-002"]["state"] == "processed"
    assert entries(area)["SRC-002"]["consumed"] == ["bank-rec"]

    # and the loop is gone: no taxonomy, no apply_review, no gate
    assert orchestrate.decide(str(area))["action"] == "aggregate"
    capsys.readouterr()


def test_the_drafter_gets_the_src_id_not_a_source_list(area, taxonomy):
    """The note must carry the `SRC-` id: `apply_review`'s dispatch deliberately
    passes no `sources` list, so the id is the drafter's only route to the file
    (through sources.yaml, which maps it)."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["bank-rec"]}])
    assert confirm(area, taxonomy) == 0

    (item,) = note_items(area, "bank-rec")
    assert item["src"] == "SRC-002"          # even with no wording proposed
    assert "SRC-002" in item["note"] and "sources.yaml" in item["note"]
    assert entries(area)["SRC-002"]["file"] == "_sources/new/june.md"


# --------------------------------------------------------------------------- #
# acceptance 2 — dedupe on the SRC- id
# --------------------------------------------------------------------------- #

def test_same_source_confirmed_twice_writes_one_note(area, taxonomy):
    """Re-running the same proposal (note still pending) adds no second item —
    the notes-bus fingerprint covers `kind`/`src`."""
    drop_source(area, "june.md")
    proposal = dict(srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                           "touches": ["bank-rec"]}],
                    notes=[{"slug": "bank-rec", "kind": "source",
                            "src": "SRC-002", "note": "New FX step."}])
    stage(area, **proposal)
    assert confirm(area, taxonomy) == 0
    stage(area, **proposal)
    assert confirm(area, taxonomy) == 0
    assert len(note_items(area, "bank-rec")) == 1


def test_a_later_pass_never_renotifies_a_consumed_slug(area, taxonomy, capsys):
    """The durable half of the dedupe: once a slug has CONSUMED a source (its
    `consumed` record), a later confirm pass must not re-dispatch that drafter —
    even though the source is still outstanding for its other procedure."""
    drop_source(area, "june.md")
    stage(area, procedures=[{"slug": "fx-reval", "title": "FX Reval", "l2": "ops"}],
          srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                 "touches": ["bank-rec", "fx-reval"]}])
    assert confirm(area, taxonomy) == 0

    apply_notes(area, "bank-rec")                    # update batch succeeded
    assert sources.mark_processed(str(area), set()) == 0
    assert entries(area)["SRC-002"]["consumed"] == ["bank-rec"]
    assert entries(area)["SRC-002"]["state"] == "new"   # fx-reval still unfilled

    # a third source arrives; confirming it must not re-notify bank-rec
    drop_source(area, "july.md")
    stage(area, srcs=[{"id": "SRC-003", "file": "_sources/new/july.md",
                       "touches": ["bank-rec"]}])
    assert confirm(area, taxonomy) == 0
    out = capsys.readouterr().out
    assert "already consumed for that source: SRC-002→bank-rec" in out

    srcs_seen = {it["src"] for it in note_items(area, "bank-rec")}
    assert srcs_seen == {"SRC-003"}


# --------------------------------------------------------------------------- #
# acceptance 3 — a mixed new/existing source, in either batch order
# --------------------------------------------------------------------------- #

def test_mixed_new_and_existing_procedures_in_one_pass(area, taxonomy, capsys):
    """The new procedure fills (sentinel path, no note) and the existing one
    updates (notes path) — and the source retires only when BOTH are done."""
    drop_source(area, "june.md")
    stage(area, procedures=[{"slug": "fx-reval", "title": "FX Reval", "l2": "ops"}],
          srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                 "touches": ["bank-rec", "fx-reval"]}],
          notes=[{"slug": "bank-rec", "kind": "source", "src": "SRC-002",
                  "note": "Adds the FX revaluation hand-off."}])
    assert confirm(area, taxonomy) == 0

    # exactly one note: the freshly scaffolded slug keeps the sentinel path
    assert os.listdir(area / "_review") == ["bank-rec.notes.yaml"]
    assert "<!-- unfilled -->" in (area / "10_fx-reval.md").read_text(encoding="utf-8")
    assert "no note needed (skeleton fills instead): SRC-002→fx-reval" \
        in capsys.readouterr().out

    # notes outrank fill, so the update batch goes first
    assert orchestrate.decide(str(area))["action"] == "apply_review"
    apply_notes(area, "bank-rec")
    sources.mark_processed(str(area), set())
    assert (area / "_sources" / "new" / "june.md").is_file()      # half consumed

    d = orchestrate.decide(str(area))
    assert d["action"] == "fill" and d["details"]["unfilled"] == ["fx-reval"]
    draft(area, "fx-reval", "FX Reval")
    sources.mark_processed(str(area), {"fx-reval"})

    assert (area / "_sources" / "processed" / "june.md").is_file()
    assert entries(area)["SRC-002"]["consumed"] == ["bank-rec", "fx-reval"]
    capsys.readouterr()


def test_cross_batch_credit_works_in_the_reverse_order(area, taxonomy):
    """Whichever batch completes first: crediting the FILL first and the update
    second retires the same source. The accounting is a durable per-slug record,
    not a single batch's set."""
    drop_source(area, "june.md")
    stage(area, procedures=[{"slug": "fx-reval", "title": "FX Reval", "l2": "ops"}],
          srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                 "touches": ["bank-rec", "fx-reval"]}])
    assert confirm(area, taxonomy) == 0

    draft(area, "fx-reval", "FX Reval")
    sources.mark_processed(str(area), {"fx-reval"})
    assert entries(area)["SRC-002"]["consumed"] == ["fx-reval"]
    assert entries(area)["SRC-002"]["state"] == "new"

    apply_notes(area, "bank-rec")
    sources.mark_processed(str(area), set())
    assert entries(area)["SRC-002"]["state"] == "processed"
    assert (area / "_sources" / "processed" / "june.md").is_file()


# --------------------------------------------------------------------------- #
# acceptance 4 — a partially failed touched set keeps the source in new/
# --------------------------------------------------------------------------- #

def test_partial_failure_keeps_the_source_in_new(area, taxonomy, capsys):
    """One of two update drafters failed (its notes were not archived), so the
    source stays outstanding and the next pass re-dispatches only what remains."""
    drop_source(area, "june.md")
    stage(area, procedures=[{"slug": "fx-reval", "title": "FX Reval", "l2": "ops"}],
          srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                 "touches": ["bank-rec", "fx-reval"]}])
    assert confirm(area, taxonomy) == 0
    draft(area, "fx-reval", "FX Reval")          # fx-reval drafted...
    # ...and now a SECOND source touching both, with both already drafted
    drop_source(area, "july.md")
    stage(area, srcs=[{"id": "SRC-003", "file": "_sources/new/july.md",
                       "touches": ["bank-rec", "fx-reval"]}])
    assert confirm(area, taxonomy) == 0
    assert sorted(os.listdir(area / "_review")) == ["bank-rec.notes.yaml",
                                                    "fx-reval.notes.yaml"]

    apply_notes(area, "bank-rec")                # only one drafter succeeded
    sources.mark_processed(str(area), set())
    assert (area / "_sources" / "new" / "july.md").is_file()
    assert entries(area)["SRC-003"]["consumed"] == ["bank-rec"]
    assert orchestrate.decide(str(area))["action"] == "apply_review"   # the rest

    apply_notes(area, "fx-reval")
    sources.mark_processed(str(area), set())
    assert entries(area)["SRC-003"]["state"] == "processed"
    capsys.readouterr()


# --------------------------------------------------------------------------- #
# acceptance 5 — retirement enumerates inbound references (F8's workflow half)
# --------------------------------------------------------------------------- #

def test_retirement_notes_let_the_drafters_clean_the_references(tmp_path, taxonomy,
                                                                capsys):
    """A retirement proposal carries one `kind: retirement` note per CITING
    procedure. The fragment is never auto-deleted: the drafters remove the
    references, and reconcile passes once they have."""
    area = initial_area(
        tmp_path, taxonomy,
        [{"slug": "goods-receipt", "title": "Goods Receipt", "l2": "ops"},
         {"slug": "three-way-match", "title": "Three Way Match", "l2": "ops"}],
        [{"id": "SRC-001", "file": "_sources/new/kickoff.md",
          "touches": ["goods-receipt", "three-way-match"]}])
    draft(area, "goods-receipt", "Goods Receipt",
          extra="\nThe match is performed in [[three-way-match]].\n")
    orchestrate.emit_aggregate(str(area), warnings=[])
    assert reconcile.reconcile(str(area)) == 0        # clean before retirement

    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["goods-receipt"]}],
          notes=[{"slug": "goods-receipt", "kind": "retirement",
                  "note": "three-way-match is retired: drop the "
                          "[[three-way-match]] reference in A and describe the "
                          "check inline."}])
    assert confirm(area, taxonomy) == 0

    kinds = {it["kind"]: it for it in note_items(area, "goods-receipt")}
    assert set(kinds) == {"retirement", "source"}
    assert "three-way-match" in kinds["retirement"]["note"]
    # never auto-deleted
    assert (area / "10_three-way-match.md").is_file()
    assert any(c.get("slug") == "three-way-match" for c in json.loads(
        (area / "manifest.json").read_text(encoding="utf-8"))["components"])

    # The human accepts the retirement: manifest entry gone, fragment archived,
    # and the retired slug pulled out of every source's `touches` (leaving it
    # there makes those sources permanently unretirable — F14, and reconcile
    # says so). The dangling [[ref]] is what blocks until the drafter runs.
    man = json.loads((area / "manifest.json").read_text(encoding="utf-8"))
    man["components"] = [c for c in man["components"]
                         if c.get("slug") != "three-way-match"]
    (area / "manifest.json").write_text(json.dumps(man), encoding="utf-8")
    (area / "10_three-way-match.md").unlink()
    sfile = area / "_reference" / "sources.yaml"
    data = yaml.safe_load(sfile.read_text(encoding="utf-8"))
    for e in data["sources"]:
        e["touches"] = [t for t in (e.get("touches") or [])
                        if t != "three-way-match"]
    sfile.write_text(yaml.safe_dump(data), encoding="utf-8")
    orchestrate.emit_aggregate(str(area), warnings=[])
    assert reconcile.reconcile(str(area)) == 1
    assert "three-way-match" in capsys.readouterr().out

    # the drafter consumes the retirement note and removes the reference
    apply_notes(area, "goods-receipt")
    orchestrate.emit_aggregate(str(area), warnings=[])
    assert reconcile.reconcile(str(area)) == 0
    capsys.readouterr()


def test_retirement_note_never_retires_a_source(area, taxonomy):
    """A retirement note carries no `src:`, so consuming it credits nothing —
    the bus contract's third rule, at the workflow level."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": []}],
          notes=[{"slug": "bank-rec", "kind": "retirement",
                  "note": "drop the [[gone]] reference"}])
    assert confirm(area, taxonomy) == 0
    assert [it["kind"] for it in note_items(area, "bank-rec")] == ["retirement"]

    apply_notes(area, "bank-rec")
    sources.mark_processed(str(area), set())
    assert entries(area)["SRC-002"]["state"] == "new"


# --------------------------------------------------------------------------- #
# acceptance 6 — the advisor never returns taxonomy twice for unchanged sources
# --------------------------------------------------------------------------- #

def test_deleted_source_note_gates_naming_the_src_id(area, taxonomy):
    """The sanctioned veto is upstream (edit `touches`); a human who deletes the
    NOTE instead strands the source — and the advisor says so, naming the SRC-
    id and the fixes, rather than re-firing taxonomy forever."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["bank-rec"]}])
    assert confirm(area, taxonomy) == 0
    os.remove(area / "_review" / "bank-rec.notes.yaml")      # the veto-by-delete

    d = orchestrate.decide(str(area))
    assert d["action"] == "unresolvable"
    assert d["human_gate"] is True
    assert d["details"]["stranded_ids"] == ["SRC-002"]
    assert d["details"]["stranded_sources"][0]["file"] == "_sources/new/june.md"
    assert "SRC-002" in d["details"]["state"]
    for fix in ("re-issue", "touches", "mark-processed"):
        assert fix in d["details"]["human_action"]

    # a resting gate: repeated calls never dispatch, and never say taxonomy
    for _ in range(3):
        assert orchestrate.decide(str(area))["action"] == "unresolvable"


def test_assessed_source_awaiting_mark_processed_is_a_gate_not_taxonomy(area,
                                                                       taxonomy):
    """The other unchanged-new/ state: the notes were applied and archived but
    the driver never ran mark-processed. Still not taxonomy — and the gate names
    the command that finishes the job from the archived evidence."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["bank-rec"]}])
    assert confirm(area, taxonomy) == 0
    apply_notes(area, "bank-rec")

    assert orchestrate.decide(str(area))["action"] == "unresolvable"
    assert sources.mark_processed(str(area), set()) == 0
    assert orchestrate.decide(str(area))["action"] == "aggregate"


def test_empty_touches_source_strands_with_a_gate(area, taxonomy):
    """A source informing no procedure can never retire (mark-processed refuses
    to auto-move it), and `taxonomy` cannot help — the F14 shape, now a gate
    that names the source and points at `touches`."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": []}])
    assert confirm(area, taxonomy) == 0
    assert not (area / "_review").exists()

    d = orchestrate.decide(str(area))
    assert d["action"] == "unresolvable"
    assert d["details"]["stranded_sources"][0]["touches"] == []


def test_an_unregistered_source_is_still_real_taxonomy_work(area):
    """The discriminator's other side: `sources.yaml` does not know this file, so
    the agent has never read it and `taxonomy` genuinely can propose something."""
    drop_source(area, "june.md")
    d = orchestrate.decide(str(area))
    assert d["action"] == "taxonomy" and d["details"]["mode"] == "incremental"


def test_a_changed_source_file_is_unassessed_again(area, taxonomy):
    """Registered but EDITED: the agent has not read these bytes, so the pass
    re-opens. The hash is the discriminator, not the filename."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["bank-rec"]}])
    assert confirm(area, taxonomy) == 0
    assert orchestrate.decide(str(area))["action"] == "apply_review"

    os.remove(area / "_review" / "bank-rec.notes.yaml")
    assert orchestrate.decide(str(area))["action"] == "unresolvable"
    drop_source(area, "june.md", body="client words, revised transcript")
    d = orchestrate.decide(str(area))
    assert d["action"] == "taxonomy" and d["details"]["mode"] == "incremental"


def test_decide_stays_pure_over_the_m6_states(area, taxonomy):
    """M7's design note holds for the new guard: same folder, same answer, not
    one byte written (the assessment hashes files, it never stamps them)."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["bank-rec"]}])
    assert confirm(area, taxonomy) == 0
    os.remove(area / "_review" / "bank-rec.notes.yaml")

    def snapshot():
        out = {}
        for root, _dirs, names in os.walk(area):
            for n in names:
                p = os.path.join(root, n)
                out[os.path.relpath(p, area)] = open(p, "rb").read()
        return out

    before = snapshot()
    first = orchestrate.decide(str(area))
    assert orchestrate.decide(str(area)) == first
    assert snapshot() == before


# --------------------------------------------------------------------------- #
# the confirm gate: what the promote step accepts, and what the human controls
# --------------------------------------------------------------------------- #

def test_touches_edited_at_the_gate_vetoes_the_dispatch(area, taxonomy, capsys):
    """`touches` is the authority, the proposal's wording is not: a human who
    removes a slug from `touches` at the confirm gate cancels that drafter
    dispatch — the sanctioned veto for a source note (M6 "Veto semantics")."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": []}],                       # human trimmed it
          notes=[{"slug": "bank-rec", "kind": "source", "src": "SRC-002",
                  "note": "SRC-002 adds the FX revaluation step."}])
    assert confirm(area, taxonomy) == 0

    assert not (area / "_review").exists()
    assert "note wording dropped (not in `touches`): SRC-002→bank-rec" \
        in capsys.readouterr().out


@pytest.mark.parametrize("note,expected", [
    ({"slug": "bank-rec", "note": "x"}, "no `kind:`"),
    ({"slug": "bank-rec", "kind": "sauce", "note": "x"}, "unknown kind"),
    ({"slug": "bank-rec", "kind": "source", "note": "x"}, "no `src:`"),
    ({"slug": "bank-rec", "kind": "source", "src": "SRC-999", "note": "x"},
     "not registered"),
    ({"slug": "bank-rec", "kind": "retirement"}, "no `note:`"),
    ({"kind": "retirement", "note": "x"}, "no `slug:`"),
    ({"slug": "bank-rec", "kind": "review", "note": "x", "urgency": "high"},
     "unknown field"),
])
def test_a_malformed_proposal_note_fails_the_gate_before_promoting(
        area, taxonomy, note, expected):
    """Shape defects are fail-loud AT THE GATE, and nothing is promoted: the
    human fixes `.proposed/` and re-confirms (guard 1 keeps returning
    `confirm`), with the live folder untouched."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["bank-rec"]}],
          notes=[note])
    with pytest.raises(SystemExit) as exc:
        confirm(area, taxonomy)
    assert expected in str(exc.value)

    assert "SRC-002" not in entries(area)                 # not promoted
    assert not (area / "_review").exists()
    assert orchestrate.decide(str(area))["action"] == "confirm"


def test_a_note_for_an_unknown_slug_is_dropped_not_written(area, taxonomy, capsys):
    """Targeting is NOT fail-loud: a note naming a procedure this area does not
    carry is dropped with a warning. Writing it would create an orphan note and
    gate the ladder at `review_triage` — a worse outcome than a report line."""
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["bank-rec"]}],
          notes=[{"slug": "ghost", "kind": "retirement", "note": "x"}])
    assert confirm(area, taxonomy) == 0
    assert "dropping note for 'ghost'" in capsys.readouterr().out
    assert os.listdir(area / "_review") == ["bank-rec.notes.yaml"]


def test_initial_scaffold_writes_no_notes(tmp_path, taxonomy):
    """The initial pass creates only skeletons, so every touched slug carries the
    sentinel: no notes at all, and `fill` (which hands the drafter its whole
    tagged source list) does the work."""
    area = initial_area(
        tmp_path, taxonomy,
        [{"slug": "bank-rec", "title": "Bank Rec", "l2": "ops"},
         {"slug": "fx-reval", "title": "FX Reval", "l2": "ops"}],
        [{"id": "SRC-001", "file": "_sources/new/kickoff.md",
          "touches": ["bank-rec", "fx-reval"]}])
    assert not (area / "_review").exists()
    assert entries(area)["SRC-001"]["state"] == "processed"


def test_a_processed_source_is_never_re_notified(area, taxonomy):
    """A source already in `processed/` never produces notes on a later pass —
    the third dedupe layer (state), so re-confirming an area cannot re-dispatch
    every drafter that ever read anything."""
    drop_source(area, "july.md")
    stage(area, srcs=[{"id": "SRC-003", "file": "_sources/new/july.md",
                       "touches": ["bank-rec"]}])
    assert confirm(area, taxonomy) == 0
    assert {it["src"] for it in note_items(area, "bank-rec")} == {"SRC-003"}
    assert entries(area)["SRC-001"]["state"] == "processed"


def test_promoted_notes_ride_the_same_file_as_review_notes(area, taxonomy):
    """One bus, one file: a source note merges into a slug's existing reviewer
    notes without disturbing them (the merge that used to drop `kind`/`src`)."""
    append_items(area, "bank-rec", [{"kind": "review", "type": "comment",
                                     "note": "Who approves?", "author": "SME"}])
    drop_source(area, "june.md")
    stage(area, srcs=[{"id": "SRC-002", "file": "_sources/new/june.md",
                       "touches": ["bank-rec"]}])
    assert confirm(area, taxonomy) == 0

    items = note_items(area, "bank-rec")
    assert [it["kind"] for it in items] == ["review", "source"]
    assert items[0]["author"] == "SME"
    assert items[1]["src"] == "SRC-002"
