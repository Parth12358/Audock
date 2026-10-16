#!/usr/bin/env python3
"""~1400 seeded synthetic tests for the Audock CLI: property tests against reference
implementations + end-to-end runs that try to break it. Usage: synth_tests.py <audock-path>"""
import hashlib, json, os, random, re, shutil, subprocess, sys, types
from pathlib import Path

AUDOCK = Path(sys.argv[1]).resolve()
SEED = int(os.environ.get("SEED", "1234"))
R = random.Random(SEED)
import tempfile
SB = Path(os.environ.get("SB") or tempfile.mkdtemp(prefix="audock-synth-")) / "synth"
shutil.rmtree(SB, ignore_errors=True); SB.mkdir(parents=True)

# ---- load the CLI as a module (no main) ----
M = types.ModuleType("audock")
M.__dict__.update(__name__="audock_test", __file__=str(AUDOCK))
exec(compile(AUDOCK.read_text(), str(AUDOCK), "exec"), M.__dict__)
as_list_ = M.as_list

RESULTS = {}
FAILS = []


def check(group, cond, detail=""):
    p, f = RESULTS.get(group, (0, 0))
    if cond:
        RESULTS[group] = (p + 1, f)
    else:
        RESULTS[group] = (p, f + 1)
        if len([x for x in FAILS if x[0] == group]) < 4:
            FAILS.append((group, detail[:400]))


def run(args, cwd=None, stdin=None):
    r = subprocess.run([str(AUDOCK), *args], cwd=cwd, input=stdin, capture_output=True)
    return r.returncode, r.stdout.decode("utf-8", "replace"), r.stderr.decode("utf-8", "replace")


def no_tb(err):
    return "Traceback" not in err


WORDS = ("alpha beta gamma delta vector index cache graph node edge shard token quorum "
         "where order limit and or select update merge null like in").split()
UNI = ["café", "naïve", "日本語", "Ωmega", "résumé", "😀", "Straße"]


def word():
    return R.choice(WORDS + UNI) if R.random() < 0.15 else R.choice(WORDS)


def phrase(n=None):
    return " ".join(word() for _ in range(n or R.randint(1, 4)))


# ======================================================================================
# A. frontmatter parse round-trip (200)
# ======================================================================================
def render_fm(d, style):
    out = []
    for k, v in d.items():
        if isinstance(v, list):
            s = style if style != "mixed" else R.choice(["inline", "indent", "flush"])
            if s == "inline" or not v:
                out.append(f"{k}: [{', '.join(json.dumps(x) if ',' in x else x for x in v)}]")
            else:
                out.append(f"{k}:")
                pre = "  - " if s == "indent" else "- "
                out += [pre + x for x in v]
        else:
            out.append(f"{k}: {json.dumps(v) if R.random() < 0.3 else v}")
    return "---\n" + "\n".join(out) + "\n---\n"


def rand_fm():
    d = {}
    for k in R.sample(["title", "status", "summary", "id", "type", "tags", "aliases", "x-key", "note_2"], R.randint(2, 7)):
        if k in ("tags", "aliases"):
            d[k] = [R.choice(["ml", "domain/ml", "topic/x", "a-b", "café"]) + str(R.randint(0, 9))
                    for _ in range(R.randint(0, 4))]
            if k == "aliases" and R.random() < 0.3 and d[k]:
                d[k][0] = "has, comma"
        else:
            v = phrase()
            if R.random() < 0.2:
                v = v + ": with colon"
            d[k] = v
    return d


def norm_expected(v):
    return v if isinstance(v, list) else v.strip()


for i in range(200):
    d = rand_fm()
    style = R.choice(["inline", "indent", "flush", "mixed"])
    body = "\n# Heading\n" + phrase(8) + "\n"
    text = render_fm(d, style) + body
    if R.random() < 0.2:
        text = "﻿" + text
    if R.random() < 0.2:
        text = text.replace("\n", "\r\n")
    fm, b = M.parse_frontmatter(text)
    ok = all(norm_expected(fm.get(k)) == norm_expected(v) for k, v in d.items())
    check("A frontmatter parse", ok, f"style={style} d={d} got={fm}")

