// T57 Part 2 — fan-out dispatch tests (no real agents spawned).
// Asserts planFanout() per-stage counts, the workflow parses, and the
// human-gate guard holds (the workflow issues no advance/render/finalize call).
//
// Run: node tests/test_fanout_dispatch.mjs

import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { planFanout, FANOUT_STAGES } from "./_planner.mjs";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const WF = join(ROOT, ".claude/workflows/consult-fanout.mjs");

let pass = 0, fail = 0;
function ok(cond, msg) { if (cond) { pass++; } else { fail++; console.error(`  FAIL: ${msg}`); } }
function eq(a, b, msg) { ok(a === b, `${msg} (got ${JSON.stringify(a)}, want ${JSON.stringify(b)})`); }

// --- dispatch counts (the core table) ---
const c = planFanout("classify", { docs: [{ path: "a.md" }, { path: "b.md" }] });
eq(c.calls.length, 2, "classify 2 docs -> 2 agents");
ok(c.calls.every((x) => x.agentType === "consult-classifier"), "classify uses consult-classifier");
eq(c.postStep, "classify_merge.py merge", "classify post-step is merge");

const co = planFanout("consolidate", { nodes: ["n1", "n2", "n3"] });
eq(co.calls.length, 3, "consolidate 3 nodes -> 3 agents");
ok(co.calls.every((x) => x.agentType === "consult-consolidator"), "consolidate uses consult-consolidator");
eq(co.postStep, null, "consolidate has NO post-step (inline apply)");

const d = planFanout("draft", { l1s: ["L1", "L2"] });
eq(d.calls.length, 4, "draft 2 L1s -> 4 agents (2 skills x 2 L1s)");
eq(d.calls.filter((x) => x.agentType === "consult-drafter").length, 2, "draft: 2 drafter calls");
eq(d.calls.filter((x) => x.agentType === "consult-improvement-drafter").length, 2, "draft: 2 improvement-drafter calls");
eq(d.postStep, null, "draft has no post-step");

const s = planFanout("synthesize", { scope: "engagement" });
eq(s.calls.length, 1, "synthesize -> exactly 1 agent");
eq(s.calls[0].agentType, "consult-synthesizer", "synthesize uses consult-synthesizer");

// draft keyed on l1s, NOT nodes: passing nodes only must yield 0 (proves the key)
eq(planFanout("draft", { nodes: ["x", "y", "z"] }).calls.length, 0, "draft ignores targets.nodes (keys on l1s)");

// unknown stage throws
let threw = false;
try { planFanout("ingest", {}); } catch { threw = true; }
ok(threw, "unknown/non-fanout stage throws");
eq(FANOUT_STAGES.length, 4, "exactly 4 fan-out stages");

// --- workflow body parses in the ENGINE'S dialect ---
// The Workflow engine wraps the script body in an async function (top-level
// await + return are legal there) and injects agent()/pipeline()/budget/args as
// globals. `node --check` would wrongly reject the legitimate top-level return,
// so validate the body the way the engine compiles it: strip the module-level
// import/export, then compile as an async-function body (syntax-only; undefined
// injected globals are fine — they'd only matter at run time).
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
const srcRaw = readFileSync(WF, "utf8");
const body = srcRaw.replace(/^export\s+/gm, "").replace(/^import[^\n]*\n/gm, "");
let parsed = true;
try { new AsyncFunction(body); } catch (e) { parsed = false; console.error(`  parse error: ${e.message}`); }
ok(parsed, "consult-fanout.mjs body compiles in the engine's async dialect");

// planner block validity: _planner.mjs extracts + evaluates the inlined planner
// from the workflow; if that block were malformed the import above would have
// thrown. So a successful import IS the planner-parses assertion.
ok(typeof planFanout === "function", "inlined planner extracted + evaluated from the workflow");

// --- human-gate guard: the workflow issues NO advance/render/finalize call ---
const src = readFileSync(WF, "utf8");
ok(!src.includes("orchestrate.py"), "human-gate: no orchestrate.py (next-loop) call");
ok(!src.includes("render_deliverables"), "human-gate: no render_deliverables call");
ok(!src.includes("--status final"), "human-gate: no finalize (--status final) call");
// and it DOES delegate to the agent types (sanity that it's wired)
ok(src.includes("agentType: call.agentType"), "workflow spawns by custom agentType");
ok(src.includes("planFanout"), "workflow drives off the pure planner");

console.log(`\nfan-out dispatch: PASS=${pass} FAIL=${fail}`);
process.exit(fail === 0 ? 0 : 1);
