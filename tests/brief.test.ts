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
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { stage, synthesisFile, sidecarCard } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";

test("compose includes the index for the stores in scope and the full cards named in params — content is listed by path, not inlined", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "policy.md", "SECRET BODY TEXT of the policy"), ["ap-approval"]);
  const rep = join(root, "_synthesis", "r.yaml"); writeFileSync(rep, "title: approval-policy\nkind: narrative\nsummary: the policy\nkeyItems: [\"$10k threshold\"]\n");
  ledger.scan(root, src, rep);
  const pq = synthesisFile(root, "je.parquet", "PAR1 SECRET BYTES");
  sidecarCard(root, pq, { title: "je-canonical", kind: "system-export", summary: "canonical JEs", keyItems: [] });
  const b = brief.compose(root, "data-analysis", "sonnet", { question: "duplicates?", cards: ["SRC-001", "_synthesis/je.parquet"] });
  assert.ok(b.includes("## Index") && b.includes("approval-policy") && b.includes("je-canonical"));
  assert.ok(b.includes("$10k threshold"), "a named card is carried in full");
  assert.ok(b.includes("_sources/new/policy.md"), "content is referenced by path");
  assert.ok(!b.includes("SECRET BODY TEXT") && !b.includes("SECRET BYTES"), "content is never inlined");
});
