#!/usr/bin/env bash
# Exercises every op and the ownership rule on the fixture. Exit non-zero on any failure.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; LINTPY="$(cd "$HERE/../.." && pwd)/consult-lint/scripts/lint.py"; SK="$HERE/.."; S="$SK/scripts"
W="$(mktemp -d)"; L="$W/ledgers"; export ASSESS_LEDGER_DIR="$L"
TAX="$SK/assets/taxonomy.yaml"; SRC="$HERE/fixture/sources"; REG="$SRC/registry.yaml"
pass(){ echo "  ok  $1"; }; fail(){ echo "FAIL $1"; exit 1; }
git config --global user.email >/dev/null 2>&1 || { git config --global user.email smoke@test; git config --global user.name smoke; }

echo "init guards"
echo '{"x":1}' | python3 "$S"/ledger.py append findings --author r 2>/dev/null && fail "write to uninitialized dir accepted" || pass "uninitialized ledger dir refused"
mkdir -p "$L"; python3 "$S"/ledger.py init 2>/dev/null && fail "init outside git accepted" || pass "init outside git refused"
python3 "$S"/ledger.py init --allow-no-git >/dev/null && rm "$L/.assessment-ledger" && pass "init --allow-no-git works"
python3 "$S"/ledger.py init --git-init >/dev/null && test -d "$W/.git" && pass "init --git-init created repo at engagement root"
python3 "$S"/ledger.py init --ledger-dir $L >/dev/null && python3 "$S"/ledger.py --ledger-dir $L init >/dev/null && pass "--ledger-dir accepted before or after the subcommand"

echo "extract (two readers)"
python3 "$S"/ledger.py append findings --author reader-G1 --group G1 --from - <<'J' >/dev/null
{"type":"gap","business_cycle":"Financial Close, JEs & Estimates","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Governance","severity":3,"evidence_basis":"stated","observation":"Controller posts manual JEs with no second approver; no approval matrix exists.","sources":["src-002:L2-L3"]}
{"type":"gap","business_cycle":"Agent Commission COGS, Payable & Clawbacks","focus_area":"Pre-Audit Readiness","assertions":["Completeness","Accuracy"],"dimension":"Process","severity":2,"evidence_basis":"stated","observation":"Clawbacks tracked in a spreadsheet not reconciled to the GL.","sources":["src-002:L4-L5"]}
{"type":"strength","business_cycle":"Cash & Escrow / Trust Accounts","focus_area":"Pre-Audit Readiness","assertions":["Existence / Occurrence"],"dimension":"Process","severity":1,"evidence_basis":"stated","observation":"Bank reconciliations completed within three days with CFO sign-off.","sources":["src-002:L6-L7"]}
J
python3 "$S"/ledger.py append findings --author reader-G2 --group G2 --from - <<'J' >/dev/null
{"type":"observation","business_cycle":"Financial Close, JEs & Estimates","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Governance","severity":3,"evidence_basis":"observed","observation":"July close checklist marks JE review as n/a.","sources":["src-003:L4"]}
{"type":"strength","business_cycle":"Cash & Escrow / Trust Accounts","focus_area":"Pre-Audit Readiness","assertions":["Existence / Occurrence"],"dimension":"Process","severity":1,"evidence_basis":"observed","observation":"July bank rec completed 8/3 with CFO sign-off.","sources":["src-003:L2"]}
{"type":"gap","business_cycle":"Entity-Level / Governance & Control Environment","focus_area":"Process Effectiveness","process_attribute":"Handoffs & ownership","dimension":"People & Organization","severity":2,"evidence_basis":"observed","observation":"Controller owns AP, JEs, and close with no segregation.","sources":["src-001:L3"]}
J
pass "6 findings appended"

