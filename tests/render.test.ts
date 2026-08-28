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

test("the shipped registry holds exactly the three the two definitions need", () => {
  assert.deepEqual([...render.BUILDERS.keys()].sort(),
    ["client-asks", "findings-by-theme", "information-requests"]);
});
