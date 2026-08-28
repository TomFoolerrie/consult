/** record — the machinery's hand: git, sessions, budget, BOTH gates. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join } from "node:path";
import { execSync } from "node:child_process";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as record from "../src/record.ts";

function gitInit(root: string) { execSync("git init -q && git add -A && git commit -qm seed", { cwd: root }); }

test("checkpoint commits the WHOLE engagement and appends the session record", () => {
  const root = bareEngagement(); gitInit(root);
  fragment(root, "ap", { statements: [{ text: "note" }] });
  const { committed } = record.checkpoint(root, "fold-in ap");
  assert.ok(committed.some(f => f.includes("capture/ap.yaml")));
  assert.ok(readdirSync(join(root, "_registers/sessions")).length > 0);
});

test("checkpoint retires fully-cited sources — consumption's one side effect (A18)", () => {
  const root = bareEngagement(); gitInit(root);
  const src = ledger.route(root, stage(root, "p.pdf", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "3-way match", cites: [src] }] });
  const { retired } = record.checkpoint(root, "consume policy");
  assert.deepEqual(retired, [src]);
  assert.equal(readdirSync(join(root, "_sources/processed")).length, 1);
  assert.equal(readdirSync(join(root, "_sources/new")).length, 0, "the file MOVED — no copies");
  const after = ledger.status(root);
  assert.ok(after.entries.some(e => e.id === src), "the entry survives the move (file rewritten root-relative)");
  assert.deepEqual(after.consumed.get(src), ["ap"], "consumption unchanged by retirement");
});

test("gate records the yes and the crossing for BOTH kinds — law 6, auditable", () => {
  const root = bareEngagement(); gitInit(root);
  record.gate(root, { kind: "send", what: "information-request v1", ruling: "approved by Dom" });
  record.gate(root, { kind: "spend", what: "assessment on opus (~40k tokens)", ruling: "over budget — approved" });
  const sessions = readdirSync(join(root, "_registers/sessions")).map(f =>
    readFileSync(join(root, "_registers/sessions", f), "utf8")).join("\n");
  assert.ok(sessions.includes("information-request v1") && sessions.includes("assessment on opus"));
});

test("budget lives in the session record; remaining is derived; spend records estimate AND actual", () => {
  const root = bareEngagement(); gitInit(root);
  record.budgetSet(root, 100_000);
  record.spend(root, 30_000, 34_000, "procedure-draft on sonnet");
  const b = record.budget(root);
  assert.equal(b.limit, 100_000);
  assert.equal(b.remaining, 100_000 - 34_000, "actuals, not estimates, draw the budget");
});

test("D9: a spend above remaining is a named refusal until a gate ruling records the yes", () => {
  const root = bareEngagement(); gitInit(root);
  record.budgetSet(root, 10_000);
  assert.throws(() => record.spend(root, 50_000, 0, "big assessment"),
    (e: Error) => e.message.includes("budget"));
  record.gate(root, { kind: "spend", what: "big assessment (~50k)", ruling: "approved over budget" });
  record.spend(root, 50_000, 48_000, "big assessment");
  assert.equal(record.budget(root).remaining, 10_000 - 48_000, "over-budget spends draw once ruled");
});
