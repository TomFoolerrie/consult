#!/usr/bin/env bash
# =============================================================================
# test_slice1_e2e.sh — CONSULT Slice-1 capstone end-to-end regression test (T20)
#
# Drives the DETERMINISTIC spine of the Slice-1 pipeline on the synthesized R2R
# fixture, with the non-deterministic LLM stages (classify / consolidate / draft /
# synthesis) STUBBED by canned outputs:
#
#   init -> ingest(2 transcripts) -> materialize canned classify artifacts ->
#   validate artifacts -> classify_merge -> apply canned findings via add-item
#   (verbal-tier gap + improvement + verbal-tier evidence; unmapped come from the
#   merge) -> gap_report scan -> assert draft_inputs / synthesis_inputs bundles ->
#   write tiny canned deliverable MDs -> render_deliverables --what all.
#
# ASSERTS:
#   * R2R nodes carry lenses + evidence (close = covered w/ 5 lenses).
#   * register has improvements + gaps + >=1 unmapped + a verbal-tier gap.
#   * a node evidence entry carries tier=verbal (the verbal control claim).
#   * .docx deliverables are produced (synthesis, sop, improvements, gap_report).
#   * a SECOND full run is IDEMPOTENT: evidence / findings / unmapped counts are
#     unchanged (proves the correctness floor — no duplicate writes on re-run).
#
# No real client data is used (the fixture is synthesized). The scratch
# engagement is removed at the end. Exits 0 only if every assertion PASSes on
# BOTH runs.
# =============================================================================
set -u

# --- locations ---------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PY="${PYTHON:-python3}"
EID="__t20__"                      # scratch engagement (removed at the end)
EDIR="engagements/$EID"
FIX="fixtures/r2r"

SM="scripts/state_machine.py"
INGEST="scripts/ingest_normalize.py"
VALIDATE="scripts/validate_artifact.py"
MERGE="scripts/classify_merge.py"
GAP="scripts/gap_report.py"
DRAFT="scripts/draft_inputs.py"
SYNTH="scripts/synthesis_inputs.py"
RENDER="scripts/render_deliverables.py"
BUILD_CANNED="$FIX/canned/build_canned.py"

PASS=0
FAIL=0

ok()   { echo "  PASS: $*"; PASS=$((PASS+1)); }
bad()  { echo "  FAIL: $*"; FAIL=$((FAIL+1)); }

# assert_eq EXPECTED ACTUAL MESSAGE
assert_eq() {
  if [ "$1" = "$2" ]; then ok "$3 (=$2)"; else bad "$3 (expected $1, got $2)"; fi
}
# assert_ge MIN ACTUAL MESSAGE
assert_ge() {
  if [ "$2" -ge "$1" ] 2>/dev/null; then ok "$3 (=$2, >= $1)"
  else bad "$3 (expected >= $1, got $2)"; fi
}
# assert_file PATH MESSAGE
assert_file() {
  if [ -f "$1" ]; then ok "$2"; else bad "$2 (missing: $1)"; fi
}

cleanup() { rm -rf "$EDIR"; }
trap cleanup EXIT

# --- small register/state probes (read-only python one-liners) ---------------
# count register rows of a given type that are active (not archived/deleted).
count_type() { # $1 = type
  "$PY" - "$EDIR/register.json" "$1" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
rows = reg.get("records", reg) if isinstance(reg, dict) else reg
n = 0
for r in rows:
    if r.get("type") != sys.argv[2]:
        continue
    rs = (r.get("record_status") or "active")
    if rs in ("archived", "deleted", "inactive"):
        continue
    n += 1
print(n)
PY
}

# count node-evidence entries carrying a given tier across all nodes.
count_evidence_tier() { # $1 = tier
  "$PY" - "$EDIR/state.json" "$1" <<'PY'
import json, sys
st = json.load(open(sys.argv[1]))
nodes = st.get("nodes", st)
n = 0
for node in nodes.values():
    for ev in node.get("evidence", []) or []:
        if ev.get("tier") == sys.argv[2]:
            n += 1
print(n)
PY
}

