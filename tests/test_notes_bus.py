"""The M6 notes-bus contract — `_review/{slug}.notes.yaml` as a five-producer bus.

One test per bullet in docs/M6-scoping-reassessment.md "Additional acceptance
(bus contract)", plus the rules the bullets rest on:

  * every item carries `kind:`; a kind-less item fails loud at load AND at append
  * `kind: source` items carry `src:`; without it the item can never retire its
    source, so it is a defect, not a warning
  * two producers appending to one slug's file lose no fields — `kind` and `src`
    survive the merge (the pre-M6 `_emit` silently dropped every field outside
    its fixed tuple)
  * an unknown field is a loud error rather than a silent drop
  * a reviewer-comment update on a procedure a source touches does NOT move that
    source to `processed/` (kind-blind accounting is the failure this forbids)
"""
import pytest
import yaml

import notes_util
import sources
from notes_util import KINDS, NotesError, append_items, load_items

SOURCE_ITEM = {"kind": "source", "src": "SRC-007",
               "note": "SRC-007 adds the FX revaluation step."}
REVIEW_ITEM = {"kind": "review", "type": "comment", "location": "Step 3",
               "anchor": "Compare balances", "note": "Who approves this?",
               "author": "SME", "date": "2026-07-01", "source": "reviewed.docx"}


def notes_file(area, slug):
    return area / "_review" / f"{slug}.notes.yaml"


def write_raw(area, slug, body):
    f = notes_file(area, slug)
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(body, encoding="utf-8")
    return f


# --------------------------------------------------------------------------- #
# rule 1 — every item carries a kind, and there is no default
# --------------------------------------------------------------------------- #

def test_kindless_item_fails_loud_at_load(tmp_path):
    """A note item without `kind:` is a loud error at LOAD — the bullet exactly.
    Silently defaulting to `review` would strand a source; defaulting to
    `source` would retire one no drafter read."""
    write_raw(tmp_path, "close", "items:\n  - type: comment\n    note: hi\n")
    with pytest.raises(NotesError) as exc:
        load_items(tmp_path, "close")
    assert "kind" in str(exc.value) and "no default" in str(exc.value)


def test_kindless_item_fails_loud_at_append(tmp_path):
    """...and at APPEND, before anything is written: a producer that forgets its
    stamp cannot leave a half-written queue behind."""
    with pytest.raises(NotesError):
        append_items(tmp_path, "close", [{"type": "comment", "note": "hi"}])
    assert not notes_file(tmp_path, "close").exists()


def test_unknown_kind_is_loud(tmp_path):
    """Only the five producers' kinds exist; a typo is not a sixth producer."""
    with pytest.raises(NotesError) as exc:
        append_items(tmp_path, "close", [{"kind": "sauce", "note": "x"}])
    assert "unknown kind" in str(exc.value)


@pytest.mark.parametrize("kind", KINDS)
def test_every_declared_kind_round_trips(tmp_path, kind):
    """All five kinds are accepted and survive a load — the bus is ready for the
    producers that do not exist yet (M12 consolidation, M20 rename)."""
    item = {"kind": kind, "note": "a finding"}
    if kind == "source":
        item["src"] = "SRC-001"
    assert append_items(tmp_path, "close", [item]) == 1
    assert load_items(tmp_path, "close") == [item]


# --------------------------------------------------------------------------- #
# rule 1b — source items carry their SRC- id
# --------------------------------------------------------------------------- #

def test_source_item_without_src_is_loud(tmp_path):
    """`kind: source` with no `src:` can never credit its source, so the source
    could never retire — a defect at the moment it is written."""
    with pytest.raises(NotesError) as exc:
        append_items(tmp_path, "close", [{"kind": "source", "note": "new stuff"}])
    assert "src" in str(exc.value)


def test_non_source_kinds_need_no_src(tmp_path):
    """Only source items need one: a retirement note names no source, and must
    not be forced to invent one."""
    assert append_items(tmp_path, "close",
                        [{"kind": "retirement", "note": "drop the ref"}]) == 1


# --------------------------------------------------------------------------- #
# rule 2 — the field set is closed and preserved
# --------------------------------------------------------------------------- #

