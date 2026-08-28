/**
 * asks — the client-engagement register. FIRST CLASS.
 *
 * Owns/writes: _registers/asks.yaml (one dump, the module's only write).
 * The brain generates client engagement throughout the engagement.
 *
 * FOUR STORED STATES (A18) — only the events the folder cannot show:
 * proposed (the mint) | accepted (the gate's yes, via record.gate) |
 * sent (the boundary crossing) | closed (deliberate withdrawal).
 * `answered` and `settled` are COMPUTED: answered = answeredBy
 * non-empty (stamped by respond); settled = THE PREDICATE, pinned:
 * for EVERY question address the ask names, either a statement in that
 * question's fragment cites one of the answeredBy sources, or the
 * question record has been removed from the fragment (removal = the
 * consultant judged it answered; the register keeps the id, so
 * ask-coverage stays clean — the register, not the fragment, is where
 * "exactly once" lives). Settlement is un-fakeable — you cannot stamp what the capture does not show — and
 * the answered-but-unsettled debt stays visible through unsettled(),
 * now a pure read.
 *
 * ONE EVENT, ONE VERB — the event is ARRIVAL (A13): respond() routes
 * the file through the ledger's one door — with intent = the DISTINCT
 * SLUGS of the answered asks' question addresses — and stamps the asks
 * it answers (answeredBy ACCUMULATES across responses: one ask may be
 * answered by several). Fold-in is the consultant's direct capture work; its
 * completion is DERIVED, not declared (A18 — settle() does not exist).
 *
 * ASK ECONOMY — a GUIDING PRINCIPLE, not a rule: prefer few, simple,
 * artifact-shaped requests tailored to the relationship — but if the
 * objective needs something, it needs something.
 *
 * Invariants — enforced at BOTH layers, deliberately: propose() refuses
 * a question id already in the register (fast feedback), AND check's
 * ask-coverage polices the register after any direct hand-edit (the
 * A14 world's law). Only `accepted` is bindable by a deliverable ·
 * sent() sweeps accepted only · accept() and sent() are record.gate's
 * ask-shaped callers — each appends a kind:"send" gate line naming the
 * ask to the session record (A18/M4).
 */
import type { Ask, AskId, AskStatus, SrcId, CalloutAddr } from "./types.ts";

/** mint a client-voiced ask referencing the question records it would close; audience/artifact optional (A13) */
export function propose(root: string, text: string, questions: CalloutAddr[], audience?: string, artifact?: string): AskId { throw new Error("mock-out"); }
/** the human gate's yes — recorded through record.gate (A18) */
export function accept(root: string, id: AskId): void { throw new Error("mock-out"); }
/** record accepted asks as sent — all by default, or just ids; a send-gate crossing (A18) */
export function sent(root: string, ids?: AskId[]): number { throw new Error("mock-out"); }
/** the arrival verb: route the file through the one door + stamp answeredBy */
export function respond(root: string, file: string, ids: AskId[]): { src: SrcId; answered: Ask[] } { throw new Error("mock-out"); }
/** withdraw an ask, or mark a question deliberately not the client's to answer — one close, durable reason */
export function close(root: string, target: AskId | CalloutAddr, reason: string): void { throw new Error("mock-out"); }
export function entriesOf(root: string, status?: AskStatus): Ask[] { throw new Error("mock-out"); }
/** PURE (A18): answered (answeredBy stamped) but not yet settled (answering sources not yet cited where the questions live) */
export function unsettled(root: string): Ask[] { throw new Error("mock-out"); }
