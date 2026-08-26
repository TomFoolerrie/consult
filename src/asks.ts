/**
 * asks — the client-engagement register. FIRST CLASS.
 *
 * Owns/writes: _registers/asks.yaml (one dump, the module's only write).
 * The brain generates client engagement throughout the engagement; this
 * register holds every curated request from proposal to settlement.
 *
 * ASK ECONOMY — a GUIDING PRINCIPLE, not a rule (ruled 2026-08-26): asks
 * are tailored to the client relationship, and clients answer artifacts,
 * not question lists — prefer FEW, SIMPLE, ARTIFACT-SHAPED requests
 * ("send the org chart, the policy doc, a data export") where one artifact
 * closes many gaps. But if the objective needs something, it needs
 * something: a pointed question the objective requires is asked, with its
 * justification. The audience/artifact fields exist so every ask is
 * phrased for the person who will read it.
 *
 * Invariants (checks, not memories): every gap id appears in the register
 * exactly once (asked or unasked) · answered-but-unsettled is a visible
 * debt · only `accepted` is bindable by a deliverable · mark-sent sweeps
 * accepted only. Lifecycle transitions are compiler-checked via AskStatus.
 */
import type { Ask, AskId, AskStatus, SrcId, CalloutAddr } from "./types.ts";

/** mint a client-voiced ask referencing the gaps it would close */
export function propose(root: string, text: string, gaps: CalloutAddr[], audience: string, artifact: string): AskId { throw new Error("mock-out"); }
/** the human gate's yes, recorded */
export function accept(root: string, id: AskId): void { throw new Error("mock-out"); }
/** record every accepted ask as sent (the render verb's sibling) */
export function markSent(root: string): number { throw new Error("mock-out"); }
/** a response came back: record answered + stamp the ledger, one verb */
export function match(root: string, src: SrcId, ids: AskId[]): Ask[] { throw new Error("mock-out"); }
/** the answer is folded into capture; the loop for this ask closes */
export function settle(root: string, id: AskId): void { throw new Error("mock-out"); }
/** withdraw with a durable reason */
export function retire(root: string, id: AskId, reason: string): void { throw new Error("mock-out"); }
/** this gap is deliberately not the client's to answer */
export function unask(root: string, gap: CalloutAddr, reason: string): void { throw new Error("mock-out"); }
export function entriesOf(root: string, status?: AskStatus): Ask[] { throw new Error("mock-out"); }
/** answered-but-unsettled — the librarian's follow-up debt */
export function unsettled(root: string): Ask[] { throw new Error("mock-out"); }
