#!/usr/bin/env python3
"""Build the German pages under /de/ from the bilingual pages.

The pages at the site root carry both languages (<x lang="en"> next to
<x lang="de">) and are served as the English site. This writes a German-only
copy of each to de/<same path>: every lang="en" element is removed, <html> and
<body> are set to German, the <head> gets German titles, descriptions, share
images and canonical address, internal links point into /de/, and alt and
aria texts are translated.

So: edit the root pages, then run this (the workflows run it too, on every
push to main and after the weekly refresh). Never edit de/ by hand.

    python3 scripts/build_german_pages.py          # write de/
    python3 scripts/build_german_pages.py --check  # exit 1 if de/ is stale

Standard library only.
"""

import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://musicdrops.app"

# source file -> (path, German <head>)
PAGES = {
    "index.html": ("/", {
        "title": "MusicDrops: Benachrichtigung bei neuer Musik für iPhone und iPad",
        "description": "Werde benachrichtigt, wenn deine Künstler neue Musik veröffentlichen, und sieh kommende Alben vor dem Release. Für iPhone, iPad und iPhone Duo. Kostenlos für 10 Künstler.",
        "og_title": "MusicDrops: Verpasse keinen Drop",
        "og_description": "Folge den Künstlern, die du liebst. MusicDrops sagt dir, wenn ihre neue Musik erscheint.",
        "image_alt": "MusicDrops: Verpasse keinen Drop",
    }),
    "support/index.html": ("/support/", {
        "title": "Support | MusicDrops",
        "description": "MusicDrops-Support: Antworten auf häufige Fragen, Hilfe zu Abos und ein Postfach für alles andere.",
        "og_title": "Support | MusicDrops",
        "og_description": "Hilfe zu MusicDrops: E-Mail, FAQ und Abo-Verwaltung.",
        "image_alt": "MusicDrops: Wie können wir helfen?",
    }),
    "press/index.html": ("/press/", {
        "title": "Pressekit | MusicDrops",
        "description": "MusicDrops-Pressekit: Fakten, Textbausteine, App-Icon und Screenshots für Journalistinnen, Journalisten und Rezensenten.",
        "og_title": "Pressekit | MusicDrops",
        "og_description": "Fakten, Textbausteine, App-Icon und Screenshots für die Berichterstattung.",
        "image_alt": "MusicDrops: Pressekit",
    }),
    "privacy/index.html": ("/privacy/", {
        "title": "Datenschutzerklärung | MusicDrops",
        "description": "Datenschutzerklärung von MusicDrops: wie mit Daten umgegangen wird.",
        "og_title": "Datenschutzerklärung | MusicDrops",
        "og_description": "Wie MusicDrops mit Daten umgeht.",
        "image_alt": "MusicDrops: Datenschutzerklärung",
    }),
    "terms/index.html": ("/terms/", {
        "title": "Nutzungsbedingungen | MusicDrops",
        "description": "Nutzungsbedingungen von MusicDrops.",
        "og_title": "Nutzungsbedingungen | MusicDrops",
        "og_description": "Die Bedingungen für die Nutzung von MusicDrops.",
        "image_alt": "MusicDrops: Nutzungsbedingungen",
    }),
    "impressum/index.html": ("/impressum/", {
        "title": "Impressum | MusicDrops",
        "description": "Impressum von MusicDrops: Angaben gemäß § 5 DDG.",
        "og_title": "Impressum | MusicDrops",
        "og_description": "Impressum von MusicDrops.",
        "image_alt": "MusicDrops: Impressum",
    }),
}

