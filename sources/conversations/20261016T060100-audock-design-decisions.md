---
id: 20261016T060100-audock-design-decisions
title: Audock design decisions
type: source
origin: conversation
origin_ref: audock-design-session
captured: 2026-10-16T06:01:00Z
hash: sha256:84dcd82ebb3a73ad02f1f80974b9e0c58ffa6af6aa5f68f69cf27cc7c30b76e4
distilled_into: ["[[two-layer-store]]", "[[lossless-storage]]", "[[audock-retrieval-strategy]]", "[[dedup-gate]]"]
---
Audock is a two-layer store: sources/ holds byte-verbatim, immutable, append-only captures (the lossless ground truth); notes/ holds distilled atomic notes that cite their sources. Losslessness is guaranteed three ways: immutable sources, append-only note logs, and git history. Retrieval is deliberately lexical (ripgrep + word-boundary scoring + a summary boost); embeddings are deferred because the vault is far under ~200K tokens. Ingestion runs a dedup gate (ADD/UPDATE/SUPERSEDE/NOOP) so notes/ does not accumulate near-duplicates or contradictions.
