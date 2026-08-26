/**
 * brief — the template composer.
 *
 * Owns: nothing. One delegate exists (the worker); what varies is the
 * TEMPLATE (ruled 2026-08-26: drafter/reader/analyst collapsed into one
 * templated worker). compose() resolves the procedural half of one
 * templated unit of work — the files and sources in scope, register
 * slices, standing tenure, open flags, the objective's framing, and the
 * template's rules verbatim — into one printable brief. Issued when, and
 * only when, delegation happens; the librarian working directly already
 * holds the picture (its sitting picture is desk.report). The brief
 * decides nothing about content: facts arrive resolved, judgment stays
 * with the worker.
 *
 * Templates live in kernel/templates/ — each declares mission, model tier,
 * write boundary, context contract, return contract, rules. Adding a
 * template is adding a file (the "YAML-sized act" property). Starter set:
 * procedure-draft, source-read, assessment, data-analysis.
 */
export type TemplateId = "procedure-draft" | "source-read" | "assessment" | "data-analysis" | (string & {});

export interface TemplateParams { area?: string; slug?: string; mode?: "first-draft" | "update"; question?: string; srcIds?: string[]; verb?: string; }

/** resolve one templated unit of work into a printable brief; unknown template is a named refusal */
export function compose(root: string, template: TemplateId, params: TemplateParams): string { throw new Error("mock-out"); }
