/**
 * desk — the consultant's desk: the ONE derived picture. (A9 merge.)
 *
 * Owns/writes: git (checkpoint) and the budget line of the session
 * record. Everything else is a read. coverage.ts and needs.ts folded in
 * here (A9): three modules computing slices of "where are we" was a v1
 * org chart — state() carries coverage and needs as sections, and the
 * pure reads are exported from the desk.
 *
 * Holds do not exist as machinery (ROT-4): "ask first — don't fill until
 * I say" is a commitment the consultant records in its state pad and obeys.
 *
 * state() DESCRIBES, never commands — one snapshot the consultant
 * consults; report() is its printable form. Both are the MACHINE's
 * derived picture; the consultant's own working memory is <root>/STATE.md
 * (A8) — free prose the consultant writes directly, never parsed here,
 * committed by checkpoint like everything else.
 *
 * Two rules survive as structure: a self-contradictory folder is its own
 * state and blocks state-changing verbs; "all quiet" requires positive
 * evidence — quiet-by-damage is a contradiction, never done. checkpoint()
 * commits the WHOLE engagement and appends the session record.
 *
 * budget is the D9 mechanism, also governing direct-vs-delegate: every
 * spend is proposed with an estimate (priced with token asymmetry in
 * mind — review-with-edits over regeneration where it wins),
 * auto-proceeds under the sitting budget, waits above it or for anything
 * client-facing. spend() records estimate and actual so pricing stays
 * auditable.
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
  budget: Budget;
}
export interface Budget { limit: number; spent: number; remaining: number; }
export interface NodeCoverage { slug: string; status: CoverageStatus; conflicts: string[]; }
export interface Need { shape: string; part: string; standing: Standing; }

/** the engagement snapshot — describes, never commands */
export function state(root: string): Snapshot { throw new Error("mock-out"); }
/** the printable form — the consultant's sitting picture */
export function report(root: string): string { throw new Error("mock-out"); }
/** pure read: per-node coverage status + lens conflicts, recomputed every call */
export function coverage(root: string): NodeCoverage[] { throw new Error("mock-out"); }
/** pure read: what a pinned shape (or all) still lacks — standing state as a read */
export function needs(root: string, deliverable?: string): Need[] { throw new Error("mock-out"); }
/** commit the whole engagement as consult: <label>; append the session record */
export function checkpoint(root: string, label: string, dryRun?: boolean): { committed: string[] } { throw new Error("mock-out"); }
export function budgetSet(root: string, tokens: number): void { throw new Error("mock-out"); }
export function budget(root: string): Budget { throw new Error("mock-out"); }
/** record one spend's estimate and actual in the session record */
export function spend(root: string, estimate: number, actual: number, what: string): void { throw new Error("mock-out"); }
