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

// the ask lifecycle (client cycle) — proposed → accepted → sent → answered → settled, or closed
export type AskStatus = "proposed" | "accepted" | "sent" | "answered" | "settled" | "closed";
export interface Ask {
  id: AskId; status: AskStatus; text: string;
  questions: CalloutAddr[]; audience: string; artifact: string;
  answeredBy?: SrcId; closedReason?: string;
}

// the honesty contract — every grounded statement carries its standing
export type Standing =
  | { kind: "evidenced"; sources: SrcId[] }
  | { kind: "claimed" }
  | { kind: "contested"; readings: [Claim, Claim] }
  | { kind: "absent"; proposal: ProposedAsk | ProposedRead };
export interface Claim { text: string; source: SrcId; }
export interface ProposedAsk { text: string; questions: CalloutAddr[]; }
export interface ProposedRead { question: string; sources: SrcId[]; }

// coverage — what the brain knows it knows, per taxonomy node
export type CoverageStatus = "evidenced" | "claimed" | "thin" | "conflicted" | "outstanding";

// findings — proposed → accepted | rejected (rejection terminal and kept)
export type FindingStatus = "proposed" | "accepted" | "rejected";
export interface Finding {
  id: FindingId; status: FindingStatus; claim: string;
  grounds: Ground[]; theme: string; rejectedReason?: string;
}

// the engagement snapshot never lies by omission: contradiction is a state
export type EngagementHealth =
  | { kind: "ok" }
  | { kind: "contradiction"; what: string; repair: string };
