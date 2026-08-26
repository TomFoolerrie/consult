/**
 * engagement — the folder truth.
 *
 * Owns/writes: area manifests + fragment skeletons, only inside scaffold
 * (the confirm gate's deterministic half). The locate rule: an engagement
 * root is the directory holding _sources/ — one mode, one marker. A tree
 * that looks like an engagement but lacks the marker is a named
 * CONTRADICTION, never a silent downgrade and never "done" (the run-3
 * wipe, structural). Scaffold is a MERGE: promotion never wipes what it
 * promotes (run-1, kept as a test).
 */
import type { EngagementHealth } from "./types.ts";
import type { Entity } from "./kernel.ts";

export interface Engagement { root: string; areas: readonly string[]; health: EngagementHealth; }

/** walk up to the _sources/ marker; absence and contradiction are named results, not guesses */
export function locate(path: string): Engagement { throw new Error("mock-out"); }
/** load + validate one area manifest; fail-loud */
export function manifest(area: string): AreaManifest { throw new Error("mock-out"); }
export interface AreaManifest { title: string; components: readonly { slug: string; file: string; order: number }[]; }
/** every capture entity, manifest order, parsed through kernel */
export function entities(area: string): Entity[] { throw new Error("mock-out"); }
/** every taxonomy node, name order */
export function taxonomy(area: string): Entity[] { throw new Error("mock-out"); }
/** the confirm gate: merge proposals live, scaffold manifest+skeletons, promote staged asks, report */
export function scaffold(area: string, proposed: string): ScaffoldReport { throw new Error("mock-out"); }
export interface ScaffoldReport { promoted: string[]; scaffolded: string[]; asksPromoted: number; }
