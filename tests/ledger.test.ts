/** ledger — one door in; consumption COMPUTED from capture citations (A18). */
import { test } from "node:test";
import assert from "node:assert/strict";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";

test("route mints SRC ids in order and is idempotent by hash", () => {
  const root = bareEngagement();
  const a = ledger.route(root, stage(root, "chart.pdf", "org chart"), ["org-structure"]);
  const b = ledger.route(root, stage(root, "policy.docx", "policy"), ["ap-approval"]);
  assert.equal(a, "SRC-001"); assert.equal(b, "SRC-002");
  const again = ledger.route(root, stage(root, "chart-copy.pdf", "org chart"), ["org-structure"]);
  assert.equal(again, a, "same content = same source");
});

test("synthesis provenance REQUIRES resolvable grounds — refused by name otherwise", () => {
  const root = bareEngagement();
  const model = stage(root, "org-model.md", "consolidated org model");
  assert.throws(() => ledger.route(root, model, ["org-structure"], { provenance: "synthesis" }),
    (e: Error) => e.message.includes("grounds"));
  ledger.route(root, stage(root, "c1.pdf", "chart one"), ["org-structure"]);
  const src = ledger.route(root, model, ["org-structure"], { provenance: "synthesis", grounds: ["SRC-001"] });
  assert.equal(src, "SRC-002");
});

test("consumption is DERIVED: a source is consumed at a slug exactly when a statement there cites it", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "chart.pdf", "org chart"), ["org-structure", "ap-team"]);
  fragment(root, "org-structure", { statements: [{ text: "Dana reports to the CFO", cites: [src] }] });
  const s = ledger.status(root);
  assert.deepEqual(s.consumed.get(src), ["org-structure"]);
  assert.deepEqual(s.outstanding.get(src), ["ap-team"], "intent minus consumed = the visible debt");
});

test("corroboration counts: joining an existing citation list IS consumption", () => {
  const root = bareEngagement();
  const one = ledger.route(root, stage(root, "a.pdf", "aa"), ["org-structure"]);
  const two = ledger.route(root, stage(root, "b.pdf", "bb"), ["org-structure"]);
  fragment(root, "org-structure", { statements: [{ text: "Dana reports to the CFO", cites: [one, two] }] });
  const s = ledger.status(root);
  assert.deepEqual(s.outstanding.get(two), [], "the corroborating source owes nothing");
});

test("park declines with a durable reason; unrouted stays loud until empty", () => {
  const root = bareEngagement();
  const f = stage(root, "junk.tmp", "noise");
  assert.ok(ledger.status(root).unrouted.some(u => u.includes("junk.tmp")));
  ledger.park(root, f, "corrupt export, re-requested");
  assert.equal(ledger.status(root).unrouted.length, 0);
});