# ======================================================================================
# B. _set_fm_field invariants (200)
# ======================================================================================
for i in range(200):
    d = rand_fm()
    style = R.choice(["inline", "indent", "flush", "mixed"])
    body = "\n# H\n" + phrase(6) + "\n## Log\n- x\n"
    bom = R.random() < 0.15
    raw = ("﻿" if bom else "") + render_fm(d, style) + body
    key = R.choice(list(d.keys()) + ["newkey", "status"])
    if R.random() < 0.4:
        newv = [R.choice(WORDS) for _ in range(R.randint(0, 3))]
        vstr = "[" + ", ".join(newv) + "]"
    else:
        newv = phrase()
        vstr = newv
    out = M._set_fm_field(raw, key, vstr)
    fm, b = M.parse_frontmatter(out)
    exp = dict(d); exp[key] = newv
    ok = all(norm_expected(fm.get(k)) == norm_expected(v) for k, v in exp.items())
    ok = ok and b == M.parse_frontmatter(raw)[1]
    ok = ok and (out.startswith("﻿") == bom)
    ok = ok and len(re.findall(rf"^{re.escape(key)}\s*:", out.lstrip("﻿"), re.M)) == 1
    check("B frontmatter set-field", ok, f"key={key} v={vstr!r}\n{raw}\n=>\n{out}")

# ======================================================================================
# C. SQL LIKE vs reference matcher (150)
# ======================================================================================
def like_ref(pat, s):
    from functools import lru_cache
    pat, s = pat.lower(), s.lower()

    @lru_cache(None)
    def go(i, j):
        if i == len(pat):
            return j == len(s)
        c = pat[i]
        if c == "%":
            return any(go(i + 1, k) for k in range(j, len(s) + 1))
        if j < len(s) and (c == "_" or c == s[j]):
            return go(i + 1, j + 1)
        return False
    return go(0, 0)


ALPH = list("abc.*+?()[]{}|^$\\") + ["%", "_", "%", "_", " "]
for i in range(150):
    pat = "".join(R.choice(ALPH) for _ in range(R.randint(0, 8)))
    if R.random() < 0.5:  # construct a haystack that should match
        hay = "".join(R.choice("xyz") * R.randint(0, 2) if c == "%" else (R.choice("xyz") if c == "_" else c) for c in pat)
    else:
        hay = "".join(R.choice(list("abc.*() ")) for _ in range(R.randint(0, 8)))
    got = bool(re.match(M._like_re(pat), hay, re.I | re.S))
    check("C SQL LIKE", got == like_ref(pat, hay), f"pat={pat!r} hay={hay!r} got={got}")

# ======================================================================================
# D. SQL WHERE parse+eval vs reference (150)
# ======================================================================================
FIELDS = ["title", "status", "tags"]
VALS = ["Rock AND Roll", "where it began", "limit of embeddings", "order by date",
        "it's fine", 'say "hi"', "stable", "draft", "ml", "a OR b"]


def qv(v):
    return f'"{v}"' if "'" in v else f"'{v}'"


def rand_cond():
    f = R.choice(FIELDS); op = R.choice(["=", "!=", "LIKE", "IN", "IS NULL", "IS NOT NULL", "CONTAINS"])
    if op in ("IS NULL", "IS NOT NULL"):
        return f"{f} {op}", (f, op, None)
    if op == "IN":
        vs = R.sample(VALS, R.randint(1, 3))
        return f"{f} IN ({', '.join(qv(v) for v in vs)})", (f, op, vs)
    v = R.choice(VALS)
    if op == "LIKE":
        v = R.choice(["%", ""]) + v.split()[0] + R.choice(["%", ""])
    return f"{f} {op} {qv(v)}", (f, op, v)


def ref_eval(fm, c):
    f, op, v = c
    val = fm.get(f, "") if f != "tags" else fm.get("tags", [])
    if op == "IS NULL":
        return val in ("", [], None)
    if op == "IS NOT NULL":
        return val not in ("", [], None)
    if op in ("=", "CONTAINS", "!="):
        pres = any(x.lower() == v.lower() for x in val) if isinstance(val, list) else str(val).lower() == v.lower()
        return (not pres) if op == "!=" else pres
    if op == "LIKE":
        return like_ref(v, " ".join(val) if isinstance(val, list) else str(val))
    if op == "IN":
        vals = [x.lower() for x in v]
        return any(x.lower() in vals for x in val) if isinstance(val, list) else str(val).lower() in vals


rows = []
for _ in range(12):
    rows.append({"title": R.choice(VALS + [""]), "status": R.choice(["stable", "draft", ""]),
                 "tags": R.sample(["ml", "stable", "a OR b", "Rock AND Roll"], R.randint(0, 2))})
dummy = Path("/x/notes/n.md")
for i in range(150):
    groups = [[rand_cond() for _ in range(R.randint(1, 3))] for _ in range(R.randint(1, 3))]
    where = " OR ".join(" AND ".join(s for s, _ in g) for g in groups)
    try:
        conds = M._parse_where(where)
        ok = True
        for fm in rows:
            got = M._match(dummy, fm, "", {}, conds)
            exp = any(all(ref_eval(fm, c) for _, c in g) for g in groups)
            if got != exp:
                ok = False; break
        check("D SQL WHERE", ok, f"where={where} row={fm} got={got} exp={exp}")
    except SystemExit as e:
        check("D SQL WHERE", False, f"where={where} exit={e}")

