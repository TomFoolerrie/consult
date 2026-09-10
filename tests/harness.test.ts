/** harness — the layer between the engine and the models (A24). Not engine; tested because it is the thing synthetic #4 stands on. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, existsSync, readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execSync } from "node:child_process";
import { install, seat, SKELETON } from "../harness/install.ts";
import { plan, deliver, loadScript } from "../harness/client.ts";
import { bareEngagement, fragment } from "./helpers.ts";
import * as asks from "../src/asks.ts";
import * as record from "../src/record.ts";

test("install puts the consultant seat, the three worker classes, and a committed skeleton into a fresh root", () => {
  const root = mkdtempSync(join(tmpdir(), "consult-live-"));
  const made = install(root);
  for (const d of SKELETON) assert.ok(existsSync(join(root, d)), d);
  const claude = readFileSync(join(root, "CLAUDE.md"), "utf8");
  assert.ok(claude.includes("## The sitting procedure") && claude.includes("## The folder reads like a sentence"), "seat = consultant.md + system.md");
  assert.ok(claude.includes("subagent_type: worker-haiku | worker-sonnet | worker-opus"), "the substrate notes say how dispatch lands");
  for (const c of ["haiku", "sonnet", "opus"]) {
    const a = readFileSync(join(root, ".claude/agents", `worker-${c}.md`), "utf8");
    assert.match(a, new RegExp(`^model: ${c}$`, "m"), `worker-${c} pins its model`);
    assert.ok(a.includes("Nothing outside the brief's write boundary"));
  }
  assert.ok(made.includes(".git"));
  assert.equal(execSync("git status --porcelain", { cwd: root }).toString().trim(), "", "first commit made; tree clean");
  // idempotent on the prose files: a second install does not clobber the pad
  writeFileSync(join(root, "STATE.md"), "# state pad\n## now\nmid-flight\n");
  install(root);
  assert.ok(readFileSync(join(root, "STATE.md"), "utf8").includes("mid-flight"));
});

test("seat() carries the consultant prompt verbatim — no model identifiers, no second copy of the rules", () => {
  const s = seat();
  assert.ok(!/claude-|opus-|sonnet-|haiku-/i.test(s.replace(/worker-(haiku|sonnet|opus)/g, "")), "no model ids beyond the class names");
  assert.equal((s.match(/## The two gates/g) ?? []).length, 1);
});

test("the scripted client answers only SENT asks, by substring match, honoring non-answer and silence — and never twice", () => {
  const root = bareEngagement();
  record.budgetSet(root, 1000);
  const dir = mkdtempSync(join(tmpdir(), "script-")); mkdirSync(join(dir, "responses"));
  writeFileSync(join(dir, "responses/reorg.md"), "Dana reports to Tomás.");
  writeFileSync(join(dir, "responses/dodge.md"), "We'll get back to you on that.");
  writeFileSync(join(dir, "script.yaml"), `responses:
  - { topic: reporting-line, match: [reporting line, 1000, 2025-01-01], file: responses/reorg.md, behavior: answer }   # non-string YAML terms must coerce
  - { topic: expedite, match: [expedite], file: responses/dodge.md, behavior: non-answer }
  - { topic: duplicates, match: [duplicate], behavior: silence }
`);
  fragment(root, "ap-approval", { questions: [{ id: "Q-1", text: "reporting line?" }] });
  fragment(root, "ap-payment", { questions: [{ id: "Q-3", text: "expedite?" }, { id: "Q-4", text: "duplicates?" }] });
  fragment(root, "ap-intake", { questions: [{ id: "Q-9", text: "vendor master?" }] });
  const a1 = asks.propose(root, "Please confirm Dana's reporting line", ["ap-approval#Q-1"]);
  const a2 = asks.propose(root, "Is the expedite path sanctioned?", ["ap-payment#Q-3"]);
  const a3 = asks.propose(root, "Are the Kessler duplicates duplicate payments?", ["ap-payment#Q-4"]);
  const a4 = asks.propose(root, "Unrelated: who owns the vendor master?", ["ap-intake#Q-9"]);
  for (const a of [a1, a2, a3, a4]) asks.accept(root, a);
  asks.sent(root, [a1, a2, a3]);           // a4 stays accepted, never sent
  const p = plan(asks.entriesOf(root), loadScript(join(dir, "script.yaml")));
  assert.deepEqual(p.map(d => [d.ask, d.behavior]), [[a1, "answer"], [a2, "non-answer"], [a3, "silence"]]);
  const got = deliver(root, join(dir, "script.yaml"));
  assert.deepEqual(got.map(d => d.ask), [a1, a2], "silence delivers nothing; the unsent ask is invisible to the client");
  assert.ok(existsSync(join(root, "_sources/new/reorg.md")) && existsSync(join(root, "_sources/new/dodge.md")));
  assert.equal(deliver(root, join(dir, "script.yaml")).length, 0, "idempotent");
  assert.ok(readFileSync(join(root, ".harness/inbox.log"), "utf8").includes(a1));
});
