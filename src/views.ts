/**
 * views — the pure builder registry.
 *
 * Owns: NOTHING (R1, 2026-08-26). Derived views are never files: builders
 * run in-memory at render time, feeding the compiled plan directly. The
 * aggregate stage, derived markers, and pending stubs do not exist in v2 —
 * a placeholder cannot ship because a view is never persisted, only
 * computed. Capture areas hold only captured knowledge, nothing generated.
 *
 * BUILDERS is the one registry a new deliverable's view builder joins
 * (what keeps "YAML-sized act" honest). Ships with exactly the four the
 * two shipped definitions need: client-asks, information-requests,
 * open-validations, findings-by-theme. A plan naming an unregistered kind
 * is refused BY NAME before any render.
 */
export type ViewBuilder = (ctx: { root: string; area: string; binding: unknown }) => string;
export const BUILDERS: ReadonlyMap<string, ViewBuilder> = new Map();

/** build every view a compiled plan names, in plan order; refuse unregistered kinds by name */
export function build(root: string, plan: { views: readonly { id: string; builder: string }[] }): Map<string, string> { throw new Error("mock-out"); }
