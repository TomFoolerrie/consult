#!/usr/bin/env bash
# The orchestrator's path, end to end: a bare engagement dir driven only by `run.py next`,
# asserting what next says at every step, with the agents simulated by writing what they would write.
# This is the sequence the work computer will actually follow.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; LINTPY="$(cd "$HERE/../.." && pwd)/consult-lint/scripts/lint.py"; SK="$(cd "$HERE/.." && pwd)"; S="$SK/scripts"; LINT="$(cd "$SK/../consult-lint" && pwd)/scripts/lint.py"
E="$(mktemp -d "/tmp/Loop Test (2026).XXXX")"; cd "$E"
pass(){ echo "  ok  $1"; }; fail(){ echo "FAIL $1"; echo "--- last next: $NEXT"; exit 1; }
git config --global user.email >/dev/null 2>&1 || { git config --global user.email loop@test; git config --global user.name loop; }
NEXT=""; nxt(){ NEXT="$(python3 "$S"/run.py next "$@" 2>&1 | tail -1)"; }
expect(){ echo "$NEXT" | grep -q "$1" && pass "next → $2" || fail "expected '$1' ($2)"; }

# --- a realistic-ish engagement: profile, org chart, 2 interviews + a summary, a checklist, a JE csv, an unrelated policy
git init -q .
mkdir -p _client/interviews _client/data _synthesis _workspace
cat > _client/profile.md << 'EOF'
Acme Realty: regional brokerage, ~120 agents, 3-person finance team (CFO, Controller, staff accountant). First audit next spring. CFO believes the problems are systems-driven.
EOF
printf '# Org chart\nCFO\n  Controller (AP, close, JEs)\n  Staff accountant (payroll, commissions)\n' > _client/org-chart.md
printf '# Engagement objective\nPre-audit readiness assessment; deliverable is a board deck.\n' > engagement_objective
printf '# Interview - Controller\nQ: How are manual JEs approved?\nA: I post them. Nobody else approves; the CFO looks at the P&L at month end.\nQ: Clawbacks?\nA: Tracked in a spreadsheet, not reconciled to the GL.\nQ: Bank recs?\nA: Done within three days every month, CFO signs.\n' > _client/interviews/controller.md
printf '# Interview - CFO\nQ: Controls over JEs?\nA: The controller and I review every manual entry together before posting.\nQ: Biggest risk?\nA: Total Brokerage: the commission system nobody understands.\n' > _client/interviews/cfo.md
printf '# Summary - Controller interview\n- JEs posted without second approval\n- Clawback spreadsheet unreconciled\n- Bank recs timely\n' > _client/interviews/controller-summary.md
printf '# Close checklist (Jul)\nBank rec - done 8/3 - CFO\nClawback recon - n/a\nJE review - n/a\n' > _client/close-checklist.md
printf 'je_no,date,user,amount\nJE-1,2026-07-05,controller,25000\nJE-2,2026-07-06,controller,120.5\nJE-3,2026-07-07,controller,1000\nJE-4,2026-08-02,controller,99999\n' > _client/data/je-listing.csv
printf '# Travel policy\nEmployees submit expenses monthly.\n' > _client/travel-policy.md
git add -A && git commit -qm "sources"

echo "== pre-loop"
nxt --root .; expect "no registry" "register the sources"
python3 "$LINTPY" register --in _client --ext md,csv --exclude profile.md --registry _client/registry.yaml >/dev/null
nxt --root .; expect "HUMAN.*no \`kind\`" "human annotates the registry"
python3 - << 'PY'
import yaml; p='_client/registry.yaml'; r=yaml.safe_load(open(p))
kinds={'org-chart.md':('org-chart',None,None),'interviews/controller.md':('interview','close','Controller'),'interviews/cfo.md':('interview','close','CFO'),
       'interviews/controller-summary.md':('summary','close',None),'close-checklist.md':('checklist','close',None),'data/je-listing.csv':('data','close',None),'travel-policy.md':('policy',None,None)}
for s in r['sources']:
    k,t,pp=kinds[s['file']]; s['kind']=k
    if t: s['topic']=t
    if pp: s['people']=pp
    if s['file']=='org-chart.md': s['pre_read_candidate']=True
    if k=='summary': s['summary_of']=next(x['id'] for x in r['sources'] if x['file']=='interviews/controller.md')
