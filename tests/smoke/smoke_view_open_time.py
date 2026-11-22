"""
Smoke measurement SMOKE-VIEW-002 of G-V4.VIEW (NFR-11, measured, no bound, D-425 E-H; TR-VIEW-008, 009, 010, 017): how long opening a graph of
about fifty steps takes.

On the owner's host (Deploy), from the installed release folder: the release's graph app and API (tests/helpers/graph_view_server.py) on a
throw-away file store holding only `chain.fifty` (50 steps, 49 connections, TR-VIEW-002), in Playwright's Firefox (headless, 1280 x 800). One
warm-up opening is not counted; then five openings, the page reloaded between them, each timed from the click in the list until the picture
has settled (window.graphViewTest.settled, TR-VIEW-010). Prints the five times, the median and the smallest and largest in milliseconds as one
JSON line for the deployment record; nothing is judged. MIA's live store is not read or written.
Protected: change only through a plan amendment. Run:
  python tests/smoke/smoke_view_open_time.py        (exit 0 = measured, 2 = cannot run)
"""
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "helpers"))

import graph_view_server  # noqa: E402

GRAPH = "chain.fifty"
RUNS = 5


def main():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("cannot run: Playwright for Python is not installed (requirements-browser.txt)")
        return 2
    try:
        server = graph_view_server.start(ids={GRAPH})
    except RuntimeError as err:
        print("cannot run: %s" % err)
        return 2
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            context = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1, locale="en-US")
            context.request.post(server.url + "/api/login", data=json.dumps({"user": "anna", "password": "pw-anna"}),
                                 headers={"Content-Type": "application/json", "Origin": server.origin})
            page = context.new_page()
            times = []
            for run in range(RUNS + 1):
                page.goto(server.url + "/graph/")
                page.wait_for_selector('[data-graph-id="%s"]' % GRAPH, timeout=10000)
                start = time.perf_counter()
                page.click('[data-graph-id="%s"]' % GRAPH)
                page.wait_for_function("() => window.graphViewTest && window.graphViewTest.settled === true", timeout=10000)
                if run:                                          # run 0 is the warm-up
                    times.append(round((time.perf_counter() - start) * 1000))
            version = browser.version
            browser.close()
    finally:
        server.stop()
    print(json.dumps({"check": "SMOKE-VIEW-002", "graph": GRAPH, "browser": "firefox " + version, "times_ms": times,
                      "median_ms": statistics.median(times), "min_ms": min(times), "max_ms": max(times)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
