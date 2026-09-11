/**
 * harness/conformance — the DYNAMIC half of a skill's conformance (A27).
 *
 * NOT engine. `consult skill check <name>` is the STATIC half (manifest valid,
 * ports declared, runtime entry exists, no `[HUMAN]`/gate vocabulary in a
 * level-2 runner). This file is the other half: RUN the skill against a known
 * engagement and prove, from the filesystem, that it stayed inside its walls.
 *
 * The proof is a BEFORE/AFTER snapshot (every file path + sha256 under
 * `_sources/`, `_registers/`, `capture/`, `_synthesis/`, plus STATE.md and
 * OBJECTIVE.md) plus the engine's own reads. A skill conforms when:
 *
 *   - nothing under `_sources/` changed except `_sources/sources.yaml` GAINING
 *     entries (publishing a work product registers it; editing, deleting, or
 *     re-hashing a source that was already there is not publication);
 *   - nothing under `_registers/` changed, and neither prose pad changed — a
 *     skill writes none of these: the CONSULTANT lands returns;
 *   - nothing under `capture/` changed, UNLESS the skill's manifest declares
 *     `writes: capture-fragment` (the `procedure-draft` grant). That grant is
 *     read from the manifest as plain YAML and honoured coarsely in this first
 *     kit: any capture change is allowed under the grant, and WHICH fragment
 *     the brief named is not checked here — the checkpoint diff still audits it;
 *   - every new file under `_synthesis/` lives under `_synthesis/<skill>/`, and
 *     no work product already published was modified or deleted (immutable);
 *   - every new synthesis ARTIFACT carries a card (index.synthesisArtifacts +
 *     index.synthesisCard — the A22 rule, sidecar or head);
 *   - every source registered BEFORE the run still matches its hash
 *     (ledger.verifySource, by id);
 *   - if `expectReturn` is given: the file exists, parses as YAML, carries
 *     `skill` and `run`, and contains no `[HUMAN]` text — a skill never stops
 *     for a human (the two gates are the consultant's, and they are the only stops);
 *   - `check.run(root)` carries no error the run introduced.
 *
 * Every finding NAMES the offending path, id, or file. `run` is whatever
 * exercises the skill: a scripted stub in the suite, a real dispatch in life,
 * a shell command from the CLI below.
 *
 * Usage (CLI): node --experimental-strip-types harness/conformance.ts \
 *                  <root> <skill> [--return <file>] -- <command…>
 * exit 0 = conforms, 2 = findings (printed, one per line).
 */
import { parse } from "yaml";
import { createHash } from "node:crypto";
import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join, relative, resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
import * as ledger from "../src/ledger.ts";
import * as index from "../src/index.ts";
import * as check from "../src/check.ts";

const REPO = resolve(dirname(fileURLToPath(import.meta.url)), "..");
/** the stores a conformance run watches — everything a skill could touch that is not its own run directory */
const WATCHED_DIRS = ["_sources", "_registers", "capture", "_synthesis"];
const WATCHED_FILES = ["STATE.md", "OBJECTIVE.md"];

export interface ConformOptions {
  /** the skill's name — its synthesis directory is `_synthesis/<skill>/` and its manifest is looked up by it */
  skill: string;
  /** whatever exercises the skill against this root */
  run: (root: string) => void | Promise<void>;
  /** the return file the skill is expected to have written (OUTSIDE the stores) */
  expectReturn?: string;
}
export interface ConformResult { ok: boolean; findings: string[] }

type Snapshot = Map<string, string>;
/** every file under the watched stores, root-relative → sha256; dotfiles skipped (the intake lock is not evidence) */
export function snapshot(root: string): Snapshot {
  const out: Snapshot = new Map();
  const walk = (dir: string) => {
    if (!existsSync(dir)) return;
    for (const f of readdirSync(dir)) {
      if (f.startsWith(".")) continue;
      const p = join(dir, f);
      if (statSync(p).isDirectory()) walk(p);
      else out.set(relative(root, p).split("\\").join("/"), createHash("sha256").update(readFileSync(p)).digest("hex"));
    }
  };
  for (const d of WATCHED_DIRS) walk(join(root, d));
  for (const f of WATCHED_FILES) {
    const p = join(root, f);
    if (existsSync(p)) out.set(f, createHash("sha256").update(readFileSync(p)).digest("hex"));
  }
  return out;
}

