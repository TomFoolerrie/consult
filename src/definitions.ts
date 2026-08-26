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
export interface Definition {
  name: string; title: string;
  blocks: readonly Block[];
  bindings: ReadonlyMap<string, Binding>;
  skin: Skin;
}
export type Block =
  | { kind: "static"; id: string; title: string; text: string }
  | { kind: "view"; id: string; title: string; binding: string }
  | { kind: "entity-part"; id: string; repeat: { over: string; order: "manifest" } };
export type Binding = Record<string, unknown>; // shaped per verb, validated at stage 2
export interface Skin { format: "docx"; requires: readonly string[]; }

/** load by name; local shadows shipped; fail-loud */
export function load(name: string, root?: string): Definition { throw new Error("mock-out"); }
/** stage 3 as records: every gap between this engagement and this shape */
export function serviceability(defn: Definition, root: string): ServiceabilityGap[] { throw new Error("mock-out"); }
export interface ServiceabilityGap { binding: string; missing: string; where: string; }
/** the ordered render plan: views to build, blocks to emit */
export function compilePlan(defn: Definition, root: string): Plan { throw new Error("mock-out"); }
export interface Plan { views: readonly { id: string; builder: string }[]; blocks: readonly Block[]; }
/** the shapes this engagement has pinned so far — what needs.standing reads */
export function pinned(root: string): Definition[] { throw new Error("mock-out"); }
