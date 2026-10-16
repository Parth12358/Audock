---
id: 20261016-markdown-as-source-of-truth
title: Markdown as source of truth
type: note
tags: [agentic-memory, topic/architecture]
summary: Keep human-readable Markdown canonical and the search index disposable; no auto-decay.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Markdown as source of truth

Basic Memory stores one Markdown note per entity and treats its SQLite index as a disposable cache rebuilt from the Markdown; it deliberately runs no automatic decay or consolidation. Audock takes the same stance — the files are truth (see [[lossless-storage]]), and supersede is explicit (see [[epistemic-status]]).

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]
