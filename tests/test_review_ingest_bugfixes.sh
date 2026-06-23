#!/usr/bin/env bash
# =============================================================================
# test_review_ingest_bugfixes.sh — T44 regression tests for review_ingest.py
#
# Covers the five fixes:
#   1. add-evidence is reachable via apply (in ALLOWED_COMMANDS) and dirties the
#      touched node.
#   2. (a) malformed actions batch fails pre-flight cleanly (no partial apply);
#      (b) a forced mark-dirty failure is NON-FATAL — the docx is still consumed,
#          so a re-run does NOT double-apply (evidence count stable).
#   3. malformed actions JSON errors cleanly (non-zero, no traceback).
#   5. the GAP-CONFLICT...REVIEW lens-override upsert succeeds end-to-end.
#
# No real client data: a scratch __t44__ engagement is seeded and removed at the
# end. Exits 0 only if every assertion passes.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
EID="__t44__"
EDIR="engagements/$EID"
SM="scripts/state_machine.py"
RI="scripts/review_ingest.py"
WORK="$EDIR/.t44work"
NODE="procure-to-pay.procurement"
LENS="current_state"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }
assert_eq() { if [ "$1" = "$2" ]; then ok "$3 (=$2)"; else bad "$3 (expected $1, got $2)"; fi; }

cleanup() { rm -rf "$EDIR"; }
trap cleanup EXIT

# node evidence count for $NODE.
ev_count() {
  "$PY" - "$EID" "$NODE" <<'PY'
import json, subprocess, sys
out = subprocess.check_output([sys.executable, "scripts/state_machine.py",
      "get-node", "--engagement", sys.argv[1], "--node", sys.argv[2], "--json"])
print(len(json.loads(out).get("evidence", []) or []))
PY
}
# is_diagnosis_dirty for $NODE (true/false) via last_evidence_at > consolidated_at proxy:
# simplest: was last_evidence_at bumped? we capture it before/after instead.
last_ev_at() {
  "$PY" - "$EID" "$NODE" <<'PY'
import json, subprocess, sys
out = subprocess.check_output([sys.executable, "scripts/state_machine.py",
      "get-node", "--engagement", sys.argv[1], "--node", sys.argv[2], "--json"])
print(json.loads(out).get("last_evidence_at") or "")
PY
}
# count active register rows of a given type.
count_type() {
  "$PY" - "$EDIR/register.json" "$1" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
rows = reg.get("records", reg) if isinstance(reg, dict) else reg
n = 0
for r in rows:
    if r.get("type") != sys.argv[2]: continue
    if (r.get("record_status") or "active") in ("archived","deleted","inactive"): continue
    n += 1
print(n)
PY
}

echo "T44 review_ingest bug-fix tests (engagement=$EID)"
cleanup
"$PY" "$SM" init --engagement "$EID" --region NA >/dev/null
mkdir -p "$WORK"

# A stand-in "reviewed docx" — apply only needs the file to exist (it hashes the
# bytes); the comments themselves come from the resolver actions JSON.
DOCX1="$WORK/round1.docx"; printf 'round1 reviewed bytes' > "$DOCX1"
DOCX2="$WORK/round2.docx"; printf 'round2 reviewed bytes' > "$DOCX2"
DOCX3="$WORK/round3.docx"; printf 'round3 reviewed bytes' > "$DOCX3"
DOCX4="$WORK/round4.docx"; printf 'round4 reviewed bytes' > "$DOCX4"