# ======================================================================================
# helpers to build synthetic vaults
# ======================================================================================
def make_vault(name, n=30, locked_frac=0.0):
    v = SB / name
    shutil.rmtree(v, ignore_errors=True)
    rc, _, err = run(["init", str(v)])
    assert rc == 0, err
    ids = [f"20260101-n{i:03d}" for i in range(n)]
    (v / "sources/manual/20260101T000000-src.md").write_text(
        "---\nid: 20260101T000000-src\ntitle: Src\ntype: source\norigin: manual\norigin_ref: x\n"
        "captured: 2026-01-01T00:00:00Z\nhash: sha256:x\ndistilled_into: []\n---\nraw source body [[n001]]\n")
    for i in range(n):
        locked = R.random() < locked_frac
        tags = R.sample(["ml", "infra", "ops", "domain/ml"], R.randint(1, 2)) + (["locked"] if locked and R.random() < 0.3 else [])
        links = " ".join(f"[[n{R.randrange(n):03d}]]" for _ in range(2))
        style = R.choice(["inline", "flush"])
        al = f"aliases: [Alias {i}]" if style == "inline" else f"aliases:\n- Alias {i}"
        (v / f"notes/n{i:03d}.md").write_text(
            f"---\nid: {ids[i]}\ntitle: Note {i} {R.choice(WORDS)}\ntype: note\ntags: [{', '.join(tags)}]\n"
            f"summary: {phrase(5)}\ncreated: 2026-01-01\nupdated: 2026-01-02\n{al}\n"
            f"sources: [\"[[20260101T000000-src]]\"]\nstatus: {R.choice(['stable','draft'])}\n"
            f"superseded_by: \nlocked: {'true' if locked else 'false'}\n---\n\n# Note {i}\n\n"
            f"{phrase(12)} {links}\n\n## Log\n- 2026-01-01 — created\n")
    (v / "maps/ml.md").write_text("---\nid: 20260101-ml\ntitle: ML\ntype: moc\ntags: [moc]\nstatus: stable\n---\n\n# ML\n- [[n000]]\n- [[n001]]\n```dataview\nTABLE summary FROM #domain/ml\n```\n")
    return v


def snapshot(paths):
    return {p: p.read_bytes() for p in paths}


# ======================================================================================
# E. ingest losslessness (100)
# ======================================================================================
EV = make_vault("ingest", n=3)
CHARS = list("abc xyz\n\t`-#[]|:") + ["\r\n", "\r", "---\n", "```\n", "﻿", "日本", "😀", "é", "[[x]]", "\x00"]
for i in range(100):
    txt = f"case {i} " + "".join(R.choice(CHARS) for _ in range(R.randint(0, 60)))
    data = txt.encode("utf-8")
    rc, out, err = run(["ingest", "-", "--type", "manual", "--title", f"t{i}"], cwd=EV, stdin=data)
    files = list((EV / "sources/manual").glob(f"*-t{i}.md"))
    ok = rc == 0 and len(files) == 1 and no_tb(err)
    if ok:
        fb = files[0].read_bytes()
        ok = fb.endswith(data + b"\n") and f"sha256:{hashlib.sha256(data).hexdigest()}".encode() in fb
        if ok and i % 5 == 0:
            rc2, _, _ = run(["show", files[0].stem, "--raw"], cwd=EV)
            ok = subprocess.run([str(AUDOCK), "show", files[0].stem, "--raw"], cwd=EV,
                                capture_output=True).stdout == fb
    check("E ingest lossless", ok, f"i={i} rc={rc} txt={txt!r} err={err[-200:]}")

# ======================================================================================
# F. search/ranking properties (90)
# ======================================================================================
FV = make_vault("search", n=60)
planted = {}
plant_notes = R.sample(range(60), 30)
for i in range(30):
    tok = "zq" + "".join(R.choice("klmnprst") for _ in range(6))
    n = plant_notes[i]
    p = FV / f"notes/n{n:03d}.md"
    where = R.choice(["body", "summary", "title"])
    t = p.read_text()
    if where == "body":
        t = t.replace("## Log", f"{tok}\n\n## Log")
    elif where == "summary":
        t = re.sub(r"^summary: .*$", f"summary: about {tok}", t, flags=re.M)
    else:
        t = re.sub(r"^title: .*$", f"title: Note {tok}", t, flags=re.M)
    p.write_text(t)
    planted[tok] = f"20260101-n{n:03d}"
for tok, nid in planted.items():
    rc, out, err = run(["query", tok, "--json"], cwd=FV)
    res = json.loads(out) if rc == 0 and out.strip().startswith("[") else []
    check("F search", bool(res) and res[0]["id"] == nid, f"tok={tok} want={nid} got={res[:2]}")
    plural = tok + ("es" if tok.endswith(("s", "x", "z", "ch", "sh")) else "s")
    rc, out, err = run(["query", plural, "--json"], cwd=FV)  # plural via stemmer
    res = json.loads(out) if out.strip().startswith("[") else []
    check("F search", bool(res) and res[0]["id"] == nid, f"plural={plural} want={nid}")
