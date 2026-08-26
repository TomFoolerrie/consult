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
export type FlagId = `FLAG-${number}`;
export type TenureId = `TEN-${number}`;
/** procedure-qualified callout address, the grounding currency */
export type CalloutAddr = `${string}#${string}`;
export type Ground = SrcId | CalloutAddr | { slug: string };

// the ask lifecycle (client cycle) — proposed → accepted → sent → answered → settled, or retired
export type AskStatus = "proposed" | "accepted" | "sent" | "answered" | "settled" | "retired";
export interface Ask {
  id: AskId; status: AskStatus; text: string;
  gaps: CalloutAddr[]; audience: string; artifact: string;
  answeredBy?: SrcId; retiredReason?: string;
}

// the honesty contract — every grounded statement carries its standing
export type Standing =
  | { kind: "evidenced"; sources: SrcId[] }
  | { kind: "claimed" }
  | { kind: "contested"; readings: [Claim, Claim] }
  | { kind: "absent"; proposal: ProposedAsk | ProposedRead };
export interface Claim { text: string; source: SrcId; }
export interface ProposedAsk { text: string; gaps: CalloutAddr[]; }
export interface ProposedRead { question: string; sources: SrcId[]; }

// coverage — what the brain knows it knows, per taxonomy node
export type CoverageStatus = "evidenced" | "claimed" | "thin" | "conflicted" | "outstanding";

// findings — proposed → accepted | rejected (rejection terminal and kept)
export type FindingStatus = "proposed" | "accepted" | "rejected";
export interface Finding {
  id: FindingId; status: FindingStatus; claim: string;
  grounds: Ground[]; theme: string; rejectedReason?: string;
}

// journal
export type FlagState = "open" | "actioned" | "declined";
export type TenureKind = "ruling" | "deferred" | "doubt";

// the engagement snapshot never lies by omission: contradiction is a state
export type EngagementHealth =
  | { kind: "ok" }
  | { kind: "contradiction"; what: string; repair: string };
