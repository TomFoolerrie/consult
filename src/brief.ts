/**
 * brief — the skill store and composer.
 *
 * Owns/writes: <root>/_skills/ — the engagement-authored skill store
 * (the consultant's one authoring surface here, written only through
 * saveSkill). The distinction, ruled 2026-08-26: worker CLASSES pin the
 * model (haiku | sonnet | opus); SKILLS are skills with agency —
 * mission, write boundary, context contract, return contract, rules, and
 * a recommended class (advisory). Class and skill are chosen
 * independently per dispatch; estimates price the pair.
 *
 * Resolution: an engagement-authored skill shadows a shipped one of the
 * same name (kernel/skills/), the same rule definitions use. The
 * consultant may author a skill ad-hoc — from scratch or as a variant —
 * but it is always SAVED before use (never run from a prompt), logged in
 * the session record, and thereby reusable: later sittings inherit it.
 *
 * compose() resolves one skilled unit of work into one printable brief:
 * the OBJECTIVE (the first 20 lines of OBJECTIVE.md), the human's
 * STANDING GUIDANCE (the text under the pad's "## human's standing
 * guidance" heading), the scoped INDEX (every store but _skills, each
 * line naming its content path), the full CARDS named in params.cards,
 * the parameters, and the skill's rules and return contract verbatim.
 * Registers are NOT inlined — the index covers them (review C10).
 *
 * A27 — the manifest: a skill DECLARES its ports (contract: v1, reads,
 * writes, returns, runtime) and the brief prints them as the worker's walls.
 * Level 1 is a YAML file; level 2 is a directory with skill.yaml at its root
 * and code beside it. skillCheck() is the STATIC half of conformance —
 * manifest valid, ports declared, the level-2 runner actually present, and
 * no human-stop vocabulary in a level-2 skill's own scripts; it returns
 * problems rather than throwing, because a bad skill is a report, not a crash.
 * Issued when, and only when, delegation happens; the consultant's own
 * picture is desk.report. The brief decides nothing about content.
 */
import { parse, stringify } from "yaml";
import { readFileSync, writeFileSync, existsSync, readdirSync, mkdirSync, statSync } from "node:fs";
import { join, dirname, basename, delimiter } from "node:path";
import { fileURLToPath } from "node:url";
import * as record from "./record.ts";
import * as index from "./index.ts";

const SHIPPED = join(dirname(fileURLToPath(import.meta.url)), "..", "kernel", "skills");

export type WorkerClass = "haiku" | "sonnet" | "opus";

/** A27: the three ports a skill may use, declared in its manifest and nowhere else. */
export const READ_PORTS = ["sources", "capture", "registers", "synthesis"] as const;
export const WRITE_PORTS = ["synthesis", "capture-fragment"] as const;
export const RETURN_KINDS = ["findings", "asks", "statements", "artifacts", "flags"] as const;
export type ReadPort = (typeof READ_PORTS)[number];
export type WritePort = (typeof WRITE_PORTS)[number];
export type ReturnKind = (typeof RETURN_KINDS)[number];
/** level 1 is prompt-only; level 2 carries code and names the command that runs it */
export type Runtime = "prompt" | { command: string; cwd?: string };

export interface Skill {
  contract: "v1";                   // the manifest version; anything else is refused by name
  name: string;
  mission: string;
  reads: readonly ReadPort[];       // what it may learn, and through which port
  writes: readonly WritePort[];     // the two landings — [] for read-only work
  returns: readonly ReturnKind[];   // what `consult return` may carry back from it
  runtime: Runtime;                 // "prompt" (level 1) or a command (level 2)
  contextContract: readonly string[];
  returnContract: readonly string[];
  rules: readonly string[];
  recommendedClass: WorkerClass;    // advisory; overrides are recorded with reason
  origin: "shipped" | "engagement"; // engagement skills shadow shipped ones by name
  variantOf?: string;               // set when authored as a variant
}

/**
 * the manifest's own validation, shared by the read door and the write door and
 * reused (as problems, not throws) by skillCheck. Order is load-bearing: the
 * older refusals (list shape, the class dial) keep firing first so a skill that
 * was malformed before contract v1 is still named for what is actually wrong.
 */