def test_two_producers_merge_without_losing_fields(tmp_path):
    """The bullet: two producers appending to one slug's notes lose no fields —
    `kind:` and `src:` survive the merge. Pre-M6 `_emit` wrote only its fixed
    tuple, so the second append silently deleted the first item's kind/src."""
    assert append_items(tmp_path, "bank-rec", [SOURCE_ITEM]) == 1
    assert append_items(tmp_path, "bank-rec", [REVIEW_ITEM]) == 1

    on_disk = yaml.safe_load(notes_file(tmp_path, "bank-rec")
                             .read_text(encoding="utf-8"))
    assert on_disk["items"] == [SOURCE_ITEM, REVIEW_ITEM]
    assert on_disk["items"][0]["src"] == "SRC-007"
    assert [it["kind"] for it in on_disk["items"]] == ["source", "review"]


def test_unknown_field_is_a_loud_error(tmp_path):
    """M6 rule 2's second half: an unknown field is an ERROR, not a silent drop.
    A silent drop is what would have eaten `kind` and `src` on merge."""
    with pytest.raises(NotesError) as exc:
        append_items(tmp_path, "close", [dict(REVIEW_ITEM, priority="high")])
    assert "priority" in str(exc.value)


def test_kind_and_src_participate_in_dedupe(tmp_path):
    """Two source notes for the same slug from DIFFERENT sources are two items,
    and re-running one source's note adds nothing."""
    append_items(tmp_path, "bank-rec", [SOURCE_ITEM])
    other = dict(SOURCE_ITEM, src="SRC-008")
    assert append_items(tmp_path, "bank-rec", [other]) == 1
    assert append_items(tmp_path, "bank-rec", [SOURCE_ITEM, other]) == 0
    assert len(load_items(tmp_path, "bank-rec")) == 2


# --------------------------------------------------------------------------- #
# rule 3 — retirement counts only source-kind consumption
# --------------------------------------------------------------------------- #

def make_area(tmp_path, touches, id="SRC-007"):
    area = tmp_path / "area"
    (area / "_sources" / "new").mkdir(parents=True)
    (area / "_reference").mkdir(parents=True)
    (area / "_sources" / "new" / "june.md").write_text("client words",
                                                       encoding="utf-8")
    (area / "_reference" / "sources.yaml").write_text(yaml.safe_dump({
        "sources": [{"id": id, "file": "_sources/new/june.md",
                     "touches": list(touches), "state": "new"}]}),
        encoding="utf-8")
    return area


def archive(area, slug, items):
    """What the driver does after a successful apply_review batch."""
    append_items(area, slug, items)
    assert sources.archive_review(str(area), [slug], None) == 0


def read_entry(area):
    return yaml.safe_load((area / "_reference" / "sources.yaml")
                          .read_text(encoding="utf-8"))["sources"][0]


def test_reviewer_comment_update_does_not_move_the_source(tmp_path, capsys):
    """THE bullet: a reviewer-comment update on a procedure a source touches
    does not retire that source. Counting every successful update slug would
    lose client material silently — the worst failure class here."""
    area = make_area(tmp_path, ["bank-rec"])
    archive(area, "bank-rec", [REVIEW_ITEM])

    assert sources.mark_processed(str(area), set()) == 0
    assert (area / "_sources" / "new" / "june.md").is_file()
    entry = read_entry(area)
    assert entry["state"] == "new"
    assert "consumed" not in entry
    assert "kept 1 source(s)" in capsys.readouterr().out


def test_source_note_consumption_does_move_the_source(tmp_path):
    """The same shape with `kind: source` + a matching `src:` retires it — the
    contrast that makes the test above meaningful."""
    area = make_area(tmp_path, ["bank-rec"])
    archive(area, "bank-rec", [SOURCE_ITEM])

    assert sources.mark_processed(str(area), set()) == 0
    assert (area / "_sources" / "processed" / "june.md").is_file()
    entry = read_entry(area)
    assert entry["state"] == "processed"
    assert entry["consumed"] == ["bank-rec"]


