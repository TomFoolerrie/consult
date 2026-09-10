/**
 * render — any pinned definition to a client-ready document.
 *
 *  A12: renders land in _synthesis/ — the consultant may register one as a
 * synthesis source (declared grounds, standing never upgraded) and work
 * from it.
 *
 * Owns/writes: _synthesis/. ONE self-contained verb (R1/R4): compile the
 * plan, run the pure view builders in-memory (build — an unbuildable
 * view is a named refusal, never a stub), assemble the job, then emit
 * the document wearing the definition's own shell — its title, its
 * skin's furniture, never another deliverable's. Demand-driven: nothing
 * schedules a render; a render of the information request is followed
 * by asks.sent — and any render leaving the building crosses the send
 * gate by the CONSULTANT's hand (A18), never here. One honest mode with
 * draft watermarking. Every render lands its CARD beside the file (A22):
 * `<stem>.card.yaml`, path from ledger.sidecarPath — and a stem another
 * artifact in _synthesis/ already owns is a named refusal (review C8):
 * one card, one artifact; a render never overwrites another's card.
 *
 * THE PYTHON SEAM (language ruling, 2026-08-26; built A23): docx
 * emission is the one place Python remains — a bounded subprocess
 * (py/render_worker.py) owning Word XML and nothing else. The contract
 * is a versioned JSON job on stdin — RenderJob v1: { version, title,
 * draft, skin: { format, requires }, sections: [{ id, title, body }],
 * out } — and a result on stdout: { path, sections, warnings }. All
 * content decisions — what the sections say, in what order, what was
 * refused — are made HERE, in TypeScript, by assembleJob (pure) before
 * the job is emitted; the worker formats, it never thinks. Three named
 * refusals at the render verb only: python3 not available, the worker
 * script missing (its path named), the worker failing (its stderr's
 * first line). Nothing else in the system touches Python. The worker
 * path is overridable (opts.worker, or CONSULT_RENDER_WORKER) so a
 * missing worker can be exercised without uninstalling anything.
 */
// A18 (M5): render absorbs the view-builder registry — three modules for
// the output half of one motion became two (definitions = the language,
// render = the seam). BUILDERS stays a PUBLIC export: joining it is what
// keeps "adding a deliverable is a YAML-sized act" honest. Views are
// never files (R1): builders run in-memory at render time; a plan naming
// an unregistered kind is refused BY NAME before any render. Ships with
// four: client-asks, information-requests, findings-by-theme,
// open-questions (the two shipped definitions need three of them).
import * as asksMod from "./asks.ts";
import * as findingsMod from "./findings.ts";
import * as kernel from "./kernel.ts";
import * as ledger from "./ledger.ts";
import type { Definition, Plan } from "./definitions.ts";
import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join, dirname, relative, isAbsolute } from "node:path";
import { fileURLToPath } from "node:url";

const WORKER = join(dirname(fileURLToPath(import.meta.url)), "..", "py", "render_worker.py");

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
registry.set("open-questions", ({ root }) => {
  // client-facing (review B8): never a question closed as not-the-client's, never a withdrawn ask's question
  const closed = asksMod.closedAddresses(root);
  return kernel.entities(root).flatMap(e => kernel.openQuestions(e).filter(q => !closed.has(q.addr)).map(q => `- ${q.addr}: ${q.text}`)).join("\n");
});
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
/** the versioned job the worker formats — v1 */
export interface RenderJob {
  version: 1; title: string; draft: boolean;
  skin: { format: string; requires: readonly string[] };
  sections: { id: string; title: string; body: string }[];
  out?: string;
}
/** PURE: the compiled plan + built view bodies → the job, in BLOCK order (static blocks bring their text, views their built body) */
export function assembleJob(defn: Definition, plan: Plan, views: ReadonlyMap<string, string>, opts: { draft?: boolean | undefined }): RenderJob {
  const sections = plan.blocks.flatMap(b => {
    if (b.kind === "static") return [{ id: b.id, title: b.title, body: b.text }];
    if (b.kind === "view") return [{ id: b.id, title: b.title, body: views.get(b.id) ?? "" }];
    return []; // unreachable: compilePlan refuses entity-part blocks by name before any plan reaches here
  });
  return { version: 1, title: defn.title, draft: opts.draft === true, skin: { format: defn.skin.format, requires: [...defn.skin.requires] }, sections };
}

