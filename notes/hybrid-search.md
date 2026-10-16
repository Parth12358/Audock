---
id: 20261016-hybrid-search
title: Hybrid search
type: note
tags: [information-retrieval, topic/search]
summary: Combine lexical (BM25/ripgrep) and semantic retrieval; fuse the two rankings.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Hybrid search

Lexical search nails exact terms; semantic search catches paraphrase. Successful systems run both and fuse them with [[reciprocal-rank-fusion]], then apply [[reranking]]. Audock ships the lexical half today and defers the semantic half — see [[skip-vectors-under-200k]] and [[audock-retrieval-strategy]].

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]
