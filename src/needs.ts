/**
 * needs — what the objective's shapes still lack.
 *
 * Owns: nothing. A pure read over the PINNED definitions, the coverage
 * map, and the registers. Each need names the deliverable it blocks, what
 * is missing, where, and on what grounds. "First-class standing state"
 * realized as a derived view — always current because recomputed, never
 * kept. The client cycle runs on this module: needs → curated asks →
 * responses → needs shrink. A deliverable is renderable when its needs are
 * empty or every remainder is a recorded, deliberate gap.
 */
import type { Ground } from "./types.ts";

export interface Need { deliverable: string; kind: string; need: string; where: string; grounds: Ground[]; }

/** every need blocking the pinned shapes (or one named shape) */
export function standing(root: string, deliverable?: string): Need[] { throw new Error("mock-out"); }
/** the needs view as printable text, grouped per deliverable then per feed */
export function render(root: string, deliverable?: string): string { throw new Error("mock-out"); }
