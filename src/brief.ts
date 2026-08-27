/**
 * brief — the skill store and composer.
 *
 * Owns/writes: <root>/_skills/ — the engagement-authored skill store
 * (the consultant's one authoring surface here, written only through
 * saveSkill). The distinction, ruled 2026-08-26: worker CLASSES pin the
 * model (haiku | sonnet | opus); SKILLS are skills with agency —
 * mission, write boundary, context contract, return contract, rules, and
 * a recommended class (advisory). Class and skill are chosen
 * independently per dispatch; estimates price the pair.
 *
 * Resolution: an engagement-authored skill shadows a shipped one of the
 * same name (kernel/skills/), the same rule definitions use. The
 * consultant may author a skill ad-hoc — from scratch or as a variant —
 * but it is always SAVED before use (never run from a prompt), logged in
 * the session record, and thereby reusable: later sittings inherit it.
 *
 * compose() resolves one skilled unit of work — files and sources in
 * scope, register slices, the consultant's standing precedent and open
 * observations (from the state pad), the objective's
 * framing, the skill's rules verbatim — into one printable brief.
 * Issued when, and only when, delegation happens; the consultant's own
 * picture is desk.report. The brief decides nothing about content.
 */
export type WorkerClass = "haiku" | "sonnet" | "opus";

export interface Skill {
  name: string;
  mission: string;
  writes: string | null;            // the write boundary, or null for read-only work
  contextContract: readonly string[];
  returnContract: string;
  rules: readonly string[];
  recommendedClass: WorkerClass;    // advisory; overrides are recorded with reason
  origin: "shipped" | "engagement"; // engagement skills shadow shipped ones by name
  variantOf?: string;               // set when authored as a variant
}

/** resolve a skill by name: engagement store shadows shipped; unknown is a named refusal */
export function skill(root: string, name: string): Skill { throw new Error("mock-out"); }
/** every skill visible to this engagement (shipped + authored), shadowing applied */
export function skills(root: string): Skill[] { throw new Error("mock-out"); }
/** save an ad-hoc skill (from scratch or a variant) into _skills/ — always saved before use, logged in the session record */
export function saveSkill(root: string, tpl: Skill): void { throw new Error("mock-out"); }
/** resolve one skilled unit of work into a printable brief for one worker class */
export function compose(root: string, name: string, cls: WorkerClass, params: Record<string, unknown>): string { throw new Error("mock-out"); }