def test_source_note_for_a_different_src_credits_nothing(tmp_path):
    """`src:` is matched, not merely present: a note carrying SRC-008 cannot
    retire SRC-007."""
    area = make_area(tmp_path, ["bank-rec"], id="SRC-007")
    archive(area, "bank-rec", [dict(SOURCE_ITEM, src="SRC-008")])

    sources.mark_processed(str(area), set())
    assert read_entry(area)["state"] == "new"


def test_pending_note_is_not_consumption(tmp_path):
    """A live (un-archived) note is QUEUED work, not consumed work: crediting it
    would retire the source before any drafter ran."""
    area = make_area(tmp_path, ["bank-rec"])
    append_items(area, "bank-rec", [SOURCE_ITEM])      # never archived

    sources.mark_processed(str(area), set())
    assert read_entry(area)["state"] == "new"

    # ...unless the driver explicitly asserts the batch succeeded first
    sources.mark_processed(str(area), set(), {"bank-rec"})
    assert read_entry(area)["state"] == "processed"


def test_malformed_note_on_the_bus_fails_mark_processed_loudly(tmp_path, capsys):
    """A hand-broken note is a defect at the gate that reads it: nothing moves,
    exit 1, the file and item named."""
    area = make_area(tmp_path, ["bank-rec"])
    proc_dir = area / "_review" / "processed"
    proc_dir.mkdir(parents=True)
    (proc_dir / "bank-rec.notes.yaml").write_text(
        "items:\n  - note: no kind here\n", encoding="utf-8")

    assert sources.mark_processed(str(area), set()) == 1
    assert (area / "_sources" / "new" / "june.md").is_file()
    assert "bank-rec.notes.yaml" in capsys.readouterr().err


def test_a_malformed_note_retires_nothing_at_all(tmp_path, capsys):
    """The loud failure is atomic: every note is read BEFORE anything moves, so a
    defect on the second source cannot leave the first one half-retired (file
    moved, `state` still `new`)."""
    area = tmp_path / "area"
    (area / "_sources" / "new").mkdir(parents=True)
    (area / "_reference").mkdir(parents=True)
    for name in ("a.md", "b.md"):
        (area / "_sources" / "new" / name).write_text("words", encoding="utf-8")
    (area / "_reference" / "sources.yaml").write_text(yaml.safe_dump({"sources": [
        {"id": "SRC-001", "file": "_sources/new/a.md", "touches": ["good"],
         "state": "new"},
        {"id": "SRC-002", "file": "_sources/new/b.md", "touches": ["broken"],
         "state": "new"}]}), encoding="utf-8")
    archive(area, "good", [dict(SOURCE_ITEM, src="SRC-001")])
    proc_dir = area / "_review" / "processed"
    (proc_dir / "broken.notes.yaml").write_text("items:\n  - note: no kind\n",
                                                encoding="utf-8")

    assert sources.mark_processed(str(area), set()) == 1
    assert (area / "_sources" / "new" / "a.md").is_file()
    assert not (area / "_sources" / "processed").exists()
    assert all(e["state"] == "new" for e in yaml.safe_load(
        (area / "_reference" / "sources.yaml").read_text(encoding="utf-8"))["sources"])
    assert "broken.notes.yaml" in capsys.readouterr().err


def test_note_src_ids_reads_only_source_kind(tmp_path):
    """The join sources.py owns, directly: only `kind: source` items contribute,
    and the archive is the evidence."""
    area = make_area(tmp_path, ["bank-rec"])
    archive(area, "bank-rec", [REVIEW_ITEM, SOURCE_ITEM,
                               {"kind": "retirement", "note": "x"}])
    assert sources.note_src_ids(str(area), "bank-rec") == {"SRC-007"}
    assert sources.note_src_ids(str(area), "ghost") == set()


def test_producers_share_one_validator(tmp_path):
    """notes_util is the single implementation: the same item is judged
    identically whether a producer appends it or a reader loads it."""
    write_raw(tmp_path, "close", "items:\n  - kind: source\n    note: x\n")
    with pytest.raises(NotesError):
        load_items(tmp_path, "close")
    with pytest.raises(NotesError):
        notes_util.validate_item({"kind": "source", "note": "x"})