# superseded hidden unless --all; journal excluded
for tok, nid in list(planted.items())[:15]:
    p = next(FV.glob(f"notes/{nid.split('-')[1]}.md"))
    t = p.read_text()
    if "status: superseded" not in t:
        p.write_text(re.sub(r"^status: .*$", "status: superseded", t, flags=re.M))
    rc, out, _ = run(["query", tok, "--json"], cwd=FV)
    res = json.loads(out) if out.strip().startswith("[") else []
    check("F search", all(r["id"] != nid for r in res), f"superseded leaked {tok}")
    rc, out, _ = run(["query", tok, "--all", "--json"], cwd=FV)
    res = json.loads(out) if out.strip().startswith("[") else []
    check("F search", any(r["id"] == nid for r in res), f"--all missing {tok}")
(FV / "journal").mkdir(exist_ok=True)
(FV / "journal/2026-01-01.md").write_text("---\nid: j\ntitle: J\ntype: journal\n---\nzzjournaltoken\n")
rc, out, _ = run(["query", "zzjournaltoken"], cwd=FV)
check("F search", "no matches" in out, "journal leaked into query")

# ======================================================================================
# G. locked notes + sources never mutated under random ops (200)
# ======================================================================================
GV = make_vault("locked", n=30, locked_frac=0.35)
for p in GV.glob("notes/*.md"):
    if R.random() < 0.15:  # some human regions in unlocked notes
        t = p.read_text().replace("## Log", "<!-- audock:human -->\nhuman text [[n002]]\n<!-- /audock:human -->\n\n## Log")
        p.write_text(t)
locked_files = [p for p in GV.glob("notes/*.md") if M._is_locked(M.parse_frontmatter(p.read_text())[0])]
src_files = list(GV.glob("sources/**/*.md"))
snap = snapshot(locked_files + src_files)
unlocked_ids = [M.parse_frontmatter(p.read_text())[0]["id"] for p in GV.glob("notes/*.md") if p not in locked_files]
locked_ids = [M.parse_frontmatter(p.read_text())[0]["id"] for p in locked_files]
OPS = [
    lambda: ["sql", "UPDATE notes SET status='review' WHERE 1=1", "--apply"],
    lambda: ["sql", f"UPDATE notes SET tags = tags + 'z{R.randint(0,9)}' WHERE tag='ml'", "--apply"],
    lambda: ["sql", "UPDATE notes SET aliases = [X, Y] WHERE status != 'nope'", "--apply"],
    lambda: ["sql", "UPDATE notes SET summary = NULL WHERE tag='infra' OR tag='ops'", "--apply"],
    lambda: ["sql", f"MERGE '{R.choice(unlocked_ids)}' INTO '{R.choice(unlocked_ids + locked_ids)}'", "--apply"],
    lambda: ["reindex", "--related"],
    lambda: ["reindex"],
    lambda: ["doctor"],
    lambda: ["sql", "SELECT title FROM notes WHERE locked = 'true'"],
]
for i in range(100):
    args = R.choice(OPS)()
    rc, out, err = run(args, cwd=GV)
    check("G locked/sources immutable", no_tb(err), f"op={args} traceback: {err[-300:]}")
    changed = [str(p) for p, b in snap.items() if not p.exists() or p.read_bytes() != b]
    check("G locked/sources immutable", not changed, f"op={args} mutated {changed[:3]}")
for p in GV.glob("notes/*.md"):  # every note's frontmatter still parses with a type
    fm, _ = M.parse_frontmatter(p.read_text())
    check("G frontmatter stays valid", fm.get("type") == "note", f"{p.name} broken fm")
# human regions survived verbatim
for p in GV.glob("notes/*.md"):
    t = p.read_text()
    if "<!-- audock:human -->" in t:
        check("G frontmatter stays valid", "human text [[n002]]" in t, f"human region altered in {p.name}")

