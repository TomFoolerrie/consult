// _planner.mjs — single source of truth for the fan-out planner.
//
// The Workflow engine requires `export const meta` first and rejects local
// imports, so planFanout is INLINED in .claude/workflows/consult-fanout.mjs.
// To guarantee the tests check the EXACT code the engine runs (no drift / no
// second copy), this helper extracts the planner block from the workflow source
// (between the `>>> PLANNER START` / `<<< PLANNER END` markers) and evaluates it.

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const WF = join(ROOT, ".claude/workflows/consult-fanout.mjs");

const src = readFileSync(WF, "utf8");
const m = src.match(/\/\/ >>> PLANNER START[^\n]*\n([\s\S]*?)\n\/\/ <<< PLANNER END/);
if (!m) {
  throw new Error("planner block (>>> PLANNER START ... <<< PLANNER END) not found in consult-fanout.mjs");
}

// Evaluate the extracted block and hand back its exports. If the block has a
// syntax error this throws here — so the tests also guard the planner's validity.
const factory = new Function(`${m[1]}\nreturn { planFanout, FANOUT_STAGES };`);
export const { planFanout, FANOUT_STAGES } = factory();
