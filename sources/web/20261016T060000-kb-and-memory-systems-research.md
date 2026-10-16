---
id: 20261016T060000-kb-and-memory-systems-research
title: KB & memory systems research
type: source
origin: web
origin_ref: research-synthesis-2026-10
captured: 2026-10-16T06:00:00Z
hash: sha256:a42c14a5a708a072df73feed2fcd76cdbf5a72a1b54b9d03f7a8d9cd2fe02b1b
distilled_into: ["[[atomic-notes]]", "[[evergreen-notes]]", "[[maps-of-content]]", "[[stable-note-ids]]", "[[tags-vs-links]]", "[[epistemic-status]]", "[[tiered-memory]]", "[[memory-write-policy]]", "[[markdown-as-source-of-truth]]", "[[dont-store-rederivable]]", "[[hybrid-search]]", "[[contextual-retrieval]]", "[[reciprocal-rank-fusion]]", "[[reranking]]", "[[lost-in-the-middle]]", "[[skip-vectors-under-200k]]"]
---
Synthesis of how successful knowledge-base and LLM-memory systems are designed.

Zettelkasten / evergreen (Matuschak, Luhmann, Nick Milo): atomic concept-per-note titled as a claim; density of links beats volume; Maps of Content are curated hubs created at a 'mental squeeze point'; a stable unique ID keeps links from breaking.

Agentic memory: MemGPT/Letta use tiered memory (small in-context core + searchable recall/archival paged via tool calls). Mem0 extracts atomic facts and, against the top-k most similar existing memories, classifies each write ADD/UPDATE/DELETE/NOOP. Claude Code auto-memory skips anything re-derivable and types each memory. Basic Memory keeps Markdown as source of truth with a disposable index and no auto-decay.

Retrieval: hybrid lexical+semantic fused with Reciprocal Rank Fusion, then a cross-encoder rerank of the top ~20. Anthropic contextual retrieval: a per-chunk context prefix cut retrieval failure 35%, +BM25 49%, +rerank 67%. 'Lost in the middle': models use the start and end of context best, so order by relevance and keep the set small. Under ~200K tokens, skip the vector DB and just load the KB with prompt caching.

Obsidian: pure timestamp-ID filenames clutter the graph; prefer a readable title filename plus a stable id and aliases. Tags describe what a note is; links do navigation (only [[links]] create graph edges). Dataview is stable but effectively frozen — fine for read-side, don't build core logic on it.
