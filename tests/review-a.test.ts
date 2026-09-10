/** review round A (2026-09-10) — the findings, pinned before the fixes. Each test names the law or claim it protects; every refusal asserted BY NAME. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, readFileSync, mkdirSync, rmSync, existsSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement, stage, fragment, node, synthesisFile } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as kernel from "../src/kernel.ts";
import * as answers from "../src/answers.ts";
import * as check from "../src/check.ts";

const errs = (root: string) => check.run(root).filter(d => d.severity === "error");
const named = (root: string, chk: string, needle: string) =>
  check.run(root).some(d => d.check === chk && d.message.includes(needle));

// ── F1 registers: a real shape check over BOTH registers and the ledger ───────

test("F1a registers/findings: a ground at a removed question or a missing SRC is an ERROR naming the file and the id", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "p.md", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "cited", cites: [src] }], questions: [{ id: "Q-1", text: "who?" }] });
  writeFileSync(join(root, "_registers/findings.yaml"),
    ["- { id: FIND-001, status: proposed, claim: c, grounds: [ap#Q-9] }",
     "- { id: FIND-002, status: proposed, claim: c, grounds: [SRC-042] }",
     "- { id: FIND-003, status: proposed, claim: c, grounds: [nope] }"].join("\n"));
  const d = check.run(root).filter(x => x.check === "registers" && x.severity === "error");
  assert.ok(d.every(x => x.file === "_registers/findings.yaml"), "every defect names the register file");
  assert.ok(d.some(x => x.message.includes("FIND-001") && x.message.includes("ap#Q-9")));
  assert.ok(d.some(x => x.message.includes("FIND-002") && x.message.includes("SRC-042")));
  assert.ok(d.some(x => x.message.includes("FIND-003") && x.message.includes("nope")));
});

test("F1a registers/findings: a status outside proposed|accepted|rejected, and a missing id/claim/grounds, are ERRORS named", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "_registers/findings.yaml"),
    ["- { id: FIND-001, status: done, claim: c, grounds: [] }",
     "- { status: proposed, claim: c, grounds: [] }",
     "- { id: FIND-003, status: proposed, grounds: [] }",
     "- { id: FIND-004, status: proposed, claim: c }"].join("\n"));
  assert.ok(named(root, "registers", "FIND-001 status"), "the bad status is named");
  assert.ok(named(root, "registers", "done"), "…and the offending value quoted");
  assert.ok(named(root, "registers", "no id"), "the entry without an id is named by position");
  assert.ok(named(root, "registers", "FIND-003") && named(root, "registers", "claim"));
  assert.ok(named(root, "registers", "FIND-004") && named(root, "registers", "grounds"));
});

test("F1b registers/asks: bad status, non-list questions, missing answeredBy, missing id/text are ERRORS named", () => {
  const root = bareEngagement();
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "who?" }] });
  writeFileSync(join(root, "_registers/asks.yaml"),
    ["- { id: ASK-001, status: pending, text: t, questions: [ap#Q-1], answeredBy: [] }",
     "- { id: ASK-002, status: proposed, text: t, questions: nope, answeredBy: [] }",
     "- { id: ASK-003, status: proposed, text: t, questions: [] }",
     "- { id: ASK-004, status: proposed, questions: [], answeredBy: [] }",
     "- { status: proposed, text: t, questions: [], answeredBy: [] }"].join("\n"));
  const d = check.run(root).filter(x => x.check === "registers" && x.severity === "error");
  assert.ok(d.every(x => x.file === "_registers/asks.yaml"));
  assert.ok(d.some(x => x.message.includes("ASK-001") && x.message.includes("pending")));
  assert.ok(d.some(x => x.message.includes("ASK-002") && x.message.includes("questions")));
  assert.ok(d.some(x => x.message.includes("ASK-003") && x.message.includes("answeredBy")));
  assert.ok(d.some(x => x.message.includes("ASK-004") && x.message.includes("text")));
  assert.ok(d.some(x => x.message.includes("no id")));
});

test("F1c registers/sources: a missing intent or file, a vanished file, a modified source, and a duplicate id are ERRORS named", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "p.md", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "cited", cites: [src] }] });
  assert.deepEqual(errs(root), [], "clean to start");
  // a modified source: the hash no longer matches
  writeFileSync(join(root, "_sources/new/p.md"), "policy, edited");
  assert.ok(named(root, "registers", `${src} content no longer matches its hash`), "a modified source is a named error");
  // a vanished file
  rmSync(join(root, "_sources/new/p.md"));
  assert.ok(named(root, "registers", "_sources/new/p.md"), "the missing file is named");
  // hand-written breakage: no intent, no file, duplicate ids
  writeFileSync(join(root, "_sources/sources.yaml"),
    ["entries:",
     "  - { id: SRC-001, file: _sources/new/p.md, hash: x, intent: ap, answers: [] }",
     "  - { id: SRC-002, hash: x, intent: [ap], answers: [] }",
     "  - { id: SRC-001, file: _sources/new/p.md, hash: x, intent: [ap], answers: [] }"].join("\n"));
  assert.ok(named(root, "registers", "SRC-001") && named(root, "registers", "intent"));
  assert.ok(named(root, "registers", "SRC-002") && named(root, "registers", "file"));
  assert.ok(named(root, "registers", "duplicate source id SRC-001"));
});

test("F1d registers: a cycle in synthesis grounds, or a chain deeper than 8 hops, is an ERROR naming the ids", () => {
  const root = bareEngagement();
  const a = ledger.route(root, synthesisFile(root, "a.md", "a"), ["ap"], { provenance: "synthesis", grounds: ["SRC-002"] });
  const b = ledger.route(root, synthesisFile(root, "b.md", "b"), ["ap"], { provenance: "synthesis", grounds: [a] });
  assert.equal(b, "SRC-002");
  assert.ok(named(root, "registers", "cycle"), "the cycle is reported");
  assert.ok(named(root, "registers", a) && named(root, "registers", b), "…naming both ids");
  // a chain deeper than 8 hops
  const root2 = bareEngagement();
  let prev = ledger.route(root2, stage(root2, "base.md", "base"), ["ap"]);
  for (let i = 0; i < 10; i++)
    prev = ledger.route(root2, synthesisFile(root2, `s${i}.md`, `s${i}`), ["ap"], { provenance: "synthesis", grounds: [prev] });
  assert.ok(named(root2, "registers", "8 hops") || named(root2, "registers", "deeper than 8"), "the depth cap is visible in check");
  assert.ok(named(root2, "registers", prev), "…naming the id at the deep end");
});

// ── F2 consumption ───────────────────────────────────────────────────────────

test("F2 consumption: a declared intent slug with no fragment YET is a WARNING (the mid-fold-in state); a retired uncited source stays an ERROR", () => {
  const root = bareEngagement();
  ledger.route(root, stage(root, "p.md", "policy"), ["not-written-yet"]);
  const d = check.run(root).filter(x => x.check === "consumption");
  assert.equal(d.length, 1);
  assert.equal(d[0]!.severity, "warning", "declaring intent before writing the fragment is normal");
  assert.ok(d[0]!.message.includes("not-written-yet"));
  // a retired source that is not fully cited: still an error
  const src2 = ledger.route(root, stage(root, "q.md", "q"), ["ap", "ar"]);
  fragment(root, "ap", { statements: [{ text: "x", cites: [src2] }] });
  fragment(root, "ar", { statements: [{ text: "y" }] });
  ledger.retire(root, src2);
  const e = check.run(root).find(x => x.check === "consumption" && x.severity === "error");
  assert.ok(e && e.message.includes(src2) && e.message.includes("ar"), "a retired source not fully cited is named");
});

// ── F3 citations: `line` is a FILE line, or it is not there at all ───────────

test("F3 citations: the defect's line is the ACTUAL file line of the statement's `- text:` entry", () => {
  const root = bareEngagement();
  const p = fragment(root, "ap", { statements: [{ text: "one" }, { text: "two", cites: ["SRC-042"] }] });
  const d = check.run(root).find(x => x.check === "citations")!;
  const lines = readFileSync(p, "utf8").split("\n");
  assert.ok(d.line !== undefined, "a line is reported");
  assert.match(lines[d.line! - 1]!, /- text: "two"/, "…and it points at the offending statement's own line");
});

// ── F4 check docstring must match the CHECKS array ───────────────────────────

test("F4 check: the header docstring lists exactly the seven checks the CHECKS array runs", () => {
  assert.equal(check.CHECKS.length, 7);
  const head = readFileSync(new URL("../src/check.ts", import.meta.url), "utf8").split("*/")[0]!;
  for (const name of ["grammar", "citations", "consumption", "mentions", "ask-coverage", "registers", "cards"])
    assert.ok(new RegExp(`^ \\*   ${name}\\b`, "m").test(head), `the docstring lists ${name}`);
  assert.ok(!/grounds resolve/.test(head.split("consumption")[1]!.split("mentions")[0]!),
    "consumption no longer claims grounds resolution");
});

