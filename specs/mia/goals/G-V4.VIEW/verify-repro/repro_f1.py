"""Reviewer repro (not a product test): ArrowDown in the graph list, real Firefox; also F-3 theme switch after a drag."""
import json, sys
sys.path.insert(0, sys.argv[1] + "/tests/helpers"); sys.path.insert(0, sys.argv[1] + "/tests"); sys.path.insert(0, sys.argv[1])
import graph_view_server
from playwright.sync_api import sync_playwright
srv = graph_view_server.start()
try:
    with sync_playwright() as p:
        b = p.firefox.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, color_scheme="light")
        ctx.request.post(srv.url + "/api/login", data=json.dumps({"user": "anna", "password": "pw-anna"}),
                         headers={"Content-Type": "application/json", "Origin": srv.origin})
        page = ctx.new_page(); errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(srv.url + "/graph/"); page.wait_for_selector("[data-graph-id]")
        first = page.locator("[data-graph-id]").first
        first.focus(); before = page.evaluate("document.activeElement.dataset.graphId")
        page.keyboard.press("ArrowDown"); after = page.evaluate("document.activeElement.dataset.graphId")
        print("F-1 focus before/after ArrowDown:", before, after, "page errors:", errors)
        b.close()
finally:
    srv.stop()
