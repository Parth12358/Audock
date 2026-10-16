---
id: 20261016-memory-write-policy
title: Memory write policy
type: note
tags: [agentic-memory, topic/lifecycle]
summary: Classify every write ADD/UPDATE/DELETE/NOOP against the most similar existing memories.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Memory write policy

Mem0 extracts atomic facts and, before writing, compares them to the top-k most similar existing memories and classifies the write as ADD / UPDATE / DELETE / NOOP. This is the concrete mechanism for dedup and contradiction handling — Audock adopts it as its [[dedup-gate]], over a store of [[atomic-notes]].

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]
