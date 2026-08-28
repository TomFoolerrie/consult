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
import { parse, stringify } from "yaml";
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import * as ledger from "./ledger.ts";
import * as record from "./record.ts";
import * as kernel from "./kernel.ts";
import type { Ask, AskId, AskStatus, SrcId, CalloutAddr } from "./types.ts";

const REG = (root: string) => join(root, "_registers", "asks.yaml");
interface MutableAsk { id: AskId; status: AskStatus; text: string; questions: CalloutAddr[]; audience?: string; artifact?: string; answeredBy: SrcId[]; closedReason?: string; }
interface Reg { asks: MutableAsk[]; closedQuestions: { question: CalloutAddr; reason: string }[]; }
function readReg(root: string): Reg {
  if (!existsSync(REG(root))) return { asks: [], closedQuestions: [] };
  const r = parse(readFileSync(REG(root), "utf8"));
  if (Array.isArray(r)) return { asks: r as MutableAsk[], closedQuestions: [] }; // tolerate a hand-written bare list
  return { asks: r?.asks ?? [], closedQuestions: r?.closedQuestions ?? [] };
}
function writeReg(root: string, r: Reg): void { writeFileSync(REG(root), stringify(r)); }
function must(r: Reg, id: AskId): MutableAsk {
  const a = r.asks.find(a => a.id === id);
  if (!a) throw new Error(`ask: no such ask ${id}`);
  return a;
}
/** settled ⇔ for every question addr: a statement in that fragment cites an answeredBy source, OR the question record is gone (A18) */
function settledIn(root: string, a: MutableAsk, ents: ReturnType<typeof kernel.entities>): boolean {
  if (a.answeredBy.length === 0) return false;
  return a.questions.every(q => {
    const [slug, qid] = q.split("#") as [string, string];
    const e = ents.find(e => e.slug === slug);
    if (!e) return false;
    const questionGone = !e.callouts.some(c => c.id === qid);
    const cited = e.statements.some(st => st.cites.some(c => a.answeredBy.includes(c as SrcId)));
    return cited || questionGone;
  });
}

/** mint a client-voiced ask referencing the question records it would close; audience/artifact optional (A13) */
export function propose(root: string, text: string, questions: CalloutAddr[], audience?: string, artifact?: string): AskId {
  const r = readReg(root);
  for (const q of questions) {
    if (r.asks.some(a => a.questions.includes(q)) || r.closedQuestions.some(c => c.question === q))
      throw new Error(`ask propose: question ${q.split("#")[1]} (${q}) is already in the register — exactly once, asked or closed`);
  }
  const id = `ASK-${String(r.asks.length + 1).padStart(3, "0")}` as AskId;
  const a: MutableAsk = { id, status: "proposed", text, questions: [...questions], answeredBy: [] };
  if (audience !== undefined) a.audience = audience;
  if (artifact !== undefined) a.artifact = artifact;
  r.asks.push(a);
  writeReg(root, r);
  return id;
}
/** the human gate's yes — recorded through record.gate (A18) */
export function accept(root: string, id: AskId): void {
  const r = readReg(root); const a = must(r, id);
  if (a.status !== "proposed") throw new Error(`ask accept: ${id} is ${a.status}, not proposed`);
  a.status = "accepted"; writeReg(root, r);
  record.gate(root, { kind: "send", what: `ask ${id}: ${a.text}`, ruling: "accepted" });
}
/** record accepted asks as sent — all by default, or just ids; a send-gate crossing (A18) */
export function sent(root: string, ids?: AskId[]): number {
  const r = readReg(root);
  const targets = r.asks.filter(a => a.status === "accepted" && (!ids || ids.includes(a.id)));
  for (const a of targets) {
    a.status = "sent";
    record.gate(root, { kind: "send", what: `ask ${a.id} crossed to the client`, ruling: "sent" });
  }
  writeReg(root, r);
  return targets.length;
}
/** the arrival verb: route the file through the one door + stamp answeredBy */
export function respond(root: string, file: string, ids: AskId[]): { src: SrcId; answered: Ask[] } {
  const r = readReg(root);
  const answeredAsks = ids.map(id => must(r, id));
  const intent = [...new Set(answeredAsks.flatMap(a => a.questions.map(q => q.split("#")[0]!)))];
  const src = ledger.route(root, file, intent, { provenance: "client" });
  for (const a of answeredAsks) { if (!a.answeredBy.includes(src)) a.answeredBy.push(src); ledger.stampAnswer(root, src, a.id); }
  writeReg(root, r);
  return { src, answered: answeredAsks.map(a => ({ ...a, questions: [...a.questions], answeredBy: [...a.answeredBy] })) as unknown as Ask[] };
}
/** withdraw an ask, or mark a question deliberately not the client's to answer — one close, durable reason */
export function close(root: string, target: AskId | CalloutAddr, reason: string): void {
  const r = readReg(root);
  const a = r.asks.find(a => a.id === target);
  if (a) { a.status = "closed"; a.closedReason = reason; }
  else if (target.includes("#")) r.closedQuestions.push({ question: target as CalloutAddr, reason });
  else throw new Error(`ask close: no such ask or question ${target}`);
  writeReg(root, r);
}
export function entriesOf(root: string, status?: AskStatus): Ask[] {
  const r = readReg(root);
  return r.asks.filter(a => !status || a.status === status) as unknown as Ask[];
}
/** PURE (A18): answered (answeredBy stamped) but not yet settled (answering sources not yet cited where the questions live) */
export function unsettled(root: string): Ask[] {
  const r = readReg(root);
  const ents = kernel.entities(root);
  return r.asks.filter(a => a.answeredBy.length > 0 && a.status !== "closed" && !settledIn(root, a, ents)) as unknown as Ask[];
}