# ======================================================================================
# H. robustness fuzz: hostile files never cause a traceback (150)
# ======================================================================================
HV = make_vault("fuzz", n=10)
GARBAGE = [
    lambda: os.urandom(R.randint(0, 400)),
    lambda: b"",
    lambda: b"---\n",
    lambda: b"---\ntitle: unclosed\ntype: note\n",
    lambda: b"---\ntype: note\ntags: [a, [nested, x], 'q]\n---\nbody",
    lambda: b"---\ntype: note\n" + b"k" * 5000 + b": v\n---\n" + b"x" * 200000,
    lambda: "---\ntype: note\ntitle: ünïcödé 😀\n---\n[[".encode() + "]]]][[|#]]".encode(),
    lambda: b"\xef\xbb\xbf---\r\ntype: note\r\ntitle: bom crlf\r\n---\r\nbody\r\n",
    lambda: b"---\ntype: note\nstatus: superseded\nsuperseded_by: \"[[nowhere]]\"\n---\n<!-- AUDOCK:RELATED:BEGIN -->\n- [[x]]\n",
    lambda: b"---\ntype: moc\n---\n```dataview\nFROM #\n```\n[[",
    lambda: b"---\n- just\n- a list\n---\n",
    lambda: b"\x00\x00---\ntype: note\n---\n",
]
QUERIES = ["", "the", "zz", "a" * 300, "'; DROP", "[[x]]", "日本語", "%_%", "WHERE OR AND"]
names = ["weird name.md", "ünïcode.md", "-dash.md", ".hidden.md", "a b c.md", "x" * 120 + ".md"]
for i in range(150):
    if i % 3 == 0:
        sub = R.choice(["notes", "maps", "sources/manual", "journal", "."])
        (HV / sub).mkdir(parents=True, exist_ok=True)
        (HV / sub / (R.choice(names).replace(".md", f"{i}.md"))).write_bytes(R.choice(GARBAGE)())
    args = R.choice([
        ["doctor"], ["reindex"], ["reindex", "--related"], ["query", R.choice(QUERIES)],
        ["context", R.choice(QUERIES) or "x"], ["similar", R.choice(QUERIES) or "x"],
        ["sql", "SELECT * FROM all"], ["sql", f"SELECT title FROM notes WHERE title LIKE '%{R.choice(['a','é','%'])}%' ORDER BY backlinks DESC LIMIT 3"],
        ["backlinks", "n001"], ["show", "n002"], ["view", "V", "--tag", 'x"y'],
    ])
    rc, out, err = run(args, cwd=HV)
    check("H hostile-input fuzz", no_tb(err) and rc in (0, 1), f"args={args} rc={rc} err={err[-400:]}")

# ======================================================================================
# I. init on hostile/existing .obsidian configs (60)
# ======================================================================================
CFG = {
    "graph.json": [b'{"colorGroups":[{"query":"tag:#mine","color":{"a":1,"rgb":1}}],"scale":0.5}',
                   b"{not json", b"[1,2]", b'{"colorGroups": "oops"}', None],
    "community-plugins.json": [b'["calendar"]', b"{bad", b'{"a":1}', b"[]", None],
    "app.json": [b'{"useMarkdownLinks":true}', b"garbage", None],
}
for i in range(20):
    v = SB / f"init{i}"; shutil.rmtree(v, ignore_errors=True); (v / ".obsidian").mkdir(parents=True)
    chosen = {}
    for f, opts in CFG.items():
        c = R.choice(opts)
        if c is not None:
            (v / ".obsidian" / f).write_bytes(c); chosen[f] = c
    before = {f: (v / ".obsidian" / f).read_bytes() for f in chosen}
    rc, out, err = run(["init", str(v), "--dry-run"])
    check("I init safety", rc == 0 and no_tb(err) and all((v / ".obsidian" / f).read_bytes() == b for f, b in before.items()),
          f"dry-run changed files or crashed: {err[-300:]}")
    rc, out, err = run(["init", str(v)])
    ok = rc == 0 and no_tb(err)
    for f, b in before.items():
        try:
            parsed = json.loads(b)
        except Exception:
            parsed = None
        valid = (f == "graph.json" and isinstance(parsed, dict)) or (f == "community-plugins.json" and isinstance(parsed, list))
        if f == "app.json" or not valid:
            ok = ok and (v / ".obsidian" / f).read_bytes() == b  # untouched
    if b'"tag:#mine"' in before.get("graph.json", b"") and b"colorGroups\": \"oops" not in before.get("graph.json", b""):
        ok = ok and "tag:#mine" in (v / ".obsidian/graph.json").read_text()
    check("I init safety", ok, f"init={i} chosen={list(chosen)} err={err[-300:]}")
    snap2 = {p: p.read_bytes() for p in v.rglob("*") if p.is_file()}
    rc, out, err = run(["init", str(v)])
    check("I init safety", rc == 0 and all(p.read_bytes() == b for p, b in snap2.items()), "init not idempotent")