# alt, aria-label and title texts (English pages keep them in English)
TEXTS = {
    "Menu": "Menü",
    "Main": "Hauptnavigation",
    "Language": "Sprache",
    "Switch to dark mode": "Zum dunklen Modus wechseln",
    "selected": "ausgewählt",
    "Plans": "Tarife",
    "On this page": "Auf dieser Seite",
    "MusicDrops app icon": "MusicDrops-App-Icon",
    "MusicDrops app icon, small": "MusicDrops-App-Icon, klein",
    "The Drops timeline on iPhone: Up next, a monthly recap card and this week’s releases":
        "Die Drops-Timeline auf dem iPhone: Als Nächstes, eine Monatsrückblick-Karte und die Releases dieser Woche",
    "The Drops timeline on iPhone": "Die Drops-Timeline auf dem iPhone",
    "Upcoming Drops on iPhone: announced records with how many days are left":
        "Kommende Drops auf dem iPhone: angekündigte Platten mit den Tagen bis zum Release",
    "A release page on iPhone with its rating, details and an Open in Apple Music button":
        "Eine Release-Seite auf dem iPhone mit Bewertung, Details und der Taste „In Apple Music öffnen“",
    "A monthly recap on iPhone: 11 drops from 11 artists, with the month’s covers":
        "Ein Monatsrückblick auf dem iPhone: 11 Drops von 11 Künstlern, mit den Covern des Monats",
    "Sharing a recap on iPhone as a square image": "Einen Rückblick auf dem iPhone als quadratisches Bild teilen",
    "An artist page on iPad in landscape, with albums, EPs and singles side by side":
        "Eine Künstlerseite auf dem iPad im Querformat, mit Alben, EPs und Singles nebeneinander",
    "The same artist page on iPhone": "Dieselbe Künstlerseite auf dem iPhone",
    "The Drops timeline on iPhone Duo’s outer display": "Die Drops-Timeline auf dem Außendisplay des iPhone Duo",
    "An artist page on iPhone Duo folded like a book: the artist on one half, their records on the other":
        "Eine Künstlerseite auf dem iPhone Duo, wie ein Buch gefaltet: der Künstler auf der einen Hälfte, seine Platten auf der anderen",
    "A release page and its track list side by side on iPhone Duo’s inner display":
        "Eine Release-Seite und ihre Titelliste nebeneinander auf dem Innendisplay des iPhone Duo",
    "Search on iPhone with trending artists and upcoming releases":
        "Die Suche auf dem iPhone mit angesagten Künstlern und kommenden Releases",
    "Search on iPad in landscape": "Die Suche auf dem iPad im Querformat",
    "Search on iPhone Duo's inner display, open flat": "Die Suche auf dem Innendisplay des iPhone Duo, ganz offen",
}

JSON_LD_DESCRIPTION = (
    "Get a notification when the artists you follow release new music, and see upcoming albums before they drop.",
    "Werde benachrichtigt, wenn die Künstler, denen du folgst, neue Musik veröffentlichen, und sieh kommende Alben vor dem Release.",
)

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class EnglishFinder(HTMLParser):
    """Finds the source spans of every lang="en" element below <html>."""

    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.text = text
        self.line_starts = [0]
        for m in re.finditer("\n", text):
            self.line_starts.append(m.end())
        self.stack = []      # (tag, start offset or None)
        self.spans = []

    def at(self):
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        start = self.at()
        english = tag != "html" and dict(attrs).get("lang") == "en"
        if tag in VOID:
            if english and not self.inside_english():
                self.spans.append((start, start + len(self.get_starttag_text())))
            return
        self.stack.append((tag, start if english else None))

    def handle_startendtag(self, tag, attrs):
        start = self.at()
        if dict(attrs).get("lang") == "en" and not self.inside_english():
            self.spans.append((start, start + len(self.get_starttag_text())))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        # Close up to the matching tag (tolerates the odd unclosed <p>/<li>).
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                opened = self.stack[i][1]
                del self.stack[i:]
                if opened is not None and not self.inside_english():
                    end = self.text.index(">", self.at()) + 1
                    self.spans.append((opened, end))
                return

    def inside_english(self):
        return any(start is not None for _, start in self.stack)


def strip_english(text):
    finder = EnglishFinder(text)
    finder.feed(text)
    finder.close()
    if finder.stack and any(start is not None for _, start in finder.stack):
        raise ValueError("an English element is never closed")
    out, last = [], 0
    for start, end in sorted(finder.spans):
        # Take the whole line when the element stood on a line of its own.
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        line_end = len(text) if line_end == -1 else line_end
        if not text[line_start:start].strip() and not text[end:line_end].strip():
            start, end = line_start, min(line_end + 1, len(text))
        out.append(text[last:start])
        last = end
    out.append(text[last:])
    return "".join(out)


