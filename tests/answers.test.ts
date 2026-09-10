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

test("synthesis inherits the WEAKEST ground's standing — ONE uncited statement in the ground fragment claims the whole chain", () => {
  const root = bareEngagement();
  const chart = ledger.route(root, stage(root, "chart.pdf", "org chart"), ["org-notes"]);
  // the ground fragment is MIXED: one cited statement, one uncited — the weakest wins.
  // (an all-uncited ground would pass on the first-statement branch alone and leave the
  //  minimum-over-statements logic, the thing actually under test, unexercised)
  fragment(root, "org-notes", {
    statements: [
      { text: "Dana signs the AP approval matrix", cites: [chart] },  // evidenced
      { text: "Team says Dana leads AP" },                            // claimed — the weak link
    ],
  });
  const model = ledger.route(root, stage(root, "model.md", "org model"), ["org-structure"],
    { provenance: "synthesis", grounds: ["org-notes"] });
  fragment(root, "org-structure", { statements: [{ text: "Consolidated: Dana leads AP", cites: [model] }] });
  const item = answers.ground(root, "org-structure").find(i => i.text.startsWith("Consolidated"))!;
  assert.equal(item.standing.kind, "claimed",
    "one uncited statement in the ground fragment claims the whole chain — no upgrade through your own summary");

  // and the SAME chain resolves UP the moment that last statement is cited — proof the
  // claimed standing came from the uncited statement, not from a broken chain.
  fragment(root, "org-notes", {
    statements: [
      { text: "Dana signs the AP approval matrix", cites: [chart] },
      { text: "Team says Dana leads AP", cites: [chart] },
    ],
  });
  const after = answers.ground(root, "org-structure").find(i => i.text.startsWith("Consolidated"))!;
  assert.equal(after.standing.kind, "evidenced", "all-cited ground — the chain carries evidence through");
  assert.deepEqual((after.standing as any).sources, [chart], "resolved to the primary artifact");
});

test("and the chain resolves UP when grounds are evidenced — building on your own work is first-class (A12)", () => {
  const root = bareEngagement();
  const src = ledger.route(root, stage(root, "chart.pdf", "org chart"), ["org-structure"]);
  fragment(root, "org-structure", { statements: [{ text: "Dana leads AP", cites: [src] }] });
  const model = ledger.route(root, stage(root, "model.md", "org model"), ["org-structure"],
    { provenance: "synthesis", grounds: [src] });
  fragment(root, "org-view", { statements: [{ text: "Summary: AP centralizes under Dana", cites: [model] }] });
  const item = answers.ground(root, "org-view").find(i => i.text.startsWith("Summary"))!;
  assert.equal(item.standing.kind, "evidenced", "grounded synthesis carries evidence through");
  assert.deepEqual((item.standing as any).sources, [src], "the chain resolves to the primary artifact");
});

test("cite resolves grounds or refuses BY NAME", () => {
  const root = bareEngagement();
  assert.throws(() => answers.cite(root, ["SRC-999"]), (e: Error) => e.message.includes("SRC-999"));
});