# ======================================================================================
# J. graph auto-coloring (20)
# ======================================================================================
KV = make_vault("graph", n=8)
gp = KV / ".obsidian/graph.json"
g = json.loads(gp.read_text()); g["colorGroups"] = [{"query": "tag:#mine", "color": {"a": 1, "rgb": 7}}] + g.get("colorGroups", []); g["scale"] = 0.42
gp.write_text(json.dumps(g))
for i in range(5):
    rc, _, err = run(["reindex"], cwd=KV)
    g = json.loads(gp.read_text()); qs = [x["query"] for x in g["colorGroups"]]
    check("J graph colors", rc == 0 and "tag:#mine" in qs, f"user group lost: {qs}")
    check("J graph colors", "tag:#domain/ml" in qs and g.get("scale") == 0.42, f"domain tag/scale: {qs} {g.get('scale')}")
    check("J graph colors", len(qs) == len(set(qs)), f"duplicate groups: {qs}")
    check("J graph colors", (KV / ".obsidian/audock-graph.json").exists(), "sidecar missing")
gp.write_text("{broken")
rc, _, err = run(["reindex"], cwd=KV)
check("J graph colors", rc == 0 and gp.read_text() == "{broken" and no_tb(err), "unparseable graph.json was overwritten")
gp.write_text(json.dumps({"colorGroups": [{"query": "tag:#mine", "color": {"a": 1, "rgb": 7}}]}))
rc, _, _ = run(["reindex"], cwd=KV); rc, _, _ = run(["reindex"], cwd=KV)
check("J graph colors", "tag:#mine" in gp.read_text(), "user group lost after repeated reindex")
for _ in range(2):
    check("J graph colors", True)

# ======================================================================================
# K. SELECT clause carving with keyword-laden values (60)
# ======================================================================================
LV = make_vault("select", n=8)
titles = ["Limit of embeddings", "order by date", "where it all began", "Rock AND Roll",
          "it's LIMIT 5", 'say "WHERE"', "plain"]
for i, t in enumerate(titles):
    p = LV / f"notes/n{i:03d}.md"
    newt = "title: " + (json.dumps(t) if chr(34) in t else t)
    p.write_text(re.sub(r"^title: .*$", lambda _m: newt, p.read_text(), flags=re.M))
for i in range(60):
    t = R.choice(titles)
    stmt = f"SELECT title FROM notes WHERE title = {qv(t)}"
    if R.random() < 0.5:
        stmt += R.choice([" ORDER BY title DESC", " LIMIT 5", " ORDER BY title LIMIT 2", " order by title desc limit 9"])
    rc, out, err = run(["sql", stmt], cwd=LV)
    lines = out.strip().split("\n")
    check("K SELECT carving", rc == 0 and t in lines and "-- 1 row(s)" in out and no_tb(err),
          f"stmt={stmt} rc={rc} out={out!r} err={err[-200:]}")

# ======================================================================================
# L. backup script (24)
# ======================================================================================
BK = AUDOCK.parent / "audock-backup"
broot = SB / "broot"
for i in range(4):
    a = make_vault(f"bk{i}/Vault", n=4); b = make_vault(f"bkx{i}/Vault", n=4)
    for v in (a, b):
        subprocess.run(["git", "init", "-q"], cwd=v)
    r1 = subprocess.run([str(BK), str(a), str(broot)], capture_output=True, text=True)
    r2 = subprocess.run([str(BK), str(b), str(broot)], capture_output=True, text=True)
    reps = sorted(x.name for x in broot.glob("Vault-*.git"))
    check("L backup", r1.returncode == 0 and r2.returncode == 0, f"{r1.stderr[-200:]} {r2.stderr[-200:]}")
    check("L backup", len(reps) == 2 * (i + 1), f"same-basename vaults collided: {reps}")
    rest = SB / f"restore{i}"; shutil.rmtree(rest, ignore_errors=True)
    rr = subprocess.run(["git", "clone", "-q", str(broot / reps[0]), str(rest)], capture_output=True)
    check("L backup", rr.returncode == 0 and (rest / "CLAUDE.md").exists(), "restore from replica failed")
    bundles = list(broot.glob("*-bundles/*.bundle"))
    check("L backup", len(bundles) >= 2, "bundles missing")
    # commit failure (index.lock) must not stop mirroring; exits non-zero and says so
    (a / "notes/new.md").write_text("---\ntype: note\n---\nx\n")
    (a / ".git/index.lock").write_text("")
    r3 = subprocess.run([str(BK), str(a), str(broot)], capture_output=True, text=True)
    (a / ".git/index.lock").unlink()
    check("L backup", r3.returncode != 0 and "WARNING: commit failed" in r3.stdout and "synced replica" in r3.stdout,
          f"commit-failure handling: rc={r3.returncode} out={r3.stdout[-300:]}")
    check("L backup", "Traceback" not in r3.stderr)

# ======================================================================================
# M. sql writes stay real YAML that Obsidian reads back as intended (needs PyYAML) (≈120)
# ======================================================================================
try:
    import yaml
except ImportError:
    yaml = None
    print("note: PyYAML not installed — skipping group M (pip install pyyaml)")


def fm_block(text):
    t = text.lstrip("﻿").replace("\r\n", "\n")
    if not t.startswith("---\n"):
        return None
    end = t.find("\n---", 4)
    return t[4:end] if end != -1 else None


