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

// the card (A20/A22) — ONE schema for every item's cheap description:
// the scan template. summary + keyItems are the engine-validated floor;
// title/kind and kind-specific sections ride along. Describes the ITEM,
// never the engagement.
export interface Card { title?: string; kind?: string; summary: string; keyItems: readonly string[]; [section: string]: unknown; }

// the ask lifecycle — ONLY the events the folder cannot show (A18):
// answered/settled are COMPUTED (answeredBy non-empty; answering sources
// cited where the ask's questions live), never stored.
export type AskStatus = "proposed" | "accepted" | "sent" | "closed";
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
  | { kind: "contested"; readings: [Claim, Claim]; more?: SrcId[] }   // review A: a question may name more than two sources — the first two are the readings, the rest are KEPT here, never dropped
  | { kind: "absent"; question: CalloutAddr };   // A18: the open question's ADDRESS — phrasing the ask is the consultant's judgment, never the engine's
export interface Claim { text: string; source: SrcId; }

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

// the RETURN port (A27) — the one door for what a skill produces.
// A return is a HAND-OFF, never engagement state: findings become
// proposals, artifacts are recorded, and asks/statements/flags are
// handed to the consultant. Asks are the consultant's judgment and
// capture is written by hand, so `return` mints neither.
export interface ReturnFinding { claim: string; grounds: string[]; theme?: string; }
export interface ReturnAsk { text: string; questions: CalloutAddr[]; }
export interface ReturnStatement { slug: string; text: string; cites: string[]; }
export interface SkillReturn {
  skill: string; run: string;
  findings: ReturnFinding[]; asks: ReturnAsk[]; statements: ReturnStatement[];
  artifacts: SrcId[]; flags: string[];
}
export interface ReturnResult {
  minted: FindingId[];
  handed: { asks: ReturnAsk[]; statements: ReturnStatement[]; flags: string[] };
  artifacts: SrcId[];
}
