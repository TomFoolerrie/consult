/**
 * render — any pinned definition to a client-ready document.
 *
 *  A12: renders land in _synthesis/ — the consultant may register one as a
 * synthesis source (declared grounds, standing never upgraded) and work
 * from it.
 *
 * Owns/writes: _synthesis/. ONE self-contained verb (R1/R4): compile the
 * plan, run the pure view builders in-memory (views.build — an unbuildable
 * view is a named refusal, never a stub), then emit the document wearing
 * the definition's own shell — its title, its skin's
 * furniture, never another deliverable's. Demand-driven: nothing schedules
 * a render; a render of the information request is immediately followed by
 * asks.sent. One honest mode with draft watermarking.
 *
 * THE PYTHON SEAM (language ruling, 2026-08-26): docx emission is the one
 * place Python remains — a bounded subprocess (py/render_worker) owning
 * Word XML and nothing else. The contract is a versioned JSON job on
 * stdin (the compiled plan: ordered sections, resolved bodies, skin
 * capabilities, title) and a result on stdout (path, stats, warnings).
 * All content decisions — what the sections say, what was refused — are
 * made HERE, in TypeScript, before the job is emitted; the worker formats,
 * it never thinks. A missing or broken worker is a named refusal at the
 * render verb only; nothing else in the system touches Python.
 */
// A18 (M5): render absorbs the view-builder registry — three modules for
// the output half of one motion became two (definitions = the language,
// render = the seam). BUILDERS stays a PUBLIC export: joining it is what
// keeps "adding a deliverable is a YAML-sized act" honest. Views are
// never files (R1): builders run in-memory at render time; a plan naming
// an unregistered kind is refused BY NAME before any render. Ships with
// the three the two shipped definitions need: client-asks,
// information-requests, findings-by-theme.
import * as asksMod from "./asks.ts";
import * as findingsMod from "./findings.ts";
import * as kernel from "./kernel.ts";

export type ViewBuilder = (ctx: { root: string; binding: unknown }) => string;
const registry = new Map<string, ViewBuilder>();
registry.set("client-asks", ({ root }) =>
  asksMod.entriesOf(root, "accepted").concat(asksMod.entriesOf(root, "sent")).map(a => `- ${a.id}: ${a.text}`).join("\n"));
registry.set("information-requests", ({ root }) =>
  asksMod.entriesOf(root, "accepted").map(a => `- ${a.text}${a.artifact ? ` (please send: ${a.artifact})` : ""}`).join("\n"));
registry.set("findings-by-theme", ({ root }) => {
  const byTheme = new Map<string, string[]>();
  for (const f of findingsMod.renderable(root)) {
    const t = f.theme ?? "general";
    byTheme.set(t, [...(byTheme.get(t) ?? []), `- ${f.claim} [${f.grounds.join(", ")}]`]);
  }
  return [...byTheme.entries()].map(([t, ls]) => `### ${t}\n${ls.join("\n")}`).join("\n\n");
});
registry.set("open-questions", ({ root }) =>
  kernel.entities(root).flatMap(e => kernel.openQuestions(e).map(q => `- ${q.addr}: ${q.text}`)).join("\n"));
export const BUILDERS: ReadonlyMap<string, ViewBuilder> = registry;
/** build every view a compiled plan names, in plan order; refuse unregistered kinds by name */
export function build(root: string, plan: { views: readonly { id: string; builder: string }[] }): Map<string, string> {
  const out = new Map<string, string>();
  for (const v of plan.views) {
    const b = BUILDERS.get(v.builder);
    if (!b) throw new Error(`render: view ${v.id} names unregistered builder ${v.builder}`);
    out.set(v.id, b({ root, binding: v.builder }));
  }
  return out;
}

export interface RenderResult { path: string; sections: number; warnings: string[]; }

/** render one pinned definition end to end; an unbuildable view is a named refusal */
export async function deliverable(root: string, name: string, opts?: { out?: string; draft?: boolean }): Promise<RenderResult> {
  const { load, compilePlan, serviceability } = await import("./definitions.ts");
  const defn = load(name, root);
  const gaps = serviceability(defn, root);
  if (gaps.length) throw new Error(`render ${name}: not serviceable — ${gaps.map(g => `${g.binding}: ${g.missing}`).join("; ")}`);
  const plan = compilePlan(defn, root);
  build(root, plan); // an unbuildable view refuses by name here
  throw new Error(`render ${name}: the docx seam (py/render_worker) is not yet built — Phase 2`);
}
