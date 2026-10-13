"""Build the Clay Hunt question bank from Wikipedia.

Answer sets come from Wikidata (the structured side of Wikipedia), and every
answer is an English Wikipedia article. Rarity comes from that article's
Wikipedia page views over the last 60 days: the less-read the article, the
rarer the answer. Accepted spellings come from the article's Wikipedia redirects.

Run:  python3 build_questions.py   -> writes questions.js
"""
import json, re, sys, time, unicodedata, urllib.parse, urllib.request

UA = "ClayHuntQuizBuilder/1.1 (one-off offline build of a trivia game question bank; https://claude.ai) python-urllib"
MAX_ANSWERS = 260

# Each question: (prompt, source, options)
#   source "S:<expr>"  -> Wikidata items matching a haswbstatement search (use " | " to union several)
#   source "V:<expr>:P" -> values of property P on items matching the search
#   source "E:Qid:P"    -> values of property P on one item
# options: surname (accept last name), keep (python filter on an item's claims)
def num(c, p):
    try: return float(c[p][0]["mainsnak"]["datavalue"]["value"]["amount"])
    except Exception: return None
def first(c, p):
    try: return c[p][0]["mainsnak"]["datavalue"]["value"]["id"]
    except Exception: return None
TRANS = {"Q15": {"Q79"}, "Q48": {"Q159", "Q43", "Q79", "Q232", "Q227", "Q230"}, "Q46": {"Q43", "Q232", "Q227", "Q230"}}
def on_continent(q):
    return lambda item, c: first(c, "P30") == q or item in TRANS.get(q, ())
LIVE = " -haswbstatement:P576"
SONG = "haswbstatement:P31=Q7366 haswbstatement:P175={0} | haswbstatement:P31=Q134556 haswbstatement:P175={0}"
NOVEL = "haswbstatement:P31=Q7725634 haswbstatement:P50={0} | haswbstatement:P31=Q8261 haswbstatement:P50={0} | haswbstatement:P31=Q47461344 haswbstatement:P50={0}"
FILM = "haswbstatement:P31=Q11424 haswbstatement:{0}"
STATE = "haswbstatement:P31=Q3624078" + LIVE
Q = [
 ("Name a chemical element", "S:haswbstatement:P31=Q11344 haswbstatement:P1086", {"keep": lambda i, c: (num(c, "P1086") or 999) <= 118}),
 ("Name a country in Africa", "S:" + STATE + " haswbstatement:P30=Q15", {"keep": on_continent("Q15")}),
 ("Name a country in Europe", "S:" + STATE + " haswbstatement:P30=Q46", {"keep": on_continent("Q46")}),
 ("Name a country in Asia", "S:" + STATE + " haswbstatement:P30=Q48", {"keep": on_continent("Q48")}),
 ("Name a country in South America", "S:" + STATE + " haswbstatement:P30=Q18", {"keep": on_continent("Q18")}),
 ("Name a country in North America", "S:" + STATE + " haswbstatement:P30=Q49", {"keep": on_continent("Q49")}),
 ("Name any country in the world", "S:" + STATE, {}),
 ("Name a U.S. state", "S:haswbstatement:P31=Q35657", {}),
 ("Name a U.S. state capital", "V:haswbstatement:P31=Q35657:P36", {}),
 ("Name a European capital city", "V:" + STATE + " haswbstatement:P30=Q46:P36", {}),
 ("Name a state or union territory of India", "S:haswbstatement:P31=Q131541 | haswbstatement:P31=Q467745", {}),
 ("Name a Canadian province or territory", "S:haswbstatement:P31=Q11828004 | haswbstatement:P31=Q9357527", {}),
 ("Name a moon of Saturn", "C:Moons of Saturn | Gallic group | Inuit group | Norse group", {"extra": ["Titan (moon)", "Mimas (moon)", "Dione (moon)", "Iapetus (moon)", "Janus (moon)", "Tethys (moon)", "Enceladus", "Hyperion (moon)"]}),
 ("Name a moon of Jupiter", "C:Moons of Jupiter | Ananke group | Carme group | Carpo group | Himalia group | Pasiphae group | Galilean moons", {"extra": ["Amalthea (moon)", "Thebe (moon)"]}),
 ("Name a constellation", "S:haswbstatement:P31=Q8928", {}),
 ("Name a dog breed", "S:haswbstatement:P31=Q39367", {}),
 ("Name a cat breed", "S:haswbstatement:P31=Q43577", {}),
 ("Name a horse breed", "S:haswbstatement:P31=Q1160573", {}),
 ("Name a cheese", "S:haswbstatement:P31=Q10943", {}),
 ("Name a cocktail", "S:haswbstatement:P31=Q134768", {}),
 ("Name a programming language", "S:haswbstatement:P31=Q9143", {}),
 ("Name a video game console", "C:Home video game consoles", {}),
 ("Name a U.S. national park", "S:haswbstatement:P31=Q34918903", {}),
 ("Name a U.S. president", "S:haswbstatement:P39=Q11696 haswbstatement:P31=Q5", {"surname": True}),
 ("Name a British prime minister", "S:haswbstatement:P39=Q14211 haswbstatement:P31=Q5", {"surname": True}),
 ("Name a Roman emperor", "S:haswbstatement:P39=Q842606 haswbstatement:P31=Q5", {}),
 ("Name a pope", "S:haswbstatement:P39=Q19546 haswbstatement:P31=Q5", {}),
 ("Name a Nobel Prize in Physics winner", "S:haswbstatement:P166=Q38104", {"surname": True}),
 ("Name a Nobel Prize in Literature winner", "S:haswbstatement:P166=Q37922", {"surname": True}),
 ("Name an NBA team", "S:haswbstatement:P118=Q155223 haswbstatement:P31=Q13393265" + LIVE, {}),
 ("Name an NFL team", "S:haswbstatement:P118=Q1215884 haswbstatement:P31=Q17156793" + LIVE, {}),
 ("Name a club that has played in the Premier League", "V:haswbstatement:P3450=Q9448:P1923", {}),
 ("Name a Beatles song or album", "C:The Beatles songs", {}),
 ("Name a Queen song", "S:" + SONG.format("Q15862"), {}),
 ("Name a Michael Jackson song or album", "S:" + SONG.format("Q2831"), {}),
 ("Name a Taylor Swift song or album", "S:" + SONG.format("Q26876"), {}),
 ("Name a Pixar film", "C:Pixar animated films", {}),
 ("Name a Studio Ghibli film", "C:Studio Ghibli animated films", {}),
 ("Name a Walt Disney Animation Studios film", "S:" + FILM.format("P272=Q1047410"), {}),
 ("Name a James Bond film", "C:James Bond films", {}),
 ("Name a Steven Spielberg film", "S:" + FILM.format("P57=Q8877"), {}),
 ("Name a Christopher Nolan film", "S:" + FILM.format("P57=Q25191"), {}),
 ("Name a Shakespeare play", "C:Shakespearean comedies | Shakespearean histories | Shakespearean tragedies | Shakespearean romances", {}),
 ("Name a Charles Dickens novel", "S:" + NOVEL.format("Q5686"), {}),
 ("Name a Stephen King novel", "S:" + NOVEL.format("Q39829"), {}),
 ("Name an opera by Mozart", "C:Operas by Wolfgang Amadeus Mozart", {}),
 ("Name a painting by Vincent van Gogh", "S:haswbstatement:P170=Q5582 haswbstatement:P31=Q3305213", {}),
 ("Name a Greek god or goddess", "S:haswbstatement:P31=Q22989102 | haswbstatement:P31=Q3307934", {}),
 ("Name a Norse god or goddess", "S:haswbstatement:P31=Q16513881", {}),
 ("Name an Olympic sport", "S:haswbstatement:P31=Q212434", {}),
 ("Name an official language of the European Union", "E:Q458:P37", {}),
 ("Name a car manufacturer", "S:haswbstatement:P31=Q786820" + LIVE, {}),
 ("Name a Formula One World Champion", "C:Formula One World Drivers' Champions", {"surname": True}),
 ("Name an Apollo mission", "S:haswbstatement:P361=Q46611", {}),
]


