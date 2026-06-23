#!/usr/bin/env bash
# =============================================================================
# test_gap_rescan_tag.sh — T47 tests for scripts/gap_report.py
#
# Asserts:
#   1. A human-edited `tag` on a GAP-STRUCT row SURVIVES a structural re-scan
#      (fix 3 — tag preserved like T36 preserves review_status/owner), while a
#      non-edited row's tag is still refreshed/stable.
#   2. A malformed node (missing l1/l2) is REPORTED on stderr and skipped — it
#      is NOT emitted as a `GAP-STRUCT-None-...` register row (fix 1).
#
# Uses a scratch engagement (__t47__) removed at the end. No client data.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
SM="scripts/state_machine.py"
GAP="scripts/gap_report.py"
ILOG="skills/consult-improvement-log/scripts/improvement_log.py"

EID="__t47__rescan"
EDIR="engagements/$EID"
TMPCSV="$(mktemp -t __t47__edit.XXXXXX.csv)"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }

cleanup() { rm -rf "$EDIR"; rm -f "$TMPCSV"; }
trap cleanup EXIT

echo "T47 gap rescan-tag tests (engagement=$EID)"
cleanup

# --- seed + first scan (every coverage=none node yields a no-coverage gap) ----
"$PY" "$SM" init --engagement "$EID" --region NA >/dev/null
"$PY" "$GAP" scan --engagement "$EID" >/dev/null 2>&1

# pick a real GAP-STRUCT id to human-edit.
GID="$("$PY" - "$EDIR/register.json" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
ids = [r["id"] for r in reg["records"]
       if str(r.get("id","")).startswith("GAP-STRUCT-")]
print(ids[0] if ids else "")
PY
)"
if [ -z "$GID" ]; then bad "no GAP-STRUCT row produced by first scan"; echo "RESULT: $PASS passed, $((FAIL)) failed."; exit 1; fi
ok "first scan produced a GAP-STRUCT row to edit ($GID)"

# --- human edits the tag via the register write-path (never hand-edit JSON) ---
printf 'id,tag\n%s,confirmed_critical\n' "$GID" > "$TMPCSV"
"$PY" "$ILOG" update-json --json "$EDIR/register.json" --csv "$TMPCSV" \
  --out-json "$EDIR/register.json" --modified-by "__t47__human" >/dev/null

tag_of() { # $1 = id  -> prints current tag
  "$PY" - "$EDIR/register.json" "$1" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
row = next((r for r in reg["records"] if r["id"] == sys.argv[2]), None)
print("" if row is None else (row.get("tag") or ""))
PY
}

assert_eq() { if [ "$1" = "$2" ]; then ok "$3 (=$2)"; else bad "$3 (expected $1, got $2)"; fi; }

assert_eq "confirmed_critical" "$(tag_of "$GID")" "human-edited tag set before re-scan"

# --- structural RE-SCAN — the human tag must survive --------------------------
"$PY" "$GAP" scan --engagement "$EID" >/dev/null 2>&1
assert_eq "confirmed_critical" "$(tag_of "$GID")" "human-edited tag SURVIVES re-scan"

# a different (un-edited) GAP-STRUCT row keeps its detector default after re-scan.
OTHER="$("$PY" - "$EDIR/register.json" "$GID" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
ids = [r["id"] for r in reg["records"]
       if str(r.get("id","")).startswith("GAP-STRUCT-") and r["id"] != sys.argv[2]
       and (r.get("record_status") or "active") == "active"]
print(ids[0] if ids else "")
PY
)"
if [ -n "$OTHER" ]; then
  assert_eq "not_documented" "$(tag_of "$OTHER")" "un-edited row keeps detector default tag"
fi

# --- malformed node: reported, NOT emitted as GAP-STRUCT-None ----------------
"$PY" - "$EDIR/state.json" <<'PY'
import json, sys
p = sys.argv[1]
st = json.load(open(p))
st["nodes"]["__t47__bogus"] = {"l1": None, "l2": None, "coverage": "none"}
json.dump(st, open(p, "w"))
PY

STDERR="$("$PY" "$GAP" scan --engagement "$EID" 2>&1 >/dev/null)"
case "$STDERR" in
  *malformed*__t47__bogus*) ok "malformed node reported on stderr";;
  *) bad "malformed node NOT reported (stderr: $STDERR)";;
esac

NONE_ROWS="$("$PY" - "$EDIR/register.json" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
print(sum(1 for r in reg["records"] if "None" in str(r.get("id",""))))
PY
)"
assert_eq "0" "$NONE_ROWS" "no GAP-STRUCT-None row emitted for malformed node"

echo "----------------------------------------------------------------"
echo "RESULT: $PASS passed, $FAIL failed."
echo "----------------------------------------------------------------"
[ "$FAIL" -eq 0 ] || exit 1
echo "ALL GAP RESCAN-TAG ASSERTIONS PASS."
exit 0
