/**
 * harness/install — put the consultant seat and the worker classes into an engagement folder.
 *
 * NOT engine. The engine is `consult <verb>`; the harness is the layer between the engine
 * and the models on the Claude Code substrate:
 *   <root>/CLAUDE.md            the consultant seat — whoever opens the folder with `claude` IS
 *                               the consultant (agents/consultant.md + agents/system.md + the
 *                               substrate notes below)
 *   <root>/.claude/agents/      the three worker classes (model pinned, tool surface fixed)
 *   <root>/.claude/settings.json  permission allow-list for the engine
 *   the folder skeleton, STATE.md, OBJECTIVE.md, a git repo with a first commit
 * Usage: node --experimental-strip-types harness/install.ts <root> [--objective <file>]
 */
import { mkdirSync, writeFileSync, existsSync, readFileSync, copyFileSync, readdirSync } from "node:fs";
import { join, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");

export const SKELETON = ["_sources/new", "_sources/processed", "_sources/parked", "_sources/scans",
  "_registers/sessions", "_skills", "_synthesis", "_definitions", "capture/_taxonomy", ".claude/agents"];

export function seat(): string {
  const consultant = readFileSync(join(REPO, "agents", "consultant.md"), "utf8");
  const system = readFileSync(join(REPO, "agents", "system.md"), "utf8");
  return [
    "# CONSULT — the consultant seat",
    "",
    "Whoever opens this folder with `claude` is THE CONSULTANT for this engagement.",
    "The two documents below are your operating procedure and your mental model.",
    "The engine is on PATH as `consult <verb>`. Read on before doing anything.",
    "",
    "## The substrate (Claude Code) — how the abstractions land here",
    "",
    "- **Dispatch a worker** = the Agent tool with `subagent_type: worker-haiku | worker-sonnet | worker-opus`",
    "  and `prompt` = the exact output of `consult brief <skill> --class <c> [--cards a,b]`. The brief IS the",
    "  skill delivery; the class pins only the model. Nothing else is passed.",
    "- **Record every dispatch's cost**: the Agent result reports token usage; immediately run",
    "  `consult spend \"<skill> on <class>: <what>\" --estimate <your estimate> --actual <tokens reported>`.",
    "  Estimate BEFORE dispatching; over-budget estimates go to the human first (the spend gate).",
    "- **The sitting budget is set once by the human's word**: `consult budget set <tokens>` at the start of a",
    "  sitting (the human names the number; you run the verb — it lands as a gate line). Until it is set the",
    "  budget is 0 and every spend is refused; that is the intended state, not a bug.",
    "- **Pin a shape before you need it**: `consult pin information-request` puts the shipped definition into",
    "  `_definitions/`; `needs` and `render` read only pinned shapes.",
    "- **Save a skill before you use it**: write the YAML anywhere, then `consult skill save <file>` — the",
    "  only writer of `_skills/`.",
    "- **Where a worker's scan report goes**: write it OUTSIDE the stores (e.g. `/tmp/scan-SRC-003.yaml`),",
    "  then `consult scan SRC-003 /tmp/scan-SRC-003.yaml`; never into `_sources/new/` or `_synthesis/`.",
    "- **The two gates are a question to the human in this chat** — nothing else. Spends over the",
    "  sitting budget, and anything client-facing. Record the answer with `consult gate` or",
    "  `consult ask accept`; then proceed.",
    "- **The client is not in this chat.** Responses arrive as files in `_sources/new/` that the human",
    "  relays to you (\"this is Marcus's reply to ASK-001\"); you run `consult ask respond`.",
    "- **Workers cannot see this conversation.** Everything a worker needs is in the brief; if it",
    "  is not, the brief was under-scoped — fix the params, do not narrate.",
    "- **End every sitting with a checkpoint**, and open every sitting with STATE.md.",
    "",
    "---",
    "",
    consultant.trim(),
    "",
    "---",
    "",
    system.trim(),
    "",
  ].join("\n");
}

export function install(root: string, opts: { objective?: string } = {}): string[] {
  const made: string[] = [];
  for (const d of SKELETON) { mkdirSync(join(root, d), { recursive: true }); }
  const put = (rel: string, content: string, overwrite = false) => {
    const p = join(root, rel);
    if (!overwrite && existsSync(p)) return;
    writeFileSync(p, content); made.push(rel);
  };
  put("STATE.md", "# state pad\n## now\nSitting 1: not yet begun.\n## human's standing guidance\n(none yet)\n## precedent\n(none yet)\n## observations\n(none yet)\n");
  put("OBJECTIVE.md", opts.objective ? readFileSync(opts.objective, "utf8") : "# objective\n(the human writes the soft objective here — who the client is, what the relationship is producing; no client facts)\n");
  put("CLAUDE.md", seat(), true);
  mkdirSync(join(root, "agents"), { recursive: true });
  copyFileSync(join(REPO, "agents", "system.md"), join(root, "agents", "system.md")); made.push("agents/system.md");
  for (const f of readdirSync(join(REPO, "harness", "agents"))) { copyFileSync(join(REPO, "harness", "agents", f), join(root, ".claude/agents", f)); made.push(join(".claude/agents", f)); }
  put(".claude/settings.json", JSON.stringify({ permissions: { allow: ["Bash(consult:*)", "Bash(git:*)", "Bash(python3:*)", "Read", "Write", "Edit", "Grep", "Glob"] } }, null, 2) + "\n", true);
  put(".gitignore", ".harness/\n");
  if (!existsSync(join(root, ".git"))) {
    execSync("git init -q && git add -A && git commit -qm 'consult: engagement opened'", { cwd: root });
    made.push(".git");
  }
  return made;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = process.argv[2];
  if (!root) { console.error("usage: install.ts <root> [--objective <file>]"); process.exit(2); }
  const i = process.argv.indexOf("--objective");
  const made = install(resolve(root), i > 0 && process.argv[i + 1] ? { objective: process.argv[i + 1]! } : {});
  console.log(made.join("\n"));
  console.log(`\nconsultant seat installed. Put ${join(REPO, "bin")} on PATH, then: cd ${resolve(root)} && claude`);
}
