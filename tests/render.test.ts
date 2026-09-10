/** render — the seam + the view registry (Phase 2). */
import { test } from "node:test";
import assert from "node:assert/strict";
import { bareEngagement } from "./helpers.ts";
import * as render from "../src/render.ts";

test("a plan naming an unregistered view kind is refused BY NAME before any render", () => {
  const root = bareEngagement();
  assert.throws(() => render.build(root, { views: [{ id: "v1", builder: "no-such-builder" }] }),
    (e: Error) => e.message.includes("no-such-builder"));
});

test("the shipped registry serves the two shipped definitions (growable — at LEAST these three)", () => {
  for (const k of ["client-asks", "findings-by-theme", "information-requests"])
    assert.ok(render.BUILDERS.has(k), k);
});

// ---- the docx seam (A23) ----
import { existsSync, readFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { join } from "node:path";
import { pinShape, fragment } from "./helpers.ts";
import * as asks from "../src/asks.ts";
import * as definitions from "../src/definitions.ts";
import * as index from "../src/index.ts";
import * as check from "../src/check.ts";

/** a docx is a zip: read word/document.xml through python's stdlib */
const documentXml = (p: string) => execFileSync("python3",
  ["-c", "import zipfile,sys; print(zipfile.ZipFile(sys.argv[1]).read('word/document.xml').decode())", p], { encoding: "utf8" });

/** an engagement the information-request is serviceable against: one open question, one accepted ask */
function servedEngagement(): { root: string; askText: string } {
  const root = bareEngagement();
  fragment(root, "ap-approval", { questions: [{ id: "Q-1", text: "who approves invoices over ten thousand" }] });
  pinShape(root, "information-request");
  const askText = "Please send the AP approval matrix for spend over ten thousand";
  const id = asks.propose(root, askText, ["ap-approval#Q-1"], "the client", "the approval matrix");
  asks.accept(root, id);
  return { root, askText };
}

test("assembleJob is pure: block order, static text and view bodies, draft and skin carried — no I/O", () => {
  const defn = definitions.load("information-request");
  const plan = definitions.compilePlan(defn, bareEngagement());
  const views = new Map([["asks", "- ask one"], ["open", "- Q-1: a question"]]);
  const job = render.assembleJob(defn, plan, views, { draft: true });
  assert.equal(job.version, 1);
  assert.equal(job.title, "Information Request");
  assert.equal(job.draft, true);
  assert.deepEqual(job.skin, { format: "docx", requires: ["title-page"] });
  assert.deepEqual(job.sections.map(s => s.id), ["intro", "asks", "open"]);
  assert.equal(job.sections[0]!.body, "Items requested to progress the engagement.");
  assert.equal(job.sections[1]!.body, "- ask one");
  assert.equal(job.sections[2]!.title, "Open questions for reference");
  assert.equal(render.assembleJob(defn, plan, views, {}).draft, false);
});

test("a real render of information-request writes _synthesis/information-request.docx carrying title and ask text", async () => {
  const { root, askText } = servedEngagement();
  const res = await render.deliverable(root, "information-request");
  assert.equal(res.path, "_synthesis/information-request.docx");
  assert.equal(res.sections, 3);
  assert.ok(Array.isArray(res.warnings));
  assert.ok(existsSync(join(root, res.path)));
  const xml = documentXml(join(root, res.path));
  assert.ok(xml.includes("Information Request"));
  assert.ok(xml.includes(askText));
  assert.ok(xml.includes("who approves invoices over ten thousand"));
});

test("--draft puts DRAFT in the document; a non-draft render carries none", async () => {
  const { root } = servedEngagement();
  const plain = await render.deliverable(root, "information-request");
  assert.ok(!documentXml(join(root, plain.path)).includes("DRAFT"));
  const draft = await render.deliverable(root, "information-request", { draft: true, out: "_synthesis/ir-draft.docx" });
  assert.equal(draft.path, "_synthesis/ir-draft.docx");
  assert.ok(documentXml(join(root, draft.path)).includes("DRAFT"));
});

test("the render lands a sidecar card beside the docx; index.card finds it and check has no cards warning", async () => {
  const { root } = servedEngagement();
  await render.deliverable(root, "information-request");
  assert.ok(existsSync(join(root, "_synthesis/information-request.card.yaml")));
  const card = index.card(root, "_synthesis/information-request.docx");
  assert.equal(card.title, "Information Request");
  assert.equal(card.kind, "deliverable");
  assert.ok(card.summary.includes("information-request"));
  assert.deepEqual(card.keyItems, ["Purpose", "Requests", "Open questions for reference"]);
  assert.equal(check.run(root).filter(d => d.check === "cards").length, 0);
});

test("a non-serviceable definition is refused BY NAME before any file is written", async () => {
  const root = bareEngagement();
  pinShape(root, "information-request");
  await assert.rejects(render.deliverable(root, "information-request"),
    (e: Error) => e.message.includes("information-request") && e.message.includes("not serviceable"));
  assert.ok(!existsSync(join(root, "_synthesis/information-request.docx")));
});

test("a missing worker is a named refusal at the render verb — the path is named, no docx is written", async () => {
  const { root } = servedEngagement();
  const bogus = "/nonexistent/render_worker.py";
  await assert.rejects(render.deliverable(root, "information-request", { worker: bogus }),
    (e: Error) => e.message.includes(bogus) && e.message.includes("information-request"));
  assert.ok(!existsSync(join(root, "_synthesis/information-request.docx")));
  assert.ok(!existsSync(join(root, "_synthesis/information-request.card.yaml")));
});
