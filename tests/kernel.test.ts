/** kernel — the grammar + enumeration. The three primitives, executable. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { bareEngagement, fragment, node } from "./helpers.ts";
import * as kernel from "../src/kernel.ts";

test("parses a well-formed fragment: statements carry citations, questions carry ids", () => {
  const root = bareEngagement();
  fragment(root, "ap-approval", {
    statements: [{ text: "Dana approves invoices over $10k", cites: ["SRC-001"] }],
    questions: [{ id: "Q-1", text: "Who approves under $10k?" }],
  });
  const [e] = kernel.entities(root);
  assert.equal(e!.slug, "ap-approval");
  assert.equal(e!.statements[0]!.cites[0], "SRC-001");
  assert.equal(kernel.openQuestions(e!)[0]!.id, "Q-1");
});

test("a malformed fragment is a NAMED refusal, never a default", async () => {
  const root = bareEngagement();
  fragment(root, "bad", { statements: [{ text: "orphan" }] });
  // corrupt it below the grammar
  (await import("node:fs")).writeFileSync(`${root}/capture/bad.yaml`, "slug: bad\n  broken: [unclosed");
  assert.throws(() => kernel.entities(root), (err: Error) => err.message.includes("bad"));
});

test("enumeration: entities in slug order, taxonomy in name order", () => {
  const root = bareEngagement();
  fragment(root, "b-two", {}); fragment(root, "a-one", {});
  node(root, "z-late", "tail"); node(root, "a-early", "head");
  assert.deepEqual(kernel.entities(root).map(e => e.slug), ["a-one", "b-two"]);
  assert.deepEqual(kernel.taxonomy(root).map(e => e.slug), ["a-early", "z-late"]);
});

test("the engine hard-codes ONE callout kind (question); other vocabulary is amendable via the type declaration", () => {
  const root = bareEngagement();
  const t = kernel.loadType(root, "process-step");
  assert.ok(t.callouts.some(c => c.kind === "question"), "question record always known");
  // shipped default vocabulary present but engagement-amendable — declared, not hard-coded
  assert.ok(t.callouts.length >= 1);
});
