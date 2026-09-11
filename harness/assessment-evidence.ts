/** First assessment adapter: read its versioned JSONL findings, delegate all
 * source integrity/excerpts to CONSULT. No source registry or ledger writes.
 * This does not replace assessment's taxonomy/layering/semantic review checks.
 * Integrated citations use authoritative uppercase SRC IDs, never inferred
 * aliases for standalone consult-lint IDs. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import * as ledger from "../src/ledger.ts";

interface CitationReview {
  reference: string;
  source?: ledger.VerifiedSource;
  excerpt?: ledger.SourceExcerpt;
  record?: ledger.SourceRecord;
  error?: string;
}
interface FindingReview {
  id: string; version: number; observation: string; evidenceBasis: string;
  type: string; citations: CitationReview[];
}
export interface EvidenceReview {
  scope: "citation-integrity-and-excerpts-only";
  ok: boolean;
  findings: FindingReview[];
  errors: string[];
  warnings: string[];
}

/** Highest row version is current, as in assessment common.current().
 * Refuse duplicate versions rather than choosing a possibly conflicting row.
 * Fail loud on broken row identity/history; record citation failures per item. */
export function reviewEvidence(root: string, findingsFile: string): EvidenceReview {
  let text: string;
  try { text = readFileSync(findingsFile, "utf8"); }
  catch { throw new Error(`assessment evidence: cannot read ${findingsFile}`); }
  const latest = new Map<string, Record<string, unknown>>();
  const versions = new Set<string>();
  for (const [i, line] of text.split(/\r?\n/).entries()) {
    if (!line.trim()) continue;
    let row: Record<string, unknown>;
    try {
      const value = JSON.parse(line);
      if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("not a row");
      row = value;
    } catch { throw new Error(`assessment evidence: ${findingsFile} line ${i + 1}: malformed JSON row`); }
    if (typeof row.id !== "string" || !/^F-\d+$/.test(row.id) || !Number.isSafeInteger(row.version) || Number(row.version) < 1 || !["active", "retired"].includes(String(row.status)))
      throw new Error(`assessment evidence: ${findingsFile} line ${i + 1}: invalid id/version/status`);
    const key = `${row.id}@${row.version}`;
    if (versions.has(key)) throw new Error(`assessment evidence: duplicate version ${key}`);
    versions.add(key);
    const prior = latest.get(row.id);
    if (!prior || Number(row.version) > Number(prior.version)) latest.set(row.id, row);
  }
  const result: EvidenceReview = { scope: "citation-integrity-and-excerpts-only", ok: false, findings: [], errors: [], warnings: [] };
  for (const [id, row] of latest) {
    if (row.status === "retired") continue;
    const finding: FindingReview = { id, version: Number(row.version), observation: String(row.observation ?? ""), evidenceBasis: String(row.evidence_basis ?? ""), type: String(row.type ?? ""), citations: [] };
    result.findings.push(finding);
    if (typeof row.observation !== "string" || !row.observation.trim()) result.errors.push(`${id}: missing observation`);
    if (!["stated", "observed", "inferred"].includes(finding.evidenceBasis)) result.errors.push(`${id}: invalid evidence_basis`);
    if (!Array.isArray(row.sources) || !row.sources.length) {
      result.errors.push(`${id}: sources must be a nonempty list`); continue;
    }
    for (const ref of row.sources) {
      const citation: CitationReview = { reference: String(ref) }; finding.citations.push(citation);
      try {
        const m = typeof ref === "string" ? /^(SRC-\d+)(?::(?:L(\d+)(?:-L?(\d+))?|R(\d+)))?$/.exec(ref) : null;
        if (!m) throw new Error("expected an engine SRC-nnn reference, optionally :Lstart-Lend or :Rrecord; standalone IDs require explicit migration, not case conversion");
        if (m[4] !== undefined) {
          const record = ledger.sourceRecord(root, m[1]!, Number(m[4]));
          citation.record = record;
          const { locator: _locator, totalRecords: _total, header: _header, values: _values, ...source } = record;
          citation.source = source;
        } else if (m[2] !== undefined) {
          const excerpt = ledger.sourceExcerpt(root, m[1]!, { start: Number(m[2]), end: Number(m[3] ?? m[2]) });
          citation.excerpt = excerpt;
          const { locator: _locator, totalLines: _total, text: _text, ...source } = excerpt;
          citation.source = source;
        } else {
          citation.source = ledger.verifySource(root, m[1]!);
          result.warnings.push(`${id}: ${ref} has no pinpoint; artifact integrity checked, no excerpt supplied`);
        }
      } catch (e) {
        citation.error = (e as Error).message;
        result.errors.push(`${id}: ${String(ref)}: ${citation.error}`);
      }
    }
  }
  if (!result.findings.length) result.errors.push("assessment evidence: no active findings to review");
  result.ok = result.errors.length === 0;
  return result;
}

