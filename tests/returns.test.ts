/**
 * returns — the RETURN port (A27). One door for what a skill produces.
 *
 * Each test names the law or claim it protects. Scratch return files are
 * written OUTSIDE the engagement stores: a return file is a skill's
 * hand-off, never a source and never engagement state.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync, existsSync, readFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { bareEngagement, stage, fragment, synthesisFile, sidecarCard } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as findings from "../src/findings.ts";
import * as record from "../src/record.ts";
import * as returns from "../src/returns.ts";
import { main } from "../src/cli.ts";

/** a scratch directory OUTSIDE any engagement — a return file is never engagement state */
const scratch = () => mkdtempSync(join(tmpdir(), "consult-return-"));
function returnFile(body: string): string {
  const p = join(scratch(), "return.yaml");
  writeFileSync(p, body);
  return p;
}

/** the fixture: a text source, a CSV source, a published work product, a client source, one fragment with an open question */
function engagement() {
  const root = bareEngagement();
  const text = ledger.route(root, stage(root, "policy.md", "one\ntwo\nthree\n"), ["payment-review"]);   // SRC-001
  const csv = ledger.route(root, stage(root, "invoices.csv", "inv,amt\nINV-001,10\nINV-001,10\n"), ["payment-review"]); // SRC-002
  fragment(root, "payment-review", {
    statements: [{ text: "the controller reports pre-payment duplicate checks", cites: [text] }],
    questions: [{ id: "Q-1", text: "were INV-001 rows paid twice?" }],
  });
  const wp = synthesisFile(root, "duplicate-review.md", "# duplicate review\n");
  sidecarCard(root, wp, { summary: "the duplicate review", keyItems: ["INV-001"] });
  const art = ledger.publishSynthesis(root, wp, ["payment-review"], [{ id: csv, hash: ledger.verifySource(root, csv).hash }]).id; // SRC-003
  return { root, text, csv, art };
}

const full = (f: ReturnType<typeof engagement>) => `
skill: consult-assessment
run: payment-review-2026-09-11
findings:
  - claim: "Two exported rows share INV-001; whether paid twice is unresolved"
    grounds: [${f.csv}:R1, ${f.csv}:R2, ${f.art}]
    theme: payment-review
asks:
  - text: "Please send one completed duplicate-review record"
    questions: [payment-review#Q-1]
statements:
  - slug: payment-review
    text: "The controller reports pre-payment duplicate checks"
    cites: [${f.text}:L1-L2]
artifacts:
  - ${f.art}
flags:
  - "register completeness not confirmed"
`;

// A27 — the return port: findings are MINTED, asks/statements/flags are HANDED, the run is RECORDED
test("a full valid return mints the findings, hands asks/statements/flags, and records one session line", () => {
  const f = engagement();
  const res = returns.land(f.root, returnFile(full(f)));

  assert.equal(res.minted.length, 1);
  const reg = findings.entriesOf(f.root);
  assert.equal(reg.length, 1);
  assert.equal(reg[0]!.id, res.minted[0]);
  assert.equal(reg[0]!.status, "proposed");
  assert.equal(reg[0]!.theme, "payment-review");
  assert.equal(reg[0]!.claim, "Two exported rows share INV-001; whether paid twice is unresolved", "the claim is untouched — locators live in grounds");
  assert.deepEqual([...reg[0]!.grounds], [`${f.csv}:R1`, `${f.csv}:R2`, f.art], "locators are first-class grounds (A27)");

  // handed, never minted, never written
  assert.equal(res.handed.asks.length, 1);
  assert.deepEqual(res.handed.asks[0]!.questions, ["payment-review#Q-1"]);
  assert.equal(res.handed.statements.length, 1);
  assert.deepEqual(res.handed.flags, ["register completeness not confirmed"]);
  assert.deepEqual(res.artifacts, [f.art]);
  assert.equal(existsSync(join(f.root, "_registers", "asks.yaml")), false, "return never writes the asks register — asks are the consultant's judgment");
  const frag = readFileSync(join(f.root, "capture", "payment-review.yaml"), "utf8");
  assert.equal(frag.includes("The controller reports pre-payment duplicate checks"), false, "capture is written by hand, never by return");

  const lines = record.sessionLines(f.root).filter(l => l.verb === "return");
  assert.equal(lines.length, 1);
  assert.equal(lines[0]!.detail, "consult-assessment/payment-review-2026-09-11: 1 findings, 1 asks, 1 statements, 1 artifacts, 1 flags");
});

// law 7 — fail loud: an unknown top-level key is refused BY NAME, and the shape's required fields are named
test("an unknown top-level key, a missing skill and a missing run are each refused by name", () => {
  const f = engagement();
  assert.throws(() => returns.land(f.root, returnFile("skill: s\nrun: r\nnotes: [x]\n")),
    (e: Error) => e.message.includes("notes"));
  assert.throws(() => returns.land(f.root, returnFile("run: r\n")), (e: Error) => e.message.includes("skill"));
  assert.throws(() => returns.land(f.root, returnFile("skill: s\n")), (e: Error) => e.message.includes("run"));
});

// law 2 — honesty is structural: a finding's ground must RESOLVE, and the refusal names the finding and the ground
test("an unresolvable ground, a malformed locator and an out-of-range line are refused naming the finding and the ground", () => {
  const f = engagement();
  const withGround = (g: string) => `skill: s\nrun: r\nfindings:\n  - claim: "c"\n    grounds: [${g}]\n`;
  for (const [g, needle] of [["SRC-099", "SRC-099"], ["no-such-fragment", "no-such-fragment"],
                             [`${f.text}:X9`, ":X9"], [`${f.text}:L1-L9`, "L1-L9"], [`${f.csv}:R9`, "R9"]] as const) {
    assert.throws(() => returns.land(f.root, returnFile(withGround(g))),
      (e: Error) => e.message.includes("finding 1") && e.message.includes(needle), `${g} must be refused by name`);
  }
});

