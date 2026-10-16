---
id: 20261016-contextual-retrieval
title: Contextual retrieval
type: note
tags: [information-retrieval, topic/search]
summary: Prepend a short context prefix to each chunk before indexing — the biggest quality lever.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Contextual retrieval

Anthropic's contextual retrieval prepends 1–2 sentences situating each chunk in its parent document before embedding/BM25: −35% retrieval failure, −49% with contextual BM25, −67% adding [[reranking]]. Audock's note `summary:` field is the cheap, no-embeddings version of this lever (see [[audock-retrieval-strategy]]).

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]