function manifestProblems(name: string, raw: Partial<Skill> | undefined): string[] {
  const p: string[] = [];
  const say = (m: string) => p.push(`skill ${name}: ${m}`);
  if (!raw?.name || !raw.mission) return [`skill ${name}: malformed — mission required`];
  for (const k of ["contextContract", "returnContract", "rules"] as const)
    if (!Array.isArray(raw[k])) say(`${k} must be a list, not ${typeof raw[k]}`);
  const cls = String(raw.recommendedClass ?? "").split(/[;\s]/)[0] ?? "";
  if (!["haiku", "sonnet", "opus"].includes(cls))
    say(`recommendedClass "${String(raw.recommendedClass)}" is not haiku | sonnet | opus`);
  if (raw.contract !== "v1") say(`contract ${String(raw.contract)} is not v1`);
  const ports: [string, readonly string[]][] = [["reads", READ_PORTS], ["writes", WRITE_PORTS], ["returns", RETURN_KINDS]];
  for (const [field, allowed] of ports) {
    const v = (raw as Record<string, unknown>)[field];
    if (!Array.isArray(v)) { say(`${field} must be a list of ${allowed.join("|")} — a skill declares its ports`); continue; }
    for (const item of v) if (!allowed.includes(String(item))) say(`${field} '${String(item)}' is not ${allowed.join("|")}`);
  }
  const rt = raw.runtime;
  if (rt !== "prompt") {
    if (!rt || typeof rt !== "object") say(`runtime ${JSON.stringify(rt) ?? String(rt)} is not "prompt" or { command }`);
    else if (typeof rt.command !== "string") say(`runtime.command must be a string, not ${typeof rt.command}`);
  }
  return p;
}

/** level 1 (<name>.yaml) or level 2 (<name>/skill.yaml) — the same manifest either way */
function manifestPath(dir: string, name: string): string | null {
  const flat = join(dir, `${name}.yaml`);
  if (existsSync(flat)) return flat;
  const nested = join(dir, name, "skill.yaml");
  if (existsSync(nested)) return nested;
  return null;
}
/** where a skill resolves from: its manifest, and (level 2) the directory that holds its code */
export function skillPath(root: string, name: string): { manifest: string; dir: string; level: 1 | 2 } {
  const local = manifestPath(join(root, "_skills"), name);   // a local name shadows a shipped one
  const path = local ?? manifestPath(SHIPPED, name);
  if (!path) throw new Error(`skill: no skill named ${name} (shipped or engagement-authored)`);
  const level = basename(path) === "skill.yaml" ? 2 : 1;
  return { manifest: path, dir: dirname(path), level };
}