echo "encoding (simulate a cp1252 console)"
printf '{"type":"observation","business_cycle":"Payroll & Payroll Taxes","focus_area":"Process Effectiveness","process_attribute":"Manual effort","dimension":"Process","severity":1,"evidence_basis":"stated","observation":"Payroll → GL tie-out is manual — em-dash and arrow survive","sources":["src-001:L1"]}\n' > $W/utf.jsonl
PYTHONIOENCODING=cp1252 LC_ALL=C python3 "$S"/ledger.py append findings --author reader-G1 --group G1 --from $W/utf.jsonl > $W/utf.out 2>&1 && grep -q "^F-007" $W/utf.out && PYTHONIOENCODING=cp1252 LC_ALL=C python3 "$S"/ledger.py show findings > $W/utf.show && grep -q "em-dash and arrow survive" $W/utf.show && grep -q "→" $W/utf.show && pass "non-ASCII round-trips through append/show under a cp1252 console" || { cat $W/utf.out; fail encoding; }
python3 "$S"/ledger.py retire F-007 --author reader-G1 --reason "encoding test row" >/dev/null

echo "refusals"
echo '{"type":"gap","business_cycle":"Payroll & Payroll Taxes","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Data","severity":1,"evidence_basis":"stated","observation":"x"}' \
  | python3 "$S"/ledger.py append findings --author reader-G1 2>/dev/null && fail "unsourced finding accepted" || pass "unsourced finding refused"
python3 "$S"/ledger.py edit F-004 --author reader-G1 --set severity=1 --reason x 2>/dev/null && fail "cross-author edit accepted" || pass "cross-author edit refused"

echo "validate findings"
python3 "$S"/validate.py --taxonomy "$TAX" --registry "$REG" >/dev/null || fail "clean ledger failed validation"; pass "validate clean"
echo '{"type":"gap","business_cycle":"Nope","focus_area":"Pre-Audit Readiness","dimension":"Data","severity":9,"evidence_basis":"stated","observation":"bad","sources":["src-009:L1"]}' \
  | python3 "$S"/ledger.py append findings --author reader-G1 >/dev/null
{ python3 "$S"/validate.py --taxonomy "$TAX" --registry "$REG" 2>/dev/null || true; } | grep -q "not in axes.business_cycle" && pass "validate catches bad enum/source" || fail "validator missed bad row"
echo '{"type":"gap","business_cycle":"Payroll & Payroll Taxes","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Data","severity":1,"evidence_basis":"stated","observation":"cites past EOF","sources":["src-003:L99"]}' | python3 "$S"/ledger.py append findings --author reader-G1 >/dev/null
{ python3 "$S"/validate.py --taxonomy "$TAX" --registry "$REG" 2>/dev/null || true; } | grep -q "cites line 99 but file has" && pass "validate catches citation past end of file" || fail "line range check"
python3 "$S"/ledger.py retire F-009 --author reader-G1 --reason "test row" >/dev/null
cp "$SRC"/src-003.md $W/src-003.bak && echo "edited" >> "$SRC"/src-003.md
{ python3 "$S"/validate.py --taxonomy "$TAX" --registry "$REG" 2>/dev/null || true; } | grep -q "changed since registration" && pass "validate catches drifted source file" || fail "drift check"
mv $W/src-003.bak "$SRC"/src-003.md
python3 "$S"/ledger.py retire F-008 --author reader-G1 --reason "test row" >/dev/null

echo "normalize -> propose -> gate -> revise"
python3 "$S"/ledger.py propose --proposer normalizer --target F-001 --kind merge --absorb F-004 --reason "same JE approval gap" >/dev/null
python3 "$S"/validate.py --taxonomy "$TAX" --gate themes >/dev/null 2>&1 && fail "gate passed with open proposal" || pass "gate blocks on open proposal"
python3 "$S"/ledger.py merge F-001 F-004 --author reader-G1 --reason "per P-001" 2>/dev/null && fail "cross-author merge accepted" || pass "cross-author merge refused"
python3 "$S"/ledger.py propose --proposer normalizer --target F-002 --kind link --set related=F-006 --reason "link kind accepted" >/dev/null && pass "link proposal kind"
python3 "$S"/ledger.py resolve P-002 --status rejected --note test >/dev/null
python3 "$S"/ledger.py edit F-002 --author reader-G1 --set evidence_basis=inferred --reason "test setup" >/dev/null
python3 "$S"/ledger.py merge F-002 F-003 --author reader-G1 --reason x 2>/dev/null && fail "merge across evidence basis accepted" || pass "merge across evidence basis refused"
python3 "$S"/ledger.py edit F-002 --author reader-G1 --set evidence_basis=stated --reason "test teardown" >/dev/null
python3 "$S"/ledger.py edit F-001 --author reader-G1 --set related=F-004 --reason "corroborated by G2 artifact; keeping both (stated vs observed)" >/dev/null
python3 "$S"/ledger.py resolve P-001 --status rejected --note "different evidence basis; linked instead" >/dev/null
python3 "$S"/validate.py --taxonomy "$TAX" --gate themes >/dev/null || fail "gate failed after resolve"; pass "gate clears after resolve"

