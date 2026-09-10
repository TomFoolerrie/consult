/** check — six mechanical checks; every defect names file and line. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdirSync, rmSync } from "node:fs";
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

// ── A20 ────────────────────────────────────────────────────────────────
test("registers: a ledger scan pointer that does not resolve to a file is an error", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "policy.md", "AP policy"), ["ap-approval"]);
  fragment(root, "ap-approval", { statements: [{ text: "Dana approves over $10k", cites: [src] }] });
  mkdirSync(join(root, "_synthesis"), { recursive: true });
  const rep = join(root, "_synthesis/s.yaml"); writeFileSync(rep, "summary: s\nkeyItems: []\n");
  const path = ledger.scan(root, src, rep);
  assert.equal(check.run(root).filter(d => d.severity === "error").length, 0, "clean with the file present");
  rmSync(join(root, path));
  const errs = check.run(root).filter(d => d.check === "registers");
  assert.equal(errs.length, 1); assert.match(errs[0]!.message, /scan/);
});

// ── A22 ────────────────────────────────────────────────────────────────
import { synthesisFile, sidecarCard } from "./helpers.ts";
test("cards: a synthesis artifact without a card is a WARNING; sidecars and lineage notes are not artifacts", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "p.pdf", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "x", cites: [src] }] });
  const pq = synthesisFile(root, "je.parquet", "PAR1");
  sidecarCard(root, pq, { title: "je", kind: "system-export", summary: "s", keyItems: [] });
  synthesisFile(root, "je-lineage.md", "# lineage");
  assert.equal(check.run(root).filter(d => d.check === "cards").length, 0);
  synthesisFile(root, "orphan.docx", "bytes");
  const w = check.run(root).filter(d => d.check === "cards");
  assert.equal(w.length, 1); assert.equal(w[0]!.severity, "warning"); assert.match(w[0]!.file, /orphan\.docx/);
});
