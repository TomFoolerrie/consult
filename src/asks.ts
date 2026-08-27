/**
 * asks — the client-engagement register. FIRST CLASS.
 *
 * Owns/writes: _registers/asks.yaml (one dump, the module's only write).
 * The brain generates client engagement throughout the engagement; this
 * register holds every curated request from proposal to settlement.
 *
 * ONE EVENT, ONE VERB — the event is ARRIVAL (A9, corrected A13): a
 * client response arriving is one motion — respond() routes the file
 * through the ledger's one door and stamps the asks it answers. It does
 * NOT settle: settle means "folded into capture", which is work that
 * happens after arrival; settle() is the post-fold-in verb, and the
 * answered-but-unsettled debt stays visible in between. retire/unask
 * merged into close(reason).
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
 * Invariants (checks, not memories): every question id appears in the
 * register exactly once (asked or closed) · answered-but-unsettled is a
 * visible debt · only `accepted` is bindable by a deliverable · sent()
 * sweeps accepted only. Lifecycle transitions compiler-checked via AskStatus.
 */
import type { Ask, AskId, AskStatus, SrcId, CalloutAddr } from "./types.ts";

/** mint a client-voiced ask referencing the question records it would close; audience/artifact optional (A13 — the ask economy is guidance, not schema) */
export function propose(root: string, text: string, questions: CalloutAddr[], audience?: string, artifact?: string): AskId { throw new Error("mock-out"); }
/** the human gate's yes, recorded */
export function accept(root: string, id: AskId): void { throw new Error("mock-out"); }
/** record accepted asks as sent — all of them by default, or just ids (A13) */
export function sent(root: string, ids?: AskId[]): number { throw new Error("mock-out"); }
/** the arrival verb: route the file through the one door + stamp answered asks (A13: arrival, not completion — settle comes after fold-in) */
export function respond(root: string, file: string, ids: AskId[]): { src: SrcId; answered: Ask[] } { throw new Error("mock-out"); }
/** the answer is folded into capture; the loop for this ask closes */
export function settle(root: string, id: AskId): void { throw new Error("mock-out"); }
/** withdraw an ask, or mark a question deliberately not the client's to answer — one close, durable reason */
export function close(root: string, target: AskId | CalloutAddr, reason: string): void { throw new Error("mock-out"); }
export function entriesOf(root: string, status?: AskStatus): Ask[] { throw new Error("mock-out"); }
/** answered-but-unsettled — the consultant's follow-up debt */
export function unsettled(root: string): Ask[] { throw new Error("mock-out"); }
