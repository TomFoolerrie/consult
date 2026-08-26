/**
 * views — the aggregate: derived views, rebuilt mechanically.
 *
 * Owns/writes: the derived view files a pinned plan names (marker-stamped,
 * one writer). Zero tokens: pure regeneration from capture. Hosts BUILDERS
 * — the one registry a new deliverable's view builder joins (what keeps
 * "YAML-sized act" honest). Ships with exactly the four builders the two
 * shipped definitions need: client-asks, information-requests,
 * open-validations, findings-by-theme. An unregistered plan kind is
 * refused BY NAME before any render — a view that cannot be built is an
 * error, never a stub that ships (the run-3 placeholder lesson).
 */
export type ViewBuilder = (ctx: { root: string; area: string; binding: unknown }) => string;
export const BUILDERS: ReadonlyMap<string, ViewBuilder> = new Map();

/** rebuild every engine-owned view the pinned plans name */
export function aggregate(root: string, area: string): { rebuilt: string[]; refused: string[] } { throw new Error("mock-out"); }
/** the one derived-file writer, marker-stamped */
export function writeDerived(path: string, heading: string, kind: string, body: string): void { throw new Error("mock-out"); }