def de_path(path):
    return "/de" + path


def build(source, path, head):
    with open(os.path.join(ROOT, source), encoding="utf-8") as f:
        text = f.read()
    text = strip_english(text)

    def sub(pattern, repl, count=1, optional=False):
        nonlocal text
        new, n = re.subn(pattern, repl, text, count=count)
        if n == 0 and not optional:
            raise ValueError(f"{source}: no match for {pattern}")
        text = new

    sub(r'<html lang="en">', '<html lang="de">')
    sub(r"<body>", '<body class="lang-de">')
    sub(r"<title>[^<]*</title>", f"<title>{head['title']}</title>")
    attr = lambda v: v.replace("&", "&amp;").replace('"', "&quot;")
    sub(r'(<meta name="description" content=")[^"]*', lambda m: m.group(1) + attr(head["description"]))
    sub(r'(<link rel="canonical" href=")[^"]*', lambda m: m.group(1) + SITE + de_path(path))
    sub(r'(<meta property="og:url" content=")[^"]*', lambda m: m.group(1) + SITE + de_path(path))
    sub(r'<meta property="og:locale" content="en_US">', '<meta property="og:locale" content="de_DE">')
    sub(r'<meta property="og:locale:alternate" content="de_DE">', '<meta property="og:locale:alternate" content="en_US">')
    for prop in ("og:title", "twitter:title"):
        sub(rf'(<meta (?:property|name)="{prop}" content=")[^"]*', lambda m: m.group(1) + attr(head["og_title"]))
    for prop in ("og:description", "twitter:description"):
        sub(rf'(<meta (?:property|name)="{prop}" content=")[^"]*', lambda m: m.group(1) + attr(head["og_description"]))
    for prop in ("og:image:alt", "twitter:image:alt"):
        sub(rf'(<meta (?:property|name)="{prop}" content=")[^"]*', lambda m: m.group(1) + attr(head["image_alt"]),
            optional=prop == "twitter:image:alt")
    sub(r"(/images/og-card-2-0(?:-[a-z]+)?)\.png", r"\1-de.png", count=0)

    # Internal page links into /de/, but not the language switch or the press kit zip.
    def link(m):
        tag = m.group(0)
        if "data-lang=" in tag:
            return tag
        return re.sub(r'href="(/(?:(?:support|press|privacy|terms|impressum)/)?(?:#[^"]*)?)"',
                      lambda h: f'href="/de{h.group(1)}"', tag)
    text = re.sub(r"<a\b[^>]*>", link, text)

    # Language switch: German is the current one here.
    sub(r'<a data-lang="en" class="active" aria-current="true" href=', '<a data-lang="en" href=')
    sub(r'<a data-lang="de" href=', '<a data-lang="de" class="active" aria-current="true" href=')

    def translate(m):
        value = m.group(2).replace("&rsquo;", "’")
        return f'{m.group(1)}="{TEXTS.get(value, m.group(2))}"'
    text = re.sub(r'\b(alt|aria-label|title)="([^"]+)"', translate, text)

    if JSON_LD_DESCRIPTION[0] in text:
        text = text.replace(JSON_LD_DESCRIPTION[0], JSON_LD_DESCRIPTION[1])
        text = text.replace(f'"url": "{SITE}/"', f'"url": "{SITE}/de/"')

    banner = f"<!-- Generated by scripts/build_german_pages.py from /{source}. Edit that file, not this one. -->\n"
    return text.replace("<!DOCTYPE html>\n", "<!DOCTYPE html>\n" + banner, 1)


def main():
    check = "--check" in sys.argv
    stale = []
    for source, (path, head) in PAGES.items():
        out = os.path.join(ROOT, "de", path.strip("/"), "index.html")
        html = build(source, path, head)
        current = open(out, encoding="utf-8").read() if os.path.exists(out) else None
        if current == html:
            continue
        stale.append(out)
        if not check:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out, "w", encoding="utf-8") as f:
                f.write(html)
    for out in stale:
        print(("stale: " if check else "wrote: ") + os.path.relpath(out, ROOT))
    if not stale:
        print("German pages are up to date.")
    return 1 if check and stale else 0


if __name__ == "__main__":
    sys.exit(main())
