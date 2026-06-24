#!/usr/bin/env bash
# =============================================================================
# test_consult_run_delegation_lint.sh — T54 Tier 1 prose-hardening lint.
#
# Asserts (POSITIVE — the language must be PRESENT, not merely absent; the
# orchestrator was never told to self-read, so asserting absence tests nothing):
#   1. consult-run's dispatch is BLOCKING for llm_fanout — it states the
#      orchestrator MUST delegate and that doing the reasoning itself is a
#      contract violation.
#   2. consult-run names the explicit CONTENT PROHIBITION — it must not read
#      `ingested/*.md` / taxonomy slices nor run the input-gatherers
#      (consolidate_inputs.py / draft_inputs.py / synthesis_inputs.py) itself.
#   3. consult-run is HONEST that Tier 1 is a rule/nudge (not a physical gate)
#      and that the structural guarantee is Tier 2.
#
# No client data; read-only over the committed skill. Exits 0 only if every
# assertion PASSes.
# =============================================================================
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

SKILL="skills/consult-run/SKILL.md"
PASS=0
FAIL=0

# assert_grep PATTERN MESSAGE  — case-insensitive, fixed-ish ERE grep.
assert_grep() {
    local pat="$1" msg="$2"
    if grep -Eiq -- "$pat" "$SKILL"; then
        echo "PASS: $msg"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $msg  (pattern not found: /$pat/)"
        FAIL=$((FAIL + 1))
    fi
}

if [ ! -f "$SKILL" ]; then
    echo "FAIL: $SKILL not found"
    exit 1
fi

echo "----------------------------------------------------------------"
echo "T54 Tier 1: blocking-delegation language present"
echo "----------------------------------------------------------------"
assert_grep "MUST.{0,40}delegate"                "states the orchestrator MUST delegate"
assert_grep "contract violation"                 "calls inlining a contract violation"
assert_grep "even for small batches"             "forbids the small-batch shortcut"
assert_grep "small batches of one or two"        "forbids the one-or-two-target inline excuse"
assert_grep "context isolation"                  "states the reason (context isolation)"

echo "----------------------------------------------------------------"
echo "T54 Tier 1: explicit content prohibition present"
echo "----------------------------------------------------------------"
assert_grep "ingested/\*\.md"                    "forbids reading ingested/*.md"
assert_grep "taxonomy slice"                      "forbids reading taxonomy slices"
assert_grep "consolidate_inputs\.py"              "names consolidate_inputs.py gatherer"
assert_grep "draft_inputs\.py"                    "names draft_inputs.py gatherer"
assert_grep "synthesis_inputs\.py"               "names synthesis_inputs.py gatherer"

echo "----------------------------------------------------------------"
echo "T54 Tier 1: honest about teeth (rule, not gate; Tier 2 is structural)"
echo "----------------------------------------------------------------"
assert_grep "not a physical gate|rule.{0,20}not a"  "honest it is a rule, not a physical gate"
assert_grep "Tier 2"                                 "points to Tier 2 as the structural fix"

echo "================================================================"
echo "RESULT: $PASS passed, $FAIL failed."
echo "================================================================"
if [ "$FAIL" -ne 0 ]; then exit 1; fi
echo "ALL ASSERTIONS PASS."
exit 0
