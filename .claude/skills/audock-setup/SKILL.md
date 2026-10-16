---
name: audock-setup
description: Set up / bootstrap Audock into a folder or an EXISTING Obsidian vault so Claude can maintain and query it. Use when the user says "set up audock", "add audock to my vault", "turn this Obsidian vault into an Audock vault", "bootstrap audock here", or "initialize a knowledge base". Safe and additive — never rewrites the user's existing notes or .obsidian config.
---

# Audock setup

Bootstrap Audock into a target folder (a new dir, or someone's existing Obsidian vault). It is
**additive and safe**: existing files and `.obsidian/` config are preserved; only missing pieces
are created and graph color-groups and the Dataview, Omnisearch and Smart Connections plugin entries are merged in.

## Steps

1. **Pick the target.** Default is the current directory. If the user has an Obsidian vault, use
   its root (the folder containing `.obsidian/`). Confirm the path if unsure.
2. **Dry-run first** (always, for an existing vault): `audock init <path> --dry-run`. Show the
   user the `~` lines (what would be created) and the `= … (kept)` lines (what is preserved).
   Nothing is written.
3. **Apply:** `audock init <path>`. This creates `sources/ notes/ maps/ journal/ templates/`,
   `CLAUDE.md`, `index.md`, `tags.md`, the `audock` skill, and merges `.obsidian/graph.json`
   color groups + adds `dataview`, `omnisearch` and `smart-connections` to community plugins —
   without touching existing files (an unreadable config file is left alone).
   (If only the installed `audock` binary is available, `tools/audock` is skipped; that's fine.)
4. **Version it:** if the folder isn't a git repo yet, `git init && git add -A &&
   git commit -m "add Audock"`. Git is Audock's history/losslessness substrate.
5. **Index + check:** `audock reindex && audock doctor`.
6. **Tell the user** to enable the **Dataview** community plugin in Obsidian so the tables render.

## Existing notes (do not auto-migrate)

Leave the user's existing `.md` files exactly as they are — they already work in Obsidian. Only
fold one into Audock when asked, and only **additively**: add missing frontmatter
(`type: note`, an `id`, `status:`, a one-line `summary:`) without changing the body or the user's
link style (respect wikilinks vs markdown-links). Never bulk-rewrite links.

## Mark human-owned content

Offer to protect notes the user authored: set `locked: true` in frontmatter (or tag `#locked`),
or wrap a region with `<!-- audock:human -->` … `<!-- /audock:human -->`. Per the librarian
protocol, Claude then treats those as read-only — read/cite/link only, never edit. `audock
doctor` reports how many notes are locked.

After setup, hand off to the `audock` skill for day-to-day ingest/query/maintain.
