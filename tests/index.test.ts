/** index — progressive disclosure (A22): index → card → content, one card schema everywhere, indexes computed never stored. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement, stage, fragment, node, synthesisFile, sidecarCard } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as index from "../src/index.ts";
import * as kernel from "../src/kernel.ts";

function scanned(root: string, name: string, title: string): string {
  const src = ledger.route(root, stage(root, name, `content of ${name}`), ["ap-approval"]);
  const rep = join(root, "_synthesis", `${name}.scan.tmp.yaml`);
  writeFileSync(rep, `title: ${title}\nkind: narrative\nsummary: the ${title}\nkeyItems: []\n`);
  ledger.scan(root, src as never, rep);
  return src;
}

test("the index is one line per item across every store, read from cards — title · kind · summary", () => {
  const root = bareEngagement();
  scanned(root, "policy.md", "approval-policy-rev3");
  const pq = synthesisFile(root, "je-canonical-2025q2.parquet", Buffer.from([0x50, 0x41, 0x52, 0x31]));
  sidecarCard(root, pq, { title: "je-canonical-2025q2", kind: "system-export", summary: "canonical JE set, Q2", keyItems: ["412,118 rows"] });
  fragment(root, "ap-approval", { statements: [] });
  writeFileSync(join(root, "capture/ap-approval.yaml"), `slug: ap-approval\ntype: process-step\nscope: "who approves what, at which thresholds"\nstatements: []\nquestions: []\n`);
  node(root, "ap", "accounts payable end to end");
  const lines = index.cards(root);
  const find = (ref: string) => lines.find(l => l.ref === ref)!;
  assert.equal(find("SRC-001").title, "approval-policy-rev3");
  assert.equal(find("_synthesis/je-canonical-2025q2.parquet").kind, "system-export");
  assert.equal(find("ap-approval").summary, "who approves what, at which thresholds", "a fragment's card is its scope line");
  assert.equal(find("ap").store, "capture");
  assert.ok(lines.some(l => l.store === "_skills" && l.ref === "data-wrangle"), "skills are already cards");
  const text = index.render(root, "_synthesis");
  assert.ok(text.includes("je-canonical-2025q2") && text.includes("canonical JE set, Q2"));
  assert.ok(!text.includes("SRC-001"), "a store filter narrows the walk");
});

test("an item without a card is LISTED, never hidden — the index is an honest walk, and '(no card)' is the debt", () => {
  const root = bareEngagement();
  ledger.route(root, stage(root, "unscanned.pdf", "pdf bytes"), ["ap-approval"]);
  synthesisFile(root, "orphan.docx", "docx bytes");
  fragment(root, "ap-approval", { statements: [] });
  const lines = index.cards(root);
  assert.equal(lines.find(l => l.ref === "SRC-001")!.summary, "(no card)");
  assert.equal(lines.find(l => l.ref === "_synthesis/orphan.docx")!.summary, "(no card)");
  assert.equal(lines.find(l => l.ref === "ap-approval")!.summary, "(no card)");
});

test("card() opens the full card for any ref — SRC id, synthesis path, capture slug, skill name — and refuses an unknown ref by name", () => {
  const root = bareEngagement();
  scanned(root, "policy.md", "approval-policy-rev3");
  const pq = synthesisFile(root, "je.parquet", "x");
  sidecarCard(root, pq, { title: "je", kind: "system-export", summary: "s", keyItems: [], schema: { rowCount: 3 } });
  assert.equal(index.card(root, "SRC-001").title, "approval-policy-rev3");
  assert.deepEqual((index.card(root, "_synthesis/je.parquet") as any).schema, { rowCount: 3 }, "kind-specific sections ride along");
  assert.equal(index.card(root, "data-wrangle").kind, "skill");
  assert.throws(() => index.card(root, "nothing-here"), (e: Error) => e.message.includes("nothing-here"));
});

test("a markdown synthesis document carries its card in its head (frontmatter) — no sidecar needed for text we author", () => {
  const root = bareEngagement();
  synthesisFile(root, "ap-model.md", `---\ntitle: ap-process-model\nkind: narrative\nsummary: consolidated AP process narrative\nkeyItems: []\n---\n# AP process\n...`);
  const c = index.card(root, "_synthesis/ap-model.md");
  assert.equal(c.title, "ap-process-model");
});

test("kernel: scope is an optional head key on any entity — the fragment's card", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "capture/ap-approval.yaml"), `slug: ap-approval\ntype: process-step\nscope: "thresholds"\nstatements: []\nquestions: []\n`);
  fragment(root, "ap-payment", { statements: [] });
  const ents = kernel.entities(root);
  assert.equal(ents.find(e => e.slug === "ap-approval")!.scope, "thresholds");
  assert.equal(ents.find(e => e.slug === "ap-payment")!.scope, undefined);
});
