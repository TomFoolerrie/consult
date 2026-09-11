/**
 * the conformance kit (A27) — the DYNAMIC half of a skill's proof.
 *
 * What this pins: a well-behaved skill (a scripted stub standing in for a
 * dispatch) passes; each way of becoming a second brain is caught and the
 * finding NAMES the offending path. The kit is the harness's, not the
 * engine's: it reads the engagement's own doors (ledger, index, check) and
 * writes nothing.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, appendFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { conform } from "../harness/conformance.ts";
import { conformanceFixture } from "../harness/fixtures/conformance/engagement.ts";
import * as ledger from "../src/ledger.ts";
import * as asks from "../src/asks.ts";

const SKILL = "payment-review-skill";
const outside = () => mkdtempSync(join(tmpdir(), "consult-return-"));
const has = (findings: string[], needle: string) =>
  assert.ok(findings.some(f => f.includes(needle)), `no finding names ${needle}: ${JSON.stringify(findings, null, 2)}`);

/** the well-behaved stub: one carded work product under its own run dir, published, and a return file outside the stores */
function goodRun(root: string, ret: string): string {
  const dir = join(root, "_synthesis", SKILL, "run-1");
  mkdirSync(dir, { recursive: true });
  const file = join(dir, "duplicate-review.md");
  writeFileSync(file, `---\ntitle: duplicate review\nkind: analysis\nsummary: "two exported rows share INV-001"\n---\n\nSRC-002:R1 and SRC-002:R2 carry the same invoice number.\n`);
  const inputs = ["SRC-001", "SRC-002"].map(id => { const v = ledger.verifySource(root, id); return { id: v.id, hash: v.hash }; });
  ledger.publishSynthesis(root, file, ["payment-review"], inputs);
  writeFileSync(ret, `skill: ${SKILL}\nrun: run-1\nfindings:\n  - claim: "Two exported rows share INV-001; whether paid twice is unresolved"\n    grounds: [SRC-002:R1, SRC-002:R2]\n    theme: payment-review\nflags:\n  - "register completeness not confirmed"\n`);
  return file;
}

test("a skill that reads through the port, writes one carded artifact under its own run directory, and returns through a file conforms", async () => {
  const { root } = conformanceFixture();
  const ret = join(outside(), "return.yaml");
  const r = await conform(root, { skill: SKILL, expectReturn: ret, run: rt => { goodRun(rt, ret); } });
  assert.deepEqual(r.findings, []);
  assert.equal(r.ok, true);
});

test("writing the state pad is caught and named", async () => {
  const { root } = conformanceFixture();
  const r = await conform(root, { skill: SKILL, run: rt => { appendFileSync(join(rt, "STATE.md"), "\nthe skill decided what is next\n"); } });
  assert.equal(r.ok, false);
  has(r.findings, "STATE.md");
  has(r.findings, "consultant's own hands");
});

test("editing a registered source's bytes is caught — the path, and the source id whose hash no longer matches", async () => {
  const { root, policy } = conformanceFixture();
  const r = await conform(root, { skill: SKILL, run: rt => { appendFileSync(join(rt, "_sources/new/ap-policy.md"), "\nAnd the controller approves everything.\n"); } });
  assert.equal(r.ok, false);
  has(r.findings, "_sources/new/ap-policy.md");
  has(r.findings, `source ${policy}: `);
  has(r.findings, "content changed since registration");
});

test("writing under another skill's synthesis directory is caught and named", async () => {
  const { root } = conformanceFixture();
  const r = await conform(root, { skill: SKILL, run: rt => {
    mkdirSync(join(rt, "_synthesis", "other-skill"), { recursive: true });
    writeFileSync(join(rt, "_synthesis/other-skill/notes.md"), "# not mine\n");
  } });
  assert.equal(r.ok, false);
  has(r.findings, "_synthesis/other-skill/notes.md");
  has(r.findings, `outside _synthesis/${SKILL}/`);
});

test("an artifact written without a card is caught and named", async () => {
  const { root } = conformanceFixture();
  const r = await conform(root, { skill: SKILL, run: rt => {
    const dir = join(rt, "_synthesis", SKILL, "run-1"); mkdirSync(dir, { recursive: true });
    writeFileSync(join(dir, "uncarded.md"), "no frontmatter, no sidecar\n");
  } });
  assert.equal(r.ok, false);
  has(r.findings, `_synthesis/${SKILL}/run-1/uncarded.md`);
  has(r.findings, "no card");
});

test("touching the ask register is caught — a skill returns, the consultant lands", async () => {
  const { root, slug } = conformanceFixture();
  const r = await conform(root, { skill: SKILL, run: rt => {
    writeFileSync(join(rt, "capture", "vendor-master.yaml"), `slug: vendor-master\ntype: process-step\nstatements: []\nquestions:\n  - id: Q-1\n    text: "who owns the vendor master?"\n`);
    asks.propose(rt, "Who owns the vendor master?", ["vendor-master#Q-1"]);
  } });
  assert.equal(r.ok, false);
  has(r.findings, "_registers/asks.yaml");
  has(r.findings, "the CONSULTANT lands the return");
  // the fragment it wrote to hang the ask on is caught too: no capture-fragment grant
  has(r.findings, `capture/vendor-master.yaml`);
  has(r.findings, "writes: capture-fragment");
  assert.ok(slug === "payment-review");
});

test("a return file carrying [HUMAN] is caught — a skill never stops for a human", async () => {
  const { root } = conformanceFixture();
  const ret = join(outside(), "return.yaml");
  const r = await conform(root, { skill: SKILL, expectReturn: ret, run: rt => {
    goodRun(rt, ret);
    appendFileSync(ret, `asks:\n  - text: "[HUMAN] confirm before I continue"\n    questions: [payment-review#Q-1]\n`);
  } });
  assert.equal(r.ok, false);
  has(r.findings, "[HUMAN]");
  has(r.findings, ret);
});

test("a missing or malformed return file is named, as is a return written inside a store", async () => {
  const a = conformanceFixture();
  const missing = join(outside(), "return.yaml");
  const r1 = await conform(a.root, { skill: SKILL, expectReturn: missing, run: () => {} });
  has(r1.findings, `${missing}: no return file`);

  const b = conformanceFixture();
  const bad = join(outside(), "return.yaml");
  const r2 = await conform(b.root, { skill: SKILL, expectReturn: bad, run: () => { writeFileSync(bad, "run: run-1\n"); } });
  has(r2.findings, "carries no skill:");

  const c = conformanceFixture();
  const inside = join(c.root, "_synthesis", SKILL, "return.yaml");
  const r3 = await conform(c.root, { skill: SKILL, expectReturn: inside, run: () => {
    mkdirSync(join(c.root, "_synthesis", SKILL), { recursive: true });
    writeFileSync(inside, `skill: ${SKILL}\nrun: run-1\n`);
  } });
  has(r3.findings, "written inside a store");
});
