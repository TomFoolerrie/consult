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
/** every parsed session line, oldest first — the clock's source (A19 resolved into state) */
export function sessionLines(root: string): SessionEvent[] {
  return readSessions(root).split("\n").filter(Boolean).map(l => { try { return JSON.parse(l) as SessionEvent; } catch { return null; } }).filter((x): x is SessionEvent => !!x);
}
function readSessions(root: string): string {
  const dir = SESSIONS(root);
  if (!existsSync(dir)) return "";
  return readdirSync(dir).sort().map(f => readFileSync(join(dir, f), "utf8")).join("\n");
}

export interface SessionEvent { at: string; verb: string; detail: string; costEstimate?: number; costActual?: number; overBudget?: boolean; gateAt?: string; gate?: { kind: "send" | "spend"; what: string; ruling: string }; }
export interface Budget { limit: number; spent: number; remaining: number; }

/** commit the whole engagement as consult: <label>; append the session record; retire fully-cited sources */
export function checkpoint(root: string, label: string, dryRun?: boolean): { committed: string[]; retired: string[] } {
  // retirement first: fully-cited sources move to processed/ (consumption's one side effect, A18)
  // git first (review): a root that is not its own repository is refused by name before any mutation
  let top = "";
  try { top = execSync("git rev-parse --show-toplevel", { cwd: root, stdio: ["ignore", "pipe", "ignore"] }).toString().trim(); } catch { /* not a repo */ }
  if (!dryRun && top !== root) throw new Error(top ? `checkpoint: ${root} is inside the repository ${top} — an engagement is its own repository` : `checkpoint: ${root} is not a git repository — run git init in the engagement root`);
  const st = ledger.status(root);
  const retired: string[] = [];
  const candidates = st.entries.filter(e => e.file.startsWith("_sources/new/") && e.intent.length > 0 && (st.outstanding.get(e.id) ?? []).length === 0);
  for (const e of candidates) {
    const to = join(root, "_sources/processed", basename(e.file));
    if (existsSync(to)) throw new Error(`checkpoint: cannot retire ${e.id} — _sources/processed/${basename(e.file)} already exists; retirement never overwrites`);
    if (!existsSync(join(root, e.file))) throw new Error(`checkpoint: cannot retire ${e.id} — ${e.file} is missing from disk`);
  }
  if (dryRun) return { committed: [], retired: candidates.map(e => e.id) };
  for (const e of candidates) { ledger.retire(root, e.id); retired.push(e.id); }
  sessionAppend(root, { at: new Date().toISOString(), verb: "checkpoint", detail: label });
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
  if (g.kind !== "send" && g.kind !== "spend") throw new Error(`gate: kind "${String(g.kind)}" is not send | spend — two gates only (law 6)`);
  if (!g.what.trim()) throw new Error("gate: what is required — a gate names what it rules on");
  sessionAppend(root, { at: new Date().toISOString(), verb: "gate", detail: `${g.kind}: ${g.what} — ${g.ruling}`, gate: { kind: g.kind, what: g.what, ruling: g.ruling } });
}
/** a ruling counts as a YES only if it says so — "no", "denied", or silence never unlock anything (review B2) */
export function isYes(ruling: string): boolean {
  const r = ruling.trim().toLowerCase();
  if (/\b(no|not|denied|refused|reject|hold)\b/.test(r)) return false;
  return /^(yes|y|ok|okay|approved|accepted|accept|approve|go|proceed|agreed|sent)\b/.test(r) || /\b(approved|accepted|yes)\b/.test(r);
}
/** appends the budget line to the session record — the budget's one home (A14); remaining is derived */
export function budgetSet(root: string, tokens: number): void {
  if (!Number.isFinite(tokens) || tokens < 0) throw new Error(`budget set: "${String(tokens)}" is not a finite, non-negative token count`);
  // the budget is itself a spend-shaped ruling (review B2): it lands as a gate line so the audit shows who set the ceiling
  sessionAppend(root, { at: new Date().toISOString(), verb: "gate", detail: `spend: budget set to ${tokens} — the human's sitting budget`, gate: { kind: "spend", what: `budget ${tokens}`, ruling: "set" } });
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
  if (!what.trim()) throw new Error("spend: a label is required — a spend names what it paid for");
  for (const [k, v] of [["estimate", estimate], ["actual", actual]] as const)
    if (!Number.isFinite(v) || v < 0) throw new Error(`spend: ${what} — ${k} "${String(v)}" is not a finite, non-negative number`);
  const b = budget(root);
  if (estimate > b.remaining) {
    // over the sitting budget (D9): requires an UNCONSUMED spend-gate line that NAMES this spend and says yes (review B2)
    const lines = sessionLines(root);
    const consumed = new Set(lines.filter(e => e.verb === "spend" && e.gateAt).map(e => e.gateAt));
    const g = lines.find(e => e.verb === "gate" && e.gate?.kind === "spend" && e.gate.what === what && isYes(e.gate.ruling) && !consumed.has(e.at));
    if (!g) throw new Error(`spend: ${what} (${estimate}) exceeds the sitting budget remaining (${b.remaining}) — needs an unconsumed spend gate that names "${what}" with a yes`);
    sessionAppend(root, { at: new Date().toISOString(), verb: "spend", detail: what, costEstimate: estimate, costActual: actual, overBudget: true, gateAt: g.at });
    return;
  }
  sessionAppend(root, { at: new Date().toISOString(), verb: "spend", detail: what, costEstimate: estimate, costActual: actual });
}
