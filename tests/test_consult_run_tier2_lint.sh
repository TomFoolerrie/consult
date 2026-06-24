#!/usr/bin/env bash
# T54 Tier 2 + T55 Phase 2 + T56 (consult-run side) — positive lint.
# Asserts consult-run now delegates each llm_fanout action to the named
# consult-fanout workflow, passes the schema for classify, hands merge to the
# workflow, and persists the returned cost map. Positive assertions only
# (presence of the wiring), not absence of a never-present instruction.
set -u
SKILL="skills/consult-run/SKILL.md"
pass=0; fail=0
have() { if grep -qiE "$1" "$SKILL"; then pass=$((pass+1)); else echo "  FAIL: missing /$1/"; fail=$((fail+1)); fi; }

# T54 Tier 2 — invoke the named workflow with the right args
have 'consult-fanout'
have 'stage:[[:space:]]*obj\.action|stage:[[:space:]]*\`?obj\.action'
have 'targets:[[:space:]]*obj\.targets'
have 'engagement:[[:space:]]*E'

# T55 Phase 2 — classify passes the schema, read once here
have 'classify_artifact\.schema\.json'
have 'args\.schema|pass it as .?args\.schema|schema:'
have 'valid by construction|StructuredOutput'

# Merge ownership — workflow runs the classify merge; orchestrator does NOT
have 'workflow runs the classify .?merge|runs the classify `?merge'
have 'you do \*\*not\*\* run|you do not run .?classify_merge|double-merge'

# T56 — persist the returned cost to a content-free cost_map.json
have 'cost_map\.json'
have 'outputTokensDelta|Δoutput-tokens|output-tokens'
have 'no document content|content-free'

# Human gate preserved
have 'one stage and returns|never advances|gate-respecting'

echo "consult-run Tier-2 lint: PASS=$pass FAIL=$fail"
[ "$fail" -eq 0 ] && echo "ALL TIER-2 LINT ASSERTIONS PASS." || exit 1