// the client loop — an ask may only name an OPEN question record
test("an ask naming a question that was never minted, or one since removed, is refused by name", () => {
  const f = engagement();
  const body = (q: string) => `skill: s\nrun: r\nasks:\n  - text: "please send it"\n    questions: [${q}]\n`;
  assert.throws(() => returns.land(f.root, returnFile(body("payment-review#Q-9"))),
    (e: Error) => e.message.includes("payment-review#Q-9"));
  assert.throws(() => returns.land(f.root, returnFile(body("no-such#Q-1"))),
    (e: Error) => e.message.includes("no-such#Q-1"));
  // settlement by removing the question record (A18/A26) — the address stops resolving
  fragment(f.root, "payment-review", { statements: [{ text: "kept", cites: [f.text] }] });
  assert.throws(() => returns.land(f.root, returnFile(body("payment-review#Q-1"))),
    (e: Error) => e.message.includes("payment-review#Q-1"));
});

// return does not create fragments — the consultant does
test("a statement naming a fragment that does not exist is refused by name; return never creates one", () => {
  const f = engagement();
  assert.throws(() => returns.land(f.root, returnFile(
    `skill: s\nrun: r\nstatements:\n  - slug: brand-new\n    text: "t"\n    cites: [${f.text}]\n`)),
    (e: Error) => e.message.includes("brand-new"));
  assert.equal(existsSync(join(f.root, "capture", "brand-new.yaml")), false);
  assert.throws(() => returns.land(f.root, returnFile(
    `skill: s\nrun: r\nstatements:\n  - slug: payment-review\n    text: "t"\n    cites: [SRC-099]\n`)),
    (e: Error) => e.message.includes("SRC-099"));
});

// A12 — an artifact on a return is a PUBLISHED work product, never a client source
test("an artifact that is a client source, or is not registered at all, is refused by name", () => {
  const f = engagement();
  const body = (a: string) => `skill: s\nrun: r\nartifacts: [${a}]\n`;
  assert.throws(() => returns.land(f.root, returnFile(body(f.text))),
    (e: Error) => e.message.includes(f.text) && e.message.includes("not a published work product"));
  assert.throws(() => returns.land(f.root, returnFile(body("SRC-099"))),
    (e: Error) => e.message.includes("SRC-099"));
});

// all-or-nothing — a refusal mints nothing and writes nothing
test("a refusal mints nothing and records nothing, even when earlier items in the same return were valid", () => {
  const f = engagement();
  const bad = `
skill: consult-assessment
run: payment-review-2026-09-11
findings:
  - claim: "good one"
    grounds: [${f.csv}:R1]
  - claim: "bad one"
    grounds: [SRC-099]
flags: ["a flag"]
`;
  assert.throws(() => returns.land(f.root, returnFile(bad)), (e: Error) => e.message.includes("SRC-099"));
  assert.deepEqual(findings.entriesOf(f.root), [], "no finding minted");
  assert.deepEqual(record.sessionLines(f.root).filter(l => l.verb === "return"), [], "no session line");
});

// idempotence — the same (skill, run) is landed once
test("landing the same skill/run twice is refused by name and mints no duplicate findings", () => {
  const f = engagement();
  const file = returnFile(full(f));
  returns.land(f.root, file);
  assert.throws(() => returns.land(f.root, file),
    (e: Error) => e.message.includes("consult-assessment/payment-review-2026-09-11") && e.message.includes("already landed"));
  assert.equal(findings.entriesOf(f.root).length, 1);
  assert.equal(record.sessionLines(f.root).filter(l => l.verb === "return").length, 1);
});

// R5 — the verb wraps the exported function; the CLI prints the typed result
test("consult return <file> prints the result as JSON on 0, and refuses by name on 2", async () => {
  const f = engagement();
  const out: string[] = [], err: string[] = [];
  const log = console.log, error = console.error;
  console.log = (s: string) => { out.push(String(s)); }; console.error = (s: string) => { err.push(String(s)); };
  try {
    assert.equal(await main(["return", returnFile(full(f)), "--root", f.root]), 0);
    assert.equal(await main(["return", returnFile("skill: s\nrun: r\nnotes: [x]\n"), "--root", f.root]), 2);
  } finally { console.log = log; console.error = error; }
  const res = JSON.parse(out[0]!);
  assert.equal(res.minted.length, 1);
  assert.equal(res.handed.asks.length, 1);
  assert.equal(res.handed.statements.length, 1);
  assert.deepEqual(res.handed.flags, ["register completeness not confirmed"]);
  assert.deepEqual(res.artifacts, [f.art]);
  assert.match(err[0]!, /^refused: /);
  assert.match(err[0]!, /notes/);
});

// no workflow in the engine — return validates, mints, records, hands over; an empty return is still a return
test("a return with only a skill and a run lands: nothing minted, nothing handed, one session line", () => {
  const f = engagement();
  const res = returns.land(f.root, returnFile("skill: tidy\nrun: 2026-09-11\n"));
  assert.deepEqual(res, { minted: [], handed: { asks: [], statements: [], flags: [] }, artifacts: [] });
  assert.equal(record.sessionLines(f.root).filter(l => l.verb === "return")[0]!.detail,
    "tidy/2026-09-11: 0 findings, 0 asks, 0 statements, 0 artifacts, 0 flags");
});
