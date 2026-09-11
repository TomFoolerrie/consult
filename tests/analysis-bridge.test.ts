import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement, stage } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";

test("CSV records preserve multiline fields and require unambiguous headers and column counts", () => {
  const root = bareEngagement();
  const id = ledger.route(root, stage(root, "data.csv", 'name,amount\r\n"first\r\nsecond",10\r\n\r\nlast,20\r\n'), ["ap"]);
  const record = ledger.sourceRecord(root, id, 1);
  assert.deepEqual(record.header, ["name", "amount"]);
  assert.deepEqual(record.values, ["first\r\nsecond", "10"]);
  assert.equal(record.locator.record, 1);
  assert.equal(ledger.sourceRecord(root, id, 2).values[0], "last");
  assert.throws(() => ledger.sourceRecord(root, id, 3), /record/);
  assert.throws(() => ledger.sourceRecord(root, id, 0), /record/);
  for (const [i, text] of ["a,a\n1,2\n", "a,\n1,2\n", "a,b\n1\n", 'a,b\n"bad,2\n'].entries()) {
    const bad = ledger.route(root, stage(root, `bad${i}.csv`, text), ["ap"]);
    assert.throws(() => ledger.sourceTable(root, bad), /CSV/);
  }
});

test("publication preserves input hashes, declares every input, and refuses drift or incompatible deduplication", () => {
  const root = bareEngagement();
  const a = ledger.route(root, stage(root, "a.txt", "first input"), ["ap"]);
  const b = ledger.route(root, stage(root, "b.txt", "second input"), ["ap"]);
  const inputs = [ledger.verifySource(root, a), ledger.verifySource(root, b)].map(s => ({ id: s.id, hash: s.hash }));
  mkdirSync(join(root, "_synthesis/run"), { recursive: true });
  const BODY = "---\ntitle: result\nkind: narrative\nsummary: analysis result\nkeyItems: []\n---\nanalysis result";  // a head card (A22)
  const file = join(root, "_synthesis/run/result-v1.md"); writeFileSync(file, BODY);
  const out = ledger.publishSynthesis(root, file, ["ap"], inputs);
  assert.equal(out.provenance, "synthesis"); assert.deepEqual(out.grounds, [a, b]);
  assert.equal(ledger.publishSynthesis(root, file, ["ap"], inputs).id, out.id, "retry same publication is idempotent");
  const copy = join(root, "_synthesis/run/result-v2.md"); writeFileSync(copy, BODY);
  assert.equal(ledger.publishSynthesis(root, copy, ["ap"], inputs).id, out.id);
  assert.throws(() => ledger.publishSynthesis(root, copy, ["ap"], [inputs[0]!]), /provenance collision/);
  writeFileSync(copy, "first input");
  assert.throws(() => ledger.publishSynthesis(root, copy, ["ap"], inputs), /provenance collision/);
  writeFileSync(join(root, "_sources/new/a.txt"), "changed");
  assert.throws(() => ledger.publishSynthesis(root, copy, ["ap"], inputs), /content changed/);
  assert.equal(readFileSync(file, "utf8"), BODY);
});

test("intake contention is refused without removing another writer's lock", () => {
  const root = bareEngagement(); const file = stage(root, "input.txt", "input");
  const lock = join(root, "_sources/.intake.lock"); writeFileSync(lock, "other writer");
  assert.throws(() => ledger.route(root, file, ["ap"]), /intake busy/);
  assert.equal(readFileSync(lock, "utf8"), "other writer");
  assert.equal(ledger.readBook(root).entries.length, 0);
});

test("publication validates expected input versions, output location and nonempty dependencies before writing ledger", () => {
  const root = bareEngagement();
  const file = stage(root, "primary.txt", "primary"); const id = ledger.route(root, file, ["ap"]);
  const source = ledger.verifySource(root, id); const input = [{ id, hash: source.hash }];
  assert.throws(() => ledger.publishSynthesis(root, file, ["ap"], input), /work product/);
  const out = join(root, "_synthesis/result.md"); writeFileSync(out, "result");
  const before = readFileSync(join(root, "_sources/sources.yaml"), "utf8");
  assert.throws(() => ledger.publishSynthesis(root, out, ["ap"], []), /inputs/);
  assert.throws(() => ledger.publishSynthesis(root, out, ["ap"], [{ id, hash: "0".repeat(64) }]), /input version/);
  assert.equal(readFileSync(join(root, "_sources/sources.yaml"), "utf8"), before);
});