interface Manifest { writes?: unknown }
/** read the skill's manifest as PLAIN YAML — level 1 (`<name>.yaml`) or level 2 (`<name>/skill.yaml`),
 * engagement-authored `_skills/` shadowing shipped `kernel/skills/`. Never imports brief.ts: the kit
 * must keep working while the manifest schema lands. */
export function readManifest(root: string, skill: string): Manifest | undefined {
  const candidates = [
    join(root, "_skills", `${skill}.yaml`), join(root, "_skills", skill, "skill.yaml"),
    join(REPO, "kernel", "skills", `${skill}.yaml`), join(REPO, "kernel", "skills", skill, "skill.yaml"),
  ];
  for (const c of candidates) {
    if (!existsSync(c)) continue;
    try { const m = parse(readFileSync(c, "utf8")); if (m && typeof m === "object") return m as Manifest; }
    catch { return undefined; }   // a manifest that will not parse grants nothing; `skill check` names it
  }
  return undefined;
}
function declaresCaptureGrant(m: Manifest | undefined): boolean {
  const w = m?.writes;
  if (Array.isArray(w)) return w.some(v => String(v).trim() === "capture-fragment");
  return typeof w === "string" && /\bcapture-fragment\b/.test(w);
}
function ledgerEntries(root: string): Map<string, { file: string; hash: string }> {
  const out = new Map<string, { file: string; hash: string }>();
  try { for (const e of ledger.readBook(root).entries) if (e?.id) out.set(e.id, { file: String(e.file), hash: String(e.hash) }); }
  catch { /* an unreadable ledger is check's defect, reported below */ }
  return out;
}
const errKey = (d: check.Defect) => `${d.check}|${d.file}|${d.line ?? ""}|${d.message}`;
function errors(root: string): Map<string, check.Defect> {
  const out = new Map<string, check.Defect>();
  try { for (const d of check.run(root)) if (d.severity === "error") out.set(errKey(d), d); }
  catch (e) { out.set("check|crash", { check: "check", severity: "error", file: ".", message: `check.run refused: ${(e as Error).message}` }); }
  return out;
}

/**
 * Run a skill against `root` and report what it did outside its walls.
 * Pure report: conform never repairs and never writes into the engagement.
 */
