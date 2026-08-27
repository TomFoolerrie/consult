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
export type ViewBuilder = (ctx: { root: string; binding: unknown }) => string;
export const BUILDERS: ReadonlyMap<string, ViewBuilder> = new Map();
/** build every view a compiled plan names, in plan order; refuse unregistered kinds by name */
export function build(root: string, plan: { views: readonly { id: string; builder: string }[] }): Map<string, string> { throw new Error("mock-out"); }

export interface RenderResult { path: string; sections: number; warnings: string[]; }

/** render one pinned definition end to end; an unbuildable view is a named refusal */
export function deliverable(root: string, name: string, opts?: { out?: string; draft?: boolean }): Promise<RenderResult> { throw new Error("mock-out"); }
