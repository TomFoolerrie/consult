/** Fictional, SCRIPTED integration demonstration. No model calls, private data,
 * or real human approvals. Exercises the production engine and package writers.
 * Usage: node --experimental-strip-types synthetic/engagement-5/run.ts [NEW_ROOT]
 * Run with Python/PyYAML and repository Node dependencies available. */
import { existsSync, mkdirSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";
import { parse, stringify } from "yaml";
import * as ledger from "../../src/ledger.ts";
import { reviewEvidence, renderReview } from "../../harness/assessment-evidence.ts";

const repo = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const packageRoot = join(repo, "packages/consult-assessment");
const requested = process.argv[2];
if (requested && existsSync(resolve(requested))) throw new Error("demo: choose a new root; never overwrite an existing engagement");
const root = requested ? resolve(requested) : mkdtempSync(join(tmpdir(), "consult-assessment-demo-"));
function put(rel: string, text: string) { const p = join(root, rel); mkdirSync(dirname(p), { recursive: true }); writeFileSync(p, text); return p; }
function exec(command: string, args: string[], input?: string) {
  const result = spawnSync(command, args, { cwd: root, encoding: "utf8", ...(input === undefined ? {} : { input }) });
  if (result.status !== 0) throw new Error(`${command} ${args.join(" ")}: ${result.stderr || result.stdout}`);
  return result.stdout.trim();
}
function py(script: string, args: string[], input?: string) { return exec("python3", [join(packageRoot, "scripts", script), ...args], input); }
mkdirSync(root, { recursive: true });
for (const path of ["_sources/new", "_sources/processed", "_sources/parked", "capture/_taxonomy", "_registers/sessions"])
  mkdirSync(join(root, path), { recursive: true });
exec("git", ["init", "-q"]);
put("OBJECTIVE.md", "# Fictional assessment\nAssess payment-review evidence and prepare a reviewable first draft. Distinguish exceptions from proven duplicate payments.\n");
put("STATE.md", "# State\n## now\nScripted integration demonstration; no live model or real approvals.\n## human's standing guidance\nPreserve uncertainty and source traceability.\n");
const note = ledger.route(root, put("_sources/new/interview.md", "# Fictional controller interview\nThe controller reports that invoices are checked for duplicates before payment.\nNo completed review evidence was supplied with this interview.\n"), ["payment-review"]);
const csv = ledger.route(root, put("_sources/new/payments.csv", "invoice_id,vendor,amount\nINV-001,Example Supplies,125\nINV-001,Example Supplies,125\nINV-002,Example Services,90\nINV-003,Example Repairs,75\n"), ["payment-review"]);
const base = "_synthesis/assessment/demo";
const dir = join(root, base, "ledger");
const taxonomy = put(`${base}/taxonomy.yaml`, stringify({ name: "payment-evidence", axes: { process: { label: "Process", primary: true, required: true, values: ["Payment review"] } }, scales: { severity: { 1: "Low", 2: "Medium", 3: "High" }, impact: { 1: "Low", 2: "Medium", 3: "High" }, effort: { 1: "Low", 2: "Medium", 3: "High" } }, figures: [], rules: "An exception is not proof of a duplicate payment; interview assertions remain stated." }));
const manifest = put("assessment.yaml", stringify({ mode: "consult", consult_root: root, capture_intent: ["payment-review"], context: "OBJECTIVE.md", taxonomy,
  paths: { ledger_dir: `${base}/ledger`, workdir: `${base}/work`, out: `${base}/out` }, source_notes: { [note]: { kind: "interview" }, [csv]: { kind: "data" } },
  groups: [{ id: "G1", agent: "reader-G1", sources: [note, csv], note: "Distinguish reported checks from exported exceptions" }], story_note: "Fictional demonstration: evidence limitations and practical follow-up, not a finished deck." }));
py("ledger.py", ["--ledger-dir", dir, "init"]);
py("run.py", ["render", "--manifest", manifest, "--op", "extract", "--group", "G1", "--format", "brief"]);
const shim = join(root, base, "work/assess.py");
exec("python3", [shim, "data", "run", "duplicates", csv, "--key", "invoice_id", "--amount", "amount"]);
const analysis = ledger.readBook(root).entries.find(s => s.provenance === "synthesis")!;
function append(layer: string, author: string, row: unknown) {
  return py("ledger.py", ["--ledger-dir", dir, "--taxonomy", taxonomy, "append", layer, "--author", author, "--group", "G1"], JSON.stringify(row) + "\n");
}
append("findings", "reader-G1", { type: "observation", process: "Payment review", severity: 1, evidence_basis: "stated", observation: "The controller reports checking invoices for duplicates before payment.", sources: [`${note}:L2-L3`] });
append("findings", "reader-G1", { type: "risk", process: "Payment review", severity: 2, evidence_basis: "observed", observation: "INV-001 was paid twice.", sources: [`${csv}:R1`, `${csv}:R2`, `${analysis.id}:L5-L12`] });
// Deliberately overreaching sample above: the simulated consultant corrects it.
// The check cannot detect the semantic error; versioned human review is the point.
py("ledger.py", ["--ledger-dir", dir, "edit", "F-002", "--author", "reader-G1", "--set", "observation=Two exported records share invoice identifier INV-001 and amount 125; whether these represent duplicate payments is unresolved.", "--reason", "SCRIPTED review correction: repeated export rows are not proof of two payments"]);
py("run.py", ["check", "--manifest", manifest]);
const resume = py("run.py", ["next", "--manifest", manifest]); // fresh process, no agent memory
if (!resume.includes("findings gate")) throw new Error(`unexpected resume: ${resume}`);
function simulatedGate(name: string, status: string, note: string) {
  py("run.py", ["gate", "--manifest", manifest, "--name", name, "--status", status, "--note", `SCRIPTED FIXTURE ONLY; not a real human approval: ${note}`]);
}
simulatedGate("findings", "passed", "the corrected two-finding sample is the expected fixture");
put(`${base}/work/retro-extract.md`, "# Scripted extraction retrospective\nTwo supplied sources accounted for. The overreaching duplicate-payment statement was corrected through its author. No extraction model was exercised.\n");
simulatedGate("normalized", "done", "single group; no open cross-author proposals in this fixture");
simulatedGate("revise", "passed", "scripted calibration preserved the observed/stated distinction");
if (!py("run.py", ["next", "--manifest", manifest]).includes("--op themes")) throw new Error("runner did not advance to themes");
append("themes", "themer", { theme: "Reported prevention needs operating evidence", root_cause: "Completed review evidence and payment identifiers have not yet been supplied", impact: "Duplicate-payment exposure cannot yet be confirmed or dismissed", findings: ["F-001", "F-002"] });
append("recommendations", "recommender", { solution: "Obtain a completed review and trace INV-001 to distinct payment identifiers", principle: "Corroborate the reported control and resolve the exception before concluding", themes: ["T-001"], what_changes: "Assessment conclusions reflect operating evidence", what_stops: "Treating duplicate export rows as proven duplicate payments" });
append("initiatives", "planner", { initiative: "Verify one review cycle and investigate INV-001", owner: "Controller", impact: 2, effort: 1, time_required: "One week", success_measure: "Review evidence inspected and INV-001 disposition supported", recommendations: ["R-001"] });
py("run.py", ["check", "--manifest", manifest, "--gate", "story"]);
const review = reviewEvidence(root, join(dir, "findings.jsonl"));
if (!review.ok) throw new Error(review.errors.join("\n"));
put(`${base}/out/evidence-review.md`, renderReview(review));
for (const operation of ["tables", "figures"]) py("render.py", [operation, "--manifest", manifest]);
put(`${base}/out/story.md`, "# Fictional assessment — consultant draft\n\nThe controller reports checking for duplicates before payment [F-001]. That is a reported practice, not independent verification of operation.\n\nTwo exported rows share invoice identifier INV-001 and amount 125 [F-002]. We have not established whether they represent duplicate payments.\n\nThe immediate need is corroboration, not a definitive control-failure conclusion [T-001]. Obtain one completed review and trace the two rows to payment identifiers [R-001]. The controller can own this bounded verification task [I-001].\n");
py("render.py", ["bundle", "--manifest", manifest]);
put(`${base}/work/retro-layers.md`, "# Scripted analytical retrospective\nLocal lineage validates through the narrative bundle. Source support still requires professional review; all judgments here were supplied by the fixture.\n");
if (!py("run.py", ["next", "--manifest", manifest]).startsWith("[DONE]")) throw new Error("initial scripted run did not reach DONE");
// A second run must retain the first publication and mint a versioned artifact.
const firstBytes = readFileSync(join(root, analysis.file), "utf8");
exec("python3", [shim, "data", "run", "duplicates", csv, "--key", "invoice_id", "--amount", "amount"]);
if (readFileSync(join(root, analysis.file), "utf8") !== firstBytes) throw new Error("rerun overwrote prior evidence");
const publications = ledger.readBook(root).entries.filter(s => s.provenance === "synthesis");
if (publications.length !== 2) throw new Error("expected two immutable analysis versions");
// A later client artifact changes the assessment; old sources and outputs remain.
put(`${base}/out/review-before-response.md`, renderReview(review));
exec("git", ["add", "."]);
exec("git", ["-c", "user.name=CONSULT synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "Fictional initial review before new evidence"]);
const response = ledger.route(root, put("_sources/new/payment-register.csv", "payment_id,invoice_id,amount\nPAY-101,INV-001,125\nPAY-102,INV-002,90\n"), ["payment-review"]);
const revisedManifest = parse(readFileSync(manifest, "utf8"));
revisedManifest.groups[0].sources.push(response);
writeFileSync(manifest, stringify(revisedManifest));
simulatedGate("revise", "pending", "new evidence requires a new review; no automatic approval carry-forward");
const responseRecord = ledger.sourceRecord(root, response, 1);
if (responseRecord.values[1] !== "INV-001") throw new Error("unexpected fictional response");
py("ledger.py", ["--ledger-dir", dir, "edit", "F-002", "--author", "reader-G1", "--set", "observation=Two exported records share invoice identifier INV-001 and amount 125; the subsequently supplied payment-register extract lists one INV-001 payment. This observation is limited to the supplied extracts.", "--set", `sources=${[`${csv}:R1`, `${csv}:R2`, `${response}:R1`, `${analysis.id}:L5-L12`].join(";")}`, "--reason", "SCRIPTED new-evidence revision: distinguish updated evidence from a silent overwrite"]);
py("ledger.py", ["--ledger-dir", dir, "edit", "T-001", "--author", "themer", "--set", "theme=Payment evidence narrows the exception; operating review and register completeness remain unverified", "--set", "root_cause=Completed review evidence is still absent from the assessment and payment-register completeness has not been confirmed", "--set", "impact=The supplied register supports one payment, not a proven duplicate payout; finish corroboration before closing", "--reason", "SCRIPTED reconsideration after new register extract"]);
py("ledger.py", ["--ledger-dir", dir, "edit", "R-001", "--author", "recommender", "--set", "solution=Confirm payment-register completeness and obtain one completed duplicate-review record", "--reason", "SCRIPTED changed follow-up after the payment identifier was supplied"]);
py("run.py", ["check", "--manifest", manifest, "--gate", "story"]);
put(`${base}/out/story.md`, "# Fictional assessment — updated consultant draft\n\nThe controller reports pre-payment duplicate checks; operation remains unverified [F-001].\n\nThe original export repeats INV-001, but a later payment-register extract lists one INV-001 payment [F-002]. The evidence does not establish that the invoice was paid twice. Register completeness still needs confirmation [T-001].\n\nThe follow-up is now narrower: confirm the register is complete and inspect one completed control review [T-001] [R-001]. Keep the controller's bounded verification task open until that evidence is inspected [I-001].\n");
const revisedReview = reviewEvidence(root, join(dir, "findings.jsonl"));
if (!revisedReview.ok) throw new Error(revisedReview.errors.join("\n"));
if (!py("run.py", ["next", "--manifest", manifest]).includes("second look")) throw new Error("new evidence did not reopen scripted review");
simulatedGate("revise", "passed", "updated findings and narrowed follow-up match the scripted response fixture");
for (const operation of ["tables", "figures", "bundle"]) py("render.py", [operation, "--manifest", manifest]);
const finalNext = py("run.py", ["next", "--manifest", manifest]);
if (!finalNext.startsWith("[DONE]")) throw new Error(`updated run incomplete: ${finalNext}`);
put("capture/payment-review.yaml", stringify({ slug: "payment-review", type: "process-step", scope: "Payment-review evidence and exported exceptions", statements: [
  { text: "The controller reports pre-payment duplicate checks.", cites: [note] },
  { text: "The supplied export contains repeated invoice identifiers; whether they represent duplicate payments is unresolved.", cites: [csv, ...publications.map(p => p.id)] },
  { text: "The subsequently supplied payment-register extract lists one payment for INV-001; completeness still needs confirmation.", cites: [response] }], questions: [{ id: "Q-1", text: "Do the repeated INV-001 records correspond to distinct payments, and what review evidence exists?" }] }));
ledger.retire(root, note); ledger.retire(root, csv); ledger.retire(root, response);
const retiredReview = reviewEvidence(root, join(dir, "findings.jsonl"));
if (!retiredReview.ok) throw new Error("retirement broke citations");
put(`${base}/out/evidence-review.md`, renderReview(retiredReview));
put(`${base}/RESULTS.md`, `# Scripted integration results\n\nPASS: verified text and CSV references; actual package writers and validators; source-backed analysis registration; simulated review correction preserving prior versions; local analytical layers; process restart; rendered review/narrative bundle; immutable rerun; new-evidence revisions of the finding/theme/recommendation; retained before-response review; source retirement.\n\nNo model was invoked. Findings and narrative were scripted. No private data or real approvals were used. This demonstrates connected mechanics, not analytical quality or usability.\n\nFresh-process next action:\n\n${resume}\n\nFinal scripted method state:\n\n${finalNext}\n\nAnalysis versions: ${publications.map(p => p.id).join(", ")}\n`);
exec("git", ["add", "."]);
exec("git", ["-c", "user.name=CONSULT synthetic", "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "Scripted fictional assessment integration"]);
console.log(JSON.stringify({ root, review: join(root, base, "out/evidence-review.md"), story: join(root, base, "out/story.md"), results: join(root, base, "RESULTS.md") }, null, 2));
