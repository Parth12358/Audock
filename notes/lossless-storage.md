---
id: 20261016-lossless-storage
title: Lossless storage
type: note
tags: [audock, topic/architecture]
summary: Three independent recovery paths: immutable sources, append-only logs, git history.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060100-audock-design-decisions]]"]
status: stable
superseded_by: 
---

# Lossless storage

Nothing is ever destroyed: `sources/` bodies are immutable (hash-verified), note changes only append to a `## Log`, and git records every mutation. Any prior state is recoverable three ways. This realizes [[markdown-as-source-of-truth]] for the [[two-layer-store]].

## Log
- 2026-10-16 — created from [[20261016T060100-audock-design-decisions]]
