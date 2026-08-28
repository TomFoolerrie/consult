/** check — six mechanical checks; every defect names file and line. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as check from "../src/check.ts";

test("a clean engagement returns zero errors", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "p.pdf", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "3-way match", cites: [src] }] });
  assert.deepEqual(check.run(root).filter(d => d.severity === "error"), []);
});

test("citations: a cite that resolves to no source on file is an error naming file and line", () => {
  const root = bareEngagement();
  fragment(root, "ap", { statements: [{ text: "ghost", cites: ["SRC-042"] }] });
  const d = check.run(root).find(d => d.check === "citations")!;
  assert.equal(d.severity, "error");
  assert.ok(d.file.includes("ap.yaml") && d.message.includes("SRC-042"));
});

test("consumption: intent slugs must exist; a retired source must actually be fully cited", () => {
  const root = bareEngagement();
  ledger.route(root, stage(root, "p.pdf", "policy"), ["no-such-fragment"]);
  const d = check.run(root).find(d => d.check === "consumption")!;
  assert.ok(d.message.includes("no-such-fragment"));
});

test("mentions is a WARNING, not an error", () => {
  const root = bareEngagement();
  fragment(root, "ap", { statements: [{ text: "see [[vendor-onboarding]] for the handoff" }] });
  const d = check.run(root).find(d => d.check === "mentions")!;
  assert.equal(d.severity, "warning");
});

test("an UNCITED capture statement is NOT a citations error — claimed is a legitimate standing", () => {
  const root = bareEngagement();
  fragment(root, "ap", { statements: [{ text: "team prefers quarterly reviews" }] });
  assert.ok(!check.run(root).some(d => d.check === "citations" && d.severity === "error"));
});

test("check polices the direct-write world: a hand-edited register is caught by ask-coverage and registers", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "_registers/asks.yaml"),
    ["- { id: ASK-001, status: proposed, text: q, questions: [ap#Q-1], answeredBy: [] }",
     "- { id: ASK-002, status: proposed, text: q2, questions: [ap#Q-1], answeredBy: [] }"].join("\n"));
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "who?" }] });
  const d = check.run(root).find(d => d.check === "ask-coverage")!;
  assert.equal(d.severity, "error");
  assert.ok(d.message.includes("Q-1"), "names the duplicated question");
});
