import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement, stage } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import { reviewEvidence, renderReview } from "../harness/assessment-evidence.ts";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

function fixture() {
  const root = bareEngagement();
  const source = stage(root, "interview.md", "Controller reports monthly review.\nNo signed evidence supplied.\n");
  const id = ledger.route(root, source, ["close"]);
  const dir = join(root, "_synthesis/assessment/run-1/ledger"); mkdirSync(dir, { recursive: true });
  const file = join(dir, "findings.jsonl");
  const row = { id: "F-001", version: 1, status: "active", observation: "Controller reports monthly review", evidence_basis: "stated", type: "observation", sources: [`${id}:L1`] };
  const save = (rows: unknown[]) => writeFileSync(file, rows.map(r => JSON.stringify(r)).join("\n") + "\n");
  save([row]); return { root, source, id, file, row, save };
}

test("assessment review uses shared IDs, verified excerpts and preserves evidence basis without writing", () => {
  const f = fixture(); const before = readFileSync(f.file, "utf8");
  const pack = reviewEvidence(f.root, f.file);
  assert.equal(pack.ok, true);
  assert.equal(pack.findings[0]!.evidenceBasis, "stated");
  assert.equal(pack.findings[0]!.citations[0]!.excerpt!.text, "Controller reports monthly review.");
  assert.equal(pack.findings[0]!.citations[0]!.source!.id, f.id);
  assert.equal(readFileSync(f.file, "utf8"), before);
  ledger.retire(f.root, f.id);
  assert.equal(reviewEvidence(f.root, f.file).ok, true);
});

test("highest version wins; retired items omitted; historical bad citations are not current failures", () => {
  const f = fixture();
  f.save([{ ...f.row, sources: ["SRC-999:L1"] }, { ...f.row, version: 2 }, { ...f.row, id: "F-002", status: "retired" }]);
  const p = reviewEvidence(f.root, f.file); assert.equal(p.ok, true); assert.equal(p.findings.length, 1);
  assert.equal(p.findings[0]!.version, 2);
});

test("bad references and changed bytes are explicit per-finding defects, not silent omissions", () => {
  const f = fixture();
  f.save([{ ...f.row, sources: ["src-001:L1", `${f.id}:L0`, `${f.id}:L2-L1`, "SRC-999:L1"] }]);
  const p = reviewEvidence(f.root, f.file); assert.equal(p.ok, false);
  assert.equal(p.findings[0]!.citations.length, 4);
  assert.equal(p.errors.length, 4);
  f.save([f.row]); writeFileSync(f.source, "changed");
  assert.match(reviewEvidence(f.root, f.file).errors.join("\n"), /content changed/);
});

test("artifact-only citation warns; empty sources and invalid evidence basis fail", () => {
  const f = fixture(); f.save([{ ...f.row, sources: [f.id] }]);
  const p = reviewEvidence(f.root, f.file); assert.equal(p.ok, true);
  assert.match(p.warnings.join("\n"), /no pinpoint/);
  f.save([{ ...f.row, sources: [], evidence_basis: "certain" }]);
  const bad = reviewEvidence(f.root, f.file); assert.equal(bad.ok, false); assert.equal(bad.errors.length, 2);
});

test("review pack and CLI show excerpts, limitations and nonzero status for broken citations", () => {
  const f = fixture();
  const markdown = renderReview(reviewEvidence(f.root, f.file));
  assert.match(markdown, /Evidence basis: stated/);
  assert.match(markdown, /> Controller reports monthly review\./);
  assert.match(markdown, /does not establish/);
  const script = fileURLToPath(new URL("../harness/assessment-evidence.ts", import.meta.url));
  const args = [script, "--root", f.root, "--findings", f.file, "--format", "markdown"];
  const good = spawnSync(process.execPath, args, { encoding: "utf8" });
  assert.equal(good.status, 0, good.stderr); assert.match(good.stdout, /F-001/);
  writeFileSync(f.source, "changed");
  const bad = spawnSync(process.execPath, args, { encoding: "utf8" });
  assert.equal(bad.status, 2); assert.match(bad.stdout, /content changed/);
});

test("missing, malformed, ambiguous or empty ledgers cannot look like successful assessment", () => {
  const f = fixture();
  assert.throws(() => reviewEvidence(f.root, `${f.file}.missing`), /cannot read/);
  writeFileSync(f.file, "{broken\n"); assert.throws(() => reviewEvidence(f.root, f.file), /line 1/);
  f.save([f.row, { ...f.row, observation: "different" }]); assert.throws(() => reviewEvidence(f.root, f.file), /duplicate version/);
  f.save([]); assert.equal(reviewEvidence(f.root, f.file).ok, false);
});