# total node-evidence entries across all nodes.
count_total_evidence() {
  "$PY" - "$EDIR/state.json" <<'PY'
import json, sys
st = json.load(open(sys.argv[1]))
nodes = st.get("nodes", st)
print(sum(len(n.get("evidence", []) or []) for n in nodes.values()))
PY
}

# a single node field via get-node --json (jq-free).
node_get() { # $1 node  $2 python-expr over var d
  "$PY" - "$EID" "$1" "$2" <<'PY'
import json, subprocess, sys
out = subprocess.check_output([sys.executable, "scripts/state_machine.py",
       "get-node", "--engagement", sys.argv[1], "--node", sys.argv[2], "--json"])
d = json.loads(out)
print(eval(sys.argv[3]))
PY
}

# does any active gap row carry evidence_tier=verbal?
count_verbal_gaps() {
  "$PY" - "$EDIR/register.json" <<'PY'
import json, sys
reg = json.load(open(sys.argv[1]))
rows = reg.get("records", reg) if isinstance(reg, dict) else reg
n = 0
for r in rows:
    if r.get("type") == "gap" and r.get("evidence_tier") == "verbal":
        rs = (r.get("record_status") or "active")
        if rs not in ("archived", "deleted", "inactive"):
            n += 1
print(n)
PY
}

# bundle assertions via the gatherers (jq-free).
bundle_count() { # $1 script  $2 args...  -> prints a count expression on stdin
  : # placeholder (unused; kept for symmetry)
}