echo "themes / recommend / plan"
echo '{"theme":"Close controls depend on one person","root_cause":"A three-person team with no designated reviewer means preparer and approver are the same role.","dimension":"People & Organization","impact":"JE accuracy is unevidenced; auditor will test 100% or qualify.","findings":["F-001","F-004","F-006"]}' | python3 "$S"/ledger.py append themes --author themer >/dev/null
echo '{"theme":"Bad","root_cause":"x","dimension":"Data","impact":"y","findings":["src-002:L3"]}' | python3 "$S"/ledger.py append themes --author themer >/dev/null
{ python3 "$S"/validate.py --taxonomy "$TAX" 2>/dev/null || true; } | grep -q "cites raw source" && pass "layer-below rule enforced" || fail "theme citing raw source passed"
python3 "$S"/ledger.py retire T-002 --author themer --reason test >/dev/null
echo '{"solution":"Introduce an independent JE reviewer","principle":"Separate preparer from approver","what_changes":"CFO approves JEs above threshold before posting","what_stops":"Post-hoc P&L review as the only control","themes":["T-001"]}' | python3 "$S"/ledger.py append recommendations --author recommender >/dev/null
echo '{"initiative":"JE approval workflow in the GL","owner":"Controller","impact":3,"effort":1,"time_required":"one close cycle","success_measure":"100% of manual JEs show approver ≠ preparer","recommendations":["R-001"]}' | python3 "$S"/ledger.py append initiatives --author planner >/dev/null
python3 "$S"/validate.py --taxonomy "$TAX" --registry "$REG" --gate initiatives >/dev/null || fail "full chain invalid"; pass "full chain valid"

echo "checkpoint"
python3 "$S"/ledger.py checkpoint -m "after plan" > $W/ck && grep -q "F=9 T=2 R=1 I=1 P=2" $W/ck && pass "checkpoint commits with layer counts" || { cat $W/ck; fail checkpoint; }
python3 "$S"/ledger.py checkpoint | grep -q "nothing" && pass "checkpoint is idempotent"
git -C $W log --oneline | grep -q "after plan" && pass "commit visible in git log"

