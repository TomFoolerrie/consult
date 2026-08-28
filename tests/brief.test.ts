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
