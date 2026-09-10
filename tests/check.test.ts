/** check — seven mechanical checks; every defect names file and line. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdirSync, rmSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as check from "../src/check.ts";
import * as asks from "../src/asks.ts";
import * as record from "../src/record.ts";

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

test("consumption, half one: an intent slug that is no capture fragment is named", () => {
  const root = bareEngagement();
  ledger.route(root, stage(root, "p.pdf", "policy"), ["no-such-fragment"]);
  const d = check.run(root).find(d => d.check === "consumption")!;
  assert.ok(d.message.includes("no-such-fragment"));
});

test("consumption, half two: a RETIRED source that is not fully cited is an error naming what is outstanding", () => {
  const root = bareEngagement();
  execFileSync("git", ["init", "-q"], { cwd: root });
  execFileSync("git", ["config", "user.email", "t@example.invalid"], { cwd: root });
  execFileSync("git", ["config", "user.name", "test"], { cwd: root });
  // route, cite, checkpoint — the citation retires the source to processed/
  const src = ledger.route(root, stage(root, "p.pdf", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "3-way match", cites: [src] }] });
  record.checkpoint(root, "fold-in");
  const entry = ledger.status(root).entries.find(e => e.id === src)!;
  assert.ok(entry.file.startsWith("_sources/processed/"), "fully cited at checkpoint => retired");
  assert.deepEqual(check.run(root).filter(d => d.severity === "error"), [], "retired and fully cited is clean");
  // now REMOVE the citation: the source is still retired but no longer accounted for
  fragment(root, "ap", { statements: [{ text: "3-way match" }] });
  const d = check.run(root).find(d => d.check === "consumption")!;
  assert.equal(d.severity, "error");
  assert.ok(d.message.includes(src) && d.message.includes("ap"),
    "names the source and the slug still outstanding");
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

test("check polices the direct-write world: a hand-edited register is caught by ask-coverage AND registers", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "_registers/asks.yaml"),
    ["- { id: ASK-001, status: proposed, text: q, questions: [ap#Q-1], answeredBy: [] }",
     "- { id: ASK-002, status: proposed, text: q2, questions: [ap#Q-1], answeredBy: [] }",
     "- { id: ASK-003, status: proposed, text: q3, questions: [ap#Q-9], answeredBy: [] }"].join("\n"));
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "who?" }] });
  // half one — ask-coverage: the same question address in two asks
  const dup = check.run(root).find(d => d.check === "ask-coverage")!;
  assert.equal(dup.severity, "error");
  assert.ok(dup.message.includes("Q-1"), "names the duplicated question");
  assert.ok(dup.message.includes("ASK-001") && dup.message.includes("ASK-002"), "names both asks");
  // half two — registers: an ask naming a question record that does not exist in capture
  const reg = check.run(root).find(d => d.check === "registers")!;
  assert.equal(reg.severity, "error");
  assert.equal(reg.file, "_registers/asks.yaml");
  assert.ok(reg.message.includes("ASK-003") && reg.message.includes("ap#Q-9"),
    "names the ask and the address that resolves to nothing");
});

// ── A20 ────────────────────────────────────────────────────────────────
test("registers: a ledger scan pointer that does not resolve to a file is an error", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "policy.md", "AP policy"), ["ap-approval"]);
  fragment(root, "ap-approval", { statements: [{ text: "Dana approves over $10k", cites: [src] }] });
  // the scout report lives OUTSIDE the stores — `consult scan` copies it in.
  // Writing it into _synthesis/ would pollute the store this very check reads.
  const rep = join(mkdtempSync(join(tmpdir(), "scan-")), "report.yaml");
  writeFileSync(rep, "summary: s\nkeyItems: []\n");
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

// ── ask coverage: settlement's SECOND branch ───────────────────────────
test("settle by REMOVING the question record leaves check clean — the docstring's second branch",
  { todo: "RED on this branch: askCoverage errors on an address whose question record was removed, which is exactly how the second settlement branch settles. Lands with the src fix." },
  () => {
  const root = bareEngagement();
  fragment(root, "ap-approval", { questions: [{ id: "Q-1", text: "Who approves under $10k?" }] });
  const id = asks.propose(root, "Could you send the AP approval policy?", ["ap-approval#Q-1"] as never);
  asks.accept(root, id); asks.sent(root);
  const { src } = asks.respond(root, stage(root, "reply.pdf", "policy attached"), [id]);
  // the fold-in answers the question and REMOVES the record — the other lawful settlement
  // (asks.test.ts covers the branch that keeps the record and adds a citing statement)
  fragment(root, "ap-approval", { statements: [{ text: "Under $10k, team leads approve", cites: [src] }] });
  assert.equal(asks.unsettled(root).length, 0, "removal settles the ask");
  assert.deepEqual(check.run(root).filter(d => d.severity === "error"), [],
    "a question settled by removal is not a dangling register reference");
});
