#!/usr/bin/env bash
# =============================================================================
# test_slice2_e2e.sh — CONSULT Slice-2 capstone end-to-end regression test (T49)
#
# Slice 2 (the human review loop) was marked complete but had ZERO end-to-end
# coverage. This drives the DETERMINISTIC spine of the review loop on a COMMITTED
# reviewed .docx fixture, with the non-deterministic comment-RESOLVER stage (which
# turns reviewer comments into state_machine actions) STUBBED by a canned actions
# JSON — exactly the pattern Slice-1 uses for its LLM stages. No live LLM call.
#
#   init -> seed close node (lens + consolidated marker) ->
#   docx_comments.py extract (committed .docx -> comments JSON) ->
#   review_ingest.py extract (idempotent bundle; consumed marker NOT yet set) ->
#   review_ingest.py apply  (canned resolver actions: a lens-override + an
#       add-evidence) -> mark-dirty (done inside apply) ->
#   STUBBED re-consolidate (mark-consolidated, canned — not a live consolidator) ->
#   gates.py final-check.
#
# ASSERTS:
#   * docx_comments extract surfaces both committed comments, anchored.
#   * review_ingest extract is read-only (does NOT consume the docx).
#   * apply applies BOTH substance actions and dirties record-to-report.close.
#   * the lens override (human > machine) is applied AND audited (GAP-CONFLICT…REVIEW).
#   * the docx is marked consumed after apply.
#   * a STUBBED re-consolidate clears the diagnosis-dirty signal on the node.
#   * gates.py final-check PASSes (exit 0) on the resulting engagement.
#   * a SECOND apply of the SAME consumed docx is an IDEMPOTENT skip (no double
#     write): evidence count, conflict-gap count, consumed count all unchanged.
#
# Scratch engagement __t49b__ is removed at the end. Exits 0 only if every
# assertion passes.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
EID="__t49b__"
EDIR="engagements/$EID"
SM="scripts/state_machine.py"
DOCX_COMMENTS="scripts/docx_comments.py"
RI="scripts/review_ingest.py"
GATES="scripts/gates.py"
NODE="record-to-report.close"
DOCX="fixtures/review/rtr_close_reviewed.docx"

