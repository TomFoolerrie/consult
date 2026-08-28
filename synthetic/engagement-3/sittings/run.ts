/** Engagement 3 — the sparse seed: mostly honest absences. */
import { mkdirSync, writeFileSync, copyFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { execSync } from "node:child_process";
import * as ledger from "../../../src/ledger.ts";
import * as record from "../../../src/record.ts";
import * as check from "../../../src/check.ts";
import * as desk from "../../../src/desk.ts";
import * as asks from "../../../src/asks.ts";
import * as answers from "../../../src/answers.ts";
import * as findings from "../../../src/findings.ts";

const HERE = dirname(fileURLToPath(import.meta.url));
const root = process.argv[2]!;
for (const d of ["_sources/new", "_registers", "_synthesis", "capture/_taxonomy"]) mkdirSync(join(root, d), { recursive: true });
writeFileSync(join(root, "STATE.md"), "# state pad\n## now\nCorvus onboarding: expect mostly absences; Elena responds slowly — batch the asks.\n");
copyFileSync(join(HERE, "..", "objective.md"), join(root, "OBJECTIVE.md"));
execSync("git init -q && git add -A && git commit -qm seed", { cwd: root });
record.budgetSet(root, 100_000);

copyFileSync(join(HERE, "..", "seed/onboarding-checklist.md"), join(root, "_sources/new/onboarding-checklist.md"));
const cl = ledger.route(root, join(root, "_sources/new/onboarding-checklist.md"), ["ob-conflicts", "ob-kyc", "ob-dataroom"], { provenance: "client" });

const node = (s: string, sc: string) => writeFileSync(join(root, "capture/_taxonomy", `${s}.yaml`), `slug: ${s}\ntype: taxonomy-node\nscope: ${JSON.stringify(sc)}\nstatements: []\nquestions: []\n`);
node("ob-conflicts", "conflict checking"); node("ob-kyc", "KYC"); node("ob-dataroom", "data room"); node("ob-letter", "engagement letter");
const frag = (slug: string, body: string) => writeFileSync(join(root, "capture", `${slug}.yaml`), body);
frag("ob-conflicts", `slug: ob-conflicts\ntype: process-step\nstatements:\n  - text: "A conflict check appears on the 2023 checklist with the annotation 'ask Elena' for ownership"\n    cites: [${cl}]\nquestions:\n  - id: Q-1\n    text: "Who runs the conflict check, against what, and when?"\n`);
frag("ob-kyc", `slug: ob-kyc\ntype: process-step\nstatements:\n  - text: "A KYC file is opened per the checklist; no owner or trigger recorded anywhere"\n    cites: [${cl}]\nquestions:\n  - id: Q-1\n    text: "Who owns the KYC file, and what triggers opening it?"\n`);
frag("ob-dataroom", `slug: ob-dataroom\ntype: process-step\nstatements:\n  - text: "The checklist's own note: 'half of this happens over email, checklist rarely used'"\n    cites: [${cl}]\nquestions:\n  - id: Q-1\n    text: "When in the sequence is data room access granted, and by whom?"\n`);
frag("ob-letter", `slug: ob-letter\ntype: process-step\nstatements: []\nquestions:\n  - id: Q-1\n    text: "What does the engagement letter require before work starts?"\n`);

console.log("S1 defects:", JSON.stringify(check.run(root)));
record.spend(root, 4000, 3600, "sitting 1: one thin source, four questions");
record.checkpoint(root, "sitting 1: the map of what we don't know");
console.log("coverage:", desk.coverage(root).map(c => `${c.slug}:${c.status}`).join(" "));

// the engagement-letter question is a document review, not a client ask — ruled not-the-client's this round
asks.close(root, "ob-letter#Q-1", "a legal document we can review ourselves once the data room opens — not Elena's to answer");
// batch the two real asks (Elena is slow — one artifact-shaped batch)
const a1 = asks.propose(root, "Who runs the conflict check, against what lists, and when in the sequence?", ["ob-conflicts#Q-1"], "Elena Marsh");
const a2 = asks.propose(root, "Who owns the KYC file and what triggers opening it?", ["ob-kyc#Q-1"], "Elena Marsh");
for (const id of [a1, a2]) asks.accept(root, id as never);
asks.sent(root);

copyFileSync(join(HERE, "..", "responses/elena-partial.md"), join(root, "_sources/new/elena-partial.md"));
const { src: elena } = asks.respond(root, join(root, "_sources/new/elena-partial.md"), [a1 as never]); // partial: answers a1 ONLY
frag("ob-conflicts", `slug: ob-conflicts\ntype: process-step\nstatements:\n  - text: "Elena Marsh personally runs the conflict check against the deal list and restricted list, before the engagement letter goes out — undocumented, every client since 2019"\n    cites: [${elena}]\n  - text: "A conflict check appears on the 2023 checklist with the annotation 'ask Elena' for ownership"\n    cites: [${cl}]\nquestions: []\n`);

// a finding on thin ground — and the human rejects it; the rejection is case law
const f1 = findings.propose(root, "Onboarding controls exist only as personal habit; the process would not survive Elena's departure", [elena, cl], "key-person-risk");
findings.reject(root, f1, "human: premature on one partial response — revisit when KYC and data room are mapped");

console.log("S2 defects:", JSON.stringify(check.run(root)));
record.spend(root, 5000, 4300, "sitting 2: batch asks, partial fold-in, finding proposed");
record.checkpoint(root, "sitting 2: one answer in, absences held honestly");
const s = desk.state(root);
console.log("DEBTS:", JSON.stringify(s.askDebts));
const probe = (l: string, t: string, m: string) => {
  const i = answers.ground(root, t).find(x => x.text.toLowerCase().includes(m.toLowerCase()));
  console.log(l, "->", i ? i.standing.kind + ("question" in i.standing ? " -> " + (i.standing as any).question : "") : "NO MATERIAL");
};
probe("Q1 conflict owner", "ob-conflicts", "personally runs the conflict check");
probe("Q2 documented?   ", "ob-conflicts", "undocumented, every client since 2019");
probe("Q3 kyc owner     ", "ob-kyc", "Who owns the KYC file");
probe("Q4 dataroom      ", "ob-dataroom", "When in the sequence");
probe("Q5 checklist used", "ob-dataroom", "rarely used");
probe("Q6 letter        ", "ob-letter", "What does the engagement letter require");
console.log("findings:", JSON.stringify(findings.entriesOf(root)));
