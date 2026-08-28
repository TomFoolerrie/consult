/** SITTING 1 — intake and first capture. The consultant's judgment, encoded. */
import { mkdirSync, writeFileSync, copyFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";
import * as ledger from "../../../src/ledger.ts";
import * as record from "../../../src/record.ts";
import * as check from "../../../src/check.ts";
import * as desk from "../../../src/desk.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const root = process.argv[2]!;

// the folder, the pads, git
for (const d of ["_sources/new", "_sources/processed", "_sources/parked", "_registers/sessions", "_skills", "_synthesis", "_definitions", "capture/_taxonomy"])
  mkdirSync(join(root, d), { recursive: true });
writeFileSync(join(root, "STATE.md"), `# state pad\n## now\nSitting 1: intake the three seed sources, first capture, taxonomy.\n## human's standing guidance\nObjective per OBJECTIVE.md; expedite path is sensitive — ask, don't assume.\n## precedent\n(none yet)\n## observations\n(none yet)\n`);
copyFileSync(join(HERE, "..", "objective.md"), join(root, "OBJECTIVE.md"));
execSync("git init -q && git add -A && git commit -qm seed", { cwd: root });
record.budgetSet(root, 200_000);

// stage + route, intent declared
for (const f of readdirSync(join(HERE, "..", "seed"))) copyFileSync(join(HERE, "..", "seed", f), join(root, "_sources/new", f));
const policy = ledger.route(root, join(root, "_sources/new/ap-policy.md"), ["ap-intake", "ap-approval", "ap-payment"], { provenance: "client" });
const org = ledger.route(root, join(root, "_sources/new/org-chart-extract.md"), ["ap-approval"], { provenance: "client" });
const sample = ledger.route(root, join(root, "_sources/new/invoice-sample-notes.md"), ["ap-payment", "ap-approval"], { provenance: "client" });

// taxonomy — the consultant's partitioning of this objective
const node = (slug: string, scope: string) =>
  writeFileSync(join(root, "capture/_taxonomy", `${slug}.yaml`), `slug: ${slug}\ntype: taxonomy-node\nscope: ${JSON.stringify(scope)}\nstatements: []\nquestions: []\n`);
node("ap-intake", "how invoices arrive and are logged");
node("ap-approval", "who approves what, at which thresholds");
node("ap-payment", "matching, payment runs, exceptions");

// fold-in — direct capture writes, every statement cited, every unknown a question
const frag = (slug: string, body: string) => writeFileSync(join(root, "capture", `${slug}.yaml`), body);
frag("ap-intake", `slug: ap-intake
type: process-step
statements:
  - text: "Invoices arrive at ap@meridian.example and are logged by the AP clerk (Jamie Fox) within one business day"
    cites: [${policy}, ${org}]
questions: []
`);
frag("ap-approval", `slug: ap-approval
type: process-step
statements:
  - text: "Invoices under $10,000 are approved by the requesting department's team lead"
    cites: [${policy}]
  - text: "Invoices of $10,000 and above require approval by Dana Okafor"
    cites: [${policy}, ${sample}]
  - text: "Approvals at or above $10k average 6.4 days, all waiting on the single approver"
    cites: [${sample}]
questions:
  - id: Q-1
    text: "Who does Dana Okafor report to? Policy (rev 2024-03) says the CFO; the 2025 reorg deck shows her under Tomás Reyes (Ops Finance) with the Controller seat open"
    sources: [${policy}, ${org}]
  - id: Q-2
    text: "With the Controller requisition open since 2025-06, is Dana's >= $10k approval authority formally delegated, and by whom?"
`);
frag("ap-payment", `slug: ap-payment
type: process-step
statements:
  - text: "A three-way match (PO, receipt, invoice) is required before payment for PO-backed purchases"
    cites: [${policy}]
  - text: "In the June sample, 6 of 20 PO-backed invoices were missing the receipt leg and 4 of those were paid anyway, marked 'expedite - DO approval'"
    cites: [${sample}]
  - text: "Payment runs occur every Thursday"
    cites: [${policy}]
  - text: "Two invoices from vendor Kessler Tooling appear twice with different invoice numbers but identical amounts and dates"
    cites: [${sample}]
questions:
  - id: Q-3
    text: "Is the 'expedite - DO approval' path a sanctioned exception to the three-way match, and where is it documented?"
  - id: Q-4
    text: "Are the duplicate Kessler Tooling invoices duplicate PAYMENTS, and has recovery been attempted?"
`);

// pin the early shape the objective expects
writeFileSync(join(root, "_definitions/information-request.yaml"), "pin: information-request\n");

const defects = check.run(root);
record.spend(root, 9000, 8200, "sitting 1 fold-in (consultant direct)");
const cp = record.checkpoint(root, "sitting 1: intake + first capture");
console.log(JSON.stringify({ defects, retired: cp.retired, report: desk.report(root) }, null, 1));
