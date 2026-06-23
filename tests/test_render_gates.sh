#!/usr/bin/env bash
# T46 — render_deliverables.py --l1 validation + gates.py path-escape / final-file existence.
# Scratch engagement __t46__ is removed at the end.
set -u
cd "$(dirname "$0")/.."

EID=__t46__
SM="python3 scripts/state_machine.py"
RENDER="python3 scripts/render_deliverables.py"
GATES="python3 scripts/gates.py"

pass=0; fail=0
ok()  { echo "  [PASS] $1"; pass=$((pass+1)); }
bad() { echo "  [FAIL] $1"; fail=$((fail+1)); }

cleanup() { rm -rf "engagements/$EID"; }
trap cleanup EXIT
cleanup
$SM init --engagement "$EID" >/dev/null 2>&1

echo "== 1. render --l1 BOGUS errors non-zero (not a silent exit-0 no-op) =="
out=$($RENDER render --engagement "$EID" --l1 not-a-real-l1 2>&1); rc=$?
if [ $rc -ne 0 ] && echo "$out" | grep -qi "Unknown --l1"; then
  ok "invalid --l1 rejected (rc=$rc)"
else
  bad "invalid --l1 not rejected (rc=$rc): $out"
fi

echo "== 2. gates: evidence source escaping the engagement dir fails the gate =="
# Pick a real node from the seeded taxonomy.
NODE=$($SM query --engagement "$EID" --json 2>/dev/null | python3 -c \
  'import sys,json; d=json.load(sys.stdin); print(next(iter(d["nodes"])) if isinstance(d,dict) and d.get("nodes") else "")' 2>/dev/null)
[ -z "$NODE" ] && NODE="record-to-report.close"
$SM add-evidence --engagement "$EID" --node "$NODE" \
  --source "../../etc/passwd" --loc "L1-L1" >/dev/null 2>&1
out=$($GATES final-check --engagement "$EID" 2>&1)
if echo "$out" | grep -q "evidence ref escapes the engagement dir"; then
  ok "path-escape evidence ref fails evidence_refs_resolve gate"
else
  bad "path-escape not caught: $out"
fi

echo "== 3. gates: final artifact whose path file is missing fails the gate =="
$SM set-sop --engagement "$EID" --node "$NODE" \
  --status final --path "deliverables/sop/does-not-exist.docx" >/dev/null 2>&1
out=$($GATES final-check --engagement "$EID" 2>&1)
if echo "$out" | grep -q "path does not exist"; then
  ok "missing final-artifact file fails final_artifacts_have_path gate"
else
  bad "missing final-artifact file not caught: $out"
fi

echo "----------------------------------------------------------------"
echo "RESULT: $pass passed, $fail failed."
[ $fail -eq 0 ]
