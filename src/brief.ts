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
 * Issued when, and only when, delegation happens; the consultant's own
 * picture is desk.report. The brief decides nothing about content.
 */
import { parse, stringify } from "yaml";
import { readFileSync, writeFileSync, existsSync, readdirSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as record from "./record.ts";
import * as index from "./index.ts";

const SHIPPED = join(dirname(fileURLToPath(import.meta.url)), "..", "kernel", "skills");

export type WorkerClass = "haiku" | "sonnet" | "opus";

export interface Skill {
  name: string;
  mission: string;
  writes: string | null;            // the write boundary, or null for read-only work
  contextContract: readonly string[];
  returnContract: readonly string[];
  rules: readonly string[];
  recommendedClass: WorkerClass;    // advisory; overrides are recorded with reason
  origin: "shipped" | "engagement"; // engagement skills shadow shipped ones by name
  variantOf?: string;               // set when authored as a variant
}

/** resolve a skill by name: engagement store shadows shipped; unknown is a named refusal */
export function skill(root: string, name: string): Skill {
  const local = join(root, "_skills", `${name}.yaml`);
  const shipped = join(SHIPPED, `${name}.yaml`);
  const path = existsSync(local) ? local : shipped;
  if (!existsSync(path)) throw new Error(`skill: no skill named ${name} (shipped or engagement-authored)`);
  const raw = parse(readFileSync(path, "utf8")) as Skill;
  if (!raw?.name || !raw.mission) throw new Error(`skill ${name}: malformed — mission required`);
  // the three list fields, validated where the skill is READ too (review C10): a string composes into "not iterable"
  for (const k of ["contextContract", "returnContract", "rules"] as const)
    if (!Array.isArray(raw[k])) throw new Error(`skill ${name}: ${k} must be a list, not ${typeof raw[k]}`);
  // the class is a dial with three positions; a skill may hedge in prose elsewhere, never here
  const cls = String(raw.recommendedClass ?? "").split(/[;\s]/)[0] as WorkerClass;
  if (!["haiku", "sonnet", "opus"].includes(cls)) throw new Error(`skill ${name}: recommendedClass "${String(raw.recommendedClass)}" is not haiku | sonnet | opus`);
  return { ...raw, recommendedClass: cls };
}
/** every skill visible to this engagement (shipped + authored), shadowing applied */
export function skills(root: string): Skill[] {
  const names = new Set<string>();
  const local = join(root, "_skills");
  if (existsSync(local)) for (const f of readdirSync(local)) if (f.endsWith(".yaml")) names.add(f.replace(/\.yaml$/, ""));
  if (existsSync(SHIPPED)) for (const f of readdirSync(SHIPPED)) if (f.endsWith(".yaml")) names.add(f.replace(/\.yaml$/, ""));
  return [...names].sort().map(n => skill(root, n));
}
/** save an ad-hoc skill (from scratch or a variant) into _skills/ — always saved before use, logged in the session record */
export function saveSkill(root: string, tpl: Skill): void {
  if (!tpl?.name || !tpl.mission) throw new Error("skill save: name and mission are required");
  // the name is the file name (verification round): a slug, so the one writer of _skills/ can never write outside it
  if (!/^[a-z0-9][a-z0-9-]*$/.test(tpl.name)) throw new Error(`skill save: name "${tpl.name}" is not a slug (lowercase letters, digits, hyphens) — it is the file name under _skills/`);
  for (const k of ["contextContract", "returnContract", "rules"] as const)
    if (!Array.isArray(tpl[k])) throw new Error(`skill save: ${tpl.name} — ${k} must be a list`);
  if (!["haiku", "sonnet", "opus"].includes(String(tpl.recommendedClass))) throw new Error(`skill save: ${tpl.name} — recommendedClass "${String(tpl.recommendedClass)}" is not haiku | sonnet | opus`);
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
    `## Write boundary`, sk.writes ?? "nothing — read-only work",
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
