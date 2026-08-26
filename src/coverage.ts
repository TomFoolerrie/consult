/**
 * coverage — what the brain knows it knows.
 *
 * Owns: nothing. A pure function, never a file: every call re-reads the
 * ledger and fragments, so the map can never be stale. Per taxonomy node:
 * evidenced | claimed | thin | conflicted | outstanding. The lens-conflict
 * record — two sources disagree, both readings held, never adjudicated —
 * is first-class here (v0's "single most valuable thing to port back").
 * This is the honesty substrate answers, needs, and the librarian stand on.
 */
import type { CoverageStatus, Claim } from "./types.ts";

/** the derived node↔step join (never stored) */
export function nodeSteps(root: string): Map<string, string[]> { throw new Error("mock-out"); }
/** {node: status}, recomputed from disk every call */
export function status(root: string): Map<string, CoverageStatus> { throw new Error("mock-out"); }
/** every lens conflict: node, both claims, both source ids */
export function conflicts(root: string): { node: string; readings: [Claim, Claim] }[] { throw new Error("mock-out"); }
/** the map as printable text — the human's and librarian's shared picture */
export function report(root: string): string { throw new Error("mock-out"); }
