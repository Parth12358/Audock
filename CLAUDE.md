# Audock — Librarian Protocol

You are the librarian for this vault. When asked to **add**, **capture**, **remember**, or
**look up** something, follow the procedures below exactly. They exist so that ingestion and
retrieval are deterministic and repeatable, and so the store stays **lossless** and
**Obsidian-compatible** (pure Markdown, YAML frontmatter, `[[wikilinks]]`, `#tags`).

The CLI lives at `tools/audock` (run it from the vault root). Prefer it over hand-writing files
— it fills IDs, dates, hashes, and templates correctly.

## When to reach for Audock (do this proactively — don't wait to be asked)

The CLI is **cheap**: its output is tiny, so probing the vault costs almost nothing. Reading
whole `.md` files into context is what costs tokens — so probe first, read last.

- **Before answering a factual/technical question**, run `tools/audock context "<question>"`
  (or `query`). If the vault knows, answer from that compact pack and cite it; this is both
  cheaper and more correct than answering from memory. If it returns nothing, say so and
  proceed normally (optionally offer to INGEST what you learn).
- **When the user shares something worth keeping** (a decision, a finding, a snippet, a link),
  offer to — or just — INGEST it.
- **Cost rule:** resolve answers with `context`/`query`/`show` (small, curated output). Only
  open a full file with Read or `show --raw` when you need exact verbatim bytes. Never slurp
  the whole vault into context.

## Invariants (never violate)

0. **Human-owned content is read-only.** Never edit, supersede, move, rename, or delete any note
   with `locked: true` in its frontmatter (or tagged `#locked`). Treat it as the human's own.
   You may *read, cite, and link to* it. If it seems wrong or outdated, surface that to the human
   and propose a change — do not make it. New knowledge on the same topic → a separate note that
   links to the locked one. The same applies to any region fenced by
   `<!-- audock:human -->` … `<!-- /audock:human -->` inside an otherwise editable note: leave
   everything between those markers exactly as-is.
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
   This writes `sources/<kind>/<timestamp>-<slug>.md` with frontmatter + a `sha256` hash. The
   body below the frontmatter is stored **byte-verbatim** — the lossless ground truth. If an
   identical body was already captured, the CLI says so; reuse that source.
3. **Dedup gate (decide ADD / UPDATE / SUPERSEDE / NOOP).** Before writing a note, run
   `tools/audock similar "<concept title>"`. Then:
   - **NOOP** — the fact is already fully captured → stop (don't duplicate).
   - **UPDATE** — a note covers this concept → go to 4b (append, don't fork).
   - **SUPERSEDE** — an existing note is now *wrong/outdated* → create the corrected note, and on
     the old one set `status: superseded` + `superseded_by: "[[new-note]]"` (never delete it).
   - **ADD** — genuinely new → 4a.
   Skip storing anything trivially re-derivable or already verbatim in a source.
4. **Distill into atomic note(s):**
   - **4a. New concept** → `tools/audock new note "Concept Title"`, fill the distilled body, set
     `tags:`, a one-line **`summary:`** (what it claims + where it came from — this boosts
     retrieval), `sources: ["[[<source-id>]]"]`, add `[[wikilinks]]` to related notes, and
     `status: stable` when confident.
   - **4b. Existing concept** → append a dated line to its `## Log`, add the new `[[source]]`
     to `sources:`, integrate the fact additively, and bump `updated:`.
5. **Backlink the source.** Add each resulting note to the source's `distilled_into:` — the one
   allowed edit to a source (frontmatter only, never the body).
6. **Place in the graph.** Link the note from the relevant `maps/<domain>` MOC (create with
   `tools/audock new moc "<Domain>"` if none fits); ensure the MOC is linked from [[index]].
7. **Reindex & commit:** `tools/audock reindex` then `git add -A && git commit -m
   "ingest(<kind>): <title>"`. (`new`/`ingest` auto-append a line to `journal/<today>.md`; add
   your own with `tools/audock log "<what you did>"`.)

## QUERY — answering from the vault

Lead with the **cheapest** step that answers the question; escalate only if needed:

1. **Answer pack (default, cheapest).** `tools/audock context "<question>" [--tag t] [--k N]`.
   Returns a bounded, deduped, comment-stripped bundle of the top notes with provenance — enough
   to answer most questions from one call. It explicitly reports anything it omitted.
2. **Targeted search.** `tools/audock query "<terms>" [--tag t] [--type note] [--since date]`
   when you want a ranked list of hits + snippets to pick from.
3. **Open one item.** `tools/audock show <id>` for a single note (compact: minimal frontmatter +
   body, comments stripped). Follow `[[wikilinks]]` by `show`-ing the linked ids.
4. **Lossless drill-down.** For exact quotes/numbers/code, `tools/audock show <source-id> --raw`
   (or Read the source file) — the verbatim capture is the ground truth.
5. **Browse** (humans / exploratory): [[index]] → a `maps/<domain>` MOC. Prefer 1–3 for answers;
   this step costs more tokens.
6. If the vault has no answer, say so plainly; don't invent. Offer to INGEST the missing info.

## MAINTAIN — keeping it healthy

Run `tools/audock doctor` for: orphans, broken `[[links]]`, notes citing missing sources,
under-linked notes, duplicate/tag-variant candidates, and stale notes. Bulk fixes are easiest
with `sql` (dry-run first, then `--apply`): retag with
`UPDATE notes SET tags = tags - 'old', tags = tags + 'new' WHERE tag='old'`; merge duplicates
with `MERGE '<drop>' INTO '<keep>'` (supersedes the drop, keeps its title as an alias, rewires
links — never hard-deletes). `sql` never touches `locked`/#human notes. Then:
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
tools/audock similar "title"                                        # dedup gate before distilling
tools/audock context "question" [--tag t] [--k N] [--all]           # cheapest answer path
tools/audock query "text" [--tag t] [--type note|source|moc] [--since D] [--all] [--json]
tools/audock show <id> [--body | --raw]                             # one item; --raw = verbatim
tools/audock sql "SELECT|UPDATE|MERGE ..." [--apply]                # SQL-style bulk query/edit
tools/audock backlinks <id>                                         # who links here
tools/audock log "what you did"                                     # append to today's journal
tools/audock reindex
tools/audock doctor
```
(`--all` includes `superseded` notes, which are hidden by default. Add `--vault <path>` or set
`$AUDOCK_VAULT` when running the installed binary from outside the vault.)

## Optional automation (not on by default)

The on-demand flow above is primary. To automate ingestion later without changing the protocol:
- **Inbox watcher:** drop raw files in `inbox/`; a watcher (or a `/loop`) runs INGEST on each
  new file, then moves it out.
- **Scheduled agent:** a cron'd Claude Code run that INGESTs anything in `inbox/`, then runs
  `doctor` + `reindex`. Same steps, different trigger.
