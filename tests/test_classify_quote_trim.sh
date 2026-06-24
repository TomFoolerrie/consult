#!/usr/bin/env bash
# =============================================================================
# test_classify_quote_trim.sh — T55 Phase 1 (quote trim) tests.
#
# Phase 1 drops the redundant `quote` field from the classifier emit contract:
# evidence is carried by `ref` + a concise `note`. `quote` stays PERMITTED in
# the schema (back-compat) but discouraged. These tests pin the four T55
# behaviours:
#
#   1. Trim (note-bearing): an artifact with ref+note and NO quote validates and
#      merges to a STATE-side evidence entry byte-identical to the pre-trim
#      (ref+note+quote) form.
#   2. Trim (quote-only edge): an evidence row with quote but NO note merges
#      note-less after the trim (the note->quote fallback has nothing to fall
#      back to once quote is gone from the emit; here we assert the NON-identical
#      outcome vs a note-bearing row).
#   3. Back-compat: a legacy quote-bearing artifact still SCHEMA-validates.
#   4. Enum trap: process:machine still FAILS validate_artifact.py (cross-field
#      gate not loosened).
#
# Uses __t55p1__ scratch engagements, removed on exit. No git commit.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
SM="scripts/state_machine.py"
MERGE="scripts/classify_merge.py"
VALIDATE="scripts/validate_artifact.py"

NODE_A="record-to-report.close"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }
assert_eq() { if [ "$1" = "$2" ]; then ok "$3 (=$2)"; else bad "$3 (expected [$1], got [$2])"; fi; }

EIDS=()
cleanup() { for e in "${EIDS[@]:-}"; do rm -rf "engagements/$e"; done; }
trap cleanup EXIT

new_eng() {
  local eid="$1"
  EIDS+=("$eid")
  rm -rf "engagements/$eid"
  "$PY" "$SM" init --engagement "$eid" --region NA >/dev/null
  mkdir -p "engagements/$eid/ingested"
  "$PY" - "engagements/$eid/ingested/doc.md" <<'PY'
import sys
with open(sys.argv[1], "w") as f:
    for i in range(1, 41):
        f.write(f"line {i}\n")
PY
}

write_artifact() { # $1 eid  $2 name  (JSON on stdin)
  local eid="$1" name="$2"
  mkdir -p "engagements/$eid/classify"
  cat > "engagements/$eid/classify/$name.artifact.json"
}

# Emit the evidence array of NODE_A as canonical JSON (sorted keys), dropping
# state-side timestamps so two runs are comparable byte-for-byte.
node_evidence() { # $1 eid
  "$PY" - "engagements/$1/state.json" "$NODE_A" <<'PY'
import json, sys
st = json.load(open(sys.argv[1]))
nodes = st.get("nodes", st)
node = nodes.get(sys.argv[2], {})
print(json.dumps(node.get("evidence", []), sort_keys=True))
PY
}

echo "T55 Phase 1 quote-trim tests"

# -----------------------------------------------------------------------------
# TEST 1 — trim (note-bearing): ref+note (no quote) merges STATE-identical to
#          the pre-trim ref+note+quote form.
# -----------------------------------------------------------------------------
echo "--- TEST 1: ref+note (no quote) merges state-identical to ref+note+quote ---"
# (a) pre-trim form: ref + note + quote.
EID="__t55p1_pretrim__"
new_eng "$EID"
write_artifact "$EID" doc <<JSON
{
  "doc": { "source": "ingested/doc.md", "doc_type": "transcript", "classified_at": "2026-06-21T00:00:00Z" },
  "node_hits": [
    { "node": "$NODE_A", "confidence": "high",
      "evidence": [ { "ref": "ingested/doc.md#L10-12", "quote": "verbatim source text here", "note": "Close sequence + accrual pain." } ] }
  ]
}
JSON
"$PY" "$VALIDATE" validate --artifact "engagements/$EID/classify/doc.artifact.json" --engagement "$EID" >/dev/null \
  || bad "pre-trim (quote+note) artifact failed validate"
"$PY" "$MERGE" merge --engagement "$EID" >/dev/null || bad "pre-trim merge errored"
EV_PRETRIM="$(node_evidence "$EID")"

# (b) trimmed form: ref + note, NO quote.
EID="__t55p1_trim__"
new_eng "$EID"
write_artifact "$EID" doc <<JSON
{
  "doc": { "source": "ingested/doc.md", "doc_type": "transcript", "classified_at": "2026-06-21T00:00:00Z" },
  "node_hits": [
    { "node": "$NODE_A", "confidence": "high",
      "evidence": [ { "ref": "ingested/doc.md#L10-12", "note": "Close sequence + accrual pain." } ] }
  ]
}
JSON
"$PY" "$VALIDATE" validate --artifact "engagements/$EID/classify/doc.artifact.json" --engagement "$EID" >/dev/null \
  || bad "trimmed (ref+note, no quote) artifact failed validate"
