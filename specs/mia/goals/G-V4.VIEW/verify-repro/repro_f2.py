"""Reviewer repro: Firefox with site storage blocked (cookieBehavior 2); does the page start? Login cookie set by hand via context API."""
import json, sys
sys.path.insert(0, sys.argv[1] + "/tests/helpers"); sys.path.insert(0, sys.argv[1] + "/tests"); sys.path.insert(0, sys.argv[1])
import graph_view_server
from playwright.sync_api import sync_playwright
srv = graph_view_server.start()
try:
    with sync_playwright() as p:
        b = p.firefox.launch(headless=True, firefox_user_prefs={"network.cookie.cookieBehavior": 2})
        ctx = b.new_context(viewport={"width": 1280, "height": 800})
        ctx.request.post(srv.url + "/api/login", data=json.dumps({"user": "anna", "password": "pw-anna"}),
                         headers={"Content-Type": "application/json", "Origin": srv.origin})
        page = ctx.new_page(); errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(srv.url + "/graph/"); page.wait_for_timeout(2000)
        print("storage probe:", page.evaluate("(() => { try { return String(window.localStorage) } catch (e) { return 'throws: ' + e.name } })()"))
        print("areas:", page.locator("[data-area]").count(), "entries:", page.locator("[data-graph-id]").count(), "errors:", errors)
        b.close()
finally:
    srv.stop()
