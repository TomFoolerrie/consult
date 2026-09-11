/**
 * cli — `consult <verb>`, the one entry point.
 *
 * Owns: nothing on disk. LIBRARY FIRST (R5): every verb is a thin wrapper
 * over an exported module function — tests and the synthetic-engagement
 * harness drive the library in-process and assert on typed results
 * (Standing, Defect, Snapshot), never on parsed stdout. One command tree;
 * every verb in the system is a subcommand here; no module has its own
 * entry. Refuses any state-changing
 * verb while a contradiction from desk.state() stands — the contradiction's
 * own `repair` field NAMES the verb that may run (A14).
 *
 * Verb inventory after the A9 distillation (each dispatches to exactly
 * one module function; every verb guards an invariant or expands context):
 *   init                                                → cli (the ONE repair: lay _sources/ + the empty ledger, nothing else)
 *   state · coverage · needs                            → desk (PURE — the one derived picture)
 *   index [store] · card <ref>                          → index (PURE — progressive disclosure, A22)
 *   checkpoint · budget · spend · gate                  → record (the machinery's hand)
 *   route · park · scan                                 → ledger (one intake door; consumption COMPUTED; the durable scan, A20)
 *   ask propose|accept|sent|respond|close               → asks (answered/settled DERIVED)
 *   finding propose|accept|reject                       → findings
 *   check                                               → check (seven mechanical checks)
 *   render <deliverable> [--draft] [--out path]        → render (self-contained: compile → build views in-memory → emit via the py seam)
 *   source verify SRC-nnn                               → ledger.verifySource (byte integrity only)
 *   source excerpt SRC-nnn --lines START:END             → ledger.sourceExcerpt (verified UTF-8 lines)
 *   source table SRC-nnn                                → ledger.sourceTable (verified CSV snapshot)
 *   source record SRC-nnn --record N                     → ledger.sourceRecord (one CSV data record)
 *   answer "<question>"                                 → answers.ground
 *   brief <skill> …                                     → brief.compose
 *   return <file>                                       → returns.land (A27: the ONE door for what a skill produces — validates, mints proposals, records, hands over)
 * Gone: register (A9) · new (A9) · flag/tenure (A9) · feeds (A9) ·
 * credit and ask settle (A18 — consumption and settlement are computed
 * from capture citations, never declared).
 */
import * as desk from "./desk.ts";
import * as ledger from "./ledger.ts";
import * as asks from "./asks.ts";
import * as findings from "./findings.ts";
import * as check from "./check.ts";
import * as answers from "./answers.ts";
import * as record from "./record.ts";
import * as brief from "./brief.ts";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { CalloutAddr, AskId, FindingId } from "./types.ts";

function opt(args: string[], name: string): string | undefined {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : undefined;
}
const BOOLEAN_FLAGS = new Set(["draft"]);
/** the ONE positional rule (review C7): drop every `--flag value` pair and every bare `--flag` — an option's value is never an id */
export function positionals(args: string[]): string[] {
  const out: string[] = [];
  for (let i = 0; i < args.length; i++) {
    const a = args[i]!;
    if (!a.startsWith("--")) { out.push(a); continue; }
    const next = args[i + 1];
    if (!BOOLEAN_FLAGS.has(a.slice(2)) && next !== undefined && !next.startsWith("--")) i++;
  }
  return out;
}
/**
 * init — the ONE repair for an engagement-shaped tree without the _sources/ marker (review C6).
 * Creates _sources/{new,processed,parked,scans} and the empty ledger, and NOTHING else: no
 * pad, no objective, no git, no registers. On a healthy root it is a no-op that says so.
 */
export function init(root: string): string[] {
  const made: string[] = [];
  for (const d of ["_sources/new", "_sources/processed", "_sources/parked", "_sources/scans"]) {
    const p = join(root, d);
    if (!existsSync(p)) { mkdirSync(p, { recursive: true }); made.push(d); }
  }
  const book = join(root, "_sources", "sources.yaml");
  if (!existsSync(book)) { writeFileSync(book, "entries: []\nparked: []\n"); made.push("_sources/sources.yaml"); }
  return made;
}
const READS = new Set(["state", "coverage", "needs", "answer", "check", "index", "card", "brief", "source"]);  // `budget` (read) vs `budget set` (write) is decided below

