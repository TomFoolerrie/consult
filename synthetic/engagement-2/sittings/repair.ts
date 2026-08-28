/** the repair sitting: check caught the consultant dropping a retired source's citation — restore it */
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import * as check from "../../../src/check.ts";
import * as record from "../../../src/record.ts";
const root = process.argv[2]!;
const p = join(root, "capture/rcv-system.yaml");
writeFileSync(p, readFileSync(p, "utf8").replace(
  'statements:',
  `statements:\n  - text: "SOP v3.1 names LogiCore as system of record (predates the May cutover; consistent with the memo)"\n    cites: [SRC-001]`));
console.log("defects after repair:", JSON.stringify(check.run(root)));
record.checkpoint(root, "repair: restore SOP citation the rewrite dropped (check-caught)");