"$PY" "$MERGE" merge --engagement "$EID" >/dev/null || bad "trimmed merge errored"
EV_TRIM="$(node_evidence "$EID")"

assert_eq "$EV_PRETRIM" "$EV_TRIM" "state-side evidence byte-identical with/without quote (note present)"

# -----------------------------------------------------------------------------
# TEST 2 — trim (quote-only edge): a row with quote but NO note merges note-less
#          once you trim quote out of the emit. We assert the trimmed (quote
#          removed, no note) row produces a NON-identical, note-less state entry
#          vs the note-bearing row from TEST 1.
# -----------------------------------------------------------------------------
echo "--- TEST 2: quote-only-no-note row merges note-less after trim ---"
EID="__t55p1_quoteonly__"
new_eng "$EID"
# Post-trim, the model would emit neither quote nor note -> ref only.
write_artifact "$EID" doc <<JSON
{
  "doc": { "source": "ingested/doc.md", "doc_type": "transcript", "classified_at": "2026-06-21T00:00:00Z" },
  "node_hits": [
    { "node": "$NODE_A", "confidence": "high",
      "evidence": [ { "ref": "ingested/doc.md#L10-12" } ] }
  ]
}
JSON
"$PY" "$MERGE" merge --engagement "$EID" >/dev/null || bad "quote-only/trimmed merge errored"
EV_NOTELESS="$(node_evidence "$EID")"
# It must NOT equal the note-bearing entry (no gloss carried).
if [ "$EV_NOTELESS" != "$EV_PRETRIM" ]; then
  ok "note-less row is non-identical to note-bearing row (no gloss carried)"
else
  bad "note-less row unexpectedly identical to note-bearing row"
fi
# And concretely: the state entry carries NO note key.
HAS_NOTE="$(echo "$EV_NOTELESS" | "$PY" -c 'import json,sys; ev=json.load(sys.stdin); print("yes" if ev and "note" in ev[0] else "no")')"
assert_eq "no" "$HAS_NOTE" "note-less row stores no note on state"

# -----------------------------------------------------------------------------
# TEST 3 — back-compat: a legacy quote-bearing (quote, NO note) artifact still
#          SCHEMA-validates after Phase 1 (quote stays declared in the schema).
# -----------------------------------------------------------------------------
echo "--- TEST 3: legacy quote-bearing artifact still schema-validates ---"
EID="__t55p1_legacy__"
new_eng "$EID"
write_artifact "$EID" doc <<JSON
{
  "doc": { "source": "ingested/doc.md", "doc_type": "transcript", "classified_at": "2026-06-21T00:00:00Z" },
  "node_hits": [
    { "node": "$NODE_A", "confidence": "high",
      "evidence": [ { "ref": "ingested/doc.md#L10-12", "quote": "legacy verbatim quote, no note field" } ] }
  ]
}
JSON
OUT3="$("$PY" "$VALIDATE" validate --artifact "engagements/$EID/classify/doc.artifact.json" --engagement "$EID" 2>&1)"
RC3=$?
echo "$OUT3" | sed 's/^/    /'
assert_eq "0" "$RC3" "legacy quote-bearing artifact validates (schema + cross-field)"

# -----------------------------------------------------------------------------
# TEST 4 — enum trap regression: process:machine still FAILS validate_artifact.py
#          (cross-field gate not loosened by the trim).
# -----------------------------------------------------------------------------
echo "--- TEST 4: enum-trap (process:machine) still fails validate ---"
EID="__t55p1_enum__"
new_eng "$EID"
write_artifact "$EID" doc <<JSON
{
  "doc": { "source": "ingested/doc.md", "doc_type": "transcript", "classified_at": "2026-06-21T00:00:00Z" },
  "node_hits": [
    { "node": "$NODE_A", "confidence": "high",
      "evidence": [ { "ref": "ingested/doc.md#L10-12", "note": "ok" } ],
      "lens_signals": [
        { "lens": "process", "value": "machine", "confidence": "high", "evidence_ref": "ingested/doc.md#L10", "rationale": "wrong-lens value" }
      ] }
  ]
}
JSON
OUT4="$("$PY" "$VALIDATE" validate --artifact "engagements/$EID/classify/doc.artifact.json" --engagement "$EID" 2>&1)"
RC4=$?
echo "$OUT4" | sed 's/^/    /'
if [ "$RC4" -ne 0 ] && echo "$OUT4" | grep -qi "not valid for lens 'process'"; then
  ok "process:machine fails the cross-field lens gate"
else
  bad "process:machine did NOT fail the cross-field gate (gate loosened)"
fi

# -----------------------------------------------------------------------------
echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
[ "$FAIL" -ne 0 ] && exit 1
echo "ALL T55 PHASE 1 ASSERTIONS PASS."
exit 0
