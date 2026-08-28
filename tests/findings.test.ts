/** findings — where the brain may hold an opinion. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as findings from "../src/findings.ts";

test("propose refuses unresolvable grounds BY NAME", () => {
  const root = bareEngagement();
  assert.throws(() => findings.propose(root, "single point of failure at Dana", ["SRC-404"]),
    (e: Error) => e.message.includes("SRC-404"));
});

test("accepted findings render; rejection is terminal and KEPT as case law", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "p.pdf", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "Dana is sole approver", cites: [src] }] });
  const a = findings.propose(root, "approval bottleneck at Dana", [src]);
  const b = findings.propose(root, "reviews are too frequent", [src]);
  findings.accept(root, a);
  findings.reject(root, b, "cadence is client preference, not a defect");
  assert.deepEqual(findings.renderable(root).map(f => f.id), [a]);
  const all = findings.entriesOf(root);
  assert.equal(all.length, 2, "the rejection is kept");
  const rej = all.find(f => f.id === b)!;
  assert.equal(rej.status, "rejected");
  assert.equal(rej.rejectedReason, "cadence is client preference, not a defect");
});
