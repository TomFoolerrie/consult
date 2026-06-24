// test_slice4_integration.mjs — T58 Slice-4 integration (acceptance gate).
//
// The Workflow ENGINE can't be invoked from a test harness, so this does not
// execute consult-fanout end to end. It verifies the genuinely-new cross-language
// seam: that `orchestrate.py next --json` (the Python spine) feeds `planFanout`
// (the JS workflow planner) EXACTLY as consult-run bridges them — action -> stage,
// targets -> the right number/kind of worker calls — using REAL `next` output.
//
// Coverage split (so this stays honest about the boundary):
//   - HERE: the real classify bridge (init+ingest -> next=classify -> planFanout);
//     and the GATE property that the planner refuses every non-fan-out action
//     (ingest/merge/gap/render/final), so the workflow is never invoked to
//     advance/render/finalize — those stay with consult-run.
//   - test_fanout_dispatch.mjs: per-stage counts for all four stages.
//   - test_slice1/2_e2e.sh: the deterministic spine (merge/render) byte-stability
//     under stubbed LLM outputs (the canned fixture's classify-completion is name-
//     based, which is why we don't drive multi-stage real-next here).
//   - test_render_gates.sh: the render human-gate in orchestrate.py.
//
// Run: node tests/test_slice4_integration.mjs   (scratch __t58__, cleaned up)

import { execFileSync } from "node:child_process";
import { rmSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { planFanout, FANOUT_STAGES } from "../.claude/workflows/lib/dispatch-plan.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const EID = "__t58__";
const FIX = "fixtures/r2r";
let pass = 0, fail = 0;
const ok = (c, m) => { if (c) pass++; else { fail++; console.error(`  FAIL: ${m}`); } };
const eq = (a, b, m) => ok(a === b, `${m} (got ${JSON.stringify(a)}, want ${JSON.stringify(b)})`);
const py = (args) => execFileSync("python3", args, { cwd: ROOT, encoding: "utf8" });

rmSync(join(ROOT, "engagements", EID), { recursive: true, force: true });
try {
  // --- the real bridge: orchestrate.py next -> planFanout (classify) --------
  py(["scripts/state_machine.py", "init", "--engagement", EID, "--region", "NA"]);
  py(["scripts/ingest_normalize.py", "ingest", "--engagement", EID,
      "--source", `${FIX}/close_walkthrough.vtt`, `${FIX}/recon_walkthrough.txt`]);

  const a1 = JSON.parse(py(["scripts/orchestrate.py", "next", "--engagement", EID, "--json"]));
  eq(a1.action, "classify", "post-ingest next is classify");
  eq(a1.kind, "llm_fanout", "classify is llm_fanout");
  ok(!["done", "render", "final"].includes(a1.action),
     "loop surfaces fan-out work, not a skip-to-finalize");

  // consult-run maps action->stage and passes targets verbatim; planFanout must
  // consume the REAL next payload and produce one classifier per ingested doc.
  const p1 = planFanout(a1.action, a1.targets);
  eq(p1.calls.length, (a1.targets.docs || []).length, "classify: plan count == #docs from real next");
  eq(p1.calls.length, 2, "classify: 2 ingested docs -> 2 worker calls");
  ok(p1.calls.every((c) => c.agentType === "consult-classifier"), "classify: consult-classifier agentType");
  eq(p1.postStep, "classify_merge.py merge", "classify: post-step is the merge (run by the workflow)");

  // --- GATE property: the planner refuses every NON-fan-out action ----------
  // orchestrate.py's deterministic / terminal actions must never reach the
  // workflow — consult-run runs scripts / handles the render+final gates itself.
  for (const det of ["ingest", "merge", "gap", "render", "final", "done", "gate_blocked"]) {
    let threw = false;
    try { planFanout(det, {}); } catch { threw = true; }
    ok(threw, `planner refuses non-fan-out action '${det}' (gate/finalize stays with consult-run)`);
  }
  eq(FANOUT_STAGES.length, 4, "exactly 4 fan-out stages are plannable");

  // --- the four stages map orchestrate's target KEYS to the right counts ----
  // (real key shapes from orchestrate _action targets: docs / nodes / l1s / scope)
  eq(planFanout("classify", { docs: [1, 2, 3] }).calls.length, 3, "classify keys on targets.docs");
  eq(planFanout("consolidate", { nodes: ["a", "b"] }).calls.length, 2, "consolidate keys on targets.nodes");
  eq(planFanout("draft", { nodes: ["x"], l1s: ["L1", "L2"] }).calls.length, 4, "draft keys on targets.l1s (2x), ignores nodes");
  eq(planFanout("synthesize", { scope: "engagement" }).calls.length, 1, "synthesize is a single engagement-scoped agent");

} finally {
  rmSync(join(ROOT, "engagements", EID), { recursive: true, force: true });
}

console.log(`\nslice-4 integration: PASS=${pass} FAIL=${fail}`);
process.exit(fail === 0 ? 0 : 1);
