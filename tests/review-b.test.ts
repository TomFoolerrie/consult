/** review round B (2026-09-10) — the eleven findings, tests first. Each test names the law or the claim it protects. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { existsSync, readFileSync, writeFileSync, mkdirSync, rmSync, mkdtempSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { execSync } from "node:child_process";
import { bareEngagement, stage, fragment, pinShape, synthesisFile, sidecarCard } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as record from "../src/record.ts";
import * as asks from "../src/asks.ts";
import * as findings from "../src/findings.ts";
import * as render from "../src/render.ts";
import * as desk from "../src/desk.ts";
import * as brief from "../src/brief.ts";
import * as definitions from "../src/definitions.ts";
import { main, init } from "../src/cli.ts";

const gitInit = (root: string) => execSync("git init -q && git add -A && git commit -qm seed", { cwd: root });
function withQuestion(root: string, slug = "ap-approval"): string {
  fragment(root, slug, { questions: [{ id: "Q-1", text: "who approves?" }] });
  return asks.propose(root, "Please send the approval matrix", [`${slug}#Q-1` as never]);
}
/** break the session record so record.gate() fails: _registers/sessions as a FILE makes mkdirSync throw */
function breakSessions(root: string): void {
  rmSync(join(root, "_registers/sessions"), { recursive: true, force: true });
  writeFileSync(join(root, "_registers/sessions"), "not a directory\n");
}
const capture = (fn: () => Promise<number> | number) => {
  const out: string[] = []; const err: string[] = [];
  const lo = console.log, le = console.error;
  console.log = (s: unknown) => { out.push(String(s)); }; console.error = (s: unknown) => { err.push(String(s)); };
  const done = (code: number) => { console.log = lo; console.error = le; return { code, out: out.join("\n"), err: err.join("\n") }; };
  const r = fn();
  return r instanceof Promise ? r.then(done, e => { console.log = lo; console.error = le; throw e; }) : Promise.resolve(done(r));
};

// C1 — law 7: no half-state. The audit line lands FIRST; the register write is LAST.
test("C1 accept and sent: the audit line first, the register last — a failed gate leaves the ask untouched", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  breakSessions(root);
  assert.throws(() => asks.accept(root, id as never));
  assert.equal(asks.entriesOf(root)[0]!.status, "proposed", "no accepted ask without its audit line");
  rmSync(join(root, "_registers/sessions"));
  asks.accept(root, id as never);
  assert.equal(asks.entriesOf(root)[0]!.status, "accepted");
  breakSessions(root);
  assert.throws(() => asks.sent(root, [id as never]));
  assert.equal(asks.entriesOf(root)[0]!.status, "accepted", "no sent ask without its crossing line");
});

// C1 — respond: route first (idempotent by hash), then stamp, then the register; and it answers only a SENT ask
test("C1 respond: a response to an ask that is not sent is a named refusal; a failed route leaves the register unstamped", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  assert.throws(() => asks.respond(root, stage(root, "early.md", "x"), [id as never]),
    (e: Error) => e.message.includes(id) && e.message.includes("proposed"), "a proposed ask has not been asked");
  asks.accept(root, id as never);
  assert.throws(() => asks.respond(root, stage(root, "early2.md", "y"), [id as never]),
    (e: Error) => e.message.includes(id) && e.message.includes("accepted"));
  asks.sent(root, [id as never]);
  assert.throws(() => asks.respond(root, join(root, "_sources/new/absent.md"), [id as never]));
  assert.equal(asks.entriesOf(root)[0]!.answeredBy.length, 0, "route refused → nothing stamped");
  const { src } = asks.respond(root, stage(root, "reply.md", "the matrix"), [id as never]);
  assert.deepEqual([...asks.entriesOf(root)[0]!.answeredBy], [src]);
  asks.close(root, id as never, "withdrawn");
  assert.throws(() => asks.respond(root, stage(root, "late.md", "z"), [id as never]),
    (e: Error) => e.message.includes(id) && e.message.includes("closed"));
});

// C2 — the gate records the HUMAN's words
test("C2 accept carries the human's ruling: the gate line quotes it, defaulting to \"accepted\"", () => {
  const root = bareEngagement();
  const a = withQuestion(root, "ap-a"); asks.accept(root, a as never, "yes — but drop the second item");
  const b = withQuestion(root, "ap-b"); asks.accept(root, b as never);
  const lines = record.sessionLines(root).filter(l => l.verb === "gate");
  assert.ok(lines.some(l => l.gate?.ruling === "yes — but drop the second item" && l.gate.what.includes(a)), "the human's words, on the ask's gate line");
  assert.ok(lines.some(l => l.gate?.ruling === "accepted" && l.gate.what.includes(b)), "default ruling");
});

