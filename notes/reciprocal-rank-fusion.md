---
id: 20261016-reciprocal-rank-fusion
title: Reciprocal Rank Fusion
type: note
tags: [information-retrieval, topic/search]
summary: Merge rankings by summing 1/(k+rank); no score normalization needed.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060000-kb-and-memory-systems-research]]"]
status: stable
superseded_by: 
---

# Reciprocal Rank Fusion

RRF fuses multiple result lists by position, scoring each item sum(1/(k+rank)) with k≈60, so lexical and semantic scores need no normalization. It is the standard glue for [[hybrid-search]].

## Log
- 2026-10-16 — created from [[20261016T060000-kb-and-memory-systems-research]]