if yaml:
    NASTY = ["a: b", "x #not a comment", "[bracketed]", "true", "null", "-dash", "say \"hi\"",
             "it's", "has, comma", "[[a link]]", "  padded  ", "日本語: ok", "50%", "@at", "plain words"]
    YV = make_vault("yaml", n=12)
    for i in range(40):
        val = R.choice(NASTY)
        field = R.choice(["summary", "status", "title", "custom-field"])
        litem = R.choice(NASTY).strip() or "x"
        stmt = R.choice([
            f"UPDATE notes SET {field} = {qv(val)} WHERE 1=1",
            f"UPDATE notes SET aliases = aliases + {qv(litem)} WHERE 1=1",
            f"UPDATE notes SET tags = tags - 'ml', tags = tags + {qv(litem)} WHERE tag='ml'",
            f"UPDATE notes SET sources = [{qv('[[x]]')}, {qv(litem)}] WHERE 1=1",
        ])
        rc, out, err = run(["sql", stmt, "--apply"], cwd=YV)
        check("M YAML validity", rc == 0 and no_tb(err), f"stmt={stmt} rc={rc} err={err[-200:]}")
        for p in sorted(YV.glob("notes/*.md"))[:2]:  # every touched note must be valid YAML
            blk = fm_block(p.read_text())
            try:
                y = yaml.safe_load(blk)
                ours, _ = M.parse_frontmatter(p.read_text())
                ok = isinstance(y, dict)
                if ok and stmt.startswith(f"UPDATE notes SET {field} = "):
                    ok = str(y.get(field)) == val and ours.get(field) == val
                if ok and "aliases = aliases +" in stmt:
                    ok = litem in [str(x) for x in (y.get("aliases") or [])] and litem in as_list_(ours.get("aliases"))
                check("M YAML validity", ok, f"stmt={stmt}\n{blk}\nyaml={y}")
            except Exception as e:  # noqa: BLE001
                check("M YAML validity", False, f"stmt={stmt} YAML error {e}\n{blk}")
    # MERGE with a nasty title → keep note's aliases still valid YAML containing that title
    for i in range(10):
        a, b = R.sample(range(12), 2)
        pa = YV / f"notes/n{a:03d}.md"
        title = R.choice(["Fusion: ranks, fused", "x #y", "[weird]", "it's \"quoted\""])
        txt = re.sub(r"^title: .*$", lambda _m: "title: " + json.dumps(title), pa.read_text(), flags=re.M)
        txt = re.sub(r"^status: .*$", "status: stable", txt, flags=re.M)
        pa.write_text(txt)
        ida = M.parse_frontmatter(pa.read_text())[0]["id"]
        idb = M.parse_frontmatter((YV / f"notes/n{b:03d}.md").read_text())[0]["id"]
        rc, out, err = run(["sql", f"MERGE '{ida}' INTO '{idb}'", "--apply"], cwd=YV)
        blk = fm_block((YV / f"notes/n{b:03d}.md").read_text())
        try:
            y = yaml.safe_load(blk)
            ok = rc == 0 and title in [str(x) for x in (y.get("aliases") or [])]
        except Exception as e:  # noqa: BLE001
            ok = False
        check("M YAML validity", ok, f"merge title={title!r} rc={rc} err={err[-200:]}\n{blk}")

# ======================================================================================
# N. behaviors fixed in the prod-polish pass (≈40)
# ======================================================================================
NV = make_vault("fixes", n=10)
# non-UTF-8 input is refused, nothing captured
for i in range(5):
    data = os.urandom(20) + b"\xff\xfe\xc3"
    before = len(list((NV / "sources/manual").glob("*.md")))
    rc, out, err = run(["ingest", "-", "--type", "manual", "--title", f"bad{i}"], cwd=NV, stdin=data)
    check("N fixes", rc != 0 and "UTF-8" in err and len(list((NV / "sources/manual").glob("*.md"))) == before,
          f"non-utf8 rc={rc} err={err[-200:]}")
