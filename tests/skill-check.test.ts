/**
 * the skill contract (A27) — the manifest and the STATIC half of conformance.
 * Each test names the claim it protects; every refusal is asserted BY NAME.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, writeFileSync, chmodSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement } from "./helpers.ts";
import * as brief from "../src/brief.ts";

/** write a manifest into the engagement's skill store; level 2 puts it in <name>/skill.yaml */
function manifest(root: string, name: string, body: string, level: 1 | 2 = 1): string {
  const dir = level === 1 ? join(root, "_skills") : join(root, "_skills", name);
  mkdirSync(dir, { recursive: true });
  const p = join(dir, level === 1 ? `${name}.yaml` : "skill.yaml");
  writeFileSync(p, body);
  return dir;
}
const V1 = (name: string, extra = "") =>
  `contract: v1\nname: ${name}\nmission: m\nreads: [sources]\nwrites: []\nreturns: [flags]\nruntime: prompt\n` +
  `contextContract: []\nreturnContract: []\nrules: []\nrecommendedClass: haiku\norigin: engagement\n${extra}`;

test("every shipped skill declares contract v1 with non-empty reads, and passes skillCheck", () => {
  const root = bareEngagement();
  const shipped = brief.skills(root).filter(s => s.origin === "shipped");
  assert.equal(shipped.length, 8, "eight shipped skills");
  for (const s of shipped) {
    assert.equal(s.contract, "v1", `${s.name}: contract`);
    assert.ok(s.reads.length, `${s.name}: a skill that learns nothing has no ports to declare`);
    assert.ok(Array.isArray(s.writes) && Array.isArray(s.returns), `${s.name}: port lists`);
    const { ok, problems } = brief.skillCheck(root, s.name);
    assert.ok(ok, `${s.name}: ${problems.join(" · ")}`);
  }
});

test("level 2: a skill DIRECTORY with skill.yaml resolves, lists, and shadows the shipped skill of the same name", () => {
  const root = bareEngagement();
  manifest(root, "source-read", V1("source-read") + "variantOf: source-read\n", 2);
  assert.equal(brief.skill(root, "source-read").origin, "engagement", "a local level-2 skill shadows shipped");
  assert.ok(brief.skills(root).some(s => s.name === "source-read" && s.origin === "engagement"), "skills() lists both forms");
  assert.equal(brief.skillPath(root, "source-read").level, 2);
  assert.equal(brief.skillPath(root, "assessment").level, 1, "a shipped YAML file is still level 1");
});

test("the manifest refuses BY NAME: an unknown contract, an undeclared port value, a missing port list, a non-string runtime command", () => {
  const root = bareEngagement();
  manifest(root, "v-two", V1("v-two").replace("contract: v1", "contract: v2"));
  assert.throws(() => brief.skill(root, "v-two"), (e: Error) => e.message === "skill v-two: contract v2 is not v1");

  manifest(root, "bad-port", V1("bad-port").replace("reads: [sources]", "reads: [pads]"));
  assert.throws(() => brief.skill(root, "bad-port"),
    (e: Error) => e.message === "skill bad-port: reads 'pads' is not sources|capture|registers|synthesis");

  manifest(root, "no-list", V1("no-list").replace("returns: [flags]\n", ""));
  assert.throws(() => brief.skill(root, "no-list"),
    (e: Error) => e.message.includes("no-list") && e.message.includes("returns must be a list"));

  manifest(root, "bad-rt", V1("bad-rt").replace("runtime: prompt", "runtime:\n  command: 7"));
  assert.throws(() => brief.skill(root, "bad-rt"),
    (e: Error) => e.message === "skill bad-rt: runtime.command must be a string, not number");

  // saveSkill refuses the same shapes at the write door
  assert.throws(() => brief.saveSkill(root, { name: "saved", mission: "m", contract: "v2",
    reads: ["sources"], writes: [], returns: [], runtime: "prompt", contextContract: [], returnContract: [],
    rules: [], recommendedClass: "haiku", origin: "engagement" } as never),
    (e: Error) => e.message === "skill saved: contract v2 is not v1");
});

