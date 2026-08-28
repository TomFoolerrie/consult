/**
 * answers — the question interface. THIS MODULE IS THE PRODUCT.
 *
 * Owns: nothing. Assembles the GROUNDED MATERIAL for answering a human
 * question about the client, the honesty contract on every item via the
 * Standing union: evidenced (cited) | claimed (uncited, flagged) |
 * contested (both readings, never a winner) | absent (with the ask or
 * cheap read that would close it — "I don't know, and here's how we find
 * out" is a first-class result).
 *
 * Division of labor, stated plainly: this module does NOT phrase the
 * answer — the consultant does, in conversation. ground() returns material;
 * determinism stays in the engine, judgment stays in the tenancy. That
 * split is what makes "the AI just needs to know the answer or how to get
 * it" auditable: every sentence the consultant says can point at the
 * material it stood on.
 */
// A12: a statement citing a synthesis source takes the standing of that
// source's declared grounds, resolved through the chain — synthesis is
// citable, never standing-upgrading.
// Contract pins (post test-review): topic is a fragment slug or free
// text matched against slugs and statement text; items return in
// DOCUMENT ORDER, statements before callouts; each item carries `where`
// (the fragment slug). Assert by predicate, not position, all the same.
import type { Standing, Ground, SrcId, CalloutAddr } from "./types.ts";

export interface GroundedItem { text: string; standing: Standing; where: string; }

/** the grounded material for a topic: entities, callouts, coverage,
 *  register entries, conflicts — each tagged with its standing */
export function ground(root: string, topic: string): GroundedItem[] { throw new Error("mock-out"); }
/** resolve grounds to citable form (SRC ids, slug#ID addresses) or refuse by name */
export function cite(root: string, grounds: Ground[]): (SrcId | CalloutAddr)[] { throw new Error("mock-out"); }