# =============================================================================
# run_pipeline — the full deterministic Slice-1 motion. Idempotent by design.
# Called twice; the second call must not change any count.
# =============================================================================
run_pipeline() {
  local phase="$1"
  echo "================================================================"
  echo "PIPELINE RUN: $phase"
  echo "================================================================"

  # --- Stage 0: init (idempotent: state_machine init is safe to re-seed) -----
  "$PY" "$SM" init --engagement "$EID" --region NA >/dev/null
  echo "[init] ok"

  # --- Stage 1: ingest the 2 synthesized transcripts -------------------------
  "$PY" "$INGEST" ingest --engagement "$EID" \
      --source "$FIX/close_walkthrough.vtt" "$FIX/recon_walkthrough.txt"

  # --- Stage 2: materialize canned classify artifacts into classify/ ---------
  #   (refs are written to resolve into the just-produced hashed ingested MDs)
  "$PY" "$BUILD_CANNED" --engagement "$EID"

  # validate every canned artifact (must pass schema+node+lens+ref) -----------
  for a in "$EDIR"/classify/*.artifact.json; do
    "$PY" "$VALIDATE" validate --artifact "$a" --engagement "$EID" >/dev/null \
      || { echo "ARTIFACT VALIDATION FAILED: $a"; "$PY" "$VALIDATE" validate --artifact "$a" --engagement "$EID"; return 1; }
  done
  echo "[classify] artifacts materialized + validated"

  # --- Stage 2b: deterministic merge (evidence + lenses + unmapped) ----------
  "$PY" "$MERGE" merge --engagement "$EID"

  # --- Stage 3 (stubbed consolidate): apply canned confirmed findings --------
  #   These stand in for the consolidator's confirmed register rows. Stable
  #   --id + dedup_key => a re-run UPSERTS rather than duplicates.
  #
  #   (a) verbal-tier control evidence on the close node (the verbally-stated
  #       dual-review control) — add-evidence is ref-dedup'd, so re-runs no-op.
  CLOSE_MD="$(node_get record-to-report.close "d['evidence'][0]['source']")"
  #       (loc L35 is the explicit verbal attestation — "it isn't written into any
  #       policy or system config ... I can confirm it happens" — and is not among
  #       the locs the merge already added, so the tiered entry actually lands.)
  "$PY" "$SM" add-evidence --engagement "$EID" --node record-to-report.close \
      --source "$CLOSE_MD" --loc L35 \
      --note "Dual-review control over reconciliations >\$50k (verbally attested; not in policy/system)." \
      --tier verbal >/dev/null

  #   (b) a verbal-tier GAP: the control is attested only verbally and needs a
  #       documentary/system source — exactly the evidence-tier gap the spec wants.
  "$PY" "$SM" add-item --engagement "$EID" --type gap \
      --l1 record-to-report --l2 close \
      --id GAP-VERBAL-rtr-close-dualreview \
      --field "tag=control_undocumented" \
      --field "dedup_key=GAP-VERBAL-rtr-close-dualreview" \
      --field "evidence_tier=verbal" \
      --field "source=$CLOSE_MD#L31" \
      --field "observation_pain_point=Dual-review control over reconciliations >\$50k is attested only verbally; no policy or system source. Requires >=documentary validation." \
      --field "recommended_action=Validate the dual-review control against a policy/system config and document it, or escalate as an open control gap." \
      >/dev/null

  #   (c) a confirmed IMPROVEMENT (automation) on the close node.
  "$PY" "$SM" add-item --engagement "$EID" --type improvement \
      --l1 record-to-report --l2 close \
      --id IMP-RTR-CLOSE-ACCRUALS \
      --field "tag=automation" \
      --field "dedup_key=IMP-RTR-CLOSE-ACCRUALS" \
      --field "observation_pain_point=Accruals are built in spreadsheets and re-keyed into the ERP every close, driving late adjustments." \
      --field "recommended_action=Automate recurring accrual journals via an accrual engine / templated upload." \
      --field "impact_type=cycle_time" \
      --field "estimated_impact_benefit=directional" \
      --field "effort=medium" \
      --field "priority=high" \
      --field "owner=Controller" \
      >/dev/null

  #   (d) an explicit unmapped row via the null-node add path (in addition to the
  #       two the merge already produced from the artifacts' `unmapped[]`).
  "$PY" "$SM" add-item --engagement "$EID" --type unmapped \
      --id UNMAPPED-DENVER-LEASE \
      --field "dedup_key=UNMAPPED-DENVER-LEASE" \
      --field "owner=Facilities/Real-Estate" \
      --field "observation_pain_point=Denver office lease renewal — facilities/real-estate decision finance is looped into; fits no R2R activity." \
      >/dev/null

  # stamp consolidated on the two touched nodes (Stage-3 marker).
  "$PY" "$SM" mark-consolidated --engagement "$EID" --node record-to-report.close >/dev/null
  "$PY" "$SM" mark-consolidated --engagement "$EID" --node record-to-report.consolidation >/dev/null
  echo "[consolidate] canned findings applied (1 verbal gap, 1 improvement, +1 unmapped)"

  # --- Stage 4: structural gap scan (deterministic, stable GAP-STRUCT ids) ----
  "$PY" "$GAP" scan --engagement "$EID" >/dev/null
  echo "[gap] structural scan complete"

  # --- Stage 5 inputs: assert the draft + synthesis bundles gather -----------
  "$PY" "$DRAFT" gather --engagement "$EID" --l1 record-to-report --json > "$EDIR/.draft_bundle.json"
  "$PY" "$SYNTH" gather --engagement "$EID" --json > "$EDIR/.synth_bundle.json"
  echo "[draft/synth] input bundles gathered"

  # --- Stage 5 (stubbed draft/synth): write tiny canned deliverable MDs -------
  mkdir -p "$EDIR/deliverables/sop" "$EDIR/deliverables/improvements"
  printf '# Record to Report — Synthesis\n\nExecutive summary: the monthly close runs but manual accruals are the dominant pain point; consolidation is mature and centralized. One verbally-attested control needs documentary validation.\n' \
    > "$EDIR/deliverables/synthesis.md"
  printf '# Record to Report — Desktop Procedures (SOP)\n\nScope: L1 cycle record-to-report.\n\nSee Appendix C for the open dual-review control validation gap.\n' \
    > "$EDIR/deliverables/sop/record-to-report.md"
  printf '# Record to Report — Process Improvement Opportunities\n\n## Automate recurring accruals (IMP-RTR-CLOSE-ACCRUALS)\n\nFinding -> Recommendation -> Effort x Impact (directional) -> Owner: Controller.\n' \
    > "$EDIR/deliverables/improvements/record-to-report.md"
  # gap_report.md is written by the scan above.

  # --- Stage 6: render all deliverable MDs to .docx --------------------------
  "$PY" "$RENDER" render --engagement "$EID" --what all
  echo "[render] deliverables rendered"
}

# =============================================================================
# assert_state — all post-run assertions (run after BOTH pipeline runs).
# =============================================================================
assert_state() {
  echo "----------------------------------------------------------------"
  echo "ASSERTIONS: $1"
  echo "----------------------------------------------------------------"

  # R2R close node: lenses set + evidence + covered.
  local close_cov close_lenses close_ev
  close_cov="$(node_get record-to-report.close "d['coverage']")"
  close_lenses="$(node_get record-to-report.close "sum(1 for v in d['lenses'].values() if v)")"
  close_ev="$(node_get record-to-report.close "len(d['evidence'])")"
  assert_eq "covered" "$close_cov" "R2R close node coverage is 'covered'"
  assert_eq "5" "$close_lenses" "R2R close node has all 5 lenses set"
  assert_ge 4 "$close_ev" "R2R close node has evidence entries"

  # R2R consolidation node: lenses + evidence present.
  local cons_lenses cons_ev
  cons_lenses="$(node_get record-to-report.consolidation "sum(1 for v in d['lenses'].values() if v)")"
  cons_ev="$(node_get record-to-report.consolidation "len(d['evidence'])")"
  assert_ge 4 "$cons_lenses" "R2R consolidation node has lenses set"
  assert_ge 3 "$cons_ev" "R2R consolidation node has evidence entries"

  # register composition.
  local n_imp n_gap n_unmapped n_verbal_gap n_verbal_ev
  n_imp="$(count_type improvement)"
  n_gap="$(count_type gap)"
  n_unmapped="$(count_type unmapped)"
  n_verbal_gap="$(count_verbal_gaps)"
  n_verbal_ev="$(count_evidence_tier verbal)"
  assert_ge 1 "$n_imp" "register has improvement rows"
  assert_ge 1 "$n_gap" "register has gap rows (incl. structural)"
  assert_ge 1 "$n_unmapped" "register has >=1 unmapped row"
  assert_ge 1 "$n_verbal_gap" "register has a verbal-tier gap row"
  assert_ge 1 "$n_verbal_ev" "a node evidence entry carries tier=verbal"

  # deliverables rendered to .docx.
  assert_file "$EDIR/deliverables/synthesis.docx"             ".docx: synthesis"
  assert_file "$EDIR/deliverables/sop/record-to-report.docx"  ".docx: SOP (record-to-report)"
  assert_file "$EDIR/deliverables/improvements/record-to-report.docx" ".docx: improvements (record-to-report)"
  assert_file "$EDIR/deliverables/gap_report.docx"            ".docx: gap_report"

  # bundles non-empty (draft has L2 nodes; synth has node coverage).
  local draft_nodes synth_nodes
  draft_nodes="$("$PY" -c "import json;print(len(json.load(open('$EDIR/.draft_bundle.json'))['l2_nodes']))")"
  synth_nodes="$("$PY" -c "import json;d=json.load(open('$EDIR/.synth_bundle.json'));print(d['totals']['node_count'])")"
  assert_eq "5"  "$draft_nodes" "draft_inputs bundle lists the 5 R2R L2 nodes"
  assert_eq "37" "$synth_nodes" "synthesis_inputs bundle spans all 37 nodes"
}

# =============================================================================
# main
# =============================================================================
echo "T20 Slice-1 e2e regression test  (engagement=$EID)"
cleanup   # start clean even if a prior run left scratch behind

# ---- RUN 1 ------------------------------------------------------------------
run_pipeline "FIRST RUN" || { echo "PIPELINE RUN 1 ERRORED"; exit 1; }

# capture floor counts after run 1.
R1_TOTAL_EV="$(count_total_evidence)"
R1_VERBAL_EV="$(count_evidence_tier verbal)"
R1_IMP="$(count_type improvement)"
R1_GAP="$(count_type gap)"
R1_UNMAPPED="$(count_type unmapped)"
echo "RUN-1 counts: total_evidence=$R1_TOTAL_EV verbal_evidence=$R1_VERBAL_EV improvements=$R1_IMP gaps=$R1_GAP unmapped=$R1_UNMAPPED"

assert_state "AFTER RUN 1"

# ---- RUN 2 (idempotency floor) ---------------------------------------------
run_pipeline "SECOND RUN (idempotency)" || { echo "PIPELINE RUN 2 ERRORED"; exit 1; }

R2_TOTAL_EV="$(count_total_evidence)"
R2_VERBAL_EV="$(count_evidence_tier verbal)"
R2_IMP="$(count_type improvement)"
R2_GAP="$(count_type gap)"
R2_UNMAPPED="$(count_type unmapped)"
echo "RUN-2 counts: total_evidence=$R2_TOTAL_EV verbal_evidence=$R2_VERBAL_EV improvements=$R2_IMP gaps=$R2_GAP unmapped=$R2_UNMAPPED"

assert_state "AFTER RUN 2"

echo "----------------------------------------------------------------"
echo "IDEMPOTENCY ASSERTIONS (run1 == run2)"
echo "----------------------------------------------------------------"
assert_eq "$R1_TOTAL_EV"  "$R2_TOTAL_EV"  "total node-evidence count unchanged on re-run"
assert_eq "$R1_VERBAL_EV" "$R2_VERBAL_EV" "verbal-tier evidence count unchanged on re-run"
assert_eq "$R1_IMP"       "$R2_IMP"       "improvement count unchanged on re-run"
assert_eq "$R1_GAP"       "$R2_GAP"       "gap count unchanged on re-run"
assert_eq "$R1_UNMAPPED"  "$R2_UNMAPPED"  "unmapped count unchanged on re-run"

# ---- doc-drift lint (T48) ---------------------------------------------------
# No contract/schema may still advertise pre-build status, and no SKILL may
# reference the register engine by its bare (wrong) path. Matches the ACTUAL
# strings, not paraphrases.
echo "----------------------------------------------------------------"
echo "DOC-DRIFT LINT (T48)"
echo "----------------------------------------------------------------"

drift_no_code="$(grep -rIl -e 'no code yet' -e 'Not yet wired into code' \
  --include='*_contract.md' --include='*.json' "$REPO_ROOT" 2>/dev/null || true)"
if [ -z "$drift_no_code" ]; then
  ok "no contract/schema still says 'no code yet' / 'Not yet wired into code'"
else
  bad "stale build-status banner(s) found in: $drift_no_code"
fi

drift_bare_path="$(grep -rIn 'scripts/improvement_log.py' \
  --include='SKILL.md' "$REPO_ROOT" 2>/dev/null \
  | grep -v 'skills/consult-improvement-log/scripts/improvement_log.py' || true)"
if [ -z "$drift_bare_path" ]; then
  ok "no SKILL references a bare scripts/improvement_log.py path"
else
  bad "bare improvement_log.py path in SKILL: $drift_bare_path"
fi

# ---- summary ----------------------------------------------------------------
echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
if [ "$FAIL" -ne 0 ]; then exit 1; fi
echo "ALL ASSERTIONS PASS (incl. idempotent second run)."
exit 0