/** render one pinned definition end to end; an unbuildable view is a named refusal */
export async function deliverable(root: string, name: string, opts?: { out?: string; draft?: boolean; worker?: string }): Promise<RenderResult> {
  const { load, compilePlan, serviceability } = await import("./definitions.ts");
  const defn = load(name, root);
  const gaps = serviceability(defn, root);
  if (gaps.length) throw new Error(`render ${name}: not serviceable — ${gaps.map(g => `${g.binding}: ${g.missing}`).join("; ")}`);
  const plan = compilePlan(defn, root);
  const views = build(root, plan); // an unbuildable view refuses by name here
  const rel = opts?.out ?? join("_synthesis", `${name}.docx`);
  const out = isAbsolute(rel) ? rel : join(root, rel);
  const relOut = relative(root, out).split("\\").join("/");
  if (relOut.startsWith("..") || !relOut.startsWith("_synthesis/")) throw new Error(`render ${name}: --out ${rel} is outside _synthesis/ — a render lands only in the work-product store`);
  const job: RenderJob = { ...assembleJob(defn, plan, views, { draft: opts?.draft }), out };

  // A22: one card per artifact — refuse a sidecar stem another artifact owns, BEFORE anything is written (review C8)
  const { synthesisArtifacts } = await import("./index.ts");
  const sidecar = ledger.sidecarPath(out);
  const owner = synthesisArtifacts(root).find(f => join(root, f) !== out && ledger.sidecarPath(join(root, f)) === sidecar);
  if (owner) throw new Error(`render ${name}: ${relative(root, sidecar).split("\\").join("/")} is already ${owner}'s card — a sidecar stem belongs to one artifact`);

  const worker = opts?.worker ?? process.env.CONSULT_RENDER_WORKER ?? WORKER;
  if (!existsSync(worker)) throw new Error(`render ${name}: render_worker missing at ${worker} — the docx seam needs it`);
  mkdirSync(dirname(out), { recursive: true });
  const run = spawnSync("python3", [worker], { input: JSON.stringify(job), encoding: "utf8" });
  if (run.error && (run.error as NodeJS.ErrnoException).code === "ENOENT")
    throw new Error(`render ${name}: python3 not available — the docx seam needs it`);
  // the worker's own refusal (exit 2) rides on stdout as {error} — surface it by name, never "no output" (review C4)
  let refusal: string | undefined;
  if (run.status === 2 && run.stdout) { try { const j = JSON.parse(run.stdout) as { error?: unknown }; if (typeof j?.error === "string") refusal = j.error; } catch { /* not the refusal shape */ } }
  const firstErr = refusal ?? (run.stderr ?? "").split("\n").find(l => l.trim()) ?? (run.error?.message ?? "no output");
  let result: { path: string; sections: number; warnings?: string[] } | undefined;
  if (run.status === 0) { try { result = JSON.parse(run.stdout); } catch { /* unparseable — refused below */ } }
  if (!result || typeof result.path !== "string") throw new Error(`render ${name}: render_worker failed — ${firstErr}`);

  const card = { title: defn.title, kind: "deliverable", summary: `Rendered deliverable ${defn.name} (${job.sections.length} sections)`, keyItems: job.sections.map(s => s.title) };
  writeFileSync(sidecar, Object.entries(card).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join("\n") + "\n");
  return { path: relative(root, out).split("\\").join("/"), sections: result.sections, warnings: result.warnings ?? [] };
}
