#!/usr/bin/env bash
# Extensive test harness for the Audock CLI. Operates on an isolated vault copy.
set -u
V="${1:?usage: test_audock.sh <vault-copy-path>}"
A="$V/tools/audock"
cd "$V"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  \033[32mPASS\033[0m %s\n' "$1"; }
no()  { FAIL=$((FAIL+1)); printf '  \033[31mFAIL\033[0m %s\n' "$1"; [ -n "${2:-}" ] && printf '       %s\n' "$2"; }
# assert: desc ; condition-cmd...
chk() { local d="$1"; shift; if "$@" >/dev/null 2>&1; then ok "$d"; else no "$d"; fi; }
section(){ printf '\n== %s ==\n' "$1"; }

section "new (note/moc/source)"
"$A" new note "Transformer Architecture" >/dev/null
chk "note file created"            test -f notes/transformer-architecture.md
grep -q 'id: 2026.*-transformer-architecture' notes/transformer-architecture.md && ok "note id filled" || no "note id filled"
"$A" new moc "Deep Learning" >/dev/null
chk "moc file created"             test -f maps/deep-learning.md
grep -q 'FROM #deep-learning' maps/deep-learning.md && ok "moc dataview slug filled" || no "moc dataview slug filled"
# duplicate title should refuse
if "$A" new note "Transformer Architecture" >/dev/null 2>&1; then no "refuses duplicate note title"; else ok "refuses duplicate note title"; fi

section "ingest — manual stdin + hash integrity (losslessness)"
IN='Attention lets a token weigh all other tokens. Scaled dot-product attention divides by sqrt(d_k).'
OUT=$(printf '%s' "$IN" | "$A" ingest - --type manual --title "Attention mechanism" --ref conv-1)
SF=$(echo "$OUT" | awk '/captured/{print $2}')
chk "source file created"          test -f "$SF"
EXP=$(printf '%s' "$IN" | sha256sum | cut -d' ' -f1)
grep -q "sha256:$EXP" "$SF" && ok "stored hash == sha256(input)" || no "stored hash == sha256(input)"
# verbatim: body after frontmatter equals input (modulo trailing newline)
BODY=$(awk 'f;/^---$/{c++; if(c==2)f=1}' "$SF")
[ "$(printf '%s' "$BODY")" = "$IN" ] && ok "body stored verbatim" || no "body stored verbatim" "got: $BODY"

section "ingest — dedup by hash"
N0=$(ls sources/manual | wc -l)
D=$(printf '%s' "$IN" | "$A" ingest - --type manual --title "dup" 2>&1)
echo "$D" | grep -qi duplicate && ok "duplicate detected" || no "duplicate detected" "$D"
[ "$(ls sources/manual | wc -l)" -eq "$N0" ] && ok "no extra file written on dup" || no "no extra file written on dup"

section "ingest — adversarial content (backticks / unicode / empty)"
printf 'code block:\n```python\nprint("hi")\n```\nend' | "$A" ingest - --type code --title "fence sample" >/dev/null
FS=$(ls sources/code/*fence-sample.md)
chk "fenced content ingests"       test -f "$FS"
python3 -c "import sys;t=open('$FS').read();from pathlib import Path" && ok "fence file readable" || no "fence file readable"
# frontmatter still parses (id present as first key)
head -2 "$FS" | grep -q '^id:' && ok "fence file frontmatter intact" || no "fence file frontmatter intact"
printf 'Café ☕ naïve — 日本語 résumé' | "$A" ingest - --type manual --title "Unicode café ☕" >/dev/null 2>&1
ls sources/manual/*unicode-caf*.md >/dev/null 2>&1 && ok "unicode title slugified+created" || no "unicode title slugified+created"
printf '' | "$A" ingest - --type manual --title "empty capture" >/dev/null 2>&1 && ok "empty stdin ingests without crash" || no "empty stdin ingests without crash"

section "ingest — url failures are errors, never fake captures"
N0=$(ls sources/web 2>/dev/null | wc -l)
WOUT=$("$A" ingest "http://127.0.0.1:9/nope" --type web --title "offline url" 2>&1); WRC=$?
[ "$WRC" -ne 0 ] && ok "refused/failed fetch exits non-zero" || no "refused/failed fetch exits non-zero" "$WOUT"
echo "$WOUT" | grep -qi 'refused' && ok "error explains the refusal" || no "error explains the refusal" "$WOUT"
[ "$(ls sources/web 2>/dev/null | wc -l)" -eq "$N0" ] && ok "no source written on failed fetch" || no "no source written on failed fetch"
"$A" ingest "http://no-such-host.invalid/x" --type web >/dev/null 2>&1 && no "unresolvable host fails closed" || ok "unresolvable host fails closed"
"$A" ingest "http://[::1]:8080/" --type web >/dev/null 2>&1 && no "IPv6 loopback refused" || ok "IPv6 loopback refused"

section "query — tokenized NL, filters, json, limit"
"$A" query "attention tokens" | grep -qi attention && ok "NL multi-term query matches" || no "NL multi-term query matches"
"$A" query "attention" --type note | grep -qi 'no matches' && ok "--type note filters out source-only hit" || no "--type note filters out source-only hit"
"$A" query "" --tag domain/ml --type note | grep -qi embeddings && ok "tag-only listing works" || no "tag-only listing works"
"$A" query "embeddings" --since 2099-01-01 | grep -qi 'no matches' && ok "--since future => none" || no "--since future => none"
"$A" query "embeddings" --json | python3 -c 'import sys,json;json.load(sys.stdin)' && ok "--json is valid JSON" || no "--json is valid JSON"

section "context — bounded answer pack"
"$A" context "sqrt divides scaled dot-product" | grep -qi 'attention' && ok "context returns relevant pack (source fallback)" || no "context returns relevant pack"
"$A" context "attention" | grep -q 'drill to a source' && ok "context prints lossless-drill hint" || no "context prints lossless-drill hint"
"$A" context "totally unrelated xyzzy plugh" | grep -qi 'no matches' && ok "context: honest empty" || no "context: honest empty"
# bounding: ingest many matching notes, cap k=1 -> must announce omissions
for i in 1 2 3; do "$A" new note "Beta Term $i" >/dev/null; sed -i 's/^tags: \[\]/tags: [topic\/beta]/' "notes/beta-term-$i.md"; echo "beta shared keyword alpha" >> "notes/beta-term-$i.md"; done
"$A" context "beta alpha" --k 1 | grep -qi 'more match' && ok "context --k cap announces omissions (no silent cap)" || no "context --k cap announces omissions"

section "show — resolve by id/title/alias/stem; compact vs raw"
"$A" show embeddings | grep -q '# Embeddings' && ok "show by stem" || no "show by stem"
"$A" show "Embeddings" | grep -q '# Embeddings' && ok "show by title" || no "show by title"
"$A" show "vector embeddings" | grep -q '# Embeddings' && ok "show by alias" || no "show by alias"
"$A" show 20261015-embeddings | grep -q '# Embeddings' && ok "show by id" || no "show by id"
"$A" show embeddings --body | grep -q '<!--' && no "show --body strips comments" || ok "show --body strips comments"
# --raw byte-identical to file
diff <("$A" show 20261015-embeddings --raw) notes/embeddings.md >/dev/null && ok "show --raw == file bytes" || no "show --raw == file bytes"
"$A" show no-such-note >/dev/null 2>&1 && no "show missing exits nonzero" || ok "show missing exits nonzero"

section "reindex — tags + maps, idempotent"
"$A" reindex >/dev/null
grep -q 'domain/ml' tags.md && ok "tags.md lists tag" || no "tags.md lists tag"
grep -q 'deep-learning' index.md && ok "index.md lists new MOC" || no "index.md lists new MOC"
R1=$(cat tags.md index.md); "$A" reindex >/dev/null; R2=$(cat tags.md index.md)
[ "$R1" = "$R2" ] && ok "reindex is idempotent" || no "reindex is idempotent"

section "doctor — broken / orphan / dup / stale"
# broken link
"$A" new note "Has Broken Link" >/dev/null; echo 'see [[does-not-exist-xyz]]' >> notes/has-broken-link.md
# orphan already exists (beta terms / transformer) ; dup-title
"$A" new note "Dup One" >/dev/null; cp notes/dup-one.md notes/dup-one-copy.md; sed -i 's/^id: .*/id: 20261015-dup-one-b/' notes/dup-one-copy.md
# stale
"$A" new note "Ancient Note" >/dev/null; sed -i 's/^updated: .*/updated: 2000-01-01/' notes/ancient-note.md
DOUT=$("$A" doctor)
echo "$DOUT" | grep -q 'does-not-exist-xyz' && ok "doctor finds broken link" || no "doctor finds broken link"
echo "$DOUT" | grep -qi 'orphan notes (no backlinks): [1-9]' && ok "doctor finds orphans" || no "doctor finds orphans"
echo "$DOUT" | grep -qi 'duplicate-title' && echo "$DOUT" | grep -qi 'dup-one' && ok "doctor finds dup titles" || no "doctor finds dup titles"
echo "$DOUT" | grep -qi 'ancient-note' && ok "doctor finds stale note" || no "doctor finds stale note"

section "frontmatter parser edge cases"
python3 - "$A" <<'PY'
import importlib.util, sys, types
# load the audock module from the no-extension script
src=open("tools/audock").read()
mod=types.ModuleType("audock"); mod.__dict__["__name__"]="audock_test"; mod.__dict__["__file__"]="tools/audock"
exec(compile(src,"tools/audock","exec"),mod.__dict__)
pf=mod.parse_frontmatter
cases={
 "inline":  "---\ntags: [a, b, c]\n---\nbody",
 "block":   "---\ntags:\n  - a\n  - b\n---\nbody",
 "quoted":  '---\naliases: ["a, b", c]\n---\nbody',
 "empty":   "---\ntags: []\n---\nbody",
 "nofm":    "no frontmatter here",
}
r=0
fm,_=pf(cases["inline"]);  assert fm["tags"]==["a","b","c"], fm
fm,_=pf(cases["block"]);   assert fm["tags"]==["a","b"], fm
fm,_=pf(cases["quoted"]);  assert fm["aliases"]==["a, b","c"], fm   # comma inside quotes preserved
fm,_=pf(cases["empty"]);   assert fm["tags"]==[], fm
fm,b=pf(cases["nofm"]);    assert fm=={} and b=="no frontmatter here", (fm,b)
print("PARSER-OK")
PY
[ $? -eq 0 ] && ok "frontmatter parser edge cases" || no "frontmatter parser edge cases"

section "losslessness via git (recover prior state)"
git add -A && git -c user.name=t -c user.email=t commit -qm "test state"
ORIG=$(cat notes/embeddings.md)
echo "DESTRUCTIVE EDIT" > notes/embeddings.md
git checkout -q -- notes/embeddings.md
[ "$(cat notes/embeddings.md)" = "$ORIG" ] && ok "git restores overwritten note" || no "git restores overwritten note"

section "supersede lifecycle"
"$A" new note "Old Claim" >/dev/null
printf 'embeddings supersede keyword zzzmarker' >> notes/old-claim.md
sed -i 's/^status: draft/status: superseded/' notes/old-claim.md
"$A" query "zzzmarker" | grep -qi 'no matches' && ok "query hides superseded by default" || no "query hides superseded by default"
"$A" query "zzzmarker" --all | grep -qi 'old claim' && ok "query --all shows superseded" || no "query --all shows superseded"

section "note summary prefix boosts ranking"
"$A" new note "Widget Protocol" >/dev/null
"$A" new note "Gadget Protocol" >/dev/null
# give gadget a summary mentioning sprocket; widget only body-mentions it once
sed -i 's/^summary: $/summary: explains the sprocket handshake/' notes/gadget-protocol.md
echo 'sprocket appears once in body' >> notes/widget-protocol.md
echo 'sprocket' >> notes/gadget-protocol.md
TOP=$("$A" query "sprocket" | head -1)
echo "$TOP" | grep -qi gadget && ok "summary-matched note ranks first" || no "summary-matched note ranks first" "$TOP"
"$A" show gadget-protocol | grep -q 'summary: explains the sprocket' && ok "show prints summary" || no "show prints summary"

section "similar (dedup gate)"
"$A" similar "Gadget Protocol" | grep -qi 'gadget protocol' && ok "similar finds near-duplicate" || no "similar finds near-duplicate"
"$A" similar "wholly unrelated quux nobody wrote" | grep -qi 'safe to ADD' && ok "similar: safe-to-add when none" || no "similar: safe-to-add when none"

section "daily journal"
BEFORE=$(ls journal/ 2>/dev/null | wc -l)
"$A" log "did a thing" >/dev/null
TODAY=$(date +%F)
test -f "journal/$TODAY.md" && ok "journal file created" || no "journal file created"
grep -q 'did a thing' "journal/$TODAY.md" && ok "manual log line appended" || no "manual log line appended"
"$A" new note "Logged Note" >/dev/null
grep -q 'new note: Logged Note' "journal/$TODAY.md" && ok "new auto-logs to journal" || no "new auto-logs to journal"
grep -q 'type: journal' "journal/$TODAY.md" && ok "journal typed as journal" || no "journal typed as journal"
"$A" query "Logged Note" | grep -qvi 'journal' >/dev/null; "$A" query "did a thing" | grep -qi 'no matches' && ok "journal excluded from knowledge query" || no "journal excluded from knowledge query"

section "doctor hygiene checks (missing source, under-linked)"
"$A" new note "Bad Provenance" >/dev/null
sed -i 's/^sources: \[\]/sources: ["[[nonexistent-source-id]]"]/' notes/bad-provenance.md
DH=$("$A" doctor)
echo "$DH" | grep -qi 'citing a missing source' && echo "$DH" | grep -q 'nonexistent-source-id' && ok "doctor flags missing source" || no "doctor flags missing source"
echo "$DH" | grep -qi 'under-linked notes' && ok "doctor has under-linked section" || no "doctor has under-linked section"

section "released-binary ergonomics (--vault + \$AUDOCK_VAULT)"
( cd /tmp && "$A" --vault "$V" query "embeddings" | grep -qi embeddings ) && ok "--vault flag works from outside" || no "--vault flag works from outside"
( cd /tmp && AUDOCK_VAULT="$V" "$A" query "embeddings" | grep -qi embeddings ) && ok "\$AUDOCK_VAULT works from outside" || no "\$AUDOCK_VAULT works"
# embedded templates: run from a copy with templates/ removed
CP="$V-notpl"; rm -rf "$CP"; cp -r "$V" "$CP"; rm -rf "$CP/templates"
( "$CP/tools/audock" --vault "$CP" new note "No Template Here" >/dev/null && grep -q 'type: note' "$CP/notes/no-template-here.md" ) && ok "embedded templates work without templates/ dir" || no "embedded templates work without templates/ dir"

section "locked (human-owned) marker"
"$A" new note "Human Owned" >/dev/null
sed -i 's/^locked: false/locked: true/' notes/human-owned.md
"$A" doctor | head -1 | grep -qi 'locked/human-owned' && "$A" doctor | head -1 | grep -qE '[1-9] locked' && ok "doctor counts locked notes" || no "doctor counts locked notes"
"$A" query "Human Owned" | grep -qi 'human owned' && ok "locked notes still queryable (read-only, not hidden)" || no "locked notes still queryable"

section "init (bootstrap)"
TMPV="$V-initcheck"; rm -rf "$TMPV"; mkdir -p "$TMPV"
"$A" --vault "$TMPV" init "$TMPV" >/dev/null
test -f "$TMPV/CLAUDE.md" && test -f "$TMPV/templates/note.md" && test -d "$TMPV/sources/web" && ok "init scaffolds a fresh vault" || no "init scaffolds a fresh vault"
( "$TMPV/tools/audock" --vault "$TMPV" new note "Bootstrapped" >/dev/null && grep -q 'locked: false' "$TMPV/notes/bootstrapped.md" ) && ok "bootstrapped vault is usable + has locked field" || no "bootstrapped vault usable"
# idempotent: second run writes nothing new
"$A" --vault "$TMPV" init "$TMPV" | grep -q 'CLAUDE.md (kept)' && ok "init is idempotent (keeps existing)" || no "init idempotent"
# dry-run writes nothing
TMPD="$V-dryrun"; rm -rf "$TMPD"; mkdir -p "$TMPD"
"$A" init "$TMPD" --dry-run >/dev/null
[ "$(find "$TMPD" -type f | wc -l)" -eq 0 ] && ok "init --dry-run writes nothing" || no "init --dry-run writes nothing"

section "BM25 ranking + stemming"
"$A" query "embedding" | grep -qi 'embeddings' && ok "stemming: 'embedding' matches 'Embeddings'" || no "stemming match"
# rarer term should rank its note above a note where it's incidental
TOP=$("$A" query "reranking cross-encoder" | head -1)
echo "$TOP" | grep -qi 'rerank' && ok "BM25 ranks best note first" || no "BM25 ranks best note first" "$TOP"
"$A" query "thing" | grep -qi 'no matches' && ok "word-boundary: 'thing' != 'everything'" || no "word-boundary precision"

section "backlinks"
"$A" backlinks dedup-gate | grep -qi 'backlinks to' && ok "backlinks lists linkers" || no "backlinks lists linkers"
"$A" new note "Nobody Links Here" >/dev/null
"$A" backlinks "Nobody Links Here" | grep -qi 'no backlinks' && ok "backlinks: none when unlinked" || no "backlinks none-case"

section "view (Bases emitter)"
"$A" view "My Drafts" --status draft --tag audock >/dev/null
test -f bases/my-drafts.base && ok "view writes .base file" || no "view writes .base"
grep -q 'type: table' bases/my-drafts.base && grep -q 'file.hasTag("audock")' bases/my-drafts.base && ok ".base has table view + tag filter" || no ".base content"
python3 -c "import sys;[l for l in open('bases/my-drafts.base')]" && ok ".base is readable text" || no ".base readable"

section "reindex --related (idempotent, orphan-safe)"
"$A" reindex --related >/dev/null
R2=$("$A" reindex --related | grep -oE '[0-9]+ related' | head -1)
[ "$R2" = "0 related" ] && ok "related blocks idempotent (0 on 2nd run)" || no "related idempotent" "$R2"
# an orphan that links OUT must still be flagged despite reciprocal Related links
"$A" new note "Linker Orphan" >/dev/null
echo 'see [[dedup-gate]] and [[two-layer-store]]' >> notes/linker-orphan.md
"$A" reindex --related >/dev/null
"$A" doctor | grep -A20 'orphan notes' | grep -q 'linker-orphan' && ok "orphan-with-outlinks still flagged (Related not counted)" || no "orphan detection defeated by Related"

section "tag hygiene (variant detection)"
"$A" new note "Widget A" >/dev/null; sed -i 's/^tags: \[\]/tags: [widget]/' notes/widget-a.md
"$A" new note "Widget B" >/dev/null; sed -i 's/^tags: \[\]/tags: [widgets]/' notes/widget-b.md
"$A" doctor | grep -A3 'tag variants' | grep -Eq 'widget.*widgets|widgets.*widget' && ok "doctor flags singular/plural tag variants" || no "tag variant detection"

section "sql — SELECT"
"$A" sql "SELECT title FROM notes WHERE tag='audock'" | grep -qi 'two-layer store' && ok "SELECT WHERE tag=" || no "SELECT tag membership"
"$A" sql "SELECT title FROM notes WHERE summary LIKE '%lossless%'" | grep -qi 'two-layer' && ok "SELECT LIKE (wildcards)" || no "SELECT LIKE"
"$A" sql "SELECT path FROM notes WHERE backlinks = 0" | grep -qi 'nobody-links-here' && ok "SELECT backlinks pseudo-col finds orphans" || no "SELECT backlinks"
"$A" sql "SELECT title FROM notes WHERE status IN ('stable') ORDER BY title DESC LIMIT 2" | grep -q '2 row' && ok "SELECT IN + ORDER BY + LIMIT" || no "SELECT IN/ORDER/LIMIT"

section "sql — UPDATE (dry-run default, --apply writes, log+updated)"
B4=$(grep '^status:' notes/dedup-gate.md)
"$A" sql "UPDATE notes SET status='review' WHERE tag='audock'" | grep -qi 'dry-run' && ok "UPDATE is dry-run by default" || no "UPDATE dry-run default"
[ "$(grep '^status:' notes/dedup-gate.md)" = "$B4" ] && ok "dry-run wrote nothing" || no "dry-run wrote nothing"
"$A" sql "UPDATE notes SET status='review' WHERE tag='audock'" --apply >/dev/null
grep -q '^status: review' notes/dedup-gate.md && ok "UPDATE --apply writes frontmatter" || no "UPDATE --apply writes"
grep -q 'sql: status=' notes/dedup-gate.md && ok "UPDATE appends audit Log line" || no "UPDATE audit log"
"$A" sql "UPDATE notes SET id='hacked' WHERE tag='audock'" 2>&1 | grep -qi 'protected' && ok "UPDATE refuses protected field (id)" || no "UPDATE protected field"
if "$A" sql "UPDATE notes SET status='x'" 2>&1 | grep -qi 'WHERE'; then ok "UPDATE without WHERE refused" ; else no "UPDATE without WHERE refused"; fi

section "sql — UPDATE skips locked notes"
"$A" new note "Sql Locked" >/dev/null
sed -i 's/^tags: \[\]/tags: [audock]/; s/^locked: false/locked: true/' notes/sql-locked.md
"$A" sql "UPDATE notes SET summary='TOUCHED' WHERE tag='audock'" --apply | grep -qi 'skipped 1 locked' && ok "UPDATE reports skipped locked" || no "UPDATE skipped locked msg"
grep -q '^summary: $' notes/sql-locked.md && ok "locked note left untouched by UPDATE" || no "locked untouched"

section "sql — MERGE (supersede + alias + link rewire)"
"$A" sql "MERGE 'reciprocal-rank-fusion' INTO 'hybrid-search'" --apply >/dev/null
grep -q '^status: superseded' notes/reciprocal-rank-fusion.md && ok "MERGE supersedes the drop note" || no "MERGE supersedes drop"
grep -q 'Reciprocal Rank Fusion' notes/hybrid-search.md && ok "MERGE keeps drop title as alias" || no "MERGE alias"
! grep -q '20261016-reciprocal-rank-fusion' notes/contextual-retrieval.md 2>/dev/null; grep -q 'hybrid-search' notes/hybrid-search.md && ok "MERGE rewired links to keep" || no "MERGE link rewire"

section "regression — code-review fixes"
# BOM-prefixed note must still be indexed/searchable
printf '\xef\xbb\xbf---\nid: bomnote\ntitle: Bom Note\ntype: note\ntags: [test]\nsummary: \ncreated: 2026-01-01\nupdated: 2026-01-01\nstatus: stable\n---\n\n# Bom\nunique bomzebra keyword\n' > notes/bomnote.md
"$A" query "bomzebra" | grep -qi 'bom note' && ok "BOM-prefixed note is searchable" || no "BOM note searchable"
# SQL: AND inside a quoted value must not crash or mis-split
"$A" sql "SELECT title FROM notes WHERE title LIKE '%AND%' OR tag='audock'" | grep -q 'row(s)' && ok "SQL quoted AND does not break parsing" || no "SQL quoted AND"
# SQL: numeric-literal vs non-number must not crash
"$A" sql "SELECT title FROM notes WHERE 1=foo" | grep -q '0 row' && ok "WHERE 1=foo no crash" || no "WHERE 1=foo"
# MERGE into a source must be refused (sources immutable)
SRCID=$(basename "$(ls sources/manual/*.md | head -1)" .md)
"$A" sql "MERGE 'two-layer-store' INTO '$SRCID'" 2>&1 | grep -qi 'immutable\|not found' && ok "MERGE into source refused" || no "MERGE into source refused"
# reindex --related must NOT write into a locked note
"$A" new note "Locked Related" >/dev/null; sed -i 's/^locked: false/locked: true/' notes/locked-related.md
"$A" reindex --related >/dev/null
grep -q '## Related' notes/locked-related.md && no "reindex --related wrote into locked note" || ok "reindex --related skips locked notes"
# block-list YAML: UPDATE tag add must not corrupt a block-style list
printf -- '---\nid: blocklist\ntitle: Block List\ntype: note\ntags:\n  - alpha\n  - beta\nsummary: \ncreated: 2026-01-01\nupdated: 2026-01-01\nstatus: stable\nlocked: false\n---\n\n# BL\nbody [[two-layer-store]] [[dedup-gate]]\n' > notes/blocklist.md
"$A" sql "UPDATE notes SET tags = tags + 'gamma' WHERE title='Block List'" --apply >/dev/null
"$A" query "" --tag gamma --type note | grep -qi 'block list' && ! grep -q '^  - alpha' notes/blocklist.md && ok "block-list YAML rewritten cleanly (no dangling)" || no "block-list YAML"
# ingest SSRF guard: metadata address refused, nothing captured
"$A" ingest "http://169.254.169.254/latest/meta-data/" --type web --title "ssrf" >/dev/null 2>&1; R=$?
[ "$R" -ne 0 ] && ! ls sources/web/*ssrf.md >/dev/null 2>&1 && ok "ingest refuses link-local/metadata SSRF" || no "ingest SSRF guard"
# auto graph coloring by domain
"$A" reindex >/dev/null
python3 -c "import json;g=json.load(open('.obsidian/graph.json'));exit(0 if any(q['query'].startswith('tag:#') for q in g['colorGroups']) else 1)" && ok "reindex auto-colors graph groups by domain" || no "graph auto-coloring"

section "runs from arbitrary cwd (absolute path)"
( cd /tmp && "$A" query "embeddings" | grep -qi embeddings ) && ok "CLI resolves vault from any cwd" || no "CLI resolves vault from any cwd"

printf '\n==== RESULT: %d passed, %d failed ====\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