// C3 — rejection is terminal (findings doctrine)
test("C3 findings: rejection is TERMINAL — accepting a rejected finding is refused by name; grounds are mandatory", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "p.md", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "cited", cites: [src] }] });
  const f = findings.propose(root, "duplicates are unreviewed", [src as never]);
  findings.reject(root, f, "not supported");
  assert.throws(() => findings.accept(root, f), (e: Error) => e.message.includes(f) && e.message.includes("rejected"));
  assert.equal(findings.entriesOf(root)[0]!.status, "rejected", "case law is kept, unchanged");
  assert.throws(() => findings.propose(root, "ungrounded", []), (e: Error) => e.message.includes("ground"));
});

// C4 — fail loud: the worker's own refusal reaches the human
test("C4 render: a worker refusal on stdout ({error}) is surfaced by name, never \"no output\"", async () => {
  const root = bareEngagement(); gitInit(root);
  pinShape(root, "information-request");
  fragment(root, "ap-approval", { questions: [{ id: "Q-1", text: "who approves?" }] });
  asks.accept(root, asks.propose(root, "Please send the matrix", ["ap-approval#Q-1"]) as never);
  const w = join(mkdtempSync(join(tmpdir(), "worker-")), "refuser.py");
  writeFileSync(w, 'import json,sys\nsys.stdin.read()\nprint(json.dumps({"error": "skin requires title-page, which this format cannot draw"}))\nsys.exit(2)\n');
  await assert.rejects(render.deliverable(root, "information-request", { worker: w }),
    (e: Error) => e.message.includes("title-page, which this format cannot draw"));
});

// C5a — align the gap record with the builder: the information request carries ACCEPTED asks
test("C5 serviceability: `asks: accepted` needs at least one ACCEPTED ask — a sent-only register is not serviceable", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  asks.accept(root, id as never); asks.sent(root, [id as never]);
  const defn = definitions.load("information-request");
  assert.ok(definitions.serviceability(defn, root).some(g => g.binding === "asks"), "sent-only leaves the Requests section empty");
  const id2 = withQuestion(root, "ap-payment"); asks.accept(root, id2 as never);
  assert.ok(!definitions.serviceability(defn, root).some(g => g.binding === "asks"));
});

// C5b/c — fail loud at load; a missing skin.requires is a default, not a crash
test("C5 definitions load: an unknown block kind is refused BY NAME; skin.requires defaults to []", () => {
  const root = bareEngagement();
  mkdirSync(join(root, "_definitions"), { recursive: true });
  writeFileSync(join(root, "_definitions/odd-shape.yaml"),
    "name: odd-shape\ntitle: Odd\nblocks:\n  - { kind: static, id: a, title: A, text: x }\n  - { kind: sparkle, id: b, title: B }\nbindings: {}\nskin: { format: docx }\n");
  assert.throws(() => definitions.load("odd-shape", root), (e: Error) => e.message.includes("sparkle") && e.message.includes("b"));
  writeFileSync(join(root, "_definitions/plain-shape.yaml"),
    "name: plain-shape\ntitle: Plain\nblocks:\n  - { kind: static, id: a, title: A, text: x }\nbindings: {}\nskin: { format: docx }\n");
  const d = definitions.load("plain-shape", root);
  assert.deepEqual([...d.skin.requires], []);
  assert.doesNotThrow(() => render.assembleJob(d, definitions.compilePlan(d, root), new Map(), { draft: false }));
});

// C5d — no "all quiet" by damage, and state() never throws: a bad pin is a health note
test("C5 state: a pin naming an unknown definition is a not-serviceable shape with a note — state() never throws", () => {
  const root = bareEngagement();
  mkdirSync(join(root, "_definitions"), { recursive: true });
  writeFileSync(join(root, "_definitions/ghost.yaml"), "pin: ghost\n");
  const s = desk.state(root);
  const p = s.pinnedShapes.find(p => p.name === "ghost")!;
  assert.equal(p.serviceable, false);
  assert.ok(p.note?.includes("ghost"), "the note names the load error");
  assert.doesNotThrow(() => desk.report(root));
  assert.doesNotThrow(() => desk.needs(root));
});

test("C5 definitions.pinned: a pin whose file name and pin/name disagree is refused BY NAME", () => {
  const root = bareEngagement();
  mkdirSync(join(root, "_definitions"), { recursive: true });
  writeFileSync(join(root, "_definitions/requests.yaml"), "pin: information-request\n");
  assert.throws(() => definitions.pinned(root), (e: Error) => e.message.includes("requests") && e.message.includes("information-request"));
  const s = desk.state(root);
  assert.equal(s.pinnedShapes.find(p => p.name === "requests")!.serviceable, false, "…and state reports it, never throws");
});