# =============================================================================
echo "----------------------------------------------------------------"
echo "TEST 1: add-evidence review action applies + dirties the node"
echo "----------------------------------------------------------------"
EV_BEFORE="$(ev_count)"
ACT1="$WORK/actions1.json"
cat > "$ACT1" <<JSON
[
  {"command": "add-evidence",
   "args": {"node": "$NODE", "source": "review-doc.md", "loc": "L10",
            "note": "reviewer-added evidence", "tier": "verbal"},
   "reviewer": "Reviewer A", "comment_id": "c1"}
]
JSON
"$PY" "$RI" apply --engagement "$EID" --docx "$DOCX1" --actions "$ACT1" --round 1
RC=$?
assert_eq "0" "$RC" "apply add-evidence exits 0"
EV_AFTER="$(ev_count)"
assert_eq "$((EV_BEFORE+1))" "$EV_AFTER" "evidence count incremented by add-evidence"
# dirtied: mark-dirty stamps last_evidence_at; review_log records the dirty set.
grep -q "dirtied (re-consolidate next run)" "$EDIR/deliverables/review_log.md" \
  && ok "review_log records the dirtied node" || bad "review_log missing dirtied node"
grep -q "consumed" <(cat "$EDIR/review/consumed.json") \
  && ok "docx1 marked consumed" || bad "docx1 not consumed"

# =============================================================================
echo "----------------------------------------------------------------"
echo "TEST 2: forced mark-dirty failure is NON-FATAL; re-run no double-apply"
echo "----------------------------------------------------------------"
# Drive apply via a Python harness that monkeypatches _run_mark_dirty to fail,
# so the substance action applies but the dirty flip errors. The docx must STILL
# be consumed (narrowed contract), so a re-run is an idempotent skip.
ACT2="$WORK/actions2.json"
cat > "$ACT2" <<JSON
[
  {"command": "add-evidence",
   "args": {"node": "$NODE", "source": "review-doc.md", "loc": "L20",
            "note": "second reviewer evidence", "tier": "verbal"},
   "reviewer": "Reviewer A", "comment_id": "c2"}
]
JSON
EV_PRE2="$(ev_count)"
"$PY" - "$EID" "$DOCX2" "$ACT2" <<'PY'
import sys, runpy, os
sys.path.insert(0, "scripts")
import review_ingest as ri
ri._run_mark_dirty = lambda eid, node: (1, "", "forced mark-dirty failure (test)")
rc = ri.cmd_apply(sys.argv[1], sys.argv[2], sys.argv[3], 2)
print("apply rc:", rc)
sys.exit(0 if rc == 0 else 1)
PY
RC=$?
assert_eq "0" "$RC" "apply returns 0 despite mark-dirty failure (non-fatal)"
EV_POST2="$(ev_count)"
assert_eq "$((EV_PRE2+1))" "$EV_POST2" "evidence applied once under forced dirty failure"
grep -q "WARN (non-fatal)" "$EDIR/deliverables/review_log.md" \
  && ok "review_log logs non-fatal mark-dirty warning" || bad "review_log missing non-fatal warning"
# Re-run the SAME docx via the real CLI: must be an idempotent skip (consumed).
OUT="$("$PY" "$RI" apply --engagement "$EID" --docx "$DOCX2" --actions "$ACT2" --round 2)"
RC=$?
assert_eq "0" "$RC" "re-run of consumed docx exits 0"
echo "$OUT" | grep -q '"skipped": true' && ok "re-run is an idempotent skip" || bad "re-run not skipped"
EV_POST2B="$(ev_count)"
assert_eq "$EV_POST2" "$EV_POST2B" "evidence count STABLE on re-run (no double-apply)"

