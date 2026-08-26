/**
 * kernel — type declarations + fragment parsing.
 *
 * Owns: nothing. Loads the two type declarations (process-step,
 * taxonomy-node) from kernel/types/*.yaml and parses a fragment's markdown
 * into an Entity through its declaration. The declaration is the vocabulary
 * authority: parts, callout kinds with declared fields (CONTROL's four,
 * GAP's Grounds+Nature), channels. No aliases of any kind — v1's ghost.
 * A refused declaration is never half-registered.
 */
import type { CalloutAddr } from "./types.ts";

export interface TypeDecl {
  name: "process-step" | "taxonomy-node";
  parts: readonly PartDecl[];
  callouts: readonly CalloutDecl[];
  channels: readonly string[];
}
export interface PartDecl { slug: string; title: string; kind: "prose" | "list" | "table"; }
export interface CalloutDecl { label: string; prefix: string; home: string; fields?: readonly string[]; }
export interface Entity {
  slug: string;
  parts: ReadonlyMap<string, string>;
  callouts: readonly Callout[];
  bindings: ReadonlyMap<string, readonly string[]>;
}
export interface Callout { addr: CalloutAddr; label: string; text: string; fields: ReadonlyMap<string, string>; }

/** load + validate a declaration; cached; fail-loud with the defect named */
export function loadType(name: TypeDecl["name"]): TypeDecl { throw new Error("mock-out"); }
/** parse one fragment through its declaration; grammar defects are named errors */
export function parseEntity(text: string, tdecl: TypeDecl, slug: string): Entity { throw new Error("mock-out"); }
/** every open validation gap on one entity, document order */
export function openGaps(entity: Entity): Callout[] { throw new Error("mock-out"); }
