#!/usr/bin/env python3
"""
Open Google Maps in a visible browser, let you log in manually, then save the
Google cookies to cookies.json. software_houses_scraper.py picks that file up automatically.

Setup
    pip install playwright
    playwright install chromium        # only needed if Google Chrome isn't installed

Run
    python save_cookies.py             # launches Chrome (falls back to Chromium)
    python save_cookies.py --cdp http://localhost:9222
        # attach to your normal Chrome instead, started with:
        #   google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-gmaps
        # use this if Google says "This browser or app may not be secure".

The login is kept in ./chrome_profile (launch mode), so later runs are usually
already logged in: just press Enter.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from playwright.sync_api import sync_playwright

PROFILE_DIR = "chrome_profile"
OUT = "cookies.json"
AUTH_COOKIES = {"SID", "__Secure-1PSID", "__Secure-3PSID"}


def launch(pw):
    kwargs = dict(
        user_data_dir=PROFILE_DIR,
        headless=False,
        viewport=None,
        args=["--disable-blink-features=AutomationControlled"],
        ignore_default_args=["--enable-automation"],
    )
    try:
        return pw.chromium.launch_persistent_context(channel="chrome", **kwargs)
    except Exception as e:
        print(f"Chrome channel unavailable ({e.__class__.__name__}); using bundled Chromium")
        return pw.chromium.launch_persistent_context(**kwargs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cdp", help="attach to a running Chrome, e.g. http://localhost:9222")
    ap.add_argument("-o", "--out", default=OUT)
    args = ap.parse_args()

    with sync_playwright() as pw:
        if args.cdp:
            browser = pw.chromium.connect_over_cdp(args.cdp)
            ctx = browser.contexts[0]
        else:
            ctx = launch(pw)

        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://www.google.com/maps", wait_until="domcontentloaded")

        print("\nLog in to your Google account in the browser window.")
        input("When signed in, press Enter here (keep the browser window OPEN)... ")

        # Run one search so the maps-specific cookies get set before we dump them.
        # Best effort: Google's login flow can replace/close tabs, so use a live one.
        try:
            live = next((pg for pg in reversed(ctx.pages) if not pg.is_closed()), None)
            page = live or ctx.new_page()
            page.goto("https://www.google.com/maps/search/software+house", wait_until="domcontentloaded")
            page.wait_for_timeout(4000)
        except Exception as e:
            print(f"skipped warm-up search ({e.__class__.__name__})")

        try:
            cookies = [c for c in ctx.cookies() if c["domain"].lstrip(".").endswith("google.com")]
        except Exception:
            print("The browser was closed before cookies could be read. Re-run, keep the window "
                  "open, and press Enter (your login is kept in ./chrome_profile).")
            sys.exit(1)
        names = {c["name"] for c in cookies}

        if not (names & AUTH_COOKIES):
            print("No Google login cookies found (SID / __Secure-*PSID). Not saving. Log in and retry.")
            ctx.close() if not args.cdp else None
            sys.exit(1)

        with open(args.out, "w", encoding="utf-8") as f:
            json.dump({"cookies": cookies}, f, indent=2)
        try:
            os.chmod(args.out, 0o600)
        except OSError:
            pass
        print(f"Saved {len(cookies)} cookies -> {args.out}")

        if not args.cdp:
            ctx.close()


if __name__ == "__main__":
    main()