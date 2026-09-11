/** JSON-over-stdin adapter for skill-produced artifacts. No package-specific
 * schemas in the engine. Output is the authoritative registered source. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { publishSynthesis } from "../src/ledger.ts";
import { locate } from "../src/desk.ts";

try {
  if (process.argv.length !== 4 || process.argv[2] !== "--root") throw new Error("usage: publish-synthesis.ts --root ENGAGEMENT (JSON on stdin)");
  const root = resolve(process.argv[3]!);
  const found = locate(root);
  if (found.health.kind === "contradiction") throw new Error(`publish synthesis: ${found.health.what}`);
  const request = JSON.parse(readFileSync(0, "utf8"));
  if (!request || typeof request.file !== "string" || !Array.isArray(request.intent) || request.intent.some((x: unknown) => typeof x !== "string")
    || !Array.isArray(request.inputs) || request.inputs.some((x: any) => !x || typeof x.id !== "string" || typeof x.hash !== "string"))
    throw new Error("publish synthesis: file, intent list and input id/hash list required");
  console.log(JSON.stringify(publishSynthesis(found.root, resolve(found.root, request.file), request.intent, request.inputs)));
} catch (error) {
  console.error((error as Error).message);
  process.exitCode = 2;
}
