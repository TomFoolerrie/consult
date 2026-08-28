/**
 * check — the QC gate over capture.
 *
 * Owns: NOTHING (ROT-5 — signal files were the dead guard table's stage
 * markers; the session record logs that a check ran). Runs over the whole
 * engagement (no area parameter — ROT-3). Six checks, all MECHANICAL —
 * the hedges check is gone (A9): word-list policing of prose style is a
 * skill rule that binds whoever drafts, not an engine invariant.
 *
 *   grammar        per-fragment parse through the declaration
 *   citations      every cited SRC resolves. An UNCITED capture
 *                  statement is NOT an error — it is the claimed
 *                  standing, legitimate by design; the cites-required
 *                  rule binds synthesis/deliverable DRAFTS only
 *   consumption    intent slugs exist · synthesis grounds resolve ·
 *                  a retired source is actually fully cited (A18 —
 *                  citations are load-bearing for ledger, asks, answers)
 *   mentions       a slug mentioned in prose exists (warning)
 *   ask-coverage   every question id in the ask register exactly once
 *   registers      referenced register entries resolve; citable fields not blank;
 *                  synthesis sources declare resolvable grounds (A12)
 *
 * Errors exit nonzero; warnings print; every message names file and line.
 */
export interface Defect { check: string; severity: "error" | "warning"; file: string; line?: number; message: string; }
export type Check = (root: string) => Defect[];
export const CHECKS: readonly Check[] = [];

/** the whole gate; empty error list = clean */
export function run(root: string): Defect[] { throw new Error("mock-out"); }
