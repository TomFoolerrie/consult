import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import * as check from "../src/check.ts";
import * as ledger from "../src/ledger.ts";

test("scripted fictional demonstration completes with review revisions, immutable evidence and clean git", t => {
  const result = spawnSync(process.execPath, ["--experimental-strip-types", resolve("synthetic/engagement-5/run.ts")], { encoding: "utf8" });
  assert.equal(result.status, 0, result.stderr);
  const demo = JSON.parse(result.stdout);
  t.after(() => rmSync(demo.root, { recursive: true, force: true }));
  assert.match(readFileSync(demo.review, "utf8"), /version 3/);
  assert.match(readFileSync(demo.story, "utf8"), /Register completeness still needs confirmation/);
  assert.match(readFileSync(demo.results, "utf8"), /No model was invoked/);
  assert.match(readFileSync(demo.results, "utf8"), /\[DONE\]/);
  assert.match(readFileSync(join(demo.root, "_synthesis/assessment/demo/ledger/gates.json"), "utf8"), /SCRIPTED FIXTURE ONLY/);
  const sources = ledger.readBook(demo.root).entries;
  assert.equal(sources.filter(s => s.provenance === "synthesis").length, 2);
  for (const source of sources) assert.equal(ledger.verifySource(demo.root, source.id).integrity, "sha256-matched");
  assert.deepEqual(check.run(demo.root).filter(d => d.severity === "error"), []);
  const status = spawnSync("git", ["-C", demo.root, "status", "--porcelain"], { encoding: "utf8" });
  assert.equal(status.status, 0); assert.equal(status.stdout, "");
  assert.ok(readFileSync(join(demo.root, "_synthesis/assessment/demo/out/review-before-response.md"), "utf8").includes("version 2"));
});
