/** cli — library first: exit codes, the contradiction blockade, and the SHAPE of a refusal.
 *
 * Every refusal the user can see is asserted on stderr here: it begins
 * `refused:`, it names the offender, and it carries no stack frame. A
 * thrown Error reaching the user as a trace is the failure mode this
 * file exists to catch (law 7 — fail loud, and loudly means legibly).
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { rmSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement } from "./helpers.ts";
import * as cli from "../src/cli.ts";

/** run a verb capturing stdout/stderr — refusals are user-facing text, so we assert on them */
async function run(argv: string[]): Promise<{ code: number; out: string; err: string }> {
  const out: string[] = [], err: string[] = [];
  const [wasLog, wasErr] = [console.log, console.error];
  console.log = (...a: unknown[]) => { out.push(a.join(" ")); };
  console.error = (...a: unknown[]) => { err.push(a.join(" ")); };
  try { return { code: await cli.main(argv), out: out.join("\n"), err: err.join("\n") }; }
  finally { console.log = wasLog; console.error = wasErr; }
}

/** the refusal contract: `refused:` first, no stack frame, and it names the offender */
function assertRefusal(err: string, offender: string) {
  assert.ok(err.length, "a refusal is never silent");
  for (const line of err.split("\n").filter(Boolean)) {
    assert.match(line, /^refused: /, `every refusal line starts with "refused:" — got: ${line}`);
    assert.ok(!/\bat .*:\d+:\d+/.test(line) && !line.includes("    at "),
      `a refusal carries no stack frame — got: ${line}`);
  }
  assert.ok(err.includes(offender), `the refusal names the offender (${offender}) — got: ${err}`);
}

test("0 on success, 2 on a named refusal — never a stack trace to the user", async () => {
  const root = bareEngagement();
  const ok = await run(["state", "--root", root]);
  assert.equal(ok.code, 0);
  assert.equal(ok.err, "", "a success says nothing on stderr");
  // a refusal from inside a module, surfaced through the catch-all
  const bad = await run(["route", "/does/not/exist", "--root", root]);
  assert.equal(bad.code, 2);
  assertRefusal(bad.err, "/does/not/exist");
  // and a refusal from the parser itself
  const unknown = await run(["frobnicate", "--root", root]);
  assert.equal(unknown.code, 2);
  assertRefusal(unknown.err, "frobnicate");
  const badSub = await run(["ask", "frobnicate", "--root", root]);
  assert.equal(badSub.code, 2);
  assertRefusal(badSub.err, "frobnicate");
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
  const blocked = await run(["ask", "propose", "send the policy", "--questions", "ap#Q-1", "--root", bad]);
  assert.equal(blocked.code, 2, "blocked by the contradiction, not the args");
  assertRefusal(blocked.err, "_sources");
  assert.match(blocked.err, /repair verb: \S+/, "a blockade always names the one verb that may run");
  const reads = await run(["state", "--root", bad]);
  assert.equal(reads.code, 0, "reads still describe");
});

/** a temp dir that is not an engagement */
async function plainDir(): Promise<string> {
  const { mkdtempSync } = await import("node:fs");
  const { tmpdir } = await import("node:os");
  return mkdtempSync(join(tmpdir(), "not-an-engagement-"));
}

test("locate: no engagement root at all — exit 2, and the refusal names the MARKER that is missing", async () => {
  const r = await run(["state", "--root", await plainDir()]);
  assert.equal(r.code, 2);
  assertRefusal(r.err, "_sources");
  assert.match(r.err, /no engagement here/, "it says what is wrong, not just that something is");
});

test("locate: the refusal names the PATH it looked at — the offender here is the FOLDER",
  async () => {
  const plain = await plainDir();
  const r = await run(["state", "--root", plain]);
  assert.equal(r.code, 2);
  assert.ok(r.err.includes(plain),
    `a consultant must be able to see WHICH folder was rejected — got: ${r.err}`);
});