echo "trace / render"
python3 "$S"/trace.py > $W/trace.md; grep -q "findings_in_no_theme: 3" $W/trace.md && pass "trace finds 3 orphans (F-002 + 2 strengths)" || { cat $W/trace.md; fail "trace orphan count"; }
python3 "$S"/render.py bundle --taxonomy "$TAX" --out $W/out >/dev/null
test -f $W/out/figures/fig-heatmap.json && test -f $W/out/figures/fig-process.json && test -f $W/out/figures/fig-unthemed.json && test -f $W/out/assessment-output.json && pass "bundle written (incl. process + unthemed)" || fail "bundle missing"
python3 -c "import json;d=json.load(open('$W/out/figures/fig-heatmap.json'));c=[x for x in d['data']['cells'] if x['row'].startswith('Financial Close')][0];assert c['findings']==2 and c['themes']==1,c" && pass "heatmap: 2 findings, 1 theme in the JE cell"
python3 -c "import json;d=json.load(open('$W/out/figures/fig-unthemed.json'));assert [i['id'] for i in d['data']['items']]==['F-002'],d" && pass "unthemed lists F-002 only"
python3 -c "import json;d=json.load(open('$W/out/figures/fig-dimensions.json'));assert d['data']['themes'][0]==1 and sum(d['data']['findings'])==4,d['data']" && pass "dimensions: theme series + findings series"
python3 "$S"/manifest.py draft --registry "$REG" --out $W/manifest.yaml >/dev/null && grep -q "reader-G1" $W/manifest.yaml && grep -q "src-001.md" $W/manifest.yaml && pass "manifest drafted from registry (org chart as pre-read)"
python3 - "$W/topics.yaml" << 'PY'
import sys, yaml
srcs=[]
def add(i, kind, words, **kw): srcs.append({"id":f"src-{i:03d}","file":f"f{i}.md","sha":str(i),"lines":10,"words":words,"status":"active","kind":kind,**kw})
add(1,"org-chart",50,pre_read_candidate=True)
add(2,"interview",9000,people="Controller",topic="close"); add(3,"summary",800,summary_of="src-002",topic="close"); add(4,"checklist",300,topic="close"); add(5,"data",5000,topic="close")
add(6,"interview",8000,people="Sales ops",topic="commissions"); add(7,"policy",1500,topic="commissions"); add(8,"data",7000,topic="commissions")
for i in range(9,21): add(i,"policy",1200)   # 12 untagged policies
yaml.safe_dump({"sources":srcs}, open(sys.argv[1],"w"), sort_keys=False)
PY
python3 "$S"/manifest.py draft --registry $W/topics.yaml --out $W/topics-m.yaml --all-groups > $W/tm.out 2>&1
python3 - "$W/topics-m.yaml" << 'PY' && pass "draft: topic groups keep interview+summary+artifact+data together; summary follows its transcript; untagged policies batched"
import sys, yaml; m=yaml.safe_load(open(sys.argv[1])); g={x["id"]:x for x in m["groups"]}
byt={x.get("topic"):x for x in m["groups"] if x.get("topic")}
assert byt["close"]["sources"]==["src-002","src-003","src-004","src-005"], byt["close"]
assert byt["commissions"]["sources"]==["src-006","src-007","src-008"], byt["commissions"]
assert len(m["groups"])==3, [x["sources"] for x in m["groups"]]
PY
mkdir -p $W/deep/er && python3 "$S"/manifest.py draft --registry "$REG" --out $W/deep/er/m.yaml --ledger-dir $W/led --context "$HERE"/fixture/context/profile.md >/dev/null && grep -q "ledger_dir: ../../led" $W/deep/er/m.yaml && pass "draft stores paths relative to the manifest file"
(cd $W && python3 "$S"/run.py next --root . 2>/dev/null | grep -q "several manifests\|using manifest\|draft the manifest\|RUN\|HUMAN") && pass "next --root works without --manifest"

echo "run.py (orchestrator entry)"
M=$W/manifest.yaml
python3 - "$M" "$L" "$W" "$REG" "$SRC" << 'PY'
import sys, yaml
m, L, W, REG, SRC = sys.argv[1:]
d = yaml.safe_load(open(m))
d.pop("ledger_dir", None); d.pop("workdir", None); d.pop("out", None)
d["paths"] = {"ledger_dir": L, "workdir": W+"/scratch", "out": W+"/deliverable", "prompts": "{workdir}/agent-briefs",
              "gates": "{workdir}/decisions.json", "tables": "{out}/tbl", "figures": "{out}/viz", "story": "{out}/narrative.md",
              "bundle": "{out}/final/assessment.json"}
d["agents"] = {"reader": "rdr-{group}", "themes": "theme-builder", "story": "narrator"}
d.update(registry=REG, context=SRC+"/../context/profile.md", story_note="Client thinks it has a systems problem")
d["groups"] = [{"id":"G1","agent":"reader-G1","pre_read":[SRC+"/src-001.md", SRC+"/../context/profile.md"],"sources":["src-002","src-003"],"note":"finance leadership"},
               {"id":"G2","pre_read":[],"sources":["src-003"],"note":"x"}]
