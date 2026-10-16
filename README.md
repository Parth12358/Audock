# Audock

An automatically-maintained, Obsidian-compatible documentation knowledge base. Claude acts as
the librarian: it ingests raw material (conversations, code, web pages, manual notes), distills
it into atomic linked notes, and queries it on demand. Everything is plain Markdown so it opens
natively in [Obsidian](https://obsidian.md).

## Design in one breath

- **Two layers.** `sources/` = verbatim, immutable, append-only captures (the lossless ground
  truth). `notes/` = distilled atomic notes that link back to their sources. Distillation is
  additive — nothing raw is ever altered, so you can always recover full fidelity.
- **Links over folders.** Navigate via `[[wikilinks]]`, the `maps/` hubs (MOCs), and tags —
  not deep folders. Start at [[index]].
- **Lossless three ways.** Immutable sources + append-only note `## Log` sections + git
  history. Any prior state is recoverable.

## Layout

| Path | What |
|------|------|
| `index.md` | Root map — start here. |
| `sources/` | Verbatim captures (`conversations/ web/ code/ manual/`). Never edited. |
| `notes/` | Distilled atomic notes (flat). |
| `maps/` | Maps of Content — one hub per domain. |
| `tags.md` | Generated tag index. |
| `templates/` | Note / source / MOC templates. |
| `tools/audock` | The CLI. |
| `inbox/` | Optional drop zone for future auto-ingestion (not wired by default). |
| `CLAUDE.md` | The librarian protocol Claude follows. |

## CLI

```sh
tools/audock new note|source|moc "Title"     # scaffold a file from a template
tools/audock ingest <file|url|-> --type web   # capture raw material into sources/
tools/audock query "text" [--tag t --type note --since 2026-01-01]
tools/audock reindex                          # rebuild tags.md + index link lists
tools/audock doctor                           # orphans / broken links / dups / stale
```

Pure Python 3, no required dependencies (uses `ripgrep` if installed, else `grep`).

## Obsidian setup

1. Open this folder as a vault.
2. Install the **Dataview** community plugin (already enabled in config) so the auto-lists in
   `index.md`, `tags.md`, and the MOCs render. Static `[[wikilinks]]` work without it.

## Everyday use

Ask Claude to "add this to Audock" (ingest) or "what does Audock say about X" (query); it
follows `CLAUDE.md`. Or use the CLI directly. Commit after changes — `git` is the history
substrate.
