export const meta = {
  name: "consult-fanout",
  description: "Deterministic per-stage fan-out for a CONSULT engagement: one worker sub-agent per target (classify/consolidate/draft/synthesize), lock-safe, gate-preserving.",
  phases: [
    { title: "fan-out", detail: "spawn one worker agent per target for the given llm_fanout stage" },
  ],
};

// consult-fanout — deterministic per-stage fan-out for a CONSULT engagement.
//
// Invoked (by scriptPath) from the `consult-run` skill (T54 Tier 2) for one
// llm_fanout action, with args = { engagement, stage, targets, schema? }. It
// spawns ONE worker sub-agent per target (via custom agent types in
// .claude/agents/), bounded to a conservative concurrency, runs the classify
// post-step, and returns a rollup. It NEVER advances the engagement — see the
// human-gate guard below — so the render hand-off and needs-human stops stay
// owned by consult-run.
//
// Constraints honoured: the workflow script has no filesystem/exec access; ALL
// side effects happen inside agent() calls; numbers the script can see (budget)
// are RETURNED for consult-run / T56 to persist. State is only ever mutated by
// the workers via state_machine.py.
//
// NOTE: planFanout is INLINED here (the engine requires `export const meta` as
// the first statement and does not resolve local imports). This inlined block IS
// the single source of truth — the tests extract and run it verbatim (see the
// PLANNER markers), so there is no second copy to drift from.

// >>> PLANNER START (extracted verbatim by tests/_planner.mjs — keep the markers)
const FANOUT_STAGES = ["classify", "consolidate", "draft", "synthesize"];

function planFanout(stage, targets = {}) {
  const nodeKey = (n) => (typeof n === "string" ? n : (n.node || n.key || n.id || JSON.stringify(n)));
  const docKey = (d, i) => (typeof d === "string" ? d : (d.path || d.hash || d.source || `doc${i}`));
  switch (stage) {
    case "classify":
      return {
        calls: (targets.docs || []).map((d, i) => ({
          agentType: "consult-classifier", label: `classify:${docKey(d, i)}`, target: d,
        })),
        postStep: "classify_merge.py merge",
      };
    case "consolidate":
      return {
        calls: (targets.nodes || []).map((n) => ({
          agentType: "consult-consolidator", label: `consolidate:${nodeKey(n)}`, target: n,
        })),
        postStep: null,
      };
    case "draft": {
      const calls = [];
      for (const l1 of (targets.l1s || [])) {
        calls.push({ agentType: "consult-drafter", label: `draft:sop:${l1}`, target: { l1 } });
        calls.push({ agentType: "consult-improvement-drafter", label: `draft:imp:${l1}`, target: { l1 } });
      }
      return { calls, postStep: null };
    }
    case "synthesize":
      return {
        calls: [{ agentType: "consult-synthesizer", label: "synthesize:engagement", target: { scope: "engagement" } }],
        postStep: null,
      };
    default:
      throw new Error(`planFanout: '${stage}' is not an llm_fanout stage (${FANOUT_STAGES.join(", ")})`);
  }
}
// <<< PLANNER END

// Conservative DEFAULT concurrency — deliberately BELOW the engine cap
// (min(16, cores-2)). The field machine ran CPU-bound; favour responsiveness +
// isolation over maximum width. One knob, tune here.
const FANOUT_CONCURRENCY = 4;

// Run `fn` over items at most `limit` at a time (chunked barriers). parallel()
// resolves thunk failures to null, so a dead worker never aborts the batch.
async function runBounded(items, limit, fn) {
  const out = [];
  for (let i = 0; i < items.length; i += limit) {
    const chunk = items.slice(i, i + limit);
    const res = await parallel(chunk.map((it, j) => () => fn(it, i + j)));
    out.push(...res);
  }
  return out;
}

