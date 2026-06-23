#!/usr/bin/env bash
# =============================================================================
# test_orchestrate_predicates.sh — T45 orchestrate.py predicate-unification +
# guard regression test.
#
# orchestrate.py is READ-ONLY. This test asserts:
#   1. `next` and `next --all` agree on the recommended stage across a matrix of
#      crafted states (pre-draft / mid-draft / post-draft) — the head of the
#      `--all` frontier is exactly what `next` returns (no decide_next/frontier
#      drift, in particular on the `synthesize` gate which requires drafted_any).
#   2. a bad `--engagement` gives a clean "no such engagement" error (SystemExit
#      message), NOT a Python traceback.
#   3. a node that is present but lacks/`None`s `l1` does NOT silently drop from
#      the draft target — its key-derived L1 still appears in targets.l1s.
#
# No real client data is used. The scratch engagement (__t45__) is removed at the
# end. Exits 0 only if every assertion PASSes.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
EID="__t45__"                      # scratch engagement (removed at the end)
EDIR="engagements/$EID"

SM="scripts/state_machine.py"
ORCH="scripts/orchestrate.py"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }

assert_eq() { # EXPECTED ACTUAL MESSAGE
  if [ "$1" = "$2" ]; then ok "$3 (=$2)"; else bad "$3 (expected '$1', got '$2')"; fi
}

cleanup() { rm -rf "$EDIR"; }
trap cleanup EXIT

# next_head: the single action `next` recommends.
next_head() {
  "$PY" "$ORCH" next --engagement "$EID" --json | "$PY" -c \
    'import json,sys;print(json.load(sys.stdin)["action"])'
}
# all_head: the FIRST action on the `next --all` frontier (ORDER-sorted).
all_head() {
  "$PY" "$ORCH" next --engagement "$EID" --all --json | "$PY" -c \
    'import json,sys;a=json.load(sys.stdin)["actions"];print(a[0]["action"] if a else "")'
}

# assert_agree LABEL: next == head(next --all), and report the shared stage.
assert_agree() { # LABEL
  local nh ah
  nh="$(next_head)"
  ah="$(all_head)"
  assert_eq "$nh" "$ah" "$1: next agrees with next --all head"
  echo "    ($1 recommended stage: $nh)"
}

# Mutate state.json in place via a python snippet (test fixture craft only).
mutate_state() { # python-snippet operating on dict `st`
  "$PY" - "$EDIR/state.json" "$1" <<'PY'
import json, sys
path = sys.argv[1]
st = json.load(open(path))
exec(sys.argv[2])
json.dump(st, open(path, "w"), indent=2)
PY
}

echo "T45 orchestrate predicate-unification + guards test (engagement=$EID)"
cleanup

# --- bad --engagement: clean error, not a traceback --------------------------
echo "----------------------------------------------------------------"
echo "GUARD: bad --engagement gives a clean error (no traceback)"
echo "----------------------------------------------------------------"
ERR="$("$PY" "$ORCH" next --engagement no-such-engagement-xyz 2>&1 1>/dev/null)"
RC=$?
assert_eq "1" "$RC" "bad --engagement exits non-zero"
if echo "$ERR" | grep -q "Traceback"; then
  bad "bad --engagement printed a Python traceback"
else
  ok "bad --engagement printed no traceback"
fi
if echo "$ERR" | grep -q "No engagement 'no-such-engagement-xyz'"; then
  ok "bad --engagement printed a clean 'No engagement ...' message"
else
  bad "bad --engagement message not clean (got: $ERR)"
fi
# same for --all (both paths route through frontier's guard).
"$PY" "$ORCH" next --engagement no-such-engagement-xyz --all 2>&1 1>/dev/null \
  | grep -q "Traceback" && bad "bad --engagement --all printed a traceback" \
  || ok "bad --engagement --all printed no traceback"

# --- pre-draft state: fresh init, nothing ingested ---------------------------
echo "----------------------------------------------------------------"
echo "MATRIX: pre-draft (fresh init, nothing ingested)"
echo "----------------------------------------------------------------"
"$PY" "$SM" init --engagement "$EID" --region NA >/dev/null
assert_eq "ingest" "$(next_head)" "pre-draft head is 'ingest'"
assert_agree "pre-draft"

