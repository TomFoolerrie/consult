/**
 * harness/client — the scripted client for a synthetic engagement.
 *
 * NOT engine. Plays the other side of the boundary: reads the ask register,
 * and for every ask that has crossed (status: sent) delivers the scripted
 * response into <root>/_sources/new/ — exactly what a real client would do
 * (send a file). It never runs a verb: relaying the file to the consultant
 * ("this is the reply to ASK-002") is the HUMAN's part, and `ask respond`
 * is the consultant's. Idempotent: a response already delivered (in new/,
 * processed/, or the ledger) is not delivered twice.
 *
 * script.yaml:
 *   responses:
 *     - topic: reporting-line
 *       match: [reporting line, report to]     # any substring of the ask text (case-insensitive)
 *       file: responses/reorg-confirmation.md  # relative to the script
 *       behavior: answer | non-answer | silence
 * Usage: node --experimental-strip-types harness/client.ts <root> <script.yaml>
 */
import { parse } from "yaml";
import { readFileSync, existsSync, copyFileSync, mkdirSync, appendFileSync } from "node:fs";
import { join, dirname, basename, resolve } from "node:path";
import { fileURLToPath } from "node:url";

export interface ScriptEntry { topic: string; match: string[]; file?: string; behavior: "answer" | "non-answer" | "silence"; }
export interface Delivery { ask: string; topic: string; behavior: ScriptEntry["behavior"]; file?: string; }

export function loadScript(path: string): ScriptEntry[] {
  const raw = parse(readFileSync(path, "utf8")) as { responses?: ScriptEntry[] };
  // YAML may parse a match term as a number or date ("1,000", "2025-01-01"); every term is a string here
  return (raw?.responses ?? []).map(e => ({ ...e, match: (e.match ?? [e.topic]).map(m => String(m)) }));
}
/** which sent asks the script answers, and how — pure */
export function plan(asks: { id: string; status: string; text: string }[], script: ScriptEntry[]): Delivery[] {
  const out: Delivery[] = [];
  for (const a of asks) {
    if (a.status !== "sent") continue;
    const hit = script.find(e => e.match.some(m => a.text.toLowerCase().includes(m.toLowerCase())));
    if (!hit) continue;
    const d: Delivery = { ask: a.id, topic: hit.topic, behavior: hit.behavior };
    if (hit.file) d.file = hit.file;
    out.push(d);
  }
  return out;
}
function alreadyDelivered(root: string, name: string): boolean {
  if (existsSync(join(root, "_sources/new", name)) || existsSync(join(root, "_sources/processed", name))) return true;
  const ledger = join(root, "_sources/sources.yaml");
  return existsSync(ledger) && readFileSync(ledger, "utf8").includes(name);
}
/** deliver: copy the scripted files into _sources/new/; log to .harness/inbox.log; return what was delivered */
export function deliver(root: string, scriptPath: string): Delivery[] {
  const regPath = join(root, "_registers/asks.yaml");
  const asks = existsSync(regPath) ? ((parse(readFileSync(regPath, "utf8"))?.asks ?? []) as { id: string; status: string; text: string }[]) : [];
  const script = loadScript(scriptPath);
  const delivered: Delivery[] = [];
  mkdirSync(join(root, "_sources/new"), { recursive: true });
  mkdirSync(join(root, ".harness"), { recursive: true });
  for (const d of plan(asks, script)) {
    if (d.behavior === "silence" || !d.file) continue;
    const src = resolve(dirname(scriptPath), d.file);
    const name = basename(d.file);
    if (alreadyDelivered(root, name)) continue;
    copyFileSync(src, join(root, "_sources/new", name));
    appendFileSync(join(root, ".harness/inbox.log"), `${new Date().toISOString()} ${d.ask} ${d.behavior} ${name}\n`);
    delivered.push(d);
  }
  return delivered;
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [root, script] = [process.argv[2], process.argv[3]];
  if (!root || !script) { console.error("usage: client.ts <root> <script.yaml>"); process.exit(2); }
  const got = deliver(resolve(root), resolve(script));
  if (!got.length) console.log("client: nothing to deliver (no sent asks the script answers, or already delivered)");
  for (const d of got) console.log(`client: ${d.ask} — ${d.behavior}: ${basename(d.file!)} → _sources/new/   (relay to the consultant: "this answers ${d.ask}")`);
}
