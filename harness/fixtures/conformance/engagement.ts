/**
 * harness/fixtures/conformance — the known root a skill is proved against (A27).
 *
 * NOT engine, and NOT a test helper: this is the fixture engagement the
 * conformance kit runs a skill INSIDE, so a skill author on another branch
 * (or another machine) proves their skill against the same ground the suite
 * does. Bare but complete: the skeleton, two ROUTED sources (one markdown,
 * one CSV — the two shapes the read port verifies), one capture fragment
 * carrying a question record, and one ACCEPTED ask against that question.
 *
 * Everything here lands through the library's own doors (ledger.route,
 * asks.propose/accept) — the fixture never hand-writes a store, so what a
 * skill meets is exactly what an engagement looks like.
 */
import { mkdtempSync, mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import * as ledger from "../../../src/ledger.ts";
import * as asks from "../../../src/asks.ts";
import * as record from "../../../src/record.ts";
import type { SrcId, AskId } from "../../../src/types.ts";

export interface ConformanceFixture {
  /** the engagement root (a fresh temp dir) */
  root: string;
  /** the routed markdown policy note */
  policy: SrcId;
  /** the routed CSV export */
  export_: SrcId;
  /** the capture fragment's slug */
  slug: string;
  /** the accepted ask */
  ask: AskId;
}

const POLICY = `# AP policy (extract)
Invoices of $10,000 and above require approval by the controller.
Duplicate checks run before payment, weekly.
Exceptions are logged in the payment file.
`;
const EXPORT = `invoice,vendor,amount,paid_on
INV-001,Kessler,12400,2025-04-02
INV-001,Kessler,12400,2025-04-09
INV-002,Ardent,3100,2025-04-11
`;

/** build the fixture engagement; returns the root and the ids a skill may be pointed at */
export function conformanceFixture(): ConformanceFixture {
  const root = mkdtempSync(join(tmpdir(), "consult-conformance-"));
  for (const d of ["_sources/new", "_sources/processed", "_sources/parked", "_sources/scans",
                   "_registers/sessions", "_skills", "_synthesis", "_definitions",
                   "capture/_taxonomy"]) mkdirSync(join(root, d), { recursive: true });
  writeFileSync(join(root, "STATE.md"), "# state pad\n## now\nconformance fixture: nothing mid-flight.\n");
  writeFileSync(join(root, "OBJECTIVE.md"), "# objective\nUnderstand the client's AP process.\n");

  const slug = "payment-review";
  writeFileSync(join(root, "capture", `${slug}.yaml`), [
    `slug: ${slug}`,
    `type: process-step`,
    `scope: "how a payment is reviewed before it goes out"`,
    `statements:`,
    `  - text: "Duplicate checks run before payment"`,
    `    cites: []`,
    `questions:`,
    `  - id: Q-1`,
    `    text: "Were the two INV-001 rows paid twice, or is one a reversal?"`,
    ``,
  ].join("\n"));

  writeFileSync(join(root, "_sources/new", "ap-policy.md"), POLICY);
  writeFileSync(join(root, "_sources/new", "ap-export.csv"), EXPORT);
  const policy = ledger.route(root, join(root, "_sources/new", "ap-policy.md"), [slug]);
  const export_ = ledger.route(root, join(root, "_sources/new", "ap-export.csv"), [slug]);

  record.budgetSet(root, 100000);
  const ask = asks.propose(root, "Please send one completed duplicate-review record for INV-001", [`${slug}#Q-1`]);
  asks.accept(root, ask, "the human said yes");
  return { root, policy, export_, slug, ask };
}
