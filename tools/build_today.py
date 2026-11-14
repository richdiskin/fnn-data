#!/usr/bin/env python3
"""Rebuild today/index.html (https://richdiskin.github.io/fnn-data/today/) from stories.json.

Run from the repo root:  python3 tools/build_today.py [--check]
- Static HTML only. Exits non-zero (and writes nothing) on any problem, so the last good page stays up.
- Sections, each with its own heading: Today's Paper (FNN news), Faith Family Freedom, The MOGazine (gossip desk, kept separate).
- Every headline, kicker and deck is copied from stories.json word for word. No new text about any story.
- Styling is read from the current today/index.html <style> block, so the v5 record-blue look carries over.
"""
import datetime as dt, html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "today" / "index.html"
STORY = "https://www.fnnfakenewsnetwork.com/story/"
MAG = "https://amber-breeze-giant-tundra.grok.me/"
BANNED = re.compile(r"\b(fictional|AI-generated|Elo)\b", re.I)

def die(m): print("STOP: " + m, file=sys.stderr); sys.exit(1)
def e(s): return html.escape(s or "", quote=True).replace("&#x27;", "'")

def card(s, lead):
    u = e(STORY + s["slug"])
    h = e(s["headline"]) + (" <em>" + e(s["headline_now"]) + "</em>" if s.get("headline_now") else "")
    return ('        <article class="fnn-card' + (" fnn-lead" if lead else "") + '">'
            '<p class="fnn-kicker">' + e(s.get("kicker")) + '</p>'
            '<h3><a href="' + u + '">' + h + '</a></h3>'
            + ('<p class="fnn-deck">' + e(s["deck"]) + '</p>' if s.get("deck") else "") +
            '<a class="fnn-go" href="' + u + '">Read the receipts \u2192</a></article>')

def section(title, sub, items, list_attr, extra=""):
    return ('<section class="tp-sec">\n  <div class="fnn-today-head"><h2>' + title + '</h2><small' +
            (' id="fnn-today-date"' if list_attr.startswith('id=') else '') + '>' + sub + '</small></div>\n'
            '  <div ' + list_attr + '>\n' + "\n".join(items) + '\n  </div>' + extra + '\n</section>')

def main():
    feed = json.loads((ROOT / "stories.json").read_text())
    day = (feed.get("date") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day): die("feed.date missing")
    todays = [s for s in feed.get("stories", []) if (s.get("date") or "")[:10] == day]
    for s in todays:
        if not s.get("slug") or not s.get("headline"): die("story missing slug or headline")
    lead = feed.get("lead")
    news = [s for s in todays if s.get("section") not in ("mogazine", "faith")]
    news.sort(key=lambda s: 0 if s["slug"] == lead else 1)  # stable: lead first, then feed order
    faith = [s for s in todays if s.get("section") == "faith"]
    gossip = [s for s in todays if s.get("section") == "mogazine"]
    if not news: die(f"no FNN news stories dated {day}; keeping the last page")

    old = PAGE.read_text()
    m = re.search(r"<style>(.*?)</style>", old, re.S)
    if not m: die("no <style> in current today/index.html")
    css = m.group(1).split("/* tp-auto */")[0].rstrip()
    # the extra sections reuse the Today's Paper list styling
    extra_css = "\n".join(r.replace("#fnn-today-list", ".tp-list")
                          for r in re.findall(r"[^{}]*#fnn-today-list[^{}]*\{[^{}]*\}", css))
    # media/container wrappers: re-wrap any list rule that sat inside one
    wrapped = []
    for w in re.finditer(r"(@(?:media|container)[^{]+)\{((?:[^{}]*\{[^{}]*\})*[^{}]*)\}", css):
        inner = [r.replace("#fnn-today-list", ".tp-list") for r in re.findall(r"[^{}]*#fnn-today-list[^{}]*\{[^{}]*\}", w.group(2))]
        if inner: wrapped.append(w.group(1).strip() + "{" + "".join(i.strip() for i in inner) + "}")
    top_level = re.sub(r"@(?:media|container)[^{]+\{(?:[^{}]*\{[^{}]*\})*[^{}]*\}", "", css)
    extra_css = "\n".join(r.strip().replace("#fnn-today-list", ".tp-list")
                          for r in re.findall(r"[^{}]*#fnn-today-list[^{}]*\{[^{}]*\}", top_level))
    css += ("\n/* tp-auto */\n" + extra_css + "\n" + "\n".join(wrapped) +
            "\n#fnn-home .tp-sec{display:block!important;margin:0 0 48px!important}"
            "\n#fnn-home .tp-foot{padding:8px 0 0!important;font-family:var(--cond)!important;font-size:16px!important;color:var(--muted)!important}"
            "\n#fnn-home .tp-foot a{color:var(--accent)!important;font-weight:700!important}")

    d = dt.date.fromisoformat(day)
    nice = f"{d.strftime('%B')} {d.day}, {d.year}"
    dline = "Edition updated " + nice
    body = [section("Today\u2019s Paper", e(dline),
                    [card(s, s["slug"] == lead) for s in news], 'id="fnn-today-list"')]
    if faith:
        body.append(section("Faith Family Freedom", "", [card(s, False) for s in faith], 'class="tp-list"'))
    if gossip:
        body.append(section("The MOGazine", "Gossip &amp; Entertainment",
                            [card(s, False) for s in gossip], 'class="tp-list"',
                            '\n  <p class="tp-foot"><a href="' + MAG + '">Read The MOGazine \u2192</a></p>'))
    title = f"Today\u2019s Paper \u00b7 {nice} \u00b7 FNN Fake News Network"
    head_end = old.find("<style>")
    head = old[:head_end]
    head = re.sub(r"<title>[^<]*</title>", "<title>" + e(title) + "</title>", head)
    head = re.sub(r'(<meta name="description" content=")[^"]*', r"\g<1>" + e(f"Today\u2019s FNN stories, {nice}."), head)
    head = re.sub(r'(<meta property="og:title" content=")[^"]*', r"\g<1>" + e(title), head)
    page = (head + "<style>" + css + "\n</style>\n</head><body>\n<div id=\"fnn-home\" class=\"fnn\">\n"
            '  <div class="tp-top"><div class="w"><a href="https://www.fnnfakenewsnetwork.com/">FNN <b>Fake News</b> Network</a></div></div>\n'
            '  <div class="tp-body"><div class="w">\n' + "\n".join(body) + "\n  </div></div>\n</div>\n</body></html>\n")

    if re.search(r"<\s*/?\s*script|\son\w+\s*=", page, re.I): die("script or on* handler in page")
    if "grok.me/story" in page: die("grok.me story link")
    txt = re.sub(r"<[^>]+>", " ", page.split("</style>", 1)[1])
    if BANNED.search(txt): die("banned word in page: " + BANNED.search(txt).group(0))
    if "--check" in sys.argv:
        print("check only; would write", len(page.encode()), "bytes"); return
    if page == old: print("today/index.html already current"); return
    PAGE.write_text(page)
    print(f"today/index.html rebuilt for {day} (edition {feed.get('edition')}): "
          f"{len(news)} news, {len(faith)} faith, {len(gossip)} MOGazine, {len(page.encode())} bytes")

if __name__ == "__main__": main()
