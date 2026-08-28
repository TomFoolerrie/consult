/** answers — the product: grounded material with COMPUTED standings. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { bareEngagement, stage, fragment } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as answers from "../src/answers.ts";

test("the four standings derive from the record's physical shape", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "chart.pdf", "org chart"), ["org-structure"]);
  const s2 = ledger.route(root, stage(root, "dept.pdf", "dept chart"), ["org-structure"]);
  fragment(root, "org-structure", {
    statements: [
      { text: "Dana approves invoices over $10k", cites: [src] },   // evidenced
      { text: "The team prefers quarterly reviews" },               // claimed (no cite)
    ],
    questions: [
      { id: "Q-1", text: "Does Ops report to CFO or COO?", sources: [src, s2] }, // contested
      { id: "Q-2", text: "Who owns vendor onboarding?" },                        // absent
    ],
  });
  const g = answers.ground(root, "org-structure");
  const kinds = g.map(i => i.standing.kind);
  assert.ok(kinds.includes("evidenced") && kinds.includes("claimed") &&
            kinds.includes("contested") && kinds.includes("absent"));
  const absent = g.find(i => i.standing.kind === "absent")!;
  assert.equal((absent.standing as any).question, "org-structure#Q-2",
    "absent carries the question's ADDRESS — phrasing the ask is the consultant's job");
});

test("a synthesis source never upgrades standing: the chain resolves to its grounds", () => {
  const root = bareEngagement();
  const model = ledger.route(root, stage(root, "model.md", "org model"), ["org-structure"],
    { provenance: "synthesis", grounds: [] }); // grounds empty = built from nothing citable
  fragment(root, "org-structure", { statements: [{ text: "Consolidated: Dana leads AP", cites: [model] }] });
  const g = answers.ground(root, "org-structure");
  assert.equal(g[0]!.standing.kind, "claimed",
    "citing your own ungrounded summary cannot make a statement evidenced");
});

test("cite resolves grounds or refuses BY NAME", () => {
  const root = bareEngagement();
  assert.throws(() => answers.cite(root, ["SRC-999"]), (e: Error) => e.message.includes("SRC-999"));
});
