/** A27: locators are the citation grammar. SRC-nnn:Lx-Ly and SRC-nnn:Rn are first-class in capture cites and finding grounds;
 *  standing is computed from the SRC part; the locator itself must resolve (check names one that does not). */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { mkdtempSync } from "node:fs";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as kernel from "../src/kernel.ts";
import * as answers from "../src/answers.ts";
import * as check from "../src/check.ts";
import * as findings from "../src/findings.ts";
import * as returns from "../src/returns.ts";

function seeded() {
  const root = bareEngagement();
  const txt = ledger.route(root, stage(root, "policy.md", "line one\nline two\nline three\n"), ["ap"]);
  const csv = ledger.route(root, stage(root, "pay.csv", "invoice,amount\nINV-1,10\nINV-1,10\n"), ["ap"]);
  return { root, txt, csv };
}

test("a capture statement may cite a locator: it parses, the bare SRC is what consumption and standing see, and the locator is kept", () => {
  const { root, txt, csv } = seeded();
  writeFileSync(join(root, "capture/ap.yaml"), `slug: ap\ntype: process-step\nstatements:\n  - text: "rule on line two"\n    cites: [${txt}:L2-L2]\n  - text: "repeated invoice"\n    cites: [${csv}:R1, ${csv}:R2]\nquestions: []\n`);
  const e = kernel.entities(root).find(x => x.slug === "ap")!;
  assert.deepEqual(e.statements[0]!.cites, [txt]); assert.deepEqual(e.statements[0]!.locators, [`${txt}:L2-L2`]);
  assert.deepEqual(e.statements[1]!.cites, [csv, csv]);
  assert.deepEqual(ledger.status(root).consumed.get(txt), ["ap"], "consumed at the slug through the locator");
  const item = answers.ground(root, "line two")[0]!;
  assert.equal(item.standing.kind, "evidenced"); assert.deepEqual((item.standing as { sources: string[] }).sources, [txt]);
  assert.equal(check.run(root).filter(d => d.severity === "error").length, 0);
});

test("check: a locator that does not resolve (line past the end, record past the end, malformed) is a citations error naming it", () => {
  const { root, txt, csv } = seeded();
  writeFileSync(join(root, "capture/ap.yaml"), `slug: ap\ntype: process-step\nstatements:\n  - text: "a"\n    cites: [${txt}:L9-L9]\n  - text: "b"\n    cites: [${csv}:R7]\nquestions: []\n`);
  const errs = check.run(root).filter(d => d.check === "citations");
  assert.equal(errs.length, 2);
  assert.ok(errs.some(d => d.message.includes(`${txt}:L9-L9`)) && errs.some(d => d.message.includes(`${csv}:R7`)));
  assert.throws(() => kernel.parseEntity(`slug: ap\ntype: process-step\nstatements:\n  - text: a\n    cites: [${txt}:X1]\n`, kernel.loadType(root, "process-step"), "ap"),
    (e: Error) => e.message.includes(`${txt}:X1`));
});

test("a finding's grounds keep the locator; cite() verifies it and refuses an unresolvable one by name", () => {
  const { root, csv } = seeded();
  const id = findings.propose(root, "INV-1 appears twice", [`${csv}:R1`, `${csv}:R2`] as never);
  const reg = readFileSync(join(root, "_registers/findings.yaml"), "utf8");
  assert.ok(reg.includes(`${csv}:R1`) && reg.includes(`${csv}:R2`), `locators preserved in the register for ${id}`);
  assert.throws(() => findings.propose(root, "x", [`${csv}:R9`] as never), (e: Error) => e.message.includes(`${csv}:R9`));
  assert.equal(check.run(root).filter(d => d.severity === "error").length, 0);
});

test("consult return passes locators straight through into the minted finding's grounds — no claim-suffix workaround", () => {
  const { root, csv } = seeded();
  const f = join(mkdtempSync(join(tmpdir(), "ret-")), "r.yaml");
  writeFileSync(f, `skill: s\nrun: r1\nfindings:\n  - claim: "INV-1 twice"\n    grounds: [${csv}:R1, ${csv}:R2]\n`);
  const res = returns.land(root, f);
  const reg = readFileSync(join(root, "_registers/findings.yaml"), "utf8");
  assert.ok(reg.includes(`${csv}:R2`)); assert.ok(!reg.includes("[grounds:"), "the locator lives in grounds, not in the claim");
  assert.equal(res.minted.length, 1);
});
