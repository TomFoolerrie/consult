/**
 * definitions — the deliverable definition language.
 *
 * Owns: nothing. Loads a definition (engagement-local shadows shipped)
 * through four fail-loud stages: syntax → vocabulary (a binding may only
 * name what its type declares; the special verbs coverage:/asks:/findings:/
 * count: each admit their one shape) → serviceability (a REPORT, never an
 * exception) → skin.
 *
 * CHARTER PROPERTY (D3): adding a deliverable is a YAML-sized act. This
 * module is the wall: a shape needing engine code beyond one registered
 * view builder is refused by name. Definitions EVOLVE with the client
 * relationship — pinning and amending are the same cheap act, and needs
 * re-reads them every call, so an amended shape has no migration step.
 */
import { parse } from "yaml";
import { readFileSync, existsSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as asksMod from "./asks.ts";
import * as findingsMod from "./findings.ts";
import * as kernel from "./kernel.ts";

const SHIPPED = join(dirname(fileURLToPath(import.meta.url)), "..", "kernel", "deliverables");
const VERBS = ["coverage", "asks", "findings", "count"];

export interface Definition {
  name: string; title: string;
  blocks: readonly Block[];
  bindings: ReadonlyMap<string, Binding>;
  skin: Skin;
}
export type Block =
  | { kind: "static"; id: string; title: string; text: string }
  | { kind: "view"; id: string; title: string; binding: string }
  | { kind: "entity-part"; id: string; repeat: { over: string; order: "slug" } };  // slug order — the manifest died in ROT-2
export type Binding = Record<string, unknown>; // shaped per verb, validated at stage 2
export interface Skin { format: "docx"; requires: readonly string[]; }

/** load by name; local shadows shipped; fail-loud */
export function load(name: string, root?: string): Definition {
  const local = root ? join(root, "_definitions", `${name}.yaml`) : "";
  let path = join(SHIPPED, `${name}.yaml`);
  if (local && existsSync(local)) {
    const raw = parse(readFileSync(local, "utf8"));
    if (!raw?.pin) path = local;   // a full local definition shadows; a pin marker points at the shipped one
  }
  if (!existsSync(path)) throw new Error(`definition ${name}: not found (shipped or local)`);
  const raw = parse(readFileSync(path, "utf8")) as any;
  if (!raw?.name || !Array.isArray(raw.blocks) || !raw.skin)
    throw new Error(`definition ${name}: malformed — name, blocks, skin required`);
  const bindings = new Map<string, Binding>(Object.entries(raw.bindings ?? {}));
  // stage 2: a binding may only name what the verbs declare
  for (const [bname, b] of bindings) {
    for (const key of Object.keys(b as object)) {
      if (!VERBS.includes(key))
        throw new Error(`definition ${raw.name}: binding ${bname} names undeclared verb "${key}" (${VERBS.join("/")} only)`);
    }
  }
  for (const blk of raw.blocks) {
    if (blk.kind === "view" && !bindings.has(blk.binding))
      throw new Error(`definition ${raw.name}: view ${blk.id} names missing binding ${blk.binding}`);
  }
  return { name: raw.name, title: raw.title ?? raw.name, blocks: raw.blocks, bindings, skin: raw.skin };
}
/** stage 3 as records: every gap between this engagement and this shape */
export function serviceability(defn: Definition, root: string): ServiceabilityGap[] {
  const gaps: ServiceabilityGap[] = [];
  for (const [bname, b] of defn.bindings) {
    const spec = b as Record<string, string>;
    if (spec.asks === "accepted" && asksMod.entriesOf(root, "accepted").length === 0 && asksMod.entriesOf(root, "sent").length === 0)
      gaps.push({ binding: bname, missing: "no accepted asks to bind", where: "_registers/asks.yaml" });
    if (spec.findings && findingsMod.renderable(root).length === 0)
      gaps.push({ binding: bname, missing: "no accepted findings to bind", where: "_registers/findings.yaml" });
    if (spec.coverage === "open-questions" && kernel.entities(root).every(e => kernel.openQuestions(e).length === 0))
      gaps.push({ binding: bname, missing: "no open question records in capture", where: "capture/" });
  }
  return gaps;
}
export interface ServiceabilityGap { binding: string; missing: string; where: string; }
/** the ordered render plan: views to build, blocks to emit */
export function compilePlan(defn: Definition, root: string): Plan {
  const views = defn.blocks.filter(b => b.kind === "view").map(b => ({ id: b.id, builder: (b as { binding: string }).binding }));
  return { views, blocks: defn.blocks };
}
export interface Plan { views: readonly { id: string; builder: string }[]; blocks: readonly Block[]; }
/** the shapes this engagement has pinned so far — what needs.standing reads */
export function pinned(root: string): Definition[] {
  const dir = join(root, "_definitions");
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter(f => f.endsWith(".yaml")).sort()
    .map(f => load(f.replace(/\.yaml$/, ""), root));
}
