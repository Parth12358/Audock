---
id: 20261016-audock-retrieval-strategy
title: Audock retrieval strategy
type: note
tags: [audock, topic/search]
summary: Built-in field-weighted BM25 with light stemming and a summary boost; defer embeddings until needed.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060100-audock-design-decisions]]"]
status: stable
superseded_by: 
---

# Audock retrieval strategy

Audock answers from a cheap CLI probe: ripgrep candidates, word-boundary scoring, and a `summary:` boost that is the no-infra form of [[contextual-retrieval]]. It intentionally skips the semantic half of [[hybrid-search]] per [[skip-vectors-under-200k]], and bounds results to respect [[lost-in-the-middle]].

**Update (2026-10-16):** candidates no longer come from ripgrep — every query runs a pure-Python field-weighted BM25 scan (title/summary weighted over body, light stemming), so there are no external tools.

## Log
- 2026-10-16 — created from [[20261016T060100-audock-design-decisions]]
- 2026-10-16 — corrected: ranking is built-in BM25, not ripgrep

## Related
<!-- AUDOCK:RELATED:BEGIN -->
- [[20261016-audock|Audock (the system)]]
- [[20261016-contextual-retrieval|Contextual retrieval]]
- [[20261016-hybrid-search|Hybrid search]]
- [[20261016-lost-in-the-middle|Lost in the middle]]
- [[20261016-skip-vectors-under-200k|Skip vectors under ~200K tokens]]
- [[20261016-tiered-memory|Tiered memory]]
<!-- AUDOCK:RELATED:END -->
