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
tools/audock init [path] [--dry-run]          # scaffold Audock into a new or existing vault
tools/audock new note|source|moc "Title"      # scaffold a file from a template
tools/audock ingest <file|url|-> --type web   # capture raw material into sources/ (verbatim+hash)
tools/audock similar "Title"                  # top-k similar notes (run before adding — dedup gate)
tools/audock context "question" [--k N --all] # bounded answer pack — the cheapest way to query
tools/audock query "text" [--tag t --type note --since 2026-01-01 --all --json]
tools/audock show <id> [--body | --raw]       # one item; --raw = verbatim (lossless drill-down)
tools/audock sql "SELECT|UPDATE|MERGE …" [--apply]  # SQL-style bulk query/edit (dry-run default)
tools/audock backlinks <id>                   # notes/MOCs that link to this one
tools/audock view "Name" [--tag t --status s] # emit an Obsidian Bases (.base) live-table view
tools/audock log "what you did"               # append to today's journal/<date>.md
tools/audock reindex [--related]              # rebuild tags.md + index (+ auto ## Related blocks)
tools/audock doctor                           # links / missing-source / orphans / dups / tags / stale
```

Pure Python 3, **no dependencies and no external tools** — ranking is a built-in field-weighted
**BM25** (title/summary weighted over body) with light stemming (`embedding`≈`embeddings`).
Superseded notes are hidden from queries unless `--all`. Journal entries are an activity log,
excluded from knowledge queries. Captures are stored as **exact UTF-8 text** (line endings
included; the hash covers the input bytes); non-UTF-8 input is refused rather than altered, and a
failed or refused URL fetch errors out instead of saving anything.

Run the tests with `tests/run.sh` (≈100 regression + ≈1,600 seeded synthetic cases; install
PyYAML to include the Obsidian-YAML validity checks).

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

### Install

**macOS (Apple silicon) and Linux** — installs `~/.local/bin/audock`, no sudo, verifies it runs:

```sh
curl -fsSL https://parth12358.github.io/Audock/install.sh | sh
```

**Windows (PowerShell)** — installs to `%LOCALAPPDATA%\audock` and adds it to your user PATH:

```powershell
irm https://parth12358.github.io/Audock/install.ps1 | iex
```

Pin a version with `AUDOCK_VERSION=v0.2.0`, or pick the folder with `AUDOCK_INSTALL_DIR`.

**By hand:** download your platform's file from [Releases](../../releases), rename it to `audock`
(`audock.exe` on Windows), `chmod +x audock`, and move it into a folder on your PATH. If macOS
blocks it, run `xattr -d com.apple.quarantine audock`. Intel Macs and ARM Linux have no prebuilt
binary yet — clone the repo and run `tools/audock` (Python 3).

Then run it from inside a vault, or point it at one:

```sh
audock init --dry-run                                # preview setup; writes nothing
audock --vault /path/to/Vault query "embeddings"     # or: export AUDOCK_VAULT=/path/to/Vault
```

Outside a vault every command except `init` stops with an error rather than scanning the current
folder. The binary carries its templates, so it works without this repo. Maintainers release with
`git tag vX.Y.Z && git push origin vX.Y.Z` (CI runs the test suites before building).

## Obsidian setup

1. Open this folder as a vault.
2. Install the declared community plugins (in `.obsidian/community-plugins.json`):
   - **Dataview** — renders the auto-lists in `index.md`, `tags.md`, and the MOCs. (Static
     `[[wikilinks]]` and the lists `reindex` writes work without it.)
   - **Omnisearch** — fuzzy full-text search in the Obsidian UI (optional).
   - **Smart Connections** — local-embedding semantic search; the bolt-on for the embeddings
     Audock deliberately defers (optional).
   - **Obsidian Git** (recommended) — auto-commit/push so the vault stays versioned.
3. The graph is auto-colored by domain — `reindex` regenerates one hue per MOC.

## Backup (RAID-like local mirror)

`tools/audock-backup <vault> [backup-root] [keep-days]` commits pending changes, mirrors the
repo to a bare replica, and writes a dated git bundle (pruning old ones). Run it daily via cron:

```sh
30 2 * * *  mkdir -p ~/.audock-backups && /path/to/tools/audock-backup /path/to/Vault >> ~/.audock-backups/backup.log 2>&1
```

Restore any time: `git clone ~/.audock-backups/<vault>.git <dir>` (replica) or
`git clone <snapshot>.bundle <dir>` (point-in-time).

## Everyday use

Ask Claude to "add this to Audock" (ingest) or "what does Audock say about X" (query); it
follows `CLAUDE.md`. Or use the CLI directly. Commit after changes — `git` is the history
substrate.
