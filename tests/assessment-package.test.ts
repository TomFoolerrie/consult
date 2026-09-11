import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, writeFileSync, readFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { bareEngagement, stage } from "./helpers.ts";
import { parse as parseYaml, stringify } from "yaml";
import { createHash } from "node:crypto";
import * as ledger from "../src/ledger.ts";

const skill = resolve("packages/consult-assessment");
function python(script: string, ...args: string[]) {
  return spawnSync("python3", [join(skill, "scripts", script), ...args], { encoding: "utf8" });
}
function fixture() {
  const root = bareEngagement();
  const git = spawnSync("git", ["init", "-q", root], { encoding: "utf8" }); assert.equal(git.status, 0, git.stderr);
  const file = stage(root, "interview.md", "The controller reports monthly access reviews.\n");
  const id = ledger.route(root, file, ["access"]);
  const dir = join(root, "_synthesis/assessment/run-1/ledger"); mkdirSync(dir, { recursive: true });
  writeFileSync(join(dir, ".assessment-ledger"), "");
  const tax = join(root, "taxonomy.yaml");
  writeFileSync(tax, JSON.stringify({ name: "fictional", axes: { area: { required: true, primary: true, values: ["Access"] } }, scales: { severity: { 1: "Low", 2: "Medium", 3: "High" }, impact: { 1: "Low" }, effort: { 1: "Low" } }, figures: [], rules: "" }));
  const row = { id: "F-001", version: 1, status: "active", author: "reader-G1", group: "G1", type: "observation", severity: 1, evidence_basis: "stated", observation: "Controller reports monthly access reviews", area: "Access", sources: [`${id}:L1`] };
  writeFileSync(join(dir, "findings.jsonl"), JSON.stringify(row) + "\n");
  const manifest = join(root, "assessment.json");
  writeFileSync(manifest, JSON.stringify({ mode: "consult", consult_root: root, context: "OBJECTIVE.md", taxonomy: tax,
    paths: { ledger_dir: dir, workdir: "_synthesis/assessment/run-1/work", out: "_synthesis/assessment/run-1/out" },
    groups: [{ id: "G1", agent: "reader-G1", sources: [id], note: "Access review practice" }] }));
  return { root, file, id, dir, tax, row, manifest };
}

test("integrated package check combines local schema validation with engine citation integrity", () => {
  const f = fixture(); const run = () => python("run.py", "check", "--manifest", f.manifest);
  const good = run(); assert.equal(good.status, 0, good.stdout + good.stderr);
  writeFileSync(f.file, "changed"); const bad = run(); assert.notEqual(bad.status, 0);
  assert.match(bad.stdout + bad.stderr, /content changed/);
  writeFileSync(f.file, "The controller reports monthly access reviews.\n");
  writeFileSync(join(f.dir, "findings.jsonl"), JSON.stringify({ ...f.row, area: "Unknown" }) + "\n");
  const schema = run(); assert.notEqual(schema.status, 0); assert.match(schema.stdout + schema.stderr, /Unknown/);
});

test("integrated render emits a shim using engine citations, surviving source retirement and refusing non-CSV data", () => {
  const f = fixture(); ledger.retire(f.root, f.id);
  const rendered = python("run.py", "render", "--manifest", f.manifest, "--op", "extract", "--group", "G1", "--format", "brief");
  assert.equal(rendered.status, 0, rendered.stdout + rendered.stderr);
  const shim = join(f.root, "_synthesis/assessment/run-1/work/assess.py");
  const call = (...args: string[]) => spawnSync("python3", [shim, ...args], { encoding: "utf8" });
  const cited = call("cite", `${f.id}:L1`); assert.equal(cited.status, 0, cited.stderr);
  assert.equal(JSON.parse(cited.stdout).text, "The controller reports monthly access reviews.");
  assert.equal(call("validate").status, 0);
  const data = call("data", "profile", f.id);
  assert.notEqual(data.status, 0); assert.match(data.stderr, /CSV requires/);
  assert.ok(!readFileSync(shim, "utf8").includes('REG = r"None"'));
});