export async function conform(root: string, opts: ConformOptions): Promise<ConformResult> {
  const skill = opts.skill;
  const mine = `_synthesis/${skill}/`;
  const captureGranted = declaresCaptureGrant(readManifest(root, skill));
  const before = snapshot(root), beforeEntries = ledgerEntries(root), beforeErrors = errors(root);
  const findings: string[] = [];

  await opts.run(root);

  const after = snapshot(root), afterEntries = ledgerEntries(root);
  const verdict = (p: string) => before.has(p) ? (after.has(p) ? (before.get(p) === after.get(p) ? "same" : "modified") : "deleted") : "added";
  const paths = [...new Set([...before.keys(), ...after.keys()])].sort();

  for (const p of paths) {
    const v = verdict(p);
    if (v === "same") continue;
    if (p === "_sources/sources.yaml") continue;                       // judged by entry, below
    if (p.startsWith("_sources/"))
      findings.push(`${p}: ${v} during the run — a skill never writes _sources/ (publication goes through publishSynthesis)`);
    else if (p.startsWith("_registers/"))
      findings.push(`${p}: ${v} during the run — a skill never writes a register; it returns, and the CONSULTANT lands the return`);
    else if (p.startsWith("capture/")) {
      if (!captureGranted)
        findings.push(`${p}: ${v} during the run — a skill writes capture only under a declared grant (writes: capture-fragment); ${skill}'s manifest declares none`);
    } else if (p === "STATE.md" || p === "OBJECTIVE.md")
      findings.push(`${p}: ${v} during the run — the prose pads are the consultant's own hands, never a skill's`);
    else if (p.startsWith("_synthesis/")) {
      if (v === "added") { if (!p.startsWith(mine)) findings.push(`${p}: written outside ${mine} — a skill writes only under its own synthesis directory`); }
      else findings.push(`${p}: ${v} during the run — a published work product is immutable (a rerun mints a new artifact, never an edit)`);
    }
  }

  for (const [id, was] of beforeEntries) {
    const now = afterEntries.get(id);
    if (!now) { findings.push(`_sources/sources.yaml: entry ${id} (${was.file}) removed during the run — publication may only ADD entries`); continue; }
    if (now.hash !== was.hash || now.file !== was.file)
      findings.push(`_sources/sources.yaml: entry ${id} changed during the run (${was.file}@${was.hash.slice(0, 12)} → ${now.file}@${now.hash.slice(0, 12)}) — publication may only ADD entries`);
    try { ledger.verifySource(root, id); }
    catch (e) { findings.push(`source ${id}: ${(e as Error).message}`); }
  }

  const artifacts = index.synthesisArtifacts(root).filter(f => !before.has(f));
  for (const f of artifacts)
    if (!index.synthesisCard(root, f))
      findings.push(`${f}: synthesis artifact written with no card — a sidecar beside it or a head card (A22); no card, no deliverable`);

  if (opts.expectReturn !== undefined) {
    const rf = opts.expectReturn;
    const rel = relative(resolve(root), resolve(rf)).split("\\").join("/");
    if (!rel.startsWith("..") && WATCHED_DIRS.some(d => rel.startsWith(`${d}/`)))
      findings.push(`${rf}: the return file was written inside a store — a return is written OUTSIDE the engagement's stores and landed with consult return <file>`);
    if (!existsSync(rf)) findings.push(`${rf}: no return file — a skill returns through one door (consult return <file>)`);
    else {
      const text = readFileSync(rf, "utf8");
      let doc: unknown;
      try { doc = parse(text); }
      catch (e) { doc = undefined; findings.push(`${rf}: return does not parse as YAML — ${(e as Error).message}`); }
      if (doc !== undefined) {
        const d = (doc ?? {}) as Record<string, unknown>;
        if (typeof d.skill !== "string" || !d.skill.trim()) findings.push(`${rf}: return carries no skill: — the return names the skill that produced it`);
        if (typeof d.run !== "string" || !d.run.trim()) findings.push(`${rf}: return carries no run: — the return names the run that produced it`);
      }
      if (text.includes("[HUMAN]")) findings.push(`${rf}: return carries [HUMAN] — a skill never stops for a human; the two gates are the consultant's and they are the only stops`);
    }
  }

  for (const [k, d] of errors(root))
    if (!beforeErrors.has(k))
      findings.push(`${d.file}${d.line ? `:${d.line}` : ""}: new check error introduced by the run (${d.check}) — ${d.message}`);

  return { ok: findings.length === 0, findings };
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const argv = process.argv.slice(2);
  const sep = argv.indexOf("--");
  const head = sep === -1 ? argv : argv.slice(0, sep);
  const cmd = sep === -1 ? [] : argv.slice(sep + 1);
  const ri = head.indexOf("--return");
  const expectReturn = ri > 0 ? head[ri + 1] : undefined;
  const rest = ri > 0 ? head.filter((_, i) => i !== ri && i !== ri + 1) : head;
  const [root, skill] = [rest[0], rest[1]];
  if (!root || !skill || !cmd.length) {
    console.error("usage: conformance.ts <root> <skill> [--return <file>] -- <command…>");
    process.exit(2);
  }
  const result = await conform(resolve(root), {
    skill,
    ...(expectReturn ? { expectReturn: resolve(expectReturn) } : {}),
    run: (r: string) => { execFileSync(cmd[0]!, cmd.slice(1), { cwd: r, stdio: "inherit" }); },
  });
  if (result.ok) console.log(`conformance: ${skill} conforms — read through the port, wrote only under _synthesis/${skill}/, hashes intact, nothing landed by hand`);
  else for (const f of result.findings) console.error(`finding: ${f}`);
  process.exit(result.ok ? 0 : 2);
}
