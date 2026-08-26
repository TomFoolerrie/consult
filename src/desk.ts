/**
 * desk — the librarian's desk.
 *
 * Owns/writes: git (checkpoint) and the budget line of the session
 * record. Everything else is a read. Holds do not exist as machinery
 * (ROT-4): "ask first — don't fill until I say" is a commitment the
 * librarian records in its journal and obeys; no YAML block, no line
 * surgery, no hold verbs.
 *
 * state() DESCRIBES, never commands — one snapshot the librarian
 * consults; report() is its printable form. Two rules survive as
 * structure: a self-contradictory folder is its own state and blocks
 * state-changing verbs; "all quiet" requires positive evidence —
 * quiet-by-damage is a contradiction, never done. checkpoint() commits
 * the WHOLE engagement and appends the session record.
 *
 * budget is the D9 mechanism, also governing direct-vs-delegate: every
 * spend is proposed with an estimate (priced with token asymmetry in
 * mind — review-with-edits over regeneration where it wins),
 * auto-proceeds under the sitting budget, waits above it or for anything
 * client-facing. spend() records estimate and actual so pricing stays
 * auditable.
 */
import type { EngagementHealth } from "./types.ts";

export interface Snapshot {
  health: EngagementHealth;
  unrouted: string[]; coverageSummary: string; needsSummary: string;
  askDebts: { unsettled: number; openFlags: number };
  pinnedShapes: { name: string; serviceable: boolean }[];
  git: { clean: boolean; note?: string };
  budget: Budget;
}
export interface Budget { limit: number; spent: number; remaining: number; }

/** the engagement snapshot — describes, never commands */
export function state(root: string): Snapshot { throw new Error("mock-out"); }
/** the printable form — the librarian's sitting picture */
export function report(root: string): string { throw new Error("mock-out"); }
/** commit the whole engagement as consult: <label>; append the session record */
export function checkpoint(root: string, label: string, dryRun?: boolean): { committed: string[] } { throw new Error("mock-out"); }
export function budgetSet(root: string, tokens: number): void { throw new Error("mock-out"); }
export function budget(root: string): Budget { throw new Error("mock-out"); }
/** record one spend's estimate and actual in the session record */
export function spend(root: string, estimate: number, actual: number, what: string): void { throw new Error("mock-out"); }
