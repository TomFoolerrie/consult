/**
 * kernel — type declarations + fragment parsing.
 *
 * Owns: nothing. Two types (process-step, taxonomy-node), one parse.
 *
 * THE CALLOUT RULING (2026-08-26): the engine hard-codes exactly ONE
 * callout kind — the QUESTION record (v1 called it GAP) — because the
 * registers join on it: asks reference question ids, coverage's
 * `conflicted` reads a question naming two sources, answers' "absent"
 * standing stands on it. Every OTHER kind (CONTROL, PAIN POINT,
 * IMPROVEMENT OPPORTUNITY, anything an objective wants) is DECLARED
 * VOCABULARY: shipped as a default in the type YAML, engagement-amendable
 * like a skill or a definition, never engine law. Skills BIND to declared
 * kinds (a drafting skill carries the discipline for minting them well);
 * they never define the schema. SCREENSHOT PLACEHOLDER does not exist.
 *
 * No aliases of any kind, ever.
 */
// A18 (M5): kernel absorbs the folder enumeration — capture's joints are
// the GRAMMAR (this module) and the STANDING (answers.ts), not v1's three
// read modules. Fragments live flat in <root>/capture/, taxonomy nodes in
// capture/_taxonomy/; no manifest, no areas; capture is a direct write.
import type { CalloutAddr } from "./types.ts";
import { parse } from "yaml";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const SHIPPED = join(dirname(fileURLToPath(import.meta.url)), "..", "kernel");

export const QUESTION_KIND = "question" as const; // the one engine-known kind


export interface TypeDecl {
  name: "process-step" | "taxonomy-node";
  parts: readonly PartDecl[];
  callouts: readonly CalloutDecl[]; // must include the question kind; rest is vocabulary
  channels: readonly string[];
}
export interface PartDecl { slug: string; title: string; kind: "prose" | "list" | "table"; }
export interface CalloutDecl { kind: string; label: string; prefix: string; home: string; fields?: readonly string[]; }
export interface Entity {
  slug: string;
  parts: ReadonlyMap<string, string>;
  /** the second primitive: statements carrying machine-readable citations */
  statements: readonly Statement[];
  callouts: readonly Callout[];
  bindings: ReadonlyMap<string, readonly string[]>;
}
export interface Statement { text: string; cites: readonly SrcRef[]; }
export type SrcRef = `SRC-${number}`;
export interface Callout { id: string; addr: CalloutAddr; kind: string; label: string; text: string; fields: ReadonlyMap<string, string>; }

/** load + validate a declaration (engagement overlay may amend vocabulary); fail-loud */
export function loadType(root: string, name: TypeDecl["name"]): TypeDecl {
  const local = join(root, "_types", `${name}.yaml`);
  const path = existsSync(local) ? local : join(SHIPPED, "types", `${name}.yaml`);
  let raw: unknown;
  try { raw = parse(readFileSync(path, "utf8")); }
  catch (e) { throw new Error(`type declaration ${name}: ${(e as Error).message}`); }
  const t = raw as TypeDecl;
  if (!t || t.name !== name || !Array.isArray(t.callouts))
    throw new Error(`type declaration ${name}: malformed at ${path}`);
  if (!t.callouts.some(c => c.kind === QUESTION_KIND))
    throw new Error(`type declaration ${name}: the question kind is engine law and must be declared`);
  return t;
}
/**
 * parse one fragment through its declaration; grammar defects are named errors.
 * THE THREE-PRIMITIVE GRAMMAR (A11): the engine prescribes only (1)
 * addressable units — slugs and local ids, (2) statements carrying
 * machine-readable citations, (3) the question record. Everything above
 * the grammar — parts, vocabulary, atoms, the taxonomy's meaning — is the
 * consultant's choice via the engagement-amendable type declarations,
 * shaped from the objective. YAML is the shipped default surface, not a
 * law: the parse lives here alone, and an alternative surface satisfying
 * the grammar is a kernel amendment, not a redesign.
 */
export function parseEntity(text: string, tdecl: TypeDecl, slug: string): Entity {
  let raw: any;
  try { raw = parse(text); }
  catch (e) { throw new Error(`fragment ${slug}: ${(e as Error).message}`); }
  if (!raw || typeof raw !== "object" || raw.slug !== slug)
    throw new Error(`fragment ${slug}: slug field must match the file name`);
  const statements: Statement[] = [];
  for (const st of raw.statements ?? []) {
    if (typeof st?.text !== "string") throw new Error(`fragment ${slug}: statement without text`);
    const cites = (st.cites ?? []).map((c: unknown) => {
      if (typeof c !== "string" || !/^SRC-\d+$/.test(c))
        throw new Error(`fragment ${slug}: malformed citation ${String(c)}`);
      return c as SrcRef;
    });
    statements.push({ text: st.text, cites });
  }
  const qdecl = tdecl.callouts.find(c => c.kind === QUESTION_KIND)!;
  const callouts: Callout[] = [];
  for (const q of raw.questions ?? []) {
    if (typeof q?.id !== "string" || typeof q?.text !== "string")
      throw new Error(`fragment ${slug}: question record needs id and text`);
    const fields = new Map<string, string>();
    if (Array.isArray(q.sources)) fields.set("sources", q.sources.join(", "));
    callouts.push({ id: q.id, addr: `${slug}#${q.id}`, kind: QUESTION_KIND, label: qdecl.label, text: q.text, fields });
  }
  const parts = new Map<string, string>();
  for (const p of tdecl.parts) if (typeof raw[p.slug] === "string") parts.set(p.slug, raw[p.slug]);
  return { slug, parts, statements, callouts, bindings: new Map() };
}
/** every open question on one entity, document order */
export function openQuestions(entity: Entity): Callout[] {
  return entity.callouts.filter(c => c.kind === QUESTION_KIND);
}

/** every capture fragment, slug order, parsed through the declaration (A18, from engagement.ts) */
export function entities(root: string): Entity[] {
  const dir = join(root, "capture");
  if (!existsSync(dir)) return [];
  const tdecl = loadType(root, "process-step");
  return readdirSync(dir).filter(f => f.endsWith(".yaml")).sort()
    .map(f => parseEntity(readFileSync(join(dir, f), "utf8"), tdecl, f.replace(/\.yaml$/, "")));
}
/** every taxonomy node, name order (A18, from engagement.ts) */
export function taxonomy(root: string): Entity[] {
  const dir = join(root, "capture", "_taxonomy");
  if (!existsSync(dir)) return [];
  const tdecl = loadType(root, "taxonomy-node");
  return readdirSync(dir).filter(f => f.endsWith(".yaml")).sort()
    .map(f => parseEntity(readFileSync(join(dir, f), "utf8"), tdecl, f.replace(/\.yaml$/, "")));
}
