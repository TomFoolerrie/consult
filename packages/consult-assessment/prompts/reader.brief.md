# Brief — {{agent}}, group {{group}}, mode: {{mode}}

Your author name for every ledger command: `{{agent}}` (group `{{group}}`).

Taxonomy: {{taxonomy}}
Context-profile: `{{context}}` — read first.

Pre-reads, in order (context, not sources):
{{pre_read}}

Reference (consult only if relevant):
{{reference}}

Orchestrator note for this group: {{note}}

{{resume}}

## Sources, in this order (id → path per the registry at `{{registry}}`), each with its reading strategy
{{sources}}

## Output per document
Write rows as JSONL to `{{workdir}}/{{group}}-<src-id>.jsonl`, then append:
```
{{sh}} ledger append findings --author {{agent}} --group {{group}} --from {{workdir}}/{{group}}-<src-id>.jsonl
```
Example row for this engagement's taxonomy:
```json
{{finding_example}}
```

## Prior findings — for the SITUATE pass only (after your own blind pass)
{{prior}}

## Open proposals addressed to you (edit mode)
{{proposals}}