// Build the worker prompt. The agentType preloads the worker SKILL (which knows
// the full procedure), so the prompt just pins the engagement + this target and
// names the gatherer to run where the stage has one (classify has none — the
// classifier reads the ingested MD + taxonomy itself).
function workerPrompt(engagement, stage, call) {
  const t = call.target || {};
  switch (stage) {
    case "classify":
      return `Classify exactly one ingested document for engagement ${engagement}: ${t.path || t.hash || JSON.stringify(t)}. Follow your skill: read that MD + the taxonomy slice and emit the per-doc artifact. Return a one-line summary.`;
    case "consolidate":
      return `Consolidate node ${t.node || t.key || t} for engagement ${engagement}. Follow your skill: gather inputs (consolidate_inputs.py gather), confirm findings, apply them inline (state_machine.py add-item -> author the node MD citing the minted IDs -> mark-consolidated). Return a one-line summary.`;
    case "draft":
      return `Draft your stream for L1 '${t.l1}' of engagement ${engagement}. Follow your skill: gather inputs (draft_inputs.py gather --l1 ${t.l1}) and write your deliverable, bumping rev via state_machine.py. Return a one-line summary.`;
    case "synthesize":
      return `Synthesize the engagement-level deliverable for ${engagement}. Follow your skill: gather inputs (synthesis_inputs.py gather) and author the synthesis. Return a one-line summary.`;
    default:
      return `Process ${JSON.stringify(t)} for engagement ${engagement}; follow your skill.`;
  }
}

// ---- main ----------------------------------------------------------------
// args may arrive as an object OR as a JSON string — handle both.
const A = typeof args === "string" ? JSON.parse(args) : (args || {});
const { engagement, stage, targets } = A;
if (!engagement) throw new Error("consult-fanout: args.engagement is required");
if (!FANOUT_STAGES.includes(stage)) {
  throw new Error(`consult-fanout: '${stage}' is not an llm_fanout stage (${FANOUT_STAGES.join(", ")})`);
}

phase("fan-out");
const plan = planFanout(stage, targets || {});
log(`consult-fanout ${stage}: ${plan.calls.length} worker(s), concurrency ${FANOUT_CONCURRENCY}`);

const spentBefore = budget.spent();

const results = await runBounded(plan.calls, FANOUT_CONCURRENCY, async (call) => {
  // Schema seam (T55 Phase 2): consult-run passes args.schema (loaded from
  // schemas/classify_artifact.schema.json — read by the skill, not this script).
  // When present on classify, the worker returns a schema-validated object
  // (valid-by-construction). Off (undefined) => today's hand-authored path.
  const opts = { agentType: call.agentType, label: call.label };
  if (stage === "classify" && A.schema) opts.schema = A.schema;
  const out = await agent(workerPrompt(engagement, stage, call), opts);
  return { label: call.label, agentType: call.agentType, ok: out != null, summary: out ?? null };
});

// Classify post-step: the workflow can't exec, so it delegates the deterministic
// merge to one tightly-scoped agent. (consult-run no longer runs the merge once
// it delegates to this workflow — T54.) Other stages have no post-step:
// consolidate applies inline per worker; draft/synthesize write directly.
let postStepResult = null;
if (plan.postStep) {
  postStepResult = await agent(
    `Run exactly this and report its one-line result, nothing else: python3 scripts/${plan.postStep} --engagement ${engagement}`,
    { label: `post:${stage}` }
  );
}

const outputTokensDelta = budget.spent() - spentBefore;

// HUMAN-GATE GUARD (structural): this workflow issues NO engagement-advance,
// render, or finalize call — it runs one stage and returns. The render hand-off
// and needs-human stops remain owned by consult-run, which re-derives the next
// step itself after this returns. (Asserted by tests/test_fanout_dispatch.mjs:
// the source contains none of those calls.)
return {
  stage,
  engagement,
  count: plan.calls.length,
  succeeded: results.filter((r) => r && r.ok).length,
  results,
  postStep: plan.postStep,
  postStepResult,
  // Budget seam (T56): the script can't write files, so the measured delta is
  // RETURNED; consult-run / T56 persist it to a content-free cost_map.json.
  cost: { stage, targets: plan.calls.length, outputTokensDelta },
  humanGate: "preserved: no advance/render/finalize issued by this workflow",
};