// ── F5 kernel ────────────────────────────────────────────────────────────────

test("F5a grammar: a .yml file or a nested directory under capture/ is refused BY NAME, never silently ignored", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "capture/foo.yml"), "slug: foo\n");
  mkdirSync(join(root, "capture/sub"), { recursive: true });
  writeFileSync(join(root, "capture/sub/a.yaml"), "slug: a\n");
  const d = check.run(root).filter(x => x.check === "grammar" && x.severity === "error");
  assert.ok(d.some(x => x.message.includes("capture/foo.yml") && x.message.includes(".yaml")));
  assert.ok(d.some(x => x.message.includes("capture/sub/") && x.message.includes("nested directories")));
  assert.ok(!d.some(x => x.message.includes("_taxonomy")), "_taxonomy is the one allowed subdirectory");
});

test("F5b kernel: a DECLARED non-question callout kind parses and carries its label; an undeclared kind is refused by name", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "capture/ap.yaml"),
    ["slug: ap", "type: process-step", "statements: []", "questions: []",
     "callouts:", "  - { kind: control, id: C-1, text: \"two-way match\" }"].join("\n") + "\n");
  const e = kernel.entities(root)[0]!;
  const c = e.callouts.find(c => c.id === "C-1")!;
  assert.equal(c.kind, "control");
  assert.equal(c.label, "CONTROL", "the label comes from the declaration, not the engine");
  assert.equal(c.addr, "ap#C-1");
  assert.deepEqual(kernel.openQuestions(e).map(q => q.id), [], "a control is not a question record");
  writeFileSync(join(root, "capture/ap.yaml"),
    ["slug: ap", "type: process-step", "statements: []", "questions: []",
     "callouts:", "  - { kind: risk, id: R-1, text: \"undeclared\" }"].join("\n") + "\n");
  assert.throws(() => kernel.entities(root), (err: Error) => err.message.includes("risk") && err.message.includes("ap"));
});