yaml.safe_dump(r,open(p,'w'),sort_keys=False)
PY
nxt --root .; expect "draft the manifest" "draft the manifest (profile found)"
python3 "$S"/manifest.py draft --registry _client/registry.yaml --out _synthesis/assessment/manifest.yaml --context _client/profile.md \
  --ledger-dir _synthesis/assessment/ledgers --workdir _workspace/assessment --out-dir _synthesis/assessment/out >/dev/null
M=_synthesis/assessment/manifest.yaml
python3 - "$M" << 'PY'
import sys,yaml; m=yaml.safe_load(open(sys.argv[1]))
assert len(m['groups'])==1 and m['groups'][0].get('topic')=='close', m['groups']
assert len(m['deferred_groups'])==1, m['deferred_groups']
# a data group that builds on the interview group, deferred; plus engagement_objective as a pre-read
g=m['groups'][0]; g['note']="how does the close actually run and who controls it?"; g['pre_read'].append('../../engagement_objective')
# split the data file out of the topic group into its own builds_on group so waves are exercised
data=[s for s in g['sources'] if s.endswith('006') or s.endswith('05') or s.endswith('006')]
m['story_note']="Client thinks it has a systems problem; lead with fig-dimensions"
yaml.safe_dump(m,open(sys.argv[1],'w'),sort_keys=False)
PY
pass "manifest: one topic group active (interviews+summary+checklist+data), one deferred"
git add -A && git commit -qm manifest
nxt --root .; expect "ledger.py.*init" "init the ledger"
python3 "$S"/ledger.py init --ledger-dir _synthesis/assessment/ledgers >/dev/null
python3 "$S"/ledger.py --ledger-dir _synthesis/assessment/ledgers checkpoint -m "before extract" >/dev/null
echo "== extract, gate"
nxt --root .; expect "op extract --group G1" "extract the first group (pre-reads small: no digest)"
B=$(python3 "$S"/run.py render --manifest $M --op extract --group G1 --format brief)
grep -q "je-listing.csv.*TABULAR" "$B" && grep -q "controller.md.*read fully" "$B" && grep -q "assess.py data profile" "$B" && python3 -c "import yaml;g=yaml.safe_load(open(\"$M\"))[\"groups\"][0][\"sources\"];import sys;r=yaml.safe_load(open(\"_client/registry.yaml\"))[\"sources\"];k={s[\"id\"]:s[\"kind\"] for s in r};ks=[k[x] for x in g];assert ks[0]==\"interview\" and ks[-1]==\"data\" and \"summary\" in ks[:3],ks" && pass "brief: csv is TABULAR, interviews read fully; group ordered interviews → summary → artifacts → data"
SH="python3 _workspace/assessment/assess.py"
# simulate reader-G1: reads interviews + checklist, runs data procedures on the csv, logs findings citing both
CTRL=$(python3 -c "import yaml;print(next(s['id'] for s in yaml.safe_load(open('_client/registry.yaml'))['sources'] if s['file']=='interviews/controller.md'))")
CFO=$(python3 -c "import yaml;print(next(s['id'] for s in yaml.safe_load(open('_client/registry.yaml'))['sources'] if s['file']=='interviews/cfo.md'))")
SUM=$(python3 -c "import yaml;print(next(s['id'] for s in yaml.safe_load(open('_client/registry.yaml'))['sources'] if s['file']=='interviews/controller-summary.md'))")
CHK=$(python3 -c "import yaml;print(next(s['id'] for s in yaml.safe_load(open('_client/registry.yaml'))['sources'] if s['file']=='close-checklist.md'))")
JE=$(python3 -c "import yaml;print(next(s['id'] for s in yaml.safe_load(open('_client/registry.yaml'))['sources'] if s['file']=='data/je-listing.csv'))")
$SH data profile $JE >/dev/null 2>&1 && $SH data run timing $JE --date date --period-end 2026-07-31 > /tmp/lt.out 2>&1 && AN=$(grep -o "registered as src-[0-9]*" /tmp/lt.out | grep -o "src-[0-9]*") && pass "reader ran a data procedure via the shim → $AN registered"
cat > _workspace/assessment/G1-rows.jsonl << EOF
{"type":"gap","business_cycle":"Financial Close, JEs & Estimates","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Governance","severity":3,"evidence_basis":"stated","observation":"Controller posts manual JEs with no second approver.","sources":["$CTRL:L3","$SUM:L2"]}
{"type":"gap","business_cycle":"Financial Close, JEs & Estimates","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Governance","severity":3,"evidence_basis":"stated","observation":"CFO states every manual JE is reviewed jointly before posting - contradicts the controller's account.","sources":["$CFO:L3"],"related":["F-001"]}
{"type":"observation","business_cycle":"Financial Close, JEs & Estimates","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Governance","severity":3,"evidence_basis":"observed","observation":"July close checklist marks JE review as n/a; no evidence of the joint review the CFO described.","sources":["$CHK:L4"],"related":["F-002"]}
{"type":"gap","business_cycle":"Financial Close, JEs & Estimates","focus_area":"Pre-Audit Readiness","assertions":["Cut-off"],"dimension":"Process","severity":2,"evidence_basis":"observed","observation":"2 of 4 July JEs posted on weekends and one posted 8/2 after period end, all by the controller.","sources":["$JE:L5","$AN:L9"]}
{"type":"gap","business_cycle":"Agent Commission COGS, Payable & Clawbacks","focus_area":"Pre-Audit Readiness","assertions":["Completeness","Accuracy"],"dimension":"Process","severity":2,"evidence_basis":"stated","observation":"Clawbacks tracked in a spreadsheet not reconciled to the GL.","sources":["$CTRL:L5"]}
{"type":"strength","business_cycle":"Cash & Escrow / Trust Accounts","focus_area":"Pre-Audit Readiness","assertions":["Existence / Occurrence"],"dimension":"Process","severity":1,"evidence_basis":"observed","observation":"Bank reconciliation completed 8/3 with CFO sign-off, consistent with the controller's account.","sources":["$CHK:L2","$CTRL:L7"]}
{"type":"open_item","business_cycle":"IT General Controls & Service Organizations","focus_area":"Pre-Audit Readiness","assertions":["Pervasive / control environment"],"dimension":"Systems / Technology","severity":2,"evidence_basis":"stated","observation":"CFO names the commission system as the biggest risk; no artifact or walkthrough of it was provided.","sources":["$CFO:L5"]}
EOF
$SH ledger append findings --author reader-G1 --group G1 --from _workspace/assessment/G1-rows.jsonl >/dev/null 2>&1 && pass "reader-G1 appended 7 findings via the shim"
$SH validate > /tmp/lv.out && grep -q "0 errors" /tmp/lv.out && pass "validate: clean (citations into interviews, summary, checklist, csv, analysis all resolve)"
python3 "$S"/run.py check --manifest $M > /tmp/lc.out && grep -q "UNCOVERED" /tmp/lc.out && pass "check: coverage report present"
$SH ledger checkpoint -m "extract G1" >/dev/null
nxt --root .; expect "HUMAN.*findings gate" "findings gate (G1 complete: every source cited)"
python3 "$S"/run.py status --manifest $M | grep -q "G1 .*complete .*5/5" && pass "status: G1 5/5 sources"
python3 "$S"/run.py gate --manifest $M --name findings --status passed --note "rubric ok" >/dev/null
nxt --root .; expect "restore the 1 deferred groups" "restore deferred groups"
python3 - "$M" << 'PY'
import sys,yaml; m=yaml.safe_load(open(sys.argv[1])); d=m.pop('deferred_groups');
for g in d: g['builds_on']=['G1']; g['note']="policies - test what interviews claimed"
m['groups']+=d; yaml.safe_dump(m,open(sys.argv[1],'w'),sort_keys=False)
PY
nxt --root .; expect "fan out wave: for G in G2" "fan-out wave (G2 builds on complete G1)"
B2=$(python3 "$S"/run.py render --manifest $M --op extract --group G2 --format brief)
grep -q "Findings so far from G1 (6)" "$B2" && grep -q "Open questions earlier readers left (1)" "$B2" && grep -q "Nothing logged yet on:" "$B2" && pass "G2 brief: prior index (6 findings), 1 open question, uncovered categories — after sources"
POL=$(python3 -c "import yaml;print(next(s['id'] for s in yaml.safe_load(open('_client/registry.yaml'))['sources'] if s['file']=='travel-policy.md'))")
echo "{\"type\":\"observation\",\"business_cycle\":\"Corporate AP, Cards & Accruals (P2P)\",\"focus_area\":\"Process Effectiveness\",\"process_attribute\":\"Documentation\",\"dimension\":\"Process\",\"severity\":1,\"evidence_basis\":\"observed\",\"observation\":\"Reviewed in full; travel policy is one line, nothing material to scope.\",\"sources\":[\"$POL:L1\"]}" | $SH ledger append findings --author reader-G2 --group G2 >/dev/null 2>&1
$SH ledger checkpoint -m "extract G2" >/dev/null
nxt --root .; expect "op retro --phase extract" "retro after fan-out"
touch _workspace/assessment/retro-extract.md
echo "== normalize, revise, layers"
nxt --root .; expect "op normalize" "normalize"
$SH ledger propose --proposer normalizer --target F-001 --kind link --set related=F-003 --reason "artifact corroborates" >/dev/null
python3 "$S"/run.py gate --manifest $M --name normalized --status done >/dev/null
nxt --root .; expect "revise: for each of \['reader-G1'\]" "revise for the author with open proposals"
B1e=$(python3 "$S"/run.py render --manifest $M --op revise --group G1 --format brief); grep -q "P-001: link on F-001" "$B1e" && pass "revise brief lists the proposal"
$SH ledger edit F-001 --author reader-G1 --set related=F-003 --reason "per P-001" >/dev/null && $SH ledger resolve P-001 --status accepted >/dev/null
nxt --root .; expect "HUMAN.*second look" "second look"
python3 "$S"/run.py gate --manifest $M --name revise --status passed >/dev/null
nxt --root .; expect "op themes" "themes"
echo '{"theme":"JE control exists on paper only","root_cause":"Two people describe the JE control differently and the artifact shows neither version operating.","dimension":"Governance","impact":"Auditor will test 100% of manual JEs or qualify.","findings":["F-001","F-002","F-003","F-004"]}' | $SH ledger append themes --author themer >/dev/null
$SH validate --gate themes >/dev/null && $SH ledger checkpoint -m themes >/dev/null
nxt --root .; expect "op recommend" "recommend"
echo '{"solution":"Independent JE approval before posting","principle":"Separate preparer from approver","themes":["T-001"]}' | $SH ledger append recommendations --author recommender >/dev/null
nxt --root .; expect "op plan" "plan"
echo '{"initiative":"JE approval workflow","owner":"CFO","impact":3,"effort":1,"time_required":"one close","success_measure":"100% of manual JEs show approver != preparer","recommendations":["R-001"]}' | $SH ledger append initiatives --author planner >/dev/null
nxt --root .; expect "render.py\"* figures" "render figures + tables"
$SH render figures >/dev/null && $SH render tables >/dev/null
nxt --root .; expect "op story" "story (story_note already set)"
printf '# Acme\n\nThe JE control exists on paper only [T-001]: the controller and CFO describe it differently [F-001, F-002] and the checklist shows it not operating [F-003]. The listing shows weekend and post-close postings [F-004, fig-heatmap].\n' > _synthesis/assessment/out/story.md
nxt --root .; expect "render.py.*bundle" "bundle"
$SH render bundle >/dev/null && test -f _synthesis/assessment/out/assessment-output.json && test -f _synthesis/assessment/out/story-client.md && pass "bundle + client story written"
nxt --root .; expect "op retro --phase layers" "layers retro"
touch _workspace/assessment/retro-layers.md
nxt --root .; expect "DONE" "DONE"
$SH ledger checkpoint -m final >/dev/null; git -C "$E" log --oneline | grep -c "F=" | grep -q "[5-9]" && pass "git history shows a checkpoint per op"
echo; echo "LOOP PASS  ($E)"
