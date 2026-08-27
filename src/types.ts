/**
 * types — the shared vocabulary, compiler-checked.
 *
 * This file is the TypeScript ruling made concrete: the lifecycles and
 * standings that lived as strings-in-dicts (and occasionally leaked) are
 * discriminated unions here. An illegal state is unrepresentable, not
 * merely tested for.
 */

// ids — branded so an ASK can never be passed where a SRC belongs
export type SrcId = `SRC-${number}`;
export type AskId = `ASK-${number}`;
export type FindingId = `FIND-${number}`;
/** fragment-qualified callout address (slug#LOCAL-ID), the grounding currency */
export type CalloutAddr = `${string}#${string}`;
export type Ground = SrcId | CalloutAddr | { slug: string };

// the ask lifecycle — proposed → accepted → sent → answered → settled, or closed
export type AskStatus = "proposed" | "accepted" | "sent" | "answered" | "settled" | "closed";
export interface Ask {
  id: AskId; status: AskStatus; text: string;
  questions: CalloutAddr[]; audience?: string; artifact?: string;
  answeredBy: readonly SrcId[];   // A14: one ask may be answered across responses
  closedReason?: string;
}

// the honesty contract — every grounded statement carries its standing.
// CODIFIED (A11): standings are COMPUTED at read time from the record's
// physical shape, never stored. evidenced = the citation resolves to an
// artifact on file in _sources/ (the line is AUDITABILITY, not truth);
// claimed = no citable provenance (a relayed conversation is routed as a
// note-source and cited, so it is evidenced BY THE NOTE — claimed is the
// residue for what has no artifact at all); contested = a question record
// naming two sources, both readings held; absent = a question record no
// statement answers, carrying the proposal that would close it.
export type Standing =
  | { kind: "evidenced"; sources: SrcId[] }
  | { kind: "claimed" }
  | { kind: "contested"; readings: [Claim, Claim] }
  | { kind: "absent"; proposal: ProposedAsk | ProposedRead };
export interface Claim { text: string; source: SrcId; }
export interface ProposedAsk { text: string; questions: CalloutAddr[]; }
export interface ProposedRead { question: string; sources: SrcId[]; }

// coverage — what the brain knows it knows, per taxonomy node.
// A13: no "thin" — thinness is a threshold judgment against the
// objective, the consultant's call; the engine reports the computable.
// A14: "contested", matching the statement standing — one concept, one name.
export type CoverageStatus = "evidenced" | "claimed" | "contested" | "outstanding";

// findings — proposed → accepted | rejected (rejection terminal and kept)
export type FindingStatus = "proposed" | "accepted" | "rejected";
export interface Finding {
  id: FindingId; status: FindingStatus; claim: string;
  grounds: Ground[]; theme?: string; rejectedReason?: string;
}

// the engagement snapshot never lies by omission: contradiction is a state
export type EngagementHealth =
  | { kind: "ok" }
  | { kind: "contradiction"; what: string; repair: string };