PASS=0
FAIL=0
ok()  { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad() { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }
assert_eq() { if [ "$1" = "$2" ]; then ok "$3 (=$2)"; else bad "$3 (expected $1, got $2)"; fi; }

cleanup() { rm -rf "$EDIR"; }
trap cleanup EXIT

# --- read-only probes --------------------------------------------------------
node_get() { # $1 node  $2 python-expr over var d (the get-node --json object)
  "$PY" - "$EID" "$1" "$2" <<'PY'
import json, subprocess, sys
out = subprocess.check_output([sys.executable, "scripts/state_machine.py",
      "get-node", "--engagement", sys.argv[1], "--node", sys.argv[2], "--json"])
d = json.loads(out)
print(eval(sys.argv[3]))
PY
}
count_type() { # $1 = type
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
consumed_count() {
  "$PY" - "$EDIR/review/consumed.json" <<'PY'
import json, os, sys
p = sys.argv[1]
print(len(json.load(open(p)).get("consumed", [])) if os.path.exists(p) else 0)
PY
}
is_dirty() { # prints True/False for is_diagnosis_dirty on $NODE
  "$PY" - "$EID" "$NODE" <<'PY'
import json, subprocess, sys
sys.path.insert(0, "scripts")
import state_machine as sm
_, state = sm.load_state(sys.argv[1])
print(sm.is_diagnosis_dirty(state["nodes"][sys.argv[2]]))
PY
}

echo "T49 Slice-2 e2e regression test  (engagement=$EID)"
cleanup

# =============================================================================
echo "----------------------------------------------------------------"
echo "STAGE 0: init + seed the close node (lens + consolidated marker)"
echo "----------------------------------------------------------------"
"$PY" "$SM" init --engagement "$EID" --region NA >/dev/null
# Seed a NON-NULL automation lens so the reviewer's override is a genuine
# disagreement (human > machine) that must be AUDITED, not silently applied.
"$PY" "$SM" set-lens --engagement "$EID" --node "$NODE" --lens automation --value mixed >/dev/null
# Seed an evidence source file under the engagement dir so the add-evidence
# resolver action's `source` resolves (the evidence_refs_resolve gate checks it).
mkdir -p "$EDIR/review"
printf 'Anchored review evidence: dual-review control verbally attested.\n' \
  > "$EDIR/review/rtr_close_anchor.md"
# Stamp consolidated so the node starts CLEAN; the review apply will dirty it.
"$PY" "$SM" mark-consolidated --engagement "$EID" --node "$NODE" >/dev/null
assert_eq "False" "$(is_dirty)" "node starts clean (consolidated, not diagnosis-dirty)"
EV_SEED="$(node_get "$NODE" "len(d.get('evidence') or [])")"

# =============================================================================
echo "----------------------------------------------------------------"
echo "STAGE 1: docx_comments.py extract — committed .docx -> comments"
echo "----------------------------------------------------------------"
assert_eq "0" "$([ -f "$DOCX" ] && echo 0 || echo 1)" "committed reviewed .docx fixture present"
DC_JSON="$("$PY" "$DOCX_COMMENTS" extract --docx "$DOCX" --json)"
N_COMMENTS="$("$PY" -c "import json,sys; d=json.loads(sys.stdin.read()); rows=d['comments'] if isinstance(d,dict) else d; print(len(rows))" <<<"$DC_JSON")"
assert_eq "2" "$N_COMMENTS" "docx_comments extracted both committed comments"
echo "$DC_JSON" | grep -q "automation lens should read human" \
  && ok "comment 0 anchored to the automation-lens sentence" \
  || bad "comment 0 anchor missing"

# =============================================================================
echo "----------------------------------------------------------------"
echo "STAGE 2: review_ingest.py extract — read-only (must NOT consume)"
echo "----------------------------------------------------------------"
"$PY" "$RI" extract --engagement "$EID" --docx "$DOCX" --round 1 >/dev/null
assert_eq "0" "$(consumed_count)" "extract did NOT mark the docx consumed (read-only)"

# =============================================================================
echo "----------------------------------------------------------------"
echo "STAGE 3 (stubbed resolver): apply canned resolver actions"
echo "----------------------------------------------------------------"
# The comment-resolver (human/LLM) step is STUBBED here with a canned actions
# JSON, exactly like Slice-1 stubs its LLM stages. Two substance actions:
#   - set-lens automation=human  (overrides the seeded non-null 'mixed' -> AUDIT)
#   - add-evidence (verbal-tier)  (records the attested control on the node)
ACTIONS="$EDIR/.t49b_actions.json"
cat > "$ACTIONS" <<JSON
[
  {"command": "set-lens",
   "args": {"node": "$NODE", "lens": "automation", "value": "human"},
   "reviewer": "Reviewer A", "comment_id": "0"},
  {"command": "add-evidence",
   "args": {"node": "$NODE", "source": "review/rtr_close_anchor.md", "loc": "L1",
            "note": "Dual-review control attested verbally (reviewer-added).",
            "tier": "verbal"},
   "reviewer": "Reviewer B", "comment_id": "1"}
]
JSON
APPLY_OUT="$("$PY" "$RI" apply --engagement "$EID" --docx "$DOCX" --actions "$ACTIONS" --round 1)"
RC=$?
assert_eq "0" "$RC" "apply exits 0"
echo "$APPLY_OUT" | grep -q "Applied 2 action" \
  && ok "apply reports 2 actions applied" || bad "apply did not apply 2 actions: $APPLY_OUT"

# applied substance: lens overridden + evidence added.
assert_eq "human" "$(node_get "$NODE" "(d.get('lenses') or {}).get('automation')")" \
  "automation lens overridden to reviewer value (human > machine)"
EV_AFTER="$(node_get "$NODE" "len(d.get('evidence') or [])")"
assert_eq "$((EV_SEED+1))" "$EV_AFTER" "add-evidence applied once"

# dirtied set: the node is now diagnosis-dirty (substance change post-consolidate).
assert_eq "True" "$(is_dirty)" "review apply dirtied record-to-report.close"
grep -q "dirtied (re-consolidate next run)" "$EDIR/deliverables/review_log.md" \
  && ok "review_log records the dirtied node" || bad "review_log missing dirtied node"

# the override is AUDITED via a GAP-CONFLICT…REVIEW row.
CONFLICT_ID="GAP-CONFLICT-record-to-report-close-automation-REVIEW"
"$PY" - "$EDIR/register.json" "$CONFLICT_ID" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
rows = reg.get("records", reg) if isinstance(reg, dict) else reg
sys.exit(0 if sys.argv[2] in {r.get("id") for r in rows} else 1)
PY
[ $? -eq 0 ] && ok "lens override audited ($CONFLICT_ID present)" || bad "override not audited ($CONFLICT_ID missing)"

# consumed marker set after apply.
assert_eq "1" "$(consumed_count)" "docx marked consumed after apply"

# =============================================================================
echo "----------------------------------------------------------------"
echo "STAGE 4 (stubbed re-consolidate): clear the dirty signal"
echo "----------------------------------------------------------------"
# A live consult-run would re-invoke the consolidator LLM here. We STUB it: the
# deterministic part is the mark-consolidated stamp that clears the dirty signal.
"$PY" "$SM" mark-consolidated --engagement "$EID" --node "$NODE" >/dev/null
assert_eq "False" "$(is_dirty)" "stubbed re-consolidate cleared the diagnosis-dirty signal"

# The audited override row is flagged requires_human_review (by design — a human
# must bless an override of evidence-backed analysis). The human disposition step
# resolves it: upsert the SAME row (stable dedup_key) approved + flag cleared, so
# the no_open_human_review gate can pass. This is a deterministic upsert, not an
# LLM call.
"$PY" "$SM" add-item --engagement "$EID" --type gap \
  --l1 record-to-report --l2 close \
  --id "$CONFLICT_ID" \
  --field "dedup_key=conflict|$NODE|automation|review" \
  --field "source=review" \
  --field "requires_human_review=false" \
  --field "review_status=approved" \
  --field "observation_pain_point=Reviewer override on automation lens approved by engagement lead." \
  >/dev/null
RHR_OPEN="$("$PY" - "$EDIR/register.json" "$CONFLICT_ID" <<'PY'
import json, sys
sys.path.insert(0, "scripts")
import state_machine as sm
reg = json.load(open(sys.argv[1]))
rows = reg.get("records", reg) if isinstance(reg, dict) else reg
r = next((x for x in rows if x.get("id") == sys.argv[2]), None)
print("OPEN" if (r is not None and sm._is_truthy_flag(r.get("requires_human_review"))) else "RESOLVED")
PY
)"
assert_eq "RESOLVED" "$RHR_OPEN" "human disposition cleared requires_human_review on the audit row"

# =============================================================================
echo "----------------------------------------------------------------"
echo "STAGE 5: gates.py final-check"
echo "----------------------------------------------------------------"
GATE_OUT="$("$PY" "$GATES" final-check --engagement "$EID")"
RC=$?
echo "$GATE_OUT"
assert_eq "0" "$RC" "final-check PASSes (exit 0) on the reviewed engagement"

# capture floor counts for the idempotency check.
EV_R1="$(node_get "$NODE" "len(d.get('evidence') or [])")"
GAP_R1="$(count_type gap)"
CONSUMED_R1="$(consumed_count)"

# =============================================================================
echo "----------------------------------------------------------------"
echo "STAGE 6: idempotency — re-applying the SAME consumed docx is a no-op"
echo "----------------------------------------------------------------"
APPLY2="$("$PY" "$RI" apply --engagement "$EID" --docx "$DOCX" --actions "$ACTIONS" --round 1)"
RC=$?
assert_eq "0" "$RC" "re-apply of consumed docx exits 0"
echo "$APPLY2" | grep -q '"skipped": true' \
  && ok "re-apply is an idempotent skip (consumed)" || bad "re-apply not skipped: $APPLY2"
assert_eq "$EV_R1"       "$(node_get "$NODE" "len(d.get('evidence') or [])")" "evidence count STABLE on re-apply"
assert_eq "$GAP_R1"      "$(count_type gap)"  "conflict-gap count STABLE on re-apply"
assert_eq "$CONSUMED_R1" "$(consumed_count)"  "consumed count STABLE on re-apply"

# =============================================================================
echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
[ "$FAIL" -ne 0 ] && exit 1
echo "ALL T49 SLICE-2 ASSERTIONS PASS (incl. idempotent re-apply)."
exit 0
