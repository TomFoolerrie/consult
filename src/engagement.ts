/**
 * engagement — the folder truth, flat.
 *
 * One engagement, one capture space (ROT-2/ROT-3, 2026-08-26): fragments
 * live in <root>/capture/, taxonomy nodes in <root>/capture/_taxonomy/.
 * There is NO manifest (membership is the files on disk; ordering, when a
 * render needs one, comes from the taxonomy or the definition) and NO
 * area directory layer (partitioning is the taxonomy's job — that is what
 * L1s are). There is no .proposed/ staging and no confirm ceremony: the
 * consultant writes live, and the gates are spends and sends. There is no scaffolding verb (A9):
 * the fragment format lives in the type declaration, the consultant writes
 * the file, and the grammar check catches malformation.
 *
 * The locate rule survives: an engagement root is the directory holding
 * _sources/. A tree that looks like an engagement but lacks the marker is
 * a named CONTRADICTION — never a silent downgrade, never "done".
 */
import type { EngagementHealth } from "./types.ts";
import type { Entity } from "./kernel.ts";

export interface Engagement { root: string; health: EngagementHealth; }

/** walk up to the _sources/ marker; absence and contradiction are named results */
export function locate(path: string): Engagement { throw new Error("mock-out"); }
/** every capture fragment, slug order, parsed through kernel */
export function entities(root: string): Entity[] { throw new Error("mock-out"); }
/** every taxonomy node, name order */
export function taxonomy(root: string): Entity[] { throw new Error("mock-out"); }
