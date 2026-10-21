#!/usr/bin/env python3
"""
Fetch Google Maps search results (tbm=map) with browser cookies, save the raw
response, and parse it with gmaps_parser.

Setup
    Run save_cookies.py once (manual Google login) to create cookies.json.
    Fallbacks: cookies.txt / GMAPS_COOKIE (raw Cookie header), then the embedded COOKIES.

Run
    python software_houses_scraper.py "software house in italy" -o results
    -> results.raw.txt, results.json, results.csv
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import time
from urllib.parse import quote

import requests
from requests.cookies import RequestsCookieJar

from gmaps_parser import parse_response, to_csv

# pb blob captured from the browser. Viewport (!1d/!2d/!3d, !4f zoom) biases which
# results come back; session tokens (!1sMGnX..., psi=) are tied to the capture.
PB = (
    "!4m9!1m3!1d2703194.9309417773!2d5.875992!3d42.9293767!2m0!3m2!1i1920!2i347!4f13.1"
    "!7i20!10b1!12m25!1m5!18b1!30b1!31m1!1b1!34e1!2m4!5m1!6e2!20e3!39b1!10b1!12b1!13b1"
    "!16b1!17m1!3e1!20m3!5e2!6b1!14b1!46m1!1b0!96b1!99b1!19m4!2m3!1i360!2i120!4i8"
    "!20m65!2m2!1i203!2i100!3m2!2i4!5b1!6m6!1m2!1i86!2i86!1m2!1i408!2i240"
    "!7m33!1m3!1e1!2b0!3e3!1m3!1e2!2b1!3e2!1m3!1e2!2b0!3e3!1m3!1e8!2b0!3e3!1m3!1e10"
    "!2b0!3e3!1m3!1e10!2b1!3e2!1m3!1e10!2b0!3e4!1m3!1e9!2b1!3e2!2b1!9b0"
    "!15m16!1m7!1m2!1m1!1e2!2m2!1i195!2i195!3i20!1m7!1m2!1m1!1e2!2m2!1i195!2i195!3i20"
    "!22m6!1sMGnXaryvA-6o9u8PgonUuA0%3A5!2s1i%3A0%2Ct%3A11886%2Cp%3AMGnXaryvA-6o9u8PgonUuA0%3A5"
    "!7e81!12e5!17sMGnXaryvA-6o9u8PgonUuA0%3A105!18e15"
    "!24m109!1m27!13m9!2b1!3b1!4b1!6i1!8b1!9b1!14b1!20b1!25b1"
    "!18m16!3b1!4b1!5b1!6b1!9b1!13b1!14b1!17b1!20b1!21b1!22b1!32b1!33m1!1b1!34b1!36e2"
    "!10m1!8e3!11m1!3e1!17b1!20m2!1e3!1e6!24b1!25b1!26b1!27b1!29b1!30m1!2b1!36b1!37b1"
    "!39m3!2m2!2i1!3i1!43b1!52b1!54m1!1b1!55b1!56m1!1b1!61m2!1m1!1e1!65m5!3m4!1m3!1m2!1i224!2i298"
    "!72m22!1m8!2b1!5b1!7b1!12m4!1b1!2b1!4m1!1e1!4b1!8m10!1m6!4m1!1e1!4m1!1e3!4m1!1e4"
    "!3sother_user_google_review_posts__and__hotel_and_vr_partner_review_posts!6m1!1e1"
    "!9b1!89b1!90m2!1m1!1e2!98m3!1b1!2b1!3b1!103b1!113b1!114m3!1b1!2m1!1b1!117b1!122m1!1b1"
    "!126b1!127b1!128m1!1b1!26m4!2m3!1i80!2i92!4i8"
    "!30m28!1m6!1m2!1i0!2i0!2m2!1i530!2i347!1m6!1m2!1i1870!2i0!2m2!1i1920!2i347"
    "!1m6!1m2!1i0!2i0!2m2!1i1920!2i20!1m6!1m2!1i0!2i327!2m2!1i1920!2i347"
    "!34m19!2b1!3b1!4b1!6b1!8m6!1b1!3b1!4b1!5b1!6b1!7b1!9b1!12b1!14b1!20b1!23b1!25b1!26b1!31b1"
    "!37m1!1e81!42b1!47m0!49m10!3b1!6m2!1b1!2b1!7m2!1e3!2b1!8b1!9b1!10e2!50m4!2e2!3m2!1b1!3b1"
    "!67m5!7b1!10b1!14b1!15m1!1b0!69i800!77b1"
)
TAIL = (
    "&gs_l=maps.3..38i426k1l5.0.0.1.25248.1.1.....266.266.2-1.1.....0......maps..0.1.297.0."
    "&tch=1&ech=1&psi=MGnXaryvA-6o9u8PgonUuA0.1792502066525.1"
)

HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "referer": "https://www.google.com/",
    "sec-ch-ua": '"Chromium";v="155", "Not(A:Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"
    ),
    "x-maps-diversion-context-bin": "CAE=",
    "available-dictionary": ":C89JSfwkSkU8m0RwFq48/1EoFrWEc1JrP8Y0zTwYk4k=:",
    "downlink": "10",
    "rtt": "100",
    "priority": "u=1, i",
}

# Session cookies captured from the browser. Do not commit this file.

COOKIES = {}

def load_cookies(path: str = "cookies.json"):
    """Order: cookies.json (from save_cookies.py) -> GMAPS_COOKIE / cookies.txt -> {}."""
    if path.endswith(".json") and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        items = data["cookies"] if isinstance(data, dict) else data
        jar = RequestsCookieJar()
        for c in items:
            dom = c.get("domain", "")
            if dom.lstrip(".").endswith("google.com"):
                jar.set(c["name"], c["value"], domain=dom, path=c.get("path", "/"))
        if len(jar):
            return jar

    raw = os.environ.get("GMAPS_COOKIE", "")
    if not raw and os.path.exists("cookies.txt"):
        raw = open("cookies.txt", encoding="utf-8").read()
    raw = raw.strip()
    if raw.lower().startswith("cookie:"):
        raw = raw[7:].strip()
    cookies = {}
    for part in raw.split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            cookies[k.strip()] = v.strip()
    return cookies


def geocode(location: str) -> tuple[float, float] | None:
    """City -> (lat, lng) via OpenStreetMap Nominatim. Used only with --recenter."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": location, "format": "json", "limit": 1},
            headers={"user-agent": "gmaps-scraper-practice/1.0"},
            timeout=20,
        )
        data = r.json()
        if data:
            return float(data[0]["lat"]), float(data[0]["lon"])
    except (requests.RequestException, ValueError, KeyError):
        pass
    return None