d["deferred_groups"] = [{"id":"G3","pre_read":[],"sources":["src-001","src-002"],"note":"deferred","builds_on":["G1"]}]
yaml.safe_dump(d, open(m,"w"), sort_keys=False)
PY
P=$(python3 "$S"/run.py render --manifest $M --op extract --group G1)
test -f "$P" && ! grep -q "{{" "$P" && grep -q "src-002 → " "$P" && grep -q "assess.py ledger" "$P" && pass "render: reader prompt fully filled, commands via shim" || { grep -n "{{" "$P"; fail render; }
echo "$P" | grep -q "scratch/agent-briefs/reader-G1.md" && pass "render: prompt lands where the manifest says (custom prompts dir)"
P2=$(python3 "$S"/run.py render --manifest $M --op extract --group G2); echo "$P2" | grep -q "rdr-G2.md" && pass "agents: reader pattern from manifest applied to a group without explicit agent"
P3=$(python3 "$S"/run.py render --manifest $M --op themes); echo "$P3" | grep -q "theme-builder.md" && grep -q "You are \`theme-builder\`" "$P3" && pass "agents: custom name for a layer agent"
P4=$(python3 "$S"/run.py render --manifest $M --op story); grep -q "deliverable/tbl" "$P4" && grep -q "deliverable/narrative.md" "$P4" && pass "story prompt uses manifest-named tables/story locations"
P=$(python3 "$S"/run.py render --manifest $M --op revise --group G1)
grep -q "mode: edit" "$P" && grep -q "Open proposals addressed to you" "$P" && pass "render: revise mode lists proposals"
B=$(python3 "$S"/run.py render --manifest $M --op extract --group G1 --format brief)
echo "$B" | grep -q "reader-G1.brief.md" && ! grep -q "{{" "$B" && ! grep -q "A finding is one specific" "$B" && grep -q "src-002 → " "$B" && pass "render --format brief: per-run part only, no static body"
grep -q "assess.py ledger append findings --author reader-G1" "$B" && ! grep -q "scripts/ledger.py" "$B" && test -f $W/scratch/assess.py && pass "brief uses the shim; no skill script paths exposed"
(cd $W && python3 scratch/assess.py ledger next-id findings > $W/sh1 && python3 scratch/assess.py taxonomy > $W/sh2 && python3 scratch/assess.py validate --gate initiatives > $W/sh3) && grep -q "^F-" $W/sh1 && grep -q "^axes:" $W/sh2 && grep -q "0 errors" $W/sh3 && pass "shim: ledger / taxonomy / validate work from the root" || { cat $W/sh1 $W/sh3 2>/dev/null | tail -3; fail shim; }
grep -q "A finding is one specific" "$P" && grep -q "src-002 → " "$P" && pass "render --format full: static body + brief"
python3 "$S"/run.py agents --out $W/agents --prefix assess- > $W/ag && test -f $W/agents/assess-reader.md && head -1 $W/agents/assess-reader.md | grep -q "^---$" && grep -q "^name: assess-reader$" $W/agents/assess-reader.md && grep -q "^tools: Read, Write, Bash, Grep, Glob$" $W/agents/assess-reader.md && grep -q "^model: inherit$" $W/agents/assess-reader.md && ! grep -q "{{" $W/agents/assess-reader.md && pass "agents: six subagent files with frontmatter, no placeholders"
test $(ls $W/agents | wc -l) -eq 6 && pass "agents: one per role"
python3 "$S"/run.py agents --out $W/agents2 --with-orchestrator >/dev/null && grep -q "^tools: Agent(assess-reader, assess-normalizer" $W/agents2/assess-orchestrator.md && grep -q "run.py next" $W/agents2/assess-orchestrator.md && pass "agents --with-orchestrator: allowlisted spawner with the runbook as body"
for op in normalize themes recommend plan story digest; do P=$(python3 "$S"/run.py render --manifest $M --op $op); grep -q "{{" "$P" && fail "unfilled in $op"; done
P=$(python3 "$S"/run.py render --manifest $M --op retro --phase extract); grep -q "{{" "$P" && fail "unfilled in retro"; pass "render: all ops fill cleanly (incl. digest, retro)"
python3 "$S"/run.py agents --out $W/agents3 >/dev/null && test $(ls $W/agents3 | wc -l) -eq 8 && pass "agents: eight roles incl. digester and retrospector"
grep -q "context-digest.md" "$(python3 "$S"/run.py render --manifest $M --op digest --format brief)" && pass "digest brief names the digest path"
python3 "$S"/run.py next --manifest $M | grep -q "HUMAN.*findings gate" && pass "next: asks for the findings gate after first group"
python3 "$S"/run.py status --manifest $M > $W/st1; grep -q "G1 .*complete .*2/2" $W/st1 && grep -q "G3 (deferred)" $W/st1 && pass "status: per-source completion and deferred groups listed"
sed -n '/^Pre-reads/,/^Reference/p' "$B" | grep -q "profile.md" && fail "context duplicated into pre_read" || pass "context file not duplicated into the pre-read list (bug 4)"
grep -q "read fully" "$B" && pass "brief carries a reading strategy per source"
python3 "$S"/run.py gate --manifest $M --name findings --status passed >/dev/null
test -f $W/scratch/decisions.json && pass "gates file lands where the manifest says"
python3 "$S"/run.py next --manifest $M | grep -q "restore the 1 deferred groups" && pass "next: after the gate, asks to restore deferred groups (the runbook's promise)"
python3 - "$M" << 'PY'
import sys,yaml; m=yaml.safe_load(open(sys.argv[1])); m["groups"] += m.pop("deferred_groups"); yaml.safe_dump(m,open(sys.argv[1],"w"),sort_keys=False)
PY
python3 "$S"/run.py next --manifest $M | grep -q "fan out wave: for G in G2 G3" && pass "next: fan-out lists restored + remaining groups (G3 builds on complete G1 -> same wave)"
python3 - "$M" << 'PY'
import sys,yaml; m=yaml.safe_load(open(sys.argv[1])); [g.__setitem__("builds_on",["G2"]) for g in m["groups"] if g["id"]=="G3"]; yaml.safe_dump(m,open(sys.argv[1],"w"),sort_keys=False)
PY
python3 "$S"/run.py next --manifest $M | grep -q "fan out wave: for G in G2:" && python3 "$S"/run.py next --manifest $M | grep -q "then \['G3'\] become spawnable" && pass "next: waves - G3 waits for G2"
B3p=$(python3 "$S"/run.py render --manifest $M --op extract --group G3 --format brief); grep -q "Findings so far from G2" "$B3p" || grep -q "Findings so far from" "$B3p" || grep -q "reads blind" "$B3p"; grep -q "Prior findings — for the SITUATE pass only" "$B3p" && pass "brief: prior-findings section present, after sources"
echo '{"type":"gap","business_cycle":"Payroll & Payroll Taxes","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Data","severity":1,"evidence_basis":"stated","observation":"g2 row","sources":["src-003:L2"]}' | python3 "$S"/ledger.py append findings --author rdr-G2 --group G2 >/dev/null 2>&1
echo '{"type":"gap","business_cycle":"Payroll & Payroll Taxes","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Data","severity":1,"evidence_basis":"stated","observation":"g3 partial","sources":["src-001:L2"]}' | python3 "$S"/ledger.py append findings --author rdr-G3 --group G3 >/dev/null 2>&1
python3 "$S"/run.py next --manifest $M | grep -q "G3 is PARTIAL: 1/2 sources logged, remaining \['src-002'\]" && pass "next: a half-written group is PARTIAL, not complete (bug 1)"
B3q=$(python3 "$S"/run.py render --manifest $M --op extract --group G3 --format brief); grep -q "Findings so far from G2 (1)" "$B3q" && grep -q "g2 row" "$B3q" && grep -q "Nothing logged yet on:" "$B3q" && pass "brief: prior index lists G2's finding + uncovered categories once G2 is complete"
B3=$(python3 "$S"/run.py render --manifest $M --op extract --group G3 --format brief); grep -q "RESUME: you .* already logged findings for src-001" "$B3" && grep -q "src-001 → .*\[DONE" "$B3" && pass "resume brief marks done sources and lists remaining"
echo '{"type":"open_item","business_cycle":"Payroll & Payroll Taxes","focus_area":"Pre-Audit Readiness","assertions":["Accuracy"],"dimension":"Data","severity":1,"evidence_basis":"stated","observation":"payroll tax filings not discussed","sources":["src-002:L1"]}' | python3 "$S"/ledger.py append findings --author rdr-G3 --group G3 >/dev/null 2>&1
python3 "$S"/run.py next --manifest $M | grep -vq "PARTIAL" && pass "resumed group completes once every source is cited"
python3 "$S"/run.py next --manifest $M | grep -q "op retro --phase extract" && pass "next: asks for the extract retro once all groups are complete"
touch $W/scratch/retro-extract.md
python3 "$S"/run.py gate --manifest $M --name normalized --status done >/dev/null
python3 "$S"/run.py gate --manifest $M --name revise --status passed >/dev/null
python3 "$S"/run.py next --manifest $M | grep -q "render.py\"* figures --manifest" && pass "next: points at render with manifest (custom out not yet rendered)" || { python3 "$S"/run.py next --manifest $M; fail next; }
python3 "$S"/render.py bundle --manifest $M >/dev/null && test -f $W/deliverable/viz/fig-open-items.json && python3 -c "import json;d=json.load(open('$W/deliverable/viz/fig-open-items.json'));assert [i['id'] for i in d['data']['items']]" && python3 -c "import json;d=json.load(open('$W/deliverable/viz/fig-heatmap.json'));assert not any('payroll tax filings' in str(c) for c in d['data']['cells'])" && pass "open_item rendered in its own figure and excluded from evidence" && test -f $W/deliverable/viz/catalog.md && test -f $W/deliverable/tbl/findings.md && test -f $W/deliverable/final/assessment.json && pass "render --manifest: tables/figures/bundle land in manifest-named locations"
python3 "$S"/run.py next --manifest $M | grep -q "op story" && pass "next: then points at story"
printf '# story\n' > $W/deliverable/narrative.md && python3 "$S"/render.py bundle --manifest $M >/dev/null && python3 "$S"/run.py next --manifest $M | grep -q "op retro --phase layers" && pass "next: asks for the layers retro before DONE" && touch $W/scratch/retro-layers.md && python3 "$S"/run.py next --manifest $M | grep -q "DONE" && pass "next: DONE"
python3 "$S"/run.py check --manifest $M --gate initiatives > $W/chk && grep -q "UNCOVERED (zero findings): " $W/chk && grep -q "Income Tax Provision" $W/chk && pass "check: validate+trace via manifest, with uncovered-category report"
python3 "$S"/run.py status --manifest $M > $W/st2; grep -q "G2 .*complete .*1/1" $W/st2 && grep -q "G3 .*complete .*2/2" $W/st2 && pass "status: per-group done/declared by manifest agent names"
python3 -c "import json;d=json.load(open('$W/out/figures/fig-heatmap.json'));assert any(c['max_severity']==3 for c in d['data']['cells'])" && pass "heatmap has severity-3 cell"

