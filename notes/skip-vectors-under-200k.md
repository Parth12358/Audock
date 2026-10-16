---
id: 20261016-skip-vectors-under-200k
title: Skip vectors under ~200K tokens
type: note
tags: [information-retrieval, topic/search]
summary: Below ~200K tokens, load the whole KB with prompt caching instead of a vector DB.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Skip vectors under ~200K tokens

Anthropic's guidance: contextual embeddings only pay off beyond ~200K tokens; under that, just load the KB and rely on prompt caching. This is why Audock's [[audock-retrieval-strategy]] stays lexical for now and avoids [[hybrid-search]]'s semantic half until the vault grows.

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]