test("fictional text assessment: author correction, analytical layers, fresh-process resume and rendered bundle", () => {
  const f = fixture();
  const edit = python("ledger.py", "--ledger-dir", f.dir, "edit", "F-001", "--author", "reader-G1", "--set", "observation=Controller reports monthly access review; operation is not independently verified", "--reason", "Human calibration: distinguish stated practice from observed operation");
  assert.equal(edit.status, 0, edit.stdout + edit.stderr);
  const append = (layer: string, row: unknown) => {
    const r = spawnSync("python3", [join(skill, "scripts/ledger.py"), "--ledger-dir", f.dir, "--taxonomy", f.tax, "append", layer, "--author", layer], { input: JSON.stringify(row) + "\n", encoding: "utf8" });
    assert.equal(r.status, 0, r.stdout + r.stderr);
  };
  append("themes", { theme: "Reported practice needs corroboration", root_cause: "Operating evidence has not been supplied to this assessment", impact: "Readiness cannot yet be established", findings: ["F-001"] });
  append("recommendations", { solution: "Obtain a completed review and verify its scope", principle: "Verify before concluding", themes: ["T-001"] });
  append("initiatives", { initiative: "Review one completed access-review cycle", owner: "Controller", impact: 1, effort: 1, time_required: "One week", success_measure: "Evidence inspected and limitations recorded", recommendations: ["R-001"] });
  const checked = python("run.py", "check", "--manifest", f.manifest, "--gate", "story");
  assert.equal(checked.status, 0, checked.stdout + checked.stderr);
  const resume = python("run.py", "next", "--manifest", f.manifest);
  assert.equal(resume.status, 0, resume.stderr); assert.match(resume.stdout, /findings gate/);
  for (const op of ["tables", "figures"]) {
    const r = python("render.py", op, "--manifest", f.manifest); assert.equal(r.status, 0, r.stdout + r.stderr);
  }
  const out = join(f.root, "_synthesis/assessment/run-1/out");
  writeFileSync(join(out, "story.md"), "# Fictional assessment\nThe controller reports monthly reviews; operation is not independently verified [F-001]. Obtain and inspect a completed review [R-001].\n");
  const bundle = python("render.py", "bundle", "--manifest", f.manifest);
  assert.equal(bundle.status, 0, bundle.stdout + bundle.stderr);
  assert.ok(readFileSync(join(out, "assessment-output.json"), "utf8").includes("monthly"));
  const rows = readFileSync(join(f.dir, "findings.jsonl"), "utf8").trim().split("\n").map(s => JSON.parse(s));
  assert.equal(rows.length, 2); assert.equal(rows[1].version, 2);
  assert.equal(ledger.readBook(f.root).entries.length, 1, "no second source identity minted by assessment");
});