// C6 — the named repair must be runnable: `consult init`
test("C6 locate: an engagement-shaped tree without _sources/ names `init` as its repair, and init is the one verb allowed", async () => {
  const root = bareEngagement();
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "who?" }] });
  rmSync(join(root, "_sources"), { recursive: true });
  const h = desk.locate(root).health;
  assert.equal(h.kind === "contradiction" && h.repair, "init");
  const blocked = await capture(() => main(["ask", "propose", "x", "--questions", "ap#Q-1", "--root", root]));
  assert.equal(blocked.code, 2);
  assert.match(blocked.err, /init/);
  const ran = await capture(() => main(["init", "--root", root]));
  assert.equal(ran.code, 0);
  for (const d of ["new", "processed", "parked", "scans"]) assert.ok(existsSync(join(root, "_sources", d)), d);
  assert.ok(existsSync(join(root, "_sources/sources.yaml")));
  assert.equal(desk.locate(root).health.kind, "ok");
  const again = await capture(() => main(["init", "--root", root]));
  assert.equal(again.code, 0);
  assert.match(again.out, /already|nothing/i, "init on a healthy root says it did nothing");
  assert.deepEqual(init(root), [], "…and it is a no-op");
});

// C6 — desk reads the LOCATED root
test("C6 desk.state(subdir): the located root is what is read — not the subdirectory", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "p.md", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "cited", cites: [src] }] });
  stage(root, "later.md", "unrouted");
  const sub = join(root, "capture");
  const s = desk.state(sub);
  assert.equal(s.health.kind, "ok");
  assert.deepEqual(s.unrouted, ["later.md"], "the engagement's own unrouted, read from the located root");
  assert.ok(desk.coverage(sub).length >= 0);
  assert.doesNotThrow(() => desk.needs(sub));
});

// C7 — the parser: an option value is never a positional
test("C7 cli positionals: `--root X` is never taken as an id — ask sent, checkpoint, spend, answer with options first", async () => {
  const root = bareEngagement(); gitInit(root);
  const id = withQuestion(root); asks.accept(root, id as never);
  const sent = await capture(() => main(["ask", "sent", "--root", root]));
  assert.equal(sent.code, 0, sent.err);
  assert.equal(sent.out.trim(), "1", "all accepted asks swept — the root path is not an ask id");
  assert.equal(asks.entriesOf(root, "sent").length, 1);
  const ans = await capture(() => main(["answer", "--root", root, "approves"]));
  assert.equal(ans.code, 0, ans.err);
  const cp = await capture(() => main(["checkpoint", "--root", root, "sitting one"]));
  assert.equal(cp.code, 0, cp.err);
  assert.match(execSync("git log -1 --pretty=%s", { cwd: root }).toString(), /consult: sitting one/);
  await capture(() => main(["budget", "set", "1000", "--root", root]));
  const sp = await capture(() => main(["spend", "--root", root, "--estimate", "10", "--actual", "12", "a dispatch"]));
  assert.equal(sp.code, 0, sp.err);
  assert.ok(record.sessionLines(root).some(l => l.verb === "spend" && l.detail === "a dispatch"), "the label is the positional, not a flag");
});

test("C7 cli: with no engagement, the refusal names a verb that exists in the installed root", async () => {
  const r = await capture(() => main([]));
  assert.equal(r.code, 2);
  assert.match(r.err, /consult init/);
  assert.ok(!r.err.includes("DESIGN.md"), "DESIGN.md is not installed into an engagement");
});

// C8 — one card per artifact (A22): a sidecar stem belongs to one artifact
test("C8 render: a sidecar stem another artifact already owns is a named refusal — no card is overwritten", async () => {
  const root = bareEngagement(); gitInit(root);
  pinShape(root, "information-request");
  fragment(root, "ap-approval", { questions: [{ id: "Q-1", text: "who approves?" }] });
  asks.accept(root, asks.propose(root, "Please send the matrix", ["ap-approval#Q-1"]) as never);
  const pq = synthesisFile(root, "je.parquet", "PAR1");
  sidecarCard(root, pq, { title: "je", kind: "system-export", summary: "the journal entries", keyItems: [] });
  const before = readFileSync(join(root, "_synthesis/je.card.yaml"), "utf8");
  await assert.rejects(render.deliverable(root, "information-request", { out: "_synthesis/je.docx" }),
    (e: Error) => e.message.includes("je.parquet") && e.message.includes("je.card.yaml"));
  assert.equal(readFileSync(join(root, "_synthesis/je.card.yaml"), "utf8"), before, "the other artifact's card is intact");
  assert.ok(!existsSync(join(root, "_synthesis/je.docx")), "and nothing was written");
});

