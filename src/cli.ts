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
 *   state · coverage · needs                            → desk (PURE — the one derived picture)
 *   checkpoint · budget · spend · gate                  → record (the machinery's hand)
 *   route · park                                        → ledger (one intake door; consumption COMPUTED)
 *   ask propose|accept|sent|respond|close               → asks (answered/settled DERIVED)
 *   finding propose|accept|reject                       → findings
 *   check                                               → check (six mechanical checks)
 *   render <deliverable>   (self-contained: compile → build views in-memory → emit)
 *   answer "<question>"                                 → answers.ground
 *   brief <skill> …                                     → brief.compose
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
import type { CalloutAddr, AskId, FindingId } from "./types.ts";

function opt(args: string[], name: string): string | undefined {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : undefined;
}
const READS = new Set(["state", "coverage", "needs", "answer", "check", "budget"]);

export async function main(argv: string[]): Promise<number> {
  try {
    const [verb, ...rest] = argv;
    if (!verb) { console.error("consult <verb> — see DESIGN.md"); return 2; }
    const root = opt(rest, "root") ?? process.cwd();
    const { root: located, health } = desk.locate(root);
    if (health.kind === "contradiction") {
      const noEngagement = health.what.startsWith("no engagement here");
      if (noEngagement) { console.error(`refused: ${health.what}`); return 2; }
      const stateChanging = !READS.has(verb);
      if (stateChanging && verb !== health.repair) {
        console.error(`refused: ${health.what} — repair verb: ${health.repair}`);
        return 2;
      }
    }
    switch (verb) {
      case "state": console.log(desk.report(located)); return 0;
      case "coverage": console.log(JSON.stringify(desk.coverage(located))); return 0;
      case "needs": console.log(JSON.stringify(desk.needs(located, rest[0]?.startsWith("--") ? undefined : rest[0]))); return 0;
      case "route": {
        const file = rest[0]!;
        ledger.route(located, file, (opt(rest, "intent") ?? "").split(",").filter(Boolean),
          opt(rest, "provenance") ? { provenance: opt(rest, "provenance") as never,
            grounds: (opt(rest, "grounds") ?? "").split(",").filter(Boolean) } : undefined);
        return 0;
      }
      case "park": ledger.park(located, rest[0]!, opt(rest, "reason") ?? ""); return 0;
      case "ask": {
        const sub = rest[0];
        if (sub === "propose") {
          const qs = (opt(rest, "questions") ?? "").split(",").filter(Boolean) as CalloutAddr[];
          if (!qs.length) { console.error("refused: ask propose needs --questions"); return 2; }
          console.log(asks.propose(located, rest[1] ?? "", qs, opt(rest, "audience"), opt(rest, "artifact"))); return 0;
        }
        if (sub === "accept") { asks.accept(located, rest[1] as AskId); return 0; }
        if (sub === "sent") { console.log(asks.sent(located, rest.slice(1).filter(a => !a.startsWith("--")) as AskId[])); return 0; }
        if (sub === "respond") { console.log(JSON.stringify(asks.respond(located, rest[1]!, (opt(rest, "asks") ?? "").split(",").filter(Boolean) as AskId[]))); return 0; }
        if (sub === "close") { asks.close(located, rest[1] as AskId, opt(rest, "reason") ?? ""); return 0; }
        console.error(`refused: unknown ask verb ${sub}`); return 2;
      }
      case "finding": {
        const sub = rest[0];
        if (sub === "propose") { console.log(findings.propose(located, rest[1] ?? "", (opt(rest, "grounds") ?? "").split(",").filter(Boolean) as import("./types.ts").Ground[], opt(rest, "theme"))); return 0; }
        if (sub === "accept") { findings.accept(located, rest[1] as FindingId); return 0; }
        if (sub === "reject") { findings.reject(located, rest[1] as FindingId, opt(rest, "reason") ?? ""); return 0; }
        console.error(`refused: unknown finding verb ${sub}`); return 2;
      }
      case "check": {
        const defects = check.run(located);
        for (const d of defects) console.log(`${d.severity}: ${d.check} ${d.file}${d.line ? ":" + d.line : ""} — ${d.message}`);
        return defects.some(d => d.severity === "error") ? 2 : 0;
      }
      case "answer": console.log(JSON.stringify(answers.ground(located, rest[0] ?? ""))); return 0;
      case "checkpoint": console.log(JSON.stringify(record.checkpoint(located, rest[0] ?? "checkpoint"))); return 0;
      case "budget": {
        if (rest[0] === "set") { record.budgetSet(located, Number(rest[1])); return 0; }
        console.log(JSON.stringify(record.budget(located))); return 0;
      }
      case "spend": record.spend(located, Number(opt(rest, "estimate")), Number(opt(rest, "actual")), rest[0] ?? ""); return 0;
      case "gate": record.gate(located, { kind: opt(rest, "kind") as "send" | "spend", what: opt(rest, "what") ?? "", ruling: opt(rest, "ruling") ?? "" }); return 0;
      case "render": { const { deliverable } = await import("./render.ts"); await deliverable(located, rest[0]!); return 0; }
      case "brief": console.log(brief.compose(located, rest[0]!, (opt(rest, "class") ?? brief.skill(located, rest[0]!).recommendedClass) as never, {})); return 0;
      default: console.error(`refused: unknown verb ${verb}`); return 2;
    }
  } catch (e) {
    console.error(`refused: ${(e as Error).message}`);
    return 2;
  }
}
