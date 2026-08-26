/**
 * check — the QC gate, distilled.
 *
 * Owns: its signal file only. The oracle's reconcile at v2's size: the
 * eleven checks that defended live runs, none that defended v1 —
 * grammar · substance · citations · touches · xrefs · hedges ·
 * individuals · markers · ask-coverage · placeholders · registers.
 * Errors exit nonzero; warnings print; every message names file and line.
 */
export interface Defect { check: string; severity: "error" | "warning"; file: string; line?: number; message: string; }

export type Check = (root: string, area: string) => Defect[];
export const CHECKS: readonly Check[] = [];

/** the whole gate over one area; empty error list = clean */
export function run(root: string, area: string): Defect[] { throw new Error("mock-out"); }