test("F5b kernel: a callout kind of `question` in the callouts list, and a duplicate id across questions and callouts, are refused by name", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "capture/ap.yaml"),
    ["slug: ap", "type: process-step", "statements: []",
     "questions:", "  - { id: Q-1, text: who }",
     "callouts:", "  - { kind: control, id: Q-1, text: dup }"].join("\n") + "\n");
  assert.throws(() => kernel.entities(root), (e: Error) => e.message.includes("Q-1"));
  writeFileSync(join(root, "capture/ap.yaml"),
    ["slug: ap", "type: process-step", "statements: []", "questions: []",
     "callouts:", "  - { kind: question, id: Q-2, text: sneaky }"].join("\n") + "\n");
  assert.throws(() => kernel.entities(root), (e: Error) => e.message.includes("Q-2") || e.message.includes("question"));
});

test("F5c kernel: the callout docstring names only kinds the shipped YAML actually declares", () => {
  const head = readFileSync(new URL("../src/kernel.ts", import.meta.url), "utf8").split("*/")[0]!;
  const decl = readFileSync(new URL("../kernel/types/process-step.yaml", import.meta.url), "utf8");
  assert.ok(!/IMPROVEMENT OPPORTUNITY/.test(head), "an unshipped kind is not named as shipped");
  for (const label of ["CONTROL", "PAIN POINT", "INPUT/OUTPUT"])
    assert.ok(decl.includes(label) && head.includes(label), `${label} is declared and named`);
});

// ── F6 answers ───────────────────────────────────────────────────────────────

test("F6a answers: a contested standing carries the STATEMENT texts citing each source, and a third source lands in `more`", () => {
  const root = bareEngagement();
  const s1 = ledger.route(root, stage(root, "a.md", "a"), ["org"]);
  const s2 = ledger.route(root, stage(root, "b.md", "b"), ["org"]);
  const s3 = ledger.route(root, stage(root, "c.md", "c"), ["org"]);
  fragment(root, "org", {
    statements: [{ text: "Ops reports to the CFO", cites: [s1] }, { text: "Ops reports to the COO", cites: [s2] }],
    questions: [{ id: "Q-1", text: "CFO or COO?", sources: [s1, s2, s3] }],
  });
  const item = answers.ground(root, "CFO or COO")!.find(i => i.standing.kind === "contested")!;
  const st = item.standing as any;
  assert.equal(st.readings[0].source, s1);
  assert.equal(st.readings[0].text, "Ops reports to the CFO", "the reading carries the citing statement, not the question text");
  assert.equal(st.readings[1].text, "Ops reports to the COO");
  assert.deepEqual(st.more, [s3], "the third source is kept, never dropped");
  // where no statement cites a source, the question text stands in — nothing is invented
  const root2 = bareEngagement();
  const t1 = ledger.route(root2, stage(root2, "a.md", "a"), ["org"]);
  const t2 = ledger.route(root2, stage(root2, "b.md", "b"), ["org"]);
  fragment(root2, "org", { questions: [{ id: "Q-1", text: "CFO or COO?", sources: [t1, t2] }] });
  const st2 = answers.ground(root2, "CFO")!.find(i => i.standing.kind === "contested")!.standing as any;
  assert.equal(st2.readings[0].text, "CFO or COO?");
  assert.equal(st2.more, undefined, "two sources: no `more`");
});

test("F6b answers: ground(\"\") is refused BY NAME — an empty topic must not match everything", () => {
  const root = bareEngagement();
  fragment(root, "ap", { statements: [{ text: "x" }] });
  assert.throws(() => answers.ground(root, ""), (e: Error) => /topic/.test(e.message));
  assert.throws(() => answers.ground(root, "   "), (e: Error) => /topic/.test(e.message));
});

test("F6d answers: the ground() docstring promises only what it returns — statements and question records", () => {
  const head = readFileSync(new URL("../src/answers.ts", import.meta.url), "utf8");
  const doc = head.split("export function ground")[0]!.split("export interface GroundedItem")[1]!;
  assert.ok(!/coverage/.test(doc) && !/register entries/.test(doc), "no promise of coverage or register entries");
});
