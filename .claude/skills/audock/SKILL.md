---
name: audock
description: Read from and write to the Audock knowledge base (an Obsidian-compatible Markdown vault). Invoke this PROACTIVELY, without being asked — the CLI is cheap (tiny output). Run `audock context "<question>"` before answering any factual/technical question the vault might cover, and offer to ingest anything worth keeping (decisions, findings, snippets, links). Also use on explicit cues: "add this to audock", "save this", "remember this", "what does audock/my notes say about X", "query the vault", "reindex", "run doctor".
---

# Audock librarian

Operate the Audock vault. The vault root is this project (where `tools/audock` and `CLAUDE.md`
live). `CLAUDE.md` holds the full protocol and invariants — follow them exactly. This skill is
the quick operator's cheat-sheet.

## Invariants (never break)
- **Human-owned is read-only:** never edit, supersede, move, or delete a note with `locked: true`
  (or tagged `#locked`), nor anything inside `<!-- audock:human -->` … `<!-- /audock:human -->`.
  Read/cite/link only; new knowledge → a separate note linking to it.
- `sources/` bodies are **immutable, append-only** — never rewrite a capture (only its
  `distilled_into:` frontmatter may be appended to).
- Notes change **additively**: append a dated `## Log` line and bump `updated:`; never delete.
- Every note cites provenance in `sources:`; one concept per note.
- **Commit to git after every mutation.**

## Add / capture / remember  → INGEST
1. `tools/audock ingest <file|url|-> --type conversation|code|web|manual [--title ..] [--ref ..]`
   (stdin via `-`). Writes a byte-verbatim, hashed capture to `sources/`. On a duplicate report,
   reuse the existing source.
2. **Dedup gate:** `tools/audock similar "<concept>"`, then choose:
   ADD (new) · UPDATE (append to existing note's `## Log`, add source, bump `updated:`) ·
   SUPERSEDE (make the corrected note; on the old set `status: superseded` +
   `superseded_by: "[[new]]"`) · NOOP (already captured). Don't store the re-derivable.
3. New note → `tools/audock new note "Title"`; fill distilled body, set `tags:`, a one-line
   `summary:` (boosts retrieval), `sources: ["[[<source-id>]]"]`, `[[wikilinks]]`, `status:`.
4. Append the new note to the source's `distilled_into:` (source frontmatter only, never body).
5. Link from the right `maps/<domain>` MOC (make one with `new moc` if needed); keep it reachable
   from `index.md`.
6. `tools/audock reindex` → `git add -A && git commit -m "ingest(<kind>): <title>"`.
   (`new`/`ingest` auto-log to `journal/<today>.md`; `tools/audock log "..."` adds manual lines.)

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
