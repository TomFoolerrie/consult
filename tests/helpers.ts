/**
 * tests/helpers — the fixture engagement.
 *
 * Builds a minimal, VALID engagement in a temp dir. These fixtures are
 * the executable spec for the on-disk shapes: capture fragments are the
 * three-primitive grammar made concrete (addressable slug, statements
 * carrying citations, question records); everything under _sources/ and
 * _registers/ is written only through the library once it exists.
 */
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

/** a bare engagement: the _sources/ marker + empty capture. */
export function bareEngagement(): string {
  const root = mkdtempSync(join(tmpdir(), "consult-"));
  for (const d of ["_sources/new", "_sources/processed", "_sources/parked",
                   "_registers/sessions", "_skills", "_synthesis",
                   "capture/_taxonomy"]) mkdirSync(join(root, d), { recursive: true });
  writeFileSync(join(root, "STATE.md"), "# state pad\n");
  writeFileSync(join(root, "OBJECTIVE.md"), "# objective\nUnderstand the client's AP process.\n");
  return root;
}

/** drop a file into _sources/new/ (the staging area) and return its path. */
export function stage(root: string, name: string, content: string): string {
  const p = join(root, "_sources/new", name);
  writeFileSync(p, content);
  return p;
}

/**
 * write one capture fragment — THE fragment format, pinned here.
 * statements: text + cites (SRC ids). questions: local id + text, and
 * optionally the two sources whose disagreement it records (contested).
 */
export function fragment(root: string, slug: string, body: {
  statements?: { text: string; cites?: string[] }[];
  questions?: { id: string; text: string; sources?: string[] }[];
}): string {
  const lines: string[] = [`slug: ${slug}`, `type: process-step`, `statements:`];
  for (const s of body.statements ?? []) {
    lines.push(`  - text: ${JSON.stringify(s.text)}`);
    lines.push(`    cites: [${(s.cites ?? []).join(", ")}]`);
  }
  lines.push(`questions:`);
  for (const q of body.questions ?? []) {
    lines.push(`  - id: ${q.id}`);
    lines.push(`    text: ${JSON.stringify(q.text)}`);
    if (q.sources) lines.push(`    sources: [${q.sources.join(", ")}]`);
  }
  const p = join(root, "capture", `${slug}.yaml`);
  writeFileSync(p, lines.join("\n") + "\n");
  return p;
}

/** a taxonomy node file. */
export function node(root: string, name: string, scope: string): string {
  const p = join(root, "capture/_taxonomy", `${name}.yaml`);
  writeFileSync(p, `slug: ${name}\ntype: taxonomy-node\nscope: ${JSON.stringify(scope)}\nstatements:\nquestions:\n`);
  return p;
}
