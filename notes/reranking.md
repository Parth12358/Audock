---
id: 20261016-reranking
title: Reranking
type: note
tags: [information-retrieval, topic/search]
summary: Retrieve a wide shortlist, then reorder with a cross-encoder so the answer surfaces.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Reranking

Retrieve ~20 candidates, then a cross-encoder rerank puts the answer-bearing passage first — the final −67% step on top of [[contextual-retrieval]]. It pairs with [[lost-in-the-middle]]: a small, well-ordered set beats a large dump.

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]