/** resolve a skill by name: engagement store shadows shipped; unknown is a named refusal */
export function skill(root: string, name: string): Skill {
  const raw = parse(readFileSync(skillPath(root, name).manifest, "utf8")) as Skill;
  const problems = manifestProblems(name, raw);
  if (problems.length) throw new Error(problems[0]);
  const cls = String(raw.recommendedClass).split(/[;\s]/)[0] as WorkerClass;
  return { ...raw, recommendedClass: cls };
}
/** every skill visible to this engagement (shipped + authored), shadowing applied */
export function skills(root: string): Skill[] {
  const names = new Set<string>();
  const local = join(root, "_skills");
  for (const dir of [local, SHIPPED]) {
    if (!existsSync(dir)) continue;
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.isFile() && e.name.endsWith(".yaml")) names.add(e.name.replace(/\.yaml$/, ""));           // level 1
      else if (e.isDirectory() && existsSync(join(dir, e.name, "skill.yaml"))) names.add(e.name);      // level 2
    }
  }
  return [...names].sort().map(n => skill(root, n));
}
/** save an ad-hoc skill (from scratch or a variant) into _skills/ — always saved before use, logged in the session record */
export function saveSkill(root: string, tpl: Skill): void {
  if (!tpl?.name || !tpl.mission) throw new Error("skill save: name and mission are required");
  // the name is the file name (verification round): a slug, so the one writer of _skills/ can never write outside it
  if (!/^[a-z0-9][a-z0-9-]*$/.test(tpl.name)) throw new Error(`skill save: name "${tpl.name}" is not a slug (lowercase letters, digits, hyphens) — it is the file name under _skills/`);
  const problems = manifestProblems(tpl.name, tpl);
  if (problems.length) throw new Error(problems[0]);
  mkdirSync(join(root, "_skills"), { recursive: true });
  writeFileSync(join(root, "_skills", `${tpl.name}.yaml`), stringify(tpl));
  try { record.sessionAppend(root, { at: new Date().toISOString(), verb: "saveSkill",
    detail: `${tpl.name}${tpl.variantOf ? ` (variant of ${tpl.variantOf})` : ""}` }); } catch { /* pre-record engagements */ }
}
/** the engagement's WHY, quoted into the brief: the first 20 lines of OBJECTIVE.md (review C10) */
function objective(root: string): string {
  const p = join(root, "OBJECTIVE.md");
  if (!existsSync(p)) return "(none)";
  const text = readFileSync(p, "utf8").split("\n").slice(0, 20).join("\n").trim();
  return text || "(none)";
}
/** the human's standing guidance, quoted from the pad's own heading — never the whole pad (review C10) */
function standingGuidance(root: string): string {
  const p = join(root, "STATE.md");
  if (!existsSync(p)) return "(none)";
  const lines = readFileSync(p, "utf8").split("\n");
  const i = lines.findIndex(l => /^#+\s*human's standing guidance\s*$/i.test(l.trim()));
  if (i < 0) return "(none)";
  const body: string[] = [];
  for (const l of lines.slice(i + 1)) { if (/^#+\s/.test(l)) break; body.push(l); }
  const text = body.join("\n").trim();
  return text || "(none)";
}
/**
 * the declared ports, printed into the brief so the worker knows its walls (A27).
 * The manifest is the wall; the prose that used to sit in `writes:` now lives in
 * the skill's rules, where a skill that needs to say "its one fragment" says it.
 */
function ports(sk: Skill): string[] {
  const lines = [
    `## Ports (your walls)`,
    `reads: ${sk.reads.length ? sk.reads.join(", ") : "nothing"}`,
    `writes: ${sk.writes.length ? sk.writes.join(", ") : "nothing"}`,
    `returns: ${sk.returns.length ? sk.returns.join(", ") : "nothing"}`,
    `runtime: ${sk.runtime === "prompt" ? "prompt" : `${sk.runtime.command}${sk.runtime.cwd ? ` (cwd ${sk.runtime.cwd})` : ""}`}`,
  ];
  if (sk.writes.includes("synthesis"))
    lines.push("your work products land under _synthesis/<skill>/<run>/ with a card; publish through publishSynthesis; a rerun is a new artifact");
  if (sk.returns.length)
    lines.push("hand your result back as a return file (see SKILL-CONTRACT.md); the consultant lands it with `consult return`");
  return lines;
}

/** resolve one skilled unit of work into a printable brief for one worker class */
export function compose(root: string, name: string, cls: WorkerClass, params: Record<string, unknown>): string {
  const sk = skill(root, name);
  // A22 — progressive disclosure at dispatch: the brief carries the INDEX (what exists) and the
  // full CARDS named in params.cards (what those are); CONTENT is named by path, never inlined.
  // The index is SCOPED (review finding): never _skills (the worker already holds its skill); when cards are
  // named, only their stores; otherwise every other store. `consult index` itself stays the full walk.
  const wanted = Array.isArray(params.cards) ? params.cards as string[] : [];
  const all = index.cards(root).filter(l => l.store !== "_skills");
  const cardBlock = wanted.flatMap(ref => {
    const c = index.card(root, ref);
    const content = all.find(l => l.ref === ref)?.content;
    return [`### ${ref}`, stringify(c).trimEnd(), ...(content ? [`content: ${content}`] : [])];
  });
  const stores = new Set(wanted.map(ref => all.find(l => l.ref === ref)?.store).filter(Boolean));
  const scoped = stores.size ? all.filter(l => stores.has(l.store)) : all;
  const indexText = scoped.map(l => `${l.store}  ${l.ref}  ·  ${l.title}  ·  ${l.kind}  —  ${l.summary}${l.src ? `  (${l.src})` : ""}${l.content ? `  ·  content: ${l.content}` : ""}`).join("\n");
  const lines = [
    `# BRIEF — ${sk.name} on worker-${cls}`,
    `## Objective`, objective(root),
    `## Standing guidance`, standingGuidance(root),
    `## Mission`, sk.mission,
    ...ports(sk),
    `## Context`, ...sk.contextContract,
    `## Index (${stores.size ? [...stores].join(", ") : "every store"} — open content only when its card says yes)`,
    indexText || "(nothing indexed)",
    ...(cardBlock.length ? [`## Cards (in scope for this unit)`, ...cardBlock] : []),
    `## Parameters`,
    ...Object.entries(params).filter(([k]) => k !== "cards").map(([k, v]) => `- ${k}: ${Array.isArray(v) ? v.join(", ") : String(v)}`),
    `## Rules (verbatim — these bind whoever works)`, ...sk.rules.map(r => `- ${r}`),
    `## Return contract`, ...sk.returnContract,
  ];
  return lines.join("\n");
}

/**
 * `consult skill check <name>` — the STATIC half of conformance (A27).
 * Never throws for a bad skill: a bad skill is a list of problems. It throws
 * only for a skill that does not exist, by name. The dynamic half (did it
 * actually read through the port, write only its own directory, stop for no
 * one) lives in harness/conformance.ts.
 */
export function skillCheck(root: string, name: string): { ok: boolean; problems: string[] } {
  const where = skillPath(root, name);   // throws by name when there is no such skill
  let raw: Partial<Skill> | undefined;
  try { raw = parse(readFileSync(where.manifest, "utf8")) as Skill; }
  catch (e) { return { ok: false, problems: [`skill ${name}: manifest does not parse — ${(e as Error).message}`] }; }
  const problems = manifestProblems(name, raw);
  if (where.level === 2) {
    problems.push(...runtimeProblems(name, where.dir, raw?.runtime));
    problems.push(...gateProblems(name, where.dir));
  }
  return { ok: problems.length === 0, problems };
}
/** a level-2 skill's runner must actually be there — relative to the skill dir, or on PATH */
function runtimeProblems(name: string, dir: string, rt: Runtime | undefined): string[] {
  if (!rt || rt === "prompt" || typeof rt !== "object" || typeof rt.command !== "string") return [];
  const first = rt.command.trim().split(/\s+/)[0];
  if (!first) return [`skill ${name}: runtime.command is empty`];
  const base = rt.cwd ? join(dir, rt.cwd) : dir;
  const isFile = (p: string) => { try { return statSync(p).isFile(); } catch { return false; } };
  if (isFile(join(base, first))) return [];
  for (const d of (process.env.PATH ?? "").split(delimiter)) if (d && isFile(join(d, first))) return [];
  return [`skill ${name}: runtime command "${first}" is not in the skill directory (${base}) and not on PATH`];
}
/**
 * a skill stops for no one: the two gates are the engine's. A level-2 skill's own
 * scripts may not carry the human-stop vocabulary — each hit is named file:line.
 */
function gateProblems(name: string, dir: string): string[] {
  const out: string[] = [];
  const walk = (d: string, rel: string) => {
    for (const e of readdirSync(d, { withFileTypes: true })) {
      const r = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) { if (e.name !== "node_modules" && e.name !== ".git") walk(join(d, e.name), r); continue; }
      if (!e.isFile() || r === "skill.yaml") continue;
      let text: string;
      try { text = readFileSync(join(d, e.name), "utf8"); } catch { continue; }
      if (text.includes("\u0000")) continue;   // not a script
      text.split("\n").forEach((line, i) => {
        const hit = line.includes("[HUMAN]") ? "[HUMAN]"
          : /run\.py\s+gate/.test(line) ? "run.py gate"
          : /(^|[^.\w])gate\s*\(/.test(line) && !/record\.gate\s*\(|consult\s+gate/.test(line) ? "gate(" : null;
        if (hit) out.push(`skill ${name}: ${r}:${i + 1} carries "${hit}" — a skill stops for no one; the two gates are the engine's`);
      });
    }
  };
  walk(dir, "");
  return out;
}