export async function main(argv: string[]): Promise<number> {
  try {
    const [verb, ...rest] = argv;
    if (!verb) { console.error("consult <verb> — run `consult init` in an engagement folder"); return 2; }
    const root = opt(rest, "root") ?? process.cwd();
    const { root: located, health } = desk.locate(root);
    const pos = positionals(rest);
    if (health.kind === "contradiction") {
      const noEngagement = health.what.startsWith("no engagement here");
      if (noEngagement) { console.error(`refused: ${health.what}`); return 2; }
      const stateChanging = !READS.has(verb) && !(verb === "budget" && pos[0] !== "set");
      if (stateChanging && verb !== health.repair) {
        console.error(`refused: ${health.what} — repair verb: ${health.repair}`);
        return 2;
      }
    }
    switch (verb) {
      case "state": console.log(desk.report(located)); return 0;
      case "coverage": console.log(JSON.stringify(desk.coverage(located))); return 0;
      case "needs": console.log(JSON.stringify(desk.needs(located, pos[0]))); return 0;
      case "init": {
        const made = init(located);
        console.log(made.length ? made.join("\n") : "init: already an engagement root — nothing to do");
        return 0;
      }
      case "route": {
        const file = pos[0]!;
        ledger.route(located, file, (opt(rest, "intent") ?? "").split(",").filter(Boolean),
          opt(rest, "provenance") ? { provenance: opt(rest, "provenance") as never,
            grounds: (opt(rest, "grounds") ?? "").split(",").filter(Boolean) } : undefined);
        return 0;
      }
      case "park": ledger.park(located, pos[0]!, opt(rest, "reason") ?? ""); return 0;
      case "source": {
        const [sub, id] = pos;
        if (sub === "verify" && id && pos.length === 2) {
          console.log(JSON.stringify(ledger.verifySource(located, id))); return 0;
        }
        if (sub === "table" && id && pos.length === 2) {
          console.log(JSON.stringify(ledger.sourceTable(located, id))); return 0;
        }
        const record = opt(rest, "record");
        if (sub === "record" && id && pos.length === 2 && record && /^\d+$/.test(record)) {
          console.log(JSON.stringify(ledger.sourceRecord(located, id, Number(record)))); return 0;
        }
        const lines = opt(rest, "lines");
        if (sub === "excerpt" && id && pos.length === 2 && lines && /^\d+:\d+$/.test(lines)) {
          const [start, end] = lines.split(":").map(Number);
          console.log(JSON.stringify(ledger.sourceExcerpt(located, id, { start: start!, end: end! }))); return 0;
        }
        throw new Error("source: use source verify|table SRC-nnn, source excerpt SRC-nnn --lines START:END, or source record SRC-nnn --record N");
      }
      case "scan": console.log(ledger.scan(located, pos[0] as import("./types.ts").SrcId, pos[1])); return 0;
      case "index": { const { render } = await import("./index.ts"); console.log(render(located, pos[0] as never)); return 0; }
      case "card": { const { card } = await import("./index.ts"); console.log(JSON.stringify(card(located, pos[0]!))); return 0; }
      case "ask": {
        const sub = pos[0];
        if (sub === "propose") {
          const qs = (opt(rest, "questions") ?? "").split(",").filter(Boolean) as CalloutAddr[];
          if (!qs.length) { console.error("refused: ask propose needs --questions"); return 2; }
          console.log(asks.propose(located, pos[1] ?? "", qs, opt(rest, "audience"), opt(rest, "artifact"))); return 0;
        }
        if (sub === "accept") { asks.accept(located, pos[1] as AskId, opt(rest, "ruling")); return 0; }
        if (sub === "sent") { const ids = pos.slice(1) as AskId[]; console.log(asks.sent(located, ids.length ? ids : undefined)); return 0; }
        if (sub === "respond") { console.log(JSON.stringify(asks.respond(located, pos[1]!, (opt(rest, "asks") ?? "").split(",").filter(Boolean) as AskId[]))); return 0; }
        if (sub === "close") { asks.close(located, pos[1] as AskId, opt(rest, "reason") ?? ""); return 0; }
        console.error(`refused: unknown ask verb ${sub}`); return 2;
      }
      case "finding": {
        const sub = pos[0];
        if (sub === "propose") { console.log(findings.propose(located, pos[1] ?? "", (opt(rest, "grounds") ?? "").split(",").filter(Boolean) as import("./types.ts").Ground[], opt(rest, "theme"))); return 0; }
        if (sub === "accept") { findings.accept(located, pos[1] as FindingId); return 0; }
        if (sub === "reject") { findings.reject(located, pos[1] as FindingId, opt(rest, "reason") ?? ""); return 0; }
        console.error(`refused: unknown finding verb ${sub}`); return 2;
      }
      case "check": {
        const defects = check.run(located);
        for (const d of defects) console.log(`${d.severity}: ${d.check} ${d.file}${d.line ? ":" + d.line : ""} — ${d.message}`);
        return defects.some(d => d.severity === "error") ? 2 : 0;
      }
      case "answer": console.log(JSON.stringify(answers.ground(located, pos[0] ?? ""))); return 0;
      case "checkpoint": console.log(JSON.stringify(record.checkpoint(located, pos[0] ?? "checkpoint"))); return 0;
      case "spend": record.spend(located, Number(opt(rest, "estimate")), Number(opt(rest, "actual")), pos[0] ?? ""); return 0;
      case "gate": record.gate(located, { kind: opt(rest, "kind") as "send" | "spend", what: opt(rest, "what") ?? "", ruling: opt(rest, "ruling") ?? "" }); return 0;
      case "budget": {
        if (pos[0] === "set") { record.budgetSet(located, Number(pos[1]), opt(rest, "ruling")); return 0; }
        console.log(JSON.stringify(record.budget(located))); return 0;
      }
      case "render": {
        const { deliverable } = await import("./render.ts");
        const out = opt(rest, "out");
        console.log(JSON.stringify(await deliverable(located, pos[0]!, { draft: rest.includes("--draft"), ...(out ? { out } : {}) }))); return 0;
      }
      case "return": {
        const { land } = await import("./returns.ts");
        if (!pos[0]) { console.error("refused: return needs the path of the return YAML"); return 2; }
        console.log(JSON.stringify(land(located, pos[0]))); return 0;
      }
      case "pin": {
        const { pin } = await import("./definitions.ts");
        console.log(pin(located, pos[0]!)); return 0;
      }
      case "skill": {
        if (pos[0] !== "save") { console.error(`refused: unknown skill verb ${pos[0]}`); return 2; }
        if (!pos[1]) { console.error("refused: skill save needs the path of the skill YAML to save"); return 2; }
        if (!existsSync(pos[1])) { console.error(`refused: skill save: no such file ${pos[1]}`); return 2; }
        const { parse } = await import("yaml"); const { readFileSync } = await import("node:fs");
        const raw = parse(readFileSync(pos[1], "utf8"));
        brief.saveSkill(located, raw); console.log(raw?.name); return 0;
      }
      case "brief": {
        const params: Record<string, unknown> = {};
        const cards = opt(rest, "cards"); if (cards) params.cards = cards.split(",").filter(Boolean);
        // --param k=v, repeatable (review B9): the skill's parameters, from the CLI
        rest.forEach((a, i) => { if (a === "--param" && rest[i + 1]) { const [k, ...v] = rest[i + 1]!.split("="); if (k) params[k] = v.join("="); } });
        console.log(brief.compose(located, pos[0]!, (opt(rest, "class") ?? brief.skill(located, pos[0]!).recommendedClass) as never, params)); return 0;
      }
      default: console.error(`refused: unknown verb ${verb}`); return 2;
    }
  } catch (e) {
    console.error(`refused: ${(e as Error).message}`);
    return 2;
  }
}
