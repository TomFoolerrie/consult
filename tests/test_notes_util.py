"""Tests for scripts/notes_util.py — merge-append with fingerprint dedupe."""
import yaml

from notes_util import append_items, load_items

ITEM = {"type": "gap", "location": "Step 3", "note": "Who approves?",
        "author": "Reviewer", "date": "2026-01-02", "source": "workbook"}


def notes_path(area, slug):
    return area / "_review" / f"{slug}.notes.yaml"


def test_append_creates_file(tmp_path):
    """First append creates _review/<slug>.notes.yaml and returns count added."""
    assert append_items(tmp_path, "close", [ITEM]) == 1
    f = notes_path(tmp_path, "close")
    assert f.is_file()
    data = yaml.safe_load(f.read_text(encoding="utf-8"))
    assert data["procedure"] == "close"
    assert data["items"] == [{k: v for k, v in ITEM.items()}]


def test_duplicate_append_is_idempotent(tmp_path):
    """Appending the same item twice leaves exactly one entry (fingerprint dedupe)."""
    append_items(tmp_path, "close", [ITEM])
    assert append_items(tmp_path, "close", [ITEM]) == 0
    assert load_items(tmp_path, "close") == [ITEM]


def test_duplicates_within_one_call(tmp_path):
    """Duplicates inside a single new_items batch are collapsed too."""
    assert append_items(tmp_path, "close", [ITEM, dict(ITEM)]) == 1
    assert len(load_items(tmp_path, "close")) == 1


def test_merge_appends_new_items(tmp_path):
    """New distinct items merge after existing ones, preserving order."""
    other = dict(ITEM, note="Different note")
    append_items(tmp_path, "close", [ITEM])
    assert append_items(tmp_path, "close", [ITEM, other]) == 1
    items = load_items(tmp_path, "close")
    assert [it["note"] for it in items] == ["Who approves?", "Different note"]


def test_no_write_when_nothing_added(tmp_path):
    """A fully-duplicate append does not rewrite the file."""
    append_items(tmp_path, "close", [ITEM])
    before = notes_path(tmp_path, "close").read_text(encoding="utf-8")
    append_items(tmp_path, "close", [ITEM])
    assert notes_path(tmp_path, "close").read_text(encoding="utf-8") == before


def test_empty_new_items_no_file(tmp_path):
    """Appending an empty list adds nothing and creates no file."""
    assert append_items(tmp_path, "close", []) == 0
    assert not notes_path(tmp_path, "close").exists()


def test_load_items_missing_file(tmp_path):
    """load_items returns [] when the notes file does not exist."""
    assert load_items(tmp_path, "ghost") == []


def test_load_items_malformed_yaml(tmp_path):
    """Unparseable YAML loads as [] rather than raising."""
    f = notes_path(tmp_path, "bad")
    f.parent.mkdir(parents=True)
    f.write_text("items: [::", encoding="utf-8")
    assert load_items(tmp_path, "bad") == []


def test_load_items_skips_non_dicts(tmp_path):
    """Non-dict entries under items: are dropped on load."""
    f = notes_path(tmp_path, "mixed")
    f.parent.mkdir(parents=True)
    f.write_text("items:\n  - just a string\n  - {type: gap, note: ok}\n",
                 encoding="utf-8")
    assert load_items(tmp_path, "mixed") == [{"type": "gap", "note": "ok"}]


def test_emit_escapes_and_flattens(tmp_path):
    """Quotes/backslashes are escaped and newlines/tabs flattened to spaces."""
    tricky = {"type": "note", "note": 'She said "hi"\nand\tleft \\ ok'}
    append_items(tmp_path, "esc", [tricky])
    data = yaml.safe_load(notes_path(tmp_path, "esc").read_text(encoding="utf-8"))
    assert data["items"][0]["note"] == 'She said "hi" and left \\ ok'


def test_empty_values_omitted(tmp_path):
    """Keys whose value is None or '' are omitted from the emitted file."""
    append_items(tmp_path, "sparse", [{"type": "gap", "note": "x",
                                       "author": "", "date": None}])
    data = yaml.safe_load(notes_path(tmp_path, "sparse").read_text(encoding="utf-8"))
    assert data["items"] == [{"type": "gap", "note": "x"}]


def test_dedupe_ignores_unknown_keys(tmp_path):
    """Fingerprint covers only the canonical keys; extra keys don't defeat dedupe."""
    append_items(tmp_path, "close", [ITEM])
    extra = dict(ITEM, bogus="different")
    assert append_items(tmp_path, "close", [extra]) == 0
