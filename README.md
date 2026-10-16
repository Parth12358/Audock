# Audock

<!-- license badge -->
*Open source under the [MIT License](LICENSE) — © 2026 Parth Kshirsagar. Free to use and modify; keep the copyright notice.*


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
tools/audock new note|source|moc "Title"      # scaffold a file from a template
tools/audock ingest <file|url|-> --type web   # capture raw material into sources/ (verbatim+hash)
tools/audock similar "Title"                  # top-k similar notes (run before adding — dedup gate)
tools/audock context "question" [--k N --all] # bounded answer pack — the cheapest way to query
tools/audock query "text" [--tag t --type note --since 2026-01-01 --all --json]
tools/audock show <id> [--body | --raw]       # one item; --raw = verbatim (lossless drill-down)
tools/audock backlinks <id>                   # notes/MOCs that link to this one
tools/audock view "Name" [--tag t --status s] # emit an Obsidian Bases (.base) live-table view
tools/audock log "what you did"               # append to today's journal/<date>.md
tools/audock reindex [--related]              # rebuild tags.md + index (+ auto ## Related blocks)
tools/audock doctor                           # links / missing-source / orphans / dups / tags / stale
```

Pure Python 3, **no dependencies and no external tools** — ranking is a built-in field-weighted
**BM25** (title/summary weighted over body) with light stemming (`embedding`≈`embeddings`).
Superseded notes are hidden from queries unless `--all`. Journal entries are an activity log,
excluded from knowledge queries.

### Set up in a new folder or an existing Obsidian vault

```sh
audock init /path/to/vault --dry-run   # preview — writes nothing
audock init /path/to/vault             # apply
```

`init` is **additive and safe**: it creates the Audock folders/docs and merges graph color-groups
+ the Dataview entry into `.obsidian/`, but **never overwrites your existing files or config** and
never touches your existing notes. Run it inside an Obsidian vault to Audock-ify it in place. (Or
just ask Claude — the **audock-setup** skill runs this for you, dry-run first.)

### Human-owned notes (Claude won't touch them)

Mark any note you own with `locked: true` in frontmatter (or tag it `#locked`), or fence a region
with `<!-- audock:human -->` … `<!-- /audock:human -->`. The librarian protocol makes Claude treat
these as **read-only** — it may read, cite, and link to them, but never edit, supersede, move, or
delete them. `audock doctor` reports how many notes are locked.

### Install (standalone binary)

No Python needed — grab a prebuilt `audock` for macOS / Linux / Windows from the repo's
[Releases](../../releases) (built by GitHub Actions on each `v*` tag). Then run it from inside a
vault, or point it at one:

```sh
audock --vault /path/to/Audock query "embeddings"   # or: export AUDOCK_VAULT=/path/to/Audock
```

The binary carries the templates internally, so it works even outside the repo. Maintainers cut
a release with `git tag v0.1.0 && git push origin v0.1.0`.

## Obsidian setup

1. Open this folder as a vault.
2. Install the **Dataview** community plugin (already enabled in config) so the auto-lists in
   `index.md`, `tags.md`, and the MOCs render. Static `[[wikilinks]]` work without it.

## Everyday use

Ask Claude to "add this to Audock" (ingest) or "what does Audock say about X" (query); it
follows `CLAUDE.md`. Or use the CLI directly. Commit after changes — `git` is the history
substrate.
