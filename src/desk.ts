/**
 * desk — the librarian's desk.
 *
 * Owns/writes: the hold block of _client/consult.yaml (self-verified line
 * surgery, restore-on-mismatch), git (checkpoint), the budget line of the
 * session record. Everything else is a read.
 *
 * state() replaces the thirteen-guard advisor AS THE SEAT OF CONTROL: it
 * does not command, it DESCRIBES — one snapshot the librarian consults.
 * The playbook order lives in the librarian's contract, not in code. Two
 * rules survive as structure: a self-contradictory folder is its own state
 * (EngagementHealth.contradiction) and blocks state-changing verbs; "all
 * quiet" requires positive evidence — quiet-by-damage is a contradiction,
 * never done. checkpoint() commits the WHOLE engagement (no curated
 * pathspec to forget a directory) and appends the session record.
 *
 * budget is the D9 mechanism, also governing the DIRECT-VS-DELEGATE
 * choice: the librarian may do any skill's work directly, and
 * dispatches the worker when the task's cost — judged from the objective
 * and the deliverable shape — warrants it. Estimates respect TOKEN
 * ASYMMETRY (input cheap on strong models, output dear): review-with-edits
 * is often the better spend than regeneration, and spend() records which
 * shape was chosen so the estimates stay auditable. Every spend
 * auto-proceeds under the sitting budget, waits above it or for anything
 * client-facing.
 */
import type { EngagementHealth } from "./types.ts";

export interface Snapshot {
  health: EngagementHealth;
  unrouted: string[]; coverageSummary: string; needsSummary: string;
  askDebts: { unsettled: number; openFlags: number };
  pinnedShapes: { name: string; serviceable: boolean }[];
  git: { clean: boolean; note?: string };
  holds: string[];
  budget: Budget;
}
export interface Budget { limit: number; spent: number; remaining: number; }

/** the engagement snapshot — describes, never commands; report() is its printable form (the librarian's sitting brief, R2) */
export function state(root: string): Snapshot { throw new Error("mock-out"); }
export function report(root: string): string { throw new Error("mock-out"); }
/** commit the whole engagement as consult: <label>; append the session record */
export function checkpoint(root: string, label: string, dryRun?: boolean): { committed: string[] } { throw new Error("mock-out"); }
/** the gate-answer verb: edit the hold block, self-verify, restore on mismatch */
export function editHold(root: string, action: string, release?: boolean): void { throw new Error("mock-out"); }
export function budgetSet(root: string, tokens: number): void { throw new Error("mock-out"); }
export function budget(root: string): Budget { throw new Error("mock-out"); }
/** record one spend's estimate and actual in the session record */
export function spend(root: string, estimate: number, actual: number, what: string): void { throw new Error("mock-out"); }