test("integrated CSV analysis uses records, declares both inputs, versions reruns and validates through the runner", () => {
  const f = fixture();
  const a = ledger.route(f.root, stage(f.root, "left.csv", 'account,amount\n"A\ncontinued",10\nB,20\n'), ["access"]);
  const b = ledger.route(f.root, stage(f.root, "right.csv", 'account,amount\n"A\ncontinued",11\nC,30\n'), ["access"]);
  const m = JSON.parse(readFileSync(f.manifest, "utf8")); m.capture_intent = ["access"];
  writeFileSync(f.manifest, JSON.stringify(m));
  const render = python("run.py", "render", "--manifest", f.manifest, "--op", "extract", "--group", "G1", "--format", "brief");
  assert.equal(render.status, 0, render.stderr);
  const shim = join(f.root, "_synthesis/assessment/run-1/work/assess.py");
  const call = (...args: string[]) => spawnSync("python3", [shim, ...args], { encoding: "utf8" });
  const first = call("data", "run", "recon", a, "--other", b, "--key", "account", "--amount", "amount");
  assert.equal(first.status, 0, first.stderr);
  const publications = () => ledger.readBook(f.root).entries.filter(s => s.provenance === "synthesis");
  const one = publications()[0]!; assert.deepEqual(one.grounds, [a, b]);
  const original = readFileSync(join(f.root, one.file), "utf8");
  assert.match(original, new RegExp(`${b}:R2`));
  assert.ok(original.includes('"implementation_sha256"'));
  assert.ok(original.includes("A\\ncontinued"), "multiline cells stay on one displayed table row");
  const second = call("data", "run", "recon", a, "--other", b, "--key", "account", "--amount", "amount");
  assert.equal(second.status, 0, second.stderr); assert.equal(publications().length, 2);
  assert.notEqual(publications()[1]!.file, one.file); assert.equal(readFileSync(join(f.root, one.file), "utf8"), original);
  const cite = call("cite", `${a}:R1`); assert.equal(cite.status, 0, cite.stderr);
  assert.deepEqual(JSON.parse(cite.stdout).values, ["A\ncontinued", "10"]);
  writeFileSync(join(f.dir, "findings.jsonl"), JSON.stringify({ ...f.row, sources: [`${a}:R1`, `${one.id}:L1`] }) + "\n");
  assert.equal(call("validate").status, 0);
  const ambiguous = ledger.route(f.root, stage(f.root, "ambiguous.csv", "account,amount\nA,10\nA,20\n"), ["access"]);
  const duplicateKeys = call("data", "run", "recon", ambiguous, "--other", b, "--key", "account", "--amount", "amount");
  assert.notEqual(duplicateKeys.status, 0); assert.match(duplicateKeys.stderr, /nonempty unique/);
  const badColumn = call("data", "run", "duplicates", a, "--key", "missing_column");
  assert.notEqual(badColumn.status, 0); assert.match(badColumn.stderr, /unknown columns/);
  writeFileSync(join(f.root, "_sources/new/left.csv"), "account,amount\nchanged,99\n");
  const changed = call("data", "run", "recon", a, "--other", b, "--key", "account", "--amount", "amount");
  assert.notEqual(changed.status, 0); assert.match(changed.stderr, /content changed/);
  assert.equal(publications().length, 2);
});

test("standalone data registration remains separate and functional without the companion CLI", () => {
  const f = fixture(); const csv = stage(f.root, "legacy.csv", "key,amount\nA,10\nA,10\n");
  const registry = join(f.root, "legacy-registry.yaml");
  writeFileSync(registry, stringify({ sources: [{ id: "src-001", file: "_sources/new/legacy.csv", status: "active", sha: createHash("sha256").update(readFileSync(csv)).digest("hex").slice(0, 16), lines: 4 }] }));
  const run = python("data.py", "--registry", registry, "--analysis-dir", join(f.root, "legacy-output"), "run", "duplicates", "src-001", "--key", "key");
  assert.equal(run.status, 0, run.stderr);
  const book = parseYaml(readFileSync(registry, "utf8"));
  assert.equal(book.sources.length, 2); assert.equal(book.sources[1].derived_from, "src-001");
  assert.equal(ledger.readBook(f.root).entries.length, 1, "standalone fixture does not touch CONSULT's registry");
});

test("CONSULT mode never silently falls back to a standalone registry", () => {
  const f = fixture(); const m = JSON.parse(readFileSync(f.manifest, "utf8"));
  m.registry = "legacy.yaml"; writeFileSync(f.manifest, JSON.stringify(m));
  const run = python("run.py", "check", "--manifest", f.manifest);
  assert.notEqual(run.status, 0); assert.match(run.stdout + run.stderr, /registry/);
  delete m.registry; m.paths.workdir = "capture"; writeFileSync(f.manifest, JSON.stringify(m));
  const escaped = python("run.py", "render", "--manifest", f.manifest, "--op", "extract", "--group", "G1");
  assert.notEqual(escaped.status, 0); assert.match(escaped.stdout + escaped.stderr, /must stay under _synthesis/);
});
