/** desk — the ONE derived picture, pure. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { rmSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement, stage, fragment, node, pinShape } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as desk from "../src/desk.ts";

test("locate walks up to the _sources/ marker; a marker-less engagement-shaped tree is a NAMED contradiction with a repair", () => {
  const root = bareEngagement();
  assert.equal(desk.locate(join(root, "capture")).root, root);
  rmSync(join(root, "_sources"), { recursive: true });
  const { health } = desk.locate(root);
  assert.equal(health.kind, "contradiction");
  assert.ok((health as any).repair.length > 0, "the contradiction names its repair verb");
});

test("state is recomputed, never cached: a direct capture edit changes the next snapshot", () => {
  const root = bareEngagement();
  node(root, "ap", "accounts payable");
  const before = desk.state(root);
  const src = ledger.route(root, stage(root, "p.pdf", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "3-way match required", cites: [src] }] });
  const after = desk.state(root);
  assert.notDeepEqual(after.coverage, before.coverage, "the capture diff IS the credit");
});

test("coverage per node: evidenced / claimed / contested / outstanding — computed, no 'thin'", () => {
  const root = bareEngagement();
  node(root, "ap", "accounts payable");
  const a = ledger.route(root, stage(root, "a.pdf", "aa"), ["ap"]);
  const b = ledger.route(root, stage(root, "b.pdf", "bb"), ["ap"]);
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "which flow?", sources: [a, b] }] });
  const cov = desk.coverage(root).find(c => c.slug === "ap")!;
  assert.equal(cov.status, "contested");
  assert.equal(cov.conflicts.length, 1);
});

test("no 'all quiet' reachable by damage: a pinned shape over an empty engagement is NOT serviceable", () => {
  const root = bareEngagement();
  pinShape(root, "information-request");
  const s = desk.state(root);
  assert.equal(s.pinnedShapes.length, 1, "shipped definitions are not auto-pinned; this one is");
  assert.equal(s.pinnedShapes[0]!.serviceable, false, "no positive evidence, no serviceable");
});
