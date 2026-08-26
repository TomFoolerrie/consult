/**
 * brief — the template store and composer.
 *
 * Owns/writes: <root>/_templates/ — the engagement-authored template store
 * (the librarian's one authoring surface here, written only through
 * saveTemplate). The distinction, ruled 2026-08-26: worker CLASSES pin the
 * model (haiku | sonnet | opus); TEMPLATES are skills with agency —
 * mission, write boundary, context contract, return contract, rules, and
 * a recommended class (advisory). Class and template are chosen
 * independently per dispatch; estimates price the pair.
 *
 * Resolution: an engagement-authored template shadows a shipped one of the
 * same name (kernel/templates/), the same rule definitions use. The
 * librarian may author a template ad-hoc — from scratch or as a variant —
 * but it is always SAVED before use (never run from a prompt), logged in
 * the session record, and thereby reusable: later sittings inherit it.
 *
 * compose() resolves one templated unit of work — files and sources in
 * scope, register slices, standing tenure, open flags, the objective's
 * framing, the template's rules verbatim — into one printable brief.
 * Issued when, and only when, delegation happens; the librarian's own
 * picture is desk.report. The brief decides nothing about content.
 */
export type WorkerClass = "haiku" | "sonnet" | "opus";

export interface Template {
  name: string;
  mission: string;
  writes: string | null;            // the write boundary, or null for read-only work
  contextContract: readonly string[];
  returnContract: string;
  rules: readonly string[];
  recommendedClass: WorkerClass;    // advisory; overrides are recorded with reason
  origin: "shipped" | "engagement"; // engagement templates shadow shipped ones by name
  variantOf?: string;               // set when authored as a variant
}

/** resolve a template by name: engagement store shadows shipped; unknown is a named refusal */
export function template(root: string, name: string): Template { throw new Error("mock-out"); }
/** every template visible to this engagement (shipped + authored), shadowing applied */
export function templates(root: string): Template[] { throw new Error("mock-out"); }
/** save an ad-hoc template (from scratch or a variant) into _templates/ — always saved before use, logged in the session record */
export function saveTemplate(root: string, tpl: Template): void { throw new Error("mock-out"); }
/** resolve one templated unit of work into a printable brief for one worker class */
export function compose(root: string, name: string, cls: WorkerClass, params: Record<string, unknown>): string { throw new Error("mock-out"); }
