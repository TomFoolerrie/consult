/**
 * render — any pinned definition to a client-ready document.
 *
 * Owns/writes: _exports/. ONE verb: materialize the plan's views,
 * aggregate, compile, REFUSE ON PLACEHOLDER by view name, then emit the
 * document wearing the definition's own shell — its title, its skin's
 * furniture, never another deliverable's. Demand-driven: nothing schedules
 * a render; a render of the information request is immediately followed by
 * asks.markSent. One honest mode with draft watermarking.
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
export interface RenderResult { path: string; sections: number; warnings: string[]; }

/** render one pinned definition end to end; refuses placeholders by view name */
export function deliverable(root: string, name: string, opts?: { out?: string; draft?: boolean }): Promise<RenderResult> { throw new Error("mock-out"); }
