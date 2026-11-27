"""Reviewer variant for V-9: cookies kept, only the localStorage getter throws SecurityError (as with site data blocked). Arg: checkout root."""
import json, sys
sys.path.insert(0, sys.argv[1] + "/tests/helpers"); sys.path.insert(0, sys.argv[1] + "/tests"); sys.path.insert(0, sys.argv[1])
import graph_view_server
from playwright.sync_api import sync_playwright
BLOCK = """Object.defineProperty(window, 'localStorage', { configurable: true,
  get() { throw new DOMException('The operation is insecure.', 'SecurityError'); } });"""
srv = graph_view_server.start()
try:
    with sync_playwright() as p:
        b = p.firefox.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 800})
        ctx.add_init_script(BLOCK)
        ctx.request.post(srv.url + "/api/login", data=json.dumps({"user": "anna", "password": "pw-anna"}),
                         headers={"Content-Type": "application/json", "Origin": srv.origin})
        page = ctx.new_page(); errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(srv.url + "/graph/"); page.wait_for_timeout(2000)
        print("storage probe:", page.evaluate("(() => { try { return String(window.localStorage) } catch (e) { return 'throws: ' + e.name } })()"))
        print("areas:", page.locator("[data-area]").count(), "entries:", page.locator("[data-graph-id]").count(), "errors:", errors)
        if page.locator("[data-graph-id]").count():
            page.locator("[data-graph-id]").first.click(); page.wait_for_timeout(1500)
            print("after open: canvas hidden:", page.locator("canvas").count() == 0, "errors:", errors)
        b.close()
finally:
    srv.stop()
