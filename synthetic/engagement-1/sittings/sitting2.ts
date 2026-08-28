/** SITTING 2 — the ask round: curate, gate, send, render-refusal, responses back, fold, synthesis. */
import { writeFileSync, readFileSync, copyFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import * as asks from "../../../src/asks.ts";
import * as ledger from "../../../src/ledger.ts";
import * as record from "../../../src/record.ts";
import * as check from "../../../src/check.ts";
import * as desk from "../../../src/desk.ts";
import * as render from "../../../src/render.ts";
import * as definitions from "../../../src/definitions.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const root = process.argv[2]!;
const out: Record<string, unknown> = {};
import { mkdirSync } from "node:fs";
for (const d of ["_synthesis", "_sources/new"]) mkdirSync(join(root, d), { recursive: true });

// curate the asks — artifact-shaped where possible, pointed where the objective demands
const a1 = asks.propose(root, "Please confirm Dana Okafor's current reporting line post-reorg — the policy and the reorg deck disagree", ["ap-approval#Q-1", "ap-approval#Q-2"], "Marcus Webb", "a line from HR/finance, or the reorg deck appendix");
const a2 = asks.propose(root, "Is the 'expedite - DO approval' path a sanctioned exception to three-way match? If so, please send where it's documented", ["ap-payment#Q-3"], "Marcus Webb", "the exception policy or approval memo");
const a3 = asks.propose(root, "The June sample shows two Kessler Tooling invoices with identical amounts/dates under different numbers — were both paid, and has recovery been attempted?", ["ap-payment#Q-4"], "Marcus Webb", "the payment register rows for both invoices");
// the human's yes at the gate (scripted human approves all three)
for (const id of [a1, a2, a3]) asks.accept(root, id as never);

// demand-driven render of the information request: MUST refuse at the docx seam, by name
try { await render.deliverable(root, "information-request"); out.render = "UNEXPECTED SUCCESS"; }
catch (e) { out.renderRefusal = (e as Error).message; }
// the views themselves build — proof the plan compiles even though emit is Phase 2
const plan = definitions.compilePlan(definitions.load("information-request", root), root);
const views = render.build(root, plan);
writeFileSync(join(root, "_synthesis/information-request-v1.md"), `# Information Request — Meridian AP\n\n${[...views.values()].join("\n\n")}\n`);
asks.sent(root); // crossed the boundary

// the scripted client answers (script.yaml): reorg confirmed, expedite dodged, Kessler silence
copyFileSync(join(HERE, "..", "responses/reorg-confirmation.md"), join(root, "_sources/new/reorg-confirmation.md"));
const r1 = asks.respond(root, join(root, "_sources/new/reorg-confirmation.md"), [a1 as never]);
copyFileSync(join(HERE, "..", "responses/expedite-nonanswer.md"), join(root, "_sources/new/expedite-nonanswer.md"));
const r2 = asks.respond(root, join(root, "_sources/new/expedite-nonanswer.md"), [a2 as never]);
out.unsettledAfterArrival = asks.unsettled(root).map(a => a.id);

// fold-in: the reorg answer settles Q-1/Q-2 — the consultant rules the contested question answered,
// removes it, and writes the evidenced statements citing the response
writeFileSync(join(root, "capture/ap-approval.yaml"), `slug: ap-approval
type: process-step
statements:
  - text: "Invoices under $10,000 are approved by the requesting department's team lead"
    cites: [SRC-001]
  - text: "Invoices of $10,000 and above require approval by Dana Okafor"
    cites: [SRC-001, SRC-003]
  - text: "Approvals at or above $10k average 6.4 days, all waiting on the single approver"
    cites: [SRC-003]
  - text: "Since the June 2025 reorg, Dana Okafor reports to Tomás Reyes (Director of Operations Finance); the AP policy rev 2024-03 predates the reorg"
    cites: [${r1.src}]
  - text: "The Controller seat is an open requisition; Dana retains the >= $10k approval authority on an interim basis per the reorg deck appendix"
    cites: [${r1.src}, SRC-002]
questions: []
`);
// the non-answer: the question STAYS OPEN; the ask closes with the client's own words as the reason
asks.close(root, a2 as never, "client deferred in writing until Marcus speaks with Tomás — expedite path stays an open question");
// Kessler: silence — the ask stays sent, the debt visible

// the synthesis: consolidated approval model, registered with grounds, then cited
writeFileSync(join(root, "_synthesis/approval-model.md"), readFileSync(join(root, "capture/ap-approval.yaml"), "utf8"));
const model = ledger.route(root, join(root, "_synthesis/approval-model.md"), ["ap-approval"], { provenance: "synthesis", grounds: ["SRC-001", r1.src as string] });
// hmm — route expects the file staged; it lives in _synthesis. The door took it from there: note for RESULTS if it misbehaved.
writeFileSync(join(root, "capture/ap-approval.yaml"), readFileSync(join(root, "capture/ap-approval.yaml"), "utf8").replace(
  "questions: []",
  `  - text: "Approval authority currently concentrates on one person for all spend >= $10k, with no documented delegation beyond the interim note"\n    cites: [${model}]\nquestions: []`));

out.settledAfterFoldIn = { unsettled: asks.unsettled(root).map(a => a.id), sentAwaiting: asks.entriesOf(root, "sent").map(a => a.id) };
out.defects = check.run(root);
record.spend(root, 14000, 12600, "sitting 2: ask round + fold-in + synthesis (consultant direct)");
out.checkpoint = record.checkpoint(root, "sitting 2: ask round complete");
out.report = desk.report(root);
console.log(JSON.stringify(out, null, 1));
