/**
 * desk — the ONE derived picture, now PURE (A18 split, M3).
 *
 * Owns: NOTHING. The A9/A15 merges welded the system's purest reads to
 * its only machine-writes; A18 split them back along the store line —
 * the machinery's hand (git, sessions, budget, gates) lives in
 * record.ts. This module writes nothing, caches nothing, ever: the
 * module now matches its own doctrine.
 *
 * state() DESCRIBES, never commands — one snapshot the consultant
 * consults; report() is its printable form. locate/health is snapshot
 * material (A18, absorbing engagement.locate): the root is the
 * directory holding _sources/; an engagement-shaped tree without the
 * marker is a named CONTRADICTION whose `repair` field names the one
 * verb allowed to run. "All quiet" requires positive evidence —
 * quiet-by-damage is a contradiction, never done.
 *
 * After a fold-in the consultant edits capture, checks, checkpoints —
 * and state() already shows which sources retired and which asks
 * settled, because the capture diff IS the credit (A18).
 *
 * BARE-ENGAGEMENT DEFAULTS, pinned: budget before budgetSet is
 * {limit: 0, spent: 0, remaining: 0} (nothing auto-proceeds until a
 * budget is set); a root that is not a git repo reports git.clean:
 * false with a note naming it; pinnedShapes lists ONLY definitions the
 * engagement has pinned — shipped definitions are NOT auto-pinned.
 *
 * Holds do not exist as machinery (ROT-4): "ask first" is a state-pad
 * commitment the consultant obeys.
 */
import type { CoverageStatus, EngagementHealth, Standing } from "./types.ts";

export interface Snapshot {
  health: EngagementHealth;
  unrouted: string[];
  coverage: NodeCoverage[];        // per taxonomy node, recomputed
  needs: Need[];                   // what each pinned shape still lacks
  askDebts: { unsettled: number };
  pinnedShapes: { name: string; serviceable: boolean }[];
  git: { clean: boolean; note?: string };
  budget: { limit: number; spent: number; remaining: number };
}
export interface NodeCoverage { slug: string; status: CoverageStatus; conflicts: string[]; }
export interface Need { shape: string; part: string; standing: Standing; }

/** walk up to the _sources/ marker; absence and contradiction are named results (A18, from engagement.ts) */
export function locate(path: string): { root: string; health: EngagementHealth } { throw new Error("mock-out"); }
/** the engagement snapshot — describes, never commands */
export function state(root: string): Snapshot { throw new Error("mock-out"); }
/** the printable form — the consultant's sitting picture */
export function report(root: string): string { throw new Error("mock-out"); }
/** pure read: per-node coverage status + lens conflicts, recomputed every call */
export function coverage(root: string): NodeCoverage[] { throw new Error("mock-out"); }
/** pure read: what a pinned shape (or all) still lacks — standing state as a read */
export function needs(root: string, deliverable?: string): Need[] { throw new Error("mock-out"); }
