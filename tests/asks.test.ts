/** asks — four stored states; answered/settled DERIVED (A18). */
import { test } from "node:test";
import assert from "node:assert/strict";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as asks from "../src/asks.ts";

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

test("settlement is DERIVED and un-fakeable: citing the answering source where the question lives settles the ask", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  asks.accept(root, id); asks.sent(root);
  const { src } = asks.respond(root, stage(root, "reply.pdf", "policy attached"), [id]);
  // the fold-in: the consultant's direct capture edit answers Q-1, citing the response
  fragment(root, "ap-approval", { statements: [{ text: "Under $10k, team leads approve", cites: [src] }] });
  assert.equal(asks.unsettled(root).length, 0, "the capture diff IS the settlement");
});

test("close is the one withdrawal: an ask, or a question ruled not-the-client's, with a durable reason", () => {
  const root = bareEngagement();
  const id = withQuestion(root);
  asks.close(root, id, "objective changed; no longer needed");
  assert.equal(asks.entriesOf(root, "closed")[0]!.closedReason, "objective changed; no longer needed");
});
