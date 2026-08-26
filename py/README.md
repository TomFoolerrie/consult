# py — the one Python seam (MOCK-OUT)

The language ruling (2026-08-26): the engine is TypeScript; Python remains
exactly here — `render_worker`, a bounded subprocess that owns Word XML and
nothing else.

Contract: a versioned JSON job on stdin (the compiled plan: ordered
sections, resolved bodies, skin capabilities, title) → a JSON result on
stdout (path, stats, warnings). All content decisions are made in
TypeScript before the job is emitted; the worker formats, it never thinks.
A missing or broken worker is a named refusal at the render verb only —
nothing else in the system touches Python.

The worker's internals port from the oracle's render/docx layer (the
battle-scarred part worth not rewriting). Output priority is shifting away
from docx toward YAML/markdown anyway; if a future ruling adds an html or
md skin, those renderers are TypeScript and this directory does not grow.