// C9 — a dry run describes; it never mutates
test("C9 checkpoint --dry-run mutates nothing: no retirement, no session line, no commit", () => {
  const root = bareEngagement(); gitInit(root);
  const src = ledger.route(root, stage(root, "p.md", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "cited", cites: [src] }] });
  const head = execSync("git rev-parse HEAD", { cwd: root }).toString().trim();
  const dry = record.checkpoint(root, "dry", true);
  assert.deepEqual(dry.retired, [src], "it says what WOULD retire");
  assert.ok(existsSync(join(root, "_sources/new/p.md")) && !existsSync(join(root, "_sources/processed/p.md")));
  assert.equal(record.sessionLines(root).filter(l => l.verb === "checkpoint").length, 0);
  assert.equal(execSync("git rev-parse HEAD", { cwd: root }).toString().trim(), head);
});

// C10a — a skill's list fields are validated where the skill is READ, not only where it is written
test("C10 brief.skill: a skill whose rules are a string is refused BY NAME, never composed into \"not iterable\"", () => {
  const root = bareEngagement();
  mkdirSync(join(root, "_skills"), { recursive: true });
  writeFileSync(join(root, "_skills/bent.yaml"),
    "name: bent\nmission: do a thing\nwrites: null\ncontextContract: []\nreturnContract: []\nrules: be careful\nrecommendedClass: haiku\norigin: engagement\n");
  assert.throws(() => brief.skill(root, "bent"), (e: Error) => e.message.includes("bent") && e.message.includes("rules"));
});

// C10b/c — the brief carries what its contract claims
test("C10 compose: the brief carries the Objective and the pad's standing guidance, and every index line names its content path", () => {
  const root = bareEngagement();
  writeFileSync(join(root, "OBJECTIVE.md"), "# objective\nHelp Meridian see its AP process whole.\n");
  writeFileSync(join(root, "STATE.md"), "# state pad\n## now\nSitting 2.\n## human's standing guidance\nAsk before contacting Marcus.\n## precedent\n(none)\n");
  const src = ledger.route(root, stage(root, "p.md", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "cited", cites: [src] }] });
  const b = brief.compose(root, "source-read", "haiku", {});
  assert.match(b, /## Objective\n[\s\S]*Meridian/);
  assert.match(b, /## Standing guidance\nAsk before contacting Marcus\./);
  assert.ok(!b.includes("## precedent"), "the guidance block is the guidance heading's text only");
  const captureLine = b.split("\n").find(l => l.startsWith("capture  ap"))!;
  assert.match(captureLine, /content: capture\/ap\.yaml/, "an index line names its content path");
  const bare = brief.compose(bareEngagement(), "source-read", "haiku", {});
  assert.match(bare, /## Standing guidance\n\(none\)/);
});

// C11 — the scripted client matches basenames exactly; a second install never clobbers the human's settings
test("C11 harness: alreadyDelivered is an exact basename match; a second install keeps settings.json and regenerates CLAUDE.md", async () => {
  const { deliver } = await import("../harness/client.ts");
  const { install } = await import("../harness/install.ts");
  const root = bareEngagement();
  const dir = mkdtempSync(join(tmpdir(), "script-")); mkdirSync(join(dir, "responses"));
  writeFileSync(join(dir, "responses/policy.md"), "the policy");
  writeFileSync(join(dir, "script.yaml"), "responses:\n  - { topic: policy, match: [policy], file: responses/policy.md, behavior: answer }\n");
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "policy?" }] });
  const id = asks.propose(root, "Please send the policy", ["ap#Q-1"]);
  asks.accept(root, id as never); asks.sent(root, [id as never]);
  // a routed ap-policy.md must not suppress the scripted policy.md (substring collision)
  ledger.route(root, stage(root, "ap-policy.md", "an unrelated file"), ["ap"]);
  assert.deepEqual(deliver(root, join(dir, "script.yaml")).map(d => d.ask), [id]);
  assert.ok(existsSync(join(root, "_sources/new/policy.md")));
  assert.equal(deliver(root, join(dir, "script.yaml")).length, 0, "still idempotent");

  const live = bareEngagement(); install(live);
  const custom = JSON.stringify({ permissions: { allow: ["Bash(consult:*)", "Bash(rg:*)"] } }, null, 2) + "\n";
  writeFileSync(join(live, ".claude/settings.json"), custom);
  writeFileSync(join(live, "CLAUDE.md"), "clobbered\n");
  install(live);
  assert.equal(readFileSync(join(live, ".claude/settings.json"), "utf8"), custom, "the human's settings survive");
  assert.ok(readFileSync(join(live, "CLAUDE.md"), "utf8").includes("THE CONSULTANT"), "the seat is the repo's, always regenerated");
  assert.ok(readdirSync(join(live, ".claude/agents")).length > 0);
});
