---
id: 20261016-dedup-gate
title: Dedup gate
type: note
tags: [audock, topic/lifecycle]
summary: Before writing a note, check similar notes and choose ADD/UPDATE/SUPERSEDE/NOOP.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060100-audock-design-decisions]]"]
status: stable
superseded_by: 
---

# Dedup gate

On ingest, `audock similar` surfaces the most similar existing notes so the librarian picks ADD, UPDATE, SUPERSEDE, or NOOP instead of forking a near-duplicate — Audock's take on the [[memory-write-policy]], keeping the store of [[atomic-notes]] clean and honoring [[epistemic-status]].

## Log
- 2026-10-16 — created from [[20261016T060100-audock-design-decisions]]
