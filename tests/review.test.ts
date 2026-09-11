/** review round (2026-09-10) — the ten blockers, pinned before the fixes. Each test names the law or claim it protects. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, writeFileSync, mkdirSync, copyFileSync } from "node:fs";
import { join } from "node:path";
import { execSync } from "node:child_process";
import { bareEngagement, stage, fragment, node, pinShape, synthesisFile, sidecarCard } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as record from "../src/record.ts";
import * as answers from "../src/answers.ts";
import * as asks from "../src/asks.ts";
import * as check from "../src/check.ts";
import * as render from "../src/render.ts";
import * as desk from "../src/desk.ts";
import * as index from "../src/index.ts";
import * as brief from "../src/brief.ts";
import * as definitions from "../src/definitions.ts";
import { main } from "../src/cli.ts";

const gitInit = (root: string) => execSync("git init -q && git add -A && git commit -qm seed", { cwd: root });

// B1 — law 2: a synthesis grounded on a capture address takes the WEAKEST standing of what it names
test("B1 synthesis grounds: a bare slug is the MINIMUM over its statements; a question address is claimed; an addressed statement is itself", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "p.md", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "cited", cites: [src] }, { text: "uncited one" }, { text: "uncited two" }], questions: [{ id: "Q-1", text: "open?" }] });
  const mixed = ledger.route(root, synthesisFile(root, "mixed.md", "x"), ["ap"], { provenance: "synthesis", grounds: ["ap"] });
  const onQ = ledger.route(root, synthesisFile(root, "onq.md", "y"), ["ap"], { provenance: "synthesis", grounds: ["ap#Q-1"] });
  fragment(root, "ap-model", { statements: [{ text: "stands on the mixed fragment", cites: [mixed] }, { text: "stands on an open question", cites: [onQ] }] });
  const items = answers.ground(root, "stands on");
  assert.equal(items.find(i => i.text.includes("mixed"))!.standing.kind, "claimed", "1 cited + 2 uncited → the weakest is claimed");
  assert.equal(items.find(i => i.text.includes("open question"))!.standing.kind, "claimed", "a question is not evidence");
  fragment(root, "ap", { statements: [{ text: "cited", cites: [src] }] });
  assert.equal(answers.ground(root, "stands on").find(i => i.text.includes("mixed"))!.standing.kind, "evidenced", "all statements cited → evidenced");
});

// B2 — law 6: the spend gate cannot be bypassed by a no, a typo, a negative, or a self-issued budget
test("B2 spend gate: a ruling must be a yes naming the spend; numbers must be finite and non-negative; budget set is gate-shaped", () => {
  const root = bareEngagement();
  record.budgetSet(root, 1000);
  record.gate(root, { kind: "spend", what: "big dispatch", ruling: "no — denied" });
  assert.throws(() => record.spend(root, 5000, 5000, "big dispatch"), (e: Error) => e.message.includes("big dispatch"), "a no is not a yes");
  record.gate(root, { kind: "spend", what: "other dispatch", ruling: "yes" });
  assert.throws(() => record.spend(root, 5000, 5000, "big dispatch"), (e: Error) => e.message.includes("big dispatch"), "a yes for something else does not unlock this");
  record.gate(root, { kind: "spend", what: "big dispatch", ruling: "yes" });
  record.spend(root, 5000, 5000, "big dispatch");
  assert.throws(() => record.spend(root, 5000, 5000, "big dispatch"), (e: Error) => e.message.includes("big dispatch"), "a gate is consumed once");
  assert.throws(() => record.budgetSet(root, Number("lots")), (e: Error) => e.message.includes("budget"));
  assert.throws(() => record.spend(root, -5, 1, "neg"), (e: Error) => e.message.includes("neg"));
  assert.throws(() => record.spend(root, Number.NaN, 1, "nan"), (e: Error) => e.message.includes("nan"));
  const lines = record.sessionLines(root);
  assert.ok(lines.some(l => l.verb === "gate" && l.detail.includes("budget") && l.detail.includes("1000")), "budget set leaves a gate-shaped line");
  assert.throws(() => record.gate(root, { kind: "design" as never, what: "x", ruling: "yes" }), (e: Error) => e.message.includes("design"), "only two gate kinds exist");
});

// B3 — law 7 / no deletions: re-routing never deletes
test("B3 route: a duplicate hash removes ONLY a fresh copy in _sources/new/; re-routing a registered path or a _synthesis/ artifact refuses by name and deletes nothing", () => {
  const root = bareEngagement();
  const p = stage(root, "policy.md", "policy");
  const src = ledger.route(root, p, ["ap"]);
  assert.throws(() => ledger.route(root, p, ["ap"]), (e: Error) => e.message.includes("policy.md") && e.message.includes(src));
  assert.ok(existsSync(p), "the registered source still exists");
  const pq = synthesisFile(root, "je.parquet", "PAR1");
  sidecarCard(root, pq, { title: "je", kind: "system-export", summary: "s", keyItems: [] });
  const s2 = ledger.route(root, pq, ["ap"], { provenance: "synthesis", grounds: [src] });
  assert.throws(() => ledger.route(root, pq, ["ap"], { provenance: "synthesis", grounds: [src] }), (e: Error) => e.message.includes(s2));
  assert.ok(existsSync(pq), "the work product still exists");
  const copy = stage(root, "policy-copy.md", "policy");
  assert.equal(ledger.route(root, copy, ["ap"]), src, "a fresh duplicate copy returns the existing id");
  assert.ok(!existsSync(copy) && existsSync(p), "…and only the copy is removed");
  const outside = join(root, "..", `outside-${Date.now()}.md`); writeFileSync(outside, "policy");
  assert.throws(() => ledger.route(root, outside, ["ap"]), (e: Error) => e.message.includes("outside"));
  assert.ok(existsSync(outside), "a file outside the engagement is never touched");
});

// B4 — render --out is confined to _synthesis/
test("B4 render: --out outside _synthesis/ is refused by name and nothing is written", async () => {
  const root = bareEngagement(); gitInit(root);
  pinShape(root, "information-request");
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "who approves?" }] }); const a = asks.propose(root, "Please send the approval matrix", ["ap#Q-1"]); asks.accept(root, a);
  const pad = readFileSync(join(root, "STATE.md"), "utf8");
  await assert.rejects(render.deliverable(root, "information-request", { out: "STATE.md" }), (e: Error) => e.message.includes("STATE.md") && e.message.includes("_synthesis"));
  assert.equal(readFileSync(join(root, "STATE.md"), "utf8"), pad);
  assert.ok(!existsSync(join(root, "STATE.card.yaml")));
});

// B5 — check never throws; taxonomy nodes are grammar-checked
test("B5 check: one malformed fragment or node is a grammar defect, not a crash; state and index keep working", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "p.md", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "ok", cites: [src] }] });
  writeFileSync(join(root, "capture/broken.yaml"), "slug: wrong-name\nstatements: [\n");
  writeFileSync(join(root, "capture/_taxonomy/bad.yaml"), "type: taxonomy-node\nscope: no slug here\n");
  const d = check.run(root);
  assert.ok(d.some(x => x.check === "grammar" && x.file === "capture/broken.yaml"));
  assert.ok(d.some(x => x.check === "grammar" && x.file === "capture/_taxonomy/bad.yaml"), "nodes are grammar-checked too");
  assert.doesNotThrow(() => desk.state(root)); assert.doesNotThrow(() => index.cards(root));
  assert.ok(desk.state(root).coverage.length >= 0);
});

// B6 — settlement is un-fakeable: propose resolves every question address
test("B6 ask propose: a question address that does not resolve is refused by name — an unresolvable question can never 'settle' by absence", () => {
  const root = bareEngagement();
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "who?" }] });
  assert.throws(() => asks.propose(root, "x", ["ap#Q-99"]), (e: Error) => e.message.includes("ap#Q-99"));
  assert.throws(() => asks.propose(root, "x", ["nope#Q-1"]), (e: Error) => e.message.includes("nope#Q-1"));
  assert.equal(asks.propose(root, "x", ["ap#Q-1"]), "ASK-001");
  // a register hand-edited to point at a phantom question is a check error
  const reg = join(root, "_registers/asks.yaml");
  writeFileSync(reg, readFileSync(reg, "utf8").replace("ap#Q-1", "ap#Q-77"));
  assert.ok(check.run(root).some(d => d.check === "registers" && d.message.includes("ap#Q-77")));
});

// B7 — a re-dropped file is never hidden, and retirement never overwrites
test("B7 unrouted compares full paths; a retired name re-dropped is visible; retirement refuses to overwrite a processed file", () => {
  const root = bareEngagement(); gitInit(root);
  const p = stage(root, "policy.md", "rev1");
  const s1 = ledger.route(root, p, ["ap"]);
  fragment(root, "ap", { statements: [{ text: "rev1 says", cites: [s1] }] });
  record.checkpoint(root, "retire rev1");
  assert.ok(existsSync(join(root, "_sources/processed/policy.md")));
  stage(root, "policy.md", "rev2");
  assert.deepEqual(ledger.status(root).unrouted, ["policy.md"], "the re-drop is visible");
  const s2 = ledger.route(root, join(root, "_sources/new/policy.md"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "rev1 says", cites: [s1] }, { text: "rev2 says", cites: [s2] }] });
  assert.throws(() => record.checkpoint(root, "retire rev2"), (e: Error) => e.message.includes("policy.md"), "never overwrite a retired file");
  assert.equal(readFileSync(join(root, "_sources/processed/policy.md"), "utf8"), "rev1", "rev1 intact");
});

// B8 — client-facing renders never carry closed questions
test("B8 open-questions builder excludes questions closed as not-the-client's and questions of closed asks", () => {
  const root = bareEngagement();
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "PUBLIC question" }, { id: "Q-2", text: "INTERNAL not for the client" }, { id: "Q-3", text: "WITHDRAWN ask's question" }] });
  asks.close(root, "ap#Q-2", "internal");
  const a = asks.propose(root, "withdrawn", ["ap#Q-3"]); asks.close(root, a, "withdrawn");
  const out = render.build(root, { views: [{ id: "open", builder: "open-questions" }] }).get("open")!;
  assert.ok(out.includes("PUBLIC") && !out.includes("INTERNAL") && !out.includes("WITHDRAWN"));
});

// B9 — skill parameters reach the brief from the CLI
test("B9 cli brief: --param k=v (repeatable) lands in the brief's Parameters block", async () => {
  const root = bareEngagement();
  const out: string[] = []; const log = console.log; console.log = (s: string) => { out.push(String(s)); };
  try { assert.equal(await main(["brief", "source-read", "--param", "question=Who signs off?", "--param", "sources=SRC-001", "--root", root]), 0); }
  finally { console.log = log; }
  const b = out.join("\n");
  assert.ok(b.includes("- question: Who signs off?") && b.includes("- sources: SRC-001"));
});

// B10 — the installed folder can execute the prompt: pin and skill-save verbs; budget set documented; system.md present
test("B10 the sitting procedure is executable on an installed root: `consult pin`, `consult skill save`, agents/system.md installed", async () => {
  const root = bareEngagement(); gitInit(root);
  const err: string[] = []; const e0 = console.error; console.error = (s: string) => { err.push(String(s)); };
  try {
    assert.equal(await main(["pin", "information-request", "--root", root]), 0);
    assert.ok(existsSync(join(root, "_definitions/information-request.yaml")));
    assert.equal(await main(["pin", "no-such-shape", "--root", root]), 2);
    assert.match(err.join("\n"), /no-such-shape/);
    const sk = join(root, "draft-skill.yaml");
    writeFileSync(sk, "contract: v1\nname: my-scan\nmission: tuned scan\nreads: [sources]\nwrites: []\nreturns: [flags]\nruntime: prompt\ncontextContract: []\nreturnContract: []\nrules: []\nrecommendedClass: haiku\norigin: engagement\nvariantOf: intake-scan\n");
    assert.equal(await main(["skill", "save", sk, "--root", root]), 0);
    assert.ok(existsSync(join(root, "_skills/my-scan.yaml")));
    assert.equal(brief.skill(root, "my-scan").variantOf, "intake-scan");
  } finally { console.error = e0; }
  const { install } = await import("../harness/install.ts");
  const live = bareEngagement(); install(live);
  assert.ok(existsSync(join(live, "agents/system.md")), "the seat's second read exists where the prompt says");
  assert.ok(readFileSync(join(live, "CLAUDE.md"), "utf8").includes("consult budget set"), "the prompt names the budget verb");
});

// follow-ups from review A
test("an ask names QUESTION records only: a control callout with the same id cannot be asked about or settle by removal", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "capture/ap.yaml"), `slug: ap\ntype: process-step\nstatements: []\nquestions:\n  - id: Q-1\n    text: "who?"\ncallouts:\n  - kind: control\n    id: C-1\n    text: "a control"\n`);
  assert.throws(() => asks.propose(root, "x", ["ap#C-1"]), (e: Error) => e.message.includes("ap#C-1"));
  assert.equal(asks.propose(root, "y", ["ap#Q-1"]), "ASK-001");
});

test("ledger.status survives a hand-broken entry (intent not a list): the read describes, check names the defect", () => {
  const root = bareEngagement();
  ledger.route(root, stage(root, "p.md", "policy"), ["ap"]);
  const book = join(root, "_sources/sources.yaml");
  writeFileSync(book, readFileSync(book, "utf8").replace(/intent:\n\s+- ap/, "intent: ap"));
  assert.doesNotThrow(() => ledger.status(root));
  assert.doesNotThrow(() => desk.state(root));
  assert.ok(check.run(root).some(d => d.check === "registers" && d.message.includes("SRC-001") && d.message.includes("intent")));
});
