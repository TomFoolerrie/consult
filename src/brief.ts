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
 * compose() resolves one skilled unit of work — files and sources in
 * scope, register slices, the consultant's standing precedent and open
 * observations (from the state pad), the objective's
 * framing, the skill's rules verbatim — into one printable brief.
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
  for (const k of ["contextContract", "returnContract", "rules"] as const)
    if (!Array.isArray(tpl[k])) throw new Error(`skill save: ${tpl.name} — ${k} must be a list`);
  if (!["haiku", "sonnet", "opus"].includes(String(tpl.recommendedClass))) throw new Error(`skill save: ${tpl.name} — recommendedClass "${String(tpl.recommendedClass)}" is not haiku | sonnet | opus`);
  mkdirSync(join(root, "_skills"), { recursive: true });
  writeFileSync(join(root, "_skills", `${tpl.name}.yaml`), stringify(tpl));
  try { record.sessionAppend(root, { at: new Date().toISOString(), verb: "saveSkill",
    detail: `${tpl.name}${tpl.variantOf ? ` (variant of ${tpl.variantOf})` : ""}` }); } catch { /* pre-record engagements */ }
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
  const indexText = scoped.map(l => `${l.store}  ${l.ref}  ·  ${l.title}  ·  ${l.kind}  —  ${l.summary}${l.src ? `  (${l.src})` : ""}`).join("\n");
  const lines = [
    `# BRIEF — ${sk.name} on worker-${cls}`,
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