echo "parallel appends (fan-out)"
for i in 1 2 3 4 5 6; do (echo "{\"type\":\"observation\",\"business_cycle\":\"Payroll & Payroll Taxes\",\"focus_area\":\"Process Effectiveness\",\"process_attribute\":\"Manual effort\",\"dimension\":\"Process\",\"severity\":1,\"evidence_basis\":\"stated\",\"observation\":\"parallel $i\",\"sources\":[\"src-001:L1\"]}" | python3 "$S"/ledger.py append findings --author par-$i --group P >/dev/null 2>&1) & done; wait
test "$(python3 "$S"/ledger.py show findings | python3 -c 'import sys,json;ids=[json.loads(l)["id"] for l in sys.stdin];print(len(ids)==len(set(ids)) and len(ids)==len(set(ids)))')" = "True" && pass "6 concurrent appends -> 6 unique ids (lock works)"
python3 "$S"/ledger.py show findings | python3 -c 'import sys,json;[print(r["id"],r["author"]) for r in map(json.loads,sys.stdin) if r["group"]=="P"]' | while read id au; do python3 "$S"/ledger.py retire $id --author $au --reason "parallel test row" >/dev/null; done


echo "data: the reader as analyst"
printf 'je_no,date,user,amount\nJE-1,2026-07-05,ali,25000\nJE-2,2026-07-06,ali,120.5\nJE-3,2026-07-07,bob,1000\nJE-3,2026-08-02,bob,99999\n' > "$SRC"/../je.csv
mkdir -p $W/dsrc && cp "$SRC"/../je.csv $W/dsrc/je-listing.csv && cp "$SRC"/src-002.md $W/dsrc/ && python3 "$LINTPY" register --in $W/dsrc --ext csv,md > /dev/null
export ASSESS_LEDGER_DIR=$W/dledgers; mkdir -p $W/dledgers && python3 "$S"/ledger.py init --allow-no-git >/dev/null
python3 "$S"/data.py --registry $W/dsrc/registry.yaml --analysis-dir $W/dout/analysis profile src-001 > $W/dp && grep -q "data rows: \*\*4\*\*" $W/dp && pass "data profile: rows, columns, types"
python3 "$S"/data.py --registry $W/dsrc/registry.yaml --analysis-dir $W/dout/analysis run timing src-001 --date date --period-end 2026-07-31 > $W/dt 2>&1 && grep -q "weekend=2" $W/dt && grep -q "registered as src-003" $W/dt && pass "data run: weekend/period procedure, output registered with provenance"
grep -q "derived_from: src-001" $W/dsrc/registry.yaml && grep -q "kind: analysis" $W/dsrc/registry.yaml && pass "registry carries kind: analysis + derived_from"
python3 "$S"/data.py --registry $W/dsrc/registry.yaml --analysis-dir $W/dout/analysis run duplicates src-001 --key je_no > /dev/null 2>&1
echo '{"type":"gap","business_cycle":"Financial Close, JEs & Estimates","focus_area":"Pre-Audit Readiness","assertions":["Cut-off"],"dimension":"Process","severity":2,"evidence_basis":"observed","observation":"2 of 4 JEs posted on weekends; JE-3 posted 8/2 after period end.","sources":["src-001:L5","src-003:L9"]}' | python3 "$S"/ledger.py append findings --author reader-D --group D >/dev/null
python3 "$S"/validate.py --taxonomy "$TAX" --registry $W/dsrc/registry.yaml > $W/dv && grep -q "0 errors" $W/dv && pass "finding citing source row + analysis output validates"
python3 "$S"/trace.py --taxonomy "$TAX" > $W/dtr && grep -q "src-003 | 1" $W/dtr && pass "coverage shows the analysis source"
unset ASSESS_LEDGER_DIR; export ASSESS_LEDGER_DIR="$L"
S2=$(cd $W && python3 "$S"/run.py render --manifest $M --op extract --group G1 --format brief); grep -q "data profile" "$S2" && pass "brief exposes data commands and playbook"