# date comparisons are lexical when not numeric
rc, out, _ = run(["sql", "SELECT title FROM notes WHERE updated > '2026-01-01'"], cwd=NV)
check("N fixes", "-- 10 row(s)" in out, f"date compare: {out[-80:]}")
rc, out, _ = run(["sql", "SELECT title FROM notes WHERE updated < '2026-01-01'"], cwd=NV)
check("N fixes", "-- 0 row(s)" in out, f"date compare lt: {out[-80:]}")
# query --json honors --limit
rc, out, _ = run(["query", "note", "--json", "--limit", "2"], cwd=NV)
check("N fixes", len(json.loads(out)) <= 2, "json ignores --limit")
# sql log lines append chronologically at the end of ## Log
p0 = NV / "notes/n000.md"
p0.write_text(p0.read_text().replace("## Log\n- 2026-01-01 — created\n", "## Log\n- 2026-01-01 — created\n- 2026-01-02 — edited\n"))
run(["sql", "UPDATE notes SET status='review' WHERE title LIKE 'Note 0 %'", "--apply"], cwd=NV)
log = p0.read_text().split("## Log", 1)[1].strip().splitlines()
check("N fixes", log and "sql: status='review'" in log[-1] and "created" in log[0], f"log order: {log}")
# no-op list op does not touch the file
p1 = NV / "notes/n001.md"; b1 = p1.read_bytes()
tag1 = as_list_(M.parse_frontmatter(p1.read_text())[0].get("tags"))[0]
run(["sql", f"UPDATE notes SET tags = tags + '{tag1}' WHERE title LIKE 'Note 1 %'", "--apply"], cwd=NV)
check("N fixes", p1.read_bytes() == b1, "no-op list_add rewrote the file")
# MERGE: keep linking to drop does not become a self-link; human region in a third note untouched
for i in range(4):
    a, b, c = R.sample(range(2, 10), 3)
    pa, pb, pc = (NV / f"notes/n{x:03d}.md" for x in (a, b, c))
    if any(M._is_locked(M.parse_frontmatter(q.read_text())[0]) for q in (pa, pb)):
        continue
    ida = M.parse_frontmatter(pa.read_text())[0]["id"]; idb = M.parse_frontmatter(pb.read_text())[0]["id"]
    if M.parse_frontmatter(pa.read_text())[0].get("status") == "superseded":
        continue
    pb.write_text(pb.read_text().replace("## Log", f"see [[{ida}]]\n\n## Log"))
    pc.write_text(pc.read_text().replace("## Log", f"<!-- audock:human -->\nmine [[{ida}]]\n<!-- /audock:human -->\nalso [[{ida}]]\n\n## Log"))
    rc, out, err = run(["sql", f"MERGE '{ida}' INTO '{idb}'", "--apply"], cwd=NV)
    tb, tc = pb.read_text(), pc.read_text()
    check("N fixes", rc == 0 and f"[[{idb}]]" not in tb.split("## Log")[0], f"self-link created in keep:\n{tb}")
    check("N fixes", f"mine [[{ida}]]" in tc and f"also [[{idb}]]" in tc, f"human region / rewire wrong:\n{tc}")
    check("N fixes", f"updated: {M.today()}" in tb, "merge did not bump keep updated")
# doctor: a self-link doesn't make a note non-orphan
po = NV / "notes/orph.md"
po.write_text("---\nid: 20260101-orph\ntitle: Orph\ntype: note\ntags: [x]\nstatus: stable\n---\n\nme [[20260101-orph]] [[n001]]\n")
rc, out, _ = run(["doctor"], cwd=NV)
check("N fixes", "notes/orph.md" in out.split("orphan notes")[1].split("under-linked")[0], "self-link counted as backlink")
# frozen-binary vault fallback = cwd (simulated)
M.sys.frozen = True
try:
    os.chdir(SB)
    check("N fixes", M._resolve_vault(None) is None, "frozen binary outside a vault must not pick the cwd")
finally:
    del M.sys.frozen

# outside any vault, every command except init refuses (never scans an arbitrary tree)
OUT = SB / "not-a-vault"; OUT.mkdir(exist_ok=True); (OUT / "random.md").write_text("---\ntype: note\n---\nzz\n")
for cmd in (["query", "zz"], ["doctor"], ["reindex"], ["sql", "SELECT * FROM all"], ["context", "zz"]):
    r = subprocess.run([str(AUDOCK), "--vault", str(OUT), *cmd], capture_output=True, text=True)
    check("N fixes", r.returncode != 0 and "not an Audock vault" in r.stderr, f"{cmd}: {r.stderr[-160:]}")
r = subprocess.run([str(AUDOCK), "query", "zz"], cwd=OUT, capture_output=True, text=True,
                   env={**os.environ, "AUDOCK_VAULT": ""})
check("N fixes", r.returncode != 0 or "not inside" in r.stderr or "zz" not in r.stdout, f"cwd fallback: {r.stdout[-160:]}")

# ======================================================================================
total_p = sum(p for p, f in RESULTS.values()); total_f = sum(f for p, f in RESULTS.values())
print(f"\nseed={SEED}")
for g, (p, f) in sorted(RESULTS.items()):
    print(f"  {g:32s} {p:4d} passed  {f:3d} failed")
print(f"\n==== SYNTHETIC: {total_p} passed, {total_f} failed ({total_p + total_f} total) ====")
for g, d in FAILS:
    print(f"\n--- FAIL [{g}]\n{d}")
sys.exit(1 if total_f else 0)
