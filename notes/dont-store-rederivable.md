---
id: 20261016-dont-store-rederivable
title: Don't store the re-derivable
type: note
tags: [agentic-memory, topic/lifecycle]
summary: Skip memories you can recompute; type what you do keep. The top anti-bloat rule.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Don't store the re-derivable

Claude Code's auto-memory skips anything derivable from the codebase or already written elsewhere, and types each memory it keeps. For Audock this means not distilling what is already verbatim in a source — a decision the [[memory-write-policy]] NOOP branch makes.

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]
