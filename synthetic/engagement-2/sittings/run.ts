/** Engagement 2, both sittings — contradiction-heavy. The consultant never adjudicates. */
import { mkdirSync, writeFileSync, copyFileSync, readdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";
import * as ledger from "../../../src/ledger.ts";
import * as record from "../../../src/record.ts";
import * as check from "../../../src/check.ts";
import * as desk from "../../../src/desk.ts";
import * as asks from "../../../src/asks.ts";
import * as answers from "../../../src/answers.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const root = process.argv[2]!;
for (const d of ["_sources/new", "_registers", "_synthesis", "capture/_taxonomy"]) mkdirSync(join(root, d), { recursive: true });
writeFileSync(join(root, "STATE.md"), "# state pad\n## now\nHalvard receiving: surface the disagreements, never smooth them.\n");
copyFileSync(join(HERE, "..", "objective.md"), join(root, "OBJECTIVE.md"));
execSync("git init -q && git add -A && git commit -qm seed", { cwd: root });
record.budgetSet(root, 150_000);

for (const f of readdirSync(join(HERE, "..", "seed"))) copyFileSync(join(HERE, "..", "seed", f), join(root, "_sources/new", f));
const sop = ledger.route(root, join(root, "_sources/new/sop-receiving.md"), ["rcv-cutoff", "rcv-signoff", "rcv-system", "rcv-claims"], { provenance: "client" });
const oslo = ledger.route(root, join(root, "_sources/new/site-audit-oslo.md"), ["rcv-cutoff", "rcv-signoff", "rcv-system"], { provenance: "client" });
const rdam = ledger.route(root, join(root, "_sources/new/site-survey-rotterdam.md"), ["rcv-cutoff", "rcv-signoff", "rcv-system", "rcv-claims"], { provenance: "client" });

const node = (slug: string, scope: string) => writeFileSync(join(root, "capture/_taxonomy", `${slug}.yaml`), `slug: ${slug}\ntype: taxonomy-node\nscope: ${JSON.stringify(scope)}\nstatements: []\nquestions: []\n`);
node("rcv-cutoff", "same-day putaway cutoffs"); node("rcv-signoff", "who signs receiving"); node("rcv-system", "system of record"); node("rcv-claims", "discrepancy claims");

const frag = (slug: string, body: string) => writeFileSync(join(root, "capture", `${slug}.yaml`), body);
frag("rcv-cutoff", `slug: rcv-cutoff\ntype: process-step\nstatements:\n  - text: "SOP cutoff for same-day putaway is 14:00 local; Rotterdam reports strict compliance"\n    cites: [${sop}, ${rdam}]\n  - text: "Oslo operates a 16:30 cutoff and believes it is sanctioned"\n    cites: [${oslo}]\nquestions:\n  - id: Q-1\n    text: "Which cutoff is the standard — SOP/Rotterdam 14:00 or Oslo's extended 16:30?"\n    sources: [${sop}, ${oslo}]\n`);
frag("rcv-signoff", `slug: rcv-signoff\ntype: process-step\nstatements:\n  - text: "SOP: the dock supervisor signs the receiving report; Rotterdam complies"\n    cites: [${sop}, ${rdam}]\n  - text: "Oslo: receiving reports are signed by the shift lead"\n    cites: [${oslo}]\nquestions:\n  - id: Q-1\n    text: "Who is authorized to sign the receiving report — dock supervisor (SOP) or shift lead (Oslo practice)?"\n    sources: [${sop}, ${oslo}]\n`);
frag("rcv-system", `slug: rcv-system\ntype: process-step\nstatements:\n  - text: "SOP names LogiCore as system of record for receipts"\n    cites: [${sop}]\n  - text: "Oslo keys LogiCore then re-keys into the AS/400 for finance"\n    cites: [${oslo}]\n  - text: "Rotterdam treats the AS/400 as system of record and keys it first"\n    cites: [${rdam}]\nquestions:\n  - id: Q-1\n    text: "Which system is the actual system of record — LogiCore (SOP) or AS/400 (Rotterdam; Oslo finance)?"\n    sources: [${sop}, ${rdam}]\n`);
frag("rcv-claims", `slug: rcv-claims\ntype: process-step\nstatements:\n  - text: "SOP requires supplier claims within 48h for discrepancies over 2%"\n    cites: [${sop}]\n  - text: "Rotterdam files claims within 5 business days and calls 48h unrealistic"\n    cites: [${rdam}]\nquestions:\n  - id: Q-1\n    text: "Is the 48h claim window policy or aspiration — SOP says 48h, Rotterdam self-reports 5 days?"\n    sources: [${sop}, ${rdam}]\n`);

console.log("SITTING1 defects:", JSON.stringify(check.run(root)));
record.spend(root, 8000, 7400, "sitting 1 fold-in");
record.checkpoint(root, "sitting 1: three sources, four conflicts surfaced");
console.log("COVERAGE BEFORE:", desk.coverage(root).map(c => `${c.slug}:${c.status}`).join(" "));

// the ask round
const a1 = asks.propose(root, "Which system is the current system of record for receipts — LogiCore or the AS/400? An IT architecture note would settle it", ["rcv-system#Q-1"], "Ravi Chandran", "IT architecture memo");
const a2 = asks.propose(root, "Which same-day cutoff is the sanctioned standard — 14:00 per SOP or Oslo's 16:30?", ["rcv-cutoff#Q-1"], "Ravi Chandran");
for (const id of [a1, a2]) asks.accept(root, id as never);
asks.sent(root);
copyFileSync(join(HERE, "..", "responses/it-memo.md"), join(root, "_sources/new/it-memo.md"));
const { src: memo } = asks.respond(root, join(root, "_sources/new/it-memo.md"), [a1 as never]);

// fold-in: the memo settles POLICY (LogiCore) — and CREATES a new conflict with both sites' observed behavior.
// The consultant records both; adjudicates neither.
frag("rcv-system", `slug: rcv-system\ntype: process-step\nstatements:\n  - text: "LogiCore is the sole system of record group-wide since 1 May; the AS/400 is read-only archive"\n    cites: [${memo}]\n  - text: "Oslo keys LogiCore then re-keys into the AS/400 for finance"\n    cites: [${oslo}]\n  - text: "Rotterdam treats the AS/400 as system of record and keys it first"\n    cites: [${rdam}]\n  - text: "IT logs show no AS/400 write transactions since 30 April"\n    cites: [${memo}]\nquestions:\n  - id: Q-2\n    text: "Both sites report actively keying the AS/400, but IT logs show no writes since 30 April — are the sites describing a dead ritual, a shadow system, or is the memo wrong?"\n    sources: [${memo}, ${oslo}]\n`);

console.log("SITTING2 defects:", JSON.stringify(check.run(root)));
record.spend(root, 6000, 5100, "sitting 2: ask round + memo fold-in");
record.checkpoint(root, "sitting 2: policy settled, behavioral conflict opened");
console.log("COVERAGE AFTER:", desk.coverage(root).map(c => `${c.slug}:${c.status}`).join(" "));
const s = desk.state(root);
console.log("DEBTS:", JSON.stringify(s.askDebts), "unrouted:", s.unrouted.length);

// exam
const probe = (label: string, topic: string, match: string) => {
  const i = answers.ground(root, topic).find(x => x.text.toLowerCase().includes(match.toLowerCase()));
  console.log(label, "->", i ? i.standing.kind : "NO MATERIAL");
};
probe("Q1 cutoff       ", "rcv-cutoff", "Which cutoff is the standard");
probe("Q2 signoff      ", "rcv-signoff", "Who is authorized to sign");
probe("Q3 SoR policy   ", "rcv-system", "sole system of record group-wide");
probe("Q3 new conflict ", "rcv-system", "dead ritual");
probe("Q4 claims window", "rcv-claims", "policy or aspiration");
probe("Q5 oslo dblkey  ", "rcv-system", "re-keys into the AS/400");
