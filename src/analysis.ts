/**
 * analysis — the mechanical half of the assessment license.
 *
 * Owns: nothing. Pure candidate GENERATORS, never verdicts: each verb
 * computes, deterministically, the population that may be judged. Whoever
 * judges receives candidates and never goes hunting — the feed is the
 * boundary that keeps "likely" out of the record.
 *
 * THE LICENSE ATTACHES TO THE ACTIVITY, NOT AN AGENT (ruled 2026-08-26,
 * artifact comment): the librarian may judge a feed itself — an analytical
 * question is just a question with a license attached — and dispatching a
 * separate analyst is a COST decision like any other delegation. Either
 * way the license rules hold: propose-only, grounds must resolve,
 * candidatesReceived === candidatesAssessed in the attestation, a feed's
 * gap is reported as a generator gap, never filled by invention.
 */
export const VERBS = ["pain-synthesis", "control-coverage", "conflict-support", "handoff-friction"] as const;
export type AnalysisVerb = (typeof VERBS)[number];

export interface Candidate { verb: AnalysisVerb; where: string; material: string; sources: string[]; }

/** the candidate feed for one verb, deterministic, engagement-scoped */
export function feeds(root: string, verb: AnalysisVerb): Candidate[] { throw new Error("mock-out"); }
/** THE artifact identity rule for edge matching, in one place */
export function normalizeArtifact(item: string): string { throw new Error("mock-out"); }