def get(url, tries=10):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:
            wait = min(60, 5 * (i + 1))
            try: wait = max(wait, int(e.headers.get("Retry-After", 0)))
            except Exception: pass
            print("  retry", i, urllib.parse.urlparse(url).netloc, e, "wait", wait, file=sys.stderr)
            time.sleep(wait)
    raise RuntimeError(url)


WD = "https://www.wikidata.org/w/api.php?"


def wd_search(expr):
    ids, off = [], 0
    while True:
        d = get(WD + urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": expr,
                 "srlimit": 500, "sroffset": off, "srprop": "", "format": "json"}))
        ids += [h["title"] for h in d["query"]["search"]]
        if "continue" not in d or off > 3000:
            return ids
        off = d["continue"]["sroffset"]


def wd_entities(ids, claims=True):
    out = {}
    for i in range(0, len(ids), 50):
        d = get(WD + urllib.parse.urlencode({"action": "wbgetentities", "ids": "|".join(ids[i:i + 50]),
                 "props": "sitelinks|claims" if claims else "sitelinks", "sitefilter": "enwiki", "format": "json"}))
        out.update(d.get("entities", {}))
    return out


def prop_values(ents, p):
    vals = []
    for e in ents.values():
        for c in e.get("claims", {}).get(p, []):
            v = c["mainsnak"].get("datavalue", {}).get("value")
            if isinstance(v, dict) and "id" in v:
                vals.append(v["id"])
    return sorted(set(vals))


JUNK = re.compile(r"^lists? of|discography|soundtrack|filmography|in popular culture|franchise|videography| group$|^galilean moons$|^moons of |\bin (film|fiction|music)\b", re.I)


