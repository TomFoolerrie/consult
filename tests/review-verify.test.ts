/** verification round (2026-09-10) — the four holes the reviewer found in the review-round fixes, tests first. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, writeFileSync, mkdtempSync, symlinkSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { execSync } from "node:child_process";
import { bareEngagement, fragment } from "./helpers.ts";
import * as record from "../src/record.ts";
import * as brief from "../src/brief.ts";
import * as desk from "../src/desk.ts";
import * as check from "../src/check.ts";
import { main } from "../src/cli.ts";

const gitInit = (root: string) => execSync("git init -q && git add -A && git commit -qm seed", { cwd: root });

test("law 6: a second `budget set` resets spent-so-far, so it needs the human's words — the consultant cannot re-issue the ceiling", () => {
  const root = bareEngagement();
  record.budgetSet(root, 100);                       // the first set needs no ruling: nothing is on record yet
  record.spend(root, 90, 90, "draft on sonnet");
  assert.throws(() => record.spend(root, 50, 50, "review on opus"), (e: Error) => e.message.includes("review on opus"));
  assert.throws(() => record.budgetSet(root, 100), (e: Error) => e.message.includes("already on record") && e.message.includes("ruling"),
    "a bare re-set is refused by name");
  assert.throws(() => record.budgetSet(root, 100, "no, hold there"), (e: Error) => e.message.includes("hold there"),
    "a ruling that is not a yes is refused, quoting it");
  assert.equal(record.budget(root).remaining, 10, "the refused re-sets changed nothing");
  record.budgetSet(root, 100, "Dom: yes, another 100k for the review");
  const g = record.sessionLines(root).filter(l => l.verb === "gate").at(-1)!;
  assert.ok(g.gate?.ruling.includes("another 100k"), "the gate line carries the human's own words");
  record.spend(root, 50, 50, "review on opus");
  assert.equal(record.budget(root).remaining, 50);
});

test("the one writer of _skills/ never writes outside it: a skill name is a slug", async () => {
  const root = bareEngagement();
  const bad = { name: "../escape", mission: "m", writes: "nothing", contextContract: [], returnContract: [], rules: [], recommendedClass: "haiku", origin: "engagement" } as const;
  assert.throws(() => brief.saveSkill(root, bad as never), (e: Error) => e.message.includes("../escape") && e.message.includes("slug"));
  assert.ok(!existsSync(join(root, "escape.yaml")) && !existsSync(join(root, "_skills/escape.yaml")), "nothing written anywhere");
  const err: string[] = []; const error = console.error; console.error = (s: string) => { err.push(String(s)); };
  try {
    assert.equal(await main(["skill", "save", "--root", root]), 2);
    assert.match(err.join("\n"), /^refused: skill save needs the path/m, "no file is a named refusal, not a path TypeError");
  } finally { console.error = error; }
});

test("checkpoint compares REAL paths: a symlinked engagement root (macOS /tmp) is its own repository, not 'inside' another", () => {
  const real = bareEngagement(); gitInit(real);
  const link = join(mkdtempSync(join(tmpdir(), "link-")), "engagement");
  symlinkSync(real, link);
  fragment(link, "ap", { statements: [{ text: "note" }] });
  const { committed } = record.checkpoint(link, "via symlink");
  assert.ok(committed.some(f => f.includes("capture/ap.yaml")), `committed through the symlink: ${committed.join(", ")}`);
});

test("a hand-broken ask entry is the registers check's defect, never a crash of state()", () => {
  const root = bareEngagement();
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "who?" }] });
  writeFileSync(join(root, "_registers/asks.yaml"), "asks:\n  - { id: ASK-001, status: sent, text: q, questions: ap#Q-1 }\nclosedQuestions: []\n");
  const s = desk.state(root);                         // no answeredBy, questions not a list — must not throw
  assert.equal(s.health.kind, "ok");
  const errs = check.run(root).filter(d => d.check === "registers").map(d => d.message);
  assert.ok(errs.some(m => m.includes("ASK-001") && m.includes("answeredBy")), errs.join(" | "));
  assert.ok(errs.some(m => m.includes("ASK-001") && m.includes("questions must be a list")), errs.join(" | "));
  // and a phantom address is reported ONCE, by the registers check, not twice
  writeFileSync(join(root, "_registers/asks.yaml"), "asks:\n  - { id: ASK-002, status: proposed, text: q, questions: [ap#Q-9], answeredBy: [] }\nclosedQuestions: []\n");
  const phantom = check.run(root).filter(d => d.message.includes("ap#Q-9"));
  assert.equal(phantom.length, 1, phantom.map(d => `${d.check}: ${d.message}`).join(" | "));
});
