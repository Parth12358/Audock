---
id: 20261016-audock-retrieval-strategy
title: Audock retrieval strategy
type: note
tags: [audock, topic/search]
summary: Lexical ripgrep + word-boundary scoring + summary boost; defer embeddings until needed.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060100-audock-design-decisions]]"]
status: stable
superseded_by: 
---

# Audock retrieval strategy

Audock answers from a cheap CLI probe: ripgrep candidates, word-boundary scoring, and a `summary:` boost that is the no-infra form of [[contextual-retrieval]]. It intentionally skips the semantic half of [[hybrid-search]] per [[skip-vectors-under-200k]], and bounds results to respect [[lost-in-the-middle]].

## Log
- 2026-10-16 — created from [[20261016T060100-audock-design-decisions]]
