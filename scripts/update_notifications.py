#!/usr/bin/env python3
"""Refresh the homepage notification mockups with real, recent releases.

Reads the artist list in data/notif-artists.json, looks each artist up in the
public iTunes lookup (one artist per call: batched lookups drop results), and
rewrites the three notification blocks in index.html between their markers:

  <!-- notif:just:start -->     a release from the last few days ("Just dropped")
  <!-- notif:upcoming:start --> a pre-order with a date ahead ("Coming Oct 17")
  <!-- notif:recap:start -->    last week's count ("31 drops from 30 artists")

Artwork is saved to images/notif-art/live/ and files no longer used are removed.
Relative wording ("now", "tomorrow") is applied in the browser by js/lang.js
from each block's data-date, so the HTML only changes when the picks change.

Standard library only. Exits 0 without touching anything when index.html has
no markers, or when the lookup fails badly enough that there is nothing to show.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTISTS = os.path.join(ROOT, "data", "notif-artists.json")
PAGE = os.path.join(ROOT, "index.html")
ART_DIR = os.path.join(ROOT, "images", "notif-art", "live")
ART_URL = "/images/notif-art/live"

COUNTRY = "us"
PAUSE = 3.2  # seconds between lookups; Apple allows roughly 20 calls a minute

JUST_DAYS, JUST_DAYS_WIDE = 3, 10
SOON_DAYS, SOON_DAYS_WIDE = 14, 60

# Re-releases and alternate takes make poor examples of a "drop".
SKIP_TITLE = re.compile(
    r"\b(remix(es)?|mixes|rmx|mix\)|version|ver\.|live|acoustic|a ?cappella|instrumental|karaoke|"
    r"video|commentary|edition|anniversary|sped up|slowed|demo|chamber|interview|dj mix)\b",
    re.I,
)

# Apple marks a whole record explicit when any track is, which would rule out
# most of the list. Only the title is shown, so screen the title instead.
ROUGH_TITLE = re.compile(
    r"fuck|shit|bitch|n[i1]gg|pussy|\bdick|\bcock|cunt|\bwhore|\bhoes?\b|\bslut|\bsex|\bdrugs?\b|\bkill",
    re.I,
)

MONTHS = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "de": ["Jan.", "Feb.", "März", "Apr.", "Mai", "Juni", "Juli", "Aug.", "Sept.", "Okt.", "Nov.", "Dez."],
}


def log(msg):
    print(msg, flush=True)


def lookup(artist_id):
    query = urllib.parse.urlencode(
        {"id": artist_id, "entity": "album", "sort": "recent", "limit": 50, "country": COUNTRY}
    )
    url = "https://itunes.apple.com/lookup?" + query
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.load(resp).get("results", [])
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as err:
            log(f"  lookup {artist_id} failed ({err}), retry {attempt + 1}")
            time.sleep(PAUSE * (attempt + 2))
    return None


def clean_title(name):
    return re.sub(r"\s+-\s+(Single|EP)$", "", name).strip()


def releases_for(artist, rows):
    """The artist's own original releases, including ones they're credited on,
    and every release credited to them (for the recap count, which like the
    app's counts versions and remixes too)."""
    out, seen, every = [], set(), {}
    for r in rows:
        if r.get("wrapperType") != "collection":
            continue
        credited = r.get("artistName", "")
        if r.get("artistId") != artist["id"] and artist["name"].casefold() not in credited.casefold():
            continue
        name = r.get("collectionName", "")
        try:
            day = date.fromisoformat(r["releaseDate"][:10])
        except (KeyError, ValueError):
            continue
        if name:
            every[(clean_title(name).casefold(), day)] = {"artist": r.get("artistName") or artist["name"], "date": day}
        if not name or SKIP_TITLE.search(name) or ROUGH_TITLE.search(name):
            continue
        title = clean_title(name)
        key = (title.casefold(), day)
        if key in seen:
            continue
        seen.add(key)
        art = (r.get("artworkUrl100") or "").replace("100x100bb", "200x200bb")
        if not art:
            continue
        out.append({
            "id": r["collectionId"],
            "title": title,
            "artist": r.get("artistName") or artist["name"],
            "date": day,
            "art": art,
            "rank": artist["rank"],
        })
    return out, list(every.values())


def pick(candidates, used_artists, key):
    for c in sorted(candidates, key=key):
        if c["artist"] not in used_artists:
            used_artists.add(c["artist"])
            return c
    return None


def month_day(day, lang):
    if lang == "de":
        return f"{day.day}. {MONTHS['de'][day.month - 1]}"
    return f"{MONTHS['en'][day.month - 1]} {day.day}"


def plural(n, one, many):
    return f"{n} {one if n == 1 else many}"


ICON = '<img class="notif__icon" src="/images/app-icon.png" alt="">'


def block(slot, release, title_en, title_de, time_en, time_de, sub_en, sub_de, date_attr=""):
    art = f'{ART_URL}/{release["id"]}.jpg'
    data_date = f' data-date="{date_attr}"' if date_attr else ""
    return (
        f'<div class="notif" data-notif="{slot}"{data_date} aria-hidden="true">\n'
        f"              {ICON}\n"
        f"              <div>\n"
        f'                <span class="notif__app"><span>MUSICDROPS</span><span class="notif__time">'
        f'<span lang="en">{time_en}</span><span lang="de">{time_de}</span></span></span>\n'
        f'                <span class="notif__title"><span lang="en">{title_en}</span><span lang="de">{title_de}</span></span>\n'
        f'                <span class="notif__sub"><span lang="en">{sub_en}</span><span lang="de">{sub_de}</span></span>\n'
        f"              </div>\n"
        f'              <img class="notif__art" src="{art}" alt="">\n'
        f"            </div>"
    )


def render(slot, release, extra=None):
    t, a = escape(release["title"]), escape(release["artist"])
    if slot == "just":
        return block(slot, release, "Just dropped", "Gerade erschienen", "now", "jetzt",
                     f"{t} by {a}", f"{t} von {a}", release["date"].isoformat())
    if slot == "upcoming":
        d = release["date"]
        return block(slot, release, f"Coming {month_day(d, 'en')}", f"Erscheint am {month_day(d, 'de')}",
                     "9:00", "9:00", f"{t} by {a}", f"{t} von {a}", d.isoformat())
    drops, artists = extra
    return block(slot, release, "Your week in drops is ready", "Dein Wochenr&uuml;ckblick ist da", "Sun", "So.",
                 f"{plural(drops, 'drop', 'drops')} from {plural(artists, 'artist', 'artists')}",
                 f"{plural(drops, 'Drop', 'Drops')} von {plural(artists, 'K&uuml;nstler', 'K&uuml;nstlern')}")


def replace_block(page, slot, html):
    pattern = re.compile(
        rf"(<!-- notif:{slot}:start -->\s*).*?(\s*<!-- notif:{slot}:end -->)", re.S
    )
    if not pattern.search(page):
        return page, False
    return pattern.sub(lambda m: m.group(1) + html + m.group(2), page, count=1), True


def download(url, path):
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = resp.read()
    if len(data) < 1000:
        raise ValueError("artwork too small")
    with open(path, "wb") as f:
        f.write(data)


def main():
    with open(PAGE, encoding="utf-8") as f:
        page = f.read()
    if "<!-- notif:just:start -->" not in page:
        log("index.html has no notification markers; nothing to do.")
        return 0

    with open(ARTISTS, encoding="utf-8") as f:
        groups = json.load(f)["groups"]
    artists = [dict(a, rank=i) for i, a in enumerate(a for g in groups for a in g["artists"])]

    today = datetime.now(timezone.utc).date()
    log(f"Looking up {len(artists)} artists for {today}")

    releases, everything, failures = [], {}, 0
    for artist in artists:
        rows = lookup(artist["id"])
        if rows is None:
            failures += 1
        else:
            picks_for, every = releases_for(artist, rows)
            releases.extend(picks_for)
            for e in every:
                everything[(e["artist"].casefold(), e["date"])] = everything.get((e["artist"].casefold(), e["date"]), 0) + 1
        time.sleep(PAUSE)
    if failures > len(artists) // 3:
        log(f"{failures} lookups failed; keeping the current notifications.")
        return 0

    def within(lo, hi):
        return [r for r in releases if lo <= (r["date"] - today).days <= hi]

    used = set()
    by_recent = lambda r: (-r["date"].toordinal(), r["rank"])
    by_soonest = lambda r: (r["date"].toordinal(), r["rank"])
    just = pick(within(-JUST_DAYS, 0), used, by_recent) or pick(within(-JUST_DAYS_WIDE, 0), used, by_recent)
    upcoming = pick(within(1, SOON_DAYS), used, by_soonest) or pick(within(1, SOON_DAYS_WIDE), used, by_soonest)

    last_week = within(-7, -1)
    recap_art = pick(last_week, used, lambda r: r["rank"]) or pick(within(-30, -1), used, lambda r: r["rank"])
    week = {k: n for k, n in everything.items() if -7 <= (k[1] - today).days <= -1}
    week_counts = (sum(week.values()), len({k[0] for k in week}))

    picks = {"just": just, "upcoming": upcoming, "recap": recap_art}
    for slot, r in picks.items():
        log(f"{slot:9} {r['date'] if r else '-'}  {r['artist'] + ' · ' + r['title'] if r else 'nothing found, keeping current'}")
    log(f"recap     {week_counts[0]} drops from {week_counts[1]} artists last week")

    os.makedirs(ART_DIR, exist_ok=True)
    changed = False
    for slot, r in picks.items():
        if not r:
            continue
        path = os.path.join(ART_DIR, f"{r['id']}.jpg")
        try:
            if not os.path.exists(path):
                download(r["art"], path)
        except (urllib.error.URLError, TimeoutError, ValueError) as err:
            log(f"  artwork for {slot} failed ({err}); keeping current {slot}")
            continue
        html = render(slot, r, week_counts if slot == "recap" else None)
        page, found = replace_block(page, slot, html)
        changed |= found

    if changed:
        with open(PAGE, "w", encoding="utf-8") as f:
            f.write(page)

    # Drop artwork nothing points at any more.
    in_use = set(re.findall(r"/images/notif-art/live/(\d+)\.jpg", page))
    for name in os.listdir(ART_DIR):
        if name.endswith(".jpg") and name[:-4] not in in_use:
            os.remove(os.path.join(ART_DIR, name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
