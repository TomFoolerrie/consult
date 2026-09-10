/** ledger — one door in; consumption COMPUTED from capture citations (A18). */
import { test } from "node:test";
import assert from "node:assert/strict";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";

test("route mints SRC ids in order and is idempotent by hash", () => {
  const root = bareEngagement();
  const a = ledger.route(root, stage(root, "chart.pdf", "org chart"), ["org-structure"]);
  const b = ledger.route(root, stage(root, "policy.docx", "policy"), ["ap-approval"]);
  assert.equal(a, "SRC-001"); assert.equal(b, "SRC-002");
  const again = ledger.route(root, stage(root, "chart-copy.pdf", "org chart"), ["org-structure"]);
  assert.equal(again, a, "same content = same source");
});

test("synthesis provenance REQUIRES resolvable grounds — refused by name otherwise", () => {
  const root = bareEngagement();
  const model = stage(root, "org-model.md", "consolidated org model");
  assert.throws(() => ledger.route(root, model, ["org-structure"], { provenance: "synthesis" }),
    (e: Error) => e.message.includes("grounds"));
  ledger.route(root, stage(root, "c1.pdf", "chart one"), ["org-structure"]);
  const src = ledger.route(root, model, ["org-structure"], { provenance: "synthesis", grounds: ["SRC-001"] });
  assert.equal(src, "SRC-002");
});

test("consumption is DERIVED: a source is consumed at a slug exactly when a statement there cites it", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "chart.pdf", "org chart"), ["org-structure", "ap-team"]);
  fragment(root, "org-structure", { statements: [{ text: "Dana reports to the CFO", cites: [src] }] });
  const s = ledger.status(root);
  assert.deepEqual(s.consumed.get(src), ["org-structure"]);
  assert.deepEqual(s.outstanding.get(src), ["ap-team"], "intent minus consumed = the visible debt");
});

test("corroboration counts: joining an existing citation list IS consumption", () => {
  const root = bareEngagement();
  const one = ledger.route(root, stage(root, "a.pdf", "aa"), ["org-structure"]);
  const two = ledger.route(root, stage(root, "b.pdf", "bb"), ["org-structure"]);
  fragment(root, "org-structure", { statements: [{ text: "Dana reports to the CFO", cites: [one, two] }] });
  const s = ledger.status(root);
  assert.deepEqual(s.outstanding.get(two), [], "the corroborating source owes nothing");
});

test("park declines with a durable reason; unrouted stays loud until empty", () => {
  const root = bareEngagement();
  const f = stage(root, "junk.tmp", "noise");
  assert.ok(ledger.status(root).unrouted.some(u => u.includes("junk.tmp")));
  ledger.park(root, f, "corrupt export, re-requested");
  assert.equal(ledger.status(root).unrouted.length, 0);
});

// ── A20: the durable scan ──────────────────────────────────────────────
import { existsSync, readFileSync, writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parse } from "yaml";

/**
 * a scout report file, as the intake-scan worker returns it — written OUTSIDE
 * the engagement root, which is where a real one lives before `consult scan`
 * lands it (A20). Staging it in _synthesis/ would pollute a store these very
 * tests read back, and would model a laundering path the charter outlaws.
 * `root` is unused and kept only so callers read the same either way.
 */
function scoutReport(_root: string, name: string, body: Record<string, unknown>): string {
  const p = join(mkdtempSync(join(tmpdir(), "scout-")), name);
  writeFileSync(p, Object.entries(body).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join("\n") + "\n");
  return p;
}

test("scan lands as ONE durable file per source — _sources/scans/SRC-nnn.yaml — and the ledger keeps only the pointer", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "policy.md", "AP policy rev 3"), ["ap-approval"]);
  const report = scoutReport(root, "scout.yaml", { summary: "AP approval policy, rev 3", keyItems: ["$10k threshold", "Dana Okafor approves"] });
  const path = ledger.scan(root, src, report);
  assert.equal(path, "_sources/scans/SRC-001.yaml");
  assert.ok(existsSync(join(root, path)), "the report is a real file");
  const entry = ledger.status(root).entries.find(e => e.id === src)!;
  assert.equal(entry.scan, path, "the ledger entry points at the file — it does not embed it");
  assert.equal(parse(readFileSync(join(root, path), "utf8")).summary, "AP approval policy, rev 3");
});

