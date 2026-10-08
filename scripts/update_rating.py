#!/usr/bin/env python3
"""Refresh the homepage App Store rating line.

Looks the app up in the public iTunes lookup for each storefront below, pools
the ratings into one average, and rewrites the block in index.html between
<!-- rating:start --> and <!-- rating:end -->. The same numbers go into the
aggregateRating of the page's structured data (<script id="app-ld">), which
search engines only accept while the rating is also visible on the page.

The line only appears once there are MIN_RATINGS ratings, and only names the
count from SHOW_COUNT on, so an early handful of ratings never reads as thin.
Below the minimum the block is emptied and the page shows nothing.

Standard library only. Exits 0 without touching anything when index.html has
no markers, or when too many lookups fail to trust the total.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "index.html")

APP_ID = 6759535792
# Where people are likely to rate it: the app's six languages plus the larger
# English-speaking stores. Ratings from storefronts not listed here are missed.
STOREFRONTS = [
    "us", "gb", "ca", "au", "ie", "nz", "in", "sg",
    "de", "at", "ch", "nl", "be", "lu", "dk", "se", "no", "fi", "pl",
    "fr", "it", "es", "pt", "mx", "ar", "br", "cl", "co",
    "jp",
]
PAUSE = 3.2  # seconds between lookups; Apple allows roughly 20 calls a minute

MIN_RATINGS = 10
SHOW_COUNT = 100


def log(msg):
    print(msg, flush=True)


def lookup(country):
    url = "https://itunes.apple.com/lookup?" + urllib.parse.urlencode({"id": APP_ID, "country": country})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                results = json.load(resp).get("results", [])
            if not results:
                return 0.0, 0
            r = results[0]
            return float(r.get("averageUserRating") or 0), int(r.get("userRatingCount") or 0)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError) as err:
            log(f"  lookup {country} failed ({err}), retry {attempt + 1}")
            time.sleep(PAUSE * (attempt + 2))
    return None


def render(average, count):
    if count < MIN_RATINGS:
        return ""
    en, de = f"{average:.1f}", f"{average:.1f}".replace(".", ",")
    count_en = count_de = ""
    if count >= SHOW_COUNT:
        count_en = f" &middot; {count:,} ratings"
        count_de = f" &middot; {count:,} Bewertungen".replace(",", ".")
    return (
        '<p class="rating"><span class="rating__star" aria-hidden="true">&#9733;</span> '
        f'<span lang="en"><b>{en}</b> out of 5 on the App Store{count_en}</span>'
        f'<span lang="de"><b>{de}</b> von 5 im App Store{count_de}</span></p>'
    )


LD = re.compile(r'(<script type="application/ld\+json" id="app-ld">\n)(.*?)(\n *</script>)', re.S)


def with_structured_rating(page, average, count):
    match = LD.search(page)
    if not match:
        return page
    data = json.loads(match.group(2))
    data.pop("aggregateRating", None)
    if count >= MIN_RATINGS:
        data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": f"{average:.1f}",
            "ratingCount": str(count),
            "bestRating": "5",
        }
    body = json.dumps(data, indent=2, ensure_ascii=False)
    return page[: match.start(2)] + body + page[match.end(2):]


def main():
    with open(PAGE, encoding="utf-8") as f:
        page = f.read()
    pattern = re.compile(r"(<!-- rating:start -->\n)(.*?)(^ *<!-- rating:end -->)", re.S | re.M)
    match = pattern.search(page)
    if not match:
        log("index.html has no rating markers; nothing to do.")
        return 0
    indent = re.search(r"( *)<!-- rating:start -->", page).group(1)

    total, weighted, failures = 0, 0.0, 0
    for country in STOREFRONTS:
        result = lookup(country)
        if result is None:
            failures += 1
        else:
            average, count = result
            if count:
                log(f"  {country}: {average:.2f} from {count}")
            total += count
            weighted += average * count
        time.sleep(PAUSE)
    if failures > len(STOREFRONTS) // 4:
        log(f"{failures} lookups failed; keeping the current rating line.")
        return 0

    average = weighted / total if total else 0.0
    log(f"Pooled: {average:.2f} from {total} ratings")

    html = render(average, total)
    block = f"{indent}{html}\n" if html else ""
    updated = page[: match.start(2)] + block + page[match.end(2):]
    updated = with_structured_rating(updated, average, total)
    if updated == page:
        log("No change.")
        return 0
    with open(PAGE, "w", encoding="utf-8") as f:
        f.write(updated)
    log("Rating line updated." if html else f"Fewer than {MIN_RATINGS} ratings; rating line hidden.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