# --- satisfy ingest+classify+merge so the walk can reach the draft stage -----
# Create one ingested MD (front-matter source_hash) + a matching classify
# artifact (so ingested>0 and unclassified==0); node evidence below stands in
# for a completed merge. All read-only inputs to build_status; no pipeline run.
HASH="t45deadbeef"
mkdir -p "$EDIR/ingested" "$EDIR/classify"
printf -- '---\nsource_hash: %s\n---\n# t45 ingested doc\n' "$HASH" \
  > "$EDIR/ingested/$HASH.md"
printf '{}\n' > "$EDIR/classify/$HASH.artifact.json"

# --- mid-draft state: a draftable node with evidence + an open gap -----------
# Craft directly: pick the first node, give it evidence + partial coverage so it
# is draftable, and add an open structural-style gap so the `gap` predicate
# (which requires open_gaps==0) is skipped and `draft` is the head.
echo "----------------------------------------------------------------"
echo "MATRIX: mid-draft (draftable node present, head = draft)"
echo "----------------------------------------------------------------"
NODE="$("$PY" -c 'import json;print(sorted(json.load(open("'"$EDIR"'/state.json"))["nodes"]))' \
        | "$PY" -c 'import ast,sys;print(ast.literal_eval(sys.stdin.read())[0])')"
echo "    (using node: $NODE)"
mutate_state "
n = st['nodes']['$NODE']
n['coverage'] = 'partial'
n['evidence'] = [{'source': 'x.md', 'loc': 'L1'}]
"
# run the structural gap scan so open (structural) gaps exist -> open_gaps>0,
# which skips the `gap` stage so `draft` is the head (the scan is read-deriving
# of state; it writes the register, not orchestrate.py).
L1="${NODE%%.*}"
"$PY" scripts/gap_report.py scan --engagement "$EID" >/dev/null
assert_eq "draft" "$(next_head)" "mid-draft head is 'draft'"
assert_agree "mid-draft"

# --- missing-l1 guard: node draftable but l1 absent must not drop -------------
echo "----------------------------------------------------------------"
echo "GUARD: node missing l1 does not silently drop from draft target"
echo "----------------------------------------------------------------"
# Drop l1 from the draftable node; its key-derived L1 must still appear.
mutate_state "st['nodes']['$NODE']['l1'] = None"
L1S="$("$PY" "$ORCH" next --engagement "$EID" --json | "$PY" -c \
  'import json,sys;print(",".join(json.load(sys.stdin)["targets"].get("l1s",[])))')"
echo "    (draft targets.l1s with l1=None: $L1S)"
if echo ",$L1S," | grep -q ",$L1,"; then
  ok "key-derived L1 '$L1' present despite node.l1=None"
else
  bad "key-derived L1 '$L1' DROPPED when node.l1=None (l1s=$L1S)"
fi
assert_eq "draft" "$(next_head)" "head still 'draft' with malformed node"
assert_agree "missing-l1"
# restore l1 for the post-draft state.
mutate_state "st['nodes']['$NODE']['l1'] = '$L1'"

# --- post-draft state: streams drafted, synthesis.md not yet authored --------
# Mark sop+improvement drafted on the draftable node so drafted_any is true and
# the node is no longer draftable -> the head must be `synthesize` (the gate that
# decide_next and frontier used to disagree on; drafted_any WINS).
echo "----------------------------------------------------------------"
echo "MATRIX: post-draft (streams drafted, head = synthesize)"
echo "----------------------------------------------------------------"
"$PY" "$SM" set-sop --engagement "$EID" --node "$NODE" --status draft >/dev/null
"$PY" "$SM" set-improvement --engagement "$EID" --node "$NODE" --status draft >/dev/null
assert_eq "synthesize" "$(next_head)" "post-draft head is 'synthesize'"
assert_agree "post-draft"

# --- summary -----------------------------------------------------------------
echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
if [ "$FAIL" -ne 0 ]; then exit 1; fi
echo "ALL ASSERTIONS PASS."
exit 0