test("a re-scan overwrites the report; the report is advisory and carries no engagement fields by default", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "policy.md", "AP policy"), ["ap-approval"]);
  ledger.scan(root, src, scoutReport(root, "s1.yaml", { summary: "first pass", keyItems: [] }));
  ledger.scan(root, src, scoutReport(root, "s2.yaml", { summary: "second pass", keyItems: ["one"], parties: ["Dana"] }));
  const got = parse(readFileSync(join(root, "_sources/scans/SRC-001.yaml"), "utf8"));
  assert.equal(got.summary, "second pass");
  assert.deepEqual(got.parties, ["Dana"], "a custom template may ADD fields — they ride along");
});

test("scan refuses by name: an unknown SRC, or a report missing the default template's required fields", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "policy.md", "AP policy"), ["ap-approval"]);
  assert.throws(() => ledger.scan(root, "SRC-009" as never, scoutReport(root, "x.yaml", { summary: "s", keyItems: [] })),
    (e: Error) => e.message.includes("SRC-009"));
  assert.throws(() => ledger.scan(root, src, scoutReport(root, "y.yaml", { keyItems: [] })),
    (e: Error) => e.message.includes("summary"));
});

test("a scan is NOT a source: route refuses anything under _sources/scans/ — a précis can never become grounding", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "policy.md", "AP policy"), ["ap-approval"]);
  const path = ledger.scan(root, src, scoutReport(root, "s.yaml", { summary: "s", keyItems: [] }));
  assert.throws(() => ledger.route(root, join(root, path), ["ap-approval"]),
    (e: Error) => e.message.includes("scan"));
  assert.throws(() => ledger.route(root, join(root, path), ["ap-approval"], { provenance: "synthesis", grounds: [src] }),
    (e: Error) => e.message.includes("scan"), "not even as synthesis");
});

// ── A22: registering a synthesis artifact lands the PRODUCER'S card ────
import { synthesisFile, sidecarCard } from "./helpers.ts";

test("scan with no report lands the sidecar card beside the source — one card, moved, no second document", () => {
  const root = bareEngagement();
  ledger.route(root, stage(root, "raw.csv", "a,b\n1,2"), ["ap-payment"]);
  const pq = synthesisFile(root, "je-canonical.parquet", "PAR1");
  sidecarCard(root, pq, { title: "je-canonical", kind: "system-export", summary: "canonical", keyItems: [] });
  const src = ledger.route(root, pq, ["ap-payment"], { provenance: "synthesis", grounds: ["SRC-001"] });
  const path = ledger.scan(root, src);
  assert.equal(path, `_sources/scans/${src}.yaml`);
  assert.equal(parse(readFileSync(join(root, path), "utf8")).title, "je-canonical");
});

test("scan with no report and no sidecar is a named refusal", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "raw.csv", "a,b"), ["ap-payment"]);
  assert.throws(() => ledger.scan(root, src), (e: Error) => e.message.includes("scout report") && e.message.includes(src),
    "a client source needs a scout report; the no-report path is for synthesis artifacts only");
});

test("a card is never a source either: route refuses any *.card.yaml by name; the no-report scan path is for synthesis artifacts only", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "raw.csv", "a,b"), ["ap-payment"]);
  const pq = synthesisFile(root, "je.parquet", "PAR1");
  const side = sidecarCard(root, pq, { title: "je", kind: "system-export", summary: "s", keyItems: [] });
  assert.throws(() => ledger.route(root, side, ["ap-payment"], { provenance: "synthesis", grounds: [src] }), (e: Error) => e.message.includes("card"));
  // a stray card lying beside a CLIENT source must not be landed by the no-report path
  writeFileSync(join(root, "_sources/new/raw.card.yaml"), "summary: stray\nkeyItems: []\n");
  assert.throws(() => ledger.scan(root, src), (e: Error) => e.message.includes("synthesis"));
});
