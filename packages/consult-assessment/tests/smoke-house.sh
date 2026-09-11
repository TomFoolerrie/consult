#!/usr/bin/env bash
# Proves the axes are the house's: a different taxonomy, same scripts, no code change.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"; LINTPY="$(cd "$HERE/../.." && pwd)/consult-lint/scripts/lint.py"; S="$HERE/../scripts"; TAX="$HERE/fixture/taxonomy-itgc.yaml"
W="$(mktemp -d)"; export ASSESS_LEDGER_DIR="$W/ledgers"; export ASSESS_TAXONOMY="$TAX"
pass(){ echo "  ok  $1"; }; fail(){ echo "FAIL $1"; exit 1; }
git config --global user.email >/dev/null 2>&1 || { git config --global user.email smoke@test; git config --global user.name smoke; }
mkdir -p $W/ledgers && python3 "$S"/ledger.py init --git-init >/dev/null

echo "itgc taxonomy"
python3 "$S"/ledger.py append findings --author reader-A --group A --from - <<'J' >/dev/null
{"type":"gap","domain":"Access Management","control_objective":"Restricted access","system":"ERP; Payroll SaaS","maturity_gap":"Informal","severity":3,"evidence_basis":"observed","observation":"Terminated users retain ERP and payroll access; no periodic review.","sources":["src-001:L4"]}
{"type":"gap","domain":"Change Management","control_objective":["Authorized changes"],"system":["ERP"],"maturity_gap":"Operating not evidenced","severity":2,"evidence_basis":"stated","observation":"Changes are approved verbally; no ticket trail.","sources":["src-002:L9"]}
{"type":"strength","domain":"Backup & Recovery","control_objective":["Recoverability"],"maturity_gap":"Operating not evidenced","severity":1,"evidence_basis":"observed","observation":"Nightly backups with quarterly restore tests.","sources":["src-003:L2"]}
J
pass "findings with house axes accepted ('a; b' list-ified via --taxonomy env)"
python3 "$S"/validate.py --taxonomy "$TAX" > $W/v && pass "validate clean under itgc axes" || { cat $W/v; fail validate; }
echo '{"type":"gap","domain":"Access Management","control_objective":["Restricted access"],"maturity_gap":"Informal","dimension":"Governance","severity":2,"evidence_basis":"stated","observation":"x","sources":["src-001:L1"]}' | python3 "$S"/ledger.py append findings --author reader-A >/dev/null
{ python3 "$S"/validate.py --taxonomy "$TAX" 2>/dev/null || true; } > $W/v2; grep -q "F-004" $W/v2 && fail "unknown axis 'dimension' should be ignored, not error" || pass "fields outside the axes are ignored (no phantom requirements from the old model)"
python3 "$S"/ledger.py retire F-004 --author reader-A --reason test >/dev/null
echo '{"type":"gap","domain":"Operations & Batch","maturity_gap":"Undefined","severity":2,"evidence_basis":"stated","observation":"x","sources":["src-001:L1"]}' | python3 "$S"/ledger.py append findings --author reader-A >/dev/null
{ python3 "$S"/validate.py --taxonomy "$TAX" 2>/dev/null || true; } | grep -q "axis 'control_objective' is required" && pass "required multi axis enforced" || fail "required axis"
python3 "$S"/ledger.py retire F-005 --author reader-A --reason test >/dev/null

echo '{"theme":"Access hygiene is nobody s job","root_cause":"No owner for joiner/mover/leaver","impact":"Auditor will fail ITGC access testing","findings":["F-001"]}' | python3 "$S"/ledger.py append themes --author themer >/dev/null
{ python3 "$S"/validate.py --taxonomy "$TAX" 2>/dev/null || true; } | grep -q "T-001: axis 'maturity_gap' is required" && pass "theme must carry the on_theme axis (maturity_gap, not dimension)" || fail "theme axis"
python3 "$S"/ledger.py retire T-001 --author themer --reason test >/dev/null
echo '{"theme":"Access hygiene is nobody s job","root_cause":"No owner for joiner/mover/leaver","maturity_gap":"Undefined","impact":"Auditor will fail ITGC access testing","findings":["F-001","F-002"]}' | python3 "$S"/ledger.py append themes --author themer >/dev/null
python3 "$S"/validate.py --taxonomy "$TAX" > $W/v3 || fail "theme with house axis should validate"
grep -q "T-002: theme maturity_gap 'Undefined' matches none" $W/v3 && pass "contradiction warning fires on the house's root-cause axis"

python3 "$S"/render.py figures --ledger-dir $W/ledgers --taxonomy "$TAX" --out $W/out > /dev/null
test -f $W/out/figures/fig-domain-objective.json && test -f $W/out/figures/fig-system-domain.json && test -f $W/out/figures/fig-maturity.json && pass "house figures rendered from the taxonomy's figures block"
test ! -f $W/out/figures/fig-heatmap.json && pass "no leftover readiness figures"
python3 -c "
import json;d=json.load(open('$W/out/figures/fig-system-domain.json'));c={(x['row'],x['col']):x for x in d['data']['cells']}
assert c[('ERP','Access Management')]['findings']==1 and c[('Payroll SaaS','Access Management')]['findings']==1 and c[('ERP','Change Management')]['themes']==1,c" && pass "multi x single axis heatmap cells correct; theme footprint lands on cells"
python3 -c "
import json;d=json.load(open('$W/out/figures/fig-scorecard.json'));assert d['data']['axis']=='domain' and d['title'].startswith('IT domain'),d['title']" && pass "scorecard groups by the house's primary axis"
python3 "$S"/render.py tables --ledger-dir $W/ledgers --taxonomy "$TAX" --out $W/out >/dev/null && head -1 $W/out/tables/findings.md | grep -q "IT domain | Control objective | System | Maturity gap" && pass "findings table columns follow the axes"

echo; echo "ALL PASS  ($W)"
