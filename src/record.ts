/**
 * record — the machinery's hand. (A18 split, M3/M4.)
 *
 * Owns/writes: git (checkpoint) and _registers/sessions/ — the
 * append-only session record every verb and dispatch appends itself to
 * (closing the oracle's named evidence gap of audits living only in
 * transcripts), the budget line included (A14/A15).
 *
 * gate() is law 6 made auditable (A18, M4): the human's yes and the
 * crossing, recorded — for BOTH gates. asks.accept/sent are its
 * ask-shaped callers; a render leaving the building is gated the same
 * way; a spend over budget records its ruling here. Two gates on the
 * cycle, both now in the record.
 *
 * checkpoint() commits the WHOLE engagement (no curated pathspec) and
 * appends the session record; fully-cited sources retire to processed/
 * here (A18 — consumption is computed, retirement is its side effect).
 *
 * budget is the D9 mechanism: spends are proposed with an estimate
 * (priced with token asymmetry in mind — review-with-edits over
 * regeneration where it wins), auto-proceed under the sitting budget,
 * wait above it or for anything client-facing. spend() records estimate
 * and actual so pricing stays auditable.
 */
import { execSync } from "node:child_process";
import { readFileSync, writeFileSync, existsSync, readdirSync, renameSync, appendFileSync, mkdirSync } from "node:fs";
import { join, basename } from "node:path";
import * as ledger from "./ledger.ts";

const SESSIONS = (root: string) => join(root, "_registers", "sessions");
function sessionFile(root: string): string {
  return join(SESSIONS(root), `${new Date().toISOString().slice(0, 10)}.log`);
}
function readSessions(root: string): string {
  const dir = SESSIONS(root);
  if (!existsSync(dir)) return "";
  return readdirSync(dir).sort().map(f => readFileSync(join(dir, f), "utf8")).join("\n");
}

export interface SessionEvent { at: string; verb: string; detail: string; costEstimate?: number; costActual?: number; }
export interface Budget { limit: number; spent: number; remaining: number; }

/** commit the whole engagement as consult: <label>; append the session record; retire fully-cited sources */
export function checkpoint(root: string, label: string, dryRun?: boolean): { committed: string[]; retired: string[] } {
  // retirement first: fully-cited sources move to processed/ (consumption's one side effect, A18)
  const st = ledger.status(root);
  const retired: string[] = [];
  const book = ledger.readBook(root);
  for (const e of book.entries) {
    const out = st.outstanding.get(e.id as never) ?? [];
    const inNew = e.file.startsWith("_sources/new/");
    if (inNew && e.intent.length > 0 && out.length === 0) {
      const from = join(root, e.file), to = join(root, "_sources/processed", basename(e.file));
      mkdirSync(join(root, "_sources/processed"), { recursive: true });
      renameSync(from, to);
      e.file = join("_sources/processed", basename(e.file));
      retired.push(e.id);
    }
  }
  ledger.writeBook(root, book);
  sessionAppend(root, { at: new Date().toISOString(), verb: "checkpoint", detail: label });
  if (dryRun) return { committed: [], retired };
  execSync("git add -A", { cwd: root });
  const staged = execSync("git diff --cached --name-only", { cwd: root }).toString().trim();
  const committed = staged ? staged.split("\n") : [];
  if (committed.length) execSync(`git commit -qm ${JSON.stringify("consult: " + label)}`, { cwd: root });
  return { committed, retired };
}
/** every verb and dispatch appends itself to the sitting's session record */
export function sessionAppend(root: string, event: SessionEvent): void {
  mkdirSync(SESSIONS(root), { recursive: true });
  const line = JSON.stringify(event);
  appendFileSync(sessionFile(root), line + "\n");
}
/** the human's yes and the crossing, in the session record — law 6, auditable (A18) */
export function gate(root: string, g: { kind: "send" | "spend"; what: string; ruling: string }): void {
  sessionAppend(root, { at: new Date().toISOString(), verb: "gate", detail: `${g.kind}: ${g.what} — ${g.ruling}` });
}
/** appends the budget line to the session record — the budget's one home (A14); remaining is derived */
export function budgetSet(root: string, tokens: number): void {
  sessionAppend(root, { at: new Date().toISOString(), verb: "budget", detail: String(tokens) });
}
export function budget(root: string): Budget {
  const lines = readSessions(root).split("\n").filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  let limit = 0, spent = 0;
  for (const e of lines) {
    if (e.verb === "budget") { limit = Number(e.detail); spent = 0; }
    else if (e.verb === "spend" && typeof e.costActual === "number") spent += e.costActual;
  }
  return { limit, spent, remaining: limit - spent };
}
/** record one spend's estimate and actual in the session record */
export function spend(root: string, estimate: number, actual: number, what: string): void {
  const b = budget(root);
  if (estimate > b.remaining) {
    // over the sitting budget: requires an unconsumed spend-gate ruling (D9)
    const lines = readSessions(root).split("\n").filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
    const gates = lines.filter(e => e.verb === "gate" && String(e.detail).startsWith("spend:")).length;
    const overs = lines.filter(e => e.verb === "spend" && e.overBudget === true).length;
    if (gates <= overs) throw new Error(`spend: ${what} (${estimate}) exceeds the sitting budget remaining (${b.remaining}) — record a spend gate ruling first`);
    appendFileSync(sessionFile(root), JSON.stringify({ at: new Date().toISOString(), verb: "spend", detail: what, costEstimate: estimate, costActual: actual, overBudget: true }) + "\n");
    return;
  }
  sessionAppend(root, { at: new Date().toISOString(), verb: "spend", detail: what, costEstimate: estimate, costActual: actual });
}
