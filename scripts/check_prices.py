#!/usr/bin/env python3
"""Check the prices on the website against the live App Store.

Reads the hand-kept PRICES table in js/lang.js, opens the app's App Store page
for one storefront per currency, reads the in-app purchase list Apple embeds
in the page, and compares the two.

Exits 1 (so the workflow run fails and GitHub sends its failure email) when a
price differs, or when no storefront could be read at all, since then the
check is blind. A single storefront that can't be read only logs a warning.
Changes nothing: fixing the table stays a deliberate edit.

Standard library only.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LANG_JS = os.path.join(ROOT, "js", "lang.js")
APP_URL = "https://apps.apple.com/{}/app/music-drops/id6759535792"

# Every eurozone storefront listed here must match the one EUR row.
STOREFRONTS = {"us": "USD", "de": "EUR", "fr": "EUR", "gb": "GBP", "ca": "CAD", "au": "AUD", "ch": "CHF"}
PAUSE = 2

# Product names are localised, so tell the plans apart by their words.
KINDS = {
    "monthly": re.compile(r"month|monat|mensu|mensil", re.I),
    "yearly": re.compile(r"year|jähr|jahr|annu|anual", re.I),
    "lifetime": re.compile(r"lifetime|lebens|vie|vita|vida", re.I),
}


def log(msg):
    print(msg, flush=True)


def site_prices():
    with open(LANG_JS, encoding="utf-8") as f:
        js = f.read()
    rows = re.findall(r"(\b[A-Z]{3}): \{ monthly: ([\d.]+), yearly: ([\d.]+), lifetime: ([\d.]+) \}", js)
    return {cur: {"monthly": float(m), "yearly": float(y), "lifetime": float(l)} for cur, m, y, l in rows}


def amount(text):
    match = re.search(r"\d[\d.,  ]*", text)
    if not match:
        return None
    number = re.sub(r"[\s ]", "", match.group()).rstrip(".,")
    if re.search(r"[.,]\d{2}$", number):
        whole, cents = number[:-3], number[-2:]
        return float(re.sub(r"[.,]", "", whole) + "." + cents)
    return float(re.sub(r"[.,]", "", number))


def store_prices(country):
    req = urllib.request.Request(APP_URL.format(country), headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        page = resp.read().decode("utf-8", "replace")
    pairs = re.findall(r'\{"\$kind":"textPair","leadingText":("(?:[^"\\]|\\.)*"),"trailingText":("(?:[^"\\]|\\.)*")\}', page)
    found = {}
    for name, price in pairs:
        name, price = json.loads(name), json.loads(price)
        for kind, pattern in KINDS.items():
            if pattern.search(name) and kind not in found:
                found[kind] = (name, price, amount(price))
    return found


def main():
    expected = site_prices()
    if not expected:
        log("::error::Couldn't read the PRICES table in js/lang.js.")
        return 1

    mismatches, read = [], 0
    for country, currency in STOREFRONTS.items():
        want = expected.get(currency)
        try:
            found = store_prices(country)
        except (urllib.error.URLError, TimeoutError) as err:
            log(f"::warning::{country}: App Store page couldn't be loaded ({err}).")
            continue
        finally:
            time.sleep(PAUSE)
        if len(found) < 3:
            log(f"::warning::{country}: found {len(found)} of 3 prices on the App Store page; its format may have changed.")
            continue
        read += 1
        for kind, (name, text, live) in found.items():
            site = want.get(kind) if want else None
            ok = site is not None and live is not None and abs(site - live) < 0.005
            log(f"  {country} {kind:8} store {text:>10}   site {site if site is not None else '-'}{'' if ok else '   <- differs'}")
            if not ok:
                mismatches.append(f"{country} {kind}: App Store {text}, website {currency} {site}")

    if not read:
        log("::error::No App Store page could be read, so the prices weren't checked.")
        return 1
    if mismatches:
        for m in mismatches:
            log(f"::error::{m}")
        log("Update the PRICES table in js/lang.js (and bump its ?v= on every page).")
        return 1
    log("All website prices match the App Store.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
