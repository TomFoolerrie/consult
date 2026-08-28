/** cli — library first: exit codes, and the contradiction blockade. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { rmSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement } from "./helpers.ts";
import * as cli from "../src/cli.ts";

test("0 on success, 2 on a named refusal — never a stack trace to the user", async () => {
  const root = bareEngagement();
  assert.equal(await cli.main(["state", "--root", root]), 0);
  assert.equal(await cli.main(["route", "/does/not/exist", "--root", root]), 2);
});

test("a standing contradiction blocks state-changing verbs — an invocation valid WITHOUT the contradiction", async () => {
  const good = bareEngagement();
  // prove the invocation itself is valid on a healthy engagement first
  const { fragment } = await import("./helpers.ts");
  fragment(good, "ap", { questions: [{ id: "Q-1", text: "who?" }] });
  assert.equal(await cli.main(["ask", "propose", "send the policy", "--questions", "ap#Q-1", "--root", good]), 0);
  // now the same invocation against a contradicted root
  const bad = bareEngagement();
  fragment(bad, "ap", { questions: [{ id: "Q-1", text: "who?" }] });
  rmSync(join(bad, "_sources"), { recursive: true });
  assert.equal(await cli.main(["ask", "propose", "send the policy", "--questions", "ap#Q-1", "--root", bad]), 2, "blocked by the contradiction, not the args");
  assert.equal(await cli.main(["state", "--root", bad]), 0, "reads still describe");
});

test("no engagement root at all: exit 2 with a refusal naming the marker — never a stack trace", async () => {
  const { mkdtempSync } = await import("node:fs");
  const { tmpdir } = await import("node:os");
  const plain = mkdtempSync(join(tmpdir(), "not-an-engagement-"));
  assert.equal(await cli.main(["state", "--root", plain]), 2);
});
