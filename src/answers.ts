/**
 * answers — the question interface. THIS MODULE IS THE PRODUCT.
 *
 * Owns: nothing. Assembles the GROUNDED MATERIAL for answering a human
 * question about the client, the honesty contract on every item via the
 * Standing union: evidenced (cited) | claimed (uncited, flagged) |
 * contested (both readings, never a winner) | absent (with the ask or
 * cheap read that would close it — "I don't know, and here's how we find
 * out" is a first-class result).
 *
 * Division of labor, stated plainly: this module does NOT phrase the
 * answer — the consultant does, in conversation. ground() returns material;
 * determinism stays in the engine, judgment stays in the tenancy. That
 * split is what makes "the AI just needs to know the answer or how to get
 * it" auditable: every sentence the consultant says can point at the
 * material it stood on.
 */
// A12: a statement citing a synthesis source takes the standing of that
// source's declared grounds, resolved through the chain — synthesis is
// citable, never standing-upgrading.
// Contract pins (post test-review): topic is a fragment slug or free
// text matched against slugs and statement text; items return in
// DOCUMENT ORDER, statements before callouts; each item carries `where`
// (the fragment slug). Assert by predicate, not position, all the same.
import * as kernel from "./kernel.ts";
import * as ledger from "./ledger.ts";
import type { Standing, Ground, SrcId, CalloutAddr, Claim } from "./types.ts";

/** resolve one citation to its standing: primary sources are evidenced;
 *  a synthesis source takes the WEAKEST standing among its grounds (A12). */
function citeStanding(root: string, src: SrcId, entries: ReturnType<typeof ledger.status>["entries"], depth = 0): Standing {
  if (depth > 8) return { kind: "claimed" };
  const e = entries.find(e => e.id === src);
  if (!e) return { kind: "claimed" };
  if (e.provenance !== "synthesis") return { kind: "evidenced", sources: [src] };
  const sources: SrcId[] = [];
  for (const g of e.grounds ?? []) {
    if (/^SRC-\d+$/.test(g)) {
      const inner = citeStanding(root, g as SrcId, entries, depth + 1);
      if (inner.kind !== "evidenced") return { kind: "claimed" };
      sources.push(...inner.sources);
    } else {
      // a capture address (slug or slug#id): weakest = the cited statement's own standing
      const slug = g.split("#")[0]!;
      const ent = kernel.entities(root).find(x => x.slug === slug);
      const anyEvidenced = ent?.statements.some(st => st.cites.length > 0);
      if (!anyEvidenced) return { kind: "claimed" };
      for (const st of ent!.statements) for (const c of st.cites) {
        const inner = citeStanding(root, c as SrcId, entries, depth + 1);
        if (inner.kind === "evidenced") sources.push(...inner.sources);
      }
    }
  }
  return sources.length ? { kind: "evidenced", sources: [...new Set(sources)] } : { kind: "claimed" };
}

export interface GroundedItem { text: string; standing: Standing; where: string; }

/** the grounded material for a topic: entities, callouts, coverage,
 *  register entries, conflicts — each tagged with its standing */
export function ground(root: string, topic: string): GroundedItem[] {
  const { entries } = ledger.status(root);
  const t = topic.toLowerCase();
  const relevant = [...kernel.entities(root), ...kernel.taxonomy(root)].filter(e =>
    e.slug === topic || e.slug.toLowerCase().includes(t) ||
    e.statements.some(st => st.text.toLowerCase().includes(t)) ||
    e.callouts.some(c => c.text.toLowerCase().includes(t)));
  const items: GroundedItem[] = [];
  for (const e of relevant) {
    for (const st of e.statements) {
      let standing: Standing;
      if (st.cites.length === 0) standing = { kind: "claimed" };
      else {
        const sources: SrcId[] = []; let weakest: Standing = { kind: "evidenced", sources: [] };
        for (const c of st.cites) {
          const s = citeStanding(root, c as SrcId, entries);
          if (s.kind === "evidenced") sources.push(...s.sources); else weakest = s;
        }
        standing = weakest.kind === "evidenced" && sources.length
          ? { kind: "evidenced", sources: [...new Set(sources)] } : { kind: "claimed" };
      }
      items.push({ text: st.text, standing, where: e.slug });
    }
    for (const q of kernel.openQuestions(e)) {
      const srcs = (q.fields.get("sources") ?? "").split(",").map(x => x.trim()).filter(Boolean) as SrcId[];
      if (srcs.length >= 2) {
        const readings: [Claim, Claim] = [{ text: q.text, source: srcs[0]! }, { text: q.text, source: srcs[1]! }];
        items.push({ text: q.text, standing: { kind: "contested", readings }, where: e.slug });
      } else {
        items.push({ text: q.text, standing: { kind: "absent", question: q.addr }, where: e.slug });
      }
    }
  }
  return items;
}
/** resolve grounds to citable form (SRC ids, slug#ID addresses) or refuse by name */
export function cite(root: string, grounds: Ground[]): (SrcId | CalloutAddr)[] {
  const { entries } = ledger.status(root);
  const ents = kernel.entities(root);
  return grounds.map(g => {
    const ref = typeof g === "string" ? g : g.slug;
    if (/^SRC-\d+$/.test(ref)) {
      if (!entries.some(e => e.id === ref)) throw new Error(`cite: ${ref} resolves to no source on file`);
      return ref as SrcId;
    }
    const [slug, local] = ref.split("#");
    const e = ents.find(e => e.slug === slug);
    if (!e) throw new Error(`cite: ${ref} names no capture fragment`);
    if (local && !e.callouts.some(c => c.id === local)) throw new Error(`cite: ${ref} names no callout`);
    return ref as CalloutAddr;
  });
}
