"""Build The Lift's question bank.

Combines Claude's nicheness tiers (tiers.txt) with the Wikipedia data in
questions.js (article titles and redirect spellings).

Run:  python3 build_lift.py   -> writes lift_questions.js
"""
import json, re, sys, unicodedata

SPECIAL = {"ð": "d", "þ": "th", "æ": "ae", "ø": "o", "œ": "oe", "ß": "ss", "ł": "l", "đ": "d", "ı": "i", "ʻ": "", "′": ""}
ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7, "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12,
         "xiii": 13, "xiv": 14, "xv": 15, "xvi": 16, "xvii": 17, "xviii": 18, "xix": 19, "xx": 20, "xxi": 21, "xxii": 22, "xxiii": 23}
SUFFIXES = [" national park and preserve", " national and state parks", " national park", " fc", " afc", " language",
            " cat", " horse", " pony", " dog", " cheese", " cocktail"]


def norm(s):
    """Must match norm() in index.html."""
    s = s.lower()
    s = "".join(SPECIAL.get(c, c) for c in s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^the ", "", s)
    return s.replace(" ", "")


def spaced(s):
    """Like norm() but keeps spaces, for word-level alias tricks."""
    s = s.lower()
    s = "".join(SPECIAL.get(c, c) for c in s)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]", "", s.replace("&", " and "))
    return re.sub(r"\s+", " ", s).strip()


def strip_paren(t):
    return re.sub(r"\s*\([^)]*\)\s*$", "", t).strip()


def auto_aliases(name, team):
    out = {name, strip_paren(name)}
    base = strip_paren(name)
    if ", " in base:
        out.add(base.split(", ")[0])
    sp = spaced(base)
    for suf in SUFFIXES:
        if sp.endswith(suf) and len(sp) > len(suf) + 2:
            out.add(sp[: -len(suf)])
    if sp.startswith("pope "):
        out.add(sp[5:])
    words = sp.split()
    if words and words[-1] in ROMAN:
        out.add(" ".join(words[:-1] + [str(ROMAN[words[-1]])]))
        if sp.startswith("pope "):
            out.add(" ".join(words[1:-1] + [str(ROMAN[words[-1]])]))
    if team and len(words) > 1:
        out.add(words[-1])
        if len(words) > 2:
            out.add(" ".join(words[-2:]))
    return out


def parse_item(raw):
    m = re.match(r"^(.*?)\s*\{([^}]*)\}\s*$", raw)
    if m:
        return m.group(1).strip(), [a.strip() for a in m.group(2).split(",") if a.strip()]
    return raw.strip(), []


def main():
    src = open("questions.js").read()
    wiki = json.loads(src[src.index("=") + 1: src.rindex(";")])
    wiki = {q["q"]: q["a"] for q in wiki}
    renamed = {"Name a country": "Name any country in the world",
               "Name a Disney animated film": "Name a Walt Disney Animation Studios film","Name a Charles Dickens book": "Name a Charles Dickens novel",
               "Name a Stephen King book or story": "Name a Stephen King novel",
               "Name an Olympic sport (past or present)": "Name an Olympic sport",
               "Name a video game console (home or handheld)": "Name a video game console"}

    blocks, cur = [], None
    for line in open("tiers.txt", encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        if line.startswith("= "):
            head = line[2:].strip()
            flags = set()
            while head.split(" ", 1)[0] in ("!", "team"):
                f, head = head.split(" ", 1)
                flags.add(f)
            cur = {"q": head, "only": "!" in flags, "team": "team" in flags, "tiers": {}, "x": []}
            blocks.append(cur)
            continue
        key, rest = line.split(":", 1)
        items = [i for i in (p.strip() for p in rest.split(" | ")) if i]
        if key.strip() == "x":
            cur["x"] += items
        else:
            cur["tiers"][int(key)] = items

    bank, report = [], []
    for b in blocks:
        data = wiki.get(b["q"]) or wiki.get(renamed.get(b["q"], ""), [])
        by_title, by_short = {}, {}
        for i, a in enumerate(data):
            title = a[3].replace("_", " ")
            by_title.setdefault(norm(title), i)
            by_short.setdefault(norm(strip_paren(title)), i)
            for al in auto_aliases(title, False):
                by_short.setdefault(norm(al), i)
        removed = set()
        for x in b["x"]:
            i = by_title.get(norm(x), by_short.get(norm(strip_paren(x))))
            if i is not None:
                removed.add(i)
        used, entries, added = set(), [], []
        for tier in range(1, 6):
            for raw in b["tiers"].get(tier, []):
                if raw == "*":
                    for i, a in enumerate(data):
                        if i not in used and i not in removed:
                            used.add(i)
                            entries.append({"name": a[3].replace("_", " "), "tier": 5, "extra": [], "data": a})
                    continue
                name, extra = parse_item(raw)
                i = by_title.get(norm(name), by_short.get(norm(strip_paren(name))))
                if i is None:
                    i = next((by_short[norm(a)] for a in auto_aliases(name, False) if norm(a) in by_short), None)
                if i is not None and i in used:
                    continue  # listed twice: first tier wins
                if i is not None:
                    used.add(i)
                elif any(norm(e["name"]) == norm(name) for e in entries):
                    continue
                else:
                    added.append(name)
                entries.append({"name": name if i is None else data[i][3].replace("_", " "),
                                "tier": tier, "extra": extra, "data": data[i] if i is not None else None})
        # display names: drop "(film)" style suffixes unless two answers would look identical
        shorts = [strip_paren(e["name"]) for e in entries]
        out = []
        for e, short in zip(entries, shorts):
            display = short if shorts.count(short) == 1 else e["name"]
            al = set()
            for s in auto_aliases(e["name"], b["team"]) | set(e["extra"]):
                al.add(norm(s))
            if e["data"]:
                al |= {norm(a) for a in e["data"][2]}
            al = sorted(a for a in al if len(a) >= 2 and a != norm(display))
            article = e["data"][3] if e["data"] else None
            out.append([display, e["tier"], al, article])
        bank.append({"q": b["q"], "a": out})
        counts = [sum(1 for o in out if o[1] == t) for t in range(1, 6)]
        report.append(f"{b['q']}: {counts}" + (f"  added: {added}" if added and not b["only"] else ""))

    with open("lift_questions.js", "w", encoding="utf-8") as f:
        f.write("// The Lift question bank. Each answer: [name, tier 1-5 (5 = most niche), accepted spellings, Wikipedia article or null]\n")
        f.write("// Tiers are Claude's judgement (tiers.txt); spellings come from Wikipedia redirects. Built by build_lift.py.\n")
        f.write("window.LIFT_BANK=" + json.dumps(bank, separators=(",", ":"), ensure_ascii=False) + ";\n")
    print("\n".join(report))
    print("wrote", len(bank), "questions,", sum(len(q["a"]) for q in bank), "answers", file=sys.stderr)


if __name__ == "__main__":
    main()
