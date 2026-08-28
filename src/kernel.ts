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
export function loadType(root: string, name: TypeDecl["name"]): TypeDecl { throw new Error("mock-out"); }
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
export function parseEntity(text: string, tdecl: TypeDecl, slug: string): Entity { throw new Error("mock-out"); }
/** every open question on one entity, document order */
export function openQuestions(entity: Entity): Callout[] { throw new Error("mock-out"); }

/** every capture fragment, slug order, parsed through the declaration (A18, from engagement.ts) */
export function entities(root: string): Entity[] { throw new Error("mock-out"); }
/** every taxonomy node, name order (A18, from engagement.ts) */
export function taxonomy(root: string): Entity[] { throw new Error("mock-out"); }