# =============================================================================
echo "----------------------------------------------------------------"
echo "TEST 3: malformed actions JSON errors cleanly"
echo "----------------------------------------------------------------"
BAD="$WORK/bad.json"; printf '{ this is not valid json ]' > "$BAD"
ERR="$("$PY" "$RI" apply --engagement "$EID" --docx "$DOCX3" --actions "$BAD" --round 3 2>&1 >/dev/null)"
RC=$?
assert_eq "2" "$RC" "malformed JSON apply exits 2"
echo "$ERR" | grep -qi "malformed" && ok "clean 'malformed' error message" || bad "no clean error: $ERR"
echo "$ERR" | grep -qi "Traceback" && bad "leaked a traceback" || ok "no traceback leaked"
# malformed batch (well-formed JSON, ill-formed action) fails pre-flight, no apply.
BADB="$WORK/badbatch.json"; printf '[{"command":"frobnicate","args":{}}]' > "$BADB"
EV_PRE3="$(ev_count)"
ERR2="$("$PY" "$RI" apply --engagement "$EID" --docx "$DOCX3" --actions "$BADB" --round 3 2>&1 >/dev/null)"
RC=$?
assert_eq "2" "$RC" "disallowed-command batch fails pre-flight (exit 2)"
echo "$ERR2" | grep -qi "pre-flight" && ok "pre-flight validation message" || bad "no pre-flight message: $ERR2"
assert_eq "$EV_PRE3" "$(ev_count)" "no state mutation on failed pre-flight"
[ -f "$EDIR/review/consumed.json" ] && grep -q "round3" "$EDIR/review/consumed.json" \
  && bad "docx3 wrongly consumed" || ok "docx3 NOT consumed on pre-flight failure"

# =============================================================================
echo "----------------------------------------------------------------"
echo "TEST 4: GAP-CONFLICT...REVIEW lens-override upsert succeeds end-to-end"
echo "----------------------------------------------------------------"
# Seed a non-null lens value, then have the reviewer override it -> audited.
"$PY" "$SM" set-lens --engagement "$EID" --node "$NODE" --lens "$LENS" --value "present" >/dev/null
GAP_PRE="$(count_type gap)"
ACT4="$WORK/actions4.json"
cat > "$ACT4" <<JSON
[
  {"command": "set-lens",
   "args": {"node": "$NODE", "lens": "$LENS", "value": "absent"},
   "reviewer": "Reviewer B", "comment_id": "c4"}
]
JSON
OUT4="$("$PY" "$RI" apply --engagement "$EID" --docx "$DOCX4" --actions "$ACT4" --round 4)"
RC=$?
assert_eq "0" "$RC" "lens-override apply exits 0"
GAP_POST="$(count_type gap)"
assert_eq "$((GAP_PRE+1))" "$GAP_POST" "one GAP-CONFLICT...REVIEW row upserted"
# the conflict id is flat-node + -REVIEW
EXPECT_ID="GAP-CONFLICT-procure-to-pay-procurement-${LENS}-REVIEW"
"$PY" - "$EDIR/register.json" "$EXPECT_ID" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
rows = reg.get("records", reg) if isinstance(reg, dict) else reg
ids = {r.get("id") for r in rows}
sys.exit(0 if sys.argv[2] in ids else 1)
PY
[ $? -eq 0 ] && ok "register has $EXPECT_ID" || bad "missing $EXPECT_ID"
# lens value was actually overridden to the reviewer's value.
LV="$("$PY" - "$EID" "$NODE" "$LENS" <<'PY'
import json, subprocess, sys
out = subprocess.check_output([sys.executable, "scripts/state_machine.py",
      "get-node", "--engagement", sys.argv[1], "--node", sys.argv[2], "--json"])
print((json.loads(out).get("lenses") or {}).get(sys.argv[3]) or "")
PY
)"
assert_eq "absent" "$LV" "reviewer lens value applied (human > machine)"
# idempotent upsert: re-applying the same override (new docx, same effect) does
# not mint a duplicate conflict row.
DOCX5="$WORK/round5.docx"; printf 'round5 reviewed bytes' > "$DOCX5"
"$PY" "$RI" apply --engagement "$EID" --docx "$DOCX5" --actions "$ACT4" --round 5 >/dev/null
assert_eq "$GAP_POST" "$(count_type gap)" "conflict upsert is idempotent (no duplicate row)"

# =============================================================================
echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
[ "$FAIL" -ne 0 ] && exit 1
echo "ALL T44 ASSERTIONS PASS."
exit 0
