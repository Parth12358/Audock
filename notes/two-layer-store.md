---
id: 20261016-two-layer-store
title: Two-layer store
type: note
tags: [audock, topic/architecture]
summary: Immutable verbatim sources + distilled atomic notes that cite them = lossless + usable.
created: 2026-10-16
updated: 2026-10-16
aliases: []
sources: ["[[20261016T060100-audock-design-decisions]]"]
status: stable
superseded_by: 
---

# Two-layer store

Audock separates `sources/` (byte-verbatim, immutable, append-only captures) from `notes/` (distilled [[atomic-notes]] that cite their sources). Distillation is additive, so you can always drill from a note down to the exact source — see [[lossless-storage]]. The shipped [[embeddings]] note is a worked example of this pattern.

## Log
- 2026-10-16 — created from [[20261016T060100-audock-design-decisions]]

## Related
<!-- AUDOCK:RELATED:BEGIN -->
- [[20261016-atomic-notes|Atomic notes]]
- [[20261016-audock|Audock (the system)]]
- [[20261016-lossless-storage|Lossless storage]]
<!-- AUDOCK:RELATED:END -->
