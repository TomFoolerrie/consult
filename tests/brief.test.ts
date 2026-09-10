/** brief — the skill store + composer: skills carry the agency. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { bareEngagement } from "./helpers.ts";
import * as brief from "../src/brief.ts";

test("shipped skills resolve; an unknown skill is a named refusal", () => {
  const root = bareEngagement();
  assert.equal(brief.skill(root, "source-read").name, "source-read");
  assert.throws(() => brief.skill(root, "mind-reading"), (e: Error) => e.message.includes("mind-reading"));
});

test("a saved local skill SHADOWS the shipped one by name — and ad-hoc skills are always saved before use", () => {
  const root = bareEngagement();
  brief.saveSkill(root, { name: "source-read", mission: "tuned for scanned tables", writes: "nothing",
    contextContract: ["the named sources"], returnContract: ["grounded material"], rules: ["quote, cite"],
    recommendedClass: "haiku", origin: "engagement", variantOf: "source-read" });
  assert.equal(brief.skill(root, "source-read").origin, "engagement");
});

test("compose resolves skill + class + params into one printable brief carrying the rules VERBATIM", () => {
  const root = bareEngagement();
  const b = brief.compose(root, "source-read", "haiku", { question: "Who signs off?", sources: ["SRC-001"] });
  assert.ok(b.includes("Who signs off?") && b.includes("SRC-001"));
  for (const rule of brief.skill(root, "source-read").rules) assert.ok(b.includes(rule));
});

// ── A22: the brief carries the index and the named cards, never content ─
import { writeFileSync, mkdirSync, rmSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { stage, synthesisFile, sidecarCard } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";

test("compose includes the index for the stores in scope and the full cards named in params — content is listed by path, not inlined", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "policy.md", "SECRET BODY TEXT of the policy"), ["ap-approval"]);
  // the scout report lives OUTSIDE the root until `consult scan` lands it (A20) —
  // staging it in _synthesis/ would put a stray card into the very index under test
  const rep = join(mkdtempSync(join(tmpdir(), "scout-")), "r.yaml");
  writeFileSync(rep, "title: approval-policy\nkind: narrative\nsummary: the policy\nkeyItems: [\"$10k threshold\"]\n");
  ledger.scan(root, src, rep);
  const pq = synthesisFile(root, "je.parquet", "PAR1 SECRET BYTES");
  sidecarCard(root, pq, { title: "je-canonical", kind: "system-export", summary: "canonical JEs", keyItems: [] });
  const b = brief.compose(root, "data-analysis", "sonnet", { question: "duplicates?", cards: ["SRC-001", "_synthesis/je.parquet"] });
  assert.ok(b.includes("## Index") && b.includes("approval-policy") && b.includes("je-canonical"));
  assert.ok(b.includes("$10k threshold"), "a named card is carried in full");
  assert.ok(b.includes("_sources/new/policy.md"), "content is referenced by path");
  assert.ok(!b.includes("SECRET BODY TEXT") && !b.includes("SECRET BYTES"), "content is never inlined");
});

test("cli: `consult brief <skill> --cards a,b` carries the named cards — the feature is reachable from the CLI", async () => {
  const root = bareEngagement();
  const pq = synthesisFile(root, "je.parquet", "PAR1");
  sidecarCard(root, pq, { title: "je-canonical", kind: "system-export", summary: "canonical JEs", keyItems: ["UNIQUE-KEY-ITEM"] });
  const { main } = await import("../src/cli.ts");
  const out: string[] = []; const log = console.log; console.log = (s: string) => { out.push(String(s)); };
  try { assert.equal(await main(["brief", "data-analysis", "--cards", "_synthesis/je.parquet", "--root", root]), 0); }
  finally { console.log = log; }
  assert.ok(out.join("\n").includes("UNIQUE-KEY-ITEM"));
});

test("the brief's index is SCOPED: never _skills; only the stores of the named cards when cards are named", () => {
  const root = bareEngagement();
  const pq = synthesisFile(root, "je.parquet", "PAR1");
  sidecarCard(root, pq, { title: "je-canonical", kind: "system-export", summary: "canonical JEs", keyItems: [] });
  ledger.route(root, stage(root, "policy.md", "policy"), ["ap"]);
  const scoped = brief.compose(root, "data-analysis", "sonnet", { cards: ["_synthesis/je.parquet"] });
  assert.ok(scoped.includes("je-canonical") && !scoped.includes("SRC-001"), "only _synthesis is indexed when only a synthesis card is named");
  assert.ok(!/_skills {2}/.test(scoped), "a worker already holds its skill — never index the skill store into a brief");
  const full = brief.compose(root, "data-analysis", "sonnet", {});
  assert.ok(full.includes("SRC-001") && full.includes("je-canonical") && !/_skills {2}/.test(full), "no cards named: every store but _skills");
});

test("a skill with an invalid recommendedClass is refused BY NAME — the class is a dial, not a free string (found by the synthesis review)", () => {
  const root = bareEngagement();
  mkdirSync(join(root, "_skills"), { recursive: true });
  writeFileSync(join(root, "_skills/broken.yaml"), "name: broken\nmission: m\nwrites: nothing\ncontextContract: []\nreturnContract: []\nrules: []\nrecommendedClass: nothing:opus\norigin: engagement\n");
  assert.throws(() => brief.skill(root, "broken"), (e: Error) => e.message.includes("broken") && e.message.includes("nothing:opus"));
  rmSync(join(root, "_skills/broken.yaml"));
  for (const s of brief.skills(root).filter(s => s.origin === "shipped")) assert.ok(["haiku", "sonnet", "opus"].includes(s.recommendedClass), `${s.name}: ${s.recommendedClass}`);
});
