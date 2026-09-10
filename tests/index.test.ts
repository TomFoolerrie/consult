/** index — progressive disclosure (A22): index → card → content, one card schema everywhere, indexes computed never stored. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, mkdirSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { bareEngagement, stage, fragment, node, synthesisFile, sidecarCard } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as index from "../src/index.ts";
import * as kernel from "../src/kernel.ts";
import { main } from "../src/cli.ts";

/** route + scan a client source; the report is written OUTSIDE the engagement so it never pollutes a store */
function scanned(root: string, name: string, title: string): string {
  const src = ledger.route(root, stage(root, name, `content of ${name}`), ["ap-approval"]);
  const rep = join(mkdtempSync(join(tmpdir(), "scan-")), "report.yaml");
  writeFileSync(rep, `title: ${title}\nkind: narrative\nsummary: the ${title}\nkeyItems: []\n`);
  ledger.scan(root, src as never, rep);
  return src;
}

test("the index is one line per item across every store, read from cards — title · kind · summary", () => {
  const root = bareEngagement();
  scanned(root, "policy.md", "approval-policy-rev3");
  const pq = synthesisFile(root, "je-canonical-2025q2.parquet", Buffer.from([0x50, 0x41, 0x52, 0x31]));
  sidecarCard(root, pq, { title: "je-canonical-2025q2", kind: "system-export", summary: "canonical JE set, Q2", keyItems: ["412,118 rows"] });
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
  assert.equal(text, "_synthesis  _synthesis/je-canonical-2025q2.parquet  ·  je-canonical-2025q2  ·  system-export  —  canonical JE set, Q2", "the rendered line format is pinned; the store filter narrows the walk");
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

test("nothing in _synthesis/ is invisible: nested dirs are walked; an orphan sidecar and a lineage note are listed by kind; dotfiles are not artifacts", () => {
  const root = bareEngagement();
  mkdirSync(join(root, "_synthesis/models"), { recursive: true });
  const deep = synthesisFile(root, "models/ap.parquet", "PAR1");
  sidecarCard(root, deep, { title: "ap-model", kind: "system-export", summary: "deep", keyItems: [] });
  synthesisFile(root, "stray.card.yaml", "title: stray\nsummary: nobody owns me\nkeyItems: []\n");
  synthesisFile(root, "je-lineage.md", "# lineage");
  synthesisFile(root, ".gitkeep", "");
  const lines = index.cards(root, "_synthesis");
  assert.equal(lines.find(l => l.ref === "_synthesis/models/ap.parquet")!.summary, "deep");
  assert.equal(lines.find(l => l.ref === "_synthesis/stray.card.yaml")!.kind, "orphan-card");
  assert.equal(lines.find(l => l.ref === "_synthesis/je-lineage.md")!.kind, "lineage");
  assert.ok(!lines.some(l => l.ref.endsWith(".gitkeep")));
});

test("a registered synthesis artifact has ONE card: the _sources line falls back to the sidecar, and both lines cross-reference the SRC id", () => {
  const root = bareEngagement();
  ledger.route(root, stage(root, "raw.csv", "a,b"), ["ap"]);
  const pq = synthesisFile(root, "je.parquet", "PAR1");
  sidecarCard(root, pq, { title: "je", kind: "system-export", summary: "canonical", keyItems: [] });
  const src = ledger.route(root, pq, ["ap"], { provenance: "synthesis", grounds: ["SRC-001"] });
  const lines = index.cards(root);
  assert.equal(lines.find(l => l.ref === src)!.summary, "canonical", "before scan is run, the source line already shows the producer's card");
  assert.equal(lines.find(l => l.ref === "_synthesis/je.parquet")!.src, src);
});

test("card() opens the full card for any ref — SRC id, synthesis path, capture slug, skill name — and refuses unknown or AMBIGUOUS refs by name", () => {
  const root = bareEngagement();
  scanned(root, "policy.md", "approval-policy-rev3");
  const pq = synthesisFile(root, "je.parquet", "x");
  sidecarCard(root, pq, { title: "je", kind: "system-export", summary: "s", keyItems: [], schema: { rowCount: 3 } });
  assert.equal(index.card(root, "SRC-001").title, "approval-policy-rev3");
  assert.deepEqual((index.card(root, "_synthesis/je.parquet") as any).schema, { rowCount: 3 }, "kind-specific sections ride along");
  assert.equal(index.card(root, "data-wrangle").kind, "skill");
  assert.throws(() => index.card(root, "nothing-here"), (e: Error) => e.message.includes("nothing-here"));
  // a fragment named like a shipped skill is ambiguous — refused, never silently shadowed
  writeFileSync(join(root, "capture/source-read.yaml"), `slug: source-read\ntype: process-step\nscope: "collides"\nstatements: []\nquestions: []\n`);
  assert.throws(() => index.card(root, "source-read"), (e: Error) => /ambiguous/.test(e.message));
  assert.throws(() => index.card(root, "_synthesis/../STATE.md"), (e: Error) => e.message.includes("outside"));
});

test("card() and the index line agree on kind for the same ref — one identity", () => {
  const root = bareEngagement();
  node(root, "ap", "accounts payable end to end");
  const line = index.cards(root).find(l => l.ref === "ap")!;
  assert.equal(index.card(root, "ap").kind, line.kind);
  assert.equal(index.card(root, "ap").summary, line.summary);
});

test("authored text carries its card in its head: md frontmatter; a yaml artifact's card is its top-level `card:` key — the body is NEVER the card", () => {
  const root = bareEngagement();
  synthesisFile(root, "ap-model.md", `---\ntitle: ap-process-model\nkind: narrative\nsummary: consolidated AP process narrative\nkeyItems: []\n---\n# AP process\n...`);
  assert.equal(index.card(root, "_synthesis/ap-model.md").title, "ap-process-model");
  synthesisFile(root, "schema.yaml", `card:\n  title: gl-schema\n  kind: system-export\n  summary: the GL schema\n  keyItems: []\ncolumns:\n  - name: SECRET_BODY_COLUMN\n`);
  const c = index.card(root, "_synthesis/schema.yaml");
  assert.equal(c.title, "gl-schema");
  assert.ok(!JSON.stringify(c).includes("SECRET_BODY_COLUMN"), "the yaml body is content, not card");
  synthesisFile(root, "bare.yaml", `summary: looks like a card but is a whole file\nkeyItems: []\nbody: SECRET\n`);
  assert.equal(index.cards(root, "_synthesis").find(l => l.ref === "_synthesis/bare.yaml")!.summary, "(no card)", "top-level keys are not a card");
});

test("kernel: scope is an optional head key on any entity — the fragment's card", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "capture/ap-approval.yaml"), `slug: ap-approval\ntype: process-step\nscope: "thresholds"\nstatements: []\nquestions: []\n`);
  fragment(root, "ap-payment", { statements: [] });
  const ents = kernel.entities(root);
  assert.equal(ents.find(e => e.slug === "ap-approval")!.scope, "thresholds");
  assert.equal(ents.find(e => e.slug === "ap-payment")!.scope, undefined);
});

