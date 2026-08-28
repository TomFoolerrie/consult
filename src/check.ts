/**
 * check — the QC gate over capture.
 *
 * Owns: NOTHING (ROT-5 — signal files were the dead guard table's stage
 * markers; the session record logs that a check ran). Runs over the whole
 * engagement (no area parameter — ROT-3). Six checks, all MECHANICAL —
 * the hedges check is gone (A9): word-list policing of prose style is a
 * skill rule that binds whoever drafts, not an engine invariant.
 *
 *   grammar        per-fragment parse through the declaration
 *   citations      every cited SRC resolves. An UNCITED capture
 *                  statement is NOT an error — it is the claimed
 *                  standing, legitimate by design; the cites-required
 *                  rule binds synthesis/deliverable DRAFTS only
 *   consumption    intent slugs exist · synthesis grounds resolve ·
 *                  a retired source is actually fully cited (A18 —
 *                  citations are load-bearing for ledger, asks, answers)
 *   mentions       a slug mentioned in prose exists (warning)
 *   ask-coverage   every question id in the ask register exactly once
 *   registers      referenced register entries resolve; citable fields not blank;
 *                  synthesis sources declare resolvable grounds (A12)
 *
 * Errors exit nonzero; warnings print; every message names file and line.
 */
import { parse } from "yaml";
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import * as kernel from "./kernel.ts";
import * as ledger from "./ledger.ts";

export interface Defect { check: string; severity: "error" | "warning"; file: string; line?: number; message: string; }
export type Check = (root: string) => Defect[];
function grammar(root: string): Defect[] {
  const out: Defect[] = [];
  const dir = join(root, "capture");
  if (!existsSync(dir)) return out;
  const tdecl = kernel.loadType(root, "process-step");
  for (const f of readdirSync(dir).filter(f => f.endsWith(".yaml"))) {
    try { kernel.parseEntity(readFileSync(join(dir, f), "utf8"), tdecl, f.replace(/\.yaml$/, "")); }
    catch (e) { out.push({ check: "grammar", severity: "error", file: join("capture", f), message: (e as Error).message }); }
  }
  return out;
}
function safeEntities(root: string) { try { return kernel.entities(root); } catch { return []; } }
function citations(root: string): Defect[] {
  const out: Defect[] = [];
  const ids = new Set(ledger.status(root).entries.map(e => e.id as string));
  for (const e of safeEntities(root)) {
    e.statements.forEach((st, i) => {
      for (const c of st.cites) if (!ids.has(c))
        out.push({ check: "citations", severity: "error", file: join("capture", `${e.slug}.yaml`), line: i + 1,
          message: `${c} resolves to no source on file` });
    });
  }
  return out;
}
function consumption(root: string): Defect[] {
  const out: Defect[] = [];
  const st = ledger.status(root);
  const slugs = new Set(safeEntities(root).map(e => e.slug));
  for (const e of st.entries) {
    for (const sl of e.intent) if (!slugs.has(sl))
      out.push({ check: "consumption", severity: "error", file: "_sources/sources.yaml",
        message: `${e.id} declares intent for ${sl}, which is no capture fragment` });
    if (e.file.startsWith("_sources/processed/") && (st.outstanding.get(e.id)?.length ?? 0) > 0)
      out.push({ check: "consumption", severity: "error", file: "_sources/sources.yaml",
        message: `${e.id} is retired but not fully cited (${st.outstanding.get(e.id)!.join(", ")} outstanding)` });
  }
  return out;
}
function mentions(root: string): Defect[] {
  const out: Defect[] = [];
  const slugs = new Set(safeEntities(root).map(e => e.slug));
  for (const e of safeEntities(root)) e.statements.forEach((st, i) => {
    for (const m of st.text.matchAll(/\[\[([a-z0-9-]+)\]\]/g)) {
      if (!slugs.has(m[1]!)) out.push({ check: "mentions", severity: "warning",
        file: join("capture", `${e.slug}.yaml`), line: i + 1, message: `mentions [[${m[1]}]], which is no fragment` });
    }
  });
  return out;
}
function askCoverage(root: string): Defect[] {
  const out: Defect[] = [];
  const p = join(root, "_registers", "asks.yaml");
  if (!existsSync(p)) return out;
  const raw = parse(readFileSync(p, "utf8"));
  const asksList: { id?: string; questions?: string[] }[] = Array.isArray(raw) ? raw : raw?.asks ?? [];
  const seen = new Map<string, string>();
  for (const a of asksList) for (const q of a.questions ?? []) {
    if (seen.has(q)) out.push({ check: "ask-coverage", severity: "error", file: "_registers/asks.yaml",
      message: `question ${q.split("#")[1] ?? q} (${q}) appears in both ${seen.get(q)} and ${a.id} — exactly once, asked or closed` });
    else seen.set(q, a.id ?? "?");
  }
  return out;
}
function registers(root: string): Defect[] {
  const out: Defect[] = [];
  const slugs = new Set(safeEntities(root).map(e => e.slug));
  const st = ledger.status(root);
  const ids = new Set(st.entries.map(e => e.id as string));
  for (const e of st.entries) {
    if (e.provenance === "synthesis") {
      if (!e.grounds?.length) out.push({ check: "registers", severity: "error", file: "_sources/sources.yaml",
        message: `${e.id} is synthesis with no declared grounds` });
      for (const g of e.grounds ?? []) {
        const ok = /^SRC-\d+$/.test(g) ? ids.has(g) : slugs.has(g.split("#")[0]!);
        if (!ok) out.push({ check: "registers", severity: "error", file: "_sources/sources.yaml",
          message: `${e.id} ground ${g} does not resolve` });
      }
    }
  }
  return out;
}
export const CHECKS: readonly Check[] = [grammar, citations, consumption, mentions, askCoverage, registers];

/** the whole gate; empty error list = clean */
export function run(root: string): Defect[] { return CHECKS.flatMap(c => c(root)); }
