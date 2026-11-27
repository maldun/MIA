"""Reviewer repro: drag step.check 100 px, then the system colour scheme turns dark; does the step stay?"""
import json, sys
sys.path.insert(0, sys.argv[1] + "/tests/helpers"); sys.path.insert(0, sys.argv[1] + "/tests"); sys.path.insert(0, sys.argv[1])
import graph_view_server
from playwright.sync_api import sync_playwright
srv = graph_view_server.start()
H = lambda page, c: page.evaluate("() => window.graphViewTest.%s" % c)
try:
    with sync_playwright() as p:
        b = p.firefox.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1, color_scheme="light")
        ctx.request.post(srv.url + "/api/login", data=json.dumps({"user": "anna", "password": "pw-anna"}),
                         headers={"Content-Type": "application/json", "Origin": srv.origin})
        page = ctx.new_page(); errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(srv.url + "/graph/"); page.wait_for_selector('[data-graph-id="sample.code"]')
        page.click('[data-graph-id="sample.code"]')
        page.wait_for_function("() => window.graphViewTest && window.graphViewTest.settled === true", timeout=10000)
        a = H(page, "domPosition('step.check')")
        page.mouse.move(a["x"], a["y"]); page.mouse.down(); page.mouse.move(a["x"] + 50, a["y"], steps=5); page.mouse.move(a["x"] + 100, a["y"], steps=5); page.mouse.up()
        page.wait_for_timeout(1500); d = H(page, "domPosition('step.check')")
        page.emulate_media(color_scheme="dark"); page.wait_for_timeout(4000); t = H(page, "domPosition('step.check')")
        print("before", a, "dropped", d, "after theme switch", t, "errors", errors)
        b.close()
finally:
    srv.stop()