def build_url(query: str, offset: int = 0, center: tuple[float, float] | None = None) -> str:
    pb = PB
    if center:
        # Re-centre the viewport (camera distance in metres, lng, lat). Best effort.
        lat, lng = center
        pb = pb.replace(
            "!1d2703194.9309417773!2d5.875992!3d42.9293767", f"!1d50000!2d{lng}!3d{lat}", 1
        )
    if offset:
        # UNVERIFIED: page offset param; compare with a "next page" capture from devtools.
        pb = pb.replace("!7i20", f"!7i20!8i{offset}", 1)
    q = quote(query)
    return f"https://www.google.com/search?tbm=map&authuser=0&hl=en&pb={pb}&q={q}&oq={q}{TAIL}"


def fetch(query: str, cookies: dict[str, str], offset: int = 0,
          center: tuple[float, float] | None = None, retries: int = 3) -> str:
    url = build_url(query, offset, center)
    last = None
    for attempt in range(1, retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, cookies=cookies, timeout=30)
            if r.status_code == 200 and r.text.lstrip().startswith(("{", ")]}'")):
                return r.text
            last = f"HTTP {r.status_code}, body starts: {r.text[:120]!r}"
        except requests.RequestException as e:
            last = repr(e)
        time.sleep(2 * attempt)
    raise RuntimeError(f"request failed after {retries} tries: {last}")


def save(results: list[dict], base: str) -> None:
    with open(f"{base}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    to_csv(results, f"{base}.csv")


PAGE_SIZE = 20


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--location", help="city / country, e.g. Islamabad")
    ap.add_argument("--count", type=int, help="how many software houses")
    ap.add_argument("--recenter", action="store_true",
                    help="geocode the location and centre the map viewport on it")
    ap.add_argument("--cookies", default="cookies.json")
    args = ap.parse_args()

    location = args.location or input("City / country: ").strip()
    while not location:
        location = input("City / country: ").strip()
    count = args.count
    while not count or count < 1:
        try:
            count = int(input("How many software houses: ").strip())
        except ValueError:
            count = None

    # cookies.json (save_cookies.py) > cookies.txt / GMAPS_COOKIE > embedded COOKIES
    cookies = load_cookies(args.cookies) or COOKIES

    center = geocode(location) if args.recenter else None
    if args.recenter:
        print(f"recentre on {center}" if center else "geocoding failed, using default viewport")

    query = f"software house in {location}"
    slug = re.sub(r"\W+", "_", location.lower()).strip("_")
    base = f"{slug}_software_houses"
    raw_dir = f"{slug}_raw"
    os.makedirs(raw_dir, exist_ok=True)

    results: list[dict] = []
    seen: set[str] = set()
    offset, page = 0, 1
    while len(results) < count:
        try:
            text = fetch(query, cookies, offset, center)
        except RuntimeError as e:
            print(f"stopping: {e}")
            break
        with open(f"{raw_dir}/page_{page}.txt", "w", encoding="utf-8") as f:
            f.write(text)

        places = parse_response(text)
        new = [p for p in places if p.get("feature_id") not in seen]
        seen.update(p.get("feature_id") for p in new)
        results.extend(new)
        print(f"page {page} (offset {offset}): {len(places)} returned, "
              f"{len(new)} new, total {len(results)}/{count}")
        save(results[:count], base)  # incremental save

        if not new:
            print("no new results: end of results, or the offset param isn't accepted")
            break
        offset += PAGE_SIZE
        page += 1
        time.sleep(random.uniform(2, 4))

    results = results[:count]
    save(results, base)
    print(f"{len(results)} places -> {base}.json / {base}.csv")


if __name__ == "__main__":
    main()