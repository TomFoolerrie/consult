/** definitions — the D3 wall: YAML-sized shapes, serviceability as records. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { bareEngagement, pinShape } from "./helpers.ts";
import * as definitions from "../src/definitions.ts";

test("the shipped information-request loads with blocks, bindings, and a docx skin", () => {
  const d = definitions.load("information-request");
  assert.equal(d.name, "information-request");
  assert.ok(d.blocks.length > 0 && d.skin.format === "docx");
});

test("serviceability returns GAPS as records — never an exception — on an empty engagement", () => {
  const root = bareEngagement();
  const gaps = definitions.serviceability(definitions.load("information-request"), root);
  assert.ok(gaps.length > 0, "an empty engagement cannot serve the shape");
  for (const g of gaps) assert.ok(g.binding && g.missing && g.where, "each gap names binding, missing, where");
});

test("a binding naming an undeclared vocabulary word is refused BY NAME at load", () => {
  const root = bareEngagement();
  mkdirSync(join(root, "_definitions"), { recursive: true });
  writeFileSync(join(root, "_definitions/bad-shape.yaml"),
    "name: bad-shape\ntitle: Bad\nblocks:\n  - { kind: view, id: v1, title: V, binding: b1 }\nbindings:\n  b1: { hallucinations: all }\nskin: { format: docx, requires: [] }\n");
  assert.throws(() => definitions.load("bad-shape", root), (e: Error) => e.message.includes("hallucinations"));
});

test("pinned() lists only what the engagement pinned — shipped shapes are not auto-pinned", () => {
  const root = bareEngagement();
  assert.equal(definitions.pinned(root).length, 0);
  pinShape(root, "information-request");
  assert.deepEqual(definitions.pinned(root).map(d => d.name), ["information-request"]);
});
