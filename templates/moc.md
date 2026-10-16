---
id: __ID__
title: __TITLE__
type: moc
tags: [moc]
created: __DATE__
updated: __DATE__
aliases: []
status: stable
---

# __TITLE__

<!-- A Map of Content: a curated hub for one domain. Hand-pick the important entry points
     below (these are what Claude follows). The Dataview block auto-lists everything tagged
     for this domain, for human browsing. -->

## Key notes
<!-- Curated [[wikilinks]] — the canonical entry points into this domain. -->

## All notes in this domain
```dataview
TABLE updated, status
FROM #__SLUG__
WHERE type = "note"
SORT updated DESC
```