/** Human review view, not a client-ready deliverable. Escape source-authored
 * markup so excerpts and observations cannot become hidden HTML or links. */
function plain(text: string): string {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/([\\`*_{}\[\]()#!|~])/g, "\\$1");
}
export function renderReview(pack: EvidenceReview): string {
  const lines = ["# Assessment evidence review", "",
    `Reference checks: ${pack.ok ? "passed" : "NEEDS ATTENTION"}. ${pack.findings.length} active findings.`, "",
    "This checks registered bytes and citation locations. It does not establish that a claim is true, supported by its excerpt, complete, or free of counterevidence. Taxonomy and analytical-layer checks are separate.", "",
    "Review each observation against its excerpt. Distinguish what someone reports from what was independently observed. Flag overreach, missing context, and conflicting evidence.", ""];
  for (const f of pack.findings) {
    lines.push(`## ${plain(f.id)} — version ${f.version}`, "", plain(f.observation), "",
      `Evidence basis: ${plain(f.evidenceBasis)}. Type: ${plain(f.type)}.`, "");
    for (const c of f.citations) {
      lines.push(`### ${plain(c.reference)}`, "");
      if (c.error) lines.push(`CHECK FAILED: ${plain(c.error)}`, "");
      else if (c.excerpt) lines.push(...c.excerpt.text.split("\n").map(l => l ? `> ${plain(l)}` : ">"), "");
      else if (c.record) lines.push(...c.record.header.map((h, i) => `> ${plain(h)}: ${plain(JSON.stringify(c.record!.values[i]))}`), "");
      else lines.push("Artifact integrity checked; no pinpoint or excerpt supplied.", "");
      if (c.source) lines.push(`Source file: ${plain(c.source.file)}`, `Registered SHA-256: ${c.source.hash}`, "");
    }
  }
  if (pack.errors.length) lines.push("## Errors", "", ...pack.errors.map(e => `- ${plain(e)}`), "");
  if (pack.warnings.length) lines.push("## Limitations", "", ...pack.warnings.map(e => `- ${plain(e)}`), "");
  return lines.join("\n");
}

/** CLI adapter: output is retained even when citations fail; nonzero exit
 * prevents a failed evidence review from looking like a passed check. */
export function main(argv: string[]): number {
  const opts = new Map<string, string>();
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i]!, value = argv[i + 1];
    if (!["--root", "--findings", "--format"].includes(key) || opts.has(key) || !value || value.startsWith("--")) {
      console.error("assessment evidence: invalid or duplicate option"); return 2;
    }
    opts.set(key, value);
  }
  const format = opts.get("--format") ?? "json";
  if (!opts.has("--root") || !opts.has("--findings") || !["json", "markdown"].includes(format)) {
    console.error("usage: assessment-evidence.ts --root ENGAGEMENT --findings FINDINGS.jsonl [--format json|markdown]"); return 2;
  }
  try {
    const root = resolve(opts.get("--root")!);
    const pack = reviewEvidence(root, resolve(root, opts.get("--findings")!));
    console.log(format === "markdown" ? renderReview(pack) : JSON.stringify(pack, null, 2));
    return pack.ok ? 0 : 2;
  } catch (e) { console.error((e as Error).message); return 2; }
}
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href)
  process.exitCode = main(process.argv.slice(2));
