---
id: 20261016-lost-in-the-middle
title: Lost in the middle
type: note
tags: [information-retrieval, topic/context]
summary: LLMs use the start and end of context best; order by relevance and keep the set small.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Lost in the middle

Retrieval quality degrades when the relevant passage sits in the middle of a long context (a U-shaped curve, >30% degradation). So order retrieved notes by relevance at the head and tail and cap the set — which is why Audock's `context` command is bounded and relevance-sorted (see [[audock-retrieval-strategy]] and [[reranking]]).

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]

## Related
<!-- AUDOCK:RELATED:BEGIN -->
- [[20261016-audock-retrieval-strategy|Audock retrieval strategy]]
- [[20261016-information-retrieval|Information Retrieval]]
- [[20261016-reranking|Reranking]]
<!-- AUDOCK:RELATED:END -->
