# Audock — Librarian Protocol

You are the librarian for this vault. When asked to **add**, **capture**, **remember**, or
**look up** something, follow the procedures below exactly. They exist so that ingestion and
retrieval are deterministic and repeatable, and so the store stays **lossless** and
**Obsidian-compatible** (pure Markdown, YAML frontmatter, `[[wikilinks]]`, `#tags`).

The CLI lives at `tools/audock` (run it from the vault root). Prefer it over hand-writing files
— it fills IDs, dates, hashes, and templates correctly.

## Invariants (never violate)

1. **`sources/` is append-only and immutable.** Once a capture file is written, never edit its
   body. New facts about the same source → a new note or a `## Log` entry, never a rewrite.
2. **Notes are additive.** To change an existing note, append a dated line to its `## Log` and
   bump `updated:` in frontmatter. Never delete past content; strike through or supersede with
   a new dated line instead.
3. **Every note cites provenance.** A note's `sources:` field lists the `[[source]]` files it
   was distilled from. Every distilled source's `distilled_into:` lists the notes it fed.
4. **One concept per note.** If material covers N concepts, make N notes.
5. **Commit every mutation** to git with a structured message (see below). Git is the history
   substrate; a commit is what makes an operation durable and revertible.

## INGEST — adding material

Input is one of: a Claude conversation/output, a code file/snippet, a web URL/page, or a manual
note. Steps:

1. **Classify origin** → `conversation` | `code` | `web` | `manual`.
2. **Capture verbatim** into `sources/<kind>/`:
   `tools/audock ingest <file|url|-> --type <kind> [--title "..."] [--ref <url-or-id>]`
   This writes `sources/<kind>/<timestamp>-<slug>.md` with frontmatter + a `sha256` hash of the
   body, and prints the new source id. The body is fenced verbatim — do not paraphrase it here.
3. **Dedup.** Before distilling, search for an existing capture/note:
   `tools/audock query "<distinctive phrase or title>"`. If an identical source hash already
   exists, reuse it instead of re-capturing. If a note on the concept already exists, go to 4b.
4. **Distill into atomic note(s):**
   - **4a. New concept** → `tools/audock new note "Concept Title"`, then fill the body with the
     distilled explanation, set `tags:`, set `sources: ["[[<source-id>]]"]`, add `[[wikilinks]]`
     to related notes, set `status: stable` when confident.
   - **4b. Existing concept** → open the note, append a dated line to its `## Log`
     (e.g. `- 2026-10-15 — added detail about X from [[<source-id>]]`), add the new `[[source]]`
     to `sources:`, integrate the new fact into the body additively, and bump `updated:`.
5. **Backlink the source.** Add each resulting note to the source file's `distilled_into:` list.
   (This is the one allowed edit to a source: its frontmatter `distilled_into:` only — never the
   body.)
6. **Place in the graph.** Add/confirm a `[[link]]` to the note from the relevant `maps/<domain>`
   MOC (create it with `tools/audock new moc "<Domain>"` if none fits) and ensure the MOC is
   linked from [[index]].
7. **Reindex & commit:** `tools/audock reindex` then
   `git add -A && git commit -m "ingest(<kind>): <title>"`.

## QUERY — answering from the vault

1. **Enter at the top.** Read [[index]], then the most relevant `maps/<domain>` MOC.
2. **Search.** `tools/audock query "<terms>" [--tag <t>] [--type note] [--since <date>]`.
   This ranks matches over frontmatter + body and prints paths + snippets.
3. **Traverse.** Follow `[[wikilinks]]` from the best hits to gather connected context.
4. **Answer with citations** to note ids. When exact fidelity matters (quotes, numbers, code),
   **drill to the `sources:`** file and read the verbatim capture — this is the lossless path.
5. If the vault has no answer, say so plainly; don't invent. Offer to INGEST the missing info.

## MAINTAIN — keeping it healthy

Run `tools/audock doctor` to get a report of: orphan notes (no backlinks), broken `[[links]]`,
duplicate-candidate notes (similar titles/aliases), and stale notes (`updated:` far in the
past). Then:
- Wire orphans into a MOC or link them from a related note.
- Fix or remove broken links.
- Merge duplicates by keeping one canonical note and adding a `## Log` line + alias on it, and
  leaving a one-line pointer (`See [[canonical]]`) on the other (never hard-delete history).
- `tools/audock reindex` and commit: `git commit -m "maintain: <summary>"`.

## Conventions

- **IDs:** notes `YYYYMMDD-<slug>`; sources `YYYYMMDDThhmmss-<slug>` (UTC). Set by the CLI.
- **Slugs:** lowercase, hyphenated, ASCII.
- **Tags:** hierarchical, e.g. `domain/ml`, `topic/embeddings`, `project/audock`. MOCs carry
  `moc`.
- **Links:** always `[[wikilink]]` by note id or title (shortest form), never Markdown links,
  so Obsidian's graph and backlinks resolve.
- **Commit messages:** `ingest(<kind>): …`, `maintain: …`, `query:` (none — queries don't
  mutate), `reindex: …`.

## Commands quick reference

```
tools/audock new note|source|moc "Title"
tools/audock ingest <file|url|-> --type conversation|code|web|manual [--title ..] [--ref ..]
tools/audock query "text" [--tag t] [--type note|source|moc] [--since YYYY-MM-DD] [--json]
tools/audock reindex
tools/audock doctor
```

## Optional automation (not on by default)

The on-demand flow above is primary. To automate ingestion later without changing the protocol:
- **Inbox watcher:** drop raw files in `inbox/`; a watcher (or a `/loop`) runs INGEST on each
  new file, then moves it out.
- **Scheduled agent:** a cron'd Claude Code run that INGESTs anything in `inbox/`, then runs
  `doctor` + `reindex`. Same steps, different trigger.
