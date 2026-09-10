/**
 * kernel — type declarations + fragment parsing.
 *
 * Owns: nothing. Two types (process-step, taxonomy-node), one parse.
 *
 * THE CALLOUT RULING (2026-08-26): the engine hard-codes exactly ONE
 * callout kind — the QUESTION record (v1 called it GAP) — because the
 * registers join on it: asks reference question ids, coverage's
 * `conflicted` reads a question naming two sources, answers' "absent"
 * standing stands on it. Every OTHER kind is DECLARED VOCABULARY: what
 * the shipped process-step YAML actually declares today is CONTROL,
 * PAIN POINT and INPUT/OUTPUT (taxonomy-node declares the question kind
 * alone); an engagement overlay may amend that list like a skill or a
 * definition — it is never engine law. Declared kinds are LIVE: a
 * fragment carries them in a top-level `callouts:` list of
 * { kind, id, text }, parsed here, refused by name when the kind is not
 * declared. Skills BIND to declared kinds (a drafting skill carries the
 * discipline for minting them well); they never define the schema.
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
  /** the fragment's card (A22): what this unit is ABOUT — intent, not summary, so it cannot go stale */
  scope?: string;
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
  const claim = (id: unknown, what: string) => {
    if (typeof id !== "string" || !id) throw new Error(`fragment ${slug}: ${what} needs id and text`);
    if (callouts.some(c => c.id === id)) throw new Error(`fragment ${slug}: duplicate callout id ${id}`);
  };
  for (const q of raw.questions ?? []) {
    if (typeof q?.id !== "string" || typeof q?.text !== "string")
      throw new Error(`fragment ${slug}: question record needs id and text`);
    if (callouts.some(c => c.id === q.id)) throw new Error(`fragment ${slug}: duplicate question id ${q.id}`);
    const fields = new Map<string, string>();
    if (q.sources !== undefined && !Array.isArray(q.sources)) throw new Error(`fragment ${slug}: question ${q.id} sources must be a list`);
    if (Array.isArray(q.sources)) fields.set("sources", q.sources.join(", "));
    callouts.push({ id: q.id, addr: `${slug}#${q.id}`, kind: QUESTION_KIND, label: qdecl.label, text: q.text, fields });
  }
  // the DECLARED vocabulary, live (review A/F5b): { kind, id, text } for any
  // non-question kind the declaration names; ids are unique across the whole
  // fragment, questions included; the label rides in from the declaration.
  if (raw.callouts !== undefined && !Array.isArray(raw.callouts))
    throw new Error(`fragment ${slug}: callouts must be a list`);
  for (const c of raw.callouts ?? []) {
    if (typeof c?.kind !== "string")
      throw new Error(`fragment ${slug}: callout without a kind`);
    if (c.kind === QUESTION_KIND)
      throw new Error(`fragment ${slug}: callout ${String(c.id)} is kind ${QUESTION_KIND} — question records live in the questions list`);
    const decl = tdecl.callouts.find(d => d.kind === c.kind);
    if (!decl) throw new Error(`fragment ${slug}: callout ${String(c.id)} declares kind ${c.kind}, which ${tdecl.name} does not declare`);
    if (typeof c.text !== "string") throw new Error(`fragment ${slug}: callout ${String(c.id)} needs id and text`);
    claim(c.id, `callout of kind ${c.kind}`);
    const fields = new Map<string, string>();
    for (const f of decl.fields ?? []) if (typeof c[f] === "string") fields.set(f, c[f]);
    callouts.push({ id: c.id, addr: `${slug}#${c.id}`, kind: c.kind, label: decl.label, text: c.text, fields });
  }
  const parts = new Map<string, string>();
  for (const p of tdecl.parts) if (typeof raw[p.slug] === "string") parts.set(p.slug, raw[p.slug]);
  const ent: Entity = { slug, parts, statements, callouts, bindings: new Map() };
  if (typeof raw.scope === "string") ent.scope = raw.scope;
  return ent;
}
/** every open question on one entity, document order */
export function openQuestions(entity: Entity): Callout[] {
  return entity.callouts.filter(c => c.kind === QUESTION_KIND);
}

/**
 * the non-conforming names under capture/ (review A/F5a): a .yml file or any
 * subdirectory other than _taxonomy is silently invisible to enumeration —
 * so the grammar check names it instead of letting it disappear.
 */
export function captureAnomalies(root: string): { path: string; message: string }[] {
  const dir = join(root, "capture");
  if (!existsSync(dir)) return [];
  const out: { path: string; message: string }[] = [];
  for (const d of readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
    if (d.isDirectory()) {
      if (d.name !== "_taxonomy") out.push({ path: `capture/${d.name}/`, message: `capture/${d.name}/: no nested directories under capture/` });
    } else if (d.name.endsWith(".yml")) {
      out.push({ path: `capture/${d.name}`, message: `capture/${d.name}: fragments are .yaml files` });
    }
  }
  return out;
}
/** every capture fragment, slug order, parsed through the declaration (A18, from engagement.ts) */
export function entities(root: string): Entity[] {
  const dir = join(root, "capture");
  if (!existsSync(dir)) return [];
  const tdecl = loadType(root, "process-step");
  return readdirSync(dir).filter(f => f.endsWith(".yaml")).sort()
    .map(f => parseEntity(readFileSync(join(dir, f), "utf8"), tdecl, f.replace(/\.yaml$/, "")));
}
/** the parseable fragments only — for reads that must survive one malformed file (review B5); check names the bad ones */
export function entitiesLenient(root: string): Entity[] {
  const dir = join(root, "capture");
  if (!existsSync(dir)) return [];
  const tdecl = loadType(root, "process-step");
  const out: Entity[] = [];
  for (const f of readdirSync(dir).filter(f => f.endsWith(".yaml")).sort()) {
    try { out.push(parseEntity(readFileSync(join(dir, f), "utf8"), tdecl, f.replace(/\.yaml$/, ""))); } catch { /* grammar defect — check reports it */ }
  }
  return out;
}
export function taxonomyLenient(root: string): Entity[] {
  const dir = join(root, "capture", "_taxonomy");
  if (!existsSync(dir)) return [];
  const tdecl = loadType(root, "taxonomy-node");
  const out: Entity[] = [];
  for (const f of readdirSync(dir).filter(f => f.endsWith(".yaml")).sort()) {
    try { out.push(parseEntity(readFileSync(join(dir, f), "utf8"), tdecl, f.replace(/\.yaml$/, ""))); } catch { /* grammar defect — check reports it */ }
  }
  return out;
}
/** every taxonomy node, name order (A18, from engagement.ts) */
export function taxonomy(root: string): Entity[] {
  const dir = join(root, "capture", "_taxonomy");
  if (!existsSync(dir)) return [];
  const tdecl = loadType(root, "taxonomy-node");
  return readdirSync(dir).filter(f => f.endsWith(".yaml")).sort()
    .map(f => parseEntity(readFileSync(join(dir, f), "utf8"), tdecl, f.replace(/\.yaml$/, "")));
}
