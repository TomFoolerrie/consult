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

test("a standing contradiction blocks state-changing verbs — except the repair its own field names", async () => {
  const root = bareEngagement();
  rmSync(join(root, "_sources"), { recursive: true });
  assert.equal(await cli.main(["ask", "propose", "x", "--root", root]), 2, "blocked");
  assert.equal(await cli.main(["state", "--root", root]), 0, "reads still describe");
});
