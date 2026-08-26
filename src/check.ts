/**
 * check — the QC gate, distilled to capture quality.
 *
 * Owns: its signal file only. Eight checks (R3): the marker and
 * placeholder checks died with derived files (R1 — the failure mode is
 * structurally impossible), and substance folded into grammar. What
 * remains is purely about the quality of CAPTURE:
 *
 *   grammar       per-fragment parse through the declaration (a heading-only
 *                 fragment is a grammar defect)
 *   citations     every cited SRC resolves; drafted prose cites
 *   touches       ledger touches ⊆ manifest slugs
 *   xrefs         every [[slug]] resolves; dangling is an error
 *   hedges        uncertainty lives in callouts, never body prose
 *   individuals   people appear by role, never by name
 *   ask-coverage  every gap id in the ask register exactly once
 *   registers     referenced register entries resolve; citable fields not blank
 *
 * Errors exit nonzero; warnings print; every message names file and line.
 */
export interface Defect { check: string; severity: "error" | "warning"; file: string; line?: number; message: string; }
export type Check = (root: string, area: string) => Defect[];
export const CHECKS: readonly Check[] = [];

/** the whole gate over one area; empty error list = clean */
export function run(root: string, area: string): Defect[] { throw new Error("mock-out"); }