echo "paths with spaces and parentheses"
SP="$W/Client (2026) - OneDrive"; mkdir -p "$SP/_client" && cp "$SRC"/src-002.md "$SP/_client/interview.md" && (cd "$SP" && git init -q . && echo "profile" > _client/profile.md)
python3 "$LINTPY" register --in "$SP/_client" >/dev/null 2>&1 || python3 "$LINTPY" register --in "$SP/_client" >/dev/null
python3 - "$SP/_client/registry.yaml" << 'PY'
import sys,yaml; p=sys.argv[1]; r=yaml.safe_load(open(p)); [s.__setitem__('kind','interview') for s in r['sources']]; yaml.safe_dump(r,open(p,'w'),sort_keys=False)
PY
(cd "$SP" && python3 "$S"/manifest.py draft --registry _client/registry.yaml --out synth/manifest.yaml --context _client/profile.md --ledger-dir synth/ledgers --workdir work --out-dir synth/out >/dev/null && python3 "$S"/ledger.py init --ledger-dir synth/ledgers >/dev/null && python3 "$S"/run.py check --manifest synth/manifest.yaml > $W/spc 2>&1) && grep -q "0 errors" $W/spc && pass "run.py check works on a root with spaces and parentheses (no shell=True)" || { cat $W/spc | tail -3; fail "check with spaces"; }
(cd "$SP" && python3 "$S"/run.py next --manifest synth/manifest.yaml > $W/spn) && grep -q '"' $W/spn && pass "next quotes paths that contain spaces"
B2=$(cd "$SP" && python3 "$S"/run.py render --manifest synth/manifest.yaml --op extract --group G1 --format brief) && (cd "$SP" && python3 work/assess.py validate > $W/spv) && grep -q "0 errors" $W/spv && pass "shim works from a root with spaces"

echo; echo "ALL PASS  (workdir: $W)"
