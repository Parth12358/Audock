---
name: audock
description: Maintain and query the Audock documentation knowledge base (an Obsidian-compatible Markdown vault). Use when the user wants to add/capture/remember something into Audock, look something up in it, or tidy it — e.g. "add this to audock", "save this to my notes", "what does audock say about X", "query the vault", "reindex", "run doctor on the vault".
---

# Audock librarian

Operate the Audock vault. The vault root is this project (where `tools/audock` and `CLAUDE.md`
live). `CLAUDE.md` holds the full protocol and invariants — follow them exactly. This skill is
the quick operator's cheat-sheet.

## Invariants (never break)
- `sources/` bodies are **immutable, append-only** — never rewrite a capture (only its
  `distilled_into:` frontmatter may be appended to).
- Notes change **additively**: append a dated `## Log` line and bump `updated:`; never delete.
- Every note cites provenance in `sources:`; one concept per note.
- **Commit to git after every mutation.**

## Add / capture / remember  → INGEST
1. `tools/audock ingest <file|url|-> --type conversation|code|web|manual [--title ..] [--ref ..]`
   (stdin via `-`). Writes a verbatim, hashed capture to `sources/`. If it reports a duplicate,
   reuse the existing source.
2. Search first: `tools/audock query "<distinctive phrase>"`.
   - New concept → `tools/audock new note "Title"`, fill the body (distilled, not verbatim),
     set `tags:`, `sources: ["[[<source-id>]]"]`, add `[[wikilinks]]`, set `status: stable`.
   - Existing concept → append a dated `## Log` line, add the source to `sources:`, integrate
     the fact additively, bump `updated:`.
3. Append the new note to the source's `distilled_into:`.
4. Link the note from the right `maps/<domain>` MOC (make one with `new moc` if needed);
   ensure the MOC is reachable from `index.md`.
5. `tools/audock reindex` → `git add -A && git commit -m "ingest(<kind>): <title>"`.

## Look up / query  → QUERY
1. Read `index.md`, then the relevant `maps/<domain>` MOC.
2. `tools/audock query "<terms>" [--tag T] [--type note] [--since YYYY-MM-DD] [--json]`.
3. Follow `[[wikilinks]]` from top hits. Cite note ids. For exact fidelity, open the
   `sources:` capture (the lossless path). If absent, say so and offer to INGEST.

## Tidy  → MAINTAIN
`tools/audock doctor` → fix orphans (wire into a MOC), broken links, merge duplicates (keep one
canonical note + alias + `## Log` pointer, never hard-delete), refresh stale notes. Then
`reindex` and commit `maintain: <summary>`.
