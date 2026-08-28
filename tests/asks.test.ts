/** asks — four stored states; answered/settled DERIVED (A18). */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as asks from "../src/asks.ts";
import * as ledger from "../src/ledger.ts";
import * as check from "../src/check.ts";

function withQuestion(root: string) {
  fragment(root, "ap-approval", { questions: [{ id: "Q-1", text: "Who approves under $10k?" }] });
  return asks.propose(root, "Could you send the AP approval policy?", ["ap-approval#Q-1"]);
}

test("propose mints ASK ids; audience/artifact optional (guidance, not schema)", () => {
  const root = bareEngagement();
  assert.equal(withQuestion(root), "ASK-001");
});

test("a question id appears in the register exactly once — a second ask naming it is refused by name", () => {
  const root = bareEngagement();
  withQuestion(root);
  assert.throws(() => asks.propose(root, "again?", ["ap-approval#Q-1"]),
    (e: Error) => e.message.includes("Q-1"));
});

test("lifecycle stores only what the folder cannot show: sent() sweeps accepted only, selectively if asked", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  assert.equal(asks.sent(root), 0, "nothing accepted yet");
  asks.accept(root, id);
  assert.equal(asks.sent(root, [id]), 1);
  assert.equal(asks.entriesOf(root, "sent").length, 1);
});

test("respond is ARRIVAL: routes the file, stamps answeredBy — and does NOT settle", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  asks.accept(root, id); asks.sent(root);
  const { src, answered } = asks.respond(root, stage(root, "reply.pdf", "policy attached"), [id]);
  assert.equal(answered[0]!.answeredBy[0], src);
  assert.equal(asks.unsettled(root).length, 1, "answered-but-unsettled is a visible debt");
});

test("settlement is DERIVED and un-fakeable: a citing statement in the question's fragment settles — question kept, check clean", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  asks.accept(root, id); asks.sent(root);
  const { src } = asks.respond(root, stage(root, "reply.pdf", "policy attached"), [id]);
  // the fold-in KEEPS the question and adds the citing statement
  fragment(root, "ap-approval", {
    statements: [{ text: "Under $10k, team leads approve", cites: [src] }],
    questions: [{ id: "Q-1", text: "Who approves under $10k?" }],
  });
  assert.equal(asks.unsettled(root).length, 0, "the capture diff IS the settlement");
  assert.deepEqual(check.run(root).filter(d => d.severity === "error"), [], "the settled state is check-clean");
});

test("answeredBy ACCUMULATES: one ask answered across two responses; respond's intent is the questions' slugs", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  asks.accept(root, id); asks.sent(root);
  const one = asks.respond(root, stage(root, "part1.pdf", "half the policy"), [id]);
  const two = asks.respond(root, stage(root, "part2.pdf", "the other half"), [id]);
  const ask = asks.entriesOf(root).find(a => a.id === id)!;
  assert.deepEqual([...ask.answeredBy], [one.src, two.src]);
  const entry = ledger.status(root).entries.find(e => e.id === one.src)!;
  assert.deepEqual([...entry.intent], ["ap-approval"], "respond routes with the answered questions' slugs");
});

test("accept and sent are record.gate's ask-shaped callers — the yes and the crossing land in the session record", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  asks.accept(root, id);
  asks.sent(root, [id]);
  const dir = join(root, "_registers/sessions");
  const lines = readdirSync(dir).map(f => readFileSync(join(dir, f), "utf8")).join("\n");
  assert.ok(lines.includes(id), "gate lines name the ask");
  assert.ok(lines.includes("send"), "kind: send recorded");
});

test("close is the one withdrawal: an ask, or a question ruled not-the-client's, with a durable reason", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  asks.close(root, id, "objective changed; no longer needed");
  assert.equal(asks.entriesOf(root, "closed")[0]!.closedReason, "objective changed; no longer needed");
});
