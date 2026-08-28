/** the question-interface exam — standings must come from ground(), never hand-assigned */
import * as answers from "../../../src/answers.ts";
const root = process.argv[2]!;
const probe = (label: string, topic: string, match: string) => {
  const items = answers.ground(root, topic);
  const hit = items.find(i => i.text.toLowerCase().includes(match.toLowerCase()));
  console.log(`${label}: ${hit ? hit.standing.kind : "NO MATERIAL"}${hit && "sources" in hit.standing ? " " + JSON.stringify((hit.standing as any).sources) : ""}${hit && "question" in hit.standing ? " -> " + (hit.standing as any).question : ""}`);
};
probe("Q1 >=10k approver ", "ap-approval", "$10,000 and above require approval");
probe("Q2 Dana reports to", "ap-approval", "Who does Dana Okafor report to");
probe("Q3 match required ", "ap-payment", "three-way match (PO, receipt, invoice) is required");
probe("Q3 match violated ", "ap-payment", "missing the receipt leg");
probe("Q4 expedite path  ", "ap-payment", "expedite - DO approval' path");
probe("Q5 duplicates     ", "ap-payment", "Kessler Tooling appear twice");
