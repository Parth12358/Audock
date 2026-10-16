---
name: audock
description: Read from and write to the Audock knowledge base (an Obsidian-compatible Markdown vault). Invoke this PROACTIVELY, without being asked — the CLI is cheap (tiny output). Run `audock context "<question>"` before answering any factual/technical question the vault might cover, and offer to ingest anything worth keeping (decisions, findings, snippets, links). Also use on explicit cues: "add this to audock", "save this", "remember this", "what does audock/my notes say about X", "query the vault", "reindex", "run doctor".
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

## Look up / query  → QUERY  (lead with the cheapest step)
1. `tools/audock context "<question>" [--tag T] [--k N]` — bounded, comment-stripped answer
   pack with provenance; answer most questions from this one call.
2. `tools/audock query "<terms>" [--tag T] [--type note] [--since DATE] [--json]` — ranked hits.
3. `tools/audock show <id>` — one note, compact (follow `[[wikilinks]]` by `show`-ing ids).
4. `tools/audock show <source-id> --raw` — verbatim source for exact quotes/numbers/code.
5. Cite note ids. If nothing matches, say so and offer to INGEST.
Avoid Read-ing whole files or browsing `index.md`/MOCs for answers — that costs tokens; the
CLI output is tiny by design.

## Tidy  → MAINTAIN
`tools/audock doctor` → fix orphans (wire into a MOC), broken links, merge duplicates (keep one
canonical note + alias + `## Log` pointer, never hard-delete), refresh stale notes. Then
`reindex` and commit `maintain: <summary>`.