test("cli: `consult index [store]` and `consult card <ref>` read through --root; an unknown store is a named refusal", async () => {
  const root = bareEngagement();
  const pq = synthesisFile(root, "je.parquet", "PAR1");
  sidecarCard(root, pq, { title: "je", kind: "system-export", summary: "s", keyItems: [] });
  const out: string[] = []; const err: string[] = [];
  const log = console.log, error = console.error;
  console.log = (s: string) => { out.push(String(s)); }; console.error = (s: string) => { err.push(String(s)); };
  try {
    assert.equal(await main(["index", "_synthesis", "--root", root]), 0);
    assert.ok(out.join("\n").includes("_synthesis/je.parquet"));
    assert.equal(await main(["card", "_synthesis/je.parquet", "--root", root]), 0);
    assert.equal(await main(["index", "bogus", "--root", root]), 2);
    assert.match(err.join("\n"), /no store named bogus/);
  } finally { console.log = log; console.error = error; }
});

test("a fixture root whose path contains a dot does not break sidecar resolution", () => {
  const root = mkdtempSync(join(tmpdir(), "consult-v2.1-"));
  for (const d of ["_sources/new", "_synthesis", "capture/_taxonomy"]) mkdirSync(join(root, d), { recursive: true });
  const f = synthesisFile(root, "README", "no extension");
  sidecarCard(root, f, { title: "readme", kind: "narrative", summary: "s", keyItems: [] });
  assert.equal(index.cards(root, "_synthesis").find(l => l.ref === "_synthesis/README")!.title, "readme");
});
