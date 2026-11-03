"""Time a study page in headless Chromium and list slow or failed page files.

Needs Playwright with Chromium (installed in the dsagent environment).
Usage: python tools/browser_first_screen.py <url> [text marking the first screen]
Example: python tools/browser_first_screen.py "https://study1.aitheoryelaboration.org/?embed=true"
"""
import sys
import time

from playwright.sync_api import sync_playwright

url = sys.argv[1]
marker = sys.argv[2] if len(sys.argv) > 2 else "Welcome to the study task"
events = []
with sync_playwright() as playwright:
    browser = playwright.chromium.launch()
    page = browser.new_page()
    started = time.monotonic()
    starts = {}
    page.on("request", lambda r: starts.__setitem__(r, time.monotonic()))
    page.on("requestfinished", lambda r: events.append(
        ("ok", time.monotonic() - starts.get(r, started), r.url)))
    page.on("requestfailed", lambda r: events.append(
        ("FAIL", time.monotonic() - starts.get(r, started), r.url)))
    page.goto(url, wait_until="commit", timeout=120_000)
    try:
        page.get_by_text(marker).first.wait_for(timeout=120_000)
        print(f"first screen visible after {time.monotonic() - started:.1f}s")
    except Exception:  # noqa: BLE001 - report the timeout instead of a traceback.
        print(f"first screen NOT visible after {time.monotonic() - started:.1f}s")
    browser.close()

failed = sum(e[0] == "FAIL" for e in events)
slow = sorted((e for e in events if e[0] == "FAIL" or e[1] > 3), key=lambda e: -e[1])
print(f"{len(events)} requests, {failed} failed, {sum(e[1] > 3 for e in events)} slower than 3s")
for status, seconds, request_url in slow[:12]:
    print(f"  {status:4} {seconds:5.1f}s {request_url[-90:]}")
