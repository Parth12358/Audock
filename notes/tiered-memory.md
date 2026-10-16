---
id: 20261016-tiered-memory
title: Tiered memory
type: note
tags: [agentic-memory, topic/architecture]
summary: Keep a small in-context core and page the rest in from searchable storage via tools.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Tiered memory

MemGPT/Letta split memory into a small always-in-context core plus searchable recall and archival tiers that the agent pages in and out via explicit tool calls — rather than stuffing everything into the context window. Audock mirrors this: a tiny CLI probe ([[audock-retrieval-strategy]]) instead of loading the whole vault.

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]

## Related
<!-- AUDOCK:RELATED:BEGIN -->
- [[20261016-agentic-memory|Agentic Memory]]
<!-- AUDOCK:RELATED:END -->
