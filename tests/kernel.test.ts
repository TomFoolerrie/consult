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
  // the shipped default vocabulary, exactly as process-step.yaml declares it: four kinds in
  // declaration order, only ONE of which the engine itself knows (question — the registers
  // join on it). The other three are amendable per engagement via _types/, so pinning the
  // exact list is what makes an accidental engine-side addition visible.
  assert.deepEqual(t.callouts.map(c => c.kind), ["question", "control", "pain", "io"]);
  assert.deepEqual(t.callouts.map(c => c.prefix), ["Q", "C", "P", "IO"]);
  assert.deepEqual(t.callouts.map(c => c.home), ["questions", "callouts", "callouts", "callouts"]);
  // the taxonomy node declares the question record and nothing else
  const n = kernel.loadType(root, "taxonomy-node");
  assert.deepEqual(n.callouts.map(c => c.kind), ["question"]);
});

test("a two-source question parses as the question callout with an address — the lens-conflict record", () => {
  const root = bareEngagement();
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "CFO or COO?", sources: ["SRC-001", "SRC-002"] }] });
  const [e] = kernel.entities(root);
  const q = e!.callouts.find(c => c.id === "Q-1")!;
  assert.equal(q.kind, "question");
  assert.equal(q.addr, "ap#Q-1");
  assert.equal(q.fields.get("sources"), "SRC-001, SRC-002", "sources land as a comma-joined field");
});
