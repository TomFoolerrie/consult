// Pure, deterministic per-stage fan-out planner for the `consult-fanout` workflow.
//
// SINGLE SOURCE OF TRUTH for "given an llm_fanout action's stage + targets,
// which agent() calls does the workflow issue, and is there a post-step?".
// Imported by BOTH `consult-fanout.mjs` (the workflow) and
// `tests/test_fanout_dispatch.mjs` (so dispatch counts are asserted WITHOUT
// spawning real agents). Keep it pure: no I/O, no globals, no side effects.
//
// Encodes T57's per-stage dispatch TABLE exactly (grounded in
// scripts/orchestrate.py ACTION_DISPATCH + _action targets):
//   classify    -> targets.docs  -> 1x consult-classifier per doc      -> post: classify_merge.py merge
//   consolidate -> targets.nodes -> 1x consult-consolidator per node   -> post: none (worker applies INLINE, Decision B)
//   draft       -> targets.l1s   -> 2x per L1 (drafter + improvement)  -> post: none
//   synthesize  -> engagement     -> exactly 1 consult-synthesizer       -> post: none

export const FANOUT_STAGES = ["classify", "consolidate", "draft", "synthesize"];

// Stable key for a consolidate node target (string key or {node|key} object).
function nodeKey(n) {
  return typeof n === "string" ? n : (n.node || n.key || n.id || JSON.stringify(n));
}

// Stable label for a classify doc target ({path, hash, ...} or string).
function docKey(d, i) {
  if (typeof d === "string") return d;
  return d.path || d.hash || d.source || `doc${i}`;
}

/**
 * Plan the fan-out for one llm_fanout action.
 * @param {string} stage  one of FANOUT_STAGES
 * @param {object} targets  the action's `targets` from orchestrate.py next --json
 * @returns {{ calls: Array<{agentType:string,label:string,target:any}>, postStep: string|null }}
 */
export function planFanout(stage, targets = {}) {
  switch (stage) {
    case "classify": {
      const docs = targets.docs || [];
      return {
        calls: docs.map((d, i) => ({
          agentType: "consult-classifier",
          label: `classify:${docKey(d, i)}`,
          target: d,
        })),
        // Workflow runs this once AFTER the fan-out (the workflow supplies the
        // `merge` subcommand; orchestrate.py emits the bare script path).
        postStep: "classify_merge.py merge",
      };
    }

    case "consolidate": {
      const nodes = targets.nodes || [];
      return {
        calls: nodes.map((n) => ({
          agentType: "consult-consolidator",
          label: `consolidate:${nodeKey(n)}`,
          target: n,
        })),
        postStep: null, // each worker mints IDs + applies inline (Decision B); lock-safe
      };
    }

    case "draft": {
      // Keyed on l1s, NOT nodes. TWO skills per L1 => 2 x len(l1s) agents.
      const l1s = targets.l1s || [];
      const calls = [];
      for (const l1 of l1s) {
        calls.push({ agentType: "consult-drafter", label: `draft:sop:${l1}`, target: { l1 } });
        calls.push({ agentType: "consult-improvement-drafter", label: `draft:imp:${l1}`, target: { l1 } });
      }
      return { calls, postStep: null };
    }

    case "synthesize": {
      // Engagement-scoped: exactly ONE agent, no list.
      return {
        calls: [{
          agentType: "consult-synthesizer",
          label: "synthesize:engagement",
          target: { scope: "engagement" },
        }],
        postStep: null,
      };
    }

    default:
      throw new Error(`planFanout: '${stage}' is not an llm_fanout stage (expected one of ${FANOUT_STAGES.join(", ")})`);
  }
}
