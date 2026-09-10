/** desk — the ONE derived picture, pure. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { rmSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement, stage, fragment, node, pinShape } from "./helpers.ts";
import * as ledger from "../src/ledger.ts";
import * as desk from "../src/desk.ts";

test("locate walks up to the _sources/ marker; a marker-less engagement-shaped tree is a NAMED contradiction with a repair", () => {
  const root = bareEngagement();
  assert.equal(desk.locate(join(root, "capture")).root, root);
  rmSync(join(root, "_sources"), { recursive: true });
  const { health } = desk.locate(root);
  assert.equal(health.kind, "contradiction");
  assert.ok((health as any).repair.length > 0, "the contradiction names its repair verb");
});

test("state is recomputed, never cached: a direct capture edit changes the next snapshot", () => {
  const root = bareEngagement();
  node(root, "ap", "accounts payable");
  const before = desk.state(root);
  const src = ledger.route(root, stage(root, "p.pdf", "policy"), ["ap"]);
  fragment(root, "ap", { statements: [{ text: "3-way match required", cites: [src] }] });
  const after = desk.state(root);
  assert.notDeepEqual(after.coverage, before.coverage, "the capture diff IS the credit");
});

test("coverage per node: evidenced / claimed / contested / outstanding — computed, no 'thin'", () => {
  const root = bareEngagement();
  node(root, "ap", "accounts payable");
  const a = ledger.route(root, stage(root, "a.pdf", "aa"), ["ap"]);
  const b = ledger.route(root, stage(root, "b.pdf", "bb"), ["ap"]);
  fragment(root, "ap", { questions: [{ id: "Q-1", text: "which flow?", sources: [a, b] }] });
  const cov = desk.coverage(root).find(c => c.slug === "ap")!;
  assert.equal(cov.status, "contested");
  assert.equal(cov.conflicts.length, 1);
});

test("no 'all quiet' reachable by damage: a pinned shape over an empty engagement is NOT serviceable", () => {
  const root = bareEngagement();
  pinShape(root, "information-request");
  const s = desk.state(root);
  assert.equal(s.pinnedShapes.length, 1, "shipped definitions are not auto-pinned; this one is");
  assert.equal(s.pinnedShapes[0]!.serviceable, false, "no positive evidence, no serviceable");
});

// ── A19 resolved into state: the clock (staleness signals), pure ───────
import { utimesSync } from "node:fs";
import * as recordMod from "../src/record.ts";
import * as asksMod from "../src/asks.ts";

test("state carries AGES — hours since the last checkpoint, per sent ask awaiting response, per unrouted file — computed from the record, never stored", () => {
  const root = bareEngagement();
  recordMod.budgetSet(root, 1000);
  const h = 3600_000, now = Date.now();
  recordMod.sessionAppend(root, { at: new Date(now - 30 * h).toISOString(), verb: "checkpoint", detail: "old" });
  const a = asksMod.propose(root, "Who approves over $1,000?", ["ap-approval#Q-1"]);
  asksMod.accept(root, a); asksMod.sent(root, [a]);
  // backdate the crossing: rewrite the gate line's timestamp
  const logs = readdirSync(join(root, "_registers/sessions"));
  const p = join(root, "_registers/sessions", logs[0]!);
  writeFileSync(p, readFileSync(p, "utf8").split("\n").map(l => l.includes("crossed to the client") ? l.replace(/"at":"[^"]+"/, `"at":"${new Date(now - 72 * h).toISOString()}"`) : l).join("\n"));
  const f = stage(root, "late.pdf", "x"); utimesSync(f, new Date(now - 10 * h), new Date(now - 10 * h));
  const s = desk.state(root);
  assert.ok(s.ages.sinceCheckpointHours! >= 29 && s.ages.sinceCheckpointHours! <= 31, `checkpoint age ${s.ages.sinceCheckpointHours}`);
  assert.equal(s.ages.awaiting.length, 1); assert.equal(s.ages.awaiting[0]!.id, a);
  assert.ok(s.ages.awaiting[0]!.hours >= 71 && s.ages.awaiting[0]!.hours <= 73);
  assert.equal(s.ages.unrouted[0]!.file, "late.pdf"); assert.ok(s.ages.unrouted[0]!.hours >= 9 && s.ages.unrouted[0]!.hours <= 11);
  assert.match(desk.report(root), /ages: checkpoint 30h · awaiting ASK-001 72h · unrouted late\.pdf 10h/);
});

test("ages describe, never command: a bare engagement with no checkpoint reports no checkpoint age and empty lists — no nag, no verdict", () => {
  const root = bareEngagement();
  const s = desk.state(root);
  assert.equal(s.ages.sinceCheckpointHours, undefined);
  assert.deepEqual(s.ages.awaiting, []); assert.deepEqual(s.ages.unrouted, []);
  assert.match(desk.report(root), /ages: no checkpoint yet/);
  assert.ok(!/should|overdue|stale/i.test(desk.report(root)), "the report names hours, not judgments");
});
