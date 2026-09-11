/** Read-only evidence bridge: identity/integrity is not semantic support. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, writeFileSync, rmSync, symlinkSync } from "node:fs";
import { join } from "node:path";
import * as ledger from "../src/ledger.ts";
import { bareEngagement, stage } from "./helpers.ts";
import { main } from "../src/cli.ts";

function fixture(text = "first\nsecond\nthird\n") {
  const root = bareEngagement();
  const file = stage(root, "note.md", text);
  const id = ledger.route(root, file, ["ap"]);
  return { root, file, id };
}

test("source verify and excerpt hash the registered bytes without changing the ledger", () => {
  const { root, id } = fixture();
  const before = readFileSync(join(root, "_sources/sources.yaml"), "utf8");
  const verified = ledger.verifySource(root, id);
  assert.equal(verified.id, id);
  assert.equal(verified.integrity, "sha256-matched");
  assert.match(verified.hash, /^[a-f0-9]{64}$/);
  assert.equal(ledger.sourceExcerpt(root, id, { start: 2, end: 3 }).text, "second\nthird");
  assert.equal(readFileSync(join(root, "_sources/sources.yaml"), "utf8"), before);
  ledger.retire(root, id);
  assert.match(ledger.verifySource(root, id).file, /processed/);
  assert.equal(ledger.sourceExcerpt(root, id, { start: 1, end: 1 }).text, "first");
});

test("unknown, duplicate, missing hash, missing file and changed bytes fail explicitly", () => {
  const { root, file, id } = fixture();
  assert.throws(() => ledger.verifySource(root, "SRC-999"), /unknown source/);
  const book = ledger.readBook(root);
  book.entries.push({ ...book.entries[0]! }); ledger.writeBook(root, book);
  assert.throws(() => ledger.verifySource(root, id), /duplicate source/);
  book.entries.pop();
  const hash = book.entries[0]!.hash;
  book.entries[0]!.hash = ""; ledger.writeBook(root, book);
  assert.throws(() => ledger.verifySource(root, id), /registered hash/);
  book.entries[0]!.hash = hash; ledger.writeBook(root, book);
  writeFileSync(file, "changed");
  assert.throws(() => ledger.sourceExcerpt(root, id, { start: 1, end: 1 }), /content changed/);
  rmSync(file);
  assert.throws(() => ledger.verifySource(root, id), /unreadable source/);
});

test("line rules: positive inclusive bounds, actual lines, Unicode, CRLF and terminal newline", () => {
  const { root, id } = fixture("α\r\nβ\r\n");
  const out = ledger.sourceExcerpt(root, id, { start: 1, end: 2 });
  assert.equal(out.text, "α\nβ");
  assert.equal(out.totalLines, 2);
  for (const range of [{ start: 0, end: 1 }, { start: 2, end: 1 }, { start: 1, end: 3 }, { start: 1.5, end: 2 }, { start: NaN, end: 2 }])
    assert.throws(() => ledger.sourceExcerpt(root, id, range), /line range/);
  const empty = fixture("");
  assert.throws(() => ledger.sourceExcerpt(empty.root, empty.id, { start: 1, end: 1 }), /line range/);
  const blank = fixture("\n");
  assert.equal(ledger.sourceExcerpt(blank.root, blank.id, { start: 1, end: 1 }).text, "");
});

test("binary and invalid UTF-8 are verifiable artifacts, not line-addressable text", () => {
  for (const bytes of [Buffer.from([0xff]), Buffer.from("a\0b")]) {
    const root = bareEngagement(); const file = stage(root, "binary.bin", "");
    writeFileSync(file, bytes); const id = ledger.route(root, file, ["ap"]);
    assert.equal(ledger.verifySource(root, id).integrity, "sha256-matched");
    assert.throws(() => ledger.sourceExcerpt(root, id, { start: 1, end: 1 }), /unsupported text/);
  }
});

test("lexical and symlink paths cannot escape allowed source stores", () => {
  const { root, file, id } = fixture();
  const book = ledger.readBook(root);
  for (const path of ["STATE.md", "_sources/scans/note.md", "../outside.md", "_sources/new/../../STATE.md"]) {
    book.entries[0]!.file = path; ledger.writeBook(root, book);
    assert.throws(() => ledger.verifySource(root, id), /outside allowed/);
  }
  book.entries[0]!.file = "_sources/new/note.md"; ledger.writeBook(root, book);
  rmSync(file); symlinkSync(join(root, "STATE.md"), file);
  assert.throws(() => ledger.verifySource(root, id), /outside allowed/);
});

test("CLI emits verified JSON and refuses absent/malformed ranges and unknown subcommands", async () => {
  const { root, id } = fixture();
  const log = console.log, error = console.error; const lines: string[] = [];
  console.log = (...v) => lines.push(v.join(" ")); console.error = () => {};
  try {
    assert.equal(await main(["source", "verify", id, "--root", root]), 0);
    assert.equal(JSON.parse(lines.pop()!).integrity, "sha256-matched");
    assert.equal(await main(["source", "excerpt", id, "--lines", "2:3", "--root", root]), 0);
    assert.equal(JSON.parse(lines.pop()!).text, "second\nthird");
    for (const args of [["excerpt", id], ["excerpt", id, "--lines", "1:2:3"], ["erase", id]])
      assert.equal(await main(["source", ...args, "--root", root]), 2);
  } finally { console.log = log; console.error = error; }
});