test("skillCheck never throws for a bad skill — it returns problems; it throws only for a skill that does not exist, by name", () => {
  const root = bareEngagement();
  manifest(root, "bent", V1("bent").replace("contract: v1", "contract: v9").replace("writes: []", "writes: [pads]"));
  const r = brief.skillCheck(root, "bent");
  assert.equal(r.ok, false);
  assert.ok(r.problems.some(p => p === "skill bent: contract v9 is not v1"));
  assert.ok(r.problems.some(p => p === "skill bent: writes 'pads' is not synthesis|capture-fragment"));
  assert.throws(() => brief.skillCheck(root, "mind-reading"), (e: Error) => e.message.includes("mind-reading"));
});

test("skillCheck on a level 2 skill: a missing runtime command is named, and a script carrying [HUMAN] is reported at file:line", () => {
  const root = bareEngagement();
  const dir = manifest(root, "gated", V1("gated").replace("runtime: prompt", 'runtime:\n  command: "scripts/run.sh --once"'), 2);
  mkdirSync(join(dir, "scripts"), { recursive: true });
  writeFileSync(join(dir, "scripts/run.sh"), "#!/bin/sh\necho starting\necho '[HUMAN] approve before continuing'\nexit 0\n");
  chmodSync(join(dir, "scripts/run.sh"), 0o755);
  const r = brief.skillCheck(root, "gated");
  assert.equal(r.ok, false);
  assert.ok(r.problems.some(p => p.includes("scripts/run.sh:3") && p.includes("[HUMAN]")
    && p.includes("a skill stops for no one; the two gates are the engine's")), r.problems.join(" · "));
  assert.ok(!r.problems.some(p => p.includes("not on PATH")), "the runner is there, relative to the skill dir");

  // the runner that is not there is named, and says where it was looked for
  const missing = manifest(root, "absent-runner", V1("absent-runner").replace("runtime: prompt", 'runtime:\n  command: "scripts/nope.py"'), 2);
  assert.ok(missing);
  const m = brief.skillCheck(root, "absent-runner");
  assert.ok(m.problems.some(p => p.includes("absent-runner") && p.includes("scripts/nope.py")
    && p.includes("skill directory") && p.includes("PATH")), m.problems.join(" · "));

  // a level 2 skill whose scripts carry none of the vocabulary passes
  const clean = manifest(root, "clean", V1("clean").replace("runtime: prompt", 'runtime:\n  command: "sh scripts/run.sh"'), 2);
  mkdirSync(join(clean, "scripts"), { recursive: true });
  writeFileSync(join(clean, "scripts/run.sh"), "#!/bin/sh\nconsult index\n");
  assert.deepEqual(brief.skillCheck(root, "clean").problems, []);
});

test("compose prints the Ports block right after Mission — and, for a synthesis writer, where its work products land", () => {
  const root = bareEngagement();
  const b = brief.compose(root, "data-wrangle", "sonnet", {});
  assert.match(b, /## Mission\n[\s\S]*?\n## Ports \(your walls\)\nreads: sources, synthesis\nwrites: synthesis\nreturns: artifacts, flags\nruntime: prompt\n/);
  assert.ok(b.includes("your work products land under _synthesis/<skill>/<run>/ with a card; publish through publishSynthesis; a rerun is a new artifact"));
  assert.ok(b.includes("hand your result back as a return file (see SKILL-CONTRACT.md); the consultant lands it with `consult return`"));

  const ro = brief.compose(root, "source-read", "haiku", {});
  assert.ok(ro.includes("writes: nothing"), "a read-only skill's write port is empty, and says so");
  assert.ok(!ro.includes("publishSynthesis"), "no synthesis landing line for a skill that writes nothing");
});