def source_titles(src, keep):
    kind, rest = src.split(":", 1)
    if kind == "C" and " | " in rest:
        return sorted({t for part in rest.split(" | ") for t in source_titles("C:" + part, keep)})
    if kind == "C":
        titles, cont = [], {}
        while True:
            d = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "list": "categorymembers",
                     "cmtitle": "Category:" + rest, "cmnamespace": 0, "cmlimit": "max", "format": "json", **cont}))
            titles += [m["title"] for m in d["query"]["categorymembers"]]
            if "continue" not in d:
                return sorted(t for t in set(titles) if not JUNK.search(t) and t != rest)
            cont = {"cmcontinue": d["continue"]["cmcontinue"]}
    if kind == "S":
        ids = sorted({i for part in rest.split(" | ") for i in wd_search(part)})
    elif kind == "V":
        expr, p = rest.rsplit(":", 1)
        ids = prop_values(wd_entities(wd_search(expr)), p)
    else:
        q, p = rest.split(":")
        ids = prop_values(wd_entities([q]), p)
    ents = wd_entities(ids, claims=bool(keep))
    titles = []
    for i, e in ents.items():
        t = e.get("sitelinks", {}).get("enwiki", {}).get("title")
        if t and (not keep or keep(i, e.get("claims", {}))):
            titles.append(t)
    return sorted(set(titles))


def wiki_info(titles):
    """Return {title: (views60, [redirects])}, following Wikipedia redirects."""
    info = {}
    for i in range(0, len(titles), 50):
        batch = titles[i:i + 50]
        params = {"action": "query", "titles": "|".join(batch), "prop": "pageviews|redirects",
                  "rdlimit": "max", "rdnamespace": 0, "pvipdays": 60, "redirects": 1,
                  "format": "json", "formatversion": 2}
        cont = {}
        while True:
            d = get("https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({**params, **cont}))
            for p in d.get("query", {}).get("pages", []):
                if p.get("missing"):
                    continue
                v, rs = info.get(p["title"], (0, []))
                if "pageviews" in p:
                    v = sum(x or 0 for x in p["pageviews"].values())
                rs = rs + [r["title"] for r in p.get("redirects", [])]
                info[p["title"]] = (v, rs)
            if "continue" not in d:
                break
            cont = d["continue"]
        time.sleep(0.2)
    return info


def strip_paren(t):
    return re.sub(r"\s*\([^)]*\)\s*$", "", t).strip()


def norm(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = s.replace("&", "and")
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"^the ", "", s)
    return re.sub(r"\s+", " ", s).strip()


BAD = re.compile(r"^(list of|history of|outline of|template|category|portal)|\b(in|of) the (19|20)\d\d|\d{4}-\d{4}|^\d+[-\d]*$", re.I)


def aliases(title, redirects, surname):
    out = {norm(title), norm(strip_paren(title))}
    for r in redirects:
        if len(r) > 45 or BAD.search(r):
            continue
        out.add(norm(strip_paren(r)))
    if surname:
        last = strip_paren(title).replace(",", " ").split()
        last = [w for w in last if w.lower() not in ("jr.", "sr.", "ii", "iii", "jr", "sr")]
        if last:
            out.add(norm(last[-1]))
    return sorted(a for a in out if len(a) >= 2)


def main():
    import os
    cache = json.load(open("bank_cache.json")) if os.path.exists("bank_cache.json") else {}
    bank = []
    for row in Q:
        if row[0] in cache:
            e = cache[row[0]]
            e["a"] = [a for a in e["a"] if not JUNK.search(a[3].replace("_", " "))]
            bank.append(e)
            continue
        prompt, src, opt = row
        surname = opt.get("surname", False)
        print(prompt, file=sys.stderr)
        try:
            titles = sorted(set(source_titles(src, opt.get("keep")) + opt.get("extra", [])))
        except RuntimeError:
            print("  SKIP: query failed", file=sys.stderr)
            continue
        if len(titles) < 6:
            print("  SKIP: only", len(titles), file=sys.stderr)
            continue
        info = wiki_info(titles)
        ans = [(t, v, rs) for t, (v, rs) in info.items() if not JUNK.search(t) and not src.endswith(":" + t)]
        ans.sort(key=lambda a: -a[1])
        ans = ans[:MAX_ANSWERS]
        print(f"  {len(ans)} answers; top: {[a[0] for a in ans[:4]]}", file=sys.stderr)
        bank.append({
            "q": prompt,
            "a": [[strip_paren(t), v, aliases(t, rs, surname), t.replace(" ", "_")] for t, v, rs in ans],
        })
        cache[prompt] = bank[-1]
        json.dump(cache, open("bank_cache.json", "w"))
        time.sleep(0.5)
    with open("questions.js", "w") as f:
        f.write("// Generated from Wikipedia/Wikidata by build_questions.py. Each answer: [name, 60-day Wikipedia views, accepted spellings, article]\n")
        f.write("window.QUESTION_BANK=" + json.dumps(bank, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print("wrote", len(bank), "questions", file=sys.stderr)


if __name__ == "__main__":
    main()
